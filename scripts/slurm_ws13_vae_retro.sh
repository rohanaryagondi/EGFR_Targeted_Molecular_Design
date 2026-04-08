#!/bin/bash
#SBATCH --job-name=ws13_vae_retro
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 02:00:00
#SBATCH --requeue

# WS13: VAE retraining on pre-cutoff data (SELFIES mode) + full retrospective
# re-run with retrained MPNN + retrained VAE candidates.
#
# Steps:
#   1. Build pre-cutoff VAE training data
#   2. Train VAE on pre-2010 data (SELFIES)
#   3. Train VAE on pre-2015 data (SELFIES)
#   4. Generate VAE candidates from each pre-cutoff VAE
#   5. Run retrospective validation with retrained MPNN + VAE candidates

set -euo pipefail

REPO="$HOME/projects/statebind/repo/.claude/worktrees/ws13-retro"
cd "$REPO"
mkdir -p logs

# ── Environment setup ────────────────────────────────────────────────────
module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================"
echo "WS13: VAE Retraining (SELFIES) + Full Retrospective"
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
    print(f'Memory:   {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
echo ""

# ── Step 1: Build pre-cutoff VAE training data ──────────────────────────
echo "========================================"
echo "Step 1: Building VAE time-split data"
echo "========================================"

python scripts/build_timesplit_vae_data.py
echo ""

# ── Step 2: Train VAE on pre-2010 data (SELFIES) ────────────────────────
echo "========================================"
echo "Step 2: Training VAE on pre-2010 data (SELFIES)"
echo "========================================"
echo "Config: configs/vae_pre2010.yaml --selfies"
echo "Start:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_vae.py --config configs/vae_pre2010.yaml --selfies
echo ""
echo "Pre-2010 VAE training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Step 3: Train VAE on pre-2015 data (SELFIES) ────────────────────────
echo "========================================"
echo "Step 3: Training VAE on pre-2015 data (SELFIES)"
echo "========================================"
echo "Config: configs/vae_pre2015.yaml --selfies"
echo "Start:  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/train_vae.py --config configs/vae_pre2015.yaml --selfies
echo ""
echo "Pre-2015 VAE training complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Step 4: Generate VAE candidates from pre-cutoff models ──────────────
echo "========================================"
echo "Step 4: Generating VAE candidates"
echo "========================================"

for cutoff in 2010 2015; do
    ckpt="artifacts/models/vae_pre${cutoff}/best_model.pt"
    config_file="artifacts/models/vae_pre${cutoff}/config.yaml"
    vocab="artifacts/models/vae_pre${cutoff}/vocabulary.json"
    output="artifacts/generation/vae_candidates_pre${cutoff}.json"

    if [ -f "$ckpt" ] && [ -f "$vocab" ]; then
        echo ""
        echo "Generating from pre-${cutoff} VAE (SELFIES)..."
        python scripts/generate_vae_candidates.py \
            --checkpoint "$ckpt" \
            --config "$config_file" \
            --vocab "$vocab" \
            --n-per-state 250 \
            --temperature 0.8 \
            --output "$output"
    else
        echo "WARNING: Pre-${cutoff} VAE checkpoint or vocab not found, skipping generation"
    fi
done
echo ""

# ── Step 5: Run retrospective validation (retrained MPNN + VAE) ─────────
echo "========================================"
echo "Step 5: Retrospective validation (retrained MPNN + VAE)"
echo "========================================"

# Copy original MPNN from main repo if it doesn't exist in worktree
MAIN_REPO="$HOME/projects/statebind/repo"
if [ ! -f artifacts/models/mpnn/best_model.pt ] && [ -f "$MAIN_REPO/artifacts/models/mpnn/best_model.pt" ]; then
    echo "Copying MPNN checkpoint from main repo..."
    mkdir -p artifacts/models/mpnn
    cp "$MAIN_REPO/artifacts/models/mpnn/best_model.pt" artifacts/models/mpnn/best_model.pt
fi

echo ""
echo "Running with --use-retrained-mpnn --use-retrained-vae..."
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

python scripts/run_retrospective_validation.py \
    --config configs/retrospective.yaml \
    --use-retrained-mpnn \
    --use-retrained-vae \
    --output-dir artifacts/evaluation/retrained/

echo ""
echo "Retrospective validation complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Verify outputs ───────────────────────────────────────────────────────
echo "========================================"
echo "Verifying all outputs"
echo "========================================"

echo ""
echo "--- VAE Models ---"
for cutoff in 2010 2015; do
    ckpt="artifacts/models/vae_pre${cutoff}/best_model.pt"
    if [ -f "$ckpt" ]; then
        echo "  vae_pre${cutoff}: $(du -h "$ckpt" | cut -f1)"
    else
        echo "  ERROR: vae_pre${cutoff} not found"
    fi
done

echo ""
echo "--- VAE Candidates ---"
for cutoff in 2010 2015; do
    cands="artifacts/generation/vae_candidates_pre${cutoff}.json"
    if [ -f "$cands" ]; then
        python -c "
import json
with open('$cands') as f:
    d = json.load(f)
print(f'  pre${cutoff}: {d[\"total_valid\"]} valid / {d[\"total_candidates\"]} total ({d[\"total_valid\"]/max(d[\"total_candidates\"],1)*100:.1f}%)')
"
    else
        echo "  WARNING: pre${cutoff} candidates not found"
    fi
done

echo ""
echo "--- Retrospective Results (retrained MPNN + VAE) ---"
for cutoff in 2010 2015; do
    results="artifacts/evaluation/retrained/retrospective_${cutoff}_retrained.json"
    if [ -f "$results" ]; then
        python -c "
import json
with open('$results') as f:
    d = json.load(f)
print(f'  MPNN model: {d.get(\"mpnn_model\", \"unknown\")}')
print(f'  VAE candidates: {d.get(\"vae_candidates\", \"none\")}')
for r in d['results']:
    ef10 = r.get('enrichment_factors', {}).get('10', 0)
    ef50 = r.get('enrichment_factors', {}).get('50', 0)
    msim = r.get('max_similarity_to_future', 0)
    nov = r.get('novelty_vs_training', 0)
    ncand = r.get('n_candidates', 0)
    print(f'  {r[\"pipeline\"]} (pre-${cutoff}): EF@10={ef10:.2f}, EF@50={ef50:.2f}, max_sim={msim:.3f}, novelty={nov:.2f}, n_cands={ncand}')
"
    else
        echo "  WARNING: retrained results for ${cutoff} not found"
    fi
done

echo ""
echo "========================================"
echo "WS13 VAE (SELFIES) + FULL RETROSPECTIVE COMPLETE"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"
