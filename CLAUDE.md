# StateBind — AI Development Guide

## Project Identity

**StateBind** is a research-grade computational biology pipeline for EGFR-targeted molecular design. The central thesis: conformational state-aware molecular design outperforms static single-structure design. The project compares a static baseline (one PDB structure, one pocket) against a state-aware pipeline (4 conformational states, pocket-conditioned generation).

**Package:** `statebind` (installed from `src/statebind/`)
**Python:** >=3.10 | **Tests:** `pytest -v --tb=short` | **Lint:** `ruff check src/`

## Non-Negotiable Rules

1. **Scientific honesty** — never overclaim. If something is a stub, label it a stub. If a result lacks statistical backing, say so.
2. **Typed Python** — all functions have type annotations. Use `from __future__ import annotations`.
3. **Pydantic v2 models** — all data structures that cross module boundaries are Pydantic `BaseModel` subclasses.
4. **Config-driven** — no hard-coded paths, thresholds, or parameters in source code. Use YAML configs in `configs/`.
5. **No hard-coded paths** — use `statebind.data.paths.DataPaths` for path resolution.
6. **Tests required** — every new module/function needs tests in `tests/`. Existing 359 tests must continue to pass.
7. **Artifacts on disk** — modules communicate via JSON artifacts in `artifacts/`, never via in-memory shared state.
8. **Backward compatibility** — when adding optional dependencies (RDKit, scipy), always provide a fallback path. The core pipeline must run with only the base dependencies.
9. **No cherry-picking** — all candidates are included in comparisons, not selected subsets.

## Architecture

12 subpackages in a sequential, acyclic pipeline:

```
data/ + utils/           Shared infrastructure (paths, config, I/O)
       |
  processing/            Raw data -> validated datasets
       |
  baselines/             Phase 2: Static single-structure pipeline
  structure/             Phase 3: Conformational state atlas
  context/               Phase 4: Mutation-to-state prediction
  dynamics/              Phase 5: State transition world model
       |
  ml/                    ML infrastructure: VAE, MPNN, ADMET models + training
       |
  generation/            Phase 6: State-conditioned candidate generation
       |
  ranking/               Phase 7: Unified scoring for both pipelines
       |
  evaluation/            Phase 7: Head-to-head comparison, tables, figures
```

## Dependency Graph

```
processing  <-- structure, context (read processed data)
baselines   <-- generation (reuses candidates, filtering, scoring functions)
             <-- ranking (reuses scoring functions)
structure   <-- generation (pocket descriptors)
ml          <-- generation (VAE for state-conditioned candidate generation)
             <-- ranking (MPNN replaces docking_proxy stub in scoring)
             <-- evaluation (ADMET predictions for safety profiling)
generation  <-- ranking (candidate models)
             <-- evaluation (diversity computation)
ranking     <-- evaluation (merged ranking, aggregation)
```

**No circular dependencies.** If you need to add a cross-module import, verify it doesn't create a cycle.

## Scoring Function (Critical to Understand)

Both pipelines are scored by the same unified function in `ranking/scoring.py`:

| Component | Weight | Method | Status |
|-----------|--------|--------|--------|
| reference_similarity | 0.35 | SMILES 3-gram Tanimoto vs erlotinib/gefitinib/osimertinib | Crude proxy (should be Morgan/ECFP4) |
| druglikeness | 0.30 | Heuristic property scoring (MW, HBA, HBD, rings) | Approximate (should use RDKit) |
| docking_proxy | 0.20 | **STUB: returns constant 0.5** — replaceable by trained MPNN (`ml.mpnn.AffinityMPNN`) which predicts pIC50 from molecular graphs | Non-functional (stub); MPNN model available in `ml/` |
| state_specificity | 0.15 | Geometric decay by state uniqueness | 0 for static baseline |

Weights must sum to 1.0 (validated by `_validate_weights()`). The docking stub wastes 20% of score weight until replaced by a trained MPNN.

## ML Models (`statebind.ml`)

