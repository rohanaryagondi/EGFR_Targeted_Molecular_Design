#!/usr/bin/env python
"""Standalone GNINA scoring component for REINVENT 4 ExternalProcess.

Reads SMILES from stdin (one per line), docks each against the specified
receptor using GNINA, and writes normalized scores to stdout as JSON.

This script is STANDALONE -- it does NOT import anything from statebind.
It runs inside the separate reinvent4 conda environment.

REINVENT 4 ExternalProcess protocol (v4.7+):
  - Parent sends SMILES on stdin, one per line, terminated by EOF.
  - This script writes a JSON dict to stdout with structure:
    {"payload": {"gnina_score": [float, float, ...]}}
  - Score 0.0 for any molecule that fails (bad SMILES, docking error).

GNINA parameters match StateBind defaults for fair comparison:
  - exhaustiveness: 8
  - num_modes: 5
  - cnn_scoring: rescore
  - Scoring: sigmoid(-vina_score / scale), scale=3.0

Usage:
  echo "c1ccccc1" | python reinvent4_gnina_component.py \\
      --receptor data/processed/docking/receptors/1m17.pdbqt \\
      --center 22.014 0.253 52.794

  # Or with all options:
  python reinvent4_gnina_component.py \\
      --receptor path/to/receptor.pdbqt \\
      --center 22.014 0.253 52.794 \\
      --box-size 25.0 25.0 25.0 \\
      --exhaustiveness 8 \\
      --num-modes 5 \\
      --gnina-bin /path/to/gnina \\
      --scale 3.0 \\
      --timeout 120 \\
      < smiles.txt
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# ── SMILES to 3D SDF ───────────────────────────────────────────────────


def smiles_to_sdf(smiles: str, output_path: Path) -> bool:
    """Convert a SMILES string to a 3D SDF file using RDKit.

    Uses ETKDGv3 embedding with MMFF optimization, matching the
    StateBind docking pipeline (src/statebind/chemistry/docking.py).

    Args:
        smiles: Input SMILES string.
        output_path: Path to write the SDF file.

    Returns:
        True on success, False on failure.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        logger.error("RDKit not available -- cannot convert SMILES to 3D")
        return False

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning("Invalid SMILES: %s", smiles[:80])
        return False

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    status = AllChem.EmbedMolecule(mol, params)
    if status != 0:
        # Retry without fixed seed
        status = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        if status != 0:
            logger.warning("3D embedding failed for: %s", smiles[:80])
            return False

    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    except Exception:
        pass  # Non-fatal: unoptimized coords are acceptable

    writer = Chem.SDWriter(str(output_path))
    writer.write(mol)
    writer.close()
    return output_path.exists() and output_path.stat().st_size > 0


# ── GNINA output parsing ───────────────────────────────────────────────


