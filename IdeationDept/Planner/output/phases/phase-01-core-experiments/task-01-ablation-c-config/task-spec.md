---
phase: "Phase 1: Core Experiments"
task_id: P1-T01
task_name: "Ablation C Config + Data Prep"
implementation_plan_ref: "P6: Ablation C -- Unconditioned VAE"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "0.5 day"
---

# Task: Ablation C Config + Data Prep

## Objective

Create the configuration, data preparation script, and SLURM script needed to
train an unconditioned VAE for Ablation C -- the thesis test. With n_states=1
and all molecules assigned to state 0, the one-hot vector is a constant [1.0],
making the conditioning input carry zero information. This is mathematically
equivalent to no conditioning while preserving identical architecture and
parameter count.

## Context

Ablation C is the project's most critical experiment. If the unconditioned VAE
achieves the same enrichment as the conditioned VAE, state conditioning provides
no value and the thesis fails. The pre-registration document (commit 9e7cf96)
specifies Cohen's d >= 0.5 as the GO threshold. This task creates the
infrastructure; actual training happens in P1-T07.

## Prerequisites

- [x] Phase 0 complete (3-state model adopted, VAE retrained)
- [x] Pre-registration committed (9e7cf96)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `configs/vae.yaml` | Reference config for the conditioned VAE -- unconditioned must match all hyperparameters except n_states |
| `src/statebind/ml/vae.py:69-95` | VAEConfig class -- verify n_states field behavior |
| `src/statebind/ml/vae_dataset.py:41-89` | DEFAULT_STATE_MAPPING and SMILESDatasetConfig -- understand state encoding |
| `data/processed/egfr_smiles_train.json` | Training data format -- understand state label structure |
| `scripts/train_vae.py:1-60` | Training script interface -- understand CLI args and config loading |
| `scripts/generate_vae_candidates.py:33,147-242` | Generation script -- STATE_NAMES hardcoded, per-state loop |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `configs/vae_unconditioned.yaml` | -- | Copy of vae.yaml with n_states=1 |
| NEW: `scripts/prepare_ablation_c_data.py` | -- | Remap all state labels to "unconditioned" |
| NEW: `scripts/slurm_ablation_c.sh` | -- | SLURM array job for 3-seed training |
| `scripts/generate_vae_candidates.py` | 33 | Make STATE_NAMES configurable (read from config or checkpoint) instead of hardcoded |

## Implementation Steps

1. **Create `configs/vae_unconditioned.yaml`**:

   Copy `configs/vae.yaml` exactly, then change ONLY:
   ```yaml
   model:
     n_states: 1    # was 3
   ```
   All other hyperparameters (hidden_dim, latent_dim, embed_dim, dropout,
   kl_weight, epochs, batch_size, lr, temperature, etc.) MUST be identical.
   Change checkpoint_dir to `artifacts/models/vae_unconditioned/`.
   Change generation output_path to `artifacts/generation/vae_unconditioned_candidates.json`.

2. **Create `scripts/prepare_ablation_c_data.py`**:

   This script reads the existing training data and remaps all state labels:
   ```python
   # Read data/processed/egfr_smiles_train.json
   # For each entry, replace the "state" field with "unconditioned"
   # Write to data/processed/egfr_smiles_unconditioned_train.json
   # Same for egfr_smiles_val.json -> egfr_smiles_unconditioned_val.json
   ```
   The script should:
   - Accept `--input-dir` and `--output-dir` arguments
   - Log how many entries were remapped and from which original states
   - Preserve all other fields (smiles, metadata, etc.) unchanged
   - Use `from __future__ import annotations`, typed functions

3. **Make `scripts/generate_vae_candidates.py` flexible about state names**:

   Currently line 33 hardcodes: `STATE_NAMES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]`

   Change to derive state names from the checkpoint's n_states or a CLI argument:
   ```python
   # Add --states CLI argument (optional, comma-separated)
   # If not provided, derive from checkpoint config:
   #   n_states=3 -> ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin"]
   #   n_states=1 -> ["unconditioned"]
   # Keep backward compatibility: default behavior unchanged
   ```

4. **Create `scripts/slurm_ablation_c.sh`**:

   SLURM array job for 3 seeds (42, 123, 7):
   ```bash
   #!/bin/bash
   #SBATCH --job-name=ablation_c
   #SBATCH --output=logs/ablation_c_%A_%a.out
   #SBATCH --error=logs/ablation_c_%A_%a.err
   #SBATCH -p priority
   #SBATCH -A prio_gerstein
   #SBATCH --gpus=h200:1
   #SBATCH --cpus-per-task=4
   #SBATCH --mem=32G
   #SBATCH -t 02:00:00
   #SBATCH --array=0-2

   SEEDS=(42 123 7)
   SEED=${SEEDS[$SLURM_ARRAY_TASK_ID]}

   # Train
   python scripts/train_vae.py \
       --config configs/vae_unconditioned.yaml \
       --seed $SEED \
       --data-dir data/processed/ \
       --train-file egfr_smiles_unconditioned_train.json \
       --val-file egfr_smiles_unconditioned_val.json \
       --checkpoint-dir artifacts/models/vae_unconditioned/seed_${SEED}/

   # Generate
   python scripts/generate_vae_candidates.py \
       --config configs/vae_unconditioned.yaml \
       --checkpoint artifacts/models/vae_unconditioned/seed_${SEED}/best_model.pt \
       --states unconditioned \
       --n-per-state 300 \
       --output artifacts/generation/vae_unconditioned_seed${SEED}.json
   ```

   Note: `--n-per-state 300` for unconditioned (1 state) matches conditioned's
   100/state x 3 states = 300 total. Verify this matches the actual conditioned
   generation count by checking `artifacts/generation/vae_candidates.json`.

## Verification

- [ ] `configs/vae_unconditioned.yaml` exists and differs from `vae.yaml` ONLY in
      n_states (1 vs 3), checkpoint_dir, and output_path
- [ ] `python scripts/prepare_ablation_c_data.py` runs without error and produces
      `data/processed/egfr_smiles_unconditioned_train.json` with all states = "unconditioned"
- [ ] `generate_vae_candidates.py --states unconditioned` works with a dummy checkpoint
      (or at least parses args correctly)
- [ ] `scripts/slurm_ablation_c.sh` is a valid SLURM script (check with `sbatch --test-only`)
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- Follow StateBind conventions: `from __future__ import annotations`, type annotations,
  Pydantic v2 for any models, config-driven
- The prepare script is straightforward JSON manipulation -- keep it simple
- Do NOT modify the VAE model code (vae.py) or training loop (train_vae.py) --
  the n_states=1 config is sufficient
- When modifying generate_vae_candidates.py, maintain backward compatibility:
  running without `--states` should produce identical behavior to current code
- SLURM scripts use priority queue: `-p priority -A prio_gerstein`
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`

## Notes and Gotchas

- The key insight: with n_states=1, the one-hot is always [1.0]. The encoder
  concatenates this constant to every embedding timestep, and the decoder
  concatenates it with z before projecting to hidden state. A constant adds
  zero information -- mathematically identical to no conditioning.
- The conditioned VAE generates 100 molecules per state x 3 states = 300 total.
  The unconditioned must generate 300 total to match. Verify the exact count
  from existing artifacts before hardcoding.
- `train_vae.py` reads config from YAML, so changing n_states in the config
  file is sufficient -- no code changes needed for training.
- The `--seed` flag in train_vae.py controls the random seed. Verify it exists;
  if not, the task agent should add it (simple argparse addition).
- Make sure `logs/` directory exists before submitting SLURM: `mkdir -p logs`
