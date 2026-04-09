#!/bin/bash
#SBATCH --job-name=vae_3state
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --requeue

# P0-T08: Retrain VAE with 3 conformational states (DFGout_aCout removed).
# Old checkpoint had 4-state one-hot input dim; this produces a compatible
# 3-state checkpoint at artifacts/models/vae/best_model.pt.

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/models/vae

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================"
echo "P0-T08: VAE 3-State Retraining (SELFIES)"
echo "========================================"
echo "Node:     $(hostname)"
echo "Date:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Python:   $(python --version)"
echo ""

# GPU diagnostics
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
python -c "
import torch
print(f'PyTorch:  {torch.__version__}')
print(f'CUDA:     {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU:      {torch.cuda.get_device_name(0)}')
"
echo ""

# ── Back up old 4-state checkpoint (if exists) ───────────────────────────
if [ -f artifacts/models/vae/best_model.pt ]; then
    echo "Backing up old 4-state checkpoint..."
    cp artifacts/models/vae/best_model.pt artifacts/models/vae/best_model_4state_backup.pt
    echo "Backup saved to artifacts/models/vae/best_model_4state_backup.pt"
    echo ""
fi

# ── Train VAE with 3-state conditioning ──────────────────────────────────
echo "Training VAE (SELFIES mode, n_states=3)..."
echo "Config: configs/vae.yaml"
echo "Start:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_vae.py --config configs/vae.yaml --selfies

echo ""
echo "========================================"
echo "VAE 3-state retraining complete"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

# ── Verify checkpoint loads with n_states=3 ──────────────────────────────
echo ""
echo "Verifying checkpoint compatibility..."
python -c "
import torch
from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig

ckpt = torch.load('artifacts/models/vae/best_model.pt', map_location='cpu', weights_only=False)
stored_config = ckpt.get('vae_config', {})
n_states = stored_config.get('n_states', 'UNKNOWN')
print(f'Checkpoint n_states: {n_states}')
print(f'Checkpoint epoch:    {ckpt.get(\"epoch\", \"UNKNOWN\")}')
print(f'Checkpoint metrics:  {ckpt.get(\"metrics\", {})}')

# Verify it loads into a 3-state model
config = VAEConfig(**stored_config)
model = ConditionalSMILESVAE(config)
model.load_state_dict(ckpt['model_state_dict'])
print(f'Model loaded successfully with n_states={config.n_states}')
print(f'Total parameters: {sum(p.numel() for p in model.parameters()):,}')
"
echo ""
echo "P0-T08 COMPLETE"
