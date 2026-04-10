#!/bin/bash
#SBATCH --job-name=vae_diag_cpu
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p day
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00

# VAE Enrichment Failure CPU Diagnostics
# 7 tests using only RDKit/numpy (TEST-C1 through TEST-C7)
# See scripts/vae_diagnostic_cpu.py and docs/vae-diagnostic-investigation.md

set -euo pipefail

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"
mkdir -p logs artifacts/evaluation/vae_diagnostics

echo "========================================================"
echo "  VAE Enrichment Failure Diagnostics — CPU Tests"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  Python: $(python --version)"
echo "========================================================"
echo ""

python scripts/vae_diagnostic_cpu.py

echo ""
echo "Completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Results in: artifacts/evaluation/vae_diagnostics/"
