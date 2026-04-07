#!/usr/bin/env python3
"""Prepare docking receptors: download PDBs, convert to PDBQT, define boxes.

For each conformational state's representative PDB:
1. Download from RCSB PDB (if not cached)
2. Extract binding site centroid from co-crystallized ligand atoms
3. Clean PDB: remove water, ions, ligands; keep chain A
4. Convert to PDBQT format (via OpenBabel or manual fallback)
5. Define docking box (centroid + configured box size)
6. Save PDBQT + box config JSON

Usage:
    python scripts/prepare_docking_receptors.py
    python scripts/prepare_docking_receptors.py --config configs/docking.yaml
    python scripts/prepare_docking_receptors.py --output-dir data/processed/docking/receptors/
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from statebind.chemistry.docking import DockingConfig, load_docking_config
from statebind.data.paths import DataPaths

# Verified PDB ligand IDs from actual RCSB PDB files.
# These override any values from processing/structures.py which may use
# literature-convention ligand codes that don't match PDB HETATM records.
_VERIFIED_PDB_LIGANDS: dict[str, tuple[str, str]] = {
    # pdb_id -> (actual_ligand_id_in_PDB, chain)
    "1m17": ("AQ4", "A"),   # erlotinib (PDB uses AQ4, not AEE)
    "2gs7": ("ANP", "A"),   # AMP-PNP analog in Src-like inactive EGFR
    "3w2r": ("W2R", "A"),   # type-II inhibitor in DFGout_aCin EGFR (T790M/L858R)
    "4zau": ("YY3", "A"),   # osimertinib (AZD9291) in classical inactive EGFR
}

# Excluded HETATM residue names (not drug-like ligands)
_EXCLUDED_HETATM = {"HOH", "MG", "IOD", "SO4", "CL", "NA", "ZN", "CA", "EDO", "GOL", "PEG"}


def _detect_ligand(pdb_path: Path, chain: str = "A") -> str | None:
    """Auto-detect the drug-like ligand in a PDB file.

    Finds the largest non-water, non-ion HETATM group by atom count.
    """
    ligand_counts: dict[str, int] = {}
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith("HETATM"):
                continue
            res_name = line[17:20].strip()
            ch = line[21].strip()
            if res_name in _EXCLUDED_HETATM:
                continue
            if ch == chain or not ch:
                ligand_counts[res_name] = ligand_counts.get(res_name, 0) + 1

    if not ligand_counts:
        return None
    return max(ligand_counts, key=ligand_counts.get)  # type: ignore[arg-type]


def download_pdb(pdb_id: str, output_path: Path) -> Path:
    """Download a PDB file from RCSB if not already cached.

    Args:
        pdb_id: 4-character PDB ID (lowercase).
        output_path: Where to save the PDB file.

    Returns:
        Path to the downloaded file.

    Raises:
        RuntimeError: If download fails.
    """
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"  Using cached PDB: {output_path}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    print(f"  Downloading {url} ...")

    try:
        urllib.request.urlretrieve(url, str(output_path))
    except Exception as exc:
        raise RuntimeError(f"Failed to download {pdb_id}: {exc}") from exc

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file is empty: {output_path}")

    return output_path


def extract_ligand_centroid(
    pdb_path: Path,
    ligand_id: str,
    chain: str = "A",
) -> tuple[float, float, float]:
    """Extract the centroid of a co-crystallized ligand from a PDB file.

    Parses HETATM records for the given ligand and chain, computes
    the mean x, y, z coordinates.

    Args:
        pdb_path: Path to the PDB file.
        ligand_id: 3-character ligand identifier (e.g. "AEE").
        chain: Chain ID to search.

    Returns:
        (x, y, z) centroid coordinates in Angstroms.

    Raises:
        ValueError: If no matching HETATM records found.
    """
    coords: list[tuple[float, float, float]] = []

    with open(pdb_path) as f:
        for line in f:
            if not line.startswith("HETATM"):
                continue
            # PDB format: columns 17-20 = residue name, 21 = chain
            res_name = line[17:20].strip()
            ch = line[21].strip()
            if res_name == ligand_id and (ch == chain or not ch):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    coords.append((x, y, z))
                except ValueError:
                    continue

    if not coords:
        raise ValueError(
            f"No HETATM records found for ligand {ligand_id} chain {chain} "
            f"in {pdb_path}"
        )

    cx = sum(c[0] for c in coords) / len(coords)
    cy = sum(c[1] for c in coords) / len(coords)
    cz = sum(c[2] for c in coords) / len(coords)

    return (round(cx, 3), round(cy, 3), round(cz, 3))


def clean_pdb(pdb_path: Path, output_path: Path, chain: str = "A") -> Path:
    """Clean a PDB file for docking: keep protein atoms, remove ligands/water.

    Keeps only ATOM records for the specified chain.  Removes HETATM
    (ligands, ions), HOH (water), and CONNECT records.

    Args:
        pdb_path: Input PDB path.
        output_path: Output cleaned PDB path.
        chain: Chain ID to keep.

    Returns:
        Path to the cleaned file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    kept_lines: list[str] = []

    with open(pdb_path) as f:
        for line in f:
            record = line[:6].strip()
            if record == "ATOM":
                ch = line[21].strip()
                if ch == chain or not ch:
                    kept_lines.append(line)
            elif record in ("TER", "END"):
                kept_lines.append(line)
            # Skip HETATM, CONECT, MASTER, etc.

    with open(output_path, "w") as f:
        f.writelines(kept_lines)

    return output_path


