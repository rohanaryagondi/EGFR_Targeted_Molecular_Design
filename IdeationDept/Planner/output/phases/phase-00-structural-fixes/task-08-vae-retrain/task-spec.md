---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T08
task_name: "VAE Retrain (3-State)"
implementation_plan_ref: "P1: Fix Structural Annotations (VAE retrain portion)"
status: completed
created: 2026-04-09T18:00:00Z
estimated_effort: "30 minutes GPU time"
conditional: true
condition: "Execute ONLY if P0-T07 ran (3-state switch). If T07 was skipped (4-state), SKIP this task."
---

# Task: VAE Retrain (3-State)

## CONDITIONAL TASK

**Execute ONLY if P0-T07 was completed (DFGout_aCout removed, n_states changed
from 4 to 3).** If T07 was skipped (4ZAU is DFGout, keeping 4 states), SKIP
this task entirely.

## Objective

Retrain the SELFIES VAE with `n_states=3` to produce a checkpoint compatible with
the updated 3-state model. Existing checkpoints have weight matrices dimensioned
for 4-state one-hot inputs and cannot be loaded with n_states=3.

## Context

The VAE's conditioning mechanism uses a one-hot state vector concatenated with the
latent code. When n_states changes from 4 to 3, the conditioning input dimension
changes, making old checkpoints incompatible. Retraining takes ~15-30 minutes on
an H200 GPU.

## Prerequisites

- [ ] P0-T07 completed (n_states=3 in all configs, DFGout_aCout removed from
      DEFAULT_STATE_MAPPING)
- [ ] All tests pass after T07's changes

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `configs/vae.yaml` | Verify n_states is 3 |
| `src/statebind/ml/vae.py` | VAE architecture (to understand conditioning) |
| `src/statebind/ml/vae_dataset.py` | DEFAULT_STATE_MAPPING (should have 3 entries) |
| `scripts/train_vae.py` | Existing VAE training script (if it exists) |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `scripts/retrain_vae_3state.slurm` | NEW | SLURM script for VAE retraining |
| `artifacts/models/vae/` | NEW | New 3-state checkpoint |

## Implementation Steps

1. **Verify T07 changes are in place:**
   ```bash
   grep "n_states" configs/vae.yaml  # Should show 3
   grep "DFGout_aCout" src/statebind/ml/vae_dataset.py  # Should find nothing
   ```

2. **Check for existing VAE training script:**
   ```bash
   ls scripts/train_vae* scripts/*vae*
   ```

3. **Create SLURM script** at `scripts/retrain_vae_3state.slurm`:
   ```bash
   #!/bin/bash
   #SBATCH --job-name=vae_3state
   #SBATCH --output=logs/%x_%j.out
   #SBATCH --error=logs/%x_%j.err
   #SBATCH -p gpu_devel
   #SBATCH -A pi_mg269
   #SBATCH --gpus=h200:1
   #SBATCH --cpus-per-task=4
   #SBATCH --mem=16G
   #SBATCH -t 01:00:00

   module load miniconda
   eval "$(conda shell.bash hook)"
   conda activate <appropriate-env>

   cd "$HOME/projects/statebind/repo"
   mkdir -p logs artifacts/models/vae

   # GPU diagnostics
   nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

   python scripts/train_vae.py --config configs/vae.yaml --selfies
   ```

   Adjust the conda environment name. Use `gpu_devel` partition for quick
   turnaround (has H200 GPUs).

4. **Submit the job:**
   ```bash
   mkdir -p logs
   sbatch scripts/retrain_vae_3state.slurm
   ```

5. **Monitor completion:**
   ```bash
   squeue -u rag88
   sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
   ```

6. **Verify the new checkpoint:**
   - Check that a new checkpoint file exists in `artifacts/models/vae/`
   - Verify it loads correctly with n_states=3:
     ```python
     python -c "
     from statebind.ml.vae import SELFIESVAE, VAEConfig
     config = VAEConfig(n_states=3)
     model = SELFIESVAE(config)
     # Attempt to load checkpoint
     import torch
     ckpt = torch.load('artifacts/models/vae/<checkpoint_file>', map_location='cpu')
     model.load_state_dict(ckpt)
     print('Checkpoint loaded successfully with n_states=3')
     "
     ```

7. **Record results** -- no formal artifact needed beyond the checkpoint itself,
   but note training loss and validation metrics in the progress log.

## Verification

- [ ] SLURM job completes successfully
- [ ] New checkpoint exists in `artifacts/models/vae/`
- [ ] Checkpoint loads with n_states=3 configuration
- [ ] Training loss converges (check log file)
- [ ] VAE validity (SELFIES-based) remains high (this is expected since validity
      comes from SELFIES, not state conditioning)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- This is a **compute task** (SLURM job management), not a code task.
- If the VAE training script doesn't exist, check `scripts/` for any training
  scripts that can be adapted. The script should use `configs/vae.yaml` which
  now has n_states=3.
- Use `-A pi_mg269` for the SLURM account.
- The `gpu_devel` partition has both H200 and RTX 5000 Ada GPUs. Use H200 for
  faster training.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **Do not retrain pre-2010/pre-2015 VAEs** at this stage. Those will be retrained
  when needed for retrospective evaluation (Phase 1). Only the main VAE needs
  retraining now.
- **The SELFIES tokenizer** is independent of n_states, so no tokenizer changes
  are needed.
- **Training data** is the same as before -- only the conditioning dimension changes.
  Each molecule's state label will be one of 3 states instead of 4.
- **Molecules that were labeled DFGout_aCout** in the training data: these should
  no longer exist in the dataset after T07's changes to DEFAULT_STATE_MAPPING.
  Verify the dataset builder doesn't crash on missing states.
