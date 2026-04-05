#!/bin/bash
#SBATCH --job-name=train_vae
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 04:00:00

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"

# GPU diagnostics
echo "=== GPU Info ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo "================"

python scripts/train_vae.py --config configs/vae.yaml