def parse_gnina_output(stdout: str) -> dict[str, Any]:
    """Parse GNINA stdout for docking scores.

    Replicates the parsing logic from StateBind
    (src/statebind/chemistry/docking.py:_parse_gnina_output).

    GNINA outputs a table like::

        mode |   affinity | intramol | CNN_pose_score | CNN_affinity
        -----+------------+----------+----------------+-------------
           1 |     -8.123 |    0.000 |          0.851 |        7.23

    Args:
        stdout: Raw GNINA stdout text.

    Returns:
        Dict with keys: vina_score, cnn_score, cnn_affinity, n_poses.
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
        # Regex fallback for alternative GNINA output formats
        for line in lines:
            match = re.match(
                r"\s*1\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)"
                r"\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)",
                line,
            )
            if match:
                result["vina_score"] = float(match.group(1))
                result["cnn_score"] = float(match.group(3))
                result["cnn_affinity"] = float(match.group(4))
                result["n_poses"] = 1
                return result
        return result

    # Parse top mode (mode 1)
    top = data_lines[0]
    parts = [p.strip() for p in top.split("|")]
    if len(parts) < 2:
        parts = top.split()

    try:
        if "|" in data_lines[0]:
            result["vina_score"] = float(parts[1])
            if len(parts) >= 4:
                result["cnn_score"] = float(parts[3])
            if len(parts) >= 5:
                result["cnn_affinity"] = float(parts[4])
        else:
            result["vina_score"] = float(parts[1])
            if len(parts) >= 4:
                result["cnn_score"] = float(parts[3])
            if len(parts) >= 5:
                result["cnn_affinity"] = float(parts[4])
    except (ValueError, IndexError) as exc:
        logger.warning("Failed to parse GNINA output line: %s (%s)", top, exc)

    return result


# ── Score normalization ─────────────────────────────────────────────────


def normalize_vina_score(vina_score: float, scale: float = 3.0) -> float:
    """Map Vina score (kcal/mol) to [0, 1] via sigmoid(-score / scale).

    Matches StateBind normalization (src/statebind/chemistry/docking.py).

    Args:
        vina_score: Vina affinity in kcal/mol (more negative = better).
        scale: Denominator for sigmoid input. Default 3.0.

    Returns:
        Normalized score in (0, 1).
    """
    return 1.0 / (1.0 + math.exp(vina_score / scale))


# ── Single molecule docking ────────────────────────────────────────────


def dock_smiles(
    smiles: str,
    receptor: str,
    center: tuple[float, float, float],
    box_size: tuple[float, float, float],
    gnina_bin: str,
    exhaustiveness: int,
    num_modes: int,
    timeout: int,
    scale: float,
) -> float:
    """Dock a single SMILES and return normalized score.

    Pipeline: SMILES -> 3D SDF (RDKit) -> GNINA docking -> parse -> normalize.

    Args:
        smiles: Input SMILES string.
        receptor: Path to receptor PDBQT file.
        center: Docking box center (x, y, z).
        box_size: Docking box dimensions (sx, sy, sz).
        gnina_bin: Path to GNINA binary.
        exhaustiveness: GNINA exhaustiveness parameter.
        num_modes: Number of binding poses.
        timeout: Subprocess timeout in seconds.
        scale: Normalization scale for sigmoid.

    Returns:
        Normalized docking score in [0, 1]. Returns 0.0 on failure.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="reinvent4_gnina_"))
    try:
        ligand_sdf = tmpdir / "ligand.sdf"
        output_sdf = tmpdir / "output.sdf"

        # Step 1: SMILES -> 3D SDF
        if not smiles_to_sdf(smiles, ligand_sdf):
            return 0.0

        # Step 2: Run GNINA
        cmd = [
            gnina_bin,
            "-r", receptor,
            "-l", str(ligand_sdf),
            "--center_x", str(center[0]),
            "--center_y", str(center[1]),
            "--center_z", str(center[2]),
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
            logger.warning(
                "GNINA failed (code %d) for %s: %s",
                proc.returncode,
                smiles[:60],
                proc.stderr[:200],
            )
            return 0.0

        # Step 3: Parse and normalize
        parsed = parse_gnina_output(proc.stdout)
        vina_score = parsed["vina_score"]

        if parsed["n_poses"] == 0:
            logger.warning("No poses generated for: %s", smiles[:60])
            return 0.0

        return round(normalize_vina_score(vina_score, scale), 4)

    except subprocess.TimeoutExpired:
        logger.warning("GNINA timed out (%ds) for: %s", timeout, smiles[:60])
        return 0.0
    except Exception as exc:
        logger.warning("Docking error for %s: %s", smiles[:60], exc)
        return 0.0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── GNINA binary resolution ───────────────────────────────────────────


def find_gnina_binary(explicit_path: str | None = None) -> str:
    """Locate the GNINA binary.

    Search order:
      1. Explicit path from --gnina-bin argument
      2. System PATH (shutil.which)
      3. Project-relative bin/gnina (repo_root/bin/gnina)

    Args:
        explicit_path: User-provided path to GNINA binary, or None.

    Returns:
        Path to GNINA binary.

    Raises:
        FileNotFoundError: If GNINA cannot be found.
    """
    if explicit_path:
        p = Path(explicit_path)
        if p.exists() and p.is_file():
            return str(p)
        raise FileNotFoundError(f"GNINA binary not found at: {explicit_path}")

    # System PATH
    path = shutil.which("gnina")
    if path is not None:
        return path

    # Project-relative bin/gnina
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    project_bin = repo_root / "bin" / "gnina"
    if project_bin.exists() and project_bin.is_file():
        return str(project_bin)

    raise FileNotFoundError(
        "GNINA binary not found. Searched: PATH, "
        f"{project_bin}. Use --gnina-bin to specify."
    )


# ── Main entry point ───────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Standalone GNINA scoring component for REINVENT 4 ExternalProcess. "
            "Reads SMILES from stdin, writes normalized scores to stdout."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  echo 'c1ccccc1' | python reinvent4_gnina_component.py \\\n"
            "      --receptor data/processed/docking/receptors/1m17.pdbqt \\\n"
            "      --center 22.014 0.253 52.794\n"
        ),
    )
    parser.add_argument(
        "--receptor",
        required=True,
        help="Path to receptor PDBQT file for docking.",
    )
    parser.add_argument(
        "--center",
        type=float,
        nargs=3,
        required=True,
        metavar=("X", "Y", "Z"),
        help="Docking box center coordinates (x, y, z) in Angstroms.",
    )
    parser.add_argument(
        "--box-size",
        type=float,
        nargs=3,
        default=[25.0, 25.0, 25.0],
        metavar=("SX", "SY", "SZ"),
        help="Docking box dimensions in Angstroms (default: 25 25 25).",
    )
    parser.add_argument(
        "--exhaustiveness",
        type=int,
        default=8,
        help="GNINA exhaustiveness parameter (default: 8).",
    )
    parser.add_argument(
        "--num-modes",
        type=int,
        default=5,
        help="Number of binding poses to generate (default: 5).",
    )
    parser.add_argument(
        "--gnina-bin",
        default=None,
        help="Path to GNINA binary (default: auto-detect from PATH or bin/).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=3.0,
        help="Normalization scale for sigmoid(-vina_score / scale) (default: 3.0).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per molecule in seconds (default: 120).",
    )
    return parser


