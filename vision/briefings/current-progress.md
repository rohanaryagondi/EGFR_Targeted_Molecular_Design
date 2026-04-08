# Current Progress

**Last updated:** 2026-04-07T20:00:00+00:00
**Briefing session:** 3

---

## Changes Since Last Briefing (Session 2)

- **3 new workstreams merged:** WS11 (GNINA, +33 tests), WS12 (Pareto, +36 tests),
  WS13 (Retrospective, +28 tests)
- **Test count:** 548 to 646 (+98)
- **Docking cascade:** 3-tier to 4-tier (GNINA added as tier 0, GPU-only)
- **Pre-cutoff models trained:** 2 MPNN + 2 VAE for retrospective validation
- **YAML configs:** 6 to 12 (added docking, retrospective, 4 pre-cutoff configs)
- **Python source files:** 84 to 91 (+7)
- **Pipeline scripts:** 37+ to 49 (+12)
- **Admin AI:** 2 sessions completed, 24 suggestions (18 implemented)
- **Vision System:** 12 ideas proposed, 3 accepted and implemented (005->WS11,
  008->WS12, 009->WS13)

---

## Summary

All 12 planned development workstreams are complete. The pipeline is fully built,
tested, and all three ML models are trained. Physics-based docking (GNINA) is
integrated. Pareto multi-objective optimization is implemented. Retrospective
time-split validation shows the state-aware pipeline achieves 10x enrichment over
static for identifying future approved drugs. 646 tests pass.

---

## Workstream Completion

All 12 workstreams were completed and merged to the ML branch between 2026-03-25 and
2026-04-08. Zero merge conflicts across all merges.

| # | Workstream | Status | Merged | Tests Added | Key Deliverable |
|---|-----------|--------|--------|-------------|-----------------|
| 01 | Chemistry Foundation | Complete | 2026-03-25 | ~25 | RDKit-backed Morgan fingerprints, descriptors, validation, SA scoring |
| 02 | Scoring Integration | Complete | 2026-03-27 | ~40 | Wired Morgan fingerprints and QED/Lipinski/SA into scoring pipeline |
| 03 | Statistical Testing | Complete | 2026-03-26 | ~25 | Mann-Whitney U, bootstrap CI, Cohen's d, weight sensitivity analysis |
| 04 | Docking Proxy | Complete | 2026-03-28 | 19 | Lightweight MLP proxy replacing constant-0.5 docking stub |
| 05 | Visualization | Complete | 2026-03-27 | ~12 | Score distribution plots, radar charts, top-K composition figures |
| 06 | CI/CD | Complete | 2026-03-26 | 0 | GitHub Actions: test matrix (3.10/3.11/3.12), lint, chemistry tests |
| 07 | Conditional VAE | Complete | 2026-03-26 | ~15 | VAE data prep pipeline, SELFIES v3 trained (99.9% valid), generation adapter |
| 08 | MPNN Affinity | Complete | 2026-03-28 | 22 | MPNN data prep, affinity predictor (RMSE=0.7182), cascading fallback |
| 09 | ADMET Predictor | Complete | 2026-03-27 | 32 | ADMET data prep, predictor adapter (hERG AUROC=0.7745), safety filter |
| 11 | GNINA Docking | Complete | 2026-04-07 | 33 | Physics-based docking as tier 0 in cascade, 4 state receptors, GPU guard |
| 12 | Pareto Optimization | Complete | 2026-04-07 | 36 | Pareto front analysis, hypervolume comparison, crowding distance |
| 13 | Retrospective Validation | Complete | 2026-04-08 | 28 | Time-split at 2010/2015, pre-cutoff MPNN/VAE retrained, EF@10 computed |

---

## Codebase Size

| Metric | Count |
|--------|-------|
| Python source files | 91 |
| Subpackages | 12 (data, utils, processing, baselines, structure, context, dynamics, ml, generation, ranking, evaluation, chemistry) |
| Test files | 22 |
| Tests passing | 646 (up from 359 at project baseline) |
| Pipeline scripts | 49 |
| YAML config files | 12 |
| Lines of source code | ~15,000+ |

