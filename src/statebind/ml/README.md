# statebind.ml

## Purpose

ML infrastructure for StateBind: provides three neural network architectures for molecular property prediction and generation, along with shared training utilities, SMILES tokenization, molecular graph construction, and Pydantic configuration models. All neural network code is gated behind optional dependencies (torch, torch_geometric, rdkit) so that the core pipeline can be imported and tested without any ML library installed. The package exposes framework-agnostic Pydantic configs (TrainerConfig, ModelCard, VAEConfig, MPNNConfig, ADMETConfig) that work unconditionally, and torch-dependent classes (Trainer, ConditionalSMILESVAE, AffinityMPNN, MultiTaskADMET) that are only defined when the relevant libraries are present.

## Internal Files

| File | Responsibility |
|------|---------------|
| `__init__.py` | Package docstring; dependency flags (`HAS_TORCH`, `HAS_TORCH_GEOMETRIC`); re-exports `TrainerConfig`, `TrainingMetrics`, `TrainingHistory`, `ModelCard`. |
| `models.py` | Pydantic v2 data models for training configuration (`TrainerConfig`), per-epoch metrics (`TrainingMetrics`), full training history (`TrainingHistory`), and model reproducibility metadata (`ModelCard`). No ML dependencies. |
| `trainer.py` | Generic PyTorch training loop (`Trainer` class) with gradient clipping, LR scheduling (cosine / plateau / none), early stopping, checkpoint save/load, CSV metric logging, mixed-precision support, and resume-from-checkpoint. |
| `utils.py` | Training utilities: `get_device()` (auto-detects CUDA/MPS/CPU), `set_seed()` (reproducibility across random/numpy/torch), `save_model()` / `load_model()` (checkpoint I/O with metadata), `count_parameters()`, `EarlyStopper` dataclass. |
| `tokenizer.py` | Regex-based SMILES tokenizer (`SMILESTokenizer`) that correctly splits multi-character atoms (Cl, Br, Si), bracketed atoms ([nH], [C@@H]), ring closures, bonds, and branches. No ML dependencies. |
| `vocabulary.py` | Token-to-index vocabulary (`Vocabulary`) with special tokens (pad/sos/eos/unk), encode/decode methods, JSON serialization, and `build_vocabulary()` factory. No ML dependencies. |
| `graphs.py` | Molecular graph construction from SMILES via RDKit. Produces PyTorch Geometric `Data` objects with atom features (~35-dim: element, degree, charge, hybridization, aromaticity, ring membership, H count) and bond features (~11-dim: bond type, conjugation, ring, stereo). Exports `ATOM_FEATURE_DIM` and `BOND_FEATURE_DIM` constants. |
| `vae.py` | Conditional SMILES VAE: `VAEConfig` (Pydantic), `SMILESEncoder` (bidirectional GRU with state conditioning), `SMILESDecoder` (GRU with teacher forcing), `ConditionalSMILESVAE` (full encode-sample-decode model with autoregressive `generate()` method), `vae_loss()` (reconstruction CE + weighted KL divergence). |
| `mpnn.py` | Message Passing Neural Network: `MPNNConfig` (Pydantic), `EdgeNetwork` (bond features to NNConv weight matrices), `MPNNLayer` (NNConv + BatchNorm + ReLU + residual), `AffinityMPNN` (full model with atom projection, N message-passing layers, mean_max or Set2Set readout, prediction MLP outputting pIC50). |
| `admet.py` | Multi-task ADMET predictor: `ADMETConfig` (Pydantic, 6 default endpoints), `TaskHead` (per-task MLP), `MultiTaskADMET` (shared GIN/GCN backbone + task-specific heads with `predict()` for single-molecule inference), `admet_loss()` (multi-task loss with NaN masking, BCE for classification, MSE for regression). |
| `vae_dataset.py` | VAE training data: `SMILESDatasetConfig` (Pydantic), `SMILESDataset` (tokenized SMILES + one-hot state labels), `collate_smiles()` (dynamic padding), `load_smiles_dataset()` (JSON/CSV loader). |
| `affinity_dataset.py` | MPNN training data: `AffinityDatasetConfig` (Pydantic, split ratios + validation), `AffinityDataset` (PyG Data with pIC50 labels), `load_affinity_dataset()` (JSON loader), `split_dataset()` (seeded train/val/test split). |
| `admet_dataset.py` | ADMET training data: `ADMETDatasetConfig` (Pydantic), `ADMETDataset` (PyG Data with multi-task NaN-masked labels + `task_mask`), `load_admet_dataset()` (JSON loader with min_tasks filtering), `split_admet_dataset()` (seeded split). |

