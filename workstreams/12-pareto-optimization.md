# Workstream 12: Pareto Multi-Objective Optimization

## Goal

Add Pareto front analysis and hypervolume-based comparison to the evaluation pipeline. Instead of relying solely on a weighted-sum composite score (with arbitrary human-chosen weights), compute the Pareto front for each pipeline and compare them using the hypervolume indicator -- a weight-free metric that measures which pipeline is better across ALL possible weight combinations. This directly addresses the methodological weakness that produced the null result.

## Why This Matters

- The null hypothesis was retained under weights 0.35/0.30/0.20/0.15. The sensitivity analysis shows state-aware wins under 44% of random weight configurations. The "winner" depends on weight choice, not scientific reality.
- Pareto front analysis eliminates arbitrary weight selection. The hypervolume indicator gives a single number comparing pipeline quality across all possible weights.
- A result like "state-aware Pareto front dominates static front in 73% of objective space" is strictly more informative and publishable than "mean score is 0.10 lower."
- Pareto analysis is the gold standard in multi-objective molecular optimization. Its absence would be noted by reviewers familiar with the field.

## Prerequisites

- **pymoo** (`pip install pymoo`) OR **DEAP** for multi-objective optimization utilities. pymoo is preferred (more modern, better maintained).
- Existing scored candidates (both pipelines) in `artifacts/ranking/comparison.json`.
- matplotlib for Pareto front visualization (already installed).

## Origin

Vision Idea 008 (Pareto Multi-Objective Optimization). Accepted 2026-04-07.

## Files to Create

| File | Purpose |
|------|---------|
| `src/statebind/ranking/pareto.py` | Pareto front computation: non-dominated sorting, hypervolume indicator, crowding distance. Pure numpy/pymoo -- no torch dependency. |
| `src/statebind/evaluation/pareto_comparison.py` | Compare Pareto fronts of static vs state-aware pipelines. Hypervolume ratio, front dominance fraction, per-objective Pareto analysis. |
| `tests/test_pareto.py` | 20+ tests for Pareto computation, hypervolume, and comparison. |

## Files to Modify

| File | Change |
|------|--------|
| `src/statebind/evaluation/figures.py` | Add 2D Pareto front projection plots (all pairs of objectives), parallel coordinates plot showing all objectives simultaneously. |
| `src/statebind/evaluation/comparison.py` | Add optional Pareto section to `ComparativeResult` when pymoo is available. Include hypervolume, front sizes, dominance fraction. |
| `scripts/report_comparative_results.py` | Add Pareto analysis to the comparison report output. |

## Interface Contracts

### Primary Interface

```python
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

@dataclass
class ParetoResult:
    """Result of Pareto front computation for a single pipeline."""
    front_indices: list[int]        # Indices of non-dominated candidates
    front_scores: np.ndarray        # Shape (n_front, n_objectives)
    hypervolume: float              # Volume dominated by the front
    crowding_distances: list[float] # Per-candidate crowding distance
    n_candidates: int
    n_objectives: int
    objective_names: list[str]

@dataclass
class ParetoComparison:
    """Comparison of two pipelines' Pareto fronts."""
    static_result: ParetoResult
    state_aware_result: ParetoResult
    hypervolume_ratio: float         # state_aware_hv / static_hv (>1 = state wins)
    dominance_fraction: float        # Fraction of static front dominated by state-aware
    per_objective_winner: dict[str, str]  # Which pipeline has better extreme per objective
    reference_point: list[float]     # Used for hypervolume computation

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
        reference_point: For hypervolume computation. Defaults to worst per objective.
        maximize: If True, higher scores are better. If False, lower is better.

    Returns:
        ParetoResult with front indices, hypervolume, and crowding distances.
    """

def compare_pareto_fronts(
    static_scores: np.ndarray,
    state_aware_scores: np.ndarray,
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
) -> ParetoComparison:
    """Compare Pareto fronts of two pipelines.

    Returns ParetoComparison with hypervolume ratio, dominance fraction,
    and per-objective winners.
    """
```

