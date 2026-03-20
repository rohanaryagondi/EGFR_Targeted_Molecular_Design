"""Summary table generation for the comparative evaluation.

All tables are returned as lists-of-dicts for easy serialization
to markdown, CSV, or JSON.
"""

from __future__ import annotations

from statebind.evaluation.comparison import ComparativeResult
from statebind.ranking.aggregation import (
    compute_rank_shifts,
    top_k_by_pipeline,
    top_k_global,
)
from statebind.ranking.models import MergedRanking, PipelineLabel


def summary_table(result: ComparativeResult) -> list[dict[str, object]]:
    """Head-to-head summary table (one row per metric)."""
    rows: list[dict[str, object]] = [
        {
            "metric": "Candidates (unique SMILES)",
            "static_baseline": result.static_n,
            "state_aware": result.state_aware_n,
            "delta": result.state_aware_n - result.static_n,
        },
        {
            "metric": "Diversity (1 - mean Tanimoto)",
            "static_baseline": round(result.diversity.static.diversity_score, 4),
            "state_aware": round(result.diversity.state_aware.diversity_score, 4),
            "delta": result.diversity.delta_diversity,
        },
        {
            "metric": "Mean composite score",
            "static_baseline": result.scores.static_stats.get("mean", 0.0),
            "state_aware": result.scores.state_aware_stats.get("mean", 0.0),
            "delta": result.scores.delta_mean,
        },
        {
            "metric": "Max composite score",
            "static_baseline": result.scores.static_stats.get("max", 0.0),
            "state_aware": result.scores.state_aware_stats.get("max", 0.0),
            "delta": round(
                result.scores.state_aware_stats.get("max", 0.0)
                - result.scores.static_stats.get("max", 0.0),
                4,
            ),
        },
        {
            "metric": f"In global top-{result.top_k.k}",
            "static_baseline": result.top_k.static_count,
            "state_aware": result.top_k.state_aware_count,
            "delta": result.top_k.state_aware_count - result.top_k.static_count,
        },
        {
            "metric": "Novel candidates (not in other pipeline)",
            "static_baseline": result.overlap.static_only,
            "state_aware": result.overlap.state_aware_only,
            "delta": result.overlap.state_aware_only - result.overlap.static_only,
        },
        {
            "metric": "SMILES overlap (shared)",
            "static_baseline": result.overlap.shared,
            "state_aware": result.overlap.shared,
            "delta": 0,
        },
        {
            "metric": "Mean global rank",
            "static_baseline": round(result.mean_ranks.get(PipelineLabel.STATIC.value, 0.0), 1),
            "state_aware": round(result.mean_ranks.get(PipelineLabel.STATE_AWARE.value, 0.0), 1),
            "delta": round(
                result.mean_ranks.get(PipelineLabel.STATIC.value, 0.0)
                - result.mean_ranks.get(PipelineLabel.STATE_AWARE.value, 0.0),
                1,
            ),
        },
    ]
    return rows


def top_candidates_table(
    merged: MergedRanking,
    k: int = 10,
) -> list[dict[str, object]]:
    """Global top-K candidates table."""
    top = top_k_global(merged, k)
    return [
        {
            "global_rank": c.global_rank,
            "pipeline": c.pipeline.value,
            "smiles": c.smiles,
            "composite_score": c.composite_score,
            "ref_similarity": c.get_score("reference_similarity") or 0.0,
            "druglikeness": c.get_score("druglikeness") or 0.0,
            "state_specificity": c.get_score("state_specificity") or 0.0,
            "target_state": c.target_state or "—",
            "strategy": c.strategy or "—",
        }
        for c in top
    ]


def per_pipeline_top_table(
    merged: MergedRanking,
    k: int = 5,
) -> dict[str, list[dict[str, object]]]:
    """Top-K from each pipeline's own ranking."""
    by_pipeline = top_k_by_pipeline(merged, k)
    result: dict[str, list[dict[str, object]]] = {}
    for pipeline, candidates in by_pipeline.items():
        result[pipeline] = [
            {
                "pipeline_rank": c.rank_in_pipeline,
                "global_rank": c.global_rank,
                "smiles": c.smiles,
                "composite_score": c.composite_score,
                "target_state": c.target_state or "—",
                "strategy": c.strategy or "—",
            }
            for c in candidates
        ]
    return result


def rank_shift_table(
    merged: MergedRanking,
    top_n: int = 10,
) -> dict[str, list[dict[str, object]]]:
    """Most promoted and most demoted candidates."""
    shifts = compute_rank_shifts(merged)

    promoted = sorted(shifts, key=lambda s: s.shift, reverse=True)[:top_n]
    demoted = sorted(shifts, key=lambda s: s.shift)[:top_n]

    def _to_row(s):
        return {
            "candidate_id": s.candidate_id,
            "smiles": s.smiles[:60] + ("..." if len(s.smiles) > 60 else ""),
            "pipeline": s.pipeline.value,
            "pipeline_rank": s.pipeline_rank,
            "global_rank": s.global_rank,
            "shift": s.shift,
            "composite_score": s.composite_score,
        }

    return {
        "most_promoted": [_to_row(s) for s in promoted],
        "most_demoted": [_to_row(s) for s in demoted],
    }


def novelty_by_strategy_table(
    result: ComparativeResult,
) -> list[dict[str, object]]:
    """Novel state-aware candidates broken down by strategy."""
    rows: list[dict[str, object]] = []
    for strategy, count in sorted(
        result.novelty.novel_strategies.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        rows.append({"strategy": strategy, "n_novel": count})
    return rows


def novelty_by_state_table(
    result: ComparativeResult,
) -> list[dict[str, object]]:
    """Novel state-aware candidates broken down by target state."""
    rows: list[dict[str, object]] = []
    for state, count in sorted(
        result.novelty.novel_states.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        rows.append({"state": state, "n_novel": count})
    return rows
