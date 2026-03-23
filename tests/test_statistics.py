"""Tests for WS03: statistical testing and sensitivity analysis.

Covers:
- Mann-Whitney U test
- Bootstrap confidence intervals
- Cohen's d and Cliff's delta effect sizes
- Permutation test
- Weight sensitivity, ablation, and sweep analysis
"""

from __future__ import annotations

import numpy as np
import pytest

from statebind.baselines.pipeline import run_static_baseline
from statebind.evaluation.sensitivity import (
    SensitivityResult,
    SensitivitySummary,
    run_ablation_analysis,
    run_weight_sensitivity,
    run_weight_sweep,
)
from statebind.evaluation.statistics import (
    BootstrapCI,
    StatisticalTest,
    bootstrap_confidence_interval,
    cliff_delta,
    cohens_d,
    mann_whitney_u,
    permutation_test,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def pipelines():
    """Run both pipelines once for all sensitivity tests."""
    baseline = run_static_baseline()
    gen = generate_all_states()
    filtered = filter_all_states(gen)

    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    merged = merge_rankings(static_pool, state_pool)
    return merged


@pytest.fixture(scope="module")
def merged(pipelines):
    return pipelines


# ── Mann-Whitney U Tests ──────────────────────────────────────────────


class TestMannWhitneyU:
    """Test Mann-Whitney U (or permutation fallback)."""

    def test_mann_whitney_identical(self):
        """Same distribution -> p > 0.05."""
        rng = np.random.default_rng(42)
        data = rng.normal(0.5, 0.1, 50).tolist()
        result = mann_whitney_u(data, data)
        assert result.p_value > 0.05

    def test_mann_whitney_shifted(self):
        """Shifted distribution -> p < 0.05."""
        rng = np.random.default_rng(42)
        a = rng.normal(0.5, 0.1, 100).tolist()
        b = rng.normal(0.8, 0.1, 100).tolist()
        result = mann_whitney_u(a, b)
        assert result.p_value < 0.05

    def test_mann_whitney_effect_size(self):
        """Shifted distributions should have non-zero effect size."""
        rng = np.random.default_rng(42)
        a = rng.normal(0.5, 0.1, 100).tolist()
        b = rng.normal(0.3, 0.1, 100).tolist()
        result = mann_whitney_u(a, b)
        assert abs(result.effect_size) > 0

    def test_mann_whitney_returns_statistical_test(self):
        """Return type is StatisticalTest dataclass."""
        result = mann_whitney_u([0.1, 0.2, 0.3], [0.4, 0.5, 0.6])
        assert isinstance(result, StatisticalTest)
        assert isinstance(result.name, str)
        assert isinstance(result.p_value, float)
        assert isinstance(result.interpretation, str)


# ── Bootstrap CI Tests ────────────────────────────────────────────────


class TestBootstrapCI:
    """Test bootstrap confidence intervals."""

    def test_bootstrap_ci_contains_mean(self):
        """CI should bracket the sample mean for normal data."""
        rng = np.random.default_rng(42)
        data = rng.normal(5.0, 1.0, 200).tolist()
        ci = bootstrap_confidence_interval(
            data, lambda x: float(np.mean(x)), seed=42
        )
        assert ci.ci_lower <= ci.point_estimate <= ci.ci_upper

    def test_bootstrap_ci_reproducible(self):
        """Same seed produces same result."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        ci1 = bootstrap_confidence_interval(
            data, lambda x: float(np.mean(x)), seed=123
        )
        ci2 = bootstrap_confidence_interval(
            data, lambda x: float(np.mean(x)), seed=123
        )
        assert ci1.ci_lower == ci2.ci_lower
        assert ci1.ci_upper == ci2.ci_upper

    def test_bootstrap_ci_narrow_with_more_data(self):
        """More data -> tighter CI."""
        rng = np.random.default_rng(42)
        small = rng.normal(0.5, 0.1, 20).tolist()
        large = rng.normal(0.5, 0.1, 1000).tolist()

        ci_small = bootstrap_confidence_interval(
            small, lambda x: float(np.mean(x)), seed=42
        )
        ci_large = bootstrap_confidence_interval(
            large, lambda x: float(np.mean(x)), seed=42
        )

        width_small = ci_small.ci_upper - ci_small.ci_lower
        width_large = ci_large.ci_upper - ci_large.ci_lower
        assert width_large < width_small

    def test_bootstrap_ci_custom_statistic(self):
        """Works with median as statistic_fn."""
        data = [1.0, 2.0, 3.0, 100.0, 5.0]
        ci = bootstrap_confidence_interval(
            data, lambda x: float(np.median(x)), seed=42
        )
        assert isinstance(ci, BootstrapCI)
        assert ci.ci_lower <= ci.ci_upper


# ── Effect Size Tests ─────────────────────────────────────────────────


class TestEffectSizes:
    """Test Cohen's d and Cliff's delta."""

    def test_cohens_d_identical(self):
        """Identical distributions -> d = 0."""
        data = [0.5, 0.6, 0.7, 0.8]
        assert cohens_d(data, data) == 0.0

    def test_cohens_d_known_shift(self):
        """Shift of 1 std -> d approximately 1.0."""
        rng = np.random.default_rng(42)
        a = rng.normal(1.0, 1.0, 500).tolist()
        b = rng.normal(0.0, 1.0, 500).tolist()
        d = cohens_d(a, b)
        assert abs(d - 1.0) < 0.15  # within 0.15 of 1.0

    def test_cohens_d_sign(self):
        """a > b gives positive d."""
        a = [10.0, 11.0, 12.0]
        b = [1.0, 2.0, 3.0]
        assert cohens_d(a, b) > 0

    def test_cliff_delta_range(self):
        """Cliff's delta is always in [-1, 1]."""
        rng = np.random.default_rng(42)
        a = rng.uniform(0, 1, 50).tolist()
        b = rng.uniform(0, 1, 50).tolist()
        d = cliff_delta(a, b)
        assert -1.0 <= d <= 1.0

    def test_cliff_delta_identical(self):
        """Identical distributions -> delta = 0."""
        data = [0.5, 0.6, 0.7, 0.8]
        assert cliff_delta(data, data) == 0.0


# ── Permutation Test Tests ────────────────────────────────────────────


class TestPermutationTest:
    """Test permutation-based hypothesis test."""

    def test_permutation_identical(self):
        """Same distribution -> p > 0.05."""
        rng = np.random.default_rng(42)
        data = rng.normal(0.5, 0.1, 50).tolist()
        result = permutation_test(data, data, n_permutations=1000, seed=42)
        assert result.p_value > 0.05

    def test_permutation_shifted(self):
        """Shifted distribution -> p < 0.05."""
        rng = np.random.default_rng(42)
        a = rng.normal(0.5, 0.1, 100).tolist()
        b = rng.normal(0.8, 0.1, 100).tolist()
        result = permutation_test(a, b, n_permutations=1000, seed=42)
        assert result.p_value < 0.05

    def test_permutation_reproducible(self):
        """Same seed -> same result."""
        a = [0.1, 0.2, 0.3, 0.4, 0.5]
        b = [0.6, 0.7, 0.8, 0.9, 1.0]
        r1 = permutation_test(a, b, n_permutations=500, seed=99)
        r2 = permutation_test(a, b, n_permutations=500, seed=99)
        assert r1.p_value == r2.p_value
        assert r1.statistic == r2.statistic

    def test_permutation_returns_statistical_test(self):
        """Return type is StatisticalTest."""
        result = permutation_test([0.1, 0.2], [0.3, 0.4], n_permutations=100, seed=42)
        assert isinstance(result, StatisticalTest)
        assert result.name == "Permutation test"


# ── Sensitivity Analysis Tests ────────────────────────────────────────


class TestSensitivity:
    """Test weight sensitivity, ablation, and sweep analysis."""

    def test_sensitivity_all_configs_valid(self, merged):
        """All Dirichlet weight configs sum to 1.0."""
        summary = run_weight_sensitivity(merged, n_samples=20, seed=42)
        for sr in summary.results:
            total = sum(sr.weight_config.values())
            assert abs(total - 1.0) < 1e-3

    def test_sensitivity_result_counts(self, merged):
        """wins + losses + ties == n_configs."""
        summary = run_weight_sensitivity(merged, n_samples=50, seed=42)
        assert (
            summary.state_aware_wins + summary.static_wins + summary.ties
            == summary.n_configs
        )

    def test_sensitivity_win_fraction_range(self, merged):
        """Win fraction is in [0.0, 1.0]."""
        summary = run_weight_sensitivity(merged, n_samples=20, seed=42)
        assert 0.0 <= summary.state_aware_win_fraction <= 1.0

    def test_sensitivity_reproducible(self, merged):
        """Same seed -> same results."""
        s1 = run_weight_sensitivity(merged, n_samples=10, seed=42)
        s2 = run_weight_sensitivity(merged, n_samples=10, seed=42)
        assert s1.state_aware_wins == s2.state_aware_wins
        assert s1.static_wins == s2.static_wins

    def test_ablation_four_configs(self, merged):
        """Ablation produces exactly 4 results."""
        results = run_ablation_analysis(merged)
        assert len(results) == 4

    def test_ablation_weights_sum_to_one(self, merged):
        """All ablation weight configs sum to 1.0."""
        results = run_ablation_analysis(merged)
        for sr in results:
            total = sum(sr.weight_config.values())
            assert abs(total - 1.0) < 1e-3

    def test_ablation_zero_component(self, merged):
        """Each ablation config has exactly one component at 0."""
        results = run_ablation_analysis(merged)
        for sr in results:
            zero_count = sum(1 for v in sr.weight_config.values() if v == 0.0)
            assert zero_count == 1

    def test_weight_sweep_correct_count(self, merged):
        """Number of results matches number of values."""
        values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        results = run_weight_sweep(merged, "state_specificity", values)
        assert len(results) == len(values)

    def test_weight_sweep_monotonic_component(self, merged):
        """Swept component increases monotonically in configs."""
        values = [0.0, 0.1, 0.2, 0.3]
        results = run_weight_sweep(merged, "state_specificity", values)
        swept_weights = [sr.weight_config["state_specificity"] for sr in results]
        for i in range(len(swept_weights) - 1):
            assert swept_weights[i] <= swept_weights[i + 1]

    def test_weight_sweep_weights_valid(self, merged):
        """All sweep configs sum to 1.0."""
        values = [0.0, 0.25, 0.5, 0.75]
        results = run_weight_sweep(merged, "docking_proxy", values)
        for sr in results:
            total = sum(sr.weight_config.values())
            assert abs(total - 1.0) < 1e-3
