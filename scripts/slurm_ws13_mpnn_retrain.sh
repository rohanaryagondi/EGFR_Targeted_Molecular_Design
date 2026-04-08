#!/bin/bash
#SBATCH --job-name=ws13_mpnn_retrain
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00

# WS13: Retrain MPNN on pre-cutoff time-split datasets (pre-2010, pre-2015)
# This provides the most scientifically rigorous retrospective validation.

set -euo pipefail

REPO="$HOME/projects/statebind/repo/.claude/worktrees/ws13-retro"
cd "$REPO"
mkdir -p logs

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================"
echo "WS13 MPNN Retraining on GPU"
echo "========================================"
echo "Node:     $(hostname)"
echo "Date:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Python:   $(python --version)"
echo ""

# GPU diagnostics
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""

# Verify CUDA torch
python -c "
import torch
print(f'PyTorch:  {torch.__version__}')
print(f'CUDA:     {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU:      {torch.cuda.get_device_name(0)}')
    print(f'Memory:   {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
echo ""

# Verify datasets exist
echo "Checking datasets..."
python -c "
import json
for cutoff in [2010, 2015]:
    path = f'data/processed/timesplit_{cutoff}_train.json'
    with open(path) as f:
        data = json.load(f)
    print(f'  timesplit_{cutoff}_train.json: {len(data)} compounds')
"
echo ""

# ── Train on pre-2010 data ───────────────────────────────────────────────
echo "========================================"
echo "Training MPNN on pre-2010 data"
echo "========================================"
echo "Config: configs/mpnn_pre2010.yaml"
echo "Start:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_mpnn.py --config configs/mpnn_pre2010.yaml

echo ""
echo "Pre-2010 training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Train on pre-2015 data ───────────────────────────────────────────────
echo "========================================"
echo "Training MPNN on pre-2015 data"
echo "========================================"
echo "Config: configs/mpnn_pre2015.yaml"
echo "Start:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_mpnn.py --config configs/mpnn_pre2015.yaml

echo ""
echo "Pre-2015 training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Verify outputs ───────────────────────────────────────────────────────
echo "========================================"
echo "Verifying outputs"
echo "========================================"

for cutoff in 2010 2015; do
    ckpt="artifacts/models/mpnn_pre${cutoff}/best_model.pt"
    metrics="artifacts/evaluation/mpnn_pre${cutoff}_metrics.json"
    card="artifacts/models/mpnn_pre${cutoff}/model_card.json"

    echo ""
    echo "--- Cutoff ${cutoff} ---"
    if [ -f "$ckpt" ]; then
        echo "  Checkpoint: $ckpt ($(du -h "$ckpt" | cut -f1))"
    else
        echo "  ERROR: Checkpoint not found: $ckpt"
    fi

    if [ -f "$metrics" ]; then
        echo "  Metrics:"
        python -c "
import json
with open('$metrics') as f:
    m = json.load(f)
print(f'    Best epoch: {m[\"best_epoch\"]}')
print(f'    Val loss:   {m[\"best_val_loss\"]}')
for k, v in m['test_metrics'].items():
    print(f'    Test {k:>8s}: {v}')
print(f'    Train size: {m[\"dataset_summary\"][\"n_train\"]}')
print(f'    Time:       {m[\"training_time_seconds\"]}s')
"
    else
        echo "  ERROR: Metrics not found: $metrics"
    fi

    if [ -f "$card" ]; then
        echo "  Model card: $card"
    else
        echo "  WARNING: Model card not found: $card"
    fi
done

echo ""
echo "========================================"
echo "WS13 MPNN Retraining COMPLETE"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"
