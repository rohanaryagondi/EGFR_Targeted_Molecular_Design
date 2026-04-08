# StateBind Project Briefing

**Prepared for:** IdeationDept specialist agents
**Date:** 2026-04-08
**Version:** 1.0

This document is embedded in every specialist agent's prompt by the orchestrator. It
provides the full project context needed for ideation -- you do not need to read the
codebase yourself. Focus your time on **internet research and idea generation**.

---

## 1. Project Thesis

StateBind tests whether **conformational state-aware molecular design outperforms
static single-structure design** for EGFR-targeted small molecules.

EGFR (Epidermal Growth Factor Receptor) is a kinase central to many cancers. Its
kinase domain adopts 4 conformational states based on two structural switches:

| State | DFG Motif | alphaC-Helix | Biological Role |
|-------|-----------|-------------|-----------------|
| DFGin/aCin | In | In | Active -- catalytically competent |
| DFGin/aCout | In | Out | Src-like inactive -- helix rotated out |
| DFGout/aCin | Out | In | Intermediate -- unusual, transient |
| DFGout/aCout | Out | Out | Fully inactive -- deepest pocket |

Each state presents a different binding pocket (estimated 450-850 cubic angstroms).
Most computational drug design ignores this and uses one crystal structure. StateBind
asks: what if we design molecules with explicit awareness of which state they target?

---

## 2. The Two Pipelines

### Static Baseline
- Single crystal structure: PDB 1M17 (active-state EGFR)
- One pocket definition, no state awareness
- 30 candidates via string-modification strategies

### State-Aware Pipeline
- Full 4-state conformational atlas
- Per-state pocket descriptors
- 461 candidates: 36 template + 395 VAE-generated + 30 shared
- Each candidate tagged with which conformational states it targets

### Fair Comparison
Both pipelines scored by the SAME unified function with identical weights:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Reference similarity | 0.35 | Morgan/ECFP4 Tanimoto to erlotinib, gefitinib, osimertinib |
| Drug-likeness | 0.30 | QED (50%) + Lipinski (25%) + SA score (25%) |
| Docking proxy | 0.20 | 4-tier cascade: GNINA > MPNN > DockingProxy MLP > 0.5 stub |
| State specificity | 0.15 | Geometric decay: 1 state=1.0, 2=0.5, 3=0.25, 4=0.0 |

State specificity is the ONLY axis where state-aware can outperform static. For static,
this is always 0.0. The comparison is conservative: 85% of weight is state-agnostic.

---

## 3. Key Results

### Head-to-Head Comparison

| Metric | Static | State-Aware | Winner |
|--------|--------|-------------|--------|
| Mean unified score | 0.5437 | 0.4378 | Static (+0.1059) |
| Max score | 0.7288 | 0.7794 | State-aware |
| Candidate count | 30 | 461 | State-aware (15x) |
| Chemical diversity | 0.5684 | 0.9056 | State-aware (+59%) |
| Novel molecules | 0 | 431 | State-aware |
| Mann-Whitney U | p < 0.001, Cohen's d = 1.36 favoring static | | |
| Weight sensitivity | 56% random weights favor static, 44% favor state-aware | | |

**Null hypothesis formally retained on mean score.** Static wins on the scoring
function because its 30 candidates are close modifications of known drugs (high
reference similarity at 35% weight).

### Retrospective Time-Split Validation (THE STRONGEST RESULT)

When trained only on data available before a cutoff year, does the pipeline identify
drugs approved after the cutoff?

| Cutoff | State-Aware EF@10 | Static EF@10 | Ratio |
|--------|-------------------|--------------|-------|
| 2010 | 4.95 | 0.47 | 10.5x |
| 2015 | 7.72 | 0.79 | 9.8x |

All held-out drugs found: 5/5 (pre-2010), 3/3 (pre-2015). State-aware novelty: 0.99.

**Why state-aware wins here but loses on mean score:** The reference similarity
component (35% weight) penalizes diverse VAE-generated molecules. But among those
diverse candidates are molecules resembling future drugs -- needles in a haystack
that the enrichment factor detects. The scoring function rewards looking like existing
drugs; the enrichment metric rewards placing future drugs near the top.

This 10x enrichment is the project's strongest result and the foundation of any
publication narrative.

---

## 4. Architecture Overview

### 12 Subpackages (sequential, acyclic pipeline)

```
data/ + utils/ + chemistry/   Infrastructure (always available)
       |
  processing/                 Phase 1: Raw data -> validated datasets
       |
  baselines/                  Phase 2: Static single-structure pipeline
  structure/                  Phase 3: Conformational state atlas (4 states, 9D features)
  context/                    Phase 4: Mutation-to-state prediction
  dynamics/                   Phase 5: State transition world model
       |
  ml/                         VAE, MPNN, ADMET (requires PyTorch)
       |
  generation/                 Phase 6: State-conditioned candidate generation
       |
  ranking/                    Phase 7a: Unified scoring + Pareto optimization
       |
  evaluation/                 Phase 7b: Head-to-head comparison + retrospective
```

