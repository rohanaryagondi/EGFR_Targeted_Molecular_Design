---
phase: "Phase 1: Core Experiments"
task_id: P1-T12
task_name: "ABL1 Model Training (VAE + MPNN)"
implementation_plan_ref: "P12: Multi-Kinase Extension -- ABL1 (step 5)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: ABL1 Model Training (VAE + MPNN)

## Objective

Train ABL1-specific VAE and MPNN models using the curated ABL1 data and verified
structural annotations. The MPNN uses scaffold split from day 1 (lesson from EGFR).

## Context

ABL1 models are trained separately from EGFR -- each kinase gets its own VAE
(state-conditioned generation) and MPNN (affinity prediction). ABL1 has genuine
DFGout structures, so the state conditioning may show a stronger effect than EGFR.

**This task is conditional on Gate G2 (GO or PIVOT).** If G2 is NO-GO, this task
is skipped.

## Prerequisites

- [x] P1-T09 completed (ABL1 features, conditioning, docking config)
- [x] G2 = GO or PIVOT (if NO-GO, skip this task)
- [x] ABL1 bioactivity data at `data/processed/abl1_affinity.json`
- [x] ABL1 structure annotations verified

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `scripts/prepare_vae_data.py` | How to prepare VAE training data (template for ABL1) |
| `scripts/prepare_mpnn_data.py` | How to prepare MPNN training data |
| `scripts/train_vae.py` | VAE training script |
| `scripts/train_mpnn.py` | MPNN training script |
| `configs/vae.yaml` | EGFR VAE config (template for ABL1) |
| `configs/mpnn.yaml` | EGFR MPNN config (template) |
| `src/statebind/ml/affinity_dataset.py` | scaffold_split() function |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `configs/vae_abl1.yaml` | -- | ABL1-specific VAE config |
| NEW: `configs/mpnn_abl1.yaml` | -- | ABL1 MPNN config with split_type=scaffold |
| NEW: `scripts/prepare_abl1_vae_data.py` | -- | ABL1 VAE data prep |
| NEW: `scripts/prepare_abl1_mpnn_data.py` | -- | ABL1 MPNN data prep |
| NEW: `scripts/slurm_abl1_training.sh` | -- | SLURM script for ABL1 training |

## Implementation Steps

1. **Determine ABL1 state count**:

   Based on P1-T09 results, ABL1 may have 3 or 4 states. Check:
   - How many distinct DFG/aC states were verified?
   - If ABL1 has genuine DFGout_aCout (unlike EGFR), use n_states=4
   - If not, use n_states=3 (matching EGFR)

2. **Prepare ABL1 VAE training data**:

   Create `scripts/prepare_abl1_vae_data.py`:
   - Read `data/processed/abl1_affinity.json`
   - Assign each compound to a conformational state based on co-crystal structure
     or nearest-neighbor in chemical space (same approach as EGFR)
   - Split into train/val sets
   - Output `data/processed/abl1_smiles_train.json` and `*_val.json`

3. **Create ABL1 VAE config** (`configs/vae_abl1.yaml`):

   Copy `configs/vae.yaml` and modify:
   - `n_states`: 3 or 4 (based on step 1)
   - `checkpoint_dir`: `artifacts/models/vae_abl1/`
   - `output_path`: `artifacts/generation/vae_abl1_candidates.json`
   - Keep all other hyperparameters identical to EGFR

4. **Prepare ABL1 MPNN training data**:

   Create `scripts/prepare_abl1_mpnn_data.py`:
   - Read `data/processed/abl1_affinity.json`
   - Convert SMILES to molecular graphs (same format as EGFR)
   - Output `data/processed/abl1_affinity_graphs.json`

5. **Create ABL1 MPNN config** (`configs/mpnn_abl1.yaml`):

   Copy `configs/mpnn.yaml` and modify:
   - `split_type: scaffold` (NOT random -- lesson from EGFR)
   - `checkpoint_dir`: `artifacts/models/mpnn_abl1/`

6. **Create SLURM training script** (`scripts/slurm_abl1_training.sh`):

   Array job with 2 tasks: VAE training and MPNN training.
   ```bash
   #SBATCH -p priority
   #SBATCH -A prio_gerstein
   #SBATCH --gpus=h200:1
   #SBATCH --cpus-per-task=4
   #SBATCH --mem=32G
   #SBATCH -t 04:00:00
   #SBATCH --array=0-1
   ```
   Task 0: VAE training. Task 1: MPNN training.

7. **Verify training results**:

   - ABL1 VAE: check convergence (val_loss comparable to EGFR VAE)
   - ABL1 MPNN: report scaffold R^2 (expected lower than EGFR due to smaller
     dataset and higher assay heterogeneity)
   - If scaffold R^2 < 0.20 for ABL1: note in results but proceed (MPNN is
     supplementary, not critical for ABL1)

## Verification

- [ ] ABL1 VAE trains to convergence (val_loss in reasonable range)
- [ ] ABL1 MPNN scaffold R^2 reported
- [ ] Checkpoints saved: `artifacts/models/vae_abl1/` and `artifacts/models/mpnn_abl1/`
- [ ] Training logs saved for reproducibility
- [ ] SLURM jobs completed on priority queue
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- **Scaffold split from day 1**: ABL1 MPNN must use `split_type: scaffold`.
  No random split allowed.
- Use priority queue: `-p priority -A prio_gerstein`
- If ABL1 dataset is small (< 200 compounds), reduce batch_size and increase
  training epochs to compensate.
- ABL1 state assignment requires domain knowledge -- check whether ChEMBL
  compounds have co-crystal structures that indicate DFG state.
- All configs must be YAML, following the vae.yaml/mpnn.yaml pattern.

## Notes and Gotchas

- **ABL1 data may be smaller than EGFR**: EGFR had ~6000 training samples for VAE.
  ABL1 may have fewer. Adjust expectations for VAE quality accordingly.
- **Assay heterogeneity**: ABL1 ChEMBL data comes from many different assays.
  The MPNN may see more noise. Scaffold R^2 may be lower than EGFR (0.5153).
- **State assignment for ChEMBL compounds**: Most compounds won't have co-crystal
  structures. May need to assign based on scaffold similarity to known type-I
  vs type-II inhibitors, or by DFG pharmacophore features.
- **If G2 = PIVOT**: Still train ABL1 models, but note that the framing will
  change from "state conditioning improves generation" to "multi-pocket docking
  provides diversity benefit."