---

## Scoring Function Status

The unified scoring function has 4 components. Here is the current implementation
status of each:

| Component | Weight | Method Active Now | Previous State | Quality |
|-----------|--------|------------------|----------------|---------|
| Reference similarity | 0.35 | Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) with n-gram fallback | SMILES 3-gram Tanimoto only | Production-grade when RDKit available |
| Drug-likeness | 0.30 | QED (50%) + Lipinski violations (25%) + SA score (25%) with heuristic fallback | Heuristic linear scoring on MW/HBA/HBD/rings | Production-grade when RDKit available |
| Docking proxy | 0.20 | 4-tier cascade (see below) | Constant 0.5 for all inputs | GNINA physics-based on GPU; MPNN learned proxy otherwise |
| State specificity | 0.15 | Geometric decay: 1.0 / 0.5 / 0.25 / 0.0 by number of states | Same | Functional, unchanged |

**Cascading docking fallback chain (4 tiers):**

| Tier | Method | Condition | Quality |
|------|--------|-----------|---------|
| 0 | GNINA physics-informed docking (Vina + CNN scoring) | GPU available, GNINA binary installed, receptor prepared | Physics-based. Validated: binders -7.32 kcal/mol vs non-binders -4.16 kcal/mol (delta -3.16) |
| 1 | MPNN affinity predictor (12.7M params) | Trained checkpoint + torch available | Learned proxy. RMSE=0.7182, R^2=0.6863, Pearson=0.8323 on 10,466 compounds |
| 2 | DockingProxy MLP | Trained + RDKit available | Lightweight proxy trained on 9 binders + 25 decoys. Overfits to training set. |
| 3 | Constant 0.5 stub | Always | Zero discriminative power. Last resort. |

**Score normalization:** GNINA uses sigmoid(-vina_score / 3). MPNN uses sigmoid((pIC50 - 5) / 2). Both map to [0, 1].

---

## ML Model Status

All three primary neural network architectures are implemented and trained. Four
additional pre-cutoff models were trained for retrospective validation.

### Primary Models

| Model | Architecture | Purpose | Training Data | Key Metrics | Params |
|-------|-------------|---------|---------------|-------------|--------|
| Conditional SELFIES VAE (v3) | GRU encoder/decoder, state conditioning, SELFIES encoding | Generate novel molecules per conformational state | 8,109 train / 2,027 val (ChEMBL EGFR actives) | 99.9% valid, 94.8% unique, 300 epochs on H200 | 9.5M |
| Affinity MPNN | NNConv message-passing + MLP head | Predict pIC50 binding affinity (replaces docking stub) | 10,466 ChEMBL EGFR compounds (pIC50 4.0-11.0) | RMSE=0.7182, R^2=0.6863, Pearson=0.8323 | 12.7M |
| Multi-task ADMET | GIN backbone + 6 task-specific heads | Predict drug safety/PK endpoints (informational only) | 27,698 molecules (TDC benchmarks, 6 endpoints) | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 | 187K |

### Pre-Cutoff Models (Retrospective Validation)

| Model | Cutoff | Training Data | Key Metrics |
|-------|--------|---------------|-------------|
| MPNN pre-2010 | 2010 | 2,974 compounds (ChEMBL, document_year < 2010) | RMSE=0.701, R^2=0.717, Pearson=0.854 |
| MPNN pre-2015 | 2015 | 4,852 compounds (ChEMBL, document_year < 2015) | RMSE=0.760, R^2=0.690, Pearson=0.832 |
| VAE pre-2010 | 2010 | 2,379 train SMILES | 1,000/1,000 valid (SELFIES), 987 unique |
| VAE pre-2015 | 2015 | 3,881 train SMILES | 1,000/1,000 valid (SELFIES), 968 unique |

**Integration adapters exist for all models:**
- VAE -> generation pipeline (converts model output to candidate objects)
- MPNN -> scoring pipeline (normalizes pIC50 via sigmoid, plugs into docking slot)
- ADMET -> filtering pipeline (flags hERG liability and CYP3A4 inhibition)

