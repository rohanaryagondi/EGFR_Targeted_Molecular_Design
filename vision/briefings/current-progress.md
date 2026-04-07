# Current Progress

**Last updated:** 2026-04-07T00:00:00+00:00
**Briefing session:** 2 (final update)

---

## Summary

All planned development workstreams are complete. The pipeline is fully built,
tested, and all three ML models have been trained. The central hypothesis has been
tested: the null hypothesis was formally retained (p<0.001, Cohen's d=1.36, but
the static baseline had higher mean scores). All ruff violations fixed. 548 tests pass.

---

## Workstream Completion

All 9 workstreams were completed and merged to the ML branch between 2026-03-25 and
2026-03-28. Zero merge conflicts occurred.

| # | Workstream | Status | Merged | Tests Added | Key Deliverable |
|---|-----------|--------|--------|-------------|-----------------|
| 01 | Chemistry Foundation | Complete | 2026-03-25 | ~25 | RDKit-backed Morgan fingerprints, descriptors, validation, SA scoring |
| 02 | Scoring Integration | Complete | 2026-03-27 | ~40 | Wired Morgan fingerprints and QED/Lipinski/SA into scoring pipeline |
| 03 | Statistical Testing | Complete | 2026-03-26 | ~25 | Mann-Whitney U, bootstrap CI, Cohen's d, weight sensitivity analysis |
| 04 | Docking Proxy | Complete | 2026-03-28 | 19 | Lightweight MLP proxy replacing constant-0.5 docking stub |
| 05 | Visualization | Complete | 2026-03-27 | ~12 | Score distribution plots, radar charts, top-K composition figures |
| 06 | CI/CD | Complete | 2026-03-26 | 0 | GitHub Actions: test matrix (3.10/3.11/3.12), lint, chemistry tests |
| 07 | Conditional VAE | Complete | 2026-03-26 | ~15 | VAE data prep pipeline, generation integration adapter |
| 08 | MPNN Affinity | Complete | 2026-03-28 | 22 | MPNN data prep, affinity predictor adapter, cascading fallback chain |
| 09 | ADMET Predictor | Complete | 2026-03-27 | 32 | ADMET data prep, predictor adapter, safety filter gate |

---

## Codebase Size

| Metric | Count |
|--------|-------|
| Python source files | 84 |
| Subpackages | 12 (data, utils, processing, baselines, structure, context, dynamics, ml, generation, ranking, evaluation, chemistry) |
| Test files | 19 |
| Tests passing | 548 (up from 359 at project baseline) |
| Pipeline scripts | 37+ |
| YAML config files | 6 |
| Lines of source code | ~13,700+ |

---

## Scoring Function Status

The unified scoring function has 4 components. Here is the current implementation
status of each:

| Component | Weight | Method Active Now | Previous State | Quality |
|-----------|--------|------------------|----------------|---------|
| Reference similarity | 0.35 | Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) with n-gram fallback | SMILES 3-gram Tanimoto only | Production-grade when RDKit available |
| Drug-likeness | 0.30 | QED (50%) + Lipinski violations (25%) + SA score (25%) with heuristic fallback | Heuristic linear scoring on MW/HBA/HBD/rings | Production-grade when RDKit available |
| Docking proxy | 0.20 | MPNN affinity predictor (12.7M params, RMSE=0.7182, R²=0.6863, Pearson=0.8323) | Constant 0.5 for all inputs | MPNN trained on 10,466 ChEMBL EGFR compounds. Falls back to DockingProxy MLP, then constant 0.5 stub |
| State specificity | 0.15 | Geometric decay: 1.0 / 0.5 / 0.25 / 0.0 by number of states | Same | Functional, unchanged |

**Cascading docking fallback chain (tier 1 active):**
1. MPNN affinity predictor (active — 12.7M params, trained on 10,466 compounds, RMSE=0.7182)
2. DockingProxy MLP (fallback, trained on 9 binders + 25 decoys)
3. Constant 0.5 stub (last resort)

---

## ML Model Status

All three neural network architectures are implemented and trained.

