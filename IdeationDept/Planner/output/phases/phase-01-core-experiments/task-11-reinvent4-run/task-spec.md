---
phase: "Phase 1: Core Experiments"
task_id: P1-T11
task_name: "REINVENT 4 EGFR Run + Gate G3"
implementation_plan_ref: "P9: REINVENT 4 Baseline on EGFR (part 2 -- execution)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "3-5 days"
---

# Task: REINVENT 4 EGFR Run + Gate G3

## Objective

Run REINVENT 4 against the EGFR 1M17 pocket using GNINA scoring, then score
the generated candidates with StateBind's unified scoring function and compute
enrichment metrics. This provides the external baseline comparison.

## Context

REINVENT 4 represents the state-of-the-art in RL-based molecular optimization.
By running it with GNINA docking on the same EGFR receptor (1M17), we create
a fair external baseline: same scoring oracle, no state conditioning. If
StateBind's state-aware pipeline beats REINVENT 4, it demonstrates that state
conditioning adds value beyond what a strong generic generator achieves.

## Prerequisites

- [x] P1-T06 completed (REINVENT 4 environment, GNINA plugin, configs)
- [x] REINVENT 4 installed in `reinvent4` conda environment
- [x] GNINA scoring component tested with single molecule
- [x] Prepared 1M17 receptor at `data/processed/docking/receptors/`

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `scripts/run_reinvent4_egfr.py` | Wrapper script from P1-T06 |
| `scripts/reinvent4_gnina_component.py` | GNINA scoring component from P1-T06 |
| `configs/reinvent4_egfr.toml` | REINVENT 4 configuration |
| `scripts/slurm_reinvent4.sh` | SLURM script from P1-T06 |
| `src/statebind/ranking/scoring.py:248-404` | Unified scoring for downstream comparison |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/score_reinvent4_candidates.py` | -- | Score REINVENT candidates with unified function |

## Implementation Steps

1. **Submit REINVENT 4 SLURM job**:

   ```bash
   sbatch scripts/slurm_reinvent4.sh
   ```

   Monitor with `squeue -u rag88`. Expected runtime: 8-24 hours depending on
   step count and docking speed.

2. **Monitor and verify REINVENT 4 run**:

   - Check that REINVENT logs show molecules being generated and scored
   - Verify GNINA scoring component is receiving SMILES and returning scores
   - Check for error rates: what fraction of molecules fail docking?
   - If the run fails, diagnose from logs and resubmit

3. **Collect REINVENT 4 candidates**:

   The wrapper script (`run_reinvent4_egfr.py`) should output candidates to
   `artifacts/generation/reinvent4_egfr_candidates.json` in StateBind format:
   ```json
   {
     "candidates": [
       {"smiles": "...", "source": "reinvent4", "gnina_score": X.X}
     ]
   }
   ```

4. **Score with unified function**:

   Create `scripts/score_reinvent4_candidates.py`:
   - Load REINVENT candidates
   - Score each with `score_unified()` from ranking/scoring.py
   - Compute: reference_similarity, druglikeness, docking_proxy, state_specificity
   - Note: state_specificity will be 0 for REINVENT candidates (no state assignment)
   - Output scored candidates to `artifacts/ranking/reinvent4_scored.json`

5. **Compute enrichment metrics**:

   - Run retrospective enrichment analysis on REINVENT candidates
   - Compute EF@10, BEDROC(alpha=20) with BCa bootstrap CIs
   - Compare with StateBind state-aware pipeline enrichment

6. **Compile Gate G3 assessment**:

   Create `artifacts/evaluation/reinvent4_results.json`:
   ```json
   {
     "gate": "G3",
     "n_valid_docked": N,
     "recommendation": "GO|CONDITIONAL_GO|NO_GO",
     "reinvent4_ef_at_10": X.X,
     "statebind_ef_at_10": X.X,
     "comparison": "StateBind wins by X.X / REINVENT wins / comparable"
   }
   ```

   Gate G3 criteria:
   - 100+ valid docked molecules: **GO**
   - Slow but functional (>10 min/mol): **CONDITIONAL GO** (reduce N)
   - GNINA integration fails: **NO-GO** (fall back to Vina scoring)

7. **Update decisions-needed.md** with G3 result.

## Verification

- [ ] REINVENT 4 run completes without errors
- [ ] 100+ valid docked molecules produced (Gate G3 primary criterion)
- [ ] Candidates scored with unified function (all 4 components)
- [ ] Enrichment metrics computed with BCa CIs
- [ ] Comparison with StateBind state-aware pipeline reported
- [ ] Gate G3 decision recorded in decisions-needed.md
- [ ] Results artifact at `artifacts/evaluation/reinvent4_results.json`
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- REINVENT 4 runs in its own conda environment. Activate with:
  `conda activate reinvent4`
- After collecting REINVENT candidates, switch back to the statebind environment
  for scoring and analysis.
- SLURM jobs use priority queue: `-p priority -A prio_gerstein`
- If REINVENT takes > 24 hours, consider reducing the number of steps or
  molecules per step in the config.
- The enrichment comparison is the key deliverable: does StateBind state-aware
  beat REINVENT 4 (no states) under the same GNINA scoring?

## Notes and Gotchas

- **Two environments**: REINVENT runs in `reinvent4` env; scoring runs in
  statebind env. Do NOT mix these.
- **GNINA rate**: ~30s per molecule. 128 molecules/step = ~1 hour/step.
  500 steps = ~500 hours. Reduce to ~50-100 steps for feasibility, or
  increase parallelism.
- **REINVENT candidates have no state assignment**: state_specificity will
  be 0 (since candidates aren't associated with any conformational state).
  This is expected and fair -- REINVENT doesn't use state information.
- **If GNINA fails for > 50% of molecules**: This indicates a systematic
  issue with the 3D conversion or receptor setup. Investigate before continuing.
- **Fallback (Gate G3 NO-GO)**: If GNINA integration truly fails, REINVENT
  can still be run with AutoDock Vina scoring as a fallback. Less comparable
  but still valid as an external baseline.
