#!/usr/bin/env python
"""Build the processed ligand dataset.

Usage:
    python scripts/build_ligand_dataset.py
    python scripts/build_ligand_dataset.py --output-dir data/processed/ligands
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.processing.ligands import build_ligand_dataset
from statebind.processing.validation import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR ligand dataset")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/ligands"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Building ligand dataset...")
    dataset = build_ligand_dataset()

    report = validate_dataset(ligands=dataset)
    print(report.summary())

    if not report.is_valid:
        print("\nValidation failed. Not writing output.")
        sys.exit(1)

    out_path = args.output_dir / "ligands.json"
    with open(out_path, "w") as f:
        json.dump(dataset.model_dump(mode="json"), f, indent=2, default=str)

    print(f"\nWrote {len(dataset.ligands)} ligands to {out_path}")
    for lig in dataset.ligands:
        approved = " [APPROVED]" if lig.is_approved else ""
        print(f"  {lig.ligand_id:<20} {lig.source.value:<16}{approved}")


if __name__ == "__main__":
    main()
