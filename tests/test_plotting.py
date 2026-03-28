"""Tests for WS05: matplotlib visualization (evaluation/plotting.py).

Covers:
- Figure generation for each plot type
- File saving and orchestrator
- Edge cases (empty data, missing deps)
- Fallback when matplotlib is unavailable
- Style checks (labels, titles)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.comparison import (
    ComparativeResult,
    NoveltyAnalysis,
    run_full_comparison,
)
from statebind.evaluation.plotting import HAS_MATPLOTLIB
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)

# Skip entire module when matplotlib is not available (except fallback test)
_requires_mpl = pytest.mark.skipif(
    not HAS_MATPLOTLIB, reason="matplotlib not installed ([science] extras)"
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def pipelines():
    """Run both pipelines once; shared by all tests in this module."""
    baseline = run_static_baseline()
    gen = generate_all_states()
    filtered = filter_all_states(gen)

    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    merged = merge_rankings(static_pool, state_pool)
    result = run_full_comparison(merged, top_k=10)
    result_with_stats = run_full_comparison(merged, top_k=10, run_statistics=True)
    return merged, result, result_with_stats


@pytest.fixture(scope="module")
def merged(pipelines):
    return pipelines[0]


@pytest.fixture(scope="module")
def result(pipelines):
    return pipelines[1]


@pytest.fixture(scope="module")
def result_with_stats(pipelines):
    return pipelines[2]


# ── Figure Generation Tests ──────────────────────────────────────────


@_requires_mpl
class TestPlotGeneration:
    """Verify each plot function returns a matplotlib Figure."""

    def test_score_distributions_returns_figure(self, result):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_score_distributions

        fig = plot_score_distributions(result)
        assert isinstance(fig, Figure)

    def test_score_components_heatmap_returns_figure(self, merged):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_score_components_heatmap

        fig = plot_score_components_heatmap(merged, top_n=10)
        assert isinstance(fig, Figure)

    def test_diversity_radar_returns_figure(self, result):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_diversity_radar

        fig = plot_diversity_radar(result)
        assert isinstance(fig, Figure)

    def test_rank_shift_waterfall_returns_figure(self, merged):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_rank_shift_waterfall

        fig = plot_rank_shift_waterfall(merged, n=10)
        assert isinstance(fig, Figure)

    def test_strategy_contribution_returns_figure(self, result):
        from statebind.evaluation.plotting import plot_strategy_contribution

        fig = plot_strategy_contribution(result)
        # May return None if no novel candidates — either is acceptable
        if result.novelty.novel_strategies or result.novelty.novel_states:
            from matplotlib.figure import Figure
            assert isinstance(fig, Figure)
        else:
            assert fig is None

    def test_sensitivity_heatmap_returns_figure(self, result_with_stats):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_sensitivity_heatmap

        fig = plot_sensitivity_heatmap(result_with_stats.sensitivity)
        assert isinstance(fig, Figure)

    def test_sa_score_returns_figure_or_none(self, merged):
        from statebind.evaluation.plotting import plot_sa_score_distribution

        fig = plot_sa_score_distribution(merged)
        # Returns Figure if RDKit available, None otherwise — both valid
        if fig is not None:
            from matplotlib.figure import Figure
            assert isinstance(fig, Figure)


# ── Save Tests ───────────────────────────────────────────────────────


@_requires_mpl
class TestPlotSaving:
    """Verify plots save to disk correctly."""

    def test_save_to_file(self, result, tmp_path):
        from statebind.evaluation.plotting import plot_score_distributions

        out = tmp_path / "test_score.png"
        fig = plot_score_distributions(result, output_path=out)
        assert fig is not None
        assert out.exists()
        assert out.stat().st_size > 0

    def test_generate_all_plots(self, result, merged, tmp_path):
        from statebind.evaluation.plotting import generate_all_plots

        plots = generate_all_plots(result, merged, tmp_path)
        assert isinstance(plots, dict)
        # At minimum: score_distributions, components_heatmap,
        # diversity_radar, rank_shift_waterfall
        assert len(plots) >= 4
        for key, path in plots.items():
            assert key.startswith("plot_")
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0


# ── Edge Case Tests ──────────────────────────────────────────────────


@_requires_mpl
class TestPlotEdgeCases:
    """Verify graceful handling of missing or empty data."""

    def test_empty_novelty_strategy_contribution(self):
        from statebind.evaluation.plotting import plot_strategy_contribution

        empty_result = ComparativeResult(
            novelty=NoveltyAnalysis(
                n_novel=0,
                novel_smiles=[],
                novel_strategies={},
                novel_states={},
            ),
        )
        fig = plot_strategy_contribution(empty_result)
        assert fig is None

    def test_no_statistical_tests_score_distributions(self, result):
        from matplotlib.figure import Figure

        from statebind.evaluation.plotting import plot_score_distributions

        # result (without stats) has statistical_tests=[]
        assert result.statistical_tests == []
        fig = plot_score_distributions(result)
        assert isinstance(fig, Figure)

    def test_sensitivity_heatmap_none_summary(self):
        from statebind.evaluation.plotting import plot_sensitivity_heatmap

        assert plot_sensitivity_heatmap(None) is None
        assert plot_sensitivity_heatmap("not a summary") is None


# ── Fallback Test ────────────────────────────────────────────────────


class TestPlotFallback:
    """Verify all functions return None when matplotlib is unavailable."""

    def test_no_matplotlib_returns_none(self, result, merged):
        import statebind.evaluation.plotting as plotting_mod

        with patch.object(plotting_mod, "HAS_MATPLOTLIB", False):
            assert plotting_mod.plot_score_distributions(result) is None
            assert plotting_mod.plot_score_components_heatmap(merged) is None
            assert plotting_mod.plot_diversity_radar(result) is None
            assert plotting_mod.plot_sensitivity_heatmap(None) is None
            assert plotting_mod.plot_rank_shift_waterfall(merged) is None
            assert plotting_mod.plot_strategy_contribution(result) is None
            assert plotting_mod.plot_sa_score_distribution(merged) is None
            assert plotting_mod.generate_all_plots(result, merged, Path("/tmp")) == {}


# ── Style Test ───────────────────────────────────────────────────────


@_requires_mpl
class TestPlotStyle:
    """Verify figures have proper labels and titles."""

    def test_figures_have_labels_and_title(self, result):
        from statebind.evaluation.plotting import plot_score_distributions

        fig = plot_score_distributions(result)
        assert fig is not None
        ax = fig.axes[0]
        assert ax.get_ylabel() != ""
        assert ax.get_title() != ""
