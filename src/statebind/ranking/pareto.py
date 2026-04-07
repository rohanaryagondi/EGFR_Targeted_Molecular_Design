"""Pareto front computation and hypervolume indicator.

Pure numpy implementation with optional pymoo acceleration for hypervolume.
No torch dependency. Complements the weighted-sum scoring -- does NOT replace it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Optional pymoo for hypervolume (falls back to pure-numpy approximation)
try:
    from pymoo.indicators.hv import HV as _PymooHV  # noqa: N811

    HAS_PYMOO = True
except ImportError:
    HAS_PYMOO = False

# Objective names in canonical order (matches ranking/scoring.py DEFAULT_WEIGHTS keys)
OBJECTIVE_NAMES = [
    "reference_similarity",
    "druglikeness",
    "docking_proxy",
    "state_specificity",
]


@dataclass
class ParetoResult:
    """Result of Pareto front computation for a single pipeline."""

    front_indices: list[int]
    front_scores: np.ndarray  # (n_front, n_objectives)
    hypervolume: float
    crowding_distances: list[float]
    n_candidates: int
    n_objectives: int
    objective_names: list[str]

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "front_indices": self.front_indices,
            "front_scores": self.front_scores.tolist(),
            "hypervolume": round(self.hypervolume, 4),
            "crowding_distances": [
                None if d == float("inf") else round(d, 4)
                for d in self.crowding_distances
            ],
            "n_candidates": self.n_candidates,
            "n_objectives": self.n_objectives,
            "objective_names": self.objective_names,
        }


@dataclass
class ParetoComparison:
    """Comparison of two pipelines' Pareto fronts."""

    static_result: ParetoResult
    state_aware_result: ParetoResult
    hypervolume_ratio: float  # state_aware_hv / static_hv (>1 = state-aware wins)
    dominance_fraction: float  # fraction of static front dominated by state-aware
    per_objective_winner: dict[str, str]  # best extreme per objective
    reference_point: list[float]

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "static_result": self.static_result.to_dict(),
            "state_aware_result": self.state_aware_result.to_dict(),
            "hypervolume_ratio": round(self.hypervolume_ratio, 4),
            "dominance_fraction": round(self.dominance_fraction, 4),
            "per_objective_winner": self.per_objective_winner,
            "reference_point": [round(r, 4) for r in self.reference_point],
        }


def _is_dominated(point: np.ndarray, other: np.ndarray, maximize: bool) -> bool:
    """Check if *point* is dominated by *other*.

    A point is dominated if `other` is at least as good on all objectives
    and strictly better on at least one.
    """
    if maximize:
        return bool(np.all(other >= point) and np.any(other > point))
    return bool(np.all(other <= point) and np.any(other < point))


def _non_dominated_sort(scores: np.ndarray, maximize: bool = True) -> list[int]:
    """Return indices of non-dominated (Pareto-optimal) points.

    Simple O(n^2) algorithm. Fine for our dataset sizes (<1000 candidates).
    """
    n = scores.shape[0]
    is_dominated_mask = np.zeros(n, dtype=bool)

    for i in range(n):
        if is_dominated_mask[i]:
            continue
        for j in range(n):
            if i == j or is_dominated_mask[j]:
                continue
            if _is_dominated(scores[i], scores[j], maximize):
                is_dominated_mask[i] = True
                break

    return [int(i) for i in range(n) if not is_dominated_mask[i]]


def _crowding_distance(front_scores: np.ndarray) -> list[float]:
    """Compute crowding distance for each point on the Pareto front.

    Points at the extremes get infinite distance. Interior points get
    the sum of normalized distances to their neighbors along each objective.
    """
    n, m = front_scores.shape
    if n <= 2:
        return [float("inf")] * n

    distances = np.zeros(n)

    for obj in range(m):
        sorted_idx = np.argsort(front_scores[:, obj])
        obj_range = float(
            front_scores[sorted_idx[-1], obj] - front_scores[sorted_idx[0], obj]
        )

        # Boundary points get infinity
        distances[sorted_idx[0]] = float("inf")
        distances[sorted_idx[-1]] = float("inf")

        if obj_range < 1e-12:
            continue

        for k in range(1, n - 1):
            distances[sorted_idx[k]] += (
                front_scores[sorted_idx[k + 1], obj]
                - front_scores[sorted_idx[k - 1], obj]
            ) / obj_range

    return [round(float(d), 4) for d in distances]


