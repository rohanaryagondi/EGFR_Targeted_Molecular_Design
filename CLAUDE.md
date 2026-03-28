# StateBind -- AI Development Guide

This is THE starting point for any AI developer working on this project. Read this
entire file before writing a single line of code.

---

## 1. Project Identity & Thesis

**StateBind** is a research-grade computational biology pipeline for EGFR-targeted
molecular design. It tests a specific scientific hypothesis:

> Conformational state-aware molecular design outperforms static single-structure
> design for EGFR-targeted small molecules.

EGFR (Epidermal Growth Factor Receptor) has 4 canonical conformational states
defined by two binary structural features:

| State | DFG motif | alphaC-helix | PDB example |
|-------|-----------|--------------|-------------|
| DFGin_aCin | DFG-in | alphaC-in | Active kinase |
| DFGin_aCout | DFG-in | alphaC-out | Src-like inactive |
| DFGout_aCin | DFG-out | alphaC-in | Intermediate |
| DFGout_aCout | DFG-out | alphaC-out | Fully inactive |

The project compares two pipelines head-to-head:
- **Static baseline:** One PDB structure (1M17), one pocket, no state awareness.
- **State-aware pipeline:** 4 conformational states, pocket-conditioned generation,
  state-specificity scoring.

Both pipelines are scored by the SAME unified function (`ranking/scoring.py`) so the
comparison is fair. The only axis where state-aware can win is the `state_specificity`
component (15% weight).

**Key numbers:**
- 72 Python source files across 12 subpackages (~13,700 lines)
- 37 pipeline scripts in `scripts/`
- 12 test modules + `test_imports.py` + `test_cli.py` = 14 test files, 359 tests
- 3 neural network architectures (VAE, MPNN, ADMET)
- 6 YAML config files
- All results are computational hypotheses, never biological claims

**Quick reference:**
```
Package:   statebind (installed from src/statebind/)
Python:    >=3.10
Tests:     pytest -v --tb=short
Lint:      ruff check src/
Install:   pip install -e ".[dev]"
ML deps:   pip install -e ".[ml]"
CLI:       statebind (typer app, defined in statebind.cli:app)
License:   MIT
```

---

## 2. Non-Negotiable Rules

### Rule 1: Scientific honesty
Never overclaim. If something is a stub, label it a stub. If a result lacks
statistical backing, say so.

- BAD: "Our molecules show strong binding affinity to EGFR."
- GOOD: "Our scoring proxy suggests moderate similarity to known binders (Tanimoto 0.35)."

### Rule 2: Typed Python
All functions have type annotations. Use `from __future__ import annotations` at the
top of every file.

- BAD: `def score(smiles, weights=None):`
- GOOD: `def score(smiles: str, weights: dict[str, float] | None = None) -> float:`

### Rule 3: Pydantic v2 models
All data structures that cross module boundaries are Pydantic `BaseModel` subclasses.

- BAD: `return {"score": 0.5, "method": "stub"}` passed between modules.
- GOOD: `return UnifiedScoreComponent(name="docking_proxy", value=0.5, method="STUB", is_stub=True)`

### Rule 4: Config-driven
No hard-coded paths, thresholds, or parameters in source code. Use YAML configs in
`configs/`.

- BAD: `if score > 0.7:` hard-coded in source.
- GOOD: `if score > config["thresholds"]["min_score"]:` loaded from YAML.

### Rule 5: No hard-coded paths
Use `statebind.data.paths.DataPaths` for path resolution. DataPaths auto-detects the
project root by walking up from `src/statebind/data/paths.py`.

- BAD: `open("/home/user/project/data/raw/mutations.json")`
- GOOD: `paths = DataPaths(); paths.raw_dir / "mutations.json"`

### Rule 6: Tests required
Every new module/function needs tests in `tests/`. Existing 359 tests must continue to
pass. Run `pytest -v --tb=short` before every commit.

- BAD: Adding a new scoring function with no test file.
- GOOD: Adding `test_new_scoring.py` with unit tests for edge cases and expected outputs.

### Rule 7: Artifacts on disk
Modules communicate via JSON artifacts in `artifacts/`, never via in-memory shared
state. This makes the pipeline resumable and debuggable.

- BAD: `ranking_result = score_all(generation_result)` -- passing objects between phases.
- GOOD: `save_json(result, "artifacts/ranking/scored.json")` then `load_json("artifacts/ranking/scored.json")` in the next script.

### Rule 8: Backward compatibility
When adding optional dependencies (RDKit, scipy), always provide a fallback path. The
core pipeline must run with only the base dependencies (numpy, pandas, pyyaml, pydantic,
typer, rich).

- BAD: `from rdkit import Chem` at module top level with no guard.
- GOOD: `try: from rdkit import Chem; HAS_RDKIT = True` / `except ImportError: HAS_RDKIT = False`

### Rule 9: No cherry-picking
All candidates are included in comparisons, not selected subsets. Report full
distributions, not just top-K highlights.

- BAD: "We selected the 5 best-scoring candidates to demonstrate superiority."
- GOOD: "Score distributions across all 200 candidates (static) vs 180 candidates (state-aware)."

