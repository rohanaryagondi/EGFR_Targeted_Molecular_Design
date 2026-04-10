#!/bin/bash
#SBATCH --job-name=vae_diag_gpu
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 04:00:00

# VAE Enrichment Failure GPU Diagnostics
# 8 tests requiring VAE model inference (TEST-G1 through TEST-G8)
# See scripts/vae_diagnostic_gpu.py and docs/vae-diagnostic-investigation.md

set -euo pipefail

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/evaluation/vae_diagnostics

echo "========================================================"
echo "  VAE Enrichment Failure Diagnostics — GPU Tests"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  GPU:    $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "  Python: $(python --version)"
echo "========================================================"
echo ""

python scripts/vae_diagnostic_gpu.py --seed 42 --device auto

echo ""
echo "Completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Results in: artifacts/evaluation/vae_diagnostics/"
