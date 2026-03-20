"""Rank aggregation and rank-shift analysis.

Compares pipeline-local ranks to global (merged) ranks to identify
candidates that are promoted or demoted by the unified comparison.
"""

from __future__ import annotations

from statebind.ranking.models import (
    MergedRanking,
    PipelineLabel,
    RankShift,
    UnifiedScoredCandidate,
)


def compute_rank_shifts(merged: MergedRanking) -> list[RankShift]:
    """Compute rank shifts for every candidate in the merged ranking.

    shift = pipeline_rank - global_rank
      positive → candidate was promoted in global ranking
      negative → candidate was demoted
    """
    shifts: list[RankShift] = []

    for c in merged.merged:
        shifts.append(RankShift(
            candidate_id=c.candidate_id,
            smiles=c.smiles,
            pipeline=c.pipeline,
            pipeline_rank=c.rank_in_pipeline,
            global_rank=c.global_rank,
            shift=c.rank_in_pipeline - c.global_rank,
            composite_score=c.composite_score,
        ))

    return shifts


def top_k_by_pipeline(
    merged: MergedRanking,
    k: int = 10,
) -> dict[str, list[UnifiedScoredCandidate]]:
    """Extract top-K candidates from each pipeline's own ranking."""
    return {
        PipelineLabel.STATIC.value: merged.static_pool.candidates[:k],
        PipelineLabel.STATE_AWARE.value: merged.state_aware_pool.candidates[:k],
    }


def top_k_global(
    merged: MergedRanking,
    k: int = 10,
) -> list[UnifiedScoredCandidate]:
    """Extract top-K candidates from the merged global ranking."""
    return merged.merged[:k]


def pipeline_representation_in_top_k(
    merged: MergedRanking,
    k: int = 10,
) -> dict[str, int]:
    """Count how many of the global top-K come from each pipeline."""
    top = merged.merged[:k]
    counts: dict[str, int] = {
        PipelineLabel.STATIC.value: 0,
        PipelineLabel.STATE_AWARE.value: 0,
    }
    for c in top:
        counts[c.pipeline.value] += 1
    return counts


def mean_rank_by_pipeline(merged: MergedRanking) -> dict[str, float]:
    """Mean global rank of candidates from each pipeline."""
    ranks: dict[str, list[int]] = {
        PipelineLabel.STATIC.value: [],
        PipelineLabel.STATE_AWARE.value: [],
    }
    for c in merged.merged:
        ranks[c.pipeline.value].append(c.global_rank)

    return {
        pipeline: (sum(r) / len(r) if r else 0.0)
        for pipeline, r in ranks.items()
    }


def score_distribution_by_pipeline(
    merged: MergedRanking,
) -> dict[str, dict[str, float]]:
    """Compute score statistics per pipeline."""
    import statistics

    scores: dict[str, list[float]] = {
        PipelineLabel.STATIC.value: [],
        PipelineLabel.STATE_AWARE.value: [],
    }
    for c in merged.merged:
        scores[c.pipeline.value].append(c.composite_score)

    result: dict[str, dict[str, float]] = {}
    for pipeline, vals in scores.items():
        if not vals:
            result[pipeline] = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "n": 0}
            continue
        result[pipeline] = {
            "mean": round(statistics.mean(vals), 4),
            "std": round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "n": len(vals),
        }
    return result
