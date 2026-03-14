#!/usr/bin/env python
"""Assemble the full v1 benchmark package.

Builds all datasets, validates, writes JSON + CSV to data/processed/benchmark/.

Usage:
    python scripts/assemble_benchmark.py
    python scripts/assemble_benchmark.py --output-dir data/processed/benchmark
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.processing.benchmark import assemble_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble v1 benchmark package")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed/benchmark"),
    )
    parser.add_argument("--split-seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 60)
    print("StateBind v1 Benchmark Assembly")
    print("=" * 60)
    print()

    try:
        summary = assemble_benchmark(
            output_dir=args.output_dir,
            split_seed=args.split_seed,
            fail_on_error=True,
        )
    except ValueError as e:
        print(f"\nFATAL: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    print(f"  Mutations:            {summary.n_mutations}")
    print(f"  Structures:           {summary.n_structures}")
    print(f"  Ligands:              {summary.n_ligands}")
    print(f"  Mut-Struct mappings:  {summary.n_mutation_structure_mappings}")
    print(f"  Struct-Lig mappings:  {summary.n_structure_ligand_mappings}")
    print(f"  States represented:   {', '.join(summary.states_represented)}")
    print(f"  Resistance gens:      {', '.join(summary.resistance_generations)}")
    print(f"  Splits:               {summary.split_counts}")
    print()
    print(f"Output directory: {args.output_dir}")
    print()

    # List output files
    for f in sorted(args.output_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:<40} {size:>8} bytes")


if __name__ == "__main__":
    main()
