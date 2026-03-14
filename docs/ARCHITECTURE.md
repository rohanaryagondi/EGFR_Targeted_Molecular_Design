# Architecture

## System Overview

StateBind is a five-module sequential pipeline. Each module has a defined contract: typed inputs, typed outputs, serialized artifacts, and a runnable script. Modules communicate exclusively through artifacts on disk (JSON, CSV, SDF, PDB files) — never through in-memory shared state. This makes every module independently testable, restartable, and inspectable.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         StateBind Pipeline                              │
│                                                                         │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐      │
│  │  CONTEXT   │───→│ STRUCTURE │───→│ DYNAMICS  │───→│GENERATION │      │
│  │           │    │           │    │           │    │           │      │
│  │ Mutation   │    │ State     │    │ State     │    │ Candidate │      │
│  │ atlas,     │    │ atlas,    │    │ relevance │    │ molecules │      │
│  │ resistance │    │ pockets,  │    │ predictions│   │ per state │      │
│  │ annotations│    │ classif.  │    │           │    │           │      │
│  └───────────┘    └───────────┘    └───────────┘    └─────┬─────┘      │
│                                                           │             │
│                                                           ▼             │
│                   ┌──────────────────────────────────────────────┐      │
│                   │              RANKING                         │      │
│                   │                                              │      │
│                   │  Score candidates across states              │      │
│                   │  Compare: state-aware vs. static baseline    │      │
│                   │  Statistical tests, effect sizes             │      │
│                   │  Final ranked lists + comparison report       │      │
│                   └──────────────────────────────────────────────┘      │
│                                                                         │
│  ┌─────────────────────────────────────────────────┐                   │
│  │            BASELINE (parallel track)             │                   │
│  │                                                  │                   │
│  │  Same generation + scoring pipeline, but using   │                   │
│  │  a single static structure (best-resolution PDB) │                   │
│  │  instead of state-predicted pocket ensemble.     │                   │
│  └─────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Module Boundaries and Contracts

### Module 1: Context (`statebind.context`)

**Responsibility:** Curate and serve EGFR mutation data with resistance annotations.

| Aspect | Detail |
|--------|--------|
| **Input** | Mutation identifiers (e.g., `T790M`), data source configs |
| **Output** | `MutationRecord` objects with: residue position, wild-type/mutant amino acid, resistance generation, mechanism category, known drug associations, conformational effect (if literature-documented) |
| **Primary artifact** | `artifacts/context/mutation_atlas.json` |
| **Secondary artifacts** | `artifacts/context/mutation_summary.csv` |
| **Script** | `scripts/run_context.py` |
| **Dependencies** | None (first module in pipeline) |
| **Key types** | `MutationRecord`, `ResistanceMechanism`, `MutationAtlas` (Pydantic models) |

### Module 2: Structure (`statebind.structure`)

**Responsibility:** Download, classify, and extract pockets from EGFR PDB structures.

| Aspect | Detail |
|--------|--------|
| **Input** | PDB IDs (curated list or queried), mutation atlas |
| **Output** | Classified structures with state labels, extracted pocket geometries, representative structure per state |
| **Primary artifact** | `artifacts/structure/state_atlas.json` |
| **Secondary artifacts** | `artifacts/structure/pockets/<state>/<pdb_id>.json`, `artifacts/structure/representatives.json` |
| **Script** | `scripts/run_structure.py` |
| **Dependencies** | Context module (for mutation-structure mapping) |
| **Key types** | `ConformationalState`, `StructureRecord`, `PocketGeometry`, `StateAtlas` |

**Classification scheme:** Each structure is labeled on two binary axes:
- DFG motif: in (catalytically competent) vs. out (inactive)
- αC-helix: in (salt bridge intact) vs. out (rotated)

This gives 4 canonical states: `DFGin-αCin` (active), `DFGin-αCout` (Src-like inactive), `DFGout-αCin`, `DFGout-αCout` (classical inactive).

### Module 3: Dynamics (`statebind.dynamics`)

