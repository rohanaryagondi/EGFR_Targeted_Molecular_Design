#!/bin/bash
#SBATCH --job-name=abl_c_10s
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH --array=0-1

# Ablation C v3 with 10 seeds: Transformer VAE conditioned vs unconditioned.
# Array job: task 0 = stochastic (T=0.8), task 1 = greedy (T=0.0)
# Seeds: 42, 123, 7, 13, 37, 99, 256, 314, 512, 777

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================================"
echo "  Ablation C v3 — 10 Seeds — Transformer VAE"
echo "  Array task: ${SLURM_ARRAY_TASK_ID}"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

if [ "${SLURM_ARRAY_TASK_ID}" -eq 0 ]; then
    echo "Mode: stochastic (T=0.8)"
    python scripts/run_ablation_c_analysis_v3.py --all-seeds
elif [ "${SLURM_ARRAY_TASK_ID}" -eq 1 ]; then
    echo "Mode: greedy (T=0.0)"
    python scripts/run_ablation_c_analysis_v3.py --greedy --all-seeds
fi

echo ""
echo "Done."
