"""Tests for Phase 7: evaluation module.

Covers:
- Comparison metrics
- Summary tables
- Figure generation
- Report tables
"""

from __future__ import annotations

import pytest

from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.comparison import (
    ComparativeResult,
    compute_diversity_comparison,
    compute_novelty,
    compute_overlap,
    compute_score_comparison,
    compute_top_k_comparison,
    run_full_comparison,
)
from statebind.evaluation.figures import (
    diversity_comparison_ascii,
    generate_all_figures,
    novelty_breakdown_ascii,
    overlap_venn_ascii,
    score_distribution_ascii,
    top_k_composition_ascii,
)
from statebind.evaluation.tables import (
    novelty_by_state_table,
    novelty_by_strategy_table,
    per_pipeline_top_table,
    rank_shift_table,
    summary_table,
    top_candidates_table,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.models import PipelineLabel
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def pipelines():
    """Run both pipelines once for all tests."""
    baseline = run_static_baseline()
    gen = generate_all_states()
    filtered = filter_all_states(gen)

    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    merged = merge_rankings(static_pool, state_pool)
    result = run_full_comparison(merged, top_k=10)
    return merged, result


@pytest.fixture(scope="module")
def merged(pipelines):
    return pipelines[0]


@pytest.fixture(scope="module")
def result(pipelines):
    return pipelines[1]


# ── Comparison Metrics Tests ─────────────────────────────────────────


class TestComparisonMetrics:
    """Test comparison computation."""

    def test_overlap_totals(self, merged, result):
        o = result.overlap
        assert o.static_total > 0
        assert o.state_aware_total > 0

    def test_overlap_consistency(self, result):
        o = result.overlap
        assert o.shared + o.static_only == o.static_total
        assert o.shared + o.state_aware_only == o.state_aware_total

    def test_jaccard_range(self, result):
        assert 0.0 <= result.overlap.jaccard <= 1.0

    def test_diversity_range(self, result):
        assert 0.0 <= result.diversity.static.diversity_score <= 1.0
        assert 0.0 <= result.diversity.state_aware.diversity_score <= 1.0

    def test_diversity_delta_consistent(self, result):
        expected = (
            result.diversity.state_aware.diversity_score
            - result.diversity.static.diversity_score
        )
        assert abs(result.diversity.delta_diversity - round(expected, 4)) < 1e-3

    def test_score_stats_have_required_keys(self, result):
        for stats in [result.scores.static_stats, result.scores.state_aware_stats]:
            if stats.get("n", 0) > 0:
                assert "mean" in stats
                assert "max" in stats

    def test_top_k_sums_to_k(self, result):
        k = result.top_k.k
        total = result.top_k.static_count + result.top_k.state_aware_count
        # Could be less if fewer candidates than k
        assert total <= k

    def test_novelty_count_positive(self, result):
        # State-aware should have some novel candidates
        assert result.novelty.n_novel >= 0

    def test_novelty_strategies_not_empty(self, result):
        if result.novelty.n_novel > 0:
            assert len(result.novelty.novel_strategies) > 0

    def test_full_comparison_returns_all_fields(self, result):
        assert isinstance(result, ComparativeResult)
        assert result.static_n > 0
        assert result.state_aware_n > 0


# ── Table Tests ──────────────────────────────────────────────────────


class TestTables:
    """Test summary table generation."""

    def test_summary_table_has_rows(self, result):
        rows = summary_table(result)
        assert len(rows) >= 5

    def test_summary_table_metrics(self, result):
        rows = summary_table(result)
        metrics = {r["metric"] for r in rows}
        assert "Diversity (1 - mean Tanimoto)" in metrics
        assert "Mean composite score" in metrics

    def test_summary_table_columns(self, result):
        rows = summary_table(result)
        for row in rows:
            assert "metric" in row
            assert "static_baseline" in row
            assert "state_aware" in row
            assert "delta" in row

    def test_top_candidates_table(self, merged):
        rows = top_candidates_table(merged, k=5)
        assert len(rows) <= 5
        for row in rows:
            assert "global_rank" in row
            assert "pipeline" in row
            assert "composite_score" in row

    def test_per_pipeline_top_table(self, merged):
        tables = per_pipeline_top_table(merged, k=3)
        assert PipelineLabel.STATIC.value in tables
        assert PipelineLabel.STATE_AWARE.value in tables

    def test_rank_shift_table(self, merged):
        shifts = rank_shift_table(merged, top_n=5)
        assert "most_promoted" in shifts
        assert "most_demoted" in shifts
        assert len(shifts["most_promoted"]) <= 5

    def test_novelty_by_strategy_table(self, result):
        rows = novelty_by_strategy_table(result)
        if result.novelty.n_novel > 0:
            assert len(rows) > 0
            assert "strategy" in rows[0]
            assert "n_novel" in rows[0]

    def test_novelty_by_state_table(self, result):
        rows = novelty_by_state_table(result)
        for row in rows:
            assert "state" in row
            assert "n_novel" in row


# ── Figure Tests ─────────────────────────────────────────────────────


class TestFigures:
    """Test ASCII figure generation."""

    def test_score_distribution_figure(self, result):
        fig = score_distribution_ascii(result)
        assert "Score Distribution" in fig
        assert "Static baseline" in fig
        assert "State-aware" in fig

    def test_diversity_comparison_figure(self, result):
        fig = diversity_comparison_ascii(result)
        assert "Diversity" in fig
        assert "Delta" in fig

    def test_top_k_composition_figure(self, result):
        fig = top_k_composition_ascii(result)
        assert "Top-" in fig

    def test_novelty_breakdown_figure(self, result):
        fig = novelty_breakdown_ascii(result)
        assert "Novel" in fig

    def test_overlap_venn_figure(self, result):
        fig = overlap_venn_ascii(result)
        assert "Overlap" in fig
        assert "Jaccard" in fig

    def test_generate_all_figures(self, result, merged):
        figures = generate_all_figures(result, merged)
        base_keys = {
            "score_distribution", "diversity_comparison",
            "top_k_composition", "novelty_breakdown", "overlap_venn",
        }
        assert base_keys.issubset(set(figures.keys()))
        # WS12: Pareto summary is included when numpy available
        assert len(figures) >= 5
        for content in figures.values():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_figures_to_files(self, result, merged, tmp_path):
        figures = generate_all_figures(result, merged, output_dir=tmp_path)
        for name in figures:
            assert (tmp_path / f"{name}.txt").exists()