Modules communicate via JSON artifacts on disk. No in-memory coupling. Every artifact
has `generated_at` timestamp and `notes` field.

### Key Design Principles
- Acyclic dependencies (imports flow strictly downward)
- Optional everything (torch, RDKit, scipy, GNINA all have fallbacks)
- Graceful degradation (GNINA -> MPNN -> proxy -> stub for docking)
- Pydantic at boundaries, dataclasses internally
- Config-driven (12 YAML files, zero hard-coded parameters)
- Environment-aware (GPU guard for GNINA, checkpoint detection for MPNN)

---

## 5. ML Models

### Conditional SELFIES VAE (v3)
- **Purpose**: Generate novel molecules conditioned on conformational state
- **Architecture**: Bidirectional GRU encoder/decoder, latent bottleneck (z=64),
  state conditioning via one-hot vector concatenated at every timestep
- **Key property**: Same latent z decoded with different state vectors -> different
  molecules. This is how state conditioning works.
- **SELFIES**: Bracket-delimited encoding that guarantees valid molecules by
  construction (vs raw SMILES which produced 0% validity on small datasets)
- **Stats**: 9.5M params, 300 epochs on H200, val_recon=2.26
- **Generation**: 999/1000 valid (99.9%), 948 unique (94.8%), 395 used in pipeline
- **Pre-cutoff versions**: pre-2010 (987 unique) and pre-2015 (968 unique) trained
  for retrospective validation

### Affinity MPNN
- **Purpose**: Predict pIC50 binding affinity for EGFR. Tier 1 in docking cascade.
- **Architecture**: NNConv message-passing GNN (3 layers, hidden=128), residual
  connections, batch norm, mean+max pooling readout, 2-layer MLP head
- **Input**: Molecular graph (atoms=35D features, bonds=11D features)
- **Stats**: 12.7M params, RMSE=0.7182, R^2=0.6863, Pearson=0.8323
- **Training data**: 10,466 ChEMBL EGFR compounds (pIC50 4.0-11.0)
- **Score normalization**: sigmoid((pIC50 - 5) / 2) maps to [0, 1]
- **Pre-cutoff versions**: pre-2010 (2,974 compounds, R^2=0.717) and pre-2015
  (4,852 compounds, R^2=0.690)

### Multi-task ADMET
- **Purpose**: Predict 6 drug safety/PK endpoints simultaneously (informational only)
- **Architecture**: GIN backbone + 6 task-specific 2-layer MLP heads
- **Endpoints**: Caco-2, hERG (1.5x loss weight), CYP3A4, hepatic clearance,
  lipophilicity, aqueous solubility
- **Stats**: 187K params, hERG AUROC=0.7745, CYP3A4 AUROC=0.7323
- **Training data**: 27,698 molecules from TDC benchmarks
- **Critical issue**: Hard filtering rejects ALL kinase inhibitors on hERG -- this
  is a known class liability, not a model failure. Used informational only.

---

## 6. Docking Infrastructure

### GNINA (Tier 0 -- Physics-Based)
- GNINA v1.1 binary (293MB, CUDA), Vina scoring + CNN binding prediction
- 4 state-specific EGFR receptors prepared (PDBQT format):
  - 1M17 (DFGin/aCin), 2GS7 (DFGin/aCout), 3W2R (DFGout/aCin), 4ZAU (DFGout/aCout)
- Validation: known binders -7.32 kcal/mol vs non-binders -4.16 (delta -3.16)
- Score normalization: sigmoid(-vina_score / 3) maps kcal/mol to [0, 1]
- GPU-only (CUDA required), ~minutes per molecule
- GNINA v1.3.2 needs GLIBC 2.29; cluster has 2.28 -- stuck on v1.1

### Docking Cascade
| Tier | Method | Requirement | Quality |
|------|--------|-------------|---------|
| 0 | GNINA physics-based | GPU + binary | Physics-based, validated |
| 1 | MPNN learned proxy | Checkpoint + PyTorch | RMSE=0.72, R^2=0.69 |
| 2 | DockingProxy MLP | RDKit | Toy model, 34 training molecules |
| 3 | Constant 0.5 | Always | Zero discriminative power |

---

## 7. Scoring System Details

### Unified Scoring (used for all comparisons)
- 4 components, weights must sum to 1.0 (enforced at runtime)
- Reference similarity: Max Morgan Tanimoto to {erlotinib, gefitinib, osimertinib}
  - Falls back to SMILES 3-gram Tanimoto without RDKit
- Drug-likeness: QED(0.5) + Lipinski(0.25) + SA(0.25)
  - Falls back to heuristic linear scoring without RDKit
