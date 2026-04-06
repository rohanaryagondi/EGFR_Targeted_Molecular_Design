#!/bin/bash
#SBATCH --job-name=train_admet
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=l40s:1
#SBATCH --requeue
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 06:00:00

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"

# GPU diagnostics
echo "=== GPU Info ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo "================"

python scripts/train_admet.py --config configs/admet.yaml