def _hypervolume_pymoo(
    front_scores: np.ndarray, reference_point: np.ndarray
) -> float:
    """Compute hypervolume using pymoo (minimization convention).

    pymoo's HV expects a minimization problem, so we negate the scores
    and the reference point.
    """
    neg_front = -front_scores
    neg_ref = -reference_point
    indicator = _PymooHV(ref_point=neg_ref)
    return float(indicator(neg_front))


def _hypervolume_2d(front_scores: np.ndarray, reference_point: np.ndarray) -> float:
    """Exact 2D hypervolume computation (no external deps)."""
    if front_scores.shape[1] != 2:
        raise ValueError("_hypervolume_2d requires exactly 2 objectives")

    # Sort by first objective descending
    sorted_idx = np.argsort(-front_scores[:, 0])
    sorted_front = front_scores[sorted_idx]

    hv = 0.0
    prev_y = reference_point[1]

    for point in sorted_front:
        if point[0] <= reference_point[0] or point[1] <= reference_point[1]:
            continue
        width = point[0] - reference_point[0]
        height = point[1] - prev_y
        if height > 0:
            hv += width * height
            prev_y = point[1]

    return hv


def _hypervolume_inclusion_exclusion(
    front_scores: np.ndarray, reference_point: np.ndarray
) -> float:
    """Approximate hypervolume for >2 objectives without pymoo.

    Uses a Monte Carlo approximation: sample random points in the bounding
    box and count the fraction dominated by at least one front point.
    Deterministic seed for reproducibility.
    """
    n_samples = 100_000
    rng = np.random.default_rng(42)

    # Bounding box: reference_point to max per objective
    upper = np.max(front_scores, axis=0)
    lower = reference_point

    # Filter out objectives where upper <= lower (no volume)
    valid = upper > lower
    if not np.any(valid):
        return 0.0

    # Only sample in dimensions with actual range
    samples = rng.uniform(
        lower[valid], upper[valid], size=(n_samples, int(np.sum(valid)))
    )

    # Count how many samples are dominated by at least one front point
    front_valid = front_scores[:, valid]
    dominated_count = 0
    for sample in samples:
        if np.any(np.all(front_valid >= sample, axis=1)):
            dominated_count += 1

    # Volume of bounding box
    box_volume = float(np.prod(upper[valid] - lower[valid]))
    return box_volume * dominated_count / n_samples


def _compute_hypervolume(
    front_scores: np.ndarray, reference_point: np.ndarray
) -> float:
    """Compute hypervolume, choosing the best available method."""
    if front_scores.shape[0] == 0:
        return 0.0

    if HAS_PYMOO:
        return _hypervolume_pymoo(front_scores, reference_point)

    if front_scores.shape[1] == 2:
        return _hypervolume_2d(front_scores, reference_point)

    return _hypervolume_inclusion_exclusion(front_scores, reference_point)


def compute_pareto_front(
    scores: np.ndarray,
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
    maximize: bool = True,
) -> ParetoResult:
    """Compute the Pareto front from a matrix of objective scores.

    Args:
        scores: Shape (n_candidates, n_objectives). Higher is better if maximize=True.
        objective_names: Names for each objective (for reporting).
        reference_point: For hypervolume computation. Defaults to origin (all zeros).
        maximize: If True, higher scores are better.

    Returns:
        ParetoResult with front indices, hypervolume, and crowding distances.
    """
    scores = np.asarray(scores, dtype=np.float64)

    if scores.ndim != 2:
        raise ValueError(f"scores must be 2D, got shape {scores.shape}")

    n_candidates, n_objectives = scores.shape

    if objective_names is None:
        objective_names = [f"obj_{i}" for i in range(n_objectives)]

    if len(objective_names) != n_objectives:
        raise ValueError(
            f"objective_names length ({len(objective_names)}) != "
            f"n_objectives ({n_objectives})"
        )

    # Handle empty input
    if n_candidates == 0:
        ref = reference_point if reference_point is not None else [0.0] * n_objectives
        return ParetoResult(
            front_indices=[],
            front_scores=np.empty((0, n_objectives)),
            hypervolume=0.0,
            crowding_distances=[],
            n_candidates=0,
            n_objectives=n_objectives,
            objective_names=objective_names,
        )

    # Compute Pareto front
    front_indices = _non_dominated_sort(scores, maximize=maximize)
    front_scores = scores[front_indices]

    # Reference point for hypervolume
    if reference_point is not None:
        ref = np.asarray(reference_point, dtype=np.float64)
    else:
        # Default: origin (0, 0, ..., 0) for maximization
        ref = np.zeros(n_objectives)

    hv = _compute_hypervolume(front_scores, ref)
    crowding = _crowding_distance(front_scores)

    return ParetoResult(
        front_indices=front_indices,
        front_scores=front_scores,
        hypervolume=round(hv, 4),
        crowding_distances=crowding,
        n_candidates=n_candidates,
        n_objectives=n_objectives,
        objective_names=objective_names,
    )


