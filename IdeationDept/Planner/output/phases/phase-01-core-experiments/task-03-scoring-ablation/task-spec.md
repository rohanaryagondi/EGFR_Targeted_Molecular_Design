---
phase: "Phase 1: Core Experiments"
task_id: P1-T03
task_name: "Scoring Ablation + Fairness Script"
implementation_plan_ref: "P10: Scoring Component Ablation (Ablation E), P11: 3-Component Scoring Fairness Check"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "1-2 days"
---

# Task: Scoring Ablation + Fairness Script

## Objective

Create a script that systematically ablates each scoring component to identify
which component drives enrichment (P10), and specifically tests whether enrichment
survives without the state_specificity component (P11 -- the 3-component fairness
check). This answers: "Is enrichment driven by physics (GNINA), learned patterns
(MPNN), or the state label itself?"

## Context

The unified scoring function has 4 components with DEFAULT_WEIGHTS:
- reference_similarity: 0.35
- druglikeness: 0.30
- docking_proxy: 0.20
- state_specificity: 0.15

If state_specificity drives enrichment, the result is circular (state labels help
because we reward state labels). If GNINA drives it, the result is robust (physics
validates the state-conditioned pocket geometries). Reviewers will demand this analysis.

## Prerequisites

- [x] Phase 0 complete
- [x] Existing scored candidates in artifacts/ (from prior pipeline runs)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/ranking/scoring.py:125-136` | DEFAULT_WEIGHTS and SCORING_METHOD |
| `src/statebind/ranking/scoring.py:248-404` | score_unified(), rank_static_baseline(), rank_state_aware() |
| `src/statebind/ranking/models.py` | RankedPool, UnifiedScoredCandidate, PipelineLabel |
| `src/statebind/evaluation/statistics.py:119-266` | bootstrap CI functions |
| `src/statebind/evaluation/retrospective.py:169-360` | enrichment factor, BEDROC, enrichment with CI |
| `scripts/run_retrospective_validation.py` | How the full evaluation pipeline runs |
| `artifacts/ranking/` | Existing scored candidate artifacts |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/run_scoring_ablation.py` | -- | Complete scoring ablation script |
| NEW: `src/statebind/evaluation/scoring_ablation.py` | -- | Ablation logic as reusable module |
| NEW: `tests/test_scoring_ablation.py` | -- | Tests for ablation weight manipulation |

## Implementation Steps

1. **Create `src/statebind/evaluation/scoring_ablation.py`**:

   ```python
   from __future__ import annotations

   from pydantic import BaseModel, Field

   class AblationConfig(BaseModel):
       """Configuration for a single scoring ablation run."""
       name: str = Field(description="Human-readable ablation name")
       weights: dict[str, float] = Field(description="Component weights for this ablation")
       zeroed_component: str | None = Field(default=None, description="Which component was zeroed")

   class AblationResult(BaseModel):
       """Results from a single scoring ablation."""
       config: AblationConfig
       ef_at_10: float
       ef_ci_lower: float
       ef_ci_upper: float
       bedroc: float
       bedroc_ci_lower: float
       bedroc_ci_upper: float
       mean_score: float
       n_candidates: int
   ```

   Functions:
   a. **`generate_ablation_configs(base_weights) -> list[AblationConfig]`**:
      - "baseline": original weights (control)
      - For each component: zero it, renormalize remaining weights to sum to 1.0
      - "3-component" (P11): zero state_specificity specifically
      - Returns 5 configs total: 1 baseline + 4 ablations

   b. **`rerank_with_weights(candidates, weights) -> list[UnifiedScoredCandidate]`**:
      - Takes existing scored candidates (with per-component scores)
      - Recomputes composite score using new weights
      - Re-ranks by new composite score
      - Does NOT re-compute individual component scores (those are fixed)

   c. **`run_ablation_battery(candidates, future_drugs, base_weights, ...) -> list[AblationResult]`**:
      - For each ablation config: rerank, compute EF@10 with BCa CIs, compute BEDROC
      - Returns list of AblationResult

2. **Create `scripts/run_scoring_ablation.py`**:

   CLI script that:
   - Loads scored candidates from `artifacts/ranking/` (both static and state-aware)
   - Loads future drug reference list from retrospective module
   - Calls `run_ablation_battery()` for state-aware candidates
   - Outputs JSON artifact at `artifacts/evaluation/scoring_ablation.json`
   - Prints summary table showing EF@10 [CI] for each ablation

3. **Create `tests/test_scoring_ablation.py`**:

   - Test `generate_ablation_configs`: verify 5 configs, weights sum to 1.0,
     correct component zeroed
   - Test `rerank_with_weights`: verify reranking changes order when weights change
   - Test weight renormalization: zeroing a 0.35 component should distribute to others
   - Test edge cases: all weights zero (should raise), single component

## Verification

- [ ] `generate_ablation_configs(DEFAULT_WEIGHTS)` produces 5 configs
- [ ] All ablation weight dicts sum to 1.0 (within floating point tolerance)
- [ ] `rerank_with_weights` changes candidate ranking when weights change
- [ ] Script runs on existing artifacts without error
- [ ] `pytest tests/test_scoring_ablation.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- Follow StateBind conventions: typed Python, Pydantic v2 models, config-driven
- The key insight: re-ranking does NOT require re-scoring. The per-component scores
  are already computed. We only recompute the weighted sum and re-sort.
- Use `bca_bootstrap_confidence_interval()` from evaluation/statistics.py
- Use `compute_bedroc()` from evaluation/retrospective.py
- Do NOT modify ranking/scoring.py or DEFAULT_WEIGHTS. This script reads existing
  scores and applies different weight vectors.
- Round all scores to 4 decimal places

## Notes and Gotchas

- **Renormalization is critical**: when zeroing a component, remaining weights must
  sum to 1.0. Example: zeroing reference_similarity (0.35) → remaining 0.30+0.20+0.15
  = 0.65 → renormalize to 0.4615+0.3077+0.2308.
- **Per-component scores must already be stored**: check that existing artifacts
  contain individual component scores, not just the composite. If not, the script
  needs to re-score from SMILES (which is expensive).
- **The 3-component check (P11) is a specific instance** of the general ablation:
  zeroing state_specificity. If enrichment persists, the advantage comes from
  multi-pocket docking diversity, not from the state-aware scoring component.
- **This analysis is done on STATE-AWARE candidates only** (the static pipeline
  doesn't use state_specificity anyway -- it's always 0 for static).
