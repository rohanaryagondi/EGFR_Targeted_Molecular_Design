#!/bin/bash
#SBATCH --job-name=ablation_c
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-2

# P1-T07: Ablation C — Train unconditioned VAE across 3 seeds.
#
# Array indices map to seeds:
#   0 -> 42
#   1 -> 123
#   2 -> 7
#
# Each task:
#   1. Prepares a per-seed config (overrides training.seed and checkpoint_dir)
#   2. Trains the unconditioned VAE (n_states=1)
#   3. Generates 300 candidates (1 state x 300) to match conditioned total (3 x 100)
#
# Prerequisites:
#   - Run: python scripts/prepare_ablation_c_data.py
#   - Verify: data/processed/egfr_smiles_unconditioned_train.json exists
#   - Config: configs/vae_unconditioned.yaml exists

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

CKPT_DIR="artifacts/models/vae_unconditioned/seed_${SEED}"
GEN_OUTPUT="artifacts/generation/vae_unconditioned_candidates_seed_${SEED}.json"
CONFIG_OVERRIDE="/tmp/vae_unconditioned_seed_${SEED}_${SLURM_JOB_ID}.yaml"

echo "========================================================"
echo "  Ablation C — Unconditioned VAE Training"
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

with open('configs/vae_unconditioned.yaml') as f:
    cfg = yaml.safe_load(f)

cfg['training']['seed'] = ${SEED}
cfg['training']['checkpoint_dir'] = '${CKPT_DIR}/'

with open('${CONFIG_OVERRIDE}', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)

print(f'Config written to ${CONFIG_OVERRIDE}')
print(f'  training.seed = {cfg[\"training\"][\"seed\"]}')
print(f'  training.checkpoint_dir = {cfg[\"training\"][\"checkpoint_dir\"]}')
"
echo ""

# ── Verify data files exist ──────────────────────────────────────────────
if [ ! -f data/processed/egfr_smiles_unconditioned_train.json ]; then
    echo "ERROR: Unconditioned training data not found."
    echo "Run first: python scripts/prepare_ablation_c_data.py"
    exit 1
fi

# ── Train unconditioned VAE ──────────────────────────────────────────────
echo "Training unconditioned VAE (seed=${SEED})..."
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_vae.py \
    --config "${CONFIG_OVERRIDE}" \
    --selfies

echo ""
echo "Training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── Generate candidates ─────────────────────────────────────────────────
# 300 per state x 1 state = 300 total (matches conditioned: 100 x 3 states)
echo ""
echo "Generating 300 unconditioned candidates (seed=${SEED})..."

python scripts/generate_vae_candidates.py \
    --config "${CKPT_DIR}/config.yaml" \
    --checkpoint "${CKPT_DIR}/best_model.pt" \
    --vocab "${CKPT_DIR}/vocabulary.json" \
    --n-per-state 300 \
    --states unconditioned \
    --output "${GEN_OUTPUT}"

echo ""
echo "========================================================"
echo "  Ablation C seed=${SEED} COMPLETE"
echo "  Checkpoint: ${CKPT_DIR}/best_model.pt"
echo "  Candidates: ${GEN_OUTPUT}"
echo "  Finished:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

# ── Cleanup temp config ─────────────────────────────────────────────────
rm -f "${CONFIG_OVERRIDE}"
