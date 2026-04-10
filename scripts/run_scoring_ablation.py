#!/usr/bin/env python3
"""Run scoring ablation analysis on state-aware candidates.

Systematically zeros each scoring component, renormalizes weights, reranks
candidates, and measures enrichment.  This identifies which component
drives retrospective enrichment (P10) and whether enrichment survives
without state_specificity (P11 -- the 3-component fairness check).

The script loads pre-scored candidates from a RankedPool JSON artifact.
If no artifact exists, it runs the pipeline to generate one.

Usage:
    python scripts/run_scoring_ablation.py
    python scripts/run_scoring_ablation.py --pool artifacts/ranking/state_aware_pool.json
    python scripts/run_scoring_ablation.py --cutoff 2010 --threshold 0.4
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from statebind.evaluation.retrospective import get_future_drugs
from statebind.evaluation.scoring_ablation import (
    AblationBattery,
    run_ablation_battery,
)
from statebind.ranking.models import RankedPool
from statebind.ranking.scoring import DEFAULT_WEIGHTS
from statebind.utils.io import save_json

logger = logging.getLogger(__name__)


def _load_or_generate_pool(pool_path: Path | None) -> RankedPool:
    """Load a RankedPool from JSON, or generate one by running the pipeline."""
    if pool_path is not None and pool_path.exists():
        import json

        with open(pool_path) as f:
            data = json.load(f)
        pool = RankedPool.model_validate(data)
        logger.info(
            "Loaded %d candidates from %s", pool.n_ranked, pool_path
        )
        return pool

    # No artifact -- run pipeline
    logger.info("No pool artifact found. Running state-aware pipeline...")
    from statebind.generation.filtering import filter_all_states
    from statebind.generation.generator import generate_all_states
    from statebind.ranking.scoring import rank_state_aware

    generation = generate_all_states()
    filtered = filter_all_states(generation)
    pool = rank_state_aware(filtered)
    logger.info("Generated %d scored candidates", pool.n_ranked)

    # Save for future use
    out_dir = Path("artifacts/ranking")
    out_dir.mkdir(parents=True, exist_ok=True)
    save_json(pool.model_dump(mode="json"), out_dir / "state_aware_pool.json")
    logger.info("Saved pool to %s", out_dir / "state_aware_pool.json")

    return pool


def _print_summary(results: list) -> None:
    """Print a formatted summary table to stdout."""
    header = (
        f"{'Config':<25} {'EF@10':>8} {'CI_low':>8} {'CI_high':>8} "
        f"{'BEDROC':>8} {'Mean':>8} {'N':>6}"
    )
    print("\n" + "=" * 80)
    print("SCORING ABLATION RESULTS")
    print("=" * 80)
    print(header)
    print("-" * 80)

    for r in results:
        bedroc_str = f"{r.bedroc:.4f}" if r.bedroc is not None else "N/A"
        print(
            f"{r.config.name:<25} {r.ef_at_10:>8.4f} {r.ef_ci_lower:>8.4f} "
            f"{r.ef_ci_upper:>8.4f} {bedroc_str:>8} {r.mean_score:>8.4f} "
            f"{r.n_candidates:>6d}"
        )

    print("=" * 80)

    # Highlight fairness check
    fairness = [r for r in results if r.config.zeroed_component == "state_specificity"]
    baseline = [r for r in results if r.config.name == "baseline"]
    if fairness and baseline:
        f = fairness[0]
        b = baseline[0]
        print(
            f"\n3-Component Fairness Check (P11):"
            f"\n  Baseline EF@10:      {b.ef_at_10:.4f} [{b.ef_ci_lower:.4f}, {b.ef_ci_upper:.4f}]"
            f"\n  No state_spec EF@10: {f.ef_at_10:.4f} [{f.ef_ci_lower:.4f}, {f.ef_ci_upper:.4f}]"
        )
        if f.ef_at_10 > 1.0:
            print("  --> Enrichment SURVIVES without state_specificity")
        else:
            print("  --> Enrichment LOST without state_specificity")

    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run scoring ablation analysis on state-aware candidates",
    )
    parser.add_argument(
        "--pool",
        type=str,
        default=None,
        help="Path to state_aware_pool.json (default: auto-detect or generate)",
    )
    parser.add_argument(
        "--cutoff",
        type=int,
        default=2010,
        help="Temporal cutoff year for future drugs (default: 2010)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="Similarity threshold for EF hit definition (default: 0.4)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="K for EF@K (default: 10)",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
        help="Number of bootstrap resamples (default: 10000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/evaluation",
        help="Output directory (default: artifacts/evaluation)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Resolve pool path
    pool_path = Path(args.pool) if args.pool else None
    if pool_path is None:
        default_path = Path("artifacts/ranking/state_aware_pool.json")
        if default_path.exists():
            pool_path = default_path

    # Load candidates
    pool = _load_or_generate_pool(pool_path)

    # Get future drugs
    future_drugs = get_future_drugs(args.cutoff)
    logger.info(
        "Cutoff %d: %d future drugs", args.cutoff, len(future_drugs)
    )

    if not future_drugs:
        logger.error(
            "No future drugs for cutoff %d -- cannot compute enrichment",
            args.cutoff,
        )
        return

    # Run ablation battery
    results = run_ablation_battery(
        candidates=pool.candidates,
        future_drugs=future_drugs,
        base_weights=DEFAULT_WEIGHTS,
        threshold=args.threshold,
        top_k=args.top_k,
        n_bootstrap=args.n_bootstrap,
    )

    # Print summary
    _print_summary(results)

    # Save artifact
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    battery = AblationBattery(
        results=results,
        base_weights=DEFAULT_WEIGHTS,
        generated_at=datetime.now(timezone.utc).isoformat(),
        notes=(
            f"Scoring ablation analysis. Cutoff={args.cutoff}, "
            f"threshold={args.threshold}, top_k={args.top_k}, "
            f"n_bootstrap={args.n_bootstrap}."
        ),
    )

    out_path = output_dir / "scoring_ablation.json"
    save_json(battery.model_dump(mode="json"), out_path)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
