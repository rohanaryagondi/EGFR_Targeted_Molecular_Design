#!/bin/bash
#SBATCH --job-name=ablation_c
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00

module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"
cd "$HOME/projects/statebind/repo"
mkdir -p logs

# GPU diagnostics
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU visible (CPU-only scoring)"

echo "Starting Ablation C analysis at $(date)"
python scripts/run_ablation_c_analysis.py
echo "Completed Ablation C analysis at $(date)"
