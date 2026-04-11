#!/bin/bash
#SBATCH --job-name=tvae_val
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH -t 01:00:00

# Transformer VAE full validation: reconstruction, generation quality,
# latent space analysis across all 6 trained models (3 cond + 3 uncond).

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================================"
echo "  Transformer VAE — Full Validation"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  GPU:    $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "========================================================"

python scripts/validate_transformer_vae_full.py

echo ""
echo "Done. Results at: artifacts/evaluation/transformer_vae_validation.json"
