---
phase: "Phase 1: Core Experiments"
task_id: P1-T07
task_name: "Ablation C Training + Generation (GPU)"
implementation_plan_ref: "P6: Ablation C -- Unconditioned VAE (training + generation)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: Ablation C Training + Generation (GPU)

## Objective

Train the unconditioned VAE (n_states=1) across 3 random seeds and generate
candidates from each checkpoint. This is the compute-intensive step of Ablation C.
The analysis of results happens in P1-T10.

## Context

The pre-registration (commit 9e7cf96) specifies 3+ random seeds for Ablation C.
Each seed trains an independent unconditioned VAE with identical architecture and
hyperparameters to the conditioned model, differing only in n_states (1 vs 3).
Multiple seeds allow computing Cohen's d across runs.

## Prerequisites

- [x] P1-T01 completed (configs, data prep, SLURM script ready)
- [x] Unconditioned training data at `data/processed/egfr_smiles_unconditioned_train.json`
- [x] `configs/vae_unconditioned.yaml` exists with n_states=1

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `configs/vae_unconditioned.yaml` | Verify n_states=1 and all other params match vae.yaml |
| `scripts/slurm_ablation_c.sh` | SLURM script prepared in P1-T01 |
| `scripts/train_vae.py` | Training script CLI args |
| `scripts/generate_vae_candidates.py` | Generation script, verify --states flag works |
| `artifacts/generation/vae_candidates.json` | Check conditioned generation count (to match total) |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| No source code changes | -- | This is a compute execution task |

## Implementation Steps

1. **Verify prerequisites from P1-T01**:

   - Confirm `configs/vae_unconditioned.yaml` exists with n_states=1
   - Confirm `data/processed/egfr_smiles_unconditioned_train.json` exists
   - Confirm `generate_vae_candidates.py` supports `--states` flag
   - Check conditioned generation total: read `artifacts/generation/vae_candidates.json`,
     count total valid candidates. The unconditioned run must generate the same total.

2. **Prepare output directories**:

   ```bash
   mkdir -p artifacts/models/vae_unconditioned/seed_{42,123,7}
   mkdir -p artifacts/generation/ablation_c/
   mkdir -p logs/
   ```

3. **Submit SLURM array job**:

   ```bash
   sbatch scripts/slurm_ablation_c.sh
   ```

   This submits 3 jobs (array 0-2) on the priority queue, each training one seed.
   Monitor with `squeue -u rag88`.

4. **Verify training completed successfully**:

   For each seed (42, 123, 7):
   - Check that `artifacts/models/vae_unconditioned/seed_${SEED}/best_model.pt` exists
   - Check training logs for convergence (final val_total_loss should be in same
     range as conditioned model: ~2.2-2.5)
   - Check that training ran for the full 300 epochs (or early-stopped reasonably)

5. **Verify generation completed**:

   For each seed:
   - Check `artifacts/generation/vae_unconditioned_seed${SEED}.json` exists
   - Verify total candidate count matches conditioned total
   - Log validity rate, uniqueness rate per seed

6. **Collect summary statistics**:

   Create a summary JSON at `artifacts/generation/ablation_c/summary.json`:
   ```json
   {
     "generated_at": "2026-...",
     "seeds": [42, 123, 7],
     "per_seed": {
       "42": {"total": 300, "valid": ..., "unique": ..., "val_loss": ...},
       "123": {"total": 300, "valid": ..., "unique": ..., "val_loss": ...},
       "7": {"total": 300, "valid": ..., "unique": ..., "val_loss": ...}
     },
     "conditioned_total": ...,
     "notes": "Unconditioned VAE (n_states=1) for Ablation C"
   }
   ```

## Verification

- [ ] 3 SLURM jobs completed successfully (check `sacct`)
- [ ] 3 checkpoints exist: `artifacts/models/vae_unconditioned/seed_*/best_model.pt`
- [ ] 3 generation artifacts exist with correct candidate counts
- [ ] Training loss convergence is comparable to conditioned model
- [ ] Summary JSON written to `artifacts/generation/ablation_c/summary.json`
- [ ] No tests needed (compute execution task), but verify 669+ tests still pass
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- This is primarily a COMPUTE task -- the main work is submitting SLURM jobs
  and monitoring results.
- Use priority queue: `-p priority -A prio_gerstein`
- If a seed fails, diagnose from SLURM logs and resubmit that seed only.
- Expected training time: ~20-30 minutes per seed on H200 (similar to the
  conditioned VAE retrain in P0-T08 which took 21.4 min).
- Do NOT modify any source code in this task.
- If the SLURM script from P1-T01 has issues, fix it and document changes.

## Notes and Gotchas

- **Monitor GPU memory**: n_states=1 uses slightly less memory than n_states=3
  (smaller input dimension). Should not be an issue.
- **Deterministic seeds**: The training script's `--seed` flag should set both
  PyTorch and NumPy seeds for reproducibility. Verify this.
- **Generation temperature**: Use 0.8 (matching conditioned). This is set in
  the config or via `--temperature` flag.
- **Total candidate count**: The conditioned VAE generates 100/state x 3 states
  = 300 total per run. Verify this from the actual artifact, as the config
  may differ (e.g., vae.yaml says n_samples_per_state: 100 under generation).
- **If early stopping triggers**: The model may stop before 300 epochs. This is
  fine -- it indicates convergence. Report the actual epoch count.
