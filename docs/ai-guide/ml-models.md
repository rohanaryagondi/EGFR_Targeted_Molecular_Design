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
| VAE | **Trained** | 8,109 SMILES, early-stopped epoch 29 (best epoch 9), val loss 2.3246, 2,601,141 params. Checkpoint: `artifacts/models/vae/best_model.pt` (30MB) |
| MPNN | Submitted | SLURM job 7285710, gpu partition, 4h limit, 10,466 compounds |
| ADMET | Submitted | SLURM job 7285711, gpu partition, 6h limit, 32G mem, 27,698 molecules |

## Integration

- **VAE -> generation:** `generation/vae_integration.py` loads pre-generated VAE candidates
  via `load_vae_candidates(path)` and groups them by state via `build_vae_libraries(candidates)`.
  VAE generation script (`scripts/generate_vae_candidates.py`) does not exist yet — needs
  to be created to sample from the trained VAE on GPU and write candidates to JSON.
- **MPNN -> ranking:** `ml/affinity_predictor.py` provides `predict_affinity(smiles) -> float`
  in [0, 1]. Normalizes pIC50 via `sigmoid((pIC50 - 5) / 2)`. Falls back to 0.5 stub.
- **ADMET -> evaluation:** `ml/admet_predictor.py` provides `predict_admet(smiles) -> dict`
  and `check_admet_pass(predictions, thresholds) -> (bool, list[str])`.
