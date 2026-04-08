# StateBind: Project Overview

## What Is This?

StateBind is a computational pipeline for designing drug candidates against EGFR, the most important kinase target in lung cancer. It tests a specific scientific hypothesis:

> **Does knowing which conformational state a kinase occupies help you design better molecules than treating it as a single static structure?**

The answer so far: **it's complicated.** State-aware design produces 431 novel candidates with dramatically higher chemical diversity (0.91 vs 0.57), but scores lower on average because the scoring function penalizes molecules dissimilar from known inhibitors. The null hypothesis is formally retained — state-aware does not produce statistically superior composite scores, though it massively expands accessible chemical space.

---

## The Biology

EGFR kinase has four conformational states, defined by two structural switches:

```
                    DFG-in              DFG-out
                 ┌──────────┐       ┌──────────┐
  aC-helix in    │ Active   │       │ Intermed │    Pocket: 450-790 A^3
                 │ (1M17)   │       │ iate     │
                 └──────────┘       └──────────┘
  aC-helix out   │ Src-like │       │ Fully    │    Pocket: 520-850 A^3
                 │ inactive │       │ inactive │
                 └──────────┘       └──────────┘
```

Each state has a differently shaped binding pocket. DFG-out conformations expose a "back pocket" absent in DFG-in states. Resistance mutations (T790M, L858R, C797S, etc.) shift which states are populated. A molecule designed for the wrong pocket shape will fail.

**Static approach:** Pick one PDB structure, design molecules for one pocket, hope for the best.

**State-aware approach:** Consider all four states, design molecules for each pocket, score candidates across the ensemble.

---

## How It Works

The pipeline has 7 phases, each producing JSON artifacts consumed by the next:

```
Phase 1: Build datasets
   18 mutations, 16 PDB structures, 9 reference inhibitors
         |
Phase 2: Static baseline
   1 structure (1M17) -> 30 candidates via analog generation
         |
Phase 3: Structural atlas
   16 PDB structures -> 4 conformational state clusters (9D feature vectors)
         |
Phase 4: Context model
   Mutation features -> which conformational states are relevant
         |
Phase 5: World model
   State transition dynamics (Markov model, contrastive embeddings)
         |
Phase 6: State-conditioned generation
   4 states x 7 strategies + VAE generation -> 461 candidates
   Strategies: hinge optimization, back-pocket extension, gatekeeper
   avoidance, volume filling, covalent warhead, P-loop interaction, analogs, VAE
         |
Phase 7: Unified ranking + comparison
   Both pipelines scored by THE SAME function
   Components: similarity (0.35), druglikeness (0.30), docking (0.20), state specificity (0.15)
```

The key fairness guarantee: both pipelines are scored identically. The only axis where state-aware can win is the state_specificity component (15% weight).

---

## The ML Stack

Three neural networks, all trained on Yale Bouchet HPC (2026-04-06):

| Model | Purpose | Key Metrics | Params |
|-------|---------|------------|--------|
| **VAE v3 (SELFIES)** | Generate novel molecules conditioned on conformational state | 99.9% valid, 94.8% unique | 9.5M |
| **Affinity MPNN** | Predict binding affinity (top of 3-tier scoring cascade) | RMSE=0.72, R²=0.69, Pearson=0.83 | 12.7M |
| **Multi-task ADMET** | Predict drug safety (hERG, CYP3A4, solubility, etc.) | hERG AUROC=0.77, CYP3A4=0.73 | 187K |

Training data:
- ChEMBL EGFR compounds (10,466 with pIC50 values for MPNN)
- TDC ADMET benchmark datasets (27,698 molecules, 6 endpoints)
- ChEMBL EGFR actives (8,109 train / 2,027 val SMILES→SELFIES for VAE)

---

## Key Results (Final, Post-Training)

| Metric | Static | State-Aware | Delta |
|--------|:------:|:-----------:|:-----:|
| Candidates | 30 | 461 | +431 |
| Mean composite score | 0.5437 | 0.4378 | -0.1059 |
| Max composite score | 0.7288 | 0.7794 | +0.0506 |
| Chemical diversity | 0.5684 | 0.9056 | +0.3372 |
| Novel candidates | 0 | 431 | +431 |
| Mann-Whitney U p-value | -- | <0.001 | -- |
| Cohen's d | -- | 1.36 (static favored) | -- |
| Weight sensitivity | 56% wins | 44% wins | -- |