## Model Architectures

### Conditional SMILES VAE (`vae.py`)

Generates novel SMILES conditioned on EGFR conformational states (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout). State conditioning is injected at two points: concatenated to encoder token embeddings at every timestep, and concatenated to the latent code before decoder hidden state projection.

- **Encoder:** Embedding(vocab_size, 128) -> Bidirectional GRU(128+4, 256, 2 layers) -> Linear(512, 64) for mu and logvar
- **Latent:** Reparameterization trick, z = mu + eps * exp(0.5 * logvar)
- **Decoder:** Linear(64+4, 256*2) -> GRU(128, 256, 2 layers) with teacher forcing -> Linear(256, vocab_size)
- **Loss:** Cross-entropy reconstruction (ignoring padding) + beta-weighted KL divergence
- **Generation:** Autoregressive decoding with temperature-scaled sampling or greedy argmax

### Affinity MPNN (`mpnn.py`)

Predicts pIC50 binding affinity from molecular graphs. Intended to replace the docking_proxy stub (constant 0.5) in the ranking pipeline's scoring function.

- **Input:** Atom features (35-dim) -> Linear -> hidden_dim
- **Message Passing:** N layers of NNConv (edge network maps bond features to weight matrices) + BatchNorm + ReLU + residual
- **Readout:** `mean_max` (global mean pool + global max pool concatenated) or `set2set` (Set2Set with configurable processing steps) -> 2*hidden_dim
- **Prediction:** Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout -> Linear(hidden_dim, 1) -> pIC50

### Multi-task ADMET (`admet.py`)

Predicts 6 drug-safety/pharmacokinetic endpoints simultaneously: Caco-2 permeability (regression), hERG inhibition (classification), CYP3A4 inhibition (classification), hepatic clearance (regression), lipophilicity (regression), aqueous solubility (regression).

