---
type: context-document
created: 2026-04-10T06:00:00Z
purpose: Full context for the generation module replacement task
---

# Generation Module Fix — Context

## What Failed and Why

The SELFIES VAE (the `ConditionalSMILESVAE` class in `src/statebind/ml/vae.py`) is a
non-functional molecular autoencoder. 15 diagnostic tests confirmed the root cause.

### Diagnosis: Total Autoencoder Failure

| Finding | Test | Key Number |
|---------|------|------------|
| 0% reconstruction accuracy | G1 | mean Tanimoto to input = 0.031 |
| Default molecule is 127-carbon aliphatic chain | G3 | identical for all 3 states |
| Near-zero aromatic rings in output | C3 | generated=0.03 vs training=3.56 |
| Zero scaffold overlap gen-vs-training | C2 | 0 of 170 generated scaffolds in training |
| Zero active latent dimensions | G7 | 0 dims with KL>0.01 (of 64) |
| States not separated in latent space | G7 | centroid distances 0.06-0.09 |
| Encoding real drugs, decode = garbage | G4 | max sim to input drug ~0.11 |
| No temperature helps | G2 | 0 molecules >0.3 sim at any T |
| Training data IS drug-relevant | C1 | max sim=1.0 to afatinib, random subset EF@10=1.32 |
| SELFIES representation is lossless | C4 | all 7 drugs roundtrip at Tanimoto=1.0 |

**Full results**: `artifacts/evaluation/vae_diagnostics/synthesis.json`

### Two Interacting Causes

1. **Decoder incapacity (primary).** The GRU decoder cannot produce aromatic ring
   systems in SELFIES notation. Ring closure requires `[Ring1]`/`[Ring2]` tokens that
   reference earlier positions — a long-range dependency the GRU fails at during
   autoregressive inference. Teacher forcing masks this during training because the
   model sees correct context at each step, but at inference it generates aliphatic
   chains and never reaches a state where ring-closure tokens are predicted.

2. **Posterior collapse (compounding).** Zero of 64 latent dimensions carry information
   (per-dim KL < 0.0013 for all). The aggregate KL of ~0.68 appeared healthy in training
   logs but is just 64 dims * ~0.01 each — noise. The encoder-decoder channel is dead.
   The decoder ignores z entirely and generates from its (broken) prior mode.

### What IS NOT broken

- **Training data**: Contains EGFR drugs at Tanimoto=1.0 (afatinib). 380/2000 above 0.4.
  Random training subsets achieve EF@10=1.32.
- **SELFIES representation itself**: All 7 EGFR drugs survive SMILES-SELFIES roundtrip
  perfectly (Tanimoto=1.0).
- **Scoring pipeline**: `ranking/scoring.py` works correctly. The analogue-based generation
  achieves EF@10 = 4.95 (static) / 7.72 (state-aware).
- **Evaluation framework**: `evaluation/retrospective.py`, bootstrap CIs, BEDROC all work.

## Current Architecture

### VAE Module: `src/statebind/ml/vae.py`

```
Encoder: Bidirectional GRU(embed_dim + n_states, hidden_dim=512, n_layers=2)
         -> concat final hidden states -> Linear -> mu, logvar (latent_dim=64)

Decoder: z_proj = Linear(latent_dim + n_states, hidden_dim * n_layers)
         -> GRU(embed_dim=128, hidden_dim=512, n_layers=2, teacher_forcing)
         -> Linear(hidden_dim, vocab_size) per step

Loss: CrossEntropy(recon) + 0.01 * KL(q(z|x) || N(0,I))
```

Config: `configs/vae.yaml` — hidden_dim=512, latent_dim=64, n_states=3, kl_weight=0.01
Training: 300 epochs, batch_size=128, cosine LR schedule, KL annealing over 50 epochs,
teacher forcing decay from 1.0 to 0.0 over 30 epochs.

### Key Classes and Their Public APIs

```python
# src/statebind/ml/vae.py
class VAEConfig(BaseModel):         # Hyperparameters (no torch dep)
class SMILESEncoder(nn.Module):     # encode(x, lengths, state_onehot) -> (mu, logvar)
class SMILESDecoder(nn.Module):     # forward(z, state_onehot, target, tf_ratio) -> logits
class ConditionalSMILESVAE(nn.Module):
    encode(x, lengths, state_onehot) -> (mu, logvar)
    sample(mu, logvar) -> z
    generate(z, state_onehot, max_len, temperature, vocab) -> list[list[int]]
    forward(x, lengths, state_onehot, tf_ratio) -> (recon_logits, mu, logvar)

def vae_loss(recon_logits, target, mu, logvar, kl_weight, pad_idx) -> (total, recon, kl)
```