**Null hypothesis formally retained.** The state-aware pipeline dramatically expands chemical space (431 novel candidates, diversity 0.91) and achieves the highest individual score (0.78 vs 0.73). However, the mean score is significantly lower because VAE-generated molecules have low reference similarity (35% of score weight). The scoring function inherently penalizes novel molecules dissimilar from known inhibitors — a meaningful finding about the tension between novelty and similarity in drug design scoring.

The state-aware pipeline finds molecules the static pipeline can't: type-II inhibitors for DFG-out conformations, P-loop binders for the fully inactive state, back-pocket extensions, and 395 VAE-generated novel scaffolds.

---

## Codebase at a Glance

```
91 Python source files across 12 subpackages
49 pipeline scripts
646 tests (all passing, 6 GPU-skips on login node)
22 test files
12 YAML config files
```

**Technology:** Python 3.10+, Pydantic v2 (all data models), NumPy, pandas, PyYAML, Typer+Rich (CLI). Optional: RDKit (chemistry), PyTorch + PyG (ML), SciPy + scikit-learn (statistics), matplotlib (visualization).

**Architecture principle:** Modules communicate via JSON artifacts on disk, never via in-memory shared state. This makes the pipeline resumable and debuggable — you can inspect any intermediate result.

---

## 12 Improvement Workstreams (All Complete)

The pipeline was upgraded from SMILES string heuristics to research-grade components:

| # | Workstream | What It Added | Status |
|---|-----------|---------------|--------|
| 01 | Chemistry Foundation | RDKit fingerprints, descriptors, validation, SA scoring | Complete |
| 02 | Scoring Integration | Morgan/ECFP4 replacing n-gram Tanimoto, QED+Lipinski | Complete |
| 03 | Statistical Testing | Mann-Whitney U, bootstrap CI, Cohen's d, sensitivity analysis | Complete |
| 04 | Docking Proxy | Lightweight MLP replacing constant-0.5 stub | Complete |
| 05 | Visualization | Score distributions, radar plots, comparison figures | Complete |
| 06 | CI/CD | GitHub Actions: test matrix (3.10-3.12) + ruff linting | Complete |
| 07 | Conditional VAE | Data prep, ChEMBL EGFR data, generation integration | Complete |
| 08 | MPNN Affinity | Affinity predictor adapter, cascading fallback chain | Complete |
| 09 | ADMET Predictor | Safety filter gate, TDC data prep, multi-task adapter | Complete |
| 11 | GNINA Docking | Physics-based docking as tier 0 in scoring cascade (33 tests) | Complete |
| 12 | Pareto Optimization | Weight-free hypervolume comparison + Pareto front plots (36 tests) | Complete |
| 13 | Retrospective Validation | Time-split validation at 2010/2015 cutoffs, 10x enrichment over static (28 tests) | Complete |

---

## How to Run

```bash
# Setup
git clone https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design.git
cd EGFR_Targeted_Molecular_Design
pip install -e ".[dev]"          # Core + test deps
pip install -e ".[chemistry]"    # + RDKit
pip install -e ".[ml]"           # + PyTorch + PyG (for training)

# Run tests
pytest -v --tb=short             # 646 tests

# Run full pipeline (no GPU needed)
python scripts/build_context_dataset.py
python scripts/build_structure_dataset.py
python scripts/build_ligand_dataset.py
python scripts/run_static_baseline.py
python scripts/build_state_atlas.py
python scripts/train_context_state_model.py
python scripts/train_world_model.py
python scripts/generate_state_conditioned_candidates.py
python scripts/filter_generated_candidates.py
python scripts/rerank_candidates.py
python scripts/compare_baseline_vs_state_aware.py

# All outputs go to artifacts/
```

---

## AI Development System

The project uses a multi-agent AI development system with 5 roles:

- **Head AI** — Coordinator. Merges work, makes architectural decisions, triages ideas and suggestions.
- **Modular Agents** — Execute workstreams in isolated git worktrees.
- **Assistant AI** — Reads full project, writes briefings for Visionary.
- **Visionary AI** — Proposes bold improvement ideas (reads only briefings, never code).
- **Admin AI** — Audits documentation and infrastructure quality.

See [AI-Operations-Manual.md](AI-Operations-Manual.md) for prompts and deployment instructions.