### Rule 10: Continuous documentation
Every AI agent must maintain a progress report at `reports/workstreams/ws{NN}-report.md`
throughout its session. Update the report after every major step -- file created, test
written, decision made. This serves as the handoff mechanism when context compacts or
another agent takes over.

- BAD: Writing code for 2 hours, then producing a summary at the end (or not at all).
- GOOD: Updating the report after each completed step, keeping "Current State" and
  "Next Steps" always accurate.

See Section 17 for the full documentation system.

---

## 3. Complete Architecture

12 subpackages in a sequential, acyclic pipeline:

```
data/ + utils/           Shared infrastructure (paths, config, I/O)
       |
  processing/            Phase 1: Raw data -> validated datasets
       |
  baselines/             Phase 2: Static single-structure pipeline
  structure/             Phase 3: Conformational state atlas
  context/               Phase 4: Mutation-to-state prediction
  dynamics/              Phase 5: State transition world model
       |
  ml/                    ML infrastructure: VAE, MPNN, ADMET
       |
  generation/            Phase 6: State-conditioned candidate generation
       |
  ranking/               Phase 7: Unified scoring for both pipelines
       |
  evaluation/            Phase 7: Head-to-head comparison
```

### Module Details

| Module | Files | Phase | Purpose | Key Files |
|--------|-------|-------|---------|-----------|
| `data/` | 5 | Infra | Path resolution, source registry, manifests, validation | `paths.py` (DataPaths), `registry.py`, `manifest.py`, `validation.py` |
| `utils/` | 3 | Infra | Config loading, JSON I/O, directory management | `config.py` (load_config), `io.py` (save_json, load_json, ensure_dir) |
| `processing/` | 8 | 1 | Raw data -> validated datasets (mutations, structures, ligands) | `context.py`, `structures.py`, `benchmark.py`, `models.py` |
| `baselines/` | 8 | 2 | Static single-structure pipeline (1M17, one pocket, no state info) | `scoring.py` (:59-66 reference binders, :135 docking stub), `filtering.py`, `pipeline.py` |
| `structure/` | 6 | 3 | Conformational state atlas (4 states via 9D feature vectors) | `atlas.py`, `features.py`, `clustering.py`, `pocket_comparison.py` |
| `context/` | 6 | 4 | Mutation-to-state prediction (T790M -> which states?) | `features.py`, `training.py`, `preprocessing.py`, `evaluation.py` |
| `dynamics/` | 6 | 5 | State transition world model (inter-state dynamics) | `world_model.py`, `transitions.py`, `sequences.py`, `embeddings.py` |
| `ml/` | 13 | ML | 3 neural nets + shared training (requires `[ml]` extras) | `vae.py`, `mpnn.py`, `admet.py`, `trainer.py`, `graphs.py`, `tokenizer.py` |
| `generation/` | 7 | 6 | State-conditioned candidate generation + filtering | `generator.py`, `filtering.py`, `conditioning.py`, `diversity.py` |
| `ranking/` | 4 | 7a | Unified scoring for BOTH pipelines (heart of fair comparison) | `scoring.py` (:40 DEFAULT_WEIGHTS, :89 validation, :100 score_unified) |
| `evaluation/` | 4 | 7b | Head-to-head comparison, tables, figures, verdict | `comparison.py` (run_full_comparison), `tables.py`, `figures.py` |
| `pockets/` | 0 | -- | Placeholder for future pocket analysis | (empty) |

---

## 4. Dependency Graph

```
data/ + utils/ -> processing/ -> baselines/, structure/, context/, dynamics/
                                      |            |
                                      v            v
                                   ml/ (torch, torch_geometric, rdkit)
                                  / | \
                                 v  v  v
                          generation/  |
                              |        |
                           ranking/ <--+
                              |
                          evaluation/
```

| Upstream | Downstream | Why |
|----------|------------|-----|
| processing | structure, context | Read processed PDB/mutation datasets |
| baselines | generation | Reuses candidate filtering and scoring functions |
| baselines | ranking | `ranking/scoring.py` imports `_score_*` from `baselines/scoring.py` |
| structure | generation | Pocket descriptors condition the generator |
| ml | generation | VAE generates state-conditioned candidates |
| ml | ranking | MPNN replaces docking_proxy stub in scoring |
| ml | evaluation | ADMET predictions for safety profiling |
| generation | ranking, evaluation | Candidate models consumed; diversity computed |
| ranking | evaluation | MergedRanking is input to all comparison functions |

**No circular dependencies.** The direction is always downward. Verify before adding
any cross-module import.

---

## 5. Scoring Function Deep Dive

Both pipelines are scored by `ranking/scoring.py:score_unified()` (line 100). The
function delegates to component scorers defined in `baselines/scoring.py`.

### Component Table

| Component | Weight | Implementation | File:Line | Status |
|-----------|--------|---------------|-----------|--------|
| reference_similarity | 0.35 | Max SMILES 3-gram Tanimoto vs 3 reference binders | `baselines/scoring.py:69` | Crude proxy; should use Morgan/ECFP4 |
| druglikeness | 0.30 | Linear scoring on MW [300-500], HBA [3-7], HBD [1-3], rings [2-5] | `baselines/scoring.py:83` | Approximate; should use RDKit descriptors |
| docking_proxy | 0.20 | **STUB: returns constant 0.5 for all inputs** | `baselines/scoring.py:135` | Non-functional; wastes 20% of score weight |
| state_specificity | 0.15 | Geometric decay: 1.0/0.5/0.25/0.0 by number of states candidate appears in | `ranking/scoring.py:55` | Functional; always 0 for static baseline |

