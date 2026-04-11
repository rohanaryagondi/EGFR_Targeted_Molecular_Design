#!/bin/bash
#SBATCH --job-name=tfm_uc_ext
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=1
#SBATCH --requeue
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH --array=0-6

# Extended seeds for unconditioned Transformer VAE (Ablation C null).
# Adds 7 seeds to existing {42, 123, 7} for n=10 total.
#
# Array indices map to seeds:
#   0 -> 13
#   1 -> 37
#   2 -> 99
#   3 -> 256
#   4 -> 314
#   5 -> 512
#   6 -> 777

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

# ── Seed mapping ─────────────────────────────────────────────────────────
SEEDS=(13 37 99 256 314 512 777)
SEED=${SEEDS[$SLURM_ARRAY_TASK_ID]}

CKPT_DIR="artifacts/models/transformer_vae_unconditioned/seed_${SEED}"
GEN_OUTPUT="artifacts/generation/transformer_vae_unconditioned_seed${SEED}.json"
CONFIG_OVERRIDE="/tmp/transformer_vae_uncond_seed_${SEED}_${SLURM_JOB_ID}.yaml"

echo "========================================================"
echo "  Transformer VAE — Unconditioned Extended Seeds"
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

with open('configs/transformer_vae_unconditioned.yaml') as f:
    cfg = yaml.safe_load(f)

cfg['training']['seed'] = ${SEED}
cfg['training']['checkpoint_dir'] = '${CKPT_DIR}/'
cfg['training']['log_dir'] = '${CKPT_DIR}/logs/'

with open('${CONFIG_OVERRIDE}', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)

print(f'Config written to ${CONFIG_OVERRIDE}')
print(f'  model.n_states = {cfg[\"model\"][\"n_states\"]}')
print(f'  training.seed = {cfg[\"training\"][\"seed\"]}')
print(f'  training.checkpoint_dir = {cfg[\"training\"][\"checkpoint_dir\"]}')
"
echo ""

# ── Verify data files exist ──────────────────────────────────────────────
if [ ! -f data/processed/egfr_smiles_unconditioned_train.json ]; then
    echo "ERROR: Training data not found: data/processed/egfr_smiles_unconditioned_train.json"
    exit 1
fi
if [ ! -f data/processed/egfr_smiles_unconditioned_val.json ]; then
    echo "ERROR: Validation data not found: data/processed/egfr_smiles_unconditioned_val.json"
    exit 1
fi

# ── Train unconditioned Transformer VAE ────────────────────────────────
echo "Training Transformer VAE (n_states=1, seed=${SEED})..."
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_transformer_vae.py \
    --config "${CONFIG_OVERRIDE}"

echo ""
echo "Training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Generate candidates ─────────────────────────────────────────────────
echo ""
echo "Generating 600 candidates (unconditioned, seed=${SEED})..."

python scripts/generate_transformer_vae.py \
    --config "${CKPT_DIR}/config.yaml" \
    --checkpoint "${CKPT_DIR}/best_model.pt" \
    --vocab "${CKPT_DIR}/vocabulary.json" \
    --n-per-state 600 --temperature 0.8 \
    --states "unconditioned" \
    --output "${GEN_OUTPUT}"

echo ""
echo "=== Greedy generation (temp=0.0, quality check) ==="

GEN_GREEDY="artifacts/generation/transformer_vae_unconditioned_seed${SEED}_greedy.json"
python scripts/generate_transformer_vae.py \
    --config "${CKPT_DIR}/config.yaml" \
    --checkpoint "${CKPT_DIR}/best_model.pt" \
    --vocab "${CKPT_DIR}/vocabulary.json" \
    --n-per-state 600 --temperature 0.0 \
    --states "unconditioned" \
    --output "${GEN_GREEDY}"

echo ""
echo "========================================================"
echo "  Unconditioned Transformer VAE seed=${SEED} COMPLETE"
echo "  Checkpoint: ${CKPT_DIR}/best_model.pt"
echo "  Stochastic: ${GEN_OUTPUT}"
echo "  Greedy:     ${GEN_GREEDY}"
echo "  Finished:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

# ── Cleanup temp config ─────────────────────────────────────────────────
rm -f "${CONFIG_OVERRIDE}"
