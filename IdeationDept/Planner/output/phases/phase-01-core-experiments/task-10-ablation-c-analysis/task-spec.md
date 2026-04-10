---
phase: "Phase 1: Core Experiments"
task_id: P1-T10
task_name: "Ablation C Analysis + Gate G2"
implementation_plan_ref: "P6: Ablation C -- Unconditioned VAE (analysis), P8: VAE Metrics"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "1-2 days"
---

# Task: Ablation C Analysis + Gate G2

## Objective

Score unconditioned VAE candidates, compute enrichment metrics with confidence
intervals, calculate Cohen's d between conditioned and unconditioned distributions,
and apply VAE quality metrics. This produces the Gate G2 decision -- the most
important decision in the project.

## Context

The pre-registration (commit 9e7cf96) specifies:
- Cohen's d >= 0.5: GO (thesis supported)
- d in [0.3, 0.5): PIVOT (reframe as diversity benefit)
- d < 0.3: NO-GO (thesis not supported, ~20% probability)

This task computes the actual d value across 3+ seeds and makes the Gate G2
recommendation. The result determines whether ABL1 work (Waves 4-5) proceeds.

## Prerequisites

- [x] P1-T07 completed (3 unconditioned VAE seeds trained and generated)
- [x] P1-T02 completed (VAE quality metrics module available)
- [x] Unconditioned candidates at `artifacts/generation/vae_unconditioned_seed*.json`
- [x] Conditioned candidates at `artifacts/generation/vae_candidates.json`

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/evaluation/statistics.py:75-266` | cohens_d(), bca_bootstrap_confidence_interval() |
| `src/statebind/evaluation/retrospective.py:169-360` | compute_enrichment_factor(), compute_bedroc(), compute_enrichment_with_ci() |
| `src/statebind/evaluation/vae_metrics.py` | VAE quality metrics from P1-T02 |
| `src/statebind/ranking/scoring.py:248-404` | score_unified(), rank functions |
| `scripts/run_retrospective_validation.py` | How the full evaluation pipeline runs |
| `artifacts/generation/ablation_c/summary.json` | Training summary from P1-T07 |
| `data/processed/egfr_smiles_train.json` | Training set (for novelty metric) |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/run_ablation_c_analysis.py` | -- | Complete ablation C analysis pipeline |
| NEW: `scripts/slurm_ablation_c_scoring.sh` | -- | SLURM script for scoring (if GNINA needed) |

## Implementation Steps

1. **Score unconditioned candidates** for each seed:

   For each seed's candidates:
   a. Load candidates from `artifacts/generation/vae_unconditioned_seed${SEED}.json`
   b. Score with unified scoring function (same as conditioned)
   c. Store scored candidates

   If GNINA docking is required for scoring, submit SLURM jobs (up to 3 in
   parallel, one per seed) on priority queue.

2. **Run retrospective enrichment analysis** for each seed:

   Using the same cutoff years as the conditioned evaluation:
   a. Get future drugs list from `evaluation/retrospective.py`
   b. Compute EF@10 for each seed
   c. Compute BEDROC(alpha=20) for each seed
   d. Compute BCa bootstrap CIs (10,000 iterations) for each metric

