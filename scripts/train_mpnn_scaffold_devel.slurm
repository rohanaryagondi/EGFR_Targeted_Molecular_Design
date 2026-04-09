#!/bin/bash
#SBATCH --job-name=mpnn_scaffold
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00

# P0-T05: MPNN Scaffold Split Evaluation (Gate G1) -- gpu_devel queue
# Trains MPNN with scaffold split, then random split for comparison.
# Writes artifacts/evaluation/mpnn_scaffold_metrics.json with Gate G1 outcome.

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

# Verify CUDA torch
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

# ── Run evaluation ───────────────────────────────────────────────────────
echo "Running scaffold + random split evaluation..."
echo ""

python scripts/evaluate_mpnn_scaffold.py --config configs/mpnn.yaml

echo ""

# ── Verify outputs ───────────────────────────────────────────────────────
echo "========================================"
echo "Verifying outputs"
echo "========================================"

ARTIFACT="artifacts/evaluation/mpnn_scaffold_metrics.json"
if [ -f "$ARTIFACT" ]; then
    echo "Artifact: $ARTIFACT"
    python -c "
import json
with open('$ARTIFACT') as f:
    m = json.load(f)
print(f'  Scaffold R^2:  {m[\"metrics\"][\"test_r2\"]}')
print(f'  Random R^2:    {m[\"comparison\"][\"random_split_r2\"]}')
print(f'  Degradation:   {m[\"comparison\"][\"degradation\"]}')
print(f'  Gate G1:       {m[\"gate_g1\"][\"outcome\"]}')
print(f'  Notes:         {m[\"gate_g1\"][\"notes\"]}')
"
else
    echo "ERROR: Artifact not found: $ARTIFACT"
    exit 1
fi

echo ""
echo "========================================"
echo "P0-T05 COMPLETE"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"
