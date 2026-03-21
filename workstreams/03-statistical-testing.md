# Workstream 03: Statistical Testing

## Goal

Add statistical hypothesis testing, confidence intervals, effect sizes, and weight sensitivity analysis to the evaluation module. This transforms the comparison from "numbers went up" to statistically grounded inference. Uses scipy (already in `[project.optional-dependencies] science`).

## Why This Matters

The current comparison reports raw deltas (e.g., +0.020 mean score, +0.035 diversity) with no confidence intervals, p-values, or effect sizes. Without statistical backing, it's impossible to know if these differences are meaningful or just noise.

## Prerequisites

None. This workstream operates on the existing `MergedRanking` data structure and can start immediately.

## Files to Create

### `src/statebind/evaluation/statistics.py`

Statistical testing functions.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class StatisticalTest:
    """Result of a statistical hypothesis test."""
    name: str                    # e.g., "Mann-Whitney U"
    statistic: float             # test statistic
    p_value: float               # two-sided p-value
    effect_size: float           # standardized effect
    ci_lower: float              # 95% CI lower bound
    ci_upper: float              # 95% CI upper bound
    interpretation: str          # plain-language interpretation

@dataclass
class BootstrapCI:
    """Bootstrap confidence interval for a metric."""
    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    alpha: float = 0.05
    n_bootstrap: int = 1000


def mann_whitney_u(scores_a: list[float], scores_b: list[float]) -> StatisticalTest:
    """Two-sided Mann-Whitney U test comparing score distributions.

    Uses scipy.stats.mannwhitneyu. Falls back to a simple permutation
    test if scipy unavailable.
    """

