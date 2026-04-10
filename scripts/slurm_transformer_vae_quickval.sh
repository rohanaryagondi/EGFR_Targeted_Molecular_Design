#!/bin/bash
#SBATCH --job-name=tfm_vae_qv
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 00:30:00

# Quick validation: Train Transformer VAE for 20 epochs on 500 molecules.
# Checks: (a) reconstruction Tanimoto > 0.1, (b) aromatic rings > 0 in generated.
#
# This script creates a small subset of training data, trains briefly,
# generates molecules, and reports validation metrics.

set -euo pipefail

cd "$HOME/projects/statebind/repo"
mkdir -p logs

module purge
module load Python/3.12.3
source "$HOME/projects/statebind/envs/statebind/bin/activate"

echo "========================================================"
echo "  Transformer VAE — Quick Validation (20 epochs)"
echo "========================================================"
echo "  Node:   $(hostname)"
echo "  Date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# ── Create small subset of training data ──────────────────────────
QUICKVAL_DIR="/tmp/transformer_vae_quickval_${SLURM_JOB_ID}"
mkdir -p "${QUICKVAL_DIR}"

python -c "
import json, yaml

# Take first 500 training and first 125 validation molecules
with open('data/processed/egfr_smiles_train.json') as f:
    train = json.load(f)[:500]
with open('data/processed/egfr_smiles_val.json') as f:
    val = json.load(f)[:125]

with open('${QUICKVAL_DIR}/train.json', 'w') as f:
    json.dump(train, f)
with open('${QUICKVAL_DIR}/val.json', 'w') as f:
    json.dump(val, f)

print(f'Quick-val data: {len(train)} train, {len(val)} val')

# Create a quick config: 20 epochs, small batch, no patience
with open('configs/transformer_vae.yaml') as f:
    cfg = yaml.safe_load(f)

cfg['training']['epochs'] = 20
cfg['training']['patience'] = 25  # Don't early-stop during quick val
cfg['training']['seed'] = 42
cfg['training']['batch_size'] = 64
cfg['training']['checkpoint_dir'] = '${QUICKVAL_DIR}/model/'
cfg['training']['log_dir'] = '${QUICKVAL_DIR}/logs/'
cfg['data']['train_path'] = '${QUICKVAL_DIR}/train.json'
cfg['data']['val_path'] = '${QUICKVAL_DIR}/val.json'
cfg['kl_annealing']['warmup_epochs'] = 5  # Fast warmup for quick test

with open('${QUICKVAL_DIR}/config.yaml', 'w') as f:
    yaml.safe_dump(cfg, f, default_flow_style=False)

print('Quick-val config written.')
"

# ── Train for 20 epochs ────────────────────────────────────────────
echo ""
echo "Training for 20 epochs on 500 molecules..."
python scripts/train_transformer_vae.py --config "${QUICKVAL_DIR}/config.yaml"

# ── Generate 100 molecules (for checking aromatic rings) ────────────
echo ""
echo "Generating 100 molecules per state..."
python scripts/generate_transformer_vae.py \
    --checkpoint "${QUICKVAL_DIR}/model/best_model.pt" \
    --vocab "${QUICKVAL_DIR}/model/vocabulary.json" \
    --config "${QUICKVAL_DIR}/model/config.yaml" \
    --n-per-state 100 \
    --temperature 0.8 \
    --states "DFGin_aCin,DFGin_aCout,DFGout_aCin" \
    --output "${QUICKVAL_DIR}/candidates.json"

# ── Validation checks ──────────────────────────────────────────────
echo ""
echo "Running validation checks..."
python -c "
import json
import sys

# Check 1: Generation stats
with open('${QUICKVAL_DIR}/candidates.json') as f:
    artifact = json.load(f)

total = artifact['total_candidates']
valid = artifact['total_valid']
validity_rate = valid / max(total, 1) * 100
print(f'  Validity:      {valid}/{total} ({validity_rate:.1f}%)')