| Model | Architecture | Purpose | Code Status | Training Data | Key Metrics | Params |
|-------|-------------|---------|-------------|---------------|-------------|--------|
| Conditional SELFIES VAE (v3) | GRU encoder/decoder, state conditioning, SELFIES encoding | Generate novel molecules per conformational state | Trained | 8,109 train / 2,027 val (ChEMBL EGFR actives) | 99.9% valid, 94.8% unique, 300 epochs on H200 | 9.5M |
| Affinity MPNN | NNConv message-passing + MLP head | Predict pIC50 binding affinity (replaces docking stub) | Trained | 10,466 ChEMBL EGFR compounds (pIC50 4.0-11.0) | RMSE=0.7182, R²=0.6863, Pearson=0.8323 | 12.7M |
| Multi-task ADMET | GIN backbone + 6 task-specific heads | Predict drug safety/PK endpoints (informational only) | Trained | 27,698 molecules (TDC benchmarks, 6 endpoints) | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 | 187K |

**Integration adapters exist for all three models:**
- VAE → generation pipeline (converts model output to candidate objects)
- MPNN → scoring pipeline (normalizes pIC50 via sigmoid, plugs into docking slot)
- ADMET → filtering pipeline (flags hERG liability and CYP3A4 inhibition)

All adapters fall back gracefully when models are unavailable.

---

## Pipeline Artifacts on Disk

### Training Data
- EGFR affinity dataset: 10,466 compounds with pIC50 values from ChEMBL (was 1,678 before pagination fix)
- ADMET combined dataset: 27,698 molecules from TDC benchmarks covering 6 endpoints
- VAE training data: 8,109 train / 2,027 val ChEMBL EGFR active SMILES (SELFIES-encoded)

### Pipeline Outputs (with trained models)
- Static baseline candidates: 30 candidates from PDB 1M17
- State-aware candidates: 461 candidates (36 template + 395 VAE-generated + 30 shared)
- Merged ranking with both pipelines scored under unified function with MPNN active
- Comparison results: state-aware mean=0.4378, max=0.7794, diversity=0.9056 vs static mean=0.5437, max=0.7288, diversity=0.5684
- Statistical tests: Mann-Whitney U p<0.001, Cohen's d=1.36 (static favored). Null hypothesis formally retained.
- 431 novel candidates. Weight sensitivity: 44% state-aware / 56% static.

### Model Checkpoints on Disk
- VAE v3 (SELFIES): trained 300 epochs on H200
- MPNN: trained on 10,466 compounds
- ADMET: trained on 27,698 molecules

---

## Recent Merge History

Test count progression as workstreams merged:

```
Base pipeline:     359 tests
+ WS01 (chem):     ~384 tests
+ WS02-07, WS09:   498 tests
+ WS04 (docking):  518 tests
+ WS08 (MPNN):     540 tests
+ Post-training:   548 tests (final)
```

All merges were clean with zero conflicts. The scoring chain (WS02 → WS04 → WS08) was
merged in strict sequential order to avoid conflicts in the shared scoring module.

---

## Infrastructure Status

| System | Status | Notes |
|--------|--------|-------|
| CI/CD (GitHub Actions) | Configured | 3 jobs: test matrix, lint, chemistry tests. All 121 ruff violations fixed (121→0) |
| Statistical testing | Complete | Mann-Whitney U (p<0.001), bootstrap CI, Cohen's d=1.36, weight sensitivity (44%/56%) — run on trained model scores |
| Visualization | Complete | Matplotlib-based, headless rendering for CI compatibility |
| Admin AI | Scaffolded, never run | Template files exist, no audit performed yet |
| Vision System | This is the first session | Briefings being created now |

---

## What Has Been Completed Since Last Briefing

1. **ML model training** — all three models trained on GPU (MPNN, ADMET on GPU; VAE v3 300 epochs on H200)
2. **Full pipeline re-run** — end-to-end with trained MPNN scores active in the cascade
3. **Statistical hypothesis testing** — Mann-Whitney U p<0.001, Cohen's d=1.36, null formally retained (static baseline had higher mean scores)
4. **Ruff lint cleanup** — all 121 violations fixed (121→0)
5. **Documentation refresh** — CLAUDE.md updated to 548 tests, 84 Python files, 12 subpackages
6. **VAE retraining** — VAE v3 with SELFIES encoding: 99.9% valid, 94.8% unique
7. **ADMET finding** — hard filtering rejects ALL kinase inhibitors on hERG; ADMET used informational only
8. **ChEMBL pagination fix** — MPNN training data expanded from 1,678 to 10,466 compounds
