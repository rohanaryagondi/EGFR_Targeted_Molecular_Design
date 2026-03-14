# Phase Plan

## Phase 0: Scaffold ✅

**Goal:** Repository structure, documentation, development environment.

- [x] Directory structure
- [x] pyproject.toml with dependencies
- [x] Documentation framework
- [x] Minimal test suite
- [x] CLI entrypoint
- [x] GitHub repository

**Deliverables:** Clean repo, passing tests, installable package.

---

## Phase 1: Context & Data

**Goal:** Build EGFR mutation atlas and resistance context database.

- [ ] Curate EGFR resistance mutations from literature (COSMIC, ClinVar, published reviews)
- [ ] Define mutation data model (Pydantic schema)
- [ ] Build mutation → resistance mechanism mapping
- [ ] Create context query API (`statebind.context.query`)
- [ ] Write loader for external mutation databases
- [ ] Unit tests for context module
- [ ] Script: `scripts/build_mutation_atlas.py`
- [ ] Artifact: `artifacts/context/mutation_atlas.json`
- [ ] Phase report

**Key decisions:** Data sources, mutation classification scheme, what counts as "resistance."

---

## Phase 2: Structure Atlas

**Goal:** Classify EGFR PDB structures by conformational state.

- [ ] Download representative EGFR structures from PDB
- [ ] Implement DFG-in/out classifier (geometric criteria)
- [ ] Implement αC-helix in/out classifier
- [ ] Build state atlas with labeled structures
- [ ] Extract binding pocket geometries per state
- [ ] Visualize state distribution
- [ ] Script: `scripts/build_state_atlas.py`
- [ ] Artifact: `artifacts/structure/state_atlas/`
- [ ] Phase report

**Key decisions:** Classification thresholds, pocket extraction method, representative structure selection.

---

## Phase 3: Dynamics & State Prediction

**Goal:** Predict which conformational states are relevant given mutation context.

- [ ] Build mutation → state preference model (start with lookup table baseline)
- [ ] Implement simple ML predictor (if data supports it)
- [ ] Validate against known mutation–state associations
- [ ] Script: `scripts/predict_states.py`
- [ ] Phase report

**Key decisions:** Model complexity, training data, validation strategy.

---

## Phase 4: Molecular Generation

**Goal:** Generate molecules conditioned on state-specific pockets.

- [ ] Implement pocket-conditioned generation (fragment-based or SMILES-based)
- [ ] Static baseline: generate against single best structure
- [ ] State-aware: generate against predicted state ensemble
- [ ] Script: `scripts/generate_candidates.py`
- [ ] Phase report

**Key decisions:** Generation method, pocket representation, diversity filters.

---

## Phase 5: Ranking & Benchmarking

**Goal:** Score and compare state-aware vs. static approaches.

- [ ] Implement scoring functions (docking proxy, shape complementarity)
- [ ] Run baseline comparison
- [ ] Statistical analysis of results
- [ ] Script: `scripts/rank_candidates.py`
- [ ] Phase report

**Key decisions:** Scoring method, statistical tests, what constitutes "better."

---

## Phase 6: Integration & Demo

**Goal:** End-to-end pipeline, polished artifacts, final report.

- [ ] End-to-end pipeline script
- [ ] Demo notebook with visualizations
- [ ] Final report with figures
- [ ] README polish
- [ ] Repository cleanup
