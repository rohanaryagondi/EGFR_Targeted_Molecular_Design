# StateBind

[![CI](https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design/actions/workflows/ci.yml/badge.svg)](https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design/actions/workflows/ci.yml)
![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Conformational State-Aware Molecular Design for EGFR-Targeted Drug Discovery**

> Does knowing which conformational state a kinase target occupies help you design better molecules than treating it as a single static structure?

StateBind is a computational pipeline that answers this question for EGFR, the most targeted kinase in lung cancer. It maps resistance mutations to conformational states, generates pocket-specific candidate molecules for each state, and benchmarks state-aware design against a conventional single-structure baseline under identical scoring.

---

## Main Result

| Metric | Static Baseline | State-Aware | Delta |
|--------|:-:|:-:|:-:|
| Unique candidates | 30 | 79 | **+49** |
| Chemical diversity | 0.526 | 0.561 | **+0.035** |
| Mean composite score | 0.584 | 0.604 | **+0.020** |
| Global top-10 share | 5/10 | 5/10 | 0 |
| Novel candidates | 0 | 49 | **+49** |

**Verdict:** State-aware design produces 49 chemically novel candidates inaccessible to a static pipeline — back-pocket extensions for DFG-out conformations, P-loop binders, and type-II inhibitor scaffolds — with higher diversity and competitive scores. The advantage is real but moderate. Without real docking validation, binding affinity claims are not supported. See [reports/phase7_comparison.md](reports/phase7_comparison.md) for the full analysis.

---

## Architecture

```
  Mutation context          Structural data            Literature
       │                         │                        │
       ▼                         ▼                        ▼
┌─────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   Context    │  │   Structure Atlas     │  │   Dynamics / World   │
│   Module     │  │   (4 EGFR states)    │  │   Model              │
│              │  │                      │  │                      │
│ 18 mutations │  │ 16 PDB structures    │  │ Markov transitions   │
│ 7 mechanisms │  │ 9-D feature vectors  │  │ 4-D state embeddings │
│ 33 features  │  │ 4 state clusters     │  │ Stationary dist.     │
└──────┬───────┘  └──────────┬───────────┘  └──────────┬───────────┘
       │                     │                         │
       └─────────┬───────────┘─────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Generation Module                              │
│                                                                  │
│  Static baseline:  1 structure × 1 pocket → 30 candidates       │
│  State-aware:      4 structures × 4 pockets → 79 candidates     │
│                    (7 strategies: hinge opt, back-pocket ext,    │
│                     gatekeeper avoidance, volume filling,        │
│                     covalent warhead, P-loop interaction, analog) │
└──────────────────────────────┬───────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│               Ranking & Evaluation Module                        │
│                                                                  │
│  Unified scoring: same function for both pipelines               │
│  Comparison: overlap, diversity, score distributions, rank shifts│
│  Verdict: qualified advantage for state-aware design             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Modules

| Module | Location | Purpose |
|--------|----------|---------|
| **Data & Processing** | `src/statebind/data/`, `processing/` | Source registry, manifests, provenance-tracked dataset construction |
| **Baselines** | `src/statebind/baselines/` | Static single-structure pipeline (1M17, active conformation) |
| **Structure Atlas** | `src/statebind/structure/` | Conformational state classification, 9-D feature vectors, clustering |
| **Context Model** | `src/statebind/context/` | Mutation-to-state prediction (29 mutation + 4 pathway features) |
| **World Model** | `src/statebind/dynamics/` | Markov state transitions, contrastive embeddings |
| **Generation** | `src/statebind/generation/` | Pocket-conditioned candidate generation with state-specific strategies |
| **Ranking** | `src/statebind/ranking/` | Unified scoring, rank aggregation, merge deduplication |
| **Evaluation** | `src/statebind/evaluation/` | Head-to-head comparison: overlap, novelty, diversity, figures |

---

## Benchmark Setup

**Target:** EGFR kinase domain (4 conformational states: DFGin/out × αC-helix in/out)

**Dataset:**
- 18 clinically relevant mutations (T790M, L858R, C797S, G719S, L861Q, ...)
- 16 PDB structures across 4 states
- 9 approved/clinical EGFR inhibitors as reference compounds

**Comparison:**
- **Static baseline:** 1 structure (1M17), 1 pocket, halogen/methyl analogs only
- **State-aware:** 4 structures, 4 state-specific pockets, 7 generation strategies

**Scoring** (applied identically to both pipelines):
```
composite = 0.35 × reference_similarity
          + 0.30 × druglikeness
          + 0.20 × docking_proxy     ← STUB (constant 0.5)
          + 0.15 × state_specificity  ← 0 for static baseline
```

---

## Setup

```bash
git clone https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design.git
cd EGFR_Targeted_Molecular_Design

pip install -e ".[dev]"

pytest                    # 548 tests, all passing
statebind --help          # CLI entry point
```

**Requirements:** Python ≥ 3.10. Core dependencies: numpy, pandas, pydantic, typer, rich. No GPU required.

---

## Running Each Phase

```bash
# Phase 1: Build benchmark datasets
python scripts/build_context_dataset.py
python scripts/build_structure_dataset.py
python scripts/build_ligand_dataset.py

# Phase 2: Static baseline pipeline
python scripts/run_static_baseline.py

# Phase 3: Structural state atlas
python scripts/build_state_atlas.py

# Phase 4: Context-to-state prediction
python scripts/train_context_state_model.py

# Phase 5: World model (state transitions)
python scripts/train_world_model.py

# Phase 6: State-conditioned generation
python scripts/generate_state_conditioned_candidates.py
python scripts/filter_generated_candidates.py

# Phase 7: Unified ranking and comparison
python scripts/rerank_candidates.py
python scripts/compare_baseline_vs_state_aware.py
python scripts/report_comparative_results.py
```

All scripts are deterministic and produce artifacts under `artifacts/`.

---

## Key Results

### Novel Chemistry by Strategy

The state-aware pipeline produces 49 candidates absent from the static baseline:

| Strategy | Novel Candidates | Rationale |
|----------|:--:|-----------|
| Back-pocket extension | 18 | CF3 tails and amide linkers for DFG-out back pocket |
| Volume filling | 12 | Cyclohexyl/naphthyl groups for large inactive pockets |
| P-loop interaction | 5 | Sulfonamide groups for folded P-loop in DFGout_aCout |
| Hinge optimization | 5 | Pyridyl swaps for improved hinge H-bonds |
| Covalent warhead | 4 | Acrylamide warheads targeting C797 |
| Gatekeeper avoiding | 3 | Smaller substituents for T790M clearance |

### Global Top-10 Candidates

| Rank | Pipeline | Score | Strategy | Target State |
|:--:|----------|:--:|----------|-------------|
| 1 | State-aware | 0.796 | P-loop interaction | DFGout_aCout |
| 2 | State-aware | 0.773 | Back-pocket extension | DFGout_aCin |
| 3 | State-aware | 0.770 | P-loop interaction | DFGout_aCout |
| 4 | State-aware | 0.751 | Volume filling | DFGin_aCout |
| 5 | Static | 0.750 | Reference analog | — |
| 6–10 | Mixed | 0.740–0.750 | Various | Various |

### What the Pipeline Learned

- **DFGin_aCin** (active): Compact pocket (450 Å³). Prioritize hinge H-bonds, avoid gatekeeper clash.
- **DFGin_aCout** (Src-like): Moderate pocket (520 Å³). Fill extra space from αC rotation.
- **DFGout_aCin**: Large pocket (790 Å³) with exposed back pocket. Type-II inhibitor opportunity.
- **DFGout_aCout**: Largest pocket (850 Å³), folded P-loop. Design for P-loop contacts.

---

## Limitations

1. **Docking is a stub.** The docking_proxy returns a constant. Without AutoDock Vina, GNINA, or FEP+, binding affinity claims are unsupported.
2. **SMILES-level chemistry.** All modifications are string-level. No 3D pose generation or synthetic accessibility scoring.
3. **Scoring bias.** The state_specificity component (weight 0.15) is structurally zero for the baseline, giving state-aware candidates a built-in advantage on that axis.
4. **Small benchmark.** 18 mutations, 16 structures, ~80 candidates. Not a large-scale validation.
5. **No experimental validation.** All results are computational. No IC50, no selectivity assays.
6. **Single kinase family.** Results are specific to EGFR. Generalization to other targets is untested.

---

## Future Work

- Replace docking stub with AutoDock Vina or GNINA scoring
- Add ECFP4/Morgan fingerprint similarity (replacing SMILES n-grams)
- Integrate synthetic accessibility scoring (SA score, ASKCOS)
- Expand to additional kinase families (ABL, ALK, BRAF)
- Add MD-derived transition matrices (replacing literature curation)
- Validate top candidates with FEP+ binding free energy calculations

---

## Development Workstreams

Six independent improvement workstreams are defined in [`workstreams/`](workstreams/README.md), designed for parallel development by multiple AI agents or contributors.

| # | Workstream | Impact | Dependencies |
|---|-----------|--------|-------------|
| 01 | Chemistry Foundation (RDKit) | High | None |
| 02 | Scoring Integration | High | 01 |
| 03 | Statistical Testing (scipy) | High | None |
| 04 | Docking Proxy (learned model) | Critical | 01 |
| 05 | Visualization (matplotlib) | Moderate | 03 |
| 06 | CI/CD (GitHub Actions) | Moderate | None |

Workstreams 01, 03, and 06 can start in parallel. See [`workstreams/INTERFACES.md`](workstreams/INTERFACES.md) for cross-workstream contracts. Each `src/statebind/*/README.md` documents the module's API and dependencies. AI-specific guidance is in [`CLAUDE.md`](CLAUDE.md).

---

## Project Structure

```
src/statebind/           # Main package (12 submodules, 84 Python files)
scripts/                 # 37 runnable pipeline scripts
tests/                   # 19 test files, 548 tests
docs/                    # 20 documentation files
reports/                 # 7 phase reports + final report
configs/                 # YAML configuration files
artifacts/               # Pipeline outputs (generated, gitignored)
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [Project Charter](docs/PROJECT_CHARTER.md) | Scope, hypotheses, success criteria |
| [Architecture](docs/ARCHITECTURE.md) | System design, module contracts |
| [Evaluation Framework](docs/EVALUATION.md) | Comparison methodology, fairness rules |
| [Results Summary](docs/RESULTS_SUMMARY.md) | Main findings with key tables |
| [Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md) | Module-by-module design decisions |
| [Limitations](docs/LIMITATIONS.md) | Complete accounting of what the project cannot claim |
| [Future Work](docs/FUTURE_WORK.md) | Concrete next steps with effort estimates |
| [Audit Report](docs/AUDIT_REPORT.md) | Full code and documentation audit findings |
| [Recruiter Summary](docs/RECRUITER_SUMMARY.md) | Non-technical project overview |
| [Benchmark Dataset](docs/BENCHMARK_DATASET_CARD.md) | Data composition and provenance |
| [Runbook](docs/RUNBOOK.md) | Step-by-step execution guide |

---

## Test Coverage

```
548 tests across 19 modules — all passing
├── test_imports.py          16 tests   Module import verification
├── test_baselines.py        32 tests   Static baseline pipeline
├── test_structure.py        31 tests   Structural state atlas
├── test_context.py          52 tests   Context-to-state prediction
├── test_dynamics.py         50 tests   World model / dynamics
├── test_generation.py       40 tests   State-conditioned generation
├── test_ranking.py          36 tests   Unified ranking pipeline
├── test_evaluation.py       25 tests   Comparative evaluation
├── test_processing.py       33 tests   Data processing
├── test_data.py             24 tests   Data layer
├── test_utils.py             5 tests   Utilities
├── test_cli.py               7 tests   CLI interface
└── test_baselines.py         8 tests   Baseline models
```

---

## License

MIT
