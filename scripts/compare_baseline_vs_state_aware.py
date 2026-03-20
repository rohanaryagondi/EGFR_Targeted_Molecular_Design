#!/usr/bin/env python3
"""Phase 7 — Step 2: Head-to-head comparison.

Reads the merged ranking from Step 1 and runs the full
comparison suite: overlap, diversity, scores, top-K, novelty.

Outputs:
  artifacts/ranking/comparison.json
  artifacts/ranking/figures/*.txt
"""

from __future__ import annotations

import json
from pathlib import Path

from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.comparison import run_full_comparison
from statebind.evaluation.figures import generate_all_figures
from statebind.evaluation.tables import (
    novelty_by_state_table,
    novelty_by_strategy_table,
    rank_shift_table,
    summary_table,
    top_candidates_table,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)


def main() -> None:
    output_dir = Path("artifacts/ranking")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ── Reproduce pipelines (ensures consistency) ────────────────────
    print("Running both pipelines for comparison...")
    baseline = run_static_baseline()
    generation = generate_all_states()
    filtered = filter_all_states(generation)

    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    merged = merge_rankings(static_pool, state_pool)

    # ── Run comparison ───────────────────────────────────────────────
    print("\nRunning comparison suite...")
    result = run_full_comparison(merged, top_k=10)

    # ── Generate tables ──────────────────────────────────────────────
    tables = {
        "summary": summary_table(result),
        "top_10_global": top_candidates_table(merged, k=10),
        "rank_shifts": rank_shift_table(merged, top_n=10),
        "novelty_by_strategy": novelty_by_strategy_table(result),
        "novelty_by_state": novelty_by_state_table(result),
    }

    # ── Generate figures ─────────────────────────────────────────────
    figures = generate_all_figures(result, merged, output_dir=fig_dir)

    # ── Write comparison artifact ────────────────────────────────────
    comparison_data = {
        "overlap": {
            "static_total": result.overlap.static_total,
            "state_aware_total": result.overlap.state_aware_total,
            "shared": result.overlap.shared,
            "static_only": result.overlap.static_only,
            "state_aware_only": result.overlap.state_aware_only,
            "jaccard": result.overlap.jaccard,
        },
        "diversity": {
            "static": round(result.diversity.static.diversity_score, 4),
            "state_aware": round(result.diversity.state_aware.diversity_score, 4),
            "delta": result.diversity.delta_diversity,
        },
        "scores": {
            "static": result.scores.static_stats,
            "state_aware": result.scores.state_aware_stats,
            "delta_mean": result.scores.delta_mean,
        },
        "top_k": {
            "k": result.top_k.k,
            "static_count": result.top_k.static_count,
            "state_aware_count": result.top_k.state_aware_count,
        },
        "novelty": {
            "n_novel": result.novelty.n_novel,
            "by_strategy": result.novelty.novel_strategies,
            "by_state": result.novelty.novel_states,
        },
        "mean_ranks": result.mean_ranks,
        "tables": tables,
    }

    path = output_dir / "comparison.json"
    with open(path, "w") as f:
        json.dump(comparison_data, f, indent=2, default=str)
    print(f"Wrote {path}")

    # ── Print summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    print("\n── Head-to-Head ──")
    for row in tables["summary"]:
        print(f"  {row['metric']:<40} Static={row['static_baseline']:<10} "
              f"State={row['state_aware']:<10} Delta={row['delta']}")

    for name, fig in figures.items():
        print(f"\n{fig}")

    print(f"\nArtifacts in {output_dir}/")
    print(f"Figures in {fig_dir}/")


if __name__ == "__main__":
    main()
