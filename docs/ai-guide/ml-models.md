# ML Models Reference

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Summary Table

| Model | Config Class | Purpose | Input | Output | Config YAML | Checkpoint Path |
|-------|-------------|---------|-------|--------|-------------|-----------------|
| Conditional SMILES VAE | `VAEConfig` | State-conditioned molecular generation | Tokenized SMILES + state one-hot (4 states) | Novel SMILES per conformational state | `configs/vae.yaml` | `artifacts/models/vae/best_model.pt` |
| Affinity MPNN | `MPNNConfig` | Binding affinity prediction (replaces docking stub) | PyG molecular graph (atom_dim=35, bond_dim=11) | pIC50 (continuous, single float) | `configs/mpnn.yaml` | `artifacts/models/mpnn/best_model.pt` |
| Multi-task ADMET | `ADMETConfig` | Drug safety/PK endpoint prediction | PyG molecular graph (atom_dim=35, bond_dim=11) | 6 ADMET scores (regression + classification) | `configs/admet.yaml` | `artifacts/models/admet/best_model.pt` |

## Conditional SMILES VAE (`ml/vae.py`)

Architecture: GRU encoder (bidirectional) + GRU decoder with teacher forcing.
State conditioning is concatenated to encoder inputs at every timestep AND to the
latent code before decoder projection. This means the same latent space generates
different molecules depending on which conformational state is conditioned on.

- Encoder: `GRU(embed_dim + state_dim, hidden_dim, n_layers, bidirectional=True)`
- Latent: `mu = Linear(2*hidden_dim, latent_dim)`, `logvar = Linear(2*hidden_dim, latent_dim)`
- Reparameterization: `z = mu + eps * exp(0.5 * logvar)`
- Decoder: `z_proj = Linear(latent_dim + state_dim, hidden_dim * n_layers)` then
  `GRU(embed_dim, hidden_dim, n_layers)`
- Loss: reconstruction (cross-entropy) + KL divergence with annealing
- KL annealing: linear warmup over 20 epochs from 0 to `kl_weight` (0.01)
- Training: ~200 epochs, batch_size=128, cosine LR schedule, ~2-4 hours on single GPU
- Classes: `VAEConfig`, `SMILESEncoder`, `SMILESDecoder`, `ConditionalSMILESVAE`

## Affinity MPNN (`ml/mpnn.py`)

Architecture: NNConv message passing layers with residual connections + graph-level
readout (mean_max pooling or Set2Set) + MLP prediction head.

- Input projection: `Linear(atom_feature_dim, hidden_dim)` (atom_feature_dim=35)
- Message passing: N layers of `NNConv(hidden_dim, hidden_dim, edge_nn)` + `BatchNorm1d` + ReLU + residual
- Edge network: `Sequential(Linear(bond_feature_dim, hidden_dim), ReLU, Linear(hidden_dim, hidden_dim*hidden_dim))`
- Readout: `concat(global_mean_pool, global_max_pool)` -> 2*hidden_dim
- Prediction head: `Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout -> Linear(hidden_dim, 1)`
- Output: single pIC50 value (continuous)
- Training: ~150 epochs, batch_size=64, cosine LR, ~1-2 hours on single GPU
- Evaluation metrics: RMSE, MAE, R-squared, Pearson correlation

## Multi-task ADMET (`ml/admet.py`)

Architecture: Shared GIN (Graph Isomorphism Network) backbone with task-specific
MLP heads. The backbone learns a general molecular representation; each head
specializes for one ADMET endpoint.

- Backbone: N GIN layers (default 3): `GINConv(hidden_dim, hidden_dim)` + `BatchNorm1d` + ReLU + Dropout
- Readout: `concat(global_mean_pool, global_max_pool)` -> 2*hidden_dim
- Shared projection: `Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout`
- Per-task heads: `Linear(hidden_dim, hidden_dim//2) -> ReLU -> Dropout -> Linear(hidden_dim//2, 1)`
- 6 endpoints: caco2 (regression), hERG (classification, safety-critical, weight=1.5),
  CYP3A4 (classification), clearance (regression), lipophilicity (regression),
  solubility (regression)
- Loss: MSE for regression tasks, BCE for classification tasks, weighted sum
- Training: ~150 epochs, batch_size=64, ~2-3 hours on single GPU
- Data source: Therapeutics Data Commons (TDC) ADMET benchmarks

## Training Commands

```bash
# Requires: pip install -e ".[ml]"
python scripts/train_vae.py            # Conditional SMILES VAE
python scripts/train_mpnn.py           # Binding affinity MPNN
python scripts/train_admet.py          # Multi-task ADMET predictor
```

