#!/bin/bash
#SBATCH --job-name=pmo_comparison
#SBATCH --output=logs/pmo_%j.out
#SBATCH --error=logs/pmo_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH -t 06:00:00

# ── PMO Compute-Matched Comparison (P1-T08) ──
# Runs GNINA docking for both static and state-aware pipelines
# under equal oracle budget of 500 calls each.
#
# GNINA docks ~106 molecules total (30 static + 76 state-aware),
# each taking ~30-60s with exhaustiveness=8.
# Estimated wall time: ~2 hours. 6h limit provides safety margin.

set -euo pipefail

# Load Python (matches the statebind install)
module load Python/3.10.8

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/evaluation

# Verify GNINA is accessible
if [ ! -x bin/gnina ]; then
    echo "ERROR: bin/gnina not found or not executable" >&2
    exit 1
fi

# Add project bin to PATH so docking wrapper finds gnina
export PATH="$HOME/projects/statebind/repo/bin:$PATH"

echo "=== PMO Comparison SLURM Job ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Run PMO comparison with budget=500 (real GNINA docking)
python scripts/run_pmo_comparison.py \
    --budget 500 \
    --output artifacts/evaluation/pmo_comparison.json \
    --sample-interval 5

echo ""
echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=== Done ==="
