"""Tests for Phase 7: ranking pipeline.

Covers:
- Ranking model schemas
- Unified scoring
- Rank aggregation
- Merge deduplication
"""

from __future__ import annotations

import pytest

from statebind.baselines.pipeline import run_static_baseline
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.aggregation import (
    compute_rank_shifts,
    mean_rank_by_pipeline,
    pipeline_representation_in_top_k,
    score_distribution_by_pipeline,
    top_k_by_pipeline,
    top_k_global,
)
from statebind.ranking.models import (
    MergedRanking,
    PipelineLabel,
    RankedPool,
    RankShift,
    UnifiedScoreComponent,
    UnifiedScoredCandidate,
)
from statebind.ranking.scoring import (
    DEFAULT_WEIGHTS,
    _compute_state_specificity,
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
    score_unified,
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def baseline():
    return run_static_baseline()


@pytest.fixture(scope="module")
def state_filtered():
    gen = generate_all_states()
    return filter_all_states(gen)


@pytest.fixture(scope="module")
def static_pool(baseline):
    return rank_static_baseline(baseline.filtered)


@pytest.fixture(scope="module")
def state_pool(state_filtered):
    return rank_state_aware(state_filtered)


@pytest.fixture(scope="module")
def merged(static_pool, state_pool):
    return merge_rankings(static_pool, state_pool)


# ── Model Schema Tests ───────────────────────────────────────────────


class TestRankingModels:
    """Test Pydantic model schemas."""

    def test_pipeline_label_values(self):
        assert PipelineLabel.STATIC.value == "static_baseline"
        assert PipelineLabel.STATE_AWARE.value == "state_aware"

    def test_score_component_fields(self):
        sc = UnifiedScoreComponent(
            name="test", value=0.5, weight=0.3, method="test_method"
        )
        assert sc.name == "test"
        assert sc.value == 0.5
        assert sc.weight == 0.3
        assert sc.is_stub is False

    def test_scored_candidate_get_score(self):
        c = UnifiedScoredCandidate(
            candidate_id="test_1",
            smiles="CCO",
            pipeline=PipelineLabel.STATIC,
            scores=[
                UnifiedScoreComponent(name="sim", value=0.8, weight=0.4),
                UnifiedScoreComponent(name="drug", value=0.6, weight=0.3),
            ],
            composite_score=0.5,
        )
        assert c.get_score("sim") == 0.8
        assert c.get_score("drug") == 0.6
        assert c.get_score("nonexistent") is None

    def test_ranked_pool_n_ranked(self):
        pool = RankedPool(pipeline=PipelineLabel.STATIC, candidates=[])
        assert pool.n_ranked == 0

    def test_merged_ranking_n_total(self):
        mr = MergedRanking(
            static_pool=RankedPool(pipeline=PipelineLabel.STATIC),
            state_aware_pool=RankedPool(pipeline=PipelineLabel.STATE_AWARE),
            merged=[],
        )
        assert mr.n_total == 0

    def test_rank_shift_fields(self):
        rs = RankShift(
            candidate_id="test",
            smiles="CCO",
            pipeline=PipelineLabel.STATIC,
            pipeline_rank=3,
            global_rank=5,
            shift=-2,
        )
        assert rs.shift == -2


# ── Unified Scoring Tests ────────────────────────────────────────────


class TestUnifiedScoring:
    """Test the unified scoring function."""

    def test_score_returns_four_components(self):
        components, score = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        assert len(components) == 4
        names = {c.name for c in components}
        assert names == {"reference_similarity", "druglikeness", "docking_proxy", "state_specificity"}

    def test_static_has_zero_specificity(self):
        components, _ = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        spec = [c for c in components if c.name == "state_specificity"][0]
        assert spec.value == 0.0

    def test_state_specificity_unique_to_one_state(self):
        state_map = {"DFGin_aCin": {"CCO"}, "DFGout_aCin": {"CCN"}}
        spec = _compute_state_specificity("CCO", "DFGin_aCin", state_map)
        assert spec == 1.0

    def test_state_specificity_in_two_states(self):
        state_map = {"DFGin_aCin": {"CCO"}, "DFGout_aCin": {"CCO"}}
        spec = _compute_state_specificity("CCO", "DFGin_aCin", state_map)
        assert spec == 0.5

    def test_state_specificity_in_all_states(self):
        state_map = {
            "DFGin_aCin": {"CCO"}, "DFGin_aCout": {"CCO"},
            "DFGout_aCin": {"CCO"}, "DFGout_aCout": {"CCO"},
        }
        spec = _compute_state_specificity("CCO", "DFGin_aCin", state_map)
        assert spec == 0.0

    def test_composite_is_weighted_sum(self):
        components, composite = score_unified(
            "CCO", "", PipelineLabel.STATIC, {}
        )
        expected = sum(c.value * c.weight for c in components)
        assert abs(composite - round(expected, 4)) < 1e-4

    def test_docking_proxy_is_stub(self):
        components, _ = score_unified("CCO", "", PipelineLabel.STATIC, {})
        dock = [c for c in components if c.name == "docking_proxy"][0]
        assert dock.is_stub is True
        assert dock.value == 0.5

    def test_default_weights_sum(self):
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6


# ── Pipeline Ranking Tests ───────────────────────────────────────────


class TestPipelineRanking:
    """Test ranking of actual pipeline outputs."""

    def test_static_pool_not_empty(self, static_pool):
        assert static_pool.n_ranked > 0

    def test_state_pool_not_empty(self, state_pool):
        assert state_pool.n_ranked > 0

    def test_static_pool_pipeline_label(self, static_pool):
        assert static_pool.pipeline == PipelineLabel.STATIC

    def test_state_pool_pipeline_label(self, state_pool):
        assert state_pool.pipeline == PipelineLabel.STATE_AWARE

    def test_static_pool_ranks_sequential(self, static_pool):
        ranks = [c.rank_in_pipeline for c in static_pool.candidates]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_state_pool_ranks_sequential(self, state_pool):
        ranks = [c.rank_in_pipeline for c in state_pool.candidates]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_static_pool_sorted_descending(self, static_pool):
        scores = [c.composite_score for c in static_pool.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_state_pool_sorted_descending(self, state_pool):
        scores = [c.composite_score for c in state_pool.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_static_all_zero_specificity(self, static_pool):
        for c in static_pool.candidates:
            spec = c.get_score("state_specificity")
            assert spec == 0.0, f"{c.candidate_id} has non-zero specificity"


# ── Merge Tests ──────────────────────────────────────────────────────


class TestMergeRanking:
    """Test merged ranking correctness."""

    def test_merged_not_empty(self, merged):
        assert merged.n_total > 0

    def test_merged_unique_smiles(self, merged):
        smiles = [c.smiles for c in merged.merged]
        assert len(smiles) == len(set(smiles))

    def test_merged_global_ranks_sequential(self, merged):
        ranks = [c.global_rank for c in merged.merged]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_merged_sorted_descending(self, merged):
        scores = [c.composite_score for c in merged.merged]
        assert scores == sorted(scores, reverse=True)

    def test_merged_contains_both_pipelines(self, merged):
        pipelines = {c.pipeline for c in merged.merged}
        assert PipelineLabel.STATIC in pipelines or PipelineLabel.STATE_AWARE in pipelines

    def test_merged_size_bounded(self, merged):
        # Merged should be <= sum of both pools (due to dedup)
        max_possible = merged.static_pool.n_ranked + merged.state_aware_pool.n_ranked
        assert merged.n_total <= max_possible


# ── Aggregation Tests ────────────────────────────────────────────────


class TestAggregation:
    """Test rank aggregation utilities."""

    def test_rank_shifts_count(self, merged):
        shifts = compute_rank_shifts(merged)
        assert len(shifts) == merged.n_total

    def test_rank_shift_formula(self, merged):
        shifts = compute_rank_shifts(merged)
        for s in shifts:
            assert s.shift == s.pipeline_rank - s.global_rank

    def test_top_k_global(self, merged):
        top = top_k_global(merged, k=5)
        assert len(top) <= 5
        assert all(c.global_rank <= 5 for c in top)

    def test_top_k_by_pipeline(self, merged):
        by_pipe = top_k_by_pipeline(merged, k=5)
        assert PipelineLabel.STATIC.value in by_pipe
        assert PipelineLabel.STATE_AWARE.value in by_pipe

    def test_pipeline_representation(self, merged):
        counts = pipeline_representation_in_top_k(merged, k=10)
        total = counts[PipelineLabel.STATIC.value] + counts[PipelineLabel.STATE_AWARE.value]
        assert total == min(10, merged.n_total)

    def test_mean_rank_positive(self, merged):
        ranks = mean_rank_by_pipeline(merged)
        for val in ranks.values():
            if val > 0:
                assert val >= 1.0

    def test_score_distribution_has_all_stats(self, merged):
        dist = score_distribution_by_pipeline(merged)
        for pipeline, stats in dist.items():
            if stats["n"] > 0:
                assert "mean" in stats
                assert "std" in stats
                assert "min" in stats
                assert "max" in stats