def main() -> None:
    """Main entry point: read SMILES from stdin, score, write JSON to stdout.

    REINVENT 4 ExternalProcess expects JSON output with structure:
      {"payload": {"<property>": [score1, score2, ...]}}
    where <property> matches the ``property`` parameter in the TOML config.
    """
    args = build_parser().parse_args()

    # Resolve GNINA binary
    try:
        gnina_bin = find_gnina_binary(args.gnina_bin)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # Validate receptor file
    receptor = Path(args.receptor)
    if not receptor.exists():
        print(f"Receptor file not found: {receptor}", file=sys.stderr)
        sys.exit(1)

    center = (args.center[0], args.center[1], args.center[2])
    box_size = (args.box_size[0], args.box_size[1], args.box_size[2])

    logger.info(
        "GNINA scoring component ready: receptor=%s, center=%s, gnina=%s",
        receptor,
        center,
        gnina_bin,
    )

    # Read all SMILES from stdin
    smiles_list: list[str] = []
    for line in sys.stdin:
        smi = line.strip()
        if smi:
            smiles_list.append(smi)

    if not smiles_list:
        logger.warning("No SMILES received on stdin")
        # Output empty JSON for REINVENT
        import json as _json
        print(_json.dumps({"payload": {"gnina_score": []}}))
        sys.exit(0)

    logger.info("Scoring %d molecules...", len(smiles_list))

    # Dock each molecule and collect scores
    scores: list[float] = []
    for smi in smiles_list:
        score = dock_smiles(
            smiles=smi,
            receptor=str(receptor),
            center=center,
            box_size=box_size,
            gnina_bin=gnina_bin,
            exhaustiveness=args.exhaustiveness,
            num_modes=args.num_modes,
            timeout=args.timeout,
            scale=args.scale,
        )
        scores.append(score)

    # Write JSON output for REINVENT 4 ExternalProcess
    import json as _json
    output = {"payload": {"gnina_score": scores}}
    print(_json.dumps(output), flush=True)


if __name__ == "__main__":
    main()
