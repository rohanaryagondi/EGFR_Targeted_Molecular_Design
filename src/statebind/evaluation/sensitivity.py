"""Weight sensitivity and ablation analysis for scoring comparison.

Tests whether the state-aware vs static result is robust to the specific
choice of scoring weights, or whether it depends on a lucky weight config.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from statebind.ranking.models import MergedRanking
from statebind.ranking.scoring import DEFAULT_WEIGHTS

# Component names in canonical order (matches DEFAULT_WEIGHTS keys)
_COMPONENT_NAMES = ["reference_similarity", "druglikeness", "docking_proxy", "state_specificity"]


@dataclass
class SensitivityResult:
    """Result of scoring under one weight configuration."""

    weight_config: dict[str, float]
    static_mean: float
    state_aware_mean: float
    winner: str  # "static", "state_aware", or "tie"
    delta: float  # state_aware_mean - static_mean


@dataclass
class SensitivitySummary:
    """Aggregated sensitivity analysis."""

    n_configs: int
    state_aware_wins: int
    static_wins: int
    ties: int
    state_aware_win_fraction: float
    results: list[SensitivityResult] = field(default_factory=list)


def _rescore_merged(merged: MergedRanking, weights: dict[str, float]) -> SensitivityResult:
    """Recompute composite scores for both pools using stored component values.

    Uses UnifiedScoredCandidate.get_score() to retrieve weight-independent
    component values, then applies the new weight vector.
    """
    static_composites: list[float] = []
    for c in merged.static_pool.candidates:
        composite = sum(
            (c.get_score(name) or 0.0) * weights[name]
            for name in _COMPONENT_NAMES
        )
        static_composites.append(round(composite, 4))

    state_composites: list[float] = []
    for c in merged.state_aware_pool.candidates:
        composite = sum(
            (c.get_score(name) or 0.0) * weights[name]
            for name in _COMPONENT_NAMES
        )
        state_composites.append(round(composite, 4))

    static_mean = float(np.mean(static_composites)) if static_composites else 0.0
    state_mean = float(np.mean(state_composites)) if state_composites else 0.0
    delta = round(state_mean - static_mean, 4)

    if abs(delta) < 1e-6:
        winner = "tie"
    elif delta > 0:
        winner = "state_aware"
    else:
        winner = "static"

    return SensitivityResult(
        weight_config={k: round(v, 4) for k, v in weights.items()},
        static_mean=round(static_mean, 4),
        state_aware_mean=round(state_mean, 4),
        winner=winner,
        delta=delta,
    )


def run_weight_sensitivity(
    merged: MergedRanking,
    n_samples: int = 100,
    seed: int = 42,
) -> SensitivitySummary:
    """Sample random weight vectors (Dirichlet) and re-score all candidates.

    For each weight vector:
    1. Re-score all candidates in both pools using stored component values
    2. Compute mean composite score per pipeline
    3. Record which pipeline wins

    Reports fraction of configs where state-aware wins.
    """
    rng = np.random.default_rng(seed)
    weight_vectors = rng.dirichlet([1, 1, 1, 1], size=n_samples)

    results: list[SensitivityResult] = []
    state_aware_wins = 0
    static_wins = 0
    ties = 0

    for row in weight_vectors:
        weights = {name: float(row[i]) for i, name in enumerate(_COMPONENT_NAMES)}
        result = _rescore_merged(merged, weights)
        results.append(result)

        if result.winner == "state_aware":
            state_aware_wins += 1
        elif result.winner == "static":
            static_wins += 1
        else:
            ties += 1

    return SensitivitySummary(
        n_configs=n_samples,
        state_aware_wins=state_aware_wins,
        static_wins=static_wins,
        ties=ties,
        state_aware_win_fraction=round(state_aware_wins / max(n_samples, 1), 4),
        results=results,
    )


def run_ablation_analysis(merged: MergedRanking) -> list[SensitivityResult]:
    """Set each weight component to 0 in turn, renormalize, re-score.

    4 ablation configs — one per component. The remaining 3 components
    are renormalized to sum to 1.0, preserving their relative ratios
    from DEFAULT_WEIGHTS.

    If state_specificity=0 and state-aware still wins, the advantage
    is NOT from structural bias.
    """
    results: list[SensitivityResult] = []

    for ablated in _COMPONENT_NAMES:
        remaining = {k: v for k, v in DEFAULT_WEIGHTS.items() if k != ablated}
        remaining_sum = sum(remaining.values())

        weights = {}
        for name in _COMPONENT_NAMES:
            if name == ablated:
                weights[name] = 0.0
            else:
                weights[name] = round(remaining[name] / remaining_sum, 4)

        # Fix rounding so weights sum exactly to 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            last_nonzero = [n for n in _COMPONENT_NAMES if n != ablated][-1]
            weights[last_nonzero] = round(weights[last_nonzero] + (1.0 - total), 4)

        results.append(_rescore_merged(merged, weights))

    return results


def run_weight_sweep(
    merged: MergedRanking,
    component: str,
    values: list[float],
) -> list[SensitivityResult]:
    """Sweep one component's weight across a range, renormalize others.

    For each value, the swept component gets that weight. The remaining
    weight (1 - value) is distributed proportionally among the other 3
    components, preserving their ratios from DEFAULT_WEIGHTS.
    """
    if component not in _COMPONENT_NAMES:
        raise ValueError(
            f"Unknown component '{component}'. Must be one of {_COMPONENT_NAMES}"
        )

    other_names = [n for n in _COMPONENT_NAMES if n != component]
    other_defaults = {n: DEFAULT_WEIGHTS[n] for n in other_names}
    other_sum = sum(other_defaults.values())

    results: list[SensitivityResult] = []

    for val in values:
        remaining = 1.0 - val
        weights = {component: round(val, 4)}

        for name in other_names:
            weights[name] = round(other_defaults[name] / other_sum * remaining, 4)

        # Fix rounding
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            weights[other_names[-1]] = round(
                weights[other_names[-1]] + (1.0 - total), 4
            )

        results.append(_rescore_merged(merged, weights))

    return results
