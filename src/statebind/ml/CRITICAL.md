# Critical Information -- ML

- All three models (VAE, MPNN, ADMET) are code-complete but UNTRAINED. Training data preparation scripts do not exist yet.
- Pydantic configs (`VAEConfig` in `vae.py`, `MPNNConfig` in `mpnn.py`, `ADMETConfig` in `admet.py`) are ALWAYS importable without torch -- by design.
- Optional dependency detection at `__init__.py:25-40`: `HAS_TORCH` and `HAS_TORCH_GEOMETRIC` flags. All neural network code is guarded behind these flags.
- Training scripts live in `scripts/` (`train_vae.py`, `train_mpnn.py`, `train_admet.py`), NOT inside the `ml/` package.
- Checkpoint convention: `artifacts/models/{vae,mpnn,admet}/best_model.pt`. Vocabulary saved as `vocab.json` alongside checkpoint.
- `ATOM_FEATURE_DIM=35` computed at `graphs.py:98`: 11 element + 7 degree + 5 charge + 5 hybridization + 1 aromatic + 1 ring + 5 num_Hs.
- `BOND_FEATURE_DIM=11` computed at `graphs.py:101`: 4 bond type + 1 conjugated + 1 ring + 5 stereo.
- MPNN at `mpnn.py:34` imports `ATOM_FEATURE_DIM` and `BOND_FEATURE_DIM` from `graphs.py`. If you change feature encoding, you MUST update both.
- Vocabulary special tokens occupy fixed indices 0-3: `<pad>=0, <sos>=1, <eos>=2, <unk>=3` -- `vocabulary.py:20-29`. Changing these breaks saved checkpoints.
- VAE architecture: GRU encoder (bidirectional) + GRU decoder with teacher forcing -- `vae.py:9-21`. State conditioning concatenated at every timestep.
- MPNN readout modes: `"mean_max"` (concat global_mean_pool + global_max_pool) or `"set2set"` -- `mpnn.py:16-18`. Both produce 2*hidden_dim output.
- ADMET model has 6 endpoints: caco2, herg, cyp3a4, clearance, lipophilicity, solubility -- `admet.py:9-14`. Mix of regression and classification tasks.
- `graphs.py` requires rdkit, torch, AND torch_geometric -- all three must be present for molecular graph construction.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
