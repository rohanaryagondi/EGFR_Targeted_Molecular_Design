# Critical Information -- Project-Wide

Non-obvious facts that an AI agent MUST know to avoid breaking things in the StateBind codebase.

## Scoring System

- Unified scoring weights must sum to 1.0 -- enforced by `_validate_weights()` at `ranking/scoring.py:173-181`. Violating this raises `ValueError`.
- The 4 required weight keys are: `reference_similarity`, `druglikeness`, `docking_proxy`, `state_specificity` -- validated at `ranking/scoring.py:173`.
- Docking uses 3-tier cascade: MPNN -> DockingProxy MLP -> constant 0.5 stub -- `baselines/scoring.py:202-216` (`_score_docking_stub`). MPNN trained (RMSE=0.72, R²=0.69, Pearson=0.83; checkpoint `artifacts/models/mpnn/best_model.pt`). ADMET trained (hERG AUROC=0.77, CYP3A4=0.73; checkpoint `artifacts/models/admet/best_model.pt`). VAE retraining with improved config (TF annealing, larger hidden dim).
- Baseline scoring uses DIFFERENT weights (0.4/0.3/0.3) than unified scoring (0.35/0.30/0.20/0.15) -- `baselines/scoring.py:269-273` vs `ranking/scoring.py:86-91`.
- `state_specificity` gives state-aware pipeline a structural 0.15 weight advantage over static baseline -- this is by design (`ranking/scoring.py:139-170`).
- Similarity scoring uses Morgan/ECFP4 fingerprints (WS02) with fallback to SMILES 3-gram Tanimoto -- `baselines/scoring.py:78` (`_score_reference_similarity`).
- Reference binders (erlotinib, gefitinib, osimertinib) are defined as SMILES literals at `baselines/scoring.py:59-66`.

## Workstream Conflicts

- WS02 (scoring integration), WS04 (docking proxy), and WS08 (MPNN affinity) ALL modify `ranking/scoring.py` -- they must execute sequentially, not in parallel.
- Cascading docking fallback chain: MPNN (WS08) -> DockingProxy MLP (WS04) -> stub returning 0.5 (current).
- Do NOT change `DEFAULT_WEIGHTS` at `ranking/scoring.py:86-91` without also updating the `SCORING_METHOD` string at `ranking/scoring.py:93-97`.

## Data and Context

- All curated data (mutations, structures, ligands) is embedded as Python literals in source code, NOT loaded from external files -- see `processing/context.py:24-37`, `structure/features.py:28-39`.
- All 17 resistance mutations map to `DFGin_aCin` (single-class) -- context model evaluation is uninformative (100% accuracy is trivial).
- `ConformationalState` enum at `processing/models.py:52-57` is the canonical state definition used across the entire codebase. 5 values: DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout, unclassified.

## ML Infrastructure

- ML models: MPNN TRAINED (RMSE=0.72, R²=0.69, Pearson=0.83, 12.7M params, best epoch 83, checkpoint `artifacts/models/mpnn/best_model.pt`). ADMET TRAINED (hERG AUROC=0.77, CYP3A4 AUROC=0.73, 187K params, best epoch 40, checkpoint `artifacts/models/admet/best_model.pt`). VAE RETRAINED (9.5M params, best epoch 293, val_recon=1.92, checkpoint `artifacts/models/vae/best_model.pt` 114MB; original had 0% valid SMILES — fixed with TF annealing 1.0→0.0, early-stop on recon_loss, hidden_dim 512, KL warmup 50 epochs; **generation quality NOT YET TESTED**). ADMET hard filtering rejects ALL kinase inhibitors on hERG — use as informational, not as pre-ranking gate.
- Optional dependency pattern used everywhere: `try: import torch; HAS_TORCH = True except ImportError: HAS_TORCH = False` -- see `ml/__init__.py:25-30`.
- Pydantic configs (`VAEConfig`, `MPNNConfig`, `ADMETConfig`) are ALWAYS importable without torch -- by design for config validation without ML deps.
- `ATOM_FEATURE_DIM=35` and `BOND_FEATURE_DIM=11` are computed at `ml/graphs.py:98-101` -- MPNN and ADMET models must match these dimensions.
- Vocabulary special tokens occupy indices 0-3: `<pad>=0, <sos>=1, <eos>=2, <unk>=3` -- `ml/vocabulary.py:20-29`.
- Checkpoint convention: `artifacts/models/{vae,mpnn,admet}/best_model.pt`. Vocabulary saved as JSON alongside checkpoint.

## Module Dependencies

