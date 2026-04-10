#!/bin/bash
#SBATCH --job-name=cond_vae_3s
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=1
#SBATCH --requeue
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-2

# Ablation C redo: Train 3-state conditioned VAE across 3 seeds.
#
# Array indices map to seeds:
#   0 -> 42
#   1 -> 123
#   2 -> 7
#
# Each task:
#   1. Creates per-seed config override (seed + checkpoint_dir)
#   2. Trains conditioned VAE (n_states=3, configs/vae.yaml) with SELFIES
#   3. Generates 100 candidates per state (3 states x 100 = 300 total)
#
# Prerequisites:
#   - data/processed/egfr_smiles_train.json exists
#   - data/processed/egfr_smiles_val.json exists
#   - configs/vae.yaml has n_states=3

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

# ── Seed mapping ─────────────────────────────────────────────────────────
SEEDS=(42 123 7)
SEED=${SEEDS[$SLURM_ARRAY_TASK_ID]}

CKPT_DIR="artifacts/models/vae_conditioned/seed_${SEED}"
GEN_OUTPUT="artifacts/generation/vae_conditioned_seed${SEED}.json"
CONFIG_OVERRIDE="/tmp/vae_conditioned_seed_${SEED}_${SLURM_JOB_ID}.yaml"

echo "========================================================"
echo "  Ablation C Redo — Conditioned VAE Training (3-state)"
echo "========================================================"
echo "  Array task: ${SLURM_ARRAY_TASK_ID}"
echo "  Seed:       ${SEED}"
echo "  Node:       $(hostname)"
echo "  Date:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  Python:     $(python --version)"
echo "  Checkpoint: ${CKPT_DIR}"
echo "  Generation: ${GEN_OUTPUT}"
echo "========================================================"
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

# ── Create per-seed config (override seed and checkpoint_dir) ────────────
mkdir -p "${CKPT_DIR}"

python -c "
import yaml

with open('configs/vae.yaml') as f:
    cfg = yaml.safe_load(f)

cfg['training']['seed'] = ${SEED}
cfg['training']['checkpoint_dir'] = '${CKPT_DIR}/'

with open('${CONFIG_OVERRIDE}', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)

print(f'Config written to ${CONFIG_OVERRIDE}')
print(f'  model.n_states = {cfg[\"model\"][\"n_states\"]}')
print(f'  training.seed = {cfg[\"training\"][\"seed\"]}')
print(f'  training.checkpoint_dir = {cfg[\"training\"][\"checkpoint_dir\"]}')
"
echo ""

# ── Verify data files exist ──────────────────────────────────────────────
if [ ! -f data/processed/egfr_smiles_train.json ]; then
    echo "ERROR: Training data not found: data/processed/egfr_smiles_train.json"
    exit 1
fi
if [ ! -f data/processed/egfr_smiles_val.json ]; then
    echo "ERROR: Validation data not found: data/processed/egfr_smiles_val.json"
    exit 1
fi

# ── Train conditioned VAE ───────────────────────────────────────────────
echo "Training conditioned VAE (n_states=3, seed=${SEED})..."
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_vae.py \
    --config "${CONFIG_OVERRIDE}" \
    --selfies

echo ""
echo "Training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Generate candidates ─────────────────────────────────────────────────
# 100 per state x 3 states = 300 total (matches unconditioned: 300 x 1 state)
echo ""
echo "Generating 100 candidates per state (3 states x 100 = 300 total, seed=${SEED})..."

python scripts/generate_vae_candidates.py \
    --config "${CKPT_DIR}/config.yaml" \
    --checkpoint "${CKPT_DIR}/best_model.pt" \
    --vocab "${CKPT_DIR}/vocabulary.json" \
    --n-per-state 100 \
    --states "DFGin_aCin,DFGin_aCout,DFGout_aCin" \
    --output "${GEN_OUTPUT}"

echo ""
echo "========================================================"
echo "  Conditioned VAE seed=${SEED} COMPLETE"
echo "  Checkpoint: ${CKPT_DIR}/best_model.pt"
echo "  Candidates: ${GEN_OUTPUT}"
echo "  Finished:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

# ── Cleanup temp config ─────────────────────────────────────────────────
rm -f "${CONFIG_OVERRIDE}"