### Visualization Interface

```python
def plot_pareto_projections(
    comparison: ParetoComparison,
    save_dir: str | Path | None = None,
) -> list[Path]:
    """Plot 2D Pareto front projections for all pairs of objectives.

    Returns list of saved figure paths (one per objective pair).
    """

def plot_parallel_coordinates(
    comparison: ParetoComparison,
    save_path: str | Path | None = None,
) -> Path:
    """Parallel coordinates plot showing all objectives simultaneously."""
```

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| Scored candidates | `artifacts/ranking/comparison.json` | Load existing scores (ref_similarity, druglikeness, docking_proxy, state_specificity) |
| ComparativeResult | `evaluation/comparison.py` | Extend with Pareto section |
| Plotting utilities | `evaluation/figures.py` | Matplotlib patterns, savefig conventions |
| Sensitivity analysis | `evaluation/sensitivity.py` | Weight sampling patterns |
| Score components | `ranking/models.py:UnifiedScoreComponent` | Per-component score access |

## Files NOT to Touch

- `src/statebind/ranking/scoring.py` -- scoring function unchanged
- `src/statebind/ml/` -- ML models unchanged
- `src/statebind/generation/` -- generation unchanged
- `src/statebind/baselines/` -- baseline pipeline unchanged
- Any existing test files

## Testing Requirements

### `tests/test_pareto.py` -- ~20 tests

**1. Pareto front computation:**
- `test_pareto_single_dominated()` -- one candidate dominates all others -> front = [that candidate]
- `test_pareto_all_nondominated()` -- when no candidate dominates another, all are on the front
- `test_pareto_two_objectives()` -- known 2D example with expected front
- `test_pareto_four_objectives()` -- works with 4 objectives (project's actual setup)
- `test_pareto_empty_input()` -- empty array returns empty front

**2. Hypervolume computation:**
- `test_hypervolume_monotone()` -- adding a non-dominated point never decreases hypervolume
- `test_hypervolume_single_point()` -- single point hypervolume = product of (point - ref)
- `test_hypervolume_known_value()` -- 2D example with analytically computable hypervolume
- `test_hypervolume_reference_point()` -- different reference points give different hypervolumes

**3. Comparison tests:**
- `test_comparison_symmetric()` -- swapping pipelines inverts the ratio
- `test_dominance_fraction_range()` -- value in [0, 1]
- `test_per_objective_winner()` -- correctly identifies best-extreme pipeline per objective
- `test_comparison_with_real_data()` -- loads comparison.json and runs without crash

**4. Visualization tests:**
- `test_pareto_projection_creates_files()` -- 6 PNG files for C(4,2) objective pairs
- `test_parallel_coordinates_creates_file()` -- one PNG file
- `test_plots_headless()` -- works with Agg backend, no display needed

**5. Integration tests:**
- `test_pareto_in_comparison_result()` -- ComparativeResult includes Pareto section
- `test_pareto_serialization()` -- ParetoResult and ParetoComparison serialize to JSON
- `test_graceful_without_pymoo()` -- falls back or skips when pymoo not installed

## Definition of Done

- [ ] `ranking/pareto.py` computes Pareto fronts and hypervolume indicators
- [ ] `evaluation/pareto_comparison.py` compares pipeline Pareto fronts
- [ ] Hypervolume ratio reported alongside weighted-sum comparison (complementary, not replacement)
- [ ] 2D Pareto projection plots for all 6 objective pairs
- [ ] Parallel coordinates plot for full 4-objective view
- [ ] 20+ tests, all passing (pymoo-dependent tests skipped when not installed)
- [ ] No existing tests broken
- [ ] Comparison report includes Pareto analysis section
- [ ] All new functions have type annotations and docstrings

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation, add them to the relevant CRITICAL.md file(s).

## Agent Instructions

Be detailed yet concise. Keep weighted-sum scoring as the primary comparison metric -- Pareto analysis is an additional lens, not a replacement. Do NOT modify the scoring function.
