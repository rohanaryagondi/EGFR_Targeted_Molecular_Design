---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T04
task_name: "Bootstrap CIs + BEDROC"
implementation_plan_ref: "P4: Bootstrap Confidence Intervals + BEDROC"
status: pending
created: 2026-04-09T18:00:00Z
estimated_effort: "0.5-1 day"
---

# Task: Bootstrap CIs + BEDROC

## Objective

Upgrade the existing percentile bootstrap to BCa (bias-corrected and accelerated)
bootstrap with 10,000 iterations, and add BEDROC computation using RDKit. These
statistical tools are needed for Phase 1 experiments (Ablation C, enrichment
comparisons) to report rigorous confidence intervals.

## Context

The implementation plan requires "10,000-fold BCa bootstrap on EF@10, BEDROC(alpha=20),
mean scores." Currently, `evaluation/statistics.py` has a percentile bootstrap
(lines 115-147) with 1,000 iterations. This is insufficient: percentile bootstrap
can be biased for skewed distributions, and BCa corrects for both bias and
acceleration. BEDROC is the standard metric for early enrichment evaluation in
virtual screening, complementing EF@10.

## Prerequisites

- [ ] No prerequisites (independent of structural fixes)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/evaluation/statistics.py:1-148` | Existing bootstrap and statistical test infrastructure |
| `src/statebind/evaluation/retrospective.py:155-200` | Existing enrichment factor computation |
| `src/statebind/evaluation/__init__.py` | Exports to understand public API |
| `tests/test_statistics.py` | Existing tests for statistics module |
| `tests/test_retrospective.py` | Existing tests for retrospective module |
| `pyproject.toml:40-55` | Optional dependency groups (RDKit, scipy) |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/evaluation/statistics.py` | 115-147 | Add `bca_bootstrap_confidence_interval()` alongside existing percentile bootstrap |
| `src/statebind/evaluation/retrospective.py` | after line 197 | Add `compute_bedroc()` function |
| `tests/test_statistics.py` | append | Add tests for BCa bootstrap |
| `tests/test_retrospective.py` | append | Add tests for BEDROC |

## Implementation Steps

1. **Add BCa bootstrap function** in `evaluation/statistics.py` after line 147:

   ```python
   def bca_bootstrap_confidence_interval(
       values: list[float],
       statistic_fn: Callable[[list[float]], float],
       alpha: float = 0.05,
       n_bootstrap: int = 10000,
       seed: int = 42,
   ) -> BootstrapCI:
       """BCa (bias-corrected and accelerated) bootstrap CI.

       More accurate than percentile bootstrap for skewed distributions.
       Uses jackknife to estimate acceleration factor and bootstrap
       distribution to estimate bias correction.

       Requires scipy for norm.ppf. Falls back to percentile bootstrap
       if scipy is not available.
       """
   ```

   Implementation:
   a. Compute point estimate: `theta_hat = statistic_fn(values)`
   b. Generate `n_bootstrap` bootstrap resamples and compute statistic for each.
   c. **Bias correction (z0):**
      - Count how many bootstrap estimates are less than `theta_hat`
      - `z0 = norm.ppf(count / n_bootstrap)` (using scipy.stats.norm)
   d. **Acceleration factor (a):**
      - Compute jackknife estimates: for each i, compute statistic on values
        with i-th element removed
      - `theta_dot = mean of jackknife estimates`
      - `a = sum((theta_dot - jack_i)^3) / (6 * sum((theta_dot - jack_i)^2)^1.5)`
   e. **Adjusted percentiles:**
      - `z_alpha_lower = norm.ppf(alpha / 2)`
      - `z_alpha_upper = norm.ppf(1 - alpha / 2)`
      - `a1 = norm.cdf(z0 + (z0 + z_alpha_lower) / (1 - a * (z0 + z_alpha_lower)))`
      - `a2 = norm.cdf(z0 + (z0 + z_alpha_upper) / (1 - a * (z0 + z_alpha_upper)))`
      - `lower = percentile(boot_stats, 100 * a1)`
      - `upper = percentile(boot_stats, 100 * a2)`
   f. Return `BootstrapCI` with the BCa-corrected bounds.
   g. **Fallback:** If scipy is not available, log a warning and call the existing
      `bootstrap_confidence_interval()` (percentile method).

