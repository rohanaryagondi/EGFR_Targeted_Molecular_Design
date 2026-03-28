# Critical Information -- ML

- All three models (VAE, MPNN, ADMET) are code-complete but UNTRAINED. VAE training data prep script exists (`scripts/prepare_vae_data.py`); ADMET data prep script exists (`scripts/prepare_admet_data.py`); MPNN data prep script does not exist yet.
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

- `admet_predictor.py` is a singleton inference adapter. Module-level `_MODEL` and `_DEVICE` persist across calls. `_LOAD_ATTEMPTED` flag prevents repeated load failures. First `predict_admet()` call triggers lazy loading from `artifacts/models/admet/best_model.pt`.
- `predict_admet()` and `predict_admet_batch()` NEVER raise — return `{}` or `[{}]` on any failure (missing model, invalid SMILES, torch not installed).
- `check_admet_pass()` is pure Python (no torch) — safe to call unconditionally. Returns `(True, [])` when predictions dict is empty (permissive fallback).
- `DEFAULT_ADMET_THRESHOLDS` at `admet_predictor.py`: operators `">"` = "fail if exceeds", `"<"` = "fail if below". 6 tasks with safety-critical thresholds.
- `admet_predictor.py:_load_model()` reconstructs `ADMETConfig` from checkpoint's `config` key if present; falls back to default config. Architecture mismatch → load_model raises → caught → returns None.
- Batch prediction in `predict_admet_batch()` uses `Batch.from_data_list()` + `model.forward()` (not `model.predict()`) for efficiency. Post-processing (sigmoid for classification, rounding to 4 dp) replicates `MultiTaskADMET.predict()` at `admet.py:333-364`. Chunks at 256 to avoid OOM.
- `generation/admet_filter.py`: Pydantic models (`ADMETFilterResult`, `ADMETFilterSummary`) are always importable without torch. The `predict_admet_batch` import is inside `filter_candidates_admet()` body.
- `scripts/prepare_admet_data.py` uses 3-tier fallback: PyTDC API → cached JSON at `data/raw/admet_tdc_cache.json` → curated ~55 drug molecules. Curated fallback always works with zero external dependencies.
- ADMET combined data format: `[{"smiles": str, "caco2": float|null, ...}]` at `data/processed/admet_combined.json`. Null = JSON null. Duplicate SMILES resolved: median (regression), majority vote (classification).

- `affinity_predictor.py` is a singleton inference adapter (same pattern as `admet_predictor.py`). Module-level `_MODEL`, `_DEVICE`, `_LOAD_ATTEMPTED` persist across calls. First `predict_affinity()` call triggers lazy loading from `artifacts/models/mpnn/best_model.pt`.
- `predict_affinity()` and `predict_affinity_batch()` NEVER raise — return `0.5` (float) on any failure (missing model, invalid SMILES, torch not installed).
- `_model_loaded() -> bool` at `affinity_predictor.py` exposes singleton status. Used by `ranking/scoring.py:_score_docking()` to distinguish "MPNN predicted 0.5" (legitimate for pIC50=5) from "MPNN failed to load".
- `_normalize_pic50(pic50)` at `affinity_predictor.py`: sigmoid((pIC50 - 5) / 2). Centers at pIC50=5 (IC50=10µM → 0.5). pIC50=7 → 0.731, pIC50=9 → 0.881.
- `affinity_predictor.py:_load_model()` reconstructs `MPNNConfig` from checkpoint's `config` key if present; falls back to default config.
- Batch prediction in `predict_affinity_batch()` uses `Batch.from_data_list()` + `model.forward()` for efficiency. Chunks at 256 to avoid OOM.
- `scripts/prepare_mpnn_data.py` uses 3-tier fallback: local file → ChEMBL REST API (stdlib `urllib.request` only, target CHEMBL203, pchembl_value ≥ 3) → curated ~90 compounds. The curated fallback always works with zero external dependencies.
- MPNN training data format: `[{"smiles": str, "pIC50": float}, ...]` at `data/processed/egfr_affinity.json`. Single file (not split); `affinity_dataset.py:split_dataset` handles train/val/test splitting.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