Three neural network architectures with shared training infrastructure. All require optional `[ml]` dependencies (`torch`, `torch_geometric`, `rdkit`). Pydantic configs are always importable.

| Model | Config | Purpose | Input | Output |
|-------|--------|---------|-------|--------|
| Conditional SMILES VAE | `VAEConfig` | State-conditioned molecular generation | Tokenized SMILES + state one-hot | Novel SMILES per conformational state |
| Affinity MPNN | `MPNNConfig` | Binding affinity prediction (replaces docking stub) | PyG molecular graph | pIC50 (continuous) |
| Multi-task ADMET | `ADMETConfig` | Drug-safety/PK endpoint prediction | PyG molecular graph | 6 ADMET scores (regression + classification) |

**YAML configs:** `configs/vae.yaml`, `configs/mpnn.yaml`, `configs/admet.yaml`
**Checkpoints:** `artifacts/models/{vae,mpnn,admet}/best_model.pt`
**Shared classes:** `TrainerConfig`, `Trainer`, `ModelCard`, `SMILESTokenizer`, `Vocabulary`

## File Organization

```
src/statebind/       Source code (12 subpackages)
tests/               Test files (one per module, plus test_imports.py, test_cli.py)
configs/             YAML configuration files
scripts/             Pipeline runner scripts and utilities
data/raw/            Curated input data (mutations, structures, ligands)
data/processed/      Pipeline-generated processed datasets
artifacts/           Pipeline output artifacts (JSON)
reports/             Generated markdown reports
docs/                Project documentation
workstreams/         Independent improvement task briefs
```

## Running the Pipeline

```bash
# Install
pip install -e ".[dev]"

# Install ML dependencies (torch, torch_geometric, rdkit)
pip install -e ".[ml]"

# Tests
pytest -v --tb=short

# Full pipeline (sequential phases)
python scripts/build_context_dataset.py
python scripts/build_structure_dataset.py
python scripts/assemble_benchmark.py
python scripts/run_static_baseline.py
python scripts/build_state_atlas.py
python scripts/train_context_state_model.py
python scripts/train_world_model.py

# ML model training (requires [ml] extras)
python scripts/train_vae.py            # Conditional SMILES VAE
python scripts/train_mpnn.py           # Binding affinity MPNN
python scripts/train_admet.py          # Multi-task ADMET predictor

# Generation, ranking, evaluation
python scripts/generate_state_conditioned_candidates.py
python scripts/filter_generated_candidates.py
python scripts/rerank_candidates.py
python scripts/compare_baseline_vs_state_aware.py
python scripts/report_comparative_results.py
```

## Key Conventions

- **Pydantic models** for all serializable data. Use `BaseModel` with field validators where appropriate.
- **Dataclasses** for internal-only data containers (e.g., comparison results in `evaluation/`).
- **`datetime.now(timezone.utc).isoformat()`** for all timestamps.
- **`round(value, 4)`** for all floating-point scores.
- **Module-level docstrings** in every `__init__.py` explaining the module's purpose.
- **Private functions** prefixed with `_` (e.g., `_score_docking_stub`, `_tanimoto_ngram`).
- **Reference binders** (erlotinib, gefitinib, osimertinib SMILES) are defined in `baselines/scoring.py:59-66`.

## What NOT to Do

- Don't remove or skip existing tests.
- Don't change public function signatures without updating all consumers.
- Don't add in-memory coupling between modules — use disk artifacts.
- Don't claim experimental validation — this is a computational pipeline.
- Don't claim docking scores until the stub is replaced.
- Don't add dependencies to the core `[project.dependencies]` — use optional extras (e.g., `[ml]` for torch/torch_geometric/rdkit).
- Don't commit secrets, credentials, or large binary files.

## Development Workstreams

See `workstreams/README.md` for independent improvement tasks designed for parallel AI development. Each workstream file is self-contained with exact files to create/modify, interface contracts, and testing requirements.

## Per-Module Documentation

Every `src/statebind/*/README.md` documents that module's API, dependencies, data flow, and testing. Read the relevant module README before modifying any module.
