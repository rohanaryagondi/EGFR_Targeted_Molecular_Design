#!/bin/bash
#SBATCH --job-name=sb_all_tests
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p scavenge_gpu
#SBATCH -A pi_mg269
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --requeue

module purge
module load Python/3.12.3
module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0
source "$HOME/projects/statebind/envs/statebind/bin/activate"

cd "$HOME/projects/statebind/repo"
pip install -e ".[dev,science]" > /dev/null 2>&1

echo "=== GNINA ==="
bin/gnina --version 2>&1 | head -1
echo ""

echo "=== Environment ==="
python --version
python -c "import torch; print('torch', torch.__version__, 'CUDA:', torch.cuda.is_available())"
python -c "import torch_geometric; print('pyg', torch_geometric.__version__)"
python -c "import sklearn; print('sklearn', sklearn.__version__)"
python -c "import pymoo; print('pymoo', pymoo.__version__)"
python -c "from statebind.chemistry.docking import is_gnina_available; print('GNINA available:', is_gnina_available())"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU visible"
echo "==================="
echo ""

python -m pytest -v --tb=short 2>&1
