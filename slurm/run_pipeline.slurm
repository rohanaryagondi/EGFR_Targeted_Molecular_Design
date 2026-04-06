#!/bin/bash
#SBATCH --job-name=statebind_pipeline
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 02:00:00

# Full StateBind pipeline: VAE generation + MPNN scoring + ADMET filtering + comparison
# Runs on GPU to support all ML model inference.

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/generation artifacts/ranking/figures

# GPU diagnostics
echo "=== GPU Info ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo "================"

# Step 1: Generate VAE candidates (100 per state, temperature 0.8)
echo ""
echo "========================================"
echo "STEP 1: VAE Candidate Generation"
echo "========================================"
python scripts/generate_vae_candidates.py \
    --checkpoint artifacts/models/vae/best_model.pt \
    --vocab artifacts/models/vae/vocabulary.json \
    --config artifacts/models/vae/config.yaml \
    --n-per-state 100 \
    --temperature 0.8 \
    --output artifacts/generation/vae_candidates.json

if [ $? -ne 0 ]; then
    echo "ERROR: VAE generation failed"
    exit 1
fi

# Step 2: Run full comparison with VAE, ADMET, and statistics
echo ""
echo "========================================"
echo "STEP 2: Full Comparison Pipeline"
echo "========================================"
python scripts/compare_baseline_vs_state_aware.py \
    --vae-candidates artifacts/generation/vae_candidates.json \
    --admet-filter \
    --statistics \
    --output-dir artifacts/ranking

echo ""
echo "========================================"
echo "Pipeline complete!"
echo "========================================"
