"""Statistical hypothesis testing for pipeline comparison.

Provides Mann-Whitney U tests, bootstrap confidence intervals, Cohen's d
and Cliff's delta effect sizes, and permutation tests. scipy is optional;
all functions fall back to numpy-only implementations when scipy is unavailable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

try:
    from scipy import stats as scipy_stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class StatisticalTest:
    """Result of a statistical hypothesis test."""

    name: str
    statistic: float
    p_value: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    interpretation: str


@dataclass
class BootstrapCI:
    """Bootstrap confidence interval for a metric."""

    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    alpha: float = 0.05
    n_bootstrap: int = 1000


def _interpret_p_value(p: float) -> str:
    """Plain-language interpretation of a p-value."""
    if p < 0.001:
        return "highly significant (p < 0.001)"
    if p < 0.01:
        return "significant (p < 0.01)"
    if p < 0.05:
        return "marginally significant (p < 0.05)"
    return "not significant (p >= 0.05)"


def _interpret_cohens_d(d: float) -> str:
    """Plain-language interpretation of Cohen's d magnitude."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    if abs_d < 0.5:
        return "small"
    if abs_d < 0.8:
        return "medium"
    return "large"


def cohens_d(scores_a: list[float], scores_b: list[float]) -> float:
    """Cohen's d effect size using pooled standard deviation.

    Positive when mean(a) > mean(b).
    Returns 0.0 if pooled std is 0 (identical distributions).
    """
    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)

    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return 0.0

    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))

    if pooled_std == 0.0:
        return 0.0

    return float((np.mean(a) - np.mean(b)) / pooled_std)


def cliff_delta(scores_a: list[float], scores_b: list[float]) -> float:
    """Cliff's delta non-parametric effect size.

    Returns value in [-1, 1]. Positive when a tends to be larger than b.
    Returns 0.0 if either list is empty.
    """
    if not scores_a or not scores_b:
        return 0.0

    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)

    # Pairwise comparisons via broadcasting
    diff = a[:, None] - b[None, :]
    n_greater = float(np.sum(diff > 0))
    n_less = float(np.sum(diff < 0))
    n_total = len(a) * len(b)

    return (n_greater - n_less) / n_total


def bootstrap_confidence_interval(
    values: list[float],
    statistic_fn: Callable[[list[float]], float],
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> BootstrapCI:
    """Percentile bootstrap CI for any scalar statistic.

    Numpy-only (no scipy needed). Seeded for reproducibility.
    """
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    rng = np.random.default_rng(seed)

    point_estimate = statistic_fn(values)

    boot_stats = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = statistic_fn(sample.tolist())

    lower = float(np.percentile(boot_stats, 100 * alpha / 2))
    upper = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))

    return BootstrapCI(
        metric_name=getattr(statistic_fn, "__name__", "statistic"),
        point_estimate=round(point_estimate, 4),
        ci_lower=round(lower, 4),
        ci_upper=round(upper, 4),
        alpha=alpha,
        n_bootstrap=n_bootstrap,
    )


def permutation_test(
    scores_a: list[float],
    scores_b: list[float],
    n_permutations: int = 10000,
    seed: int = 42,
) -> StatisticalTest:
    """Permutation-based hypothesis test for difference in means.

    Numpy-only. Seeded for reproducibility.
    """
    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)
    n_a = len(a)

    observed_diff = abs(float(np.mean(a) - np.mean(b)))
    combined = np.concatenate([a, b])
    rng = np.random.default_rng(seed)

    count_extreme = 0
    for _ in range(n_permutations):
        rng.shuffle(combined)
        perm_diff = abs(float(np.mean(combined[:n_a]) - np.mean(combined[n_a:])))
        if perm_diff >= observed_diff:
            count_extreme += 1

    p_value = count_extreme / n_permutations
    d = cohens_d(scores_a, scores_b)

    # Bootstrap CI on the mean difference
    mean_b_val = float(np.mean(b))
    ci = bootstrap_confidence_interval(
        scores_a,
        lambda x: float(np.mean(x)) - mean_b_val,
        seed=seed,
    )

    interpretation = (
        f"Permutation test ({n_permutations} permutations): "
        f"{_interpret_p_value(p_value)}. "
        f"Effect size (Cohen's d): {d:.3f} ({_interpret_cohens_d(d)})."
    )

    return StatisticalTest(
        name="Permutation test",
        statistic=round(observed_diff, 4),
        p_value=round(p_value, 4),
        effect_size=round(d, 4),
        ci_lower=ci.ci_lower,
        ci_upper=ci.ci_upper,
        interpretation=interpretation,
    )


def mann_whitney_u(
    scores_a: list[float],
    scores_b: list[float],
) -> StatisticalTest:
    """Two-sided Mann-Whitney U test comparing score distributions.

    Uses scipy.stats.mannwhitneyu when available. Falls back to
    permutation_test() if scipy is not installed.
    """
    if not HAS_SCIPY:
        result = permutation_test(scores_a, scores_b)
        return StatisticalTest(
            name="Mann-Whitney U (fallback: permutation test)",
            statistic=result.statistic,
            p_value=result.p_value,
            effect_size=result.effect_size,
            ci_lower=result.ci_lower,
            ci_upper=result.ci_upper,
            interpretation=result.interpretation.replace(
                "Permutation test", "Mann-Whitney U (fallback: permutation)"
            ),
        )

    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)

    stat, p_value = scipy_stats.mannwhitneyu(a, b, alternative="two-sided")
    d = cohens_d(scores_a, scores_b)

    # Bootstrap CI on the mean difference
    mean_b_val = float(np.mean(b))
    ci = bootstrap_confidence_interval(
        scores_a,
        lambda x: float(np.mean(x)) - mean_b_val,
        seed=42,
    )

    interpretation = (
        f"Mann-Whitney U test: {_interpret_p_value(p_value)}. "
        f"Effect size (Cohen's d): {d:.3f} ({_interpret_cohens_d(d)})."
    )

    return StatisticalTest(
        name="Mann-Whitney U",
        statistic=round(float(stat), 4),
        p_value=round(float(p_value), 4),
        effect_size=round(d, 4),
        ci_lower=ci.ci_lower,
        ci_upper=ci.ci_upper,
        interpretation=interpretation,
    )
