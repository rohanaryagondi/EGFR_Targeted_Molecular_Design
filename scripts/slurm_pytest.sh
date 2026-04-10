#!/bin/bash
#SBATCH --job-name=pytest_all
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p devel
#SBATCH -A pi_mg269
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH -t 00:30:00

# Run full test suite on SLURM (CPU partition).

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"
pip install -e ".[dev]" > /dev/null 2>&1

echo "Running pytest on $(hostname) at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Python: $(python --version)"
echo ""

pytest -x -q --tb=short 2>&1

echo ""
echo "Tests finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