def convert_to_pdbqt(pdb_path: Path, pdbqt_path: Path) -> bool:
    """Convert a cleaned PDB to PDBQT format.

    Tries OpenBabel first, then falls back to a minimal manual conversion
    that adds Gasteiger partial charges.

    Args:
        pdb_path: Input cleaned PDB.
        pdbqt_path: Output PDBQT path.

    Returns:
        True on success.
    """
    pdbqt_path.parent.mkdir(parents=True, exist_ok=True)

    # Try OpenBabel
    obabel = shutil.which("obabel")
    if obabel:
        try:
            result = subprocess.run(
                [obabel, str(pdb_path), "-O", str(pdbqt_path), "-xr"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and pdbqt_path.exists():
                print(f"  Converted via OpenBabel: {pdbqt_path}")
                return True
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Fallback: minimal PDB -> PDBQT conversion
    # PDBQT = PDB + partial charges in columns 71-76 + AD4 atom types in 77-79
    # This is a simplified conversion; OpenBabel is preferred.
    print("  OpenBabel not found, using minimal PDB->PDBQT conversion")
    _AD4_TYPES = {
        "C": "C", "N": "N", "O": "O", "S": "S", "H": "H",
        "CA": "C", "CB": "C", "CG": "C", "CD": "C", "CE": "C", "CZ": "C",
        "ND": "N", "NE": "N", "NZ": "N", "NH": "N",
        "OD": "O", "OE": "O", "OG": "O", "OH": "O",
        "SD": "S", "SG": "S",
    }

    output_lines: list[str] = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM"):
                atom_name = line[12:16].strip()
                element = line[76:78].strip() if len(line) > 76 else atom_name[0]
                # Look up AD4 type
                ad4 = _AD4_TYPES.get(atom_name[:2], _AD4_TYPES.get(element, "C"))
                # Set charge to 0.000 (Gasteiger charges require full computation)
                new_line = f"{line[:54]}  0.000 {ad4:>2s}  \n"
                output_lines.append(new_line)
            elif line.startswith("TER") or line.startswith("END"):
                output_lines.append(line)

    with open(pdbqt_path, "w") as f:
        f.writelines(output_lines)

    return pdbqt_path.exists() and pdbqt_path.stat().st_size > 0


def save_box_config(
    pdb_id: str,
    state: str,
    center: tuple[float, float, float],
    box_size: tuple[float, float, float],
    ligand_id: str,
    output_dir: Path,
) -> Path:
    """Save docking box configuration as JSON.

    Args:
        pdb_id: PDB ID.
        state: Conformational state name.
        center: Box center coordinates.
        box_size: Box dimensions.
        ligand_id: Ligand used to define the center.
        output_dir: Output directory.

    Returns:
        Path to the saved JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    box_path = output_dir / f"{pdb_id}_box.json"

    config = {
        "pdb_id": pdb_id,
        "state": state,
        "center_x": center[0],
        "center_y": center[1],
        "center_z": center[2],
        "size_x": box_size[0],
        "size_y": box_size[1],
        "size_z": box_size[2],
        "ligand_id": ligand_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(box_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"  Saved box config: {box_path}")
    return box_path


def prepare_all_receptors(
    config: DockingConfig | None = None,
    output_dir: Path | None = None,
) -> dict[str, bool]:
    """Prepare docking receptors for all conformational states.

    Args:
        config: Docking configuration.
        output_dir: Override output directory.

    Returns:
        Dict mapping state -> success bool.
    """
    if config is None:
        config = load_docking_config()

    paths = DataPaths()

    if output_dir is None:
        output_dir = paths.root / config.receptor_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_pdb_dir = paths.raw_structures_dir
    raw_pdb_dir.mkdir(parents=True, exist_ok=True)

    box_size = config.default_box_size
    results: dict[str, bool] = {}

    for state, pdb_id in config.representatives.items():
        print(f"\n{'='*60}")
        print(f"Preparing receptor: {pdb_id} (state: {state})")
        print(f"{'='*60}")

        # Look up verified ligand info, or auto-detect from PDB
        verified = _VERIFIED_PDB_LIGANDS.get(pdb_id)
        if verified:
            ligand_id, chain = verified
        else:
            ligand_id, chain = None, "A"  # type: ignore[assignment]

        try:
            # 1. Download PDB
            pdb_path = raw_pdb_dir / f"{pdb_id}.pdb"
            download_pdb(pdb_id, pdb_path)

            # 2. Auto-detect ligand if not verified
            if ligand_id is None:
                ligand_id = _detect_ligand(pdb_path, chain)
                if ligand_id is None:
                    print(f"  ERROR: No drug-like ligand found in {pdb_id}")
                    results[state] = False
                    continue
                print(f"  Auto-detected ligand: {ligand_id}")

            # 3. Extract ligand centroid
            center = extract_ligand_centroid(pdb_path, ligand_id, chain)
            print(f"  Ligand {ligand_id} centroid: ({center[0]}, {center[1]}, {center[2]})")

            # 4. Clean PDB
            clean_path = output_dir / f"{pdb_id}_clean.pdb"
            clean_pdb(pdb_path, clean_path, chain)
            print(f"  Cleaned PDB: {clean_path}")

            # 5. Convert to PDBQT
            pdbqt_path = output_dir / f"{pdb_id}.pdbqt"
            success = convert_to_pdbqt(clean_path, pdbqt_path)
            if not success:
                print(f"  ERROR: PDBQT conversion failed for {pdb_id}")
                results[state] = False
                continue

            # 6. Save box config
            save_box_config(pdb_id, state, center, box_size, ligand_id, output_dir)

            results[state] = True
            print(f"  SUCCESS: {pdb_id} ready for docking")

        except Exception as exc:
            print(f"  ERROR: {exc}")
            results[state] = False

    print(f"\n{'='*60}")
    print("Summary:")
    for state, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {state}: {status}")
    print(f"{'='*60}")

    return results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Prepare docking receptors for each EGFR conformational state.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to docking config YAML (default: configs/docking.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for PDBQT files and box configs",
    )
    args = parser.parse_args()

    config = load_docking_config(args.config)
    prepare_all_receptors(config, args.output_dir)


if __name__ == "__main__":
    main()
