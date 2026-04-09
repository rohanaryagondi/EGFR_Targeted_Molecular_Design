"""GNINA docking wrapper: physics-informed docking with CNN scoring.

Wraps the GNINA CLI binary (AutoDock Vina + CNN scoring) for
protein-ligand docking.  Converts SMILES to 3D conformers via RDKit,
calls GNINA as a subprocess, and parses results into structured
DockingResult objects.

Optional dependencies:
    gnina (CLI binary) -- must be on PATH or configured in docking.yaml
    rdkit -- for 3D conformer generation from SMILES

The flag ``HAS_GNINA`` lets callers check availability at runtime.
Contract reference: workstreams/INTERFACES.md Contract 8.
"""

from __future__ import annotations

import json
import logging
import math
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── GNINA availability ───────────────────────────────────────────────────

_gnina_verified: bool | None = None  # None = not yet checked
_gnina_path: str | None = None  # Cached path to the GNINA binary


def _find_gnina_binary() -> str | None:
    """Locate the GNINA binary.

    Search order:
    1. PATH (``shutil.which("gnina")``)
    2. Project-relative ``bin/gnina`` (for worktree-local installs)
    3. Config ``gnina.binary_path`` if it's an absolute path
    """
    # 1. System PATH
    path = shutil.which("gnina")
    if path is not None:
        return path

    # 2. Project-relative bin/gnina
    try:
        from statebind.data.paths import DataPaths
        project_bin = DataPaths().root / "bin" / "gnina"
        if project_bin.exists() and project_bin.is_file():
            return str(project_bin)
    except Exception:
        pass

    return None


HAS_GNINA: bool = _find_gnina_binary() is not None
"""True when GNINA binary is found (PATH or project bin/)."""


def is_gnina_available() -> bool:
    """Check if the GNINA binary is installed and callable.

    First call verifies by running ``gnina --version``; result is cached.
    Returns False without raising if GNINA is missing or broken.
    """
    global _gnina_verified, _gnina_path  # noqa: PLW0603
    if _gnina_verified is not None:
        return _gnina_verified

    path = _find_gnina_binary()
    if path is None:
        _gnina_verified = False
        return False

    try:
        subprocess.run(
            [path, "--version"],
            capture_output=True,
            timeout=10,
        )
        _gnina_verified = True
        _gnina_path = path
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        _gnina_verified = False
    return _gnina_verified


def _get_gnina_path() -> str:
    """Return the cached path to the GNINA binary."""
    if _gnina_path is not None:
        return _gnina_path
    return _find_gnina_binary() or "gnina"


# ── Data models ──────────────────────────────────────────────────────────


class DockingResult(BaseModel):
    """Result from a single GNINA docking run."""

    smiles: str
    receptor_state: str = Field(default="", description="e.g. DFGin_aCin")
    vina_score: float = Field(
        default=0.0, description="Best Vina affinity in kcal/mol (more negative = better)"
    )
    cnn_score: float = Field(
        default=0.0, description="CNN pose score [0, 1]"
    )
    cnn_affinity: float = Field(
        default=0.0, description="CNN predicted pKd"
    )
    pose_pdb: str | None = Field(
        default=None, description="PDB block of best pose"
    )
    n_poses: int = Field(default=0)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)


class DockingConfig(BaseModel):
    """Configuration for GNINA docking, loaded from configs/docking.yaml."""

    binary_path: str = "gnina"
    exhaustiveness: int = 8
    num_modes: int = 5
    cnn_scoring: str = "rescore"
    timeout_per_molecule: int = 120
    gpu: bool = False
    box_padding: float = 5.0
    default_box_size: tuple[float, float, float] = (25.0, 25.0, 25.0)
    vina_scale: float = 3.0
    score_source: str = "vina"
    receptor_output_dir: str = "data/processed/docking/receptors/"
    n_workers: int = 4
    representatives: dict[str, str] = Field(default_factory=lambda: {
        "DFGin_aCin": "1m17",
        "DFGin_aCout": "2gs7",
        "DFGout_aCin": "3w2r",
    })


# ── Config loading ───────────────────────────────────────────────────────