### Weight Definition & Validation

- **Weights defined:** `ranking/scoring.py:40-45` (`DEFAULT_WEIGHTS` dict)
- **Weights validated:** `ranking/scoring.py:89-97` (`_validate_weights()`) -- checks
  all 4 keys present and sum == 1.0 (tolerance 1e-4)
- **Method string:** `ranking/scoring.py:47-52` (`SCORING_METHOD`) -- human-readable
  description embedded in every RankedPool artifact

### Reference Binders

Defined at `baselines/scoring.py:59-66`:
- Erlotinib: `COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC`
- Gefitinib: `COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1`
- Osimertinib: `COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1`

### Cascading Fallback Plan for docking_proxy

The docking_proxy component has a planned 3-tier fallback (see
`workstreams/INTERFACES.md` Contract 4):

```
Priority 1: MPNN prediction (AffinityMPNN predicts pIC50, normalize via sigmoid)
    - Requires: trained model at artifacts/models/mpnn/best_model.pt + torch
    - Implemented in: ml/mpnn.py (model) + ml/affinity_predictor.py (integration, to be created)

Priority 2: DockingProxy MLP (Workstream 04, lightweight numpy-based)
    - Requires: trained proxy from chemistry/docking_proxy.py
    - Interface: DockingProxy.predict(smiles) -> float in [0.0, 1.0]

Priority 3: Constant 0.5 stub (current default)
    - File: baselines/scoring.py:135-149
    - Always available, zero discriminative power
```

### Baseline vs Unified Scoring Difference

The baseline has its OWN scorer at `baselines/scoring.py:155` (`score_candidates()`)
with slightly different weights (0.4/0.3/0.3, no state_specificity). The UNIFIED scorer
at `ranking/scoring.py:100` (`score_unified()`) uses 0.35/0.30/0.20/0.15. The unified
scorer is what matters for the head-to-head comparison. The baseline scorer exists only
for Phase 2 standalone runs.

---

## 6. ML Models

### Summary Table

| Model | Config Class | Purpose | Input | Output | Config YAML | Checkpoint Path |
|-------|-------------|---------|-------|--------|-------------|-----------------|
| Conditional SMILES VAE | `VAEConfig` | State-conditioned molecular generation | Tokenized SMILES + state one-hot (4 states) | Novel SMILES per conformational state | `configs/vae.yaml` | `artifacts/models/vae/best_model.pt` |
| Affinity MPNN | `MPNNConfig` | Binding affinity prediction (replaces docking stub) | PyG molecular graph (atom_dim=35, bond_dim=11) | pIC50 (continuous, single float) | `configs/mpnn.yaml` | `artifacts/models/mpnn/best_model.pt` |
| Multi-task ADMET | `ADMETConfig` | Drug safety/PK endpoint prediction | PyG molecular graph (atom_dim=35, bond_dim=11) | 6 ADMET scores (regression + classification) | `configs/admet.yaml` | `artifacts/models/admet/best_model.pt` |

### Conditional SMILES VAE (`ml/vae.py`)

Architecture: GRU encoder (bidirectional) + GRU decoder with teacher forcing.
State conditioning is concatenated to encoder inputs at every timestep AND to the
latent code before decoder projection. This means the same latent space generates
different molecules depending on which conformational state is conditioned on.

- Encoder: `GRU(embed_dim + state_dim, hidden_dim, n_layers, bidirectional=True)`
- Latent: `mu = Linear(2*hidden_dim, latent_dim)`, `logvar = Linear(2*hidden_dim, latent_dim)`
- Reparameterization: `z = mu + eps * exp(0.5 * logvar)`
- Decoder: `z_proj = Linear(latent_dim + state_dim, hidden_dim * n_layers)` then
  `GRU(embed_dim, hidden_dim, n_layers)`
- Loss: reconstruction (cross-entropy) + KL divergence with annealing
- KL annealing: linear warmup over 20 epochs from 0 to `kl_weight` (0.01)
- Training: ~200 epochs, batch_size=128, cosine LR schedule, ~2-4 hours on single GPU
- Classes: `VAEConfig`, `SMILESEncoder`, `SMILESDecoder`, `ConditionalSMILESVAE`

### Affinity MPNN (`ml/mpnn.py`)

Architecture: NNConv message passing layers with residual connections + graph-level
readout (mean_max pooling or Set2Set) + MLP prediction head.

- Input projection: `Linear(atom_feature_dim, hidden_dim)` (atom_feature_dim=35)
- Message passing: N layers of `NNConv(hidden_dim, hidden_dim, edge_nn)` + `BatchNorm1d` + ReLU + residual
- Edge network: `Sequential(Linear(bond_feature_dim, hidden_dim), ReLU, Linear(hidden_dim, hidden_dim*hidden_dim))`
- Readout: `concat(global_mean_pool, global_max_pool)` -> 2*hidden_dim
- Prediction head: `Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout -> Linear(hidden_dim, 1)`
- Output: single pIC50 value (continuous)
- Training: ~150 epochs, batch_size=64, cosine LR, ~1-2 hours on single GPU
- Evaluation metrics: RMSE, MAE, R-squared, Pearson correlation

