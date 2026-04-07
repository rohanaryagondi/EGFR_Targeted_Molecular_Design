# WS11: GNINA Physics-Informed Docking -- Progress Report

## Status

- **State:** Complete — implementation, validation, and tests all pass
- **Last updated:** 2026-04-07T12:00:00+00:00
- **Session count:** 2
- **Test count added:** 33
- **Files created:** 7
- **Files modified:** 5

## Objective

Integrate GNINA as the top tier of the docking fallback chain, providing physics-based
binding scores and 3D binding poses for all candidates docked into each conformational
state's pocket. This activates 20% of scoring weight with real protein-ligand structural
modeling. See `workstreams/11-gnina-docking.md` for the full brief.

---

## Progress Log

### Session 1 (2026-04-07)

**Files created:**
- `configs/docking.yaml` — GNINA config: binary path, exhaustiveness, box size, state reps
- `src/statebind/chemistry/docking.py` — Core GNINA wrapper with `DockingResult`, `dock_molecule`, `dock_batch`, `is_gnina_available`, `normalize_vina_score`, `get_receptor_for_state`
- `scripts/prepare_docking_receptors.py` — Download PDBs from RCSB, convert to PDBQT, define docking boxes for each state
- `src/statebind/evaluation/docking_analysis.py` — State-specific docking: `dock_candidate_all_states`, `run_docking_analysis`, `compute_score_heatmap`
- `tests/test_docking.py` — 26 tests across 11 categories

**Files modified:**
- `src/statebind/data/paths.py` — Added `docking_receptors_dir` and `docking_results_dir` properties
- `src/statebind/ranking/scoring.py` — GNINA as tier 0 in `_score_docking()` cascade + `_get_scoring_method()` updated
- `src/statebind/chemistry/__init__.py` — Exported new docking symbols
- `tests/test_imports.py` — Added `test_import_docking()`

---

## Current State

**What is done:**
- GNINA wrapper (`chemistry/docking.py`) with Contract 8 interface
- Docking config (`configs/docking.yaml`) with all parameters
- Receptor preparation script (downloads PDBs from RCSB, converts to PDBQT)
- GNINA integrated as tier 0 in scoring cascade with GPU guard and graceful fallback
- State-specific docking analysis module for candidate x state selectivity
- 33 tests across 11 categories — all pass (33/33 on GPU, 27 pass + 6 skip on CPU)
- Score normalization: `sigmoid(-vina_score / 3)` maps kcal/mol to [0, 1]
- `DataPaths` extended with docking paths
- GNINA v1.1 installed at `bin/gnina` (standalone binary, works with glibc 2.28)
- RDKit + OpenBabel installed via pip (rdkit-pypi + openbabel-wheel)
- Receptors prepared for all 4 states (1m17, 2gs7, 3w2r, 4zau PDBQT + box JSON)
- Full validation passed on GPU node (SLURM job 7561991, L40S GPU)
- Full test suite: 542 passed, 1 pre-existing failure (sklearn), 8 skipped

**GPU guard:** The scoring cascade only attempts GNINA when a GPU is detected
(`torch.cuda.is_available()` or `CUDA_VISIBLE_DEVICES` set). This prevents
CPU docking (too slow) from blocking the cascade during tests or on login nodes.

**Validation results (exhaustiveness=8, GPU):**

| Compound | Type | Mean Vina (kcal/mol) | Normalized | CNN pKd |
|-----------|--------|---------------------|------------|---------|
| Erlotinib | Binder | -6.68 | 0.90 | 6.1 |
| Gefitinib | Binder | -7.43 | 0.92 | 6.7 |
| Osimertinib | Binder | -7.47 | 0.92 | 7.1 |
| Afatinib | Binder | -7.71 | 0.93 | 6.9 |
| Ethanol | Non-binder | -1.86 | 0.65 | 2.7 |
| Aspirin | Non-binder | -5.33 | 0.85 | 3.9 |
| Caffeine | Non-binder | -4.93 | 0.84 | 4.2 |
| Glucose | Non-binder | -4.54 | 0.82 | 3.1 |

**PASS:** Binders mean=-7.32 vs Non-binders mean=-4.16 (delta=-3.16 kcal/mol)

**Key corrections made:**
- PDB 3IKU is NOT EGFR (it's E. coli ParM). Replaced with 3W2R (EGFR T790M/L858R, DFGout_aCin)
- Ligand IDs corrected from literature to actual PDB HETATM codes:
  1m17: AQ4, 2gs7: ANP, 3w2r: W2R, 4zau: YY3
- Lapatinib SMILES corrected (quinazoline `ncnc` vs benzimidazole-like `nc...n`)
- GNINA v1.3.2 requires GLIBC 2.29 (cluster has 2.28) — using v1.1 instead
- rdkit-pypi needs numpy<2 (downgraded to 1.26.4)

**What is NOT done (optional):**
- Evaluation figures integration (`evaluation/figures.py` heatmap)

---

## Next Steps

1. Optionally add heatmap to `evaluation/figures.py`
2. Run full 4-state analysis on pipeline candidates
3. Merge `ws11/gnina` branch into `ML`

### Session 2 (2026-04-07)

**Software installation:**
- GNINA v1.1 standalone binary → `bin/gnina` (293 MB, CUDA-capable)
- `pip install rdkit-pypi openbabel-wheel "numpy<2"` in worktree venv
- Requires `module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0` at runtime

**Receptor preparation:**
- All 4 EGFR state receptors prepared via `scripts/prepare_docking_receptors.py`
- Output: `data/processed/docking/receptors/{pdb_id}.pdbqt` + `{pdb_id}_box.json`
- Box centers derived from co-crystallized ligand centroids

**Validation:**
- Quick sanity check (CPU, exhaustiveness=2): erlotinib=-3.49 vs ethanol=-1.58
- Full validation (GPU L40S, exhaustiveness=8): 4 binders scored, 4 non-binders scored
- PASS: binders mean=-7.32, non-binders mean=-4.16, delta=-3.16 kcal/mol
- Lapatinib SMILES fixed (kekulization error in rdkit-pypi 2022.9.5)

**GPU guard added:**
- `_gpu_available()` helper in `ranking/scoring.py`
- Scoring cascade only attempts GNINA on GPU nodes
- Prevents test suite hang on login nodes (evaluation tests run full pipeline)

**Files created:**
- `scripts/validate_docking.py` — Validation script (--quick mode for CPU)
- `scripts/validate_docking.slurm` — SLURM GPU job for full validation
- `scripts/validate_docking_scavenge.slurm` — SLURM scavenge partition variant

**Files modified:**
- `tests/test_docking.py` — 33 tests: exhaustiveness=2 for GNINA tests, GPU guard mocks
- `src/statebind/ranking/scoring.py` — Added `_gpu_available()`, GPU guard on cascade

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md` (project rules)
2. Read `workstreams/11-gnina-docking.md` (workstream brief)
3. Read THIS file (you are here)
4. Pick up from "Next Steps" above

**DO NOT:**
- Modify `src/statebind/ml/` (model code is finalized)
- Modify `src/statebind/baselines/scoring.py` (baseline scoring is separate)
- Delete or weaken any existing tests