def _dominance_fraction(
    front_a: np.ndarray, front_b: np.ndarray, maximize: bool = True
) -> float:
    """Fraction of front_a points dominated by at least one point in front_b."""
    if front_a.shape[0] == 0:
        return 0.0

    dominated_count = 0
    for point in front_a:
        for other in front_b:
            if _is_dominated(point, other, maximize):
                dominated_count += 1
                break

    return dominated_count / front_a.shape[0]


def compare_pareto_fronts(
    static_scores: np.ndarray,
    state_aware_scores: np.ndarray,
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
) -> ParetoComparison:
    """Compare Pareto fronts of two pipelines.

    Args:
        static_scores: Shape (n_static, n_objectives).
        state_aware_scores: Shape (n_state_aware, n_objectives).
        objective_names: Names for each objective.
        reference_point: For hypervolume. Defaults to origin.

    Returns:
        ParetoComparison with hypervolume ratio, dominance fraction,
        and per-objective winners.
    """
    static_scores = np.asarray(static_scores, dtype=np.float64)
    state_aware_scores = np.asarray(state_aware_scores, dtype=np.float64)

    if objective_names is None:
        n_obj = static_scores.shape[1] if static_scores.ndim == 2 else 0
        objective_names = OBJECTIVE_NAMES[:n_obj] if n_obj <= 4 else [
            f"obj_{i}" for i in range(n_obj)
        ]

    static_result = compute_pareto_front(
        static_scores,
        objective_names=objective_names,
        reference_point=reference_point,
    )
    state_aware_result = compute_pareto_front(
        state_aware_scores,
        objective_names=objective_names,
        reference_point=reference_point,
    )

    # Hypervolume ratio: >1 means state-aware has larger dominated region
    if static_result.hypervolume > 0:
        hv_ratio = state_aware_result.hypervolume / static_result.hypervolume
    else:
        hv_ratio = float("inf") if state_aware_result.hypervolume > 0 else 1.0

    # Dominance fraction: what fraction of static front is dominated by state-aware
    dom_frac = _dominance_fraction(
        static_result.front_scores, state_aware_result.front_scores
    )

    # Per-objective winner: who has the best extreme value?
    per_obj_winner: dict[str, str] = {}
    for i, name in enumerate(objective_names):
        static_best = (
            float(np.max(static_scores[:, i]))
            if static_scores.shape[0] > 0 else -float("inf")
        )
        state_best = (
            float(np.max(state_aware_scores[:, i]))
            if state_aware_scores.shape[0] > 0 else -float("inf")
        )

        if state_best > static_best:
            per_obj_winner[name] = "state_aware"
        elif static_best > state_best:
            per_obj_winner[name] = "static"
        else:
            per_obj_winner[name] = "tie"

    ref = reference_point if reference_point is not None else [0.0] * len(objective_names)

    return ParetoComparison(
        static_result=static_result,
        state_aware_result=state_aware_result,
        hypervolume_ratio=round(hv_ratio, 4),
        dominance_fraction=round(dom_frac, 4),
        per_objective_winner=per_obj_winner,
        reference_point=[round(r, 4) for r in ref],
    )


def extract_score_matrix(
    candidates: list,
    objective_names: list[str] | None = None,
) -> np.ndarray:
    """Extract an (n_candidates, n_objectives) score matrix from UnifiedScoredCandidate list.

    Args:
        candidates: List of UnifiedScoredCandidate (from ranking.models).
        objective_names: Which score components to extract. Defaults to OBJECTIVE_NAMES.

    Returns:
        numpy array of shape (n_candidates, len(objective_names)).
    """
    if objective_names is None:
        objective_names = OBJECTIVE_NAMES

    rows = []
    for c in candidates:
        row = [c.get_score(name) or 0.0 for name in objective_names]
        rows.append(row)

    if not rows:
        return np.empty((0, len(objective_names)))

    return np.array(rows, dtype=np.float64)