### Multi-task ADMET (`ml/admet.py`)

Architecture: Shared GIN (Graph Isomorphism Network) backbone with task-specific
MLP heads. The backbone learns a general molecular representation; each head
specializes for one ADMET endpoint.

- Backbone: N GIN layers (default 3): `GINConv(hidden_dim, hidden_dim)` + `BatchNorm1d` + ReLU + Dropout
- Readout: `concat(global_mean_pool, global_max_pool)` -> 2*hidden_dim
- Shared projection: `Linear(2*hidden_dim, hidden_dim) -> ReLU -> Dropout`
- Per-task heads: `Linear(hidden_dim, hidden_dim//2) -> ReLU -> Dropout -> Linear(hidden_dim//2, 1)`
- 6 endpoints: caco2 (regression), hERG (classification, safety-critical, weight=1.5),
  CYP3A4 (classification), clearance (regression), lipophilicity (regression),
  solubility (regression)
- Loss: MSE for regression tasks, BCE for classification tasks, weighted sum
- Training: ~150 epochs, batch_size=64, ~2-3 hours on single GPU
- Data source: Therapeutics Data Commons (TDC) ADMET benchmarks

### Training Commands

```bash
# Requires: pip install -e ".[ml]"
python scripts/train_vae.py            # Conditional SMILES VAE
python scripts/train_mpnn.py           # Binding affinity MPNN
python scripts/train_admet.py          # Multi-task ADMET predictor
```

### Integration Plan

- **VAE -> generation:** `ml/vae_integration.py` (to be created) produces
  `StateConditionedCandidate` objects with `source=ML_GENERATED`, `strategy=VAE_GENERATED`.
  See `workstreams/INTERFACES.md` Contract 5.
- **MPNN -> ranking:** `ml/affinity_predictor.py` (to be created) provides
  `predict_affinity(smiles) -> float` in [0, 1]. Normalizes pIC50 via
  `sigmoid((pIC50 - 5) / 2)`. Falls back to 0.5 stub. See Contract 4.
- **ADMET -> evaluation:** `ml/admet_predictor.py` (to be created) provides
  `predict_admet(smiles) -> dict[str, float]` and `check_admet_pass(smiles) -> (bool, dict)`.
  See Contract 6.

---

## 7. Config System

All configuration is driven by YAML files in `configs/`. Scripts accept a `--config`
CLI argument (convention, not enforced by framework). Configs are loaded via
`statebind.utils.config.load_config()` which returns a plain dict.

### Config Files

| File | Purpose | Used By |
|------|---------|---------|
| `configs/default.yaml` | Project-level defaults: name, version, paths, logging | All scripts (base config) |
| `configs/structure.yaml` | Structure module: PDB references, classification thresholds, output dirs | `scripts/build_state_atlas.py`, `scripts/run_structure.py` |
| `configs/context.yaml` | Context module: target gene (EGFR), UniProt ID (P00533), mutation list, sources | `scripts/build_context_dataset.py`, `scripts/run_context.py` |
| `configs/vae.yaml` | VAE hyperparameters: vocab_size=150, embed_dim=128, hidden_dim=256, latent_dim=64, KL annealing (20 epoch warmup) | `scripts/train_vae.py` |
| `configs/mpnn.yaml` | MPNN hyperparameters: hidden_dim=128, 3 message-passing layers, mean_max readout | `scripts/train_mpnn.py` |
| `configs/admet.yaml` | ADMET hyperparameters: GIN backbone, 6 tasks, task weights (hERG=1.5x) | `scripts/train_admet.py` |

### Config Convention

YAML structure: `model:` (hyperparameters), `training:` (epochs, LR, device),
`data:` (paths, splits). `training.device: auto` means auto-detect GPU/CPU.
`training.seed: 42` is the default. Checkpoints: `artifacts/models/{name}/`.
Logs: `artifacts/logs/{name}/`.

---

## 8. Data Flow Per Phase

