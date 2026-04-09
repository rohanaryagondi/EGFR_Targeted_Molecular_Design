"""Statistical hypothesis testing for pipeline comparison.

Provides Mann-Whitney U tests, bootstrap confidence intervals (percentile and
BCa), Cohen's d and Cliff's delta effect sizes, and permutation tests. scipy is
optional; all functions fall back to numpy-only implementations when scipy is
unavailable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

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


def bca_bootstrap_confidence_interval(
    values: list[float],
    statistic_fn: Callable[[list[float]], float],
    alpha: float = 0.05,
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> BootstrapCI:
    """Bias-corrected and accelerated (BCa) bootstrap confidence interval.

    Provides narrower and more accurate CIs than percentile bootstrap,
    especially for skewed distributions. Requires scipy for the normal
    quantile function; falls back to percentile bootstrap if scipy is
    unavailable.

    Args:
        values: Observed sample values.
        statistic_fn: Function mapping a list of floats to a scalar statistic.
        alpha: Significance level (default 0.05 for 95 % CI).
        n_bootstrap: Number of bootstrap resamples (default 10 000).
        seed: Random seed for reproducibility.

    Returns:
        BootstrapCI with BCa-corrected bounds.
    """
    if not HAS_SCIPY:
        logger.warning(
            "scipy not available -- falling back to percentile bootstrap CI"
        )
        return bootstrap_confidence_interval(
            values, statistic_fn, alpha=alpha, n_bootstrap=n_bootstrap, seed=seed
        )

    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    rng = np.random.default_rng(seed)

    # Point estimate
    theta_hat = statistic_fn(values)

    # --- Bootstrap distribution ---
    boot_stats = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = statistic_fn(sample.tolist())

    # Edge case: zero variance in bootstrap distribution
    if np.all(boot_stats == boot_stats[0]):
        logger.warning(
            "All bootstrap estimates are identical (%.4f) -- "
            "returning point estimate as both bounds",
            boot_stats[0],
        )
        return BootstrapCI(
            metric_name=getattr(statistic_fn, "__name__", "statistic"),
            point_estimate=round(theta_hat, 4),
            ci_lower=round(theta_hat, 4),
            ci_upper=round(theta_hat, 4),
            alpha=alpha,
            n_bootstrap=n_bootstrap,
        )

    # --- Bias correction (z0) ---
    prop_below = np.mean(boot_stats < theta_hat)
    # Clamp to avoid +-inf from ppf(0) or ppf(1)
    prop_below = np.clip(prop_below, 1e-10, 1.0 - 1e-10)
    z0 = float(scipy_stats.norm.ppf(prop_below))

    # --- Acceleration (a) via jackknife ---
    jack_estimates = np.empty(n)
    for i in range(n):
        jack_sample = np.concatenate([arr[:i], arr[i + 1 :]]).tolist()
        jack_estimates[i] = statistic_fn(jack_sample)

    theta_dot = np.mean(jack_estimates)
    diff = theta_dot - jack_estimates
    numerator = np.sum(diff ** 3)
    denominator = 6.0 * (np.sum(diff ** 2) ** 1.5)

    if denominator == 0.0:
        # All jackknife estimates identical -- acceleration is zero
        a = 0.0
    else:
        a = float(numerator / denominator)

    # --- Adjusted percentiles ---
    z_alpha_lower = float(scipy_stats.norm.ppf(alpha / 2))
    z_alpha_upper = float(scipy_stats.norm.ppf(1 - alpha / 2))

    # BCa adjustment formula
    numer_lower = z0 + z_alpha_lower
    alpha1 = float(
        scipy_stats.norm.cdf(z0 + numer_lower / (1 - a * numer_lower))
    )
    numer_upper = z0 + z_alpha_upper
    alpha2 = float(
        scipy_stats.norm.cdf(z0 + numer_upper / (1 - a * numer_upper))
    )

    # Clamp to valid percentile range
    alpha1 = np.clip(alpha1, 1e-10, 1.0 - 1e-10)
    alpha2 = np.clip(alpha2, 1e-10, 1.0 - 1e-10)

    lower = float(np.percentile(boot_stats, 100 * alpha1))
    upper = float(np.percentile(boot_stats, 100 * alpha2))

    return BootstrapCI(
        metric_name=getattr(statistic_fn, "__name__", "statistic"),
        point_estimate=round(theta_hat, 4),
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