def load_docking_config(config_path: Path | None = None) -> DockingConfig:
    """Load docking configuration from YAML.

    Falls back to defaults if config file is not found.
    """
    if config_path is None:
        from statebind.data.paths import DataPaths
        config_path = DataPaths().root / "configs" / "docking.yaml"

    try:
        from statebind.utils.config import load_config
        raw = load_config(config_path)
    except FileNotFoundError:
        logger.debug("Docking config not found at %s, using defaults", config_path)
        return DockingConfig()

    gnina = raw.get("gnina", {})
    receptor = raw.get("receptor", {})
    scoring = raw.get("scoring", {})
    states = raw.get("states", {})
    batch = raw.get("batch", {})

    box_size = receptor.get("default_box_size", [25.0, 25.0, 25.0])

    return DockingConfig(
        binary_path=gnina.get("binary_path", "gnina"),
        exhaustiveness=gnina.get("exhaustiveness", 8),
        num_modes=gnina.get("num_modes", 5),
        cnn_scoring=gnina.get("cnn_scoring", "rescore"),
        timeout_per_molecule=gnina.get("timeout_per_molecule", 120),
        gpu=gnina.get("gpu", False),
        box_padding=receptor.get("box_padding", 5.0),
        default_box_size=(box_size[0], box_size[1], box_size[2]),
        vina_scale=scoring.get("vina_scale", 3.0),
        score_source=scoring.get("score_source", "vina"),
        receptor_output_dir=receptor.get("output_dir", "data/processed/docking/receptors/"),
        n_workers=batch.get("n_workers", 4),
        representatives=states.get("representatives", {
            "DFGin_aCin": "1m17",
            "DFGin_aCout": "2gs7",
            "DFGout_aCin": "3w2r",
        }),
    )


# ── Score normalization ──────────────────────────────────────────────────


def normalize_vina_score(vina_score: float, scale: float = 3.0) -> float:
    """Map Vina score (kcal/mol) to [0, 1] via sigmoid(-score / scale).

    Vina scores are negative (more negative = better binding)::

        -9 kcal/mol -> sigmoid(3.0) = 0.95  (strong binder)
        -6 kcal/mol -> sigmoid(2.0) = 0.88
        -3 kcal/mol -> sigmoid(1.0) = 0.73
         0 kcal/mol -> sigmoid(0.0) = 0.50  (no binding)
        +3 kcal/mol -> sigmoid(-1)  = 0.27  (unfavorable)

    Args:
        vina_score: Vina affinity in kcal/mol.
        scale: Denominator for sigmoid input.  Default 3.0.

    Returns:
        Normalized score in (0, 1).
    """
    return 1.0 / (1.0 + math.exp(vina_score / scale))


# ── Ligand preparation ───────────────────────────────────────────────────


