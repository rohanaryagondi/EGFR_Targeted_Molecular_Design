# StateBind -- AI Development Guide

Read this file and `CRITICAL.md` before writing code. Detailed reference docs
are in `docs/ai-guide/` -- read them when working on the relevant area.

## Quick Reference

```
Package:   statebind (installed from src/statebind/)
Python:    >=3.10
Tests:     pytest -v --tb=short   (618 passing)
Lint:      ruff check src/
Install:   pip install -e ".[dev]"
ML deps:   pip install -e ".[ml]"
CLI:       statebind (typer app, defined in statebind.cli:app)
```

## Project Thesis

**StateBind** tests whether conformational state-aware molecular design outperforms
static single-structure design for EGFR-targeted small molecules. EGFR has 4
conformational states (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout). The
project compares a static baseline (1M17, one pocket) against a state-aware pipeline
(4 states, pocket-conditioned generation). Both scored by the SAME unified function
(`ranking/scoring.py`). All results are computational hypotheses, never biological claims.

## Non-Negotiable Rules

1. **Scientific honesty.** Never overclaim. Label stubs as stubs.
2. **Typed Python.** All functions have type annotations. Use `from __future__ import annotations`.
3. **Pydantic v2 models.** All cross-module data structures are `BaseModel` subclasses.
4. **Config-driven.** No hard-coded thresholds/parameters. Use YAML configs in `configs/`.
5. **No hard-coded paths.** Use `statebind.data.paths.DataPaths` for path resolution.
6. **Tests required.** Every new function needs tests. 618+ tests must pass. Run pytest before commits. See `docs/ai-guide/testing-and-deps.md` for full testing policy including SLURM GPU test requirements.
7. **Artifacts on disk.** Modules communicate via JSON in `artifacts/`, never in-memory.
8. **Backward compatibility.** Optional deps (RDKit, scipy, torch) always have fallback paths.
   Core deps: numpy, pandas, pyyaml, pydantic, typer, rich.
9. **No cherry-picking.** Report full distributions, not selected subsets.
10. **Continuous documentation.** Maintain `reports/workstreams/ws{NN}-report.md` after every
    major step. Keep "Current State" and "Next Steps" always accurate.

## Architecture (12 subpackages)

```
data/ + utils/ + chemistry/   Shared infrastructure
       |
  processing/                 Phase 1: Raw data -> validated datasets
       |
  baselines/                  Phase 2: Static single-structure pipeline
  structure/                  Phase 3: Conformational state atlas
  context/                    Phase 4: Mutation-to-state prediction
  dynamics/                   Phase 5: State transition world model
       |
  ml/                         ML: VAE, MPNN, ADMET (requires [ml] extras)
       |
  generation/                 Phase 6: State-conditioned candidate generation
       |
  ranking/                    Phase 7a: Unified scoring for both pipelines
       |
  evaluation/                 Phase 7b: Head-to-head comparison
```

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `data/` | Path resolution, registry, manifests | `paths.py`, `registry.py` |
| `utils/` | Config loading, JSON I/O | `config.py`, `io.py` |
| `chemistry/` | Fingerprints, descriptors, SA scores, docking proxy, GNINA wrapper | `fingerprints.py`, `descriptors.py`, `docking.py` |
| `processing/` | Raw data -> validated datasets | `context.py`, `structures.py`, `models.py` |
| `baselines/` | Static pipeline (1M17) | `scoring.py`, `filtering.py`, `pipeline.py` |
| `structure/` | State atlas (4 states, 9D features) | `atlas.py`, `features.py` |
| `context/` | Mutation-to-state prediction | `features.py`, `training.py` |
| `dynamics/` | State transition world model | `world_model.py`, `transitions.py` |
| `ml/` | 3 neural nets + training + integration | `vae.py`, `mpnn.py`, `admet.py`, `trainer.py` |
| `generation/` | State-conditioned generation + filtering | `generator.py`, `filtering.py` |
| `ranking/` | Unified scoring, Pareto optimization | `scoring.py`, `pareto.py` |
| `evaluation/` | Comparison, statistics, figures, Pareto, docking analysis | `comparison.py`, `figures.py`, `pareto_comparison.py`, `docking_analysis.py` |

## File Organization

```
repo/
|-- CLAUDE.md, CRITICAL.md       AI guides (this file + non-obvious facts)
|-- pyproject.toml                Package definition
|-- src/statebind/                84 .py files across 12 subpackages
|-- tests/                        21 test files, 618 tests
|-- configs/                      7 YAML: default, structure, context, vae, mpnn, admet, docking
|-- scripts/                      37 pipeline scripts
|-- data/raw/, data/processed/    Input and processed datasets
|-- artifacts/                    Pipeline outputs (JSON artifacts)
|-- reports/                      Generated reports
|-- docs/                         Documentation (incl. docs/ai-guide/ reference)
|-- workstreams/                  9 workstream briefs + INTERFACES.md
|-- vision/                       Vision System: briefings, ideas, logs
|-- admin/                        Admin AI: suggestions and audit log
+-- HumanOnly/                    Human-only (AI agents must NOT read)
```

## Conventions

- **Pydantic BaseModel** for cross-module data; **dataclass** for module-internal only.
- **Timestamps:** `datetime.now(timezone.utc).isoformat()` -- always UTC ISO.
- **Scores:** round to 4 decimal places.
- **Naming:** `_private_func`, `public_func`, `UPPER_SNAKE_CASE` constants.
- **Pipeline labels:** `PipelineLabel.STATIC` and `PipelineLabel.STATE_AWARE` (`ranking/models.py`).
- **Artifacts:** JSON with `generated_at` and `notes` fields.

## What NOT to Do

- Do not remove or skip existing tests.
- Do not change public function signatures without updating all consumers.
- Do not add in-memory coupling between modules -- use disk artifacts.
- Do not claim experimental validation -- computational pipeline only.
- Do not add torch/rdkit/scipy/scikit-learn to core `[project.dependencies]`.
- Do not commit secrets, credentials, or large binary files.
- Do not create circular imports. Flow is always downward (see dependency graph).
- Do not mock scoring in integration tests -- mock I/O, not scoring logic.
- Do not change `DEFAULT_WEIGHTS` without updating `SCORING_METHOD` (`ranking/scoring.py:86-97`).
- Do not modify `_REFERENCE_BINDERS` without re-running the full pipeline (`baselines/scoring.py:59-66`).
- Do not use `datetime.now()` without `timezone.utc`.
- Do not read files in `HumanOnly/`.
- Do not run workstreams 02, 04, and 08 in parallel (all modify `ranking/scoring.py`).

## Reference Docs (read when working on the relevant area)

| Doc | Contents |
|-----|----------|
| `CRITICAL.md` | Non-obvious facts: scoring gotchas, workstream conflicts, ML infra, path resolution |
| `docs/ai-guide/scoring-and-architecture.md` | Scoring deep dive, dependency graph, component weights, fallback cascade |
| `docs/ai-guide/ml-models.md` | VAE/MPNN/ADMET architectures, training commands, integration adapters |
| `docs/ai-guide/pipeline-and-config.md` | Config system, data flow per phase, execution order, debug guide |
| `docs/ai-guide/testing-and-deps.md` | Testing patterns, optional dependency handling, dependency groups |
| `docs/ai-guide/workstreams.md` | Workstream index, parallel groups, conflict zones, worktree naming |
| `docs/ai-guide/operations.md` | Merge procedure, documentation system, vision system, admin system |