| Phase | Script(s) | Input | Output Artifacts |
|-------|-----------|-------|-----------------|
| 0 - Data validation | `scripts/validate_data_layout.py`, `scripts/register_sources.py` | `data/raw/*.json` | `artifacts/data/manifest.json` |
| 1 - Processing | `scripts/build_context_dataset.py`, `scripts/build_structure_dataset.py`, `scripts/build_ligand_dataset.py`, `scripts/assemble_benchmark.py` | `data/raw/` | `data/processed/*.json`, `artifacts/processing/benchmark.json` |
| 2 - Static baseline | `scripts/run_static_baseline.py`, `scripts/extract_baseline_pocket.py`, `scripts/select_baseline_structure.py` | `data/processed/`, `configs/default.yaml` | `artifacts/baselines/static_candidates.json`, `artifacts/baselines/ranked.json` |
| 3 - Structure atlas | `scripts/build_state_atlas.py`, `scripts/cluster_structural_states.py`, `scripts/compare_pockets_across_states.py` | `data/processed/structures.json`, `configs/structure.yaml` | `artifacts/structure/state_atlas.json`, `artifacts/structure/pockets/` |
| 4 - Context model | `scripts/train_context_state_model.py`, `scripts/train_context_baseline.py`, `scripts/evaluate_context_state_model.py` | `data/processed/`, `configs/context.yaml` | `artifacts/context/mutation_atlas.json`, `artifacts/context/model_metrics.json` |
| 5 - World model | `scripts/train_world_model.py`, `scripts/build_state_sequences.py`, `scripts/train_transition_baseline.py`, `scripts/evaluate_world_model.py` | `artifacts/structure/`, `artifacts/context/` | `artifacts/dynamics/world_model.json`, `artifacts/dynamics/transitions.json` |
| ML - VAE training | `scripts/train_vae.py` | `data/processed/egfr_smiles_train.json`, `configs/vae.yaml` | `artifacts/models/vae/best_model.pt`, `artifacts/logs/vae/` |
| ML - MPNN training | `scripts/train_mpnn.py` | `data/processed/egfr_affinity.json`, `configs/mpnn.yaml` | `artifacts/models/mpnn/best_model.pt`, `artifacts/logs/mpnn/` |
| ML - ADMET training | `scripts/train_admet.py` | `data/processed/admet_combined.json`, `configs/admet.yaml` | `artifacts/models/admet/best_model.pt`, `artifacts/logs/admet/` |
| 6 - Generation | `scripts/generate_state_conditioned_candidates.py`, `scripts/filter_generated_candidates.py` | `artifacts/structure/`, `artifacts/context/` | `artifacts/generation/candidates.json`, `artifacts/generation/filtered.json` |
| 7a - Ranking | `scripts/rerank_candidates.py` | `artifacts/baselines/`, `artifacts/generation/` | `artifacts/ranking/merged.json` |
| 7b - Evaluation | `scripts/compare_baseline_vs_state_aware.py`, `scripts/report_comparative_results.py`, `scripts/generate_final_summary.py` | `artifacts/ranking/merged.json` | `artifacts/evaluation/comparison.json`, `reports/*.md` |

### Execution Order (abbreviated)

```bash
# Phase 0-1    validate_data_layout.py -> build_context_dataset.py -> build_structure_dataset.py -> assemble_benchmark.py
# Phase 2      run_static_baseline.py
# Phase 3-5    build_state_atlas.py -> train_context_state_model.py -> train_world_model.py
# ML (opt)     train_vae.py, train_mpnn.py, train_admet.py
# Phase 6-7    generate_state_conditioned_candidates.py -> filter_generated_candidates.py -> rerank_candidates.py -> compare_baseline_vs_state_aware.py -> report_comparative_results.py
```

---

## 9. File Organization

```
BioForge/
|-- CLAUDE.md                    This file
|-- pyproject.toml               Package definition, deps, tool config
|-- src/statebind/               72 .py files across 12 subpackages (see Section 3)
|-- tests/                       14 test files, 359 tests (test_{module}.py pattern)
|-- configs/                     6 YAML files: default, structure, context, vae, mpnn, admet
|-- scripts/                     37 pipeline scripts (see Section 8 for execution order)
|-- data/raw/                    Curated input data (mutations, structures, ligands)
|-- data/processed/              Pipeline-generated processed datasets
|-- artifacts/                   Pipeline outputs: baselines/, context/, dynamics/, evaluation/,
|                                generation/, models/{vae,mpnn,admet}/, logs/, ranking/, structure/
|-- reports/                     Generated markdown reports
|-- docs/                        PROJECT_CHARTER.md and other documentation
|-- notebooks/                   Jupyter notebooks
+-- workstreams/                 9 independent improvement task briefs + INTERFACES.md
```

---

## 10. Testing Patterns

### Running Tests

```bash
pytest -v --tb=short                    # All tests
pytest tests/test_ranking.py -v         # Single module
pytest tests/test_ranking.py::test_unified_scoring -v   # Single test
pytest -k "scoring" -v                  # Tests matching keyword
pytest --co -q                          # List all tests without running
```

### Conventions

- One test file per subpackage: `tests/test_{module}.py`.
- `test_imports.py` is a smoke test that verifies all modules are importable and
  key classes/functions exist. This catches broken imports early.
- Test functions follow `test_{what_is_being_tested}` naming.
- Tests import directly from source: `from statebind.ranking.scoring import score_unified`.

### Fixture Patterns

Tests construct their own data inline rather than using shared conftest fixtures.
This keeps each test file self-contained and readable. Example pattern from
`test_ranking.py`:

```python
# Tests import pipeline functions and call them to generate test data:
from statebind.baselines.pipeline import run_static_baseline
from statebind.generation.generator import generate_all_states
from statebind.generation.filtering import filter_all_states
```

### Optional Dependency Testing

For ML modules that require torch/torch_geometric/rdkit, use `pytest.importorskip()`:

```python
def test_mpnn_forward():
    torch = pytest.importorskip("torch")
    pyg = pytest.importorskip("torch_geometric")
    # ... test code that requires torch and PyG
```

Alternatively, check the module-level flags:

```python
from statebind.ml import HAS_TORCH
@pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")
def test_vae_training():
    ...
```

### Test Count Verification

If you add tests, the total count must be >= 359. Never delete or skip existing
tests without explicit justification.

---

## 11. Workstream System