def _smiles_to_sdf(smiles: str, output_path: Path) -> bool:
    """Convert SMILES to a 3D SDF file using RDKit.

    Returns True on success, False on failure (invalid SMILES, RDKit
    unavailable, or embedding failure).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        logger.debug("RDKit not available for 3D conformer generation")
        return False

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    status = AllChem.EmbedMolecule(mol, params)
    if status != 0:
        # Retry with random coordinates
        status = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        if status != 0:
            return False

    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    except Exception:
        pass  # Optimization failure is non-fatal; unoptimized coords are OK

    writer = Chem.SDWriter(str(output_path))
    writer.write(mol)
    writer.close()
    return output_path.exists() and output_path.stat().st_size > 0


# ── GNINA output parsing ────────────────────────────────────────────────


def _parse_gnina_output(stdout: str) -> dict[str, Any]:
    """Parse GNINA stdout for docking scores.

    GNINA outputs a table like::

        mode |   affinity | intramol | CNN_pose_score | CNN_affinity
        -----+------------+----------+----------------+-------------
           1 |     -8.123 |    0.000 |          0.851 |        7.23

    Returns dict with keys: vina_score, cnn_score, cnn_affinity, n_poses.
    Returns zeros if parsing fails.
    """
    result: dict[str, Any] = {
        "vina_score": 0.0,
        "cnn_score": 0.0,
        "cnn_affinity": 0.0,
        "n_poses": 0,
    }

    lines = stdout.strip().splitlines()
    data_lines: list[str] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-----"):
            in_table = True
            continue
        if in_table and stripped and stripped[0].isdigit():
            data_lines.append(stripped)

    result["n_poses"] = len(data_lines)

    if not data_lines:
        # Try regex fallback for different GNINA output formats
        for line in lines:
            match = re.match(
                r"\s*1\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)",
                line,
            )
            if match:
                result["vina_score"] = float(match.group(1))
                result["cnn_score"] = float(match.group(3))
                result["cnn_affinity"] = float(match.group(4))
                result["n_poses"] = 1
                return result
        return result

    # Parse the top mode (mode 1)
    top = data_lines[0]
    parts = [p.strip() for p in top.split("|")]
    if len(parts) < 2:
        # Try whitespace-separated format
        parts = top.split()

    try:
        if "|" in data_lines[0]:
            # Pipe-separated format
            result["vina_score"] = float(parts[1])
            if len(parts) >= 4:
                result["cnn_score"] = float(parts[3])
            if len(parts) >= 5:
                result["cnn_affinity"] = float(parts[4])
        else:
            # Whitespace-separated: mode affinity intramol cnn_pose cnn_aff
            result["vina_score"] = float(parts[1])
            if len(parts) >= 4:
                result["cnn_score"] = float(parts[3])
            if len(parts) >= 5:
                result["cnn_affinity"] = float(parts[4])
    except (ValueError, IndexError) as exc:
        logger.warning("Failed to parse GNINA output line: %s (%s)", top, exc)

    return result


# ── Core docking functions ───────────────────────────────────────────────


def dock_molecule(
    smiles: str,
    receptor_pdbqt: str | Path,
    box_center: tuple[float, float, float],
    box_size: tuple[float, float, float] = (25.0, 25.0, 25.0),
    exhaustiveness: int = 8,
    num_modes: int = 5,
    timeout: int = 120,
) -> DockingResult:
    """Dock a single molecule into a receptor pocket using GNINA.

    Converts SMILES to a 3D SDF via RDKit, runs GNINA as a subprocess,
    and parses the output.

    Returns DockingResult with ``success=False`` and an error message
    on any failure (GNINA missing, invalid SMILES, timeout, etc.).

    Args:
        smiles: SMILES string of the ligand.
        receptor_pdbqt: Path to the receptor PDBQT file.
        box_center: (x, y, z) center of the docking box in Angstroms.
        box_size: (sx, sy, sz) dimensions of the docking box.
        exhaustiveness: Vina exhaustiveness parameter (higher = more thorough).
        num_modes: Number of binding poses to generate.
        timeout: Seconds before killing the GNINA subprocess.

    Returns:
        DockingResult with scores and optional pose.
    """
    if not is_gnina_available():
        return DockingResult(
            smiles=smiles, success=False,
            error="GNINA not installed or not on PATH",
        )

    receptor_pdbqt = Path(receptor_pdbqt)
    if not receptor_pdbqt.exists():
        return DockingResult(
            smiles=smiles, success=False,
            error=f"Receptor file not found: {receptor_pdbqt}",
        )

    tmpdir = Path(tempfile.mkdtemp(prefix="gnina_"))
    try:
        ligand_sdf = tmpdir / "ligand.sdf"
        output_sdf = tmpdir / "output.sdf"

        if not _smiles_to_sdf(smiles, ligand_sdf):
            return DockingResult(
                smiles=smiles, success=False,
                error="Failed to generate 3D conformer from SMILES (RDKit)",
            )

        gnina_bin = _get_gnina_path()
        cmd = [
            gnina_bin,
            "-r", str(receptor_pdbqt),
            "-l", str(ligand_sdf),
            "--center_x", str(box_center[0]),
            "--center_y", str(box_center[1]),
            "--center_z", str(box_center[2]),
            "--size_x", str(box_size[0]),
            "--size_y", str(box_size[1]),
            "--size_z", str(box_size[2]),
            "--exhaustiveness", str(exhaustiveness),
            "--num_modes", str(num_modes),
            "--cnn_scoring", "rescore",
            "-o", str(output_sdf),
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.returncode != 0:
            return DockingResult(
                smiles=smiles, success=False,
                error=f"GNINA exited with code {proc.returncode}: {proc.stderr[:500]}",
            )

        parsed = _parse_gnina_output(proc.stdout)

        # Read best pose from output SDF if available
        pose_pdb: str | None = None
        if output_sdf.exists():
            try:
                pose_pdb = output_sdf.read_text()[:10000]  # Cap at 10KB
            except Exception:
                pass

        return DockingResult(
            smiles=smiles,
            vina_score=parsed["vina_score"],
            cnn_score=parsed["cnn_score"],
            cnn_affinity=parsed["cnn_affinity"],
            pose_pdb=pose_pdb,
            n_poses=parsed["n_poses"],
            success=True,
        )

    except subprocess.TimeoutExpired:
        return DockingResult(
            smiles=smiles, success=False,
            error=f"GNINA timed out after {timeout}s",
        )
    except Exception as exc:
        return DockingResult(
            smiles=smiles, success=False,
            error=f"Docking failed: {exc}",
        )
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def _dock_single(
    args: tuple[str, str | Path, tuple[float, float, float], tuple[float, float, float]],
) -> DockingResult:
    """Wrapper for dock_molecule to work with ProcessPoolExecutor."""
    smiles, receptor_pdbqt, box_center, box_size = args
    return dock_molecule(smiles, receptor_pdbqt, box_center, box_size)


def dock_batch(
    smiles_list: list[str],
    receptor_pdbqt: str | Path,
    box_center: tuple[float, float, float],
    box_size: tuple[float, float, float] = (25.0, 25.0, 25.0),
    n_workers: int = 4,
) -> list[DockingResult]:
    """Batch docking with optional parallelization.

    Args:
        smiles_list: List of SMILES strings to dock.
        receptor_pdbqt: Path to the receptor PDBQT file.
        box_center: (x, y, z) center of the docking box.
        box_size: (sx, sy, sz) dimensions of the docking box.
        n_workers: Number of parallel workers (1 = sequential).

    Returns:
        List of DockingResult in the same order as input.
    """
    if not smiles_list:
        return []

    if n_workers <= 1:
        return [
            dock_molecule(s, receptor_pdbqt, box_center, box_size)
            for s in smiles_list
        ]

    args_list = [
        (s, str(receptor_pdbqt), box_center, box_size) for s in smiles_list
    ]

    results: dict[int, DockingResult] = {}
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        future_to_idx = {
            executor.submit(_dock_single, args): i
            for i, args in enumerate(args_list)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                results[idx] = DockingResult(
                    smiles=smiles_list[idx],
                    success=False,
                    error=f"Batch docking failed: {exc}",
                )

    return [results[i] for i in range(len(smiles_list))]


# ── Receptor lookup ──────────────────────────────────────────────────────


def get_receptor_for_state(
    state: str,
    config: DockingConfig | None = None,
) -> tuple[Path, tuple[float, float, float], tuple[float, float, float]] | None:
    """Look up prepared receptor files for a conformational state.

    Returns (pdbqt_path, box_center, box_size) or None if the receptor
    has not been prepared yet.

    Args:
        state: Conformational state name (e.g. "DFGin_aCin").
        config: Docking config.  Loaded from defaults if None.
    """
    if config is None:
        config = load_docking_config()

    pdb_id = config.representatives.get(state)
    if pdb_id is None:
        return None

    from statebind.data.paths import DataPaths
    paths = DataPaths()
    receptor_dir = paths.root / config.receptor_output_dir

    pdbqt_path = receptor_dir / f"{pdb_id}.pdbqt"
    box_config_path = receptor_dir / f"{pdb_id}_box.json"

    if not pdbqt_path.exists() or not box_config_path.exists():
        return None

    try:
        with open(box_config_path) as f:
            box = json.load(f)
        center = (
            float(box["center_x"]),
            float(box["center_y"]),
            float(box["center_z"]),
        )
        size = (
            float(box.get("size_x", config.default_box_size[0])),
            float(box.get("size_y", config.default_box_size[1])),
            float(box.get("size_z", config.default_box_size[2])),
        )
        return pdbqt_path, center, size
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Invalid box config %s: %s", box_config_path, exc)
        return None
