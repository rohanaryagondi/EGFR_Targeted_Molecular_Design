#!/usr/bin/env python
"""Build the processed structure dataset.

Usage:
    python scripts/build_structure_dataset.py
    python scripts/build_structure_dataset.py --output-dir data/processed/structures
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.processing.structures import build_structure_dataset
from statebind.processing.validation import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR structure dataset")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/structures"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Building structure dataset...")
    dataset = build_structure_dataset()

    report = validate_dataset(structures=dataset)
    print(report.summary())

    if not report.is_valid:
        print("\nValidation failed. Not writing output.")
        sys.exit(1)

    out_path = args.output_dir / "structures.json"
    with open(out_path, "w") as f:
        json.dump(dataset.model_dump(mode="json"), f, indent=2, default=str)

    print(f"\nWrote {len(dataset.structures)} structures to {out_path}")

    # State distribution
    from collections import Counter
    state_counts = Counter(s.state.value for s in dataset.structures)
    print("\nState distribution:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state:<20} {count}")


if __name__ == "__main__":
    main()