- **Backbone:** Shared GIN or GCN network (configurable), N layers with BatchNorm + ReLU + Dropout + residual connections
- **Readout:** global_mean_pool + global_max_pool -> 2*hidden_dim
- **Shared projection:** Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout
- **Task heads:** One per endpoint: Linear(hidden_dim, hidden_dim//2) -> ReLU -> Dropout -> Linear(hidden_dim//2, 1)
- **Loss:** Per-task MSE (regression) or BCEWithLogits (classification) with NaN masking and configurable task weights

## Shared Infrastructure

- **Trainer** (`trainer.py`): Generic training loop accepting any `nn.Module`, `DataLoader`, and loss function. Handles AdamW optimizer, cosine/plateau LR scheduling, gradient clipping, early stopping, best-model checkpointing, CSV logging, mixed-precision (CUDA only), and resume from checkpoint. Returns a `TrainingHistory` Pydantic model.
- **Tokenizer** (`tokenizer.py`): Regex-based SMILES tokenizer. Handles multi-character atoms, bracketed atoms, ring closures, bonds, and branches. No ML dependencies.
- **Vocabulary** (`vocabulary.py`): Bidirectional token-to-index mapping with special tokens (pad=0, sos=1, eos=2, unk=3). Supports JSON serialization for checkpoint reproducibility. `build_vocabulary()` constructs from a SMILES corpus.
- **Graph conversion** (`graphs.py`): SMILES -> RDKit Mol -> PyG Data with atom/bond feature matrices. Computes 35-dim atom features (element one-hot, degree, charge, hybridization, aromaticity, ring, H count) and 11-dim bond features (type, conjugation, ring, stereo). Undirected edges (each bond stored in both directions).
- **Utilities** (`utils.py`): `get_device("auto")` resolves CUDA > MPS > CPU. `set_seed(42)` sets random/numpy/torch seeds. `save_model()` / `load_model()` store state_dict + config + metrics + timestamp.

## Optional Dependencies

All neural network code is gated behind try/except imports with boolean flags:

| Dependency | Flag | Required by |
|------------|------|-------------|
| `torch` | `HAS_TORCH` | `trainer.py`, `utils.py`, `vae.py`, `mpnn.py`, `admet.py`, `graphs.py`, all dataset modules |
| `torch_geometric` | `HAS_TORCH_GEOMETRIC` | `mpnn.py`, `admet.py`, `graphs.py`, `affinity_dataset.py`, `admet_dataset.py` |
| `rdkit` | `HAS_RDKIT` | `graphs.py` (atom/bond featurization) |

**Fallback behavior:** When dependencies are missing, Pydantic config models (`VAEConfig`, `MPNNConfig`, `ADMETConfig`, `TrainerConfig`, `ModelCard`) remain importable. Neural network classes raise `RuntimeError` with install instructions. `smiles_to_graph()` returns `None` and logs a warning.

Install ML dependencies with: `pip install -e ".[ml]"`

## Training Workflow

1. **Configure** via YAML files in `configs/`: `vae.yaml`, `mpnn.yaml`, `admet.yaml`
2. **Run training scripts:**
   ```bash
   python scripts/train_vae.py      # Conditional SMILES VAE
   python scripts/train_mpnn.py     # Binding affinity MPNN
   python scripts/train_admet.py    # Multi-task ADMET predictor
   ```
3. **Artifacts produced:**
   - Checkpoints: `artifacts/models/{vae,mpnn,admet}/best_model.pt`
   - Training logs: `artifacts/logs/{vae,mpnn,admet}/training_log.csv`
   - Evaluation metrics: `artifacts/evaluation/{mpnn,admet}_metrics.json`

## Key API

| Symbol | Module | Description |
|--------|--------|-------------|
| `TrainerConfig` | `models.py` | Hyperparameters: epochs, batch_size, lr, scheduler, patience, device, checkpoint/log dirs, seed, mixed_precision. |
| `TrainingMetrics` | `models.py` | Per-epoch snapshot: epoch, train_loss, val_loss, learning_rate, extra dict. |
| `TrainingHistory` | `models.py` | Full run record: config, metrics list, best_epoch, best_val_loss, total_time. |
| `ModelCard` | `models.py` | Reproducibility metadata: model_name, type, description, I/O formats, training data, n_parameters, performance, limitations. |
| `Trainer` | `trainer.py` | Generic training loop. `fit(model, train_loader, val_loader, loss_fn)` -> `TrainingHistory`. |
| `VAEConfig` | `vae.py` | VAE hyperparameters: vocab_size, embed/hidden/latent dims, n_layers, dropout, n_states, kl_weight, pad_idx. |
| `ConditionalSMILESVAE` | `vae.py` | Full VAE model. `forward(x, lengths, state_onehot)` -> (logits, mu, logvar). `generate(z, state, max_len, temperature)` -> token indices. |
| `vae_loss` | `vae.py` | Reconstruction CE + beta*KL. Returns (total, recon, kl) tensors. |
| `MPNNConfig` | `mpnn.py` | MPNN hyperparameters: atom/bond feature dims, hidden_dim, n_layers, dropout, readout, set2set_steps. |
| `AffinityMPNN` | `mpnn.py` | Binding affinity predictor. `forward(data)` -> pIC50 tensor of shape (batch, 1). |
| `ADMETConfig` | `admet.py` | ADMET hyperparameters: atom/bond dims, hidden_dim, n_gnn_layers, dropout, task_names, task_types, gnn_type. |
| `MultiTaskADMET` | `admet.py` | Multi-task predictor. `forward(data)` -> dict[task_name, tensor]. `predict(data)` -> dict[task_name, float]. |
| `admet_loss` | `admet.py` | Multi-task loss with NaN masking and per-task weighting. |
| `SMILESTokenizer` | `tokenizer.py` | `tokenize(smiles)` -> tokens, `detokenize(tokens)` -> smiles. |
| `Vocabulary` | `vocabulary.py` | `encode(tokens)` -> indices, `decode(indices)` -> tokens, `to_json()` / `from_json()`. |
| `build_vocabulary` | `vocabulary.py` | Build vocabulary from a list of SMILES strings. |
| `smiles_to_graph` | `graphs.py` | SMILES -> PyG Data (or None). |
| `smiles_to_graph_batch` | `graphs.py` | Batch conversion, skipping invalid SMILES. |
| `ATOM_FEATURE_DIM` | `graphs.py` | Constant: 35 (atom feature vector length). |
| `BOND_FEATURE_DIM` | `graphs.py` | Constant: 11 (bond feature vector length). |

## Dependencies

- **Imports from:**
  - `statebind.ml.tokenizer` (used by `vocabulary.py`, `vae_dataset.py`)
  - `statebind.ml.vocabulary` (used by `vae.py`, `vae_dataset.py`)
  - `statebind.ml.graphs` (used by `mpnn.py`, `affinity_dataset.py`, `admet_dataset.py`)
  - `statebind.ml.models` (used by `trainer.py`, `__init__.py`)
  - `statebind.ml.utils` (used by `trainer.py`)
- **Imported by:**
  - `statebind.ranking` — trained MPNN replaces docking_proxy stub in scoring
  - `statebind.generation` — trained VAE provides state-conditioned candidate generation
  - `statebind.evaluation` — ADMET predictions feed into candidate safety profiling

## Data Flow

**Reads:**
- SMILES + state label JSON for VAE training (from `data/processed/egfr_smiles_{train,val}.json`)
- SMILES + pIC50 JSON for MPNN training (from `data/processed/egfr_affinity.json`)
- SMILES + multi-task labels JSON for ADMET training (from `data/processed/admet_combined.json`)
- YAML configs from `configs/{vae,mpnn,admet}.yaml`

**Produces:**
- Model checkpoints: `artifacts/models/{vae,mpnn,admet}/best_model.pt`
- Training CSV logs: `artifacts/logs/{vae,mpnn,admet}/training_log.csv`
- Evaluation metrics: `artifacts/evaluation/{mpnn,admet}_metrics.json`
- Generated candidates (VAE): `artifacts/generation/vae_candidates.json`

## Integration Points

- **VAE -> generation/**: Trained VAE can generate novel state-conditioned SMILES to augment or replace the string-manipulation generation strategies in `generation/generator.py`.
- **MPNN -> ranking/scoring.py**: Trained MPNN replaces the `docking_proxy` stub (which returns constant 0.5) with learned pIC50 predictions, making the 20% docking weight in the scoring function functional.
- **ADMET -> evaluation/**: Multi-task ADMET predictions provide safety/PK profiling for candidate molecules, enabling filtering by drug-safety endpoints beyond the current heuristic property checks.

## Testing

- **Test files:** Tests for the ML package should be placed in `tests/test_ml.py` (or split per-model: `tests/test_ml_vae.py`, `tests/test_ml_mpnn.py`, etc.)
- **Run:** `pytest tests/test_ml*.py -v`
- **Note:** Tests should be structured to pass both with and without torch/torch_geometric installed, by using `pytest.importorskip("torch")` or `pytest.mark.skipif(not HAS_TORCH, ...)` guards.

## Known Limitations

- The MPNN and ADMET models depend on RDKit for SMILES-to-graph conversion; if RDKit is not installed, `smiles_to_graph()` returns `None` and those models cannot be used.
- Graph featurization uses a fixed vocabulary of 10 elements; less common atoms are mapped to "other".
- The VAE uses SMILES-level tokenization and GRU encoding, not graph-based — generated SMILES may not always be chemically valid.
- Teacher forcing ratio in the VAE decoder is a fixed hyperparameter (default 0.5), not annealed during training.
- The ADMET model's default endpoints are generic drug-safety properties, not EGFR-specific.
- No hyperparameter search infrastructure is provided; configs must be manually tuned.
- Training data files (`data/processed/*.json`) must be prepared by upstream pipeline scripts before ML training can run.

## Patterns to Follow

- All Pydantic config models (`VAEConfig`, `MPNNConfig`, `ADMETConfig`, `TrainerConfig`) are importable without any ML library.
- Neural network classes use `_require_torch()` or `_require_deps()` guards in `__init__` to give clear error messages.
- Conditional class definition (`if HAS_TORCH: class ...`) is used for torch.nn.Module subclasses so the module can be imported without torch.
- Feature dimension constants (`ATOM_FEATURE_DIM`, `BOND_FEATURE_DIM`) are precomputed and exported for config validation.
- Dataset classes handle both JSON and CSV input formats where applicable.
- All checkpoint files include `model_state_dict`, `config`, `metrics`, and `timestamp` for reproducibility.