Workstreams are independent improvement tasks designed for parallel AI development.
Each workstream file in `workstreams/` is self-contained: an AI agent given only
the workstream file, `CLAUDE.md`, and the relevant module READMEs can execute the
work autonomously.

### Workstream Index

| # | Name | Effort | Impact | Dependencies |
|---|------|--------|--------|-------------|
| 01 | Chemistry Foundation | Moderate | High | None |
| 02 | Scoring Integration | Low | High | 01 |
| 03 | Statistical Testing | Low | High | None |
| 04 | Docking Proxy | Moderate | Critical | 01 |
| 05 | Visualization | Low | Moderate | 03 |
| 06 | CI/CD | Low | Moderate | None |
| 07 | Conditional VAE | High | High | None (01 helpful) |
| 08 | MPNN Affinity | High | Critical | 01 |
| 09 | ADMET Predictor | High | High | 01 |

### Three Parallel Groups

**Group A** -- Start immediately (no dependencies):
- WS01: Chemistry Foundation (RDKit integration, fingerprints, descriptors)
- WS03: Statistical Testing (Mann-Whitney U, bootstrap CI, effect sizes)
- WS06: CI/CD (GitHub Actions, automated testing)
- WS07: Conditional VAE (train and integrate VAE for generation)

**Group B** -- After WS01 completes:
- WS02: Scoring Integration (replace n-gram with Morgan fingerprints)
- WS04: Docking Proxy (lightweight MLP-based proxy)
- WS08: MPNN Affinity (train MPNN, replace docking stub)
- WS09: ADMET Predictor (train multi-task ADMET, add safety filtering)

**Group C** -- After WS03 completes:
- WS05: Visualization (score distributions, radar plots, comparison figures)

### Conflict Zone: WS02 -> WS04 -> WS08

Workstreams 02, 04, and 08 ALL modify `ranking/scoring.py`. They must NOT run in
parallel. Execute in order: WS02 (Morgan fingerprints) -> WS04 (docking proxy MLP) ->
WS08 (MPNN replaces docking proxy). Each builds a fallback layer on top of the
previous.

WS09 modifies the filtering pipeline (`generation/`) and does not conflict with
scoring workstreams.

### Worktree Naming Convention

Each modular agent runs in its own isolated git worktree. Worktree names MUST
reflect the workstream — never use auto-generated names.

**Format:** `ws{NN}-{short-description}`
**Branch:** `ws{NN}/{short-description}`
**Location:** `.claude/worktrees/ws{NN}-{short-description}`

| WS | Worktree Name | Branch |
|----|---------------|--------|
| 01 | `ws01-chemistry` | `ws01/chemistry` |
| 02 | `ws02-scoring` | `ws02/scoring` |
| 03 | `ws03-stats` | `ws03/stats` |
| 04 | `ws04-docking` | `ws04/docking` |
| 05 | `ws05-viz` | `ws05/viz` |
| 06 | `ws06-cicd` | `ws06/cicd` |
| 07 | `ws07-vae` | `ws07/vae` |
| 08 | `ws08-mpnn` | `ws08/mpnn` |
| 09 | `ws09-admet` | `ws09/admet` |

For non-workstream tasks, use `task-{short-description}` (e.g., `task-docs-update`).

**Head AI has no worktree.** The Head AI always operates directly on the `ML` branch
in the main repository. It commits and pushes directly to `origin/ML`. It does not
create or live in a worktree. Only modular agents use worktrees.

### How to Deploy an Agent on a Workstream

Give the agent these files (in order of priority):
1. `CLAUDE.md` -- project rules and architecture
2. `workstreams/{NN}-{name}.md` -- the specific workstream brief
3. `src/statebind/{module}/README.md` -- relevant module documentation
4. `workstreams/INTERFACES.md` -- interface contracts the workstream must honor

Each workstream file contains: goal, files to create, files to modify, interface
contracts, existing code to reuse (with file:line references), files NOT to touch,
testing requirements, and definition of done.

---

## 12. Optional Dependencies

### The Pattern

The canonical pattern for optional dependencies is demonstrated in `ml/__init__.py`
(lines 22-40):

```python
# Module-level boolean flags
HAS_TORCH: bool
try:
    import torch as _torch  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

HAS_TORCH_GEOMETRIC: bool
try:
    import torch_geometric as _pyg  # noqa: F401
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False
```

### Key Principles

1. **Boolean flags at module level.** Callers check `HAS_TORCH` rather than catching
   ImportError themselves. Flags are defined in the `__init__.py` of the module that
   owns the dependency.

2. **Pydantic configs are always importable.** `VAEConfig`, `MPNNConfig`, `ADMETConfig`,
   `TrainerConfig` are all Pydantic models that require ONLY pydantic (a core dep).
   They live in the config section of each model file and are imported even when
   torch is not available. This means you can always load, validate, and serialize
   configs without ML libraries.

3. **Neural network classes are guarded.** The actual model classes (`ConditionalSMILESVAE`,
   `AffinityMPNN`, `MultiTaskADMET`) use `TYPE_CHECKING` guards and are only
   instantiable when torch is present.

4. **Fallback behavior is always defined.** Every function that might use an optional
   dep must specify what happens when the dep is missing:
   - Scoring: falls back to n-gram Tanimoto (no RDKit)
   - Docking: falls back to constant 0.5 (no MPNN)
   - ADMET: falls back to permissive pass (no model)
   - Validation: falls back to permissive True (no RDKit)

