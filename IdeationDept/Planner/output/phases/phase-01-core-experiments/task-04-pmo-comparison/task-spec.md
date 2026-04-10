---
phase: "Phase 1: Core Experiments"
task_id: P1-T04
task_name: "PMO Comparison Infrastructure"
implementation_plan_ref: "P7: Compute-Matched PMO Comparison"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "1-2 days"
---

# Task: PMO Comparison Infrastructure

## Objective

Create the infrastructure for a compute-matched comparison between static and
state-aware pipelines using a fixed oracle budget of N=500 GNINA docking calls
per pipeline. This addresses the current 30 vs 461 candidate ratio (15:1 oracle
call imbalance) that makes the existing comparison unfair.

## Context

The implementation plan flags the compute imbalance as a critical fairness issue.
The static pipeline docks ~30 candidates while the state-aware pipeline docks ~461.
Under equal oracle budgets, the enrichment advantage may shrink or disappear. The
PMO (Practical Molecular Optimization) framework from Gao et al. 2022 provides
the standard for compute-matched comparisons in molecular design.

## Prerequisites

- [x] Phase 0 complete
- [x] GNINA available on the cluster (check with `which gnina` or `bin/gnina`)
- [x] Existing generation pipeline functional

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/chemistry/docking.py:346-524` | dock_molecule(), dock_batch() -- GNINA interface |
| `src/statebind/baselines/pipeline.py` | Static baseline pipeline -- how to generate more analogs |
| `src/statebind/generation/generator.py` | State-aware generation strategies |
| `src/statebind/ranking/scoring.py:248-404` | score_unified(), rank functions |
| `scripts/run_static_baseline.py` | How static pipeline is currently run |
| `scripts/generate_state_conditioned_candidates.py` | How state-aware pipeline runs |
| `configs/docking.yaml` | Docking configuration and receptor paths |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/run_pmo_comparison.py` | -- | Complete PMO comparison script |
| NEW: `src/statebind/evaluation/pmo_comparison.py` | -- | PMO budget tracking and analysis |
| NEW: `tests/test_pmo_comparison.py` | -- | Tests for budget tracking logic |

## Implementation Steps

1. **Create `src/statebind/evaluation/pmo_comparison.py`**:

   ```python
   class OracleBudget(BaseModel):
       """Tracks oracle (GNINA docking) call consumption."""
       total_budget: int = Field(default=500)
       calls_used: int = Field(default=0)
       results: list[dict] = Field(default_factory=list)

       @property
       def remaining(self) -> int: ...
       def record_call(self, smiles: str, score: float) -> None: ...

   class PMOResult(BaseModel):
       """Results from a PMO-style comparison."""
       pipeline: str  # "static" or "state_aware"
       budget: int
       calls_used: int
       top_10_avg_score: float
       ef_at_10: float | None
       ef_ci_lower: float | None
       ef_ci_upper: float | None
       bedroc: float | None
       auc_curve: list[dict]  # [{oracle_calls: int, top_10_avg: float}, ...]
   ```

   Functions:
   a. **`run_pipeline_with_budget(pipeline, budget, dock_fn) -> PMOResult`**:
      - Generate candidates (many more than budget)
      - Pre-filter by cheap descriptors (druglikeness, MW, etc.)
      - Dock top-N by pre-filter score, where N = budget
      - Track AUC: top-10 average score vs number of oracle calls used
      - Return results

   b. **`compare_pmo(static_result, state_aware_result) -> dict`**:
      - Compare AUC curves
      - Compute enrichment under equal budgets
      - Statistical comparison if multiple seeds available

2. **Create `scripts/run_pmo_comparison.py`**:

   CLI script that:
   - Accepts `--budget N` (default 500)
   - Runs static pipeline: generate from 1M17, pre-filter, dock top-N
   - Runs state-aware pipeline: generate across 3 states, pre-filter, dock top-N
   - Both use GNINA docking (same receptor prep, same scoring)
   - Outputs JSON artifact at `artifacts/evaluation/pmo_comparison.json`
   - Prints comparison table

   This script DOES require GNINA and will submit SLURM jobs for the docking
   portion. Use `-p priority -A prio_gerstein`.

3. **Create `tests/test_pmo_comparison.py`**:

   - Test `OracleBudget` tracks calls correctly
   - Test budget exhaustion raises appropriate error
   - Test AUC curve accumulation
   - Test comparison logic with mock results

## Verification

- [ ] `OracleBudget(total_budget=10)` correctly tracks and limits calls
- [ ] Script accepts `--budget` argument and validates it
- [ ] PMOResult serializes to JSON correctly
- [ ] `pytest tests/test_pmo_comparison.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- This task creates the CODE infrastructure only. Actual docking execution
  happens in P1-T08.
- The pre-filter step is critical: generate many candidates (1000+), then dock
  only the top-500 by cheap pre-filter score. This simulates how a real pipeline
  would allocate a fixed compute budget.
- Pre-filter scoring should use descriptors only (no GNINA) -- druglikeness,
  reference similarity (Tanimoto), and property filters.
- GNINA docking is the "oracle call" -- each call costs ~30 seconds per molecule.
- For the static pipeline, the existing `baselines/pipeline.py` generates analogs
  from a single structure (1M17). May need to increase the number of analogs
  generated to have a large enough pool for pre-filtering.

## Notes and Gotchas

- **Pre-filter bias**: The pre-filter scoring function should NOT include GNINA
  scores (that would use oracle calls before the budget). Use only cheap
  descriptors: Tanimoto to reference binders, druglikeness (QED or Lipinski),
  property ranges.
- **Equal budget means equal GNINA calls**, not equal candidates generated.
  The state-aware pipeline may generate more candidates (from 3 states) but
  only docks the top-500 by pre-filter score.
- **AUC curve**: Track how top-10 average score improves as more oracle calls
  are made. This follows the PMO benchmark convention.
- **Receptor preparation**: Both pipelines must use the same prepared receptor
  files. Static uses only 1M17; state-aware uses 3 receptors (1m17, 2gs7, 3w2r).
  But the budget is per-pipeline, not per-receptor.
