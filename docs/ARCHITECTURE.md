# Architecture

## System Design

StateBind is organized as a pipeline of five modules, each with a defined input/output contract. Modules communicate through serialized artifacts (JSON, CSV, PDB files) stored under `artifacts/`.

```
Context → Structure → Dynamics → Generation → Ranking
```

Each module is a Python subpackage under `src/statebind/` with:
- A public API defined in `__init__.py`
- Config-driven execution via YAML files in `configs/`
- A runnable script in `scripts/`
- Tests in `tests/`

## Module Contracts

### 1. Context Module (`statebind.context`)

**Purpose:** Curate EGFR mutation data and map mutations to resistance mechanisms.

- **Input:** Mutation query (e.g., `T790M`, `C797S`)
- **Output:** Structured mutation record with annotations (resistance type, prevalence, co-occurring mutations, literature references)
- **Artifacts:** `artifacts/context/mutation_atlas.json`

### 2. Structure Module (`statebind.structure`)

**Purpose:** Build and classify EGFR conformational states from PDB structures.

- **Input:** PDB IDs or AlphaFold models, mutation context
- **Output:** Classified structures with state labels (DFG-in/out, αC-helix position), extracted pocket geometries
- **Artifacts:** `artifacts/structure/state_atlas/`, `artifacts/structure/pockets/`

### 3. Dynamics Module (`statebind.dynamics`)

**Purpose:** Predict conformational state preferences given mutation context.

- **Input:** Mutation context, structure atlas
- **Output:** State probability distribution, recommended states for design
- **Artifacts:** `artifacts/dynamics/state_predictions.json`

### 4. Generation Module (`statebind.generation`)

**Purpose:** Generate candidate molecules conditioned on state-specific pockets.

- **Input:** Pocket geometries, state context
- **Output:** Candidate molecules (SMILES), generation metadata
- **Artifacts:** `artifacts/generation/candidates/`

### 5. Ranking Module (`statebind.ranking`)

**Purpose:** Score candidates and compare state-aware vs. static baselines.

- **Input:** Candidates, pocket geometries, baseline results
- **Output:** Ranked candidate lists, comparison reports
- **Artifacts:** `artifacts/ranking/results/`, `reports/`

## Shared Utilities (`statebind.utils`)

- Configuration loading (`config.py`)
- Logging setup (`logging.py`)
- File I/O helpers (`io.py`)
- Type definitions (`types.py`)

## Configuration

All module behavior is controlled by YAML configs in `configs/`. No hard-coded paths, parameters, or thresholds in source code.

## Data Flow

```
configs/*.yaml ──→ scripts/run_*.py ──→ src/statebind/* ──→ artifacts/*
                                                          └──→ reports/*
```

## Testing Strategy

- Unit tests per module (`tests/test_<module>.py`)
- Integration tests for pipeline stages (`tests/test_pipeline.py`)
- Structure tests to verify project conventions (`tests/test_structure.py`)