### Integration Points

The VAE connects to the rest of StateBind through these touchpoints:

1. **Training script**: `scripts/train_vae.py` — reads config, builds model, trains, saves checkpoint
2. **Generation script**: `scripts/generate_vae_candidates.py` — loads checkpoint, calls `model.generate()`,
   writes JSON artifact to `artifacts/generation/vae_candidates.json`
3. **Pipeline integration**: `src/statebind/generation/vae_integration.py` — reads the JSON artifact
   (not the model itself), converts to `StateConditionedCandidate` objects for the scoring pipeline
4. **Ablation C scripts**: `scripts/run_ablation_c_analysis_v2.py`, `scripts/prepare_ablation_c_data.py`
5. **Tokenizer**: `src/statebind/ml/tokenizer.py` — `SELFIESTokenizer` and `SMILESTokenizer`
6. **Vocabulary**: `src/statebind/ml/vocabulary.py` — `Vocabulary` class with encode/decode
7. **Dataset**: `src/statebind/ml/vae_dataset.py` — `SMILESDataset`, `collate_smiles`, `load_smiles_dataset`
8. **Trainer**: `src/statebind/ml/trainer.py` — generic training loop

### What the Pipeline Expects from the Generator

The downstream pipeline does NOT depend on the VAE's internal architecture. It consumes a
JSON artifact with this schema:

```json
{
  "model_config": { ... },
  "temperature": 0.8,
  "n_per_state": 100,
  "candidates": [
    {"smiles": "CCO...", "state": "DFGin_aCin", "is_valid": true, "source": "vae_generated"},
    ...
  ]
}
```

`vae_integration.py` wraps each candidate as a `StateConditionedCandidate` with
`source=CandidateSource.ML_GENERATED` and `strategy=GenerationStrategy.VAE_GENERATED`.
The scoring pipeline then scores them identically to template-generated candidates.

**Key insight**: Any generative model that produces `{smiles, state}` pairs and writes
this JSON format can slot in with zero changes to the scoring/evaluation pipeline.

## Training Data

- **Source**: ChEMBL EGFR bioactivity (IC50 < 10uM) + known binders
- **Size**: 5995 training, 1542 validation (3-state filtered, DFGout_aCout removed)
- **States**: DFGin_aCin, DFGin_aCout, DFGout_aCin
- **Format**: JSON with `{"smiles": "...", "state": "..."}` per molecule
- **Paths**:
  - `data/processed/egfr_smiles_train.json` (conditioned, 3-state)
  - `data/processed/egfr_smiles_val.json` (conditioned, 3-state)
  - `data/processed/egfr_smiles_unconditioned_train.json` (ablation, 1-state)
  - `data/processed/egfr_smiles_unconditioned_val.json` (ablation, 1-state)

## EGFR Reference Drugs (Evaluation Targets)

| Drug | Year | State | In Training? |
|------|------|-------|-------------|
| erlotinib | 2004 | DFGin_aCin | Yes (reference) |
| gefitinib | 2003 | DFGin_aCin | Yes (reference) |
| afatinib | 2013 | DFGin_aCin | No (future, Tanimoto=1.0 to training) |
| osimertinib | 2015 | DFGin_aCin | No (future, Tanimoto=0.87 to training) |
| dacomitinib | 2018 | DFGin_aCin | No (future, Tanimoto=0.83 to training) |
| lazertinib | 2021 | DFGin_aCin | No (future, Tanimoto=0.66 to training) |
| mobocertinib | 2021 | DFGin_aCin | No (future, Tanimoto=0.59 to training) |

Enrichment is measured using the 2010 cutoff: compounds approved after 2010 are "future drugs."
EF@10 = (fraction of future drugs in top 10%) / (fraction of future drugs overall).

## HPC Environment

- **Cluster**: Yale Bouchet
- **Account**: `pi_mg269` (SLURM `-A pi_mg269`)
- **GPU partitions**: gpu_devel (H200+RTX5000), gpu (RTX5000), gpu_h200 (H200), scavenge_gpu (preemptable)
- **Python env**: `source ~/projects/statebind/envs/statebind/bin/activate` after `module load Python/3.12.3`
- **Conda env**: alternative via `module load miniconda && conda activate statebind_ml`
- **Key constraint**: Max 3 parallel SLURM agents (user preference)
