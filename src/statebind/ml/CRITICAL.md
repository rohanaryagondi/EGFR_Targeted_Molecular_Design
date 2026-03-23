# Critical Information -- ML

- All three models (VAE, MPNN, ADMET) are code-complete but UNTRAINED. VAE training data prep script exists (`scripts/prepare_vae_data.py`); MPNN and ADMET data prep scripts do not exist yet.
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

- `scripts/prepare_vae_data.py` uses 3-tier fallback: local ChEMBL file → ChEMBL REST API (stdlib `urllib.request` only) → curated ~55 EGFR inhibitors. The curated fallback always works with zero external dependencies.
- VAE training data format: `[{"smiles": str, "state": str}, ...]` at `data/processed/egfr_smiles_{train,val}.json`. State labels MUST match `DEFAULT_STATE_MAPPING` keys in `vae_dataset.py:41-46`.
- State assignment for curated compounds uses inhibitor-type heuristics (Type-I→DFGin_aCin, Type-I½→DFGin_aCout, Type-II→DFGout_aCin, allosteric→DFGout_aCout). Unknown types get seeded random assignment — this is a documented limitation.
- Reference binders from `baselines/scoring.py:59-66` are forced into the training split, never validation. See `_split_train_val()` in `scripts/prepare_vae_data.py`.
- Tests `test_generate_with_temperature_zero` and `test_generate_empty_latent` in `tests/test_vae_integration.py` are skipped when torch is not installed (`pytest.importorskip("torch")`). They test VAE `.generate()` determinism and zero-latent behavior respectively.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