3. **Compute Cohen's d**:

   ```python
   from statebind.evaluation.statistics import cohens_d

   # Collect EF@10 values across seeds
   conditioned_ef10 = [ef10_seed42_cond, ef10_seed123_cond, ef10_seed7_cond]
   unconditioned_ef10 = [ef10_seed42_uncond, ef10_seed123_uncond, ef10_seed7_uncond]

   d = cohens_d(conditioned_ef10, unconditioned_ef10)
   ```

   Note: The conditioned VAE may have only 1 seed (the current checkpoint).
   If so, run retrospective evaluation 3 times with bootstrap resampling to
   get a distribution, or retrain conditioned for 3 seeds as well (the
   conditioned model's pre-registration allows this).

   More robust: use per-molecule enrichment scores (not per-seed means) for
   the effect size computation. Each seed produces N scored molecules; Cohen's d
   compares the score distributions.

4. **Apply VAE quality metrics** to both models:

   ```python
   from statebind.evaluation.vae_metrics import evaluate_vae_quality

   # Conditioned VAE
   cond_metrics = evaluate_vae_quality(
       generated_smiles=conditioned_candidates,
       training_smiles=training_set,
   )

   # Unconditioned VAE (each seed)
   for seed in [42, 123, 7]:
       uncond_metrics = evaluate_vae_quality(
           generated_smiles=unconditioned_candidates[seed],
           training_smiles=training_set,
       )
   ```

   Report: FCD, reconstruction accuracy, novelty, internal diversity for both.

5. **Compile Gate G2 report**:

   Create `artifacts/evaluation/ablation_c_results.json`:
   ```json
   {
     "generated_at": "2026-...",
     "gate": "G2",
     "cohens_d": 0.XX,
     "recommendation": "GO|PIVOT|NO-GO",
     "conditioned": {
       "ef_at_10": {"point": X, "ci_lower": X, "ci_upper": X},
       "bedroc": {"point": X, "ci_lower": X, "ci_upper": X},
       "vae_metrics": {"fcd": X, "novelty": X, "diversity": X}
     },
     "unconditioned": {
       "per_seed": {
         "42": {"ef_at_10": X, "bedroc": X, "vae_metrics": {...}},
         "123": {"ef_at_10": X, "bedroc": X, "vae_metrics": {...}},
         "7": {"ef_at_10": X, "bedroc": X, "vae_metrics": {...}}
       },
       "mean_ef_at_10": X,
       "std_ef_at_10": X
     },
     "pre_registration_ref": "commit 9e7cf96",
     "notes": "..."
   }
   ```

6. **Update decisions-needed.md**:

   Add Gate G2 result to `IdeationDept/Planner/output/dashboard/decisions-needed.md`:
   ```
   | 4 | 2026-XX-XX | Ablation C result | G2 | GO/PIVOT/NO-GO | Cohen's d = X.XX; ... |
   ```

## Verification

- [ ] Cohen's d computed across 3+ seeds with correct pooled standard deviation
- [ ] BCa bootstrap uses 10,000 iterations
- [ ] BEDROC computed with alpha=20
- [ ] FCD scores reported for both conditioned and unconditioned
- [ ] Gate G2 recommendation matches pre-registered thresholds
- [ ] Results artifact at `artifacts/evaluation/ablation_c_results.json`
- [ ] decisions-needed.md updated with G2 outcome
- [ ] `pytest -v --tb=short` -- 669+ tests pass
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- This is the project's most important analysis. Double-check all computations.
- Use `bca_bootstrap_confidence_interval()` (not plain percentile bootstrap)
  for CIs. BCa corrects for bias and skewness.
- Cohen's d uses the `cohens_d()` function from evaluation/statistics.py which
  computes the pooled standard deviation.
- Round all scores to 4 decimal places (StateBind convention).
- The Gate G2 recommendation is a RECOMMENDATION -- the human operator makes
  the final decision. Present the data clearly.
- If the conditioned VAE has only 1 seed, note this limitation. Consider
  retraining conditioned for 3 seeds if time permits.

## Notes and Gotchas

- **Small N for Cohen's d**: With only 3 seeds, the d estimate has wide confidence
  intervals. Report this limitation. The per-molecule analysis (using individual
  enrichment scores) provides a more robust estimate.
- **FCD requires >= 100 molecules**: If a seed produces fewer than 100 valid
  molecules, FCD is unreliable. Log a warning.
- **BEDROC alpha=20**: This is the standard setting for early enrichment (emphasis
  on top-ranked molecules). Higher alpha = more emphasis on early ranking.
- **Pre-registration match**: Verify that the analysis exactly matches the
  pre-registration document. Any deviation must be disclosed.
- **If d is borderline (0.45-0.55)**: Flag this clearly. The decision is
  ambiguous and requires human judgment.