def bootstrap_confidence_interval(
    values: list[float],
    statistic_fn: Callable[[list[float]], float],
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> BootstrapCI:
    """Percentile bootstrap CI for any scalar statistic.

    Uses numpy only (no scipy needed). Seeded for reproducibility.
    """

def cohens_d(scores_a: list[float], scores_b: list[float]) -> float:
    """Cohen's d effect size (pooled standard deviation)."""

def cliff_delta(scores_a: list[float], scores_b: list[float]) -> float:
    """Cliff's delta non-parametric effect size. Returns value in [-1, 1]."""

def permutation_test(
    scores_a: list[float],
    scores_b: list[float],
    n_permutations: int = 10000,
    seed: int = 42,
) -> StatisticalTest:
    """Permutation-based p-value for difference in means."""
```

Fallback pattern for scipy:
```python
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
```

### `src/statebind/evaluation/sensitivity.py`

Weight sensitivity and ablation analysis.

```python
from __future__ import annotations
from dataclasses import dataclass, field

from statebind.ranking.models import MergedRanking

@dataclass
class SensitivityResult:
    """Result of scoring under one weight configuration."""
    weight_config: dict[str, float]
    static_mean: float
    state_aware_mean: float
    winner: str                  # "static", "state_aware", or "tie"
    delta: float                 # state_aware_mean - static_mean

@dataclass
class SensitivitySummary:
    """Aggregated sensitivity analysis."""
    n_configs: int
    state_aware_wins: int
    static_wins: int
    ties: int
    state_aware_win_fraction: float
    results: list[SensitivityResult]


def run_weight_sensitivity(
    merged: MergedRanking,
    n_samples: int = 100,
    seed: int = 42,
) -> SensitivitySummary:
    """Sample random weight vectors (Dirichlet) and re-score all candidates.

    For each weight vector:
    1. Re-score all candidates in both pools using score_unified()
    2. Compute mean composite score per pipeline
    3. Record which pipeline wins

    Reports fraction of configs where state-aware wins.
    This quantifies whether the result depends on the specific weight choice.
    """

def run_ablation_analysis(merged: MergedRanking) -> list[SensitivityResult]:
    """Set each weight component to 0 in turn, renormalize, re-score.

    4 ablation configs:
    - reference_similarity=0
    - druglikeness=0
    - docking_proxy=0
    - state_specificity=0

    If state_specificity=0 and state-aware still wins, the advantage
    is NOT from structural bias.
    """

def run_weight_sweep(
    merged: MergedRanking,
    component: str,
    values: list[float],
) -> list[SensitivityResult]:
    """Sweep one component's weight across a range, renormalize others.

    Example: sweep state_specificity from 0.0 to 0.5 in 0.05 increments.
    """
```

**Key implementation note:** To re-score candidates, you need to call `score_unified()` from `ranking/scoring.py` with different weight dicts. The MergedRanking object contains all candidate SMILES, so you can re-derive scores. Import `score_unified` and `_validate_weights` from `ranking.scoring`.

### `tests/test_statistics.py`

Target: ~25-30 tests.

1. **Mann-Whitney U:**
   - `test_mann_whitney_identical()` — same distribution, p > 0.05
   - `test_mann_whitney_shifted()` — shifted distribution, p < 0.05
   - `test_mann_whitney_effect_size()` — known shift, verify Cohen's d > 0

2. **Bootstrap CI:**
   - `test_bootstrap_ci_contains_mean()` — CI contains true mean ~95% of time
   - `test_bootstrap_ci_reproducible()` — same seed = same result
   - `test_bootstrap_ci_narrow_with_more_data()` — more data = tighter CI

3. **Effect sizes:**
   - `test_cohens_d_identical()` — returns 0.0
   - `test_cohens_d_known_shift()` — shift of 1 std = d ~1.0
   - `test_cliff_delta_range()` — always in [-1, 1]
   - `test_cliff_delta_identical()` — returns 0.0

4. **Permutation test:**
   - `test_permutation_identical()` — p > 0.05
   - `test_permutation_shifted()` — p < 0.05
   - `test_permutation_reproducible()` — seeded

5. **Sensitivity analysis:**
   - `test_sensitivity_all_configs_valid()` — all weight configs sum to 1.0
   - `test_sensitivity_result_counts()` — wins + losses + ties = n_configs
   - `test_ablation_four_configs()` — exactly 4 results
   - `test_ablation_weights_sum_to_one()` — renormalized weights valid
   - `test_weight_sweep_correct_count()` — len(results) == len(values)

## Files to Modify

### `src/statebind/evaluation/comparison.py`

Add optional statistical results to `ComparativeResult`:

```python
@dataclass
class ComparativeResult:
    # ... existing fields ...
    statistical_tests: list[StatisticalTest] = field(default_factory=list)
    sensitivity: SensitivitySummary | None = None
```

Update `run_full_comparison()` to accept optional `run_statistics=True`:
```python
def run_full_comparison(
    merged: MergedRanking,
    top_k: int = 10,
    run_statistics: bool = False,
) -> ComparativeResult:
    result = ComparativeResult(...)  # existing logic
    if run_statistics:
        try:
            from statebind.evaluation.statistics import mann_whitney_u, cohens_d, bootstrap_confidence_interval
            from statebind.evaluation.sensitivity import run_weight_sensitivity, run_ablation_analysis
            # Add statistical tests
            # Add sensitivity analysis
        except ImportError:
            pass  # scipy not available
    return result
```

### `src/statebind/evaluation/tables.py`

Add new table functions:
```python
def statistical_summary_table(result: ComparativeResult) -> list[dict]:
    """Format statistical test results as a table."""

def sensitivity_table(summary: SensitivitySummary) -> list[dict]:
    """Format sensitivity analysis as a table."""
```

### `src/statebind/evaluation/figures.py`

Add new ASCII figure functions:
```python
def statistical_summary_ascii(result: ComparativeResult) -> str:
    """ASCII visualization of CIs and p-values."""

def sensitivity_heatmap_ascii(summary: SensitivitySummary) -> str:
    """ASCII heatmap of weight sensitivity results."""
```

## Files NOT to Touch

- `src/statebind/baselines/*` — Workstreams 02/04 own these
- `src/statebind/ranking/scoring.py` — only import from it, don't modify
- `src/statebind/chemistry/*` — Workstream 01 owns this
- `src/statebind/generation/*`, `src/statebind/dynamics/*`, `src/statebind/context/*`, `src/statebind/structure/*`

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| `score_unified()` | `ranking/scoring.py:100-151` | Call with custom weight dicts for sensitivity analysis |
| `_validate_weights()` | `ranking/scoring.py:89-97` | Validate weight configs before re-scoring |
| `DEFAULT_WEIGHTS` | `ranking/scoring.py:40-45` | Starting point for sensitivity sweep |
| `MergedRanking` | `ranking/models.py` | Input data structure for all functions |
| `score_distribution_by_pipeline()` | `ranking/aggregation.py` | Extract score lists for statistical tests |
| `_bar()` | `evaluation/figures.py` | ASCII bar rendering helper for new figures |

## Definition of Done

- [ ] `statistics.py` with 5 functions (mann_whitney_u, bootstrap_ci, cohens_d, cliff_delta, permutation_test)
- [ ] `sensitivity.py` with 3 functions (run_weight_sensitivity, run_ablation_analysis, run_weight_sweep)
- [ ] `comparison.py` updated with optional statistical_tests and sensitivity fields
- [ ] `tables.py` updated with 2 new table functions
- [ ] `figures.py` updated with 2 new ASCII figure functions
- [ ] `tests/test_statistics.py` with 25+ tests
- [ ] All functions work without scipy (permutation fallback or skip)
- [ ] All existing 359+ tests pass
- [ ] Seeded randomness for reproducibility

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