## Training Data (WS10 expanded, 2026-04-05)

| Model | Dataset | Records | Source |
|-------|---------|---------|--------|
| VAE | `data/processed/egfr_smiles_train.json` | 8,109 | ChEMBL EGFR (paginated, 40 pages) |
| VAE | `data/processed/egfr_smiles_val.json` | 2,027 | ChEMBL EGFR (paginated, 40 pages) |
| MPNN | `data/processed/egfr_affinity.json` | 10,466 | ChEMBL EGFR (paginated, 40 pages) |
| ADMET | `data/processed/admet_combined.json` | 27,698 | PyTDC (6 endpoints) |

## Training Status

| Model | Status | Details |
|-------|--------|---------|
| VAE | **Trained (v3 SELFIES)** | 9.5M params, 300 epochs on H200, val_recon=2.26, best epoch 297. SELFIES representation (100% validity by construction). Generation: 999/1000 valid (99.9%), 948 unique (94.8%). Checkpoint: `artifacts/models/vae/best_model.pt` |
| MPNN | **Trained** | RMSE=0.7182, R²=0.6863, Pearson=0.8323. 12.7M params, 10,466 compounds, best epoch 83/150. Trained 217s on H200. Checkpoint: `artifacts/models/mpnn/best_model.pt` (50MB). Active in scoring cascade |
| ADMET | **Trained** | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323. 187K params, 27,698 molecules (6 TDC endpoints), best epoch 40/150. Trained 197s on L40S. Checkpoint: `artifacts/models/admet/best_model.pt` (775KB). Informational only — hard filtering rejects ALL kinase inhibitors |

## Pre-Cutoff Models (WS13 Retrospective Validation)

Retrained MPNN and VAE models on time-restricted pre-cutoff data for retrospective validation.

### Pre-Cutoff MPNN

| Cutoff | N_train | Best Epoch | Test RMSE | Test R² | Test Pearson | Checkpoint |
|--------|---------|------------|-----------|---------|--------------|------------|
| 2010 | 2,379 | 79/150 | 0.701 | 0.717 | 0.854 | `artifacts/models/mpnn_pre2010/best_model.pt` |
| 2015 | 3,881 | 15/150 | 0.760 | 0.690 | 0.832 | `artifacts/models/mpnn_pre2015/best_model.pt` |

Same architecture as main MPNN (hidden_dim=128, 3 MP layers, mean_max readout). Configs: `configs/mpnn_pre2010.yaml`, `configs/mpnn_pre2015.yaml`.

### Pre-Cutoff VAE (SELFIES)

| Cutoff | N_train | Best Epoch | Unique Valid Candidates | Checkpoint |
|--------|---------|------------|------------------------|------------|
| 2010 | 2,379 | 298/300 | 987 (100% valid) | `artifacts/models/vae_pre2010/best_model.pt` |
| 2015 | 3,881 | 299/300 | 968 (100% valid) | `artifacts/models/vae_pre2015/best_model.pt` |

Same architecture as main VAE. SELFIES mode is essential for small training sets — SMILES mode produced 0-7.9% valid molecules. Configs: `configs/vae_pre2010.yaml`, `configs/vae_pre2015.yaml`.

Training commands:
```bash
python scripts/train_mpnn.py --config configs/mpnn_pre2010.yaml   # Pre-2010 MPNN
python scripts/train_mpnn.py --config configs/mpnn_pre2015.yaml   # Pre-2015 MPNN
python scripts/train_vae.py --config configs/vae_pre2010.yaml --selfies  # Pre-2010 VAE
python scripts/train_vae.py --config configs/vae_pre2015.yaml --selfies  # Pre-2015 VAE
```

## Integration

- **VAE -> generation:** `generation/vae_integration.py` loads pre-generated VAE candidates
  via `load_vae_candidates(path)` and groups them by state via `build_vae_libraries(candidates)`.
  VAE generation script: `scripts/generate_vae_candidates.py` generates candidates by sampling from the prior, auto-detects SELFIES mode from checkpoint config, and converts back to SMILES via `SELFIESTokenizer` in `ml/tokenizer.py`. Usage: `python scripts/generate_vae_candidates.py --n-per-state 250 --temperature 0.8`
- **MPNN -> ranking:** `ml/affinity_predictor.py` provides `predict_affinity(smiles) -> float`
  in [0, 1]. Normalizes pIC50 via `sigmoid((pIC50 - 5) / 2)`. Falls back to 0.5 stub.
- **ADMET -> evaluation:** `ml/admet_predictor.py` provides `predict_admet(smiles) -> dict`
  and `check_admet_pass(predictions, thresholds) -> (bool, list[str])`.
