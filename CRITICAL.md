# Critical Information -- Project-Wide

Non-obvious facts that an AI agent MUST know to avoid breaking things in the StateBind codebase.

## Scoring System

- Unified scoring weights must sum to 1.0 -- enforced by `_validate_weights()` at `ranking/scoring.py:89-97`. Violating this raises `ValueError`.
- The 4 required weight keys are: `reference_similarity`, `druglikeness`, `docking_proxy`, `state_specificity` -- validated at `ranking/scoring.py:91`.
- Docking stub returns constant 0.5 for ALL candidates -- `baselines/scoring.py:135-149` -- wastes 20% of unified score weight.
- Baseline scoring uses DIFFERENT weights (0.4/0.3/0.3) than unified scoring (0.35/0.30/0.20/0.15) -- `baselines/scoring.py:176-180` vs `ranking/scoring.py:40-45`.
- `state_specificity` gives state-aware pipeline a structural 0.15 weight advantage over static baseline -- this is by design (`ranking/scoring.py:55-86`).
- `_tanimoto_ngram` uses SMILES character 3-grams, NOT Morgan/ECFP4 fingerprints -- `baselines/scoring.py:31-54`. This is a crude proxy.
- Reference binders (erlotinib, gefitinib, osimertinib) are defined as SMILES literals at `baselines/scoring.py:59-66`.

## Workstream Conflicts

- WS02 (scoring integration), WS04 (docking proxy), and WS08 (MPNN affinity) ALL modify `ranking/scoring.py` -- they must execute sequentially, not in parallel.
- Cascading docking fallback chain: MPNN (WS08) -> DockingProxy MLP (WS04) -> stub returning 0.5 (current).
- Do NOT change `DEFAULT_WEIGHTS` at `ranking/scoring.py:40-45` without also updating the `SCORING_METHOD` string at `ranking/scoring.py:47-52`.

## Data and Context

- All curated data (mutations, structures, ligands) is embedded as Python literals in source code, NOT loaded from external files -- see `processing/context.py:24-37`, `structure/features.py:28-39`.
- All 17 resistance mutations map to `DFGin_aCin` (single-class) -- context model evaluation is uninformative (100% accuracy is trivial).
- `ConformationalState` enum at `processing/models.py:52-57` is the canonical state definition used across the entire codebase. 5 values: DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout, unclassified.

## ML Infrastructure

- ML models (VAE, MPNN, ADMET) are code-complete but UNTRAINED -- no training data prep scripts exist yet.
- Optional dependency pattern used everywhere: `try: import torch; HAS_TORCH = True except ImportError: HAS_TORCH = False` -- see `ml/__init__.py:25-30`.
- Pydantic configs (`VAEConfig`, `MPNNConfig`, `ADMETConfig`) are ALWAYS importable without torch -- by design for config validation without ML deps.
- `ATOM_FEATURE_DIM=35` and `BOND_FEATURE_DIM=11` are computed at `ml/graphs.py:98-101` -- MPNN and ADMET models must match these dimensions.
- Vocabulary special tokens occupy indices 0-3: `<pad>=0, <sos>=1, <eos>=2, <unk>=3` -- `ml/vocabulary.py:20-29`.
- Checkpoint convention: `artifacts/models/{vae,mpnn,admet}/best_model.pt`. Vocabulary saved as JSON alongside checkpoint.

## Module Dependencies

- Import flow is strictly downward: `processing -> structure -> generation -> ranking -> evaluation`. No cycles allowed.
- `data/` and `utils/` are leaf modules with zero statebind imports -- they can be imported by anything.
- `ranking/scoring.py` imports scoring functions FROM `baselines/scoring.py` (`_score_druglikeness`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram`) at lines 19-24.
- `generation/models.py` imports `CandidateSource` enum from `baselines/models.py:53-57` -- changing that enum breaks generation.

## Path Resolution

- `DataPaths` at `data/paths.py:18-21` walks up 4 parent directories from `paths.py` to find project root. This is fragile but has a `project_root` fallback parameter.
- All pipeline artifacts go to `artifacts/` as JSON -- modules communicate via disk, never via in-memory shared state.

## Testing

- 359 existing tests must continue to pass. Run: `pytest -v --tb=short`.
- Every new module/function needs tests in `tests/`.

## Model Types

- `ComparativeResult` in `evaluation/comparison.py:75-86` is a DATACLASS, not a Pydantic model. Do not call `.model_dump()` on it.
- `merge_rankings()` at `ranking/scoring.py:242-275` deduplicates by SMILES, keeping the HIGHER-scoring version.
- `rank_state_aware()` at `ranking/scoring.py:191-239` deduplicates across states, keeping the FIRST occurrence.

## Conventions

- All timestamps: `datetime.now(timezone.utc).isoformat()`.
- All floating-point scores: `round(value, 4)`.
- Private functions prefixed with `_` (e.g., `_score_docking_stub`, `_tanimoto_ngram`).
- `compute_properties()` in `baselines/filtering.py` returns heuristic SMILES-based estimates, NOT RDKit calculations.

---

> AI agents: when you discover new critical facts during your work, ADD them here with file:line references. Keep one fact per line. Be detailed yet concise.