### Dependency Groups (from `pyproject.toml`)

| Extra | Packages | Purpose |
|-------|----------|---------|
| (core) | numpy, pandas, pyyaml, pydantic, typer, rich | Base pipeline, always available |
| `[dev]` | pytest, pytest-cov, ruff, mypy | Testing and linting |
| `[science]` | scikit-learn, scipy, matplotlib, seaborn | Statistical analysis, visualization |
| `[structure]` | biopython | PDB structure parsing |
| `[chemistry]` | rdkit | Molecular fingerprints, descriptors, validation |
| `[ml]` | torch, torch-geometric, rdkit | Neural network training and inference |

---

## 13. Debug Guide

| # | Problem | Solution |
|---|---------|----------|
| 1 | `ModuleNotFoundError: No module named 'statebind'` | Run `pip install -e ".[dev]"` from project root. |
| 2 | `ImportError: cannot import name 'AffinityMPNN'` | Install ML deps: `pip install -e ".[ml]"`. The class requires torch. |
| 3 | `ValueError: Scoring weights must sum to 1.0` | Check `DEFAULT_WEIGHTS` in `ranking/scoring.py:40`. Your custom weights dict must have all 4 keys summing to 1.0. |
| 4 | `FileNotFoundError` on any data path | Use `DataPaths()` for resolution. Check `data/raw/` exists. Run `scripts/validate_data_layout.py`. |
| 5 | Tests fail with `assert statebind.__version__ == "0.1.0"` | Version is pinned in both `pyproject.toml:7` and `src/statebind/__init__.py`. Keep them in sync. |
| 6 | `pydantic.ValidationError` on model construction | Check field types match Pydantic v2 expectations. Common: `float` vs `int`, missing required fields. |
| 7 | All docking scores are 0.5 | Expected. `_score_docking_stub` returns constant 0.5. This is a known stub (see Section 5). |
| 8 | State-aware scores barely beat static | Expected with current scoring. The state_specificity component is only 15% weight, and the docking stub wastes another 20%. |
| 9 | `torch_geometric` import fails despite torch being installed | PyG requires matching CUDA/torch versions. Install via: `pip install torch-geometric -f https://data.pyg.org/whl/torch-{version}+{cuda}.html` |
| 10 | Circular import error between modules | You violated the dependency graph. Check Section 4. The import direction must flow downward. |

---

## 14. Conventions

### Data Modeling
- **Pydantic `BaseModel`** for all data that crosses module boundaries (artifacts,
  API returns, config objects). This gives you validation, serialization, and
  type safety.
- **`dataclasses.dataclass`** for internal-only data containers that don't leave
  the module (e.g., `ComparativeResult` in `evaluation/`, `StatisticalTest` in
  future statistics module).

### Timestamps
Always use UTC ISO format:
```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()
```

### Floating Point
Round all scores to 4 decimal places:
```python
composite = round(sum(c.value * c.weight for c in components), 4)
```

### Naming
- **Private functions** prefixed with `_`: `_score_docking_stub`, `_tanimoto_ngram`,
  `_compute_state_specificity`, `_validate_weights`.
- **Public functions** are unprefixed: `score_unified`, `rank_static_baseline`,
  `merge_rankings`.
- **Constants** are UPPER_SNAKE_CASE: `DEFAULT_WEIGHTS`, `SCORING_METHOD`,
  `_REFERENCE_BINDERS`, `ATOM_FEATURE_DIM`.
- **Module-level docstrings** in every `__init__.py` explaining the module's purpose.

### Reference Binder Location
The three reference EGFR binders (erlotinib, gefitinib, osimertinib) are defined
at `baselines/scoring.py:59-66` in the `_REFERENCE_BINDERS` list. Any code that
needs reference SMILES should import from there, not redefine them.

### Artifact Format
All artifacts are JSON files with at minimum:
- A `generated_at` field (UTC ISO timestamp)
- A `notes` field (human-readable description)
- Descriptive keys (not positional arrays)

### Pipeline Labels
Two canonical labels defined in `ranking/models.py`:
- `PipelineLabel.STATIC` -- the static baseline
- `PipelineLabel.STATE_AWARE` -- the state-conditioned pipeline

---

## 15. What NOT to Do

### Existing Rules (do not remove)
- Do not remove or skip existing tests.
- Do not change public function signatures without updating all consumers.
- Do not add in-memory coupling between modules -- use disk artifacts.
- Do not claim experimental validation -- this is a computational pipeline.
- Do not claim docking scores until the stub is replaced.
- Do not add dependencies to the core `[project.dependencies]` -- use optional extras.
- Do not commit secrets, credentials, or large binary files.

### Additional Rules
- **Do not create circular imports.** The dependency graph (Section 4) is acyclic.
  If your import creates a cycle, restructure. Move shared types to a lower-level
  module (typically `data/` or `utils/`).

- **Do not mock scoring in integration tests.** The scoring function IS the thing
  being tested. If you mock `_score_docking_stub`, you are testing nothing. Mock
  external I/O (file reads), not scoring logic.

- **Do not add `torch`, `torch_geometric`, `rdkit`, `scipy`, or `scikit-learn` to
  core `[project.dependencies]`.** These are always optional extras. The base
  pipeline must run with only: numpy, pandas, pyyaml, pydantic, typer, rich.

