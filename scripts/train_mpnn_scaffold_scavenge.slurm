#!/bin/bash
#SBATCH --job-name=mpnn_scaffold
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00

# P0-T05: MPNN Scaffold Split Evaluation (Gate G1) -- scavenge_gpu
# Preemptable but faster to schedule.

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/evaluation

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================"
echo "P0-T05: MPNN Scaffold Split Evaluation"
echo "========================================"
echo "Node:     $(hostname)"
echo "Date:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Python:   $(python --version)"
echo ""

# GPU diagnostics
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""

python -c "
import torch
print(f'PyTorch:  {torch.__version__}')
print(f'CUDA:     {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU:      {torch.cuda.get_device_name(0)}')
    props = torch.cuda.get_device_properties(0)
    print(f'Memory:   {props.total_memory / 1e9:.1f} GB')
"
echo ""

python scripts/evaluate_mpnn_scaffold.py --config configs/mpnn.yaml

echo ""
echo "========================================"
echo "P0-T05 COMPLETE"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"