2. **Add BEDROC function** in `evaluation/retrospective.py` after `compute_enrichment_factor()`:

   ```python
   def compute_bedroc(
       scores: list[float],
       actives: list[bool],
       alpha: float = 20.0,
   ) -> float:
       """BEDROC (Boltzmann-Enhanced Discrimination of ROC).

       Uses rdkit.ML.Scoring.Scoring.CalcBEDROC for computation.
       Higher alpha emphasizes early enrichment more strongly.

       Args:
           scores: Predicted scores (higher = better predicted activity).
           actives: Boolean flags indicating which entries are true actives.
           alpha: Exponential weight parameter. 20.0 is standard for virtual screening.

       Returns:
           BEDROC value in [0, 1]. 1.0 = perfect early enrichment.

       Raises:
           ImportError: If RDKit is not available.
       """
   ```

   Implementation:
   a. Import RDKit scoring:
      ```python
      try:
          from rdkit.ML.Scoring.Scoring import CalcBEDROC
          HAS_RDKIT_SCORING = True
      except ImportError:
          HAS_RDKIT_SCORING = False
      ```
   b. Pair scores with active flags, sort by score descending.
   c. Create the sorted activity list (1 for active, 0 for inactive) that
      `CalcBEDROC` expects.
   d. Call `CalcBEDROC(sorted_actives, n_actives, alpha)`.
   e. Return the BEDROC value rounded to 4 decimal places.

3. **Add integrated enrichment + CI function** in `evaluation/retrospective.py`:

   ```python
   def compute_enrichment_with_ci(
       candidate_similarities: list[float],
       threshold: float = 0.4,
       top_k: int = 10,
       alpha: float = 0.05,
       n_bootstrap: int = 10000,
       seed: int = 42,
   ) -> dict:
       """Compute EF@10 and BEDROC with BCa bootstrap confidence intervals."""
   ```

   This function:
   a. Computes EF@10 point estimate using existing `compute_enrichment_factor()`
   b. Computes BEDROC point estimate using new `compute_bedroc()`
   c. Computes BCa bootstrap CIs for both metrics
   d. Returns a dict with point estimates and CIs for each metric

4. **Update module exports** in `evaluation/__init__.py` if needed.

5. **Write tests** for BCa bootstrap in `tests/test_statistics.py`:

   a. **Test BCa with symmetric distribution:** BCa CI should be close to
      percentile CI for symmetric data (normal distribution).
   b. **Test BCa with skewed distribution:** BCa CI should differ from percentile
      CI (shifted toward the skew-corrected bounds).
   c. **Test BCa produces valid bounds:** lower < point_estimate < upper.
   d. **Test BCa with scipy fallback:** Mock scipy unavailability, verify it
      falls back to percentile and logs a warning.
   e. **Test n_bootstrap=10000 default:** Verify the default is 10000.

6. **Write tests** for BEDROC in `tests/test_retrospective.py`:

   a. **Test BEDROC with perfect ranking:** All actives ranked first -> BEDROC ~ 1.0.
   b. **Test BEDROC with random ranking:** BEDROC ~ fraction of actives.
   c. **Test BEDROC with worst ranking:** All actives ranked last -> BEDROC ~ 0.0.
   d. **Test BEDROC alpha parameter:** Higher alpha should penalize late actives more.
   e. **Test BEDROC without RDKit:** Mock RDKit unavailability, verify ImportError.

## Verification

- [ ] `bca_bootstrap_confidence_interval()` returns valid `BootstrapCI` objects
- [ ] BCa CIs are narrower than or equal to percentile CIs on test data
- [ ] `compute_bedroc()` returns float in [0, 1] range
- [ ] `compute_bedroc()` with alpha=20 and perfect ranking returns ~1.0
- [ ] `pytest tests/test_statistics.py tests/test_retrospective.py -v` passes
- [ ] `pytest -v --tb=short` -- full test suite passes (646+)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- Follow StateBind conventions: `from __future__ import annotations`, type
  annotations, optional deps with fallback.
- scipy is in `[science]` extras. RDKit is in `[chemistry]`/`[ml]` extras.
  Both must be optional with clean error messages.
- **Do not modify** the existing `bootstrap_confidence_interval()` function. Add
  the BCa version alongside it. Existing code that uses the percentile version
  should continue to work unchanged.
- Round all scores to 4 decimal places (project convention).
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **BCa edge cases:** If all bootstrap estimates equal the point estimate (zero
  variance), BCa will fail with division by zero in the acceleration calculation.
  Handle this by returning the point estimate as both bounds with a warning.
- **BEDROC input format:** `CalcBEDROC` expects a sorted list of 0/1 values (sorted
  by predicted score descending) and the total number of actives. Read the RDKit
  docs or source to confirm the exact expected input format.
- **Jackknife cost:** BCa with jackknife is O(n * n_bootstrap + n^2). For large n,
  this may be slow. The retrospective datasets are small (30-500 candidates), so
  this should be fine.
- **Existing `BootstrapCI` dataclass:** Reuse the existing `BootstrapCI` return type
  from `statistics.py`. It already has all needed fields.