**Responsibility:** Predict which conformational states are most relevant given a mutation context.

| Aspect | Detail |
|--------|--------|
| **Input** | Mutation context (from Context module), state atlas (from Structure module) |
| **Output** | State relevance scores: probability distribution over the 4 canonical states for a given mutation |
| **Primary artifact** | `artifacts/dynamics/state_predictions.json` |
| **Secondary artifacts** | `artifacts/dynamics/state_relevance_matrix.csv` |
| **Script** | `scripts/run_dynamics.py` |
| **Dependencies** | Context module, Structure module |
| **Baseline** | Curated lookup table (literature-derived mutation→state mapping) |
| **Stretch** | Lightweight classifier trained on PDB metadata (mutation × deposited state co-occurrence) |

### Module 4: Generation (`statebind.generation`)

**Responsibility:** Generate candidate molecules conditioned on pocket geometry.

| Aspect | Detail |
|--------|--------|
| **Input** | Pocket geometries (from Structure module), state relevance predictions (from Dynamics module) |
| **Output** | Candidate molecules as SMILES with generation metadata (which pocket, which state, generation method) |
| **Primary artifact** | `artifacts/generation/candidates_stateaware.csv` |
| **Secondary artifacts** | `artifacts/generation/candidates_baseline.csv` |
| **Script** | `scripts/run_generation.py` |
| **Dependencies** | Structure module, Dynamics module |

**Two parallel runs:**
- **State-aware:** Generate against top-ranked state pocket(s) from Dynamics predictions
- **Baseline:** Generate against the single best-resolution PDB pocket (static)

### Module 5: Ranking (`statebind.ranking`)

**Responsibility:** Score all candidates, compare state-aware vs. baseline, report results.

| Aspect | Detail |
|--------|--------|
| **Input** | Candidate molecules (both tracks), pocket geometries (all states), state predictions |
| **Output** | Scored and ranked candidate lists, statistical comparison, final report |
| **Primary artifact** | `artifacts/ranking/comparison_results.json` |
| **Secondary artifacts** | `artifacts/ranking/scores_stateaware.csv`, `artifacts/ranking/scores_baseline.csv`, `reports/final_comparison.md` |
| **Script** | `scripts/run_ranking.py` |
| **Dependencies** | All upstream modules |

## Where Baselines Fit

Baselines are not an afterthought — they are a parallel track that runs through the pipeline:

```
                    ┌──────────────────┐
                    │  Context Module   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Structure Module  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼                              ▼
   ┌─────────────────┐           ┌─────────────────┐
   │ Dynamics Module  │           │ BASELINE:        │
   │ (state-aware     │           │ Skip dynamics.   │
   │  prediction)     │           │ Use single best  │
   │                  │           │ structure.        │
   └────────┬────────┘           └────────┬────────┘
            ▼                              ▼
   ┌─────────────────┐           ┌─────────────────┐
   │ Generation       │           │ Generation       │
   │ (state pockets)  │           │ (static pocket)  │
   └────────┬────────┘           └────────┬────────┘
            │                              │
            └──────────┬───────────────────┘
                       ▼
              ┌─────────────────┐
              │ Ranking Module   │
              │ (compare both)   │
              └─────────────────┘
```

**Defined baselines:**

| Baseline | Description | Purpose |
|----------|-------------|---------|
| **B1: Static single-structure** | Generate + score against the highest-resolution WT EGFR structure | Primary comparison |
| **B2: Random pocket** | Generate against a randomly selected state's pocket | Tests whether state selection matters vs. just using multiple structures |
| **B3: Random molecules (stretch)** | Sample random drug-like SMILES from ZINC | Sanity check that generation is better than random |

## Where Ablations Fit

Ablations test which components of the state-aware pipeline contribute to any observed improvement:

| Ablation | What is removed | What it tests |
|----------|----------------|---------------|
| **A1: No state prediction** | Use all states equally (uniform distribution) | Does state relevance prediction matter? |
| **A2: No multi-state scoring** | Score only against the top-1 predicted state | Does cross-state scoring add value? |
| **A3: No pocket conditioning** | Generate molecules without pocket features | Does pocket-conditioned generation matter vs. unconditioned? |

