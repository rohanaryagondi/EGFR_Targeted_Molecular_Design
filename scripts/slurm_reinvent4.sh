#!/bin/bash
#SBATCH --job-name=reinvent4_egfr
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=rtx_5000_ada:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 06:00:00

# REINVENT 4 EGFR Baseline Run (Full Pipeline)
#
# Three-stage pipeline:
#   1. Create prior model from EGFR SMILES vocabulary (if not exists)
#   2. Transfer learning to train the model on EGFR chemical space
#   3. Reinforcement learning with GNINA docking as reward
#
# Prerequisites:
#   - reinvent4 conda env created (REINVENT 4 + RDKit + torch)
#   - GNINA binary at bin/gnina
#   - Prepared receptor at data/processed/docking/receptors/1m17.pdbqt
#   - SMILES file at data/processed/egfr_all_smiles.smi
#
# Submit with:
#   sbatch scripts/slurm_reinvent4.sh

set -euo pipefail

# ── Environment setup ──────────────────────────────────────────────────
module purge
module load miniconda
eval "$(conda shell.bash hook)"
conda activate reinvent4

# ── Working directory ──────────────────────────────────────────────────
cd "$HOME/projects/statebind/repo"
mkdir -p logs models artifacts/generation

# ── Job diagnostics ───────────────────────────────────────────────────
echo "=== Job Info ==="
echo "Job ID:    ${SLURM_JOB_ID}"
echo "Node:      $(hostname)"
echo "Date:      $(date -u --iso-8601=seconds)"
echo ""

echo "=== GPU Info ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""

# ── Verify prerequisites ─────────────────────────────────────────────
echo "=== Prerequisites ==="
echo -n "Python:    "; python --version
echo -n "REINVENT:  "; python -c "import reinvent; print(f'OK (v{reinvent.__version__})')" 2>/dev/null || echo "FAILED"
echo -n "RDKit:     "; python -c "from rdkit import Chem; print('OK')" 2>/dev/null || echo "FAILED"
echo -n "PyTorch:   "; python -c "import torch; print(f'OK (CUDA: {torch.cuda.is_available()})')" 2>/dev/null || echo "FAILED"
echo -n "GNINA:     "; [ -x bin/gnina ] && echo "OK (bin/gnina)" || echo "MISSING"
echo -n "Receptor:  "; [ -f data/processed/docking/receptors/1m17.pdbqt ] && echo "OK" || echo "MISSING"
echo -n "SMILES:    "; [ -f data/processed/egfr_all_smiles.smi ] && echo "OK ($(wc -l < data/processed/egfr_all_smiles.smi) lines)" || echo "MISSING"
echo ""

# ── Step 1: Create prior model (if needed) ────────────────────────────
if [ -f models/reinvent4_egfr_prior.model ]; then
    echo "=== Step 1: Prior model already exists, skipping ==="
else
    echo "=== Step 1: Creating prior model ==="
    echo "Start:  $(date -u --iso-8601=seconds)"
    python scripts/create_reinvent4_prior.py
    echo "Done:   $(date -u --iso-8601=seconds)"
fi
echo ""

# ── Step 2: Transfer learning ─────────────────────────────────────────
if [ -f models/reinvent4_egfr_agent.model ]; then
    echo "=== Step 2: Agent model already exists, skipping TL ==="
else
    echo "=== Step 2: Transfer Learning ==="
    echo "Config: configs/reinvent4_tl.toml"
    echo "Start:  $(date -u --iso-8601=seconds)"
    python -m reinvent -l logs/reinvent4_tl.log configs/reinvent4_tl.toml
    echo "Done:   $(date -u --iso-8601=seconds)"
fi
echo ""

# ── Step 3: Reinforcement Learning with GNINA ─────────────────────────
echo "=== Step 3: Reinforcement Learning ==="
echo "Config: configs/reinvent4_egfr.toml"
echo "Start:  $(date -u --iso-8601=seconds)"

# Run REINVENT 4 RL
python -m reinvent -l logs/reinvent4_rl.log configs/reinvent4_egfr.toml

echo "Done:   $(date -u --iso-8601=seconds)"
echo ""

# ── Step 4: Convert output to StateBind format ────────────────────────
echo "=== Step 4: Converting output ==="

python scripts/run_reinvent4_egfr.py \
    --convert-only artifacts/generation/reinvent4_egfr_summary.csv \
    --output artifacts/generation/reinvent4_egfr_candidates.json \
    2>&1 || {
    # Try finding the CSV with a different name pattern
    echo "Direct CSV not found, searching..."
    CSV=$(ls -t artifacts/generation/reinvent4_egfr_summary*.csv 2>/dev/null | head -1)
    if [ -n "$CSV" ]; then
        echo "Found: $CSV"
        python scripts/run_reinvent4_egfr.py \
            --convert-only "$CSV" \
            --output artifacts/generation/reinvent4_egfr_candidates.json
    else
        echo "WARNING: No REINVENT output CSV found"
    fi
}

echo ""

# ── Summary ───────────────────────────────────────────────────────────
echo "=== Summary ==="
if [ -f artifacts/generation/reinvent4_egfr_candidates.json ]; then
    echo "Output: artifacts/generation/reinvent4_egfr_candidates.json"
    python -c "
import json
with open('artifacts/generation/reinvent4_egfr_candidates.json') as f:
    data = json.load(f)
print(f\"Total candidates: {data.get('total_candidates', 'N/A')}\")
print(f\"Unique candidates: {data.get('total_unique', 'N/A')}\")
print(f\"Stats: {data.get('stats', {})}\")
"
else
    echo "WARNING: Output file not found"
fi
echo ""
echo "=== REINVENT 4 pipeline complete ==="
echo "End: $(date -u --iso-8601=seconds)"
