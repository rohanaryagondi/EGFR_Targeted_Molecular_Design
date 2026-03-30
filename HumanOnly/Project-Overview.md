# StateBind: Project Overview

## What Is This?

StateBind is a computational pipeline for designing drug candidates against EGFR, the most important kinase target in lung cancer. It tests a specific scientific hypothesis:

> **Does knowing which conformational state a kinase occupies help you design better molecules than treating it as a single static structure?**

The answer so far: **yes, with caveats.** State-aware design produces 49 chemically novel candidates that a static pipeline can't access, with higher chemical diversity — but the advantage is moderate and unvalidated without real docking or experimental data.

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
   4 states x 7 strategies -> 79 candidates
   Strategies: hinge optimization, back-pocket extension, gatekeeper
   avoidance, volume filling, covalent warhead, P-loop interaction, analogs
         |
Phase 7: Unified ranking + comparison
   Both pipelines scored by THE SAME function
   Components: similarity (0.35), druglikeness (0.30), docking (0.20), state specificity (0.15)
```

The key fairness guarantee: both pipelines are scored identically. The only axis where state-aware can win is the state_specificity component (15% weight).

---

## The ML Stack

Three neural networks are written but need GPU training:

| Model | Purpose | Input | Output | Training Time |
|-------|---------|-------|--------|--------------|
| **Conditional SMILES VAE** | Generate novel molecules conditioned on conformational state | Tokenized SMILES + state one-hot | Novel SMILES per state | 2-4 hours |
| **Affinity MPNN** | Predict binding affinity (replaces constant-0.5 docking stub) | Molecular graph | pIC50 value | 1-2 hours |
| **Multi-task ADMET** | Predict drug safety (hERG, CYP3A4, solubility, etc.) | Molecular graph | 6 ADMET scores | 2-3 hours |

Training data is prepared:
- ChEMBL EGFR compounds (1,678 with pIC50 values)
- TDC ADMET benchmark datasets
- SMILES training set for VAE

---

## Key Results (Current, Pre-Training)

| Metric | Static | State-Aware | Delta |
|--------|:------:|:-----------:|:-----:|
| Unique candidates | 30 | 79 | +49 |
| Chemical diversity | 0.526 | 0.561 | +0.035 |
| Mean composite score | 0.584 | 0.604 | +0.020 |
| Novel candidates | 0 | 49 | +49 |

The state-aware pipeline finds molecules the static pipeline can't: type-II inhibitors for DFG-out conformations, P-loop binders for the fully inactive state, and back-pocket extensions using CF3 tails and amide linkers.

**But:** The docking component is a stub (constant 0.5), so 20% of the scoring function has zero discriminative power. The real comparison happens after MPNN training.

---

## Codebase at a Glance

```
84 Python source files across 12 subpackages
37 pipeline scripts
548 tests (all passing)
19 test files
6 YAML config files
```

**Technology:** Python 3.10+, Pydantic v2 (all data models), NumPy, pandas, PyYAML, Typer+Rich (CLI). Optional: RDKit (chemistry), PyTorch + PyG (ML), SciPy + scikit-learn (statistics), matplotlib (visualization).

**Architecture principle:** Modules communicate via JSON artifacts on disk, never via in-memory shared state. This makes the pipeline resumable and debuggable — you can inspect any intermediate result.

---

## 9 Improvement Workstreams (All Complete)

The pipeline was upgraded from SMILES string heuristics to research-grade components:

| # | Workstream | What It Added |
|---|-----------|---------------|
| 01 | Chemistry Foundation | RDKit fingerprints, descriptors, validation, SA scoring |
| 02 | Scoring Integration | Morgan/ECFP4 replacing n-gram Tanimoto, QED+Lipinski |
| 03 | Statistical Testing | Mann-Whitney U, bootstrap CI, Cohen's d, sensitivity analysis |
| 04 | Docking Proxy | Lightweight MLP replacing constant-0.5 stub |
| 05 | Visualization | Score distributions, radar plots, comparison figures |
| 06 | CI/CD | GitHub Actions: test matrix (3.10-3.12) + ruff linting |
| 07 | Conditional VAE | Data prep, ChEMBL EGFR data, generation integration |
| 08 | MPNN Affinity | Affinity predictor adapter, cascading fallback chain |
| 09 | ADMET Predictor | Safety filter gate, TDC data prep, multi-task adapter |

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
pytest -v --tb=short             # 548 tests

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