# Check 2: Aromatic rings (requires RDKit)
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    ring_counts = []
    for c in artifact['candidates']:
        if c['is_valid']:
            mol = Chem.MolFromSmiles(c['smiles'])
            if mol:
                ring_counts.append(Descriptors.NumAromaticRings(mol))
    if ring_counts:
        mean_rings = sum(ring_counts) / len(ring_counts)
        has_rings = sum(1 for r in ring_counts if r > 0)
        print(f'  Aromatic rings: mean={mean_rings:.2f}, {has_rings}/{len(ring_counts)} have rings')
        print(f'  CHECK (b): mean_aromatic_rings > 0 : {\"PASS\" if mean_rings > 0 else \"FAIL\"}')
    else:
        print('  No valid molecules to check rings')
except ImportError:
    print('  RDKit not available, skipping ring check')

# Check 3: Reconstruction (encode training mols, decode, compare)
try:
    import torch
    from statebind.ml.transformer_vae import ConditionalTransformerVAE, TransformerVAEConfig
    from statebind.ml.vocabulary import Vocabulary
    from statebind.ml.tokenizer import SMILESTokenizer
    from statebind.ml.utils import get_device
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit import DataStructs

    device = get_device('auto')
    ckpt = torch.load('${QUICKVAL_DIR}/model/best_model.pt', map_location=device, weights_only=False)
    cfg = TransformerVAEConfig(**ckpt['transformer_vae_config'])
    model = ConditionalTransformerVAE(cfg)
    model.load_state_dict(ckpt['model_state_dict'])
    model.to(device)
    model.eval()

    with open('${QUICKVAL_DIR}/model/vocabulary.json') as f:
        vocab = Vocabulary.from_json(f.read())

    tokenizer = SMILESTokenizer()

    # Encode first 50 training molecules, decode, compute Tanimoto
    with open('${QUICKVAL_DIR}/train.json') as f:
        train_data = json.load(f)[:50]

    tanimotos = []
    for rec in train_data:
        smi = rec['smiles']
        state = rec['state']

        tokens = tokenizer.tokenize(smi)
        indices = vocab.encode(tokens)
        x = torch.tensor([indices], dtype=torch.long, device=device)
        lengths = torch.tensor([len(indices)], dtype=torch.long, device=device)

        state_map = {'DFGin_aCin': 0, 'DFGin_aCout': 1, 'DFGout_aCin': 2}
        state_idx = state_map.get(state, 0)
        state_oh = torch.zeros(1, cfg.n_states, device=device)
        state_oh[0, state_idx] = 1.0

        mu, logvar = model.encode(x, lengths, state_oh)
        z = mu  # deterministic

        seqs = model.generate(z, state_oh, max_len=128, temperature=0, vocab=vocab)
        if seqs and seqs[0]:
            decoded_tokens = vocab.decode(seqs[0], strip_special=True)
            decoded_smi = ''.join(decoded_tokens)
            mol_orig = Chem.MolFromSmiles(smi)
            mol_dec = Chem.MolFromSmiles(decoded_smi)
            if mol_orig and mol_dec:
                fp1 = AllChem.GetMorganFingerprintAsBitVect(mol_orig, 2, nBits=2048)
                fp2 = AllChem.GetMorganFingerprintAsBitVect(mol_dec, 2, nBits=2048)
                tan = DataStructs.TanimotoSimilarity(fp1, fp2)
                tanimotos.append(tan)

    if tanimotos:
        mean_tan = sum(tanimotos) / len(tanimotos)
        max_tan = max(tanimotos)
        print(f'  Reconstruction: mean_tanimoto={mean_tan:.3f}, max={max_tan:.3f} (n={len(tanimotos)})')
        print(f'  CHECK (a): mean_recon_tanimoto > 0.1 : {\"PASS\" if mean_tan > 0.1 else \"FAIL\"}')
    else:
        print('  No reconstruction comparisons possible')
except Exception as e:
    print(f'  Reconstruction check error: {e}')

print()
print('Quick validation complete.')
"

echo ""
echo "========================================================"
echo "  Quick Validation DONE"
echo "  Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================================"

# Cleanup
rm -rf "${QUICKVAL_DIR}"
