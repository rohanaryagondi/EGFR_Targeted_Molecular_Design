# Current Progress

**Last updated:** 2026-03-30T00:00:00+00:00
**Briefing session:** 1 (first briefing)

---

## Summary

All planned development workstreams are complete. The pipeline is fully built and
tested. The project is blocked on GPU-based ML model training — three neural networks
are code-complete but have never been trained. No model checkpoints exist.

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
| Python source files | 86 |
| Subpackages | 13 (data, utils, processing, baselines, structure, context, dynamics, ml, generation, ranking, evaluation, chemistry, pockets) |
| Test files | 19 |
| Tests passing | 540 (up from 359 at project baseline) |
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
| Docking proxy | 0.20 | Lightweight MLP trained on 9 EGFR binders + 25 decoys | Constant 0.5 for all inputs | Discriminates known binders from decoys (AUROC >0.7 on training set) but trained on tiny dataset. MPNN adapter ready but model untrained |
| State specificity | 0.15 | Geometric decay: 1.0 / 0.5 / 0.25 / 0.0 by number of states | Same | Functional, unchanged |

**Cascading docking fallback chain (ready but tier 1 inactive):**
1. MPNN affinity predictor (adapter written, model untrained — currently skipped)
2. DockingProxy MLP (active, trained on embedded data)
3. Constant 0.5 stub (last resort)

---

## ML Model Status

Three neural network architectures are implemented. None have been trained.

| Model | Architecture | Purpose | Code Status | Training Data | Checkpoint | Training Time (est.) |
|-------|-------------|---------|-------------|---------------|------------|---------------------|
| Conditional SMILES VAE | GRU encoder/decoder, state conditioning | Generate novel molecules per conformational state | Complete | Prepared (ChEMBL EGFR actives) | None | 2-4 hours GPU |
| Affinity MPNN | NNConv message-passing + MLP head | Predict pIC50 binding affinity (replaces docking stub) | Complete | Prepared (1,678 ChEMBL compounds, pIC50 4.0-11.0) | None | 1-2 hours GPU |
| Multi-task ADMET | GIN backbone + 6 task-specific heads | Predict drug safety/PK endpoints | Complete | Prepared (TDC benchmarks, 6 endpoints) | None | 2-3 hours GPU |

**Integration adapters exist for all three models:**
- VAE → generation pipeline (converts model output to candidate objects)
- MPNN → scoring pipeline (normalizes pIC50 via sigmoid, plugs into docking slot)
- ADMET → filtering pipeline (flags hERG liability and CYP3A4 inhibition)

All adapters fall back gracefully when models are unavailable.

---

## Pipeline Artifacts on Disk

### Training Data (prepared, ready for GPU training)
- EGFR affinity dataset: 1,678 compounds with pIC50 values from ChEMBL
- ADMET combined dataset: TDC benchmark data covering 6 endpoints
- VAE training data: ChEMBL EGFR active SMILES

### Pipeline Outputs (from current stub/proxy scoring)
- Static baseline candidates: 30 candidates from PDB 1M17
- State-aware candidates: 49 candidates from 7 strategies across 4 states
- Merged ranking with both pipelines scored under unified function
- Observed delta: mean score +0.020, diversity +0.035 (state-aware over static)

### Not Yet on Disk
- No model checkpoints (VAE, MPNN, or ADMET)
- No comparison results with trained model scores
- No statistical test results (Mann-Whitney U not yet run with real data)

---

## Recent Merge History

Test count progression as workstreams merged:

```
Base pipeline:     359 tests
+ WS01 (chem):     ~384 tests
+ WS02-07, WS09:   498 tests
+ WS04 (docking):  518 tests
+ WS08 (MPNN):     540 tests
```

All merges were clean with zero conflicts. The scoring chain (WS02 → WS04 → WS08) was
merged in strict sequential order to avoid conflicts in the shared scoring module.

---

## Infrastructure Status

| System | Status | Notes |
|--------|--------|-------|
| CI/CD (GitHub Actions) | Configured | 3 jobs: test matrix, lint, chemistry tests. ~40 pre-existing ruff violations remain |
| Statistical testing | Framework complete | Mann-Whitney U, bootstrap CI, effect sizes, sensitivity analysis — not yet run on real data |
| Visualization | Complete | Matplotlib-based, headless rendering for CI compatibility |
| Admin AI | Scaffolded, never run | Template files exist, no audit performed yet |
| Vision System | This is the first session | Briefings being created now |

---

## What Is NOT Done

1. **ML model training** — all three models need GPU time (estimated 5-9 hours total)
2. **Full pipeline re-run** — must re-run end-to-end with trained model scores
3. **Statistical hypothesis testing** — Mann-Whitney U on real scores to reject/retain null
4. **Ruff lint cleanup** — ~40 pre-existing violations blocking clean CI
5. **Documentation refresh** — some references in CLAUDE.md cite 359 tests (now 540)