- Import flow is strictly downward: `processing -> structure -> generation -> ranking -> evaluation`. No cycles allowed.
- `data/` and `utils/` are leaf modules with zero statebind imports -- they can be imported by anything.
- `ranking/scoring.py` imports scoring functions FROM `baselines/scoring.py` (`_has_rdkit`, `_score_druglikeness`, `_score_druglikeness_enhanced`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram`) at lines 19-26.
- `generation/models.py` imports `CandidateSource` enum from `baselines/models.py:53-57` -- changing that enum breaks generation.

## Path Resolution

- `DataPaths` at `data/paths.py:18-21` walks up 4 parent directories from `paths.py` to find project root. This is fragile but has a `project_root` fallback parameter.
- All pipeline artifacts go to `artifacts/` as JSON -- modules communicate via disk, never via in-memory shared state.

## CI/CD

- `.github/workflows/ci.yml` has 3 jobs: `test` (matrix 3.10/3.11/3.12), `lint` (3.12 only), `test-with-chemistry` (3.12 + `[dev,science,chemistry]`). Triggers on push/PR to both `main` and `ML` branches.
- The `full` extras group in `pyproject.toml` bundles `[dev,science,structure,chemistry]` but excludes `ml` -- torch-geometric requires CUDA-matched installs incompatible with generic CI runners.
- CI badge URL: `https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design/actions/workflows/ci.yml/badge.svg`.
- **~40 pre-existing ruff violations exist in `src/`** -- the `test` and `lint` jobs will fail until they are fixed. Affected files: `baselines/candidates.py` (F401 `re`), `baselines/filtering.py` (F401, I001), `baselines/models.py` (F401 `Literal`, I001, N815 `volume_A3`), `baselines/pipeline.py` (F401 `datetime/timezone`, F541 f-string), `baselines/pocket.py` (I001), `baselines/scoring.py` (F401 `re`, I001), `cli.py` (E501 line 9), `generation/filtering.py` (F401 unused imports, I001), `generation/generator.py` (I001, E501 lines 84/131), `ml/graphs.py` (F401 `numpy`, F401 `rdchem`, E501 line 98), plus I001/F401 violations in `context/`, `dynamics/`, `processing/`, `ranking/`, `structure/`. Run `ruff check --fix src/` to auto-fix all fixable violations, then manually resolve any remaining.

## Testing

- 548 existing tests must continue to pass (was 359 pre-workstreams). Run: `pytest -v --tb=short`.
- Every new module/function needs tests in `tests/`.

## Model Types

- `ComparativeResult` in `evaluation/comparison.py:75-86` is a DATACLASS, not a Pydantic model. Do not call `.model_dump()` on it.
- `merge_rankings()` at `ranking/scoring.py:339-372` deduplicates by SMILES, keeping the HIGHER-scoring version.
- `rank_state_aware()` at `ranking/scoring.py:288-336` deduplicates across states, keeping the FIRST occurrence.

## Conventions

- All timestamps: `datetime.now(timezone.utc).isoformat()`.
- All floating-point scores: `round(value, 4)`.
- Private functions prefixed with `_` (e.g., `_score_docking_stub`, `_tanimoto_ngram`).
- `compute_properties()` in `baselines/filtering.py` returns heuristic SMILES-based estimates, NOT RDKit calculations.

## Operational Gotchas

### Worktree Naming
- Agents consistently use auto-generated worktree names (e.g., `claude/charming-liskov`) instead of the required `ws{NN}-{description}` convention from CLAUDE.md Section 11.
- The human operator must either rename worktrees after creation or explicitly instruct agents with the worktree name in the prompt: "Name your worktree `ws{NN}-{description}` on branch `ws{NN}/{description}`."
- Worktrees live under `.claude/worktrees/`. Use `git worktree list` to see all active worktrees.

### Editable Install Cross-Contamination
- Running `pip install -e .` in one git worktree makes ALL worktrees' imports resolve to that worktree's `src/` directory (pip overwrites the path entry globally in the virtualenv).
- **Solution:** Always run `pip install -e ".[dev]"` on the ML branch before running definitive tests.
- Never trust test results from a worktree if another worktree ran `pip install -e .` in the same virtualenv. Import errors in this situation are artifacts, not real failures.

### Shell CWD After Worktree Removal
- After `git worktree remove --force <path>`, if the shell's current working directory was inside the deleted path, ALL subsequent Bash commands fail with "No such file or directory."
- **Fix:** Run `mkdir -p <deleted-path>` to recreate the directory, then `git worktree prune` to clean stale references. Or `cd` to a valid path before removing.
- `.claude/worktrees/epic-clarke` exists as an empty stub directory specifically to prevent this problem for prior sessions. It can be safely removed once no shell session has it as CWD.

### Agents Don't Always Commit
- Modular agents sometimes complete their code work but do not `git commit` or `git push`.
- Head AI must always: (1) `cd` into the worktree, (2) check `git status` for uncommitted changes, (3) stage and commit if needed, (4) verify tests pass before merging.
- Never assume a worktree is ready to merge just because the agent reported "done."

### Scoring Chain Merge Order
- WS02 -> WS04 -> WS08 must merge to ML in strictly sequential order.
- All three modify `ranking/scoring.py`. Merging out of order creates conflicts because each workstream builds a fallback layer on top of the previous one.
- The cascading fallback chain after all three are merged: MPNN (WS08) -> DockingProxy MLP (WS04) -> constant 0.5 stub.

### ML Branch Is Default
- The default branch on GitHub was changed from `main` to `ML`. All work happens on `ML`.
- The Head AI always operates directly on `ML` -- no worktree.
- Push with `git push origin ML`.

### Test Count History
- Base: 359 tests (pre-workstream)
- After WS01/02/03/05/06/07/09: 498 tests
- After WS04: 518 tests
- After WS08: 548 tests (current)
- Target: 500+ (exceeded)

---

> AI agents: when you discover new critical facts during your work, ADD them here with file:line references. Keep one fact per line. Be detailed yet concise.
