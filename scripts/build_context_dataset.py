#!/usr/bin/env python
"""Build the processed context (mutation) dataset.

Usage:
    python scripts/build_context_dataset.py
    python scripts/build_context_dataset.py --output-dir data/processed/context
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.processing.context import build_context_dataset
from statebind.processing.validation import validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR context dataset")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/context"),
    )
    parser.add_argument("--split-seed", type=int, default=42)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Building context dataset...")
    dataset = build_context_dataset(assign_splits=True, split_seed=args.split_seed)

    report = validate_dataset(context=dataset)
    print(report.summary())

    if not report.is_valid:
        print("\nValidation failed. Not writing output.")
        sys.exit(1)

    out_path = args.output_dir / "context.json"
    with open(out_path, "w") as f:
        json.dump(dataset.model_dump(mode="json"), f, indent=2, default=str)

    print(f"\nWrote {len(dataset.mutations)} mutations to {out_path}")
    for m in dataset.mutations:
        print(f"  {m.mutation_id:<20} {m.resistance_generation.value:<12} "
              f"{m.mechanism_category.value:<20} split={m.split}")


if __name__ == "__main__":
    main()
