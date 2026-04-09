---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T05
task_name: "MPNN Scaffold Split Evaluation (GPU)"
implementation_plan_ref: "P3: MPNN Scaffold + Temporal Split (evaluation portion)"
status: pending
created: 2026-04-09T18:00:00Z
estimated_effort: "2-4 hours (mostly SLURM wait time)"
---

# Task: MPNN Scaffold Split Evaluation (GPU)

## Objective

Train the MPNN model using scaffold split (implemented in P0-T03) and measure
the test-set R^2. This determines whether the MPNN remains a credible scoring
component (Gate G1: scaffold R^2 >= 0.35).

## Context

The current MPNN achieves R^2 = 0.69 with random split, but random splits are
known to inflate performance by leaking scaffold information between train and
test sets. The implementation plan expects degradation to 0.45-0.55 with scaffold
split, which would still pass Gate G1.

This task requires GPU compute (SLURM job submission). It is separated from the
code implementation (P0-T03) to keep code verification and GPU compute in
distinct tasks.

## Prerequisites

- [ ] P0-T03 completed (scaffold_split function implemented and tested)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/ml/affinity_dataset.py` | The updated split function from T03 |
| `src/statebind/ml/mpnn.py` | MPNN model architecture |
| `configs/mpnn.yaml` | MPNN training config |
| `scripts/train_mpnn.py` | Existing MPNN training script (if it exists) |
| `CLAUDE.md` | SLURM submission conventions |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `scripts/train_mpnn_scaffold.slurm` | NEW | SLURM script for scaffold-split training |
| `artifacts/evaluation/mpnn_scaffold_metrics.json` | NEW | Output metrics artifact |

## Implementation Steps

1. **Check for existing MPNN training script:**
   ```bash
   ls scripts/train_mpnn* scripts/*mpnn*
   ```
   If a training script exists, adapt it. If not, create one.

2. **Create or modify training script** to accept a `--split-type` argument:
   - If `scripts/train_mpnn.py` exists, add `--split-type scaffold` CLI argument
   - If not, create a minimal training script that:
     a. Loads config from `configs/mpnn.yaml`
     b. Builds dataset via `build_affinity_dataset()`
     c. Splits with `split_dataset(ds, split_type="scaffold")`
     d. Trains the MPNN
     e. Evaluates on test set (R^2, MSE, MAE)
     f. Writes metrics to `artifacts/evaluation/mpnn_scaffold_metrics.json`

3. **Create SLURM script** at `scripts/train_mpnn_scaffold.slurm`:
   ```bash
   #!/bin/bash
   #SBATCH --job-name=mpnn_scaffold
   #SBATCH --output=logs/%x_%j.out
   #SBATCH --error=logs/%x_%j.err
   #SBATCH -p gpu
   #SBATCH -A pi_mg269
   #SBATCH --gpus=rtx_5000_ada:1
   #SBATCH --cpus-per-task=4
   #SBATCH --mem=16G
   #SBATCH -t 02:00:00

   module load miniconda
   eval "$(conda shell.bash hook)"
   conda activate <appropriate-env>

   cd "$HOME/projects/statebind/repo"
   mkdir -p logs artifacts/evaluation

   python scripts/train_mpnn.py --split-type scaffold --config configs/mpnn.yaml
   ```

   Adjust the conda environment name to match what's available. Check with
   `conda env list`.

4. **Submit the job:**
   ```bash
   mkdir -p logs
   sbatch scripts/train_mpnn_scaffold.slurm
   ```

5. **Monitor completion:**
   ```bash
   squeue -u rag88
   # After completion:
   sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
   ```

6. **Record results** in the output artifact:
   ```json
   {
     "generated_at": "<UTC ISO timestamp>",
     "split_type": "scaffold",
     "seed": 42,
     "metrics": {
       "test_r2": <float>,
       "test_mse": <float>,
       "test_mae": <float>,
       "train_r2": <float>,
       "n_train": <int>,
       "n_val": <int>,
       "n_test": <int>,
       "n_unique_scaffolds": <int>,
       "n_train_scaffolds": <int>,
       "n_test_scaffolds": <int>
     },
     "gate_g1": {
       "criterion": "scaffold R^2 >= 0.35",
       "value": <float>,
       "outcome": "<GO | CONDITIONAL_GO | NO_GO>",
       "notes": "<interpretation>"
     },
     "comparison": {
       "random_split_r2": 0.69,
       "scaffold_split_r2": <float>,
       "degradation": <float>
     },
     "notes": "MPNN trained with scaffold split. See Gate G1 for evaluation."
   }
   ```

7. **Also run random split** for direct comparison (same training setup, only
   `split_type="random"`). Record both R^2 values.

## Verification

- [ ] SLURM job completes successfully (check logs for errors)
- [ ] Output artifact exists at `artifacts/evaluation/mpnn_scaffold_metrics.json`
- [ ] Scaffold R^2 is reported (not NaN or negative)
- [ ] Random-split R^2 is close to the reported 0.69 (sanity check)
- [ ] Gate G1 outcome is clearly stated
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion
      and G1 outcome

## Agent Instructions

- This is primarily a **compute task** (SLURM job management), not a code task.
- The code changes were done in P0-T03. This task just runs the training.
- If the SLURM job fails, check `logs/mpnn_scaffold_*.err` for error messages.
  Common issues: OOM (increase `--mem`), missing deps (check environment),
  timeout (increase `-t`).
- Use `-A pi_mg269` for the account. Use `-p gpu` with `--gpus=rtx_5000_ada:1`.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status AND the Gate G1 outcome.

## Notes and Gotchas

- **Environment setup:** Make sure the conda env has PyTorch, RDKit, and the
  statebind package installed (`pip install -e ".[ml]"`).
- **GPU memory:** RTX 5000 Ada has 32GB VRAM. MPNN training should be well within
  this limit.
- **Training time:** MPNN training on EGFR data is typically fast (< 30 min).
  The 2-hour SLURM limit is generous.
- **Multiple seeds:** The implementation plan mentions "3+ random seeds" for
  Ablation C, but for G1 evaluation a single seed is sufficient. If time permits,
  run 3 seeds and report mean +/- std R^2.
- **The `priority` partition** (`-p priority -A prio_gerstein`) may give faster
  scheduling if the `gpu` queue is busy.