- Docking: 4-tier cascade (see above)
- State specificity: Geometric decay by number of states (1->1.0, 4->0.0)
  - Static baseline always gets 0.0 (no state info)

### Pareto Multi-Objective Analysis
- Non-dominated sorting on raw component scores (no weight assumptions)
- Hypervolume via pymoo (or numpy fallback)
- Crowding distance for diversity along Pareto front
- Weight-free comparison: which pipeline explores more objective space?

### Baseline Scoring (standalone, different weights)
- 3 components only (no state specificity): 0.4/0.3/0.3
- Used for Phase 2 standalone runs only, NOT for the head-to-head comparison

---

## 8. Evaluation Framework

The comparison computes metrics at multiple levels:
1. Overlap analysis (SMILES-level: shared, unique, Jaccard)
2. Diversity comparison (mean pairwise Tanimoto distance)
3. Score distributions (mean, median, std, min, max with deltas)
4. Top-K dominance (which pipeline owns top positions)
5. Novelty detection (candidates unique to state-aware)
6. Statistical testing (Mann-Whitney U, bootstrap CI, Cohen's d)
7. Weight sensitivity (100 random Dirichlet weight configs)
8. Pareto analysis (hypervolume ratio, dominance fraction)
9. Retrospective validation (enrichment factors at time-split cutoffs)

---

## 9. Infrastructure and Compute

### Yale Bouchet HPC Cluster
- **GPUs available**: H200 (8/node), RTX 5000 Ada (4/node), RTX Pro 6000 Blackwell
  (8/node), B200 (8/node)
- **Account**: pi_mg269, priority queue available via prio_gerstein
- **Partitions**: day (24h), week (7d), gpu, gpu_h200, gpu_devel, scavenge_gpu
- **Software**: Python 3.12, miniconda, SLURM scheduler
- **Storage**: Home directory (quota), scratch at /nfs/roberts/scratch/pi_mg269/rag88/

### Software Stack
- Python >=3.10, PyTorch, PyTorch Geometric
- RDKit for cheminformatics
- GNINA v1.1 for physics-based docking
- Core: numpy, pandas, pyyaml, pydantic, typer, rich
- Optional: scipy, scikit-learn, pymoo

---

## 10. Codebase Stats

| Metric | Value |
|--------|-------|
| Python source files | 91 |
| Subpackages | 12 |
| Test files | 22 |
| Tests passing | 646 |
| Pipeline scripts | 49 |
| YAML configs | 12 |
| Workstreams completed | 12/12 |
| Lines of source code | ~15,000+ |

---

## 11. Known Limitations (Opportunity Areas)

### Scoring Limitations
1. **Docking is environment-dependent** -- GNINA on GPU gives physics scores; login
   node gives MPNN proxy scores. Different scales despite normalization.
2. **Only 3 reference molecules for 35% of score** -- Rewards similarity to existing
   drugs, penalizes novelty. Primary driver of static baseline's mean-score advantage.
3. **ADMET is informational only** -- Hard filtering rejects all kinase inhibitors on
   hERG. Not integrated into scoring weights.
4. **Fixed weighted sum** -- Pareto exists but weighted sum is primary ranking. Weights
   are human-chosen, not optimized. 44/56 sensitivity split.
5. **GNINA is slow** -- Minutes per molecule on GPU. 461 candidates x 4 states = hours.

### Scientific Limitations
1. **No experimental validation** -- Zero wet-lab data. All scores are computational.
2. **4 discrete states** -- Real kinase dynamics are continuous.
3. **All 17 mutations map to one state** -- Context model is uninformative.
4. **No MD simulations** -- Static crystal structures only.
5. **No selectivity** -- Only scores binding to EGFR, not off-target kinases.

### ML Limitations
1. **No pre-training** -- Models trained from scratch on moderate datasets.
2. **Retrospective validation has small N** -- Only 3-5 held-out drugs (all that exist).
3. **No uncertainty quantification** -- Point predictions only.
4. **VAE generates 1D (SMILES/SELFIES)** -- No 3D pocket awareness.
5. **No active learning** -- One-shot pipeline, no iterative refinement.

### Pipeline Limitations
1. **No retrosynthetic analysis** -- SA score only, no actual synthesis routes.
2. **No protein-ligand interaction fingerprints** -- Scores molecules in isolation.
3. **No water/solvent modeling** -- Gas-phase binding assumption.

---

## 12. What Peer Reviewers Would Attack

1. "Where is the experimental validation?"
2. "Why only 3 reference molecules for 35% of the score?"
3. "Enrichment factors are based on 3-5 drugs -- confidence intervals?"
4. "4 discrete states is a gross oversimplification"
5. "State-aware advantage is only 15% of the score"
6. "No comparison to existing generative models (REINVENT, GraphAF, MolGPT)"

---

## 13. What Drug Discovery Practitioners Would Find Naive

1. No lead optimization cycle (one-shot, no design-synthesize-test-redesign)
2. No ADMET in scoring (safety is a post-hoc annotation)
3. No intellectual property analysis
4. No formulation/delivery considerations
5. Pocket shape not exploited in generation (1D strings, not 3D structures)

---

## 14. Existing Vision System Ideas (Prior Art)

The Vision System proposed 12 ideas. 3 were accepted and implemented. 9 remain
deferred. Do NOT re-propose these without new evidence. DO build on them.

### Implemented (as workstreams 11, 12, 13)
- **005: GNINA Physics-Informed Docking** -- Now tier 0 in cascade, validated on GPU
- **008: Pareto Multi-Objective Optimization** -- Hypervolume comparison implemented
- **009: Retrospective Time-Split Validation** -- 10x enrichment result

### Deferred (available for revisiting with new research)
- **001: Continuous Conformational Conditioning** (P0) -- Replace 4 discrete states
  with continuous protein language model embeddings. Deferred because null result isn't
  driven by discretization.
- **002: 3D Pocket-Conditioned Diffusion** (P1) -- Replace SMILES VAE with DiffSBDD/
  TargetDiff/Pocket2Mol. Deferred due to complexity.
- **003: Kinome-Wide Selectivity Panel** (P0) -- Multi-kinase MPNN + cross-docking for
  selectivity. Deferred to focus on single-target validation first.
- **004: Ensemble Uncertainty + Active Learning** (P1) -- Model ensembles, MC dropout,
  active learning loop. Deferred due to 5-10x GPU cost.
- **006: Learned Chemical Similarity** (P1) -- Replace Morgan fingerprints with
  learned activity-cliff-aware embeddings. Deferred to avoid scope creep.
- **007: Retrosynthetic Feasibility Gate** (P2) -- ASKCOS/IBM RXN integration for
  synthesis route analysis. Deferred as lower priority.
- **010: Self-Supervised GNN Pre-Training** (P1) -- Pre-train MPNN on millions of
  compounds before fine-tuning. Deferred because models meet metrics.
- **011: Water Thermodynamics** (P2) -- WaterMap-style solvation analysis. Deferred
  as incremental improvement.
- **012: RL for Molecular Optimization** (P2) -- REINVENT-style RL loop for
  iterative molecular improvement. Deferred due to complexity.

---

## 15. The Publication Question

The project needs to answer: **What is the paper?**

Options range from:
- "Method paper" -- Here is a state-aware molecular design framework, here are the results
- "Benchmark paper" -- Rigorous comparison of state-aware vs static with multiple evaluation methods
- "Biological insight paper" -- What conformational awareness reveals about EGFR drug design
- "ML paper" -- Novel state-conditioned generation with retrospective validation

The 10x enrichment result is the headline, but a single result on a single target with
3-5 held-out drugs needs strengthening. The IdeationDept's job is to identify the
highest-impact ways to strengthen this result and frame the publication narrative.

---

## 16. What the Project Needs Next

The engineering phase is done. The question is now about **scientific credibility**
and **publication readiness**. The highest-impact directions are:

1. **Strengthen the 10x enrichment claim** -- More targets, more drugs, confidence intervals
2. **Address the #1 reviewer concern** -- Experimental validation or strong computational surrogates
3. **Expand beyond EGFR** -- Multi-kinase generalization would transform a single-target demo into a general method
4. **Modernize the ML stack** -- Foundation models, 3D generation, better baselines
5. **Close the scoring gap** -- Why does state-aware lose on mean score? Can we reframe or fix?
6. **Build the narrative** -- What is the paper's main claim, and what evidence makes it bulletproof?

---

## 17. Key File References

For agents who need to check specific implementation details:

| What | Where |
|------|-------|
| Unified scoring function | `src/statebind/ranking/scoring.py` |
| Scoring weights | `ranking/scoring.py:125-130` |
| Reference binders (3 SMILES) | `baselines/scoring.py:57-66` |
| Conformational states enum | `processing/models.py:51-57` |
| VAE architecture | `ml/vae.py` |
| MPNN architecture | `ml/mpnn.py` |
| ADMET architecture | `ml/admet.py` |
| GNINA wrapper | `chemistry/docking.py` |
| Retrospective validation | `evaluation/retrospective.py` |
| Pareto optimization | `ranking/pareto.py` |
| Comparison engine | `evaluation/comparison.py` |
| EGFR drug approvals | `evaluation/retrospective.py` (EGFR_DRUG_APPROVALS constant) |
| All configs | `configs/*.yaml` (12 files) |
| Vision ideas | `vision/ideas/001-012*.md` |
| Project rules | `CLAUDE.md`, `CRITICAL.md` |
