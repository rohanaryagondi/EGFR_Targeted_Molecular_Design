#!/bin/bash
# Helper to submit a single Transformer VAE sweep job.
# Usage: bash scripts/sweep_submit.sh <job_name> <partition> <gpu_type> <python_overrides>
#
# python_overrides is a Python snippet that modifies the cfg dict.

set -euo pipefail

JOB_NAME="$1"
PARTITION="$2"
GPU_TYPE="$3"
shift 3
OVERRIDES="$*"

cd "$HOME/projects/statebind/repo"
mkdir -p logs

sbatch --wrap="
set -euo pipefail
cd \"\$HOME/projects/statebind/repo\"
module purge
module load Python/3.12.3
source \"\$HOME/projects/statebind/envs/statebind/bin/activate\"

CKPT_DIR=\"/tmp/tvae_sweep_${JOB_NAME}_\$\$\"
mkdir -p \"\${CKPT_DIR}\"

python -c \"
import yaml
with open('configs/transformer_vae.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['training']['seed'] = 42
cfg['training']['epochs'] = 2000
cfg['training']['patience'] = 300
cfg['training']['checkpoint_dir'] = '\${CKPT_DIR}/'
cfg['training']['log_dir'] = '\${CKPT_DIR}/logs/'
${OVERRIDES}
with open('\${CKPT_DIR}/config.yaml', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)
for k in ['kl_weight','d_model','n_decoder_layers','latent_dim','word_dropout','dim_feedforward']:
    v = cfg['model'].get(k)
    if v is not None: print(f'  {k}={v}')
print(f'  warmup={cfg[\"kl_annealing\"][\"warmup_epochs\"]}')
\"

echo '=== ${JOB_NAME} TRAINING ==='
python scripts/train_transformer_vae.py --config \"\${CKPT_DIR}/config.yaml\"

echo ''
echo '=== GENERATION (temp=0.5) ==='
python scripts/generate_transformer_vae.py \\
    --checkpoint \"\${CKPT_DIR}/best_model.pt\" \\
    --vocab \"\${CKPT_DIR}/vocabulary.json\" \\
    --config \"\${CKPT_DIR}/config.yaml\" \\
    --n-per-state 200 --temperature 0.5 \\
    --states 'DFGin_aCin,DFGin_aCout,DFGout_aCin' \\
    --output \"\${CKPT_DIR}/candidates.json\"

echo ''
echo '=== GENERATION (temp=0.0, greedy) ==='
python scripts/generate_transformer_vae.py \\
    --checkpoint \"\${CKPT_DIR}/best_model.pt\" \\
    --vocab \"\${CKPT_DIR}/vocabulary.json\" \\
    --config \"\${CKPT_DIR}/config.yaml\" \\
    --n-per-state 200 --temperature 0.0 \\
    --states 'DFGin_aCin,DFGin_aCout,DFGout_aCin' \\
    --output \"\${CKPT_DIR}/candidates_greedy.json\"
" \
  -J "${JOB_NAME}" \
  -o "logs/${JOB_NAME}_%j.out" \
  -e "logs/${JOB_NAME}_%j.err" \
  -p "${PARTITION}" \
  -A pi_mg269 \
  --gpus="${GPU_TYPE}:1" \
  --requeue \
  --cpus-per-task=4 \
  --mem=32G \
  -t 04:00:00