- **Do not change `DEFAULT_WEIGHTS` without updating `SCORING_METHOD`.** They are
  defined 7 lines apart in `ranking/scoring.py:40-52` and must stay in sync. The
  `SCORING_METHOD` string is embedded in every artifact for reproducibility.

- **Do not modify `_REFERENCE_BINDERS` without re-running the full pipeline.** All
  similarity scores change. Defined at `baselines/scoring.py:59-66`.

- **Do not cherry-pick top-K results for claims.** Report full distributions.

- **Do not use `datetime.now()` without `timezone.utc`.** Naive datetimes are not
  reproducible across timezones.

- **Do not create new top-level directories** without updating this guide (Section 9).

- **Do not run workstreams 02, 04, and 08 in parallel.** They all modify
  `ranking/scoring.py` and must execute sequentially (see Section 11).

---

## 16. Head AI: Worktree Merge Procedure

The Head AI operates directly on the `ML` branch — no worktree. All commits and
pushes go to `origin/ML`. The Head AI's job is to merge completed modular agent
worktrees into ML and push.

**Never merge without explicit human confirmation.**

### Step-by-Step Procedure

**1. Locate worktrees.**
```bash
ls .claude/worktrees/
git worktree list
```
Worktrees follow the `ws{NN}-{description}` naming convention (Section 11). For ML
work done on an HPC cluster, the worktree is not at the standard path — ask the user:
"Where is the worktree for this work?" Do not guess.

**2. Ask the user before merging each worktree.**
For each ready branch, ask: "Is the work on `ws{NN}-{name}` ready to merge?" Do NOT
proceed without a "yes". The user may want to review output, run additional tests, or
hold a worktree for further iteration.

**3. Check for file conflicts between branches.**
```bash
git diff --name-only ML...ws{NN}/{description}
```
If two pending branches modify the same file, flag it before merging. The scoring
chain (WS02 → WS04 → WS08) always merges in that order — never simultaneously.

**4. Run tests in each worktree before merging.**
```bash
cd .claude/worktrees/ws{NN}-{name} && pytest -v --tb=short
```
Do not merge a branch with failing tests.

**5. Merge from the main repository (on ML branch).**
```bash
git merge ws{NN}/{description} -m "Merge WS{NN}: {title}"
```
Independent branches merge in any order. Dependent branches follow the dependency
graph (Section 11).

**6. Push and verify.**
```bash
git push origin ML
git log --oneline -10
```
Confirm all expected commits appear on `origin/ML`.

---

## 17. Documentation System

Every AI agent -- modular or head -- must produce and continuously maintain a detailed
progress report. These reports are the primary mechanism for:

1. **Context recovery** -- when the context window compacts, re-read your report to
   know where you left off.
2. **Agent handoff** -- if you are replaced by another agent, your report is the only
   thing it reads (besides CLAUDE.md and the workstream brief).
3. **Human review** -- the human operator uses your report to verify your work.
4. **Historical record** -- future agents and humans can understand why decisions
   were made.

### Report Location and Naming

```
reports/workstreams/TEMPLATE.md     -- The template (copy for new reports)
reports/workstreams/ws{NN}-report.md -- One report per workstream
```

### When to Update Your Report

Update your report file **after every major action**:

- Created a file -> log it in "Progress Log" and "Files Created"
- Modified a file -> log it in "Progress Log" and "Files Modified"
- Wrote tests -> log in "Tests Written" with count and coverage
- Made a non-obvious decision -> log in "Decisions Made" with rationale
- Hit a blocker -> log in "Issues Encountered" and update "Current State"
- Completed a milestone -> update "Current State" and "Next Steps"

**Minimum update frequency:** after every 2-3 tool calls that change the codebase.
Do not wait until the end of your session.

### What Must Always Be Accurate

Two sections must be kept current at all times:

1. **Current State** -- what is done, what is in progress, what remains, any blockers.
2. **Next Steps** -- ordered list of what to do next.

If your context compacts, these two sections are what you re-read to get oriented.

### Context Recovery Procedure

If you notice your conversation context has been compacted (prior messages summarized),
do the following before continuing work:

1. Read your report: `reports/workstreams/ws{NN}-report.md`
2. Read your workstream brief: `workstreams/{NN}-{name}.md`
3. Check git status: `git status` and `git log --oneline -5`
4. Resume from "Next Steps" in your report

### Head AI Documentation

The Head AI does not have a workstream report. Instead, it documents merge operations
and cross-cutting decisions directly in commit messages and by updating:
- `workstreams/README.md` (workstream status table)
- `CLAUDE.md` (if architectural decisions change)
- `CRITICAL.md` (if cross-cutting issues arise)

### Template Reference

The full template is at `reports/workstreams/TEMPLATE.md`. Copy it when starting a
new workstream. Key sections:
- **Status** -- state, timestamps, counts
- **Progress Log** -- chronological work log (newest first)
- **Current State** -- always-accurate snapshot
- **Next Steps** -- ordered action list
- **Files Created/Modified** -- complete file inventory
- **Architecture Decisions** -- non-obvious choices with rationale
- **Handoff Notes** -- critical context for replacement agents