Ablations are secondary deliverables. At minimum, B1 must be compared. Ablations strengthen the scientific argument but are not required for v1 to ship.

## Artifact Flow

```
artifacts/
├── context/
│   ├── mutation_atlas.json          ← Context module
│   └── mutation_summary.csv         ← Context module
├── structure/
│   ├── state_atlas.json             ← Structure module
│   ├── representatives.json         ← Structure module
│   └── pockets/
│       ├── DFGin_aCin/              ← Structure module
│       ├── DFGin_aCout/             ← Structure module
│       ├── DFGout_aCin/             ← Structure module
│       └── DFGout_aCout/            ← Structure module
├── dynamics/
│   ├── state_predictions.json       ← Dynamics module (reads context + structure)
│   └── state_relevance_matrix.csv   ← Dynamics module
├── generation/
│   ├── candidates_stateaware.csv    ← Generation module (reads structure + dynamics)
│   └── candidates_baseline.csv      ← Generation module (reads structure only)
└── ranking/
    ├── comparison_results.json      ← Ranking module (reads everything)
    ├── scores_stateaware.csv        ← Ranking module
    └── scores_baseline.csv          ← Ranking module

reports/
└── final_comparison.md              ← Ranking module
```

## Shared Utilities (`statebind.utils`)

| File | Purpose |
|------|---------|
| `config.py` | YAML config loading with validation |
| `io.py` | JSON/CSV read/write, directory creation |
| `types.py` | Shared Pydantic base models and enums |
| `logging.py` | Structured logging setup |
| `metrics.py` | Shared metric computation helpers |

## Configuration Strategy

All module behavior is controlled by YAML configs in `configs/`. No hard-coded paths, parameters, or thresholds in source code. Each module has its own config file; a `default.yaml` provides shared settings.

```
configs/
├── default.yaml        # Shared paths, logging
├── context.yaml        # Mutation sources, filters
├── structure.yaml      # PDB list, classification thresholds
├── dynamics.yaml       # Prediction method, parameters
├── generation.yaml     # Generation method, pocket representation
└── ranking.yaml        # Scoring functions, statistical tests
```

## Failure Points and Mitigation

| Failure point | Likelihood | Impact | Mitigation |
|--------------|------------|--------|------------|
| Too few PDB structures in underrepresented states (DFGout-αCout) | High | Cannot build balanced state atlas | Accept imbalanced atlas; note in report; consider AlphaFold-predicted structures for missing states |
| Docking scores too noisy to distinguish state-aware from baseline | Medium | Null result | Use multiple scoring functions; report effect sizes; a well-characterized null result is still publishable |
| Pocket extraction produces inconsistent geometries across states | Medium | Generation quality suffers | Validate pocket extraction visually on known co-crystal structures; use conservative extraction radius |
| Mutation→state lookup table too sparse for meaningful prediction | Medium | Dynamics module adds no value | This is an expected possible outcome; report it honestly; the lookup table IS the baseline |
| RDKit/docking tool compatibility issues | Low | Blocks generation/scoring | Pin dependency versions; have fallback to simpler scoring (pharmacophore fingerprint similarity) |
| Scope creep into MD, deep learning, multi-target | Medium | Project never ships | Enforce scope via charter; each phase has a hard stop |

## Testing Strategy

| Level | What | Where |
|-------|------|-------|
| **Structure tests** | Verify project conventions (dirs exist, init files present, configs valid) | `tests/test_structure.py` |
| **Unit tests** | Per-module function tests with fixtures | `tests/test_<module>.py` |
| **Integration tests** | Two-module handoff tests (does Context output parse as Structure input?) | `tests/test_pipeline.py` |
| **Smoke tests** | End-to-end pipeline on minimal toy data | `tests/test_smoke.py` |
| **Benchmark tests** | Full pipeline on real data, compare to saved baselines | `scripts/run_benchmark.py` |
