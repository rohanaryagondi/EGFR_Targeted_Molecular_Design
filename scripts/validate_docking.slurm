#!/bin/bash
#SBATCH --job-name=ws11_validate
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 01:00:00

module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0

cd "$HOME/projects/statebind/repo/.claude/worktrees/ws11-gnina"
mkdir -p logs

# Use worktree's installed packages
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export PATH="$PWD/bin:$PATH"

echo "=== Environment ==="
which python
python -c "from statebind.chemistry.docking import is_gnina_available; print('GNINA:', is_gnina_available())"

echo "=== Running validation (full exhaustiveness=8) ==="
python -u scripts/validate_docking.py 2>&1

echo "=== Running docking tests ==="
python -m pytest tests/test_docking.py -v --tb=short 2>&1

echo "=== Done ==="
