#!/bin/bash
#SBATCH --job-name=ablation_c_v2
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH -t 04:00:00

# Ablation C v2 analysis: corrected 3-seed conditioned vs 3-seed unconditioned.
#
# Prerequisites:
#   - artifacts/generation/vae_conditioned_seed{42,123,7}.json must exist
#   - artifacts/generation/vae_unconditioned_candidates_seed_{42,123,7}.json must exist
#   - Both from correct 3-state / 1-state models trained across 3 seeds

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================================"
echo "  Ablation C v2 Analysis"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  Python: $(python --version)"
echo "========================================================"
echo ""

# Verify candidate files exist
for SEED in 42 123 7; do
    COND="artifacts/generation/vae_conditioned_seed${SEED}.json"
    UNCOND="artifacts/generation/vae_unconditioned_candidates_seed_${SEED}.json"
    if [ ! -f "$COND" ]; then
        echo "ERROR: Missing conditioned candidates: $COND"
        exit 1
    fi
    if [ ! -f "$UNCOND" ]; then
        echo "ERROR: Missing unconditioned candidates: $UNCOND"
        exit 1
    fi
    echo "  OK: $COND"
    echo "  OK: $UNCOND"
done
echo ""

# GPU not needed for scoring (uses CPU-based docking proxy)
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU visible (CPU-only scoring)"

echo "Starting Ablation C v2 analysis at $(date)"
python scripts/run_ablation_c_analysis_v2.py
echo "Completed Ablation C v2 analysis at $(date)"
