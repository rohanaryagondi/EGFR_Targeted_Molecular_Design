#!/usr/bin/env python
"""Run the complete static baseline pipeline.

This is the main baseline script. It runs the full pipeline:
structure → pocket → candidates → filter → score → rank → evaluate

Usage:
    python scripts/run_static_baseline.py
    python scripts/run_static_baseline.py --output-dir artifacts/baselines/static_v1
    python scripts/run_static_baseline.py --no-analogs
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.baselines.pipeline import run_static_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run static baseline pipeline")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/baselines/static_v1"),
        help="Output directory for artifacts",
    )
    parser.add_argument(
        "--no-analogs", action="store_true",
        help="Skip analog enumeration (reference compounds only)",
    )
    parser.add_argument(
        "--top-k", type=int, default=10,
        help="Number of top candidates to highlight",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("StateBind — Static Baseline Pipeline")
    print("=" * 60)
    print()
    print("This baseline uses ONE structure, ONE pocket, and NO")
    print("conformational state information. It is the comparator")
    print("that state-aware design must beat.")
    print()

    result = run_static_baseline(
        output_dir=args.output_dir,
        enumerate_analogs=not args.no_analogs,
        top_k=args.top_k,
    )

    # Print top candidates
    print()
    print("=" * 60)
    print(f"Top {args.top_k} Candidates")
    print("=" * 60)
    print(f"{'Rank':<6} {'ID':<25} {'Score':<10} {'Similarity':<12} {'DrugLike':<10}")
    print("-" * 63)

    for c in result.ranked.candidates[:args.top_k]:
        sim = c.get_score("reference_similarity") or 0
        drug = c.get_score("druglikeness") or 0
        print(f"{c.rank:<6} {c.candidate_id:<25} {c.composite_score:<10.4f} "
              f"{sim:<12.4f} {drug:<10.4f}")

    # Print evaluation summary
    ev = result.evaluation
    print()
    print("=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"  Candidates ranked:  {ev.n_candidates_ranked}")
    print(f"  Validity rate:      {ev.validity_rate:.1%}")
    print(f"  Uniqueness rate:    {ev.uniqueness_rate:.1%}")
    print(f"  Diversity score:    {ev.diversity_score:.4f}")
    print()

    if ev.score_stats:
        print("  Score distributions:")
        for name, stats in ev.score_stats.items():
            print(f"    {name:<25} mean={stats['mean']:.4f}  "
                  f"std={stats['std']:.4f}  "
                  f"[{stats['min']:.4f}, {stats['max']:.4f}]")

    print()
    print("IMPORTANT LIMITATIONS:")
    print("  - Docking score is a STUB (constant 0.5)")
    print("  - Similarity is SMILES n-gram based, not fingerprint-based")
    print("  - Property estimates are heuristic, not RDKit-computed")
    print("  - This baseline is deliberately weak — it exists to be beaten")


if __name__ == "__main__":
    main()