All adapters fall back gracefully when models are unavailable.

---

## Pipeline Artifacts on Disk

### Training Data
- EGFR affinity dataset: 10,466 compounds with pIC50 values from ChEMBL
- ADMET combined dataset: 27,698 molecules from TDC benchmarks covering 6 endpoints
- VAE training data: 8,109 train / 2,027 val ChEMBL EGFR active SMILES (SELFIES-encoded)
- Time-split datasets: 2,974 (pre-2010) and 4,852 (pre-2015) compounds, leakage-verified

### Docking Infrastructure
- GNINA v1.1 binary (293 MB, CUDA-capable)
- 4 state-specific EGFR receptors (PDBQT format): 1M17 (DFGin/aCin), 2GS7 (DFGin/aCout), 3W2R (DFGout/aCin), 4ZAU (DFGout/aCout)
- Docking box definitions for each receptor (derived from co-crystallized ligand centroids)

### Model Checkpoints
- VAE v3 (SELFIES): 30 MB, 300 epochs on H200
- MPNN: 50 MB, trained on 10,466 compounds
- ADMET: 775 KB, trained on 27,698 molecules
- MPNN pre-2010: 49 MB, trained on 2,974 compounds
- MPNN pre-2015: 49 MB, trained on 4,852 compounds
- VAE pre-2010: trained on 2,379 SMILES
- VAE pre-2015: trained on 3,881 SMILES

### Pipeline Outputs (with trained models)
- Static baseline candidates: 30 candidates from PDB 1M17
- State-aware candidates: 461 candidates (36 template + 395 VAE-generated + 30 shared)
- Merged ranking with both pipelines scored under unified function with MPNN active
- Comparison results: state-aware mean=0.4378, max=0.7794, diversity=0.9056 vs static mean=0.5437, max=0.7288, diversity=0.5684
- Statistical tests: Mann-Whitney U p<0.001, Cohen's d=1.36 (static favored on mean). Null hypothesis formally retained.
- 431 novel candidates. Weight sensitivity: 44% state-aware / 56% static.
- Retrospective validation: state-aware EF@10=4.95/7.72 vs static 0.47/0.79 (10x enrichment)

---

## Recent Merge History

Test count progression as workstreams merged:

```
Base pipeline:         359 tests
+ WS01 (chem):         ~384 tests
+ WS02-07, WS09:       498 tests
+ WS04 (docking):      518 tests
+ WS08 (MPNN):         540 tests
+ Post-training:        548 tests
+ WS11 (GNINA):        581 tests
+ WS12 (Pareto):       618 tests
+ WS13 (retrospective): 646 tests (current)
```

All merges were clean with zero conflicts. The scoring chain (WS02 -> WS04 -> WS08)
was merged in strict sequential order to avoid conflicts in the shared scoring module.
WS11 and WS12 were merged in parallel (no shared files), then WS13 followed.

---

## Infrastructure Status

| System | Status | Notes |
|--------|--------|-------|
| CI/CD (GitHub Actions) | Configured | 3 jobs: test matrix, lint, chemistry tests. All 121 ruff violations fixed (121->0) |
| Statistical testing | Complete | Mann-Whitney U (p<0.001), bootstrap CI, Cohen's d=1.36, weight sensitivity (44%/56%) |
| Pareto optimization | Complete | Hypervolume comparison, non-dominated sorting, crowding distance, Pareto projections |
| Retrospective validation | Complete | Time-split at 2010/2015 cutoffs. Pre-cutoff MPNN + VAE retrained. EF@10 computed. |
| GNINA docking | Complete | v1.1 binary, 4 receptors prepared, validated on GPU (binders vs non-binders) |
| Visualization | Complete | Matplotlib-based, headless rendering for CI compatibility |
| Admin AI | 2 sessions complete | 24 suggestions: 18 implemented, 4 wont-fix, 2 P0 awaiting triage |
| Vision System | Session 2 active | 12 ideas proposed, 3 accepted (all implemented as WS11/12/13), 9 deferred |
