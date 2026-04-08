"""Head-to-head comparison between static baseline and state-aware pipeline.

Every metric is computed for both pipelines under identical conditions.
No cherry-picking: all candidates are included, not a selected subset.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.generation.diversity import DiversityMetrics, compute_diversity
from statebind.ranking.aggregation import (
    mean_rank_by_pipeline,
    pipeline_representation_in_top_k,
    score_distribution_by_pipeline,
)
from statebind.ranking.models import (
    MergedRanking,
    PipelineLabel,
    UnifiedScoredCandidate,
)


@dataclass
class OverlapAnalysis:
    """SMILES overlap between pipelines."""

    static_total: int = 0
    state_aware_total: int = 0
    shared: int = 0
    static_only: int = 0
    state_aware_only: int = 0
    jaccard: float = 0.0


@dataclass
class DiversityComparison:
    """Diversity metrics side-by-side."""

    static: DiversityMetrics = field(default_factory=DiversityMetrics)
    state_aware: DiversityMetrics = field(default_factory=DiversityMetrics)
    delta_diversity: float = 0.0  # state_aware - static


@dataclass
class ScoreComparison:
    """Score distribution comparison."""

    static_stats: dict[str, float] = field(default_factory=dict)
    state_aware_stats: dict[str, float] = field(default_factory=dict)
    delta_mean: float = 0.0  # state_aware_mean - static_mean


@dataclass
class TopKComparison:
    """Who dominates the top-K?"""

    k: int = 10
    static_count: int = 0
    state_aware_count: int = 0
    state_aware_fraction: float = 0.0


@dataclass
class NoveltyAnalysis:
    """New candidates discovered by state-aware pipeline."""

    n_novel: int = 0
    novel_smiles: list[str] = field(default_factory=list)
    novel_strategies: dict[str, int] = field(default_factory=dict)
    novel_states: dict[str, int] = field(default_factory=dict)


@dataclass
class ComparativeResult:
    """Complete comparison between pipelines."""

    overlap: OverlapAnalysis = field(default_factory=OverlapAnalysis)
    diversity: DiversityComparison = field(default_factory=DiversityComparison)
    scores: ScoreComparison = field(default_factory=ScoreComparison)
    top_k: TopKComparison = field(default_factory=TopKComparison)
    novelty: NoveltyAnalysis = field(default_factory=NoveltyAnalysis)
    mean_ranks: dict[str, float] = field(default_factory=dict)
    static_n: int = 0
    state_aware_n: int = 0
    # WS03: statistical testing results (populated when run_statistics=True)
    statistical_tests: list = field(default_factory=list)
    sensitivity: object = field(default=None)
    # WS12: Pareto analysis results (always populated when numpy available)
    pareto: object = field(default=None)
    # WS13: Retrospective validation results (populated when retrospective data available)
    retrospective: object = field(default=None)


def compute_overlap(merged: MergedRanking) -> OverlapAnalysis:
    """Compute SMILES overlap between the two pipelines."""
    static_smiles = {c.smiles for c in merged.static_pool.candidates}
    state_smiles = {c.smiles for c in merged.state_aware_pool.candidates}

    shared = static_smiles & state_smiles
    union = static_smiles | state_smiles
    jaccard = len(shared) / len(union) if union else 0.0

    return OverlapAnalysis(
        static_total=len(static_smiles),
        state_aware_total=len(state_smiles),
        shared=len(shared),
        static_only=len(static_smiles - state_smiles),
        state_aware_only=len(state_smiles - static_smiles),
        jaccard=round(jaccard, 4),
    )


def compute_diversity_comparison(merged: MergedRanking) -> DiversityComparison:
    """Compare diversity of both candidate pools."""
    static_smiles = [c.smiles for c in merged.static_pool.candidates]
    state_smiles = [c.smiles for c in merged.state_aware_pool.candidates]

    static_div = compute_diversity(static_smiles)
    state_div = compute_diversity(state_smiles)

    return DiversityComparison(
        static=static_div,
        state_aware=state_div,
        delta_diversity=round(
            state_div.diversity_score - static_div.diversity_score, 4
        ),
    )


def compute_score_comparison(merged: MergedRanking) -> ScoreComparison:
    """Compare score distributions."""
    dist = score_distribution_by_pipeline(merged)
    static_stats = dist.get(PipelineLabel.STATIC.value, {})
    state_stats = dist.get(PipelineLabel.STATE_AWARE.value, {})

    delta = state_stats.get("mean", 0.0) - static_stats.get("mean", 0.0)
    return ScoreComparison(
        static_stats=static_stats,
        state_aware_stats=state_stats,
        delta_mean=round(delta, 4),
    )


def compute_top_k_comparison(merged: MergedRanking, k: int = 10) -> TopKComparison:
    """Who dominates the global top-K?"""
    counts = pipeline_representation_in_top_k(merged, k)
    state_count = counts.get(PipelineLabel.STATE_AWARE.value, 0)
    static_count = counts.get(PipelineLabel.STATIC.value, 0)

    return TopKComparison(
        k=k,
        static_count=static_count,
        state_aware_count=state_count,
        state_aware_fraction=round(state_count / max(k, 1), 4),
    )


def compute_novelty(merged: MergedRanking) -> NoveltyAnalysis:
    """Identify candidates unique to state-aware pipeline."""
    static_smiles = {c.smiles for c in merged.static_pool.candidates}

    novel: list[UnifiedScoredCandidate] = []
    for c in merged.state_aware_pool.candidates:
        if c.smiles not in static_smiles:
            novel.append(c)

    strategy_counts: dict[str, int] = {}
    state_counts: dict[str, int] = {}
    for c in novel:
        strategy_counts[c.strategy] = strategy_counts.get(c.strategy, 0) + 1
        if c.target_state:
            state_counts[c.target_state] = state_counts.get(c.target_state, 0) + 1

    return NoveltyAnalysis(
        n_novel=len(novel),
        novel_smiles=[c.smiles for c in novel],
        novel_strategies=strategy_counts,
        novel_states=state_counts,
    )


def run_full_comparison(
    merged: MergedRanking,
    top_k: int = 10,
    run_statistics: bool = False,
) -> ComparativeResult:
    """Run the complete comparison suite.

    When run_statistics=True, also runs Mann-Whitney U, bootstrap CI,
    and weight sensitivity analysis (requires numpy; scipy optional).
    """
    overlap = compute_overlap(merged)
    diversity = compute_diversity_comparison(merged)
    scores = compute_score_comparison(merged)
    top_k_comp = compute_top_k_comparison(merged, k=top_k)
    novelty = compute_novelty(merged)
    ranks = mean_rank_by_pipeline(merged)

    statistical_tests: list = []
    sensitivity_result = None

    if run_statistics:
        try:
            from statebind.evaluation.statistics import mann_whitney_u

            # Extract composite scores per pipeline
            static_scores = [
                c.composite_score for c in merged.static_pool.candidates
            ]
            state_scores = [
                c.composite_score for c in merged.state_aware_pool.candidates
            ]

            if static_scores and state_scores:
                mw_result = mann_whitney_u(static_scores, state_scores)
                statistical_tests.append(mw_result)
        except ImportError:
            pass

        try:
            from statebind.evaluation.sensitivity import (
                run_ablation_analysis,
                run_weight_sensitivity,
            )

            sens = run_weight_sensitivity(merged)
            ablation = run_ablation_analysis(merged)
            # Attach ablation results to sensitivity summary
            sens.results.extend(ablation)
            sensitivity_result = sens
        except ImportError:
            pass

    # WS12: Pareto analysis always runs (only needs numpy, a core dep)
    pareto_result = None
    try:
        from statebind.evaluation.pareto_comparison import run_pareto_comparison

        pareto_result = run_pareto_comparison(merged)
    except ImportError:
        pass

    return ComparativeResult(
        overlap=overlap,
        diversity=diversity,
        scores=scores,
        top_k=top_k_comp,
        novelty=novelty,
        mean_ranks=ranks,
        static_n=merged.static_pool.n_ranked,
        state_aware_n=merged.state_aware_pool.n_ranked,
        statistical_tests=statistical_tests,
        sensitivity=sensitivity_result,
        pareto=pareto_result,
    )
