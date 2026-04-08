# Deep Research Briefing: Techniques & Methods for Publication-Grade State-Aware Drug Design

**Agent mission:** Survey the cutting-edge computational drug design techniques that
StateBind should adopt, integrate, or benchmark against to achieve publication at a
top venue (Nature Computational Science, JCIM, Nature Methods, or similar).

**Read only this file.** It contains all the project context you need.

---

## 1. What StateBind Is

StateBind is a computational biology pipeline that tests whether **conformational
state-aware molecular design outperforms static single-structure design** for
EGFR-targeted small molecules.

EGFR (Epidermal Growth Factor Receptor) is a kinase with 4 conformational states
defined by two structural switches:

| State | DFG motif | alphaC helix | Character |
|-------|----------|-------------|-----------|
| DFGin/aCin | In (active) | In (active) | Fully active kinase |
| DFGin/aCout | In | Out (inactive) | Src-like inactive |
| DFGout/aCin | Out (inactive) | In | Intermediate, transient |
| DFGout/aCout | Out | Out | Fully inactive, deepest pocket |

Each state presents a different binding pocket geometry (volumes range 450-850 cubic
angstroms). The hypothesis is that designing molecules aware of these 4 states
produces better drug candidates than designing against a single static structure.

### The Two Pipelines Compared

1. **Static baseline:** Uses a single PDB structure (1M17, active state), one pocket.
   Produces 30 candidates via template string modification.

2. **State-aware pipeline:** Uses 4-state atlas, generates candidates conditioned on
   each state. Produces 461 candidates (36 template + 395 VAE-generated + 30 shared).

Both pipelines are scored by the **same unified scoring function** for fair comparison.

### Unified Scoring Function

| Component | Weight | Method |
|-----------|--------|--------|
| Reference similarity | 0.35 | Morgan fingerprint (ECFP4, radius 2, 2048 bits) Tanimoto vs 3 known drugs (erlotinib, gefitinib, osimertinib). Max similarity used. |
| Drug-likeness | 0.30 | QED (50%) + Lipinski violations (25%) + SA score (25%). Composite with heuristic fallback. |
| Docking proxy | 0.20 | 4-tier cascade: GNINA physics-based (GPU) -> MPNN learned affinity -> MLP proxy -> constant 0.5 stub |
| State specificity | 0.15 | Geometric decay: 1 state = 1.0, 2 = 0.5, 3 = 0.25, 4 = 0.0. Static always 0.0. |

Pareto multi-objective optimization (hypervolume, non-dominated sorting, crowding
distance) runs alongside the weighted sum as a weight-free comparison.

### ML Models (all trained from scratch)

| Model | Architecture | Purpose | Key Metrics |
|-------|-------------|---------|-------------|
| Conditional SELFIES VAE | GRU encoder/decoder, 4D state conditioning, 64D latent | Generate novel molecules per state | 99.9% valid, 94.8% unique, 9.5M params |
| Affinity MPNN | NNConv message-passing + MLP head | Predict pIC50 binding affinity | RMSE=0.7182, R^2=0.6863, Pearson=0.8323 on 10,466 EGFR compounds |
| Multi-task ADMET | GIN backbone + 6 task heads | Predict drug safety (hERG, CYP3A4, etc.) | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323, 187K params |

### Docking Infrastructure

GNINA v1.1 integrated as tier-0 physics-based docking. 4 EGFR receptors prepared
(PDBQT format, one per conformational state: 1M17, 2GS7, 3W2R, 4ZAU). Validation
shows clear separation: known binders score -7.32 kcal/mol vs non-binders -4.16
kcal/mol (delta -3.16). Runs on GPU only (CUDA required).

---

## 2. Key Results

### Head-to-Head Comparison

| Metric | Static | State-Aware | Winner |
|--------|--------|-------------|--------|
| Mean unified score | 0.5437 | 0.4378 | Static (p<0.001, Cohen's d=1.36) |
| Max score | 0.7288 | 0.7794 | State-aware |
| Candidates | 30 | 461 | State-aware (15x) |
| Chemical diversity | 0.5684 | 0.9056 | State-aware (59% higher) |
| Novel molecules | 0 | 431 | State-aware |

### Retrospective Time-Split Validation (strongest signal)

Models retrained on pre-cutoff data only. Enrichment factor measures how densely
future approved drugs appear in the top-ranked candidates:

| Cutoff | Held-Out Drugs | State-Aware EF@10 | Static EF@10 | Enrichment Ratio |
|--------|---------------|-------------------|-------------|-----------------|
| 2010 | afatinib, osimertinib, dacomitinib, lazertinib, mobocertinib | 4.95 | 0.47 | 10.5x |
| 2015 | dacomitinib, lazertinib, mobocertinib | 7.72 | 0.79 | 9.8x |

All held-out drugs found (5/5 pre-2010, 3/3 pre-2015). Novelty score 0.99 --
the VAE generates genuinely new molecules, not memorized training data.

**Why state-aware wins on enrichment but loses on mean score:** The 35% reference
similarity component (heaviest weight) penalizes novel VAE molecules that don't
resemble the 3 reference drugs. This drags down the mean. But among those diverse
candidates are molecules resembling future drugs -- needles in a haystack detected
by enrichment factor, not mean score.

---

## 3. Current Limitations Relevant to This Research

### 3.1 No 3D Pocket Awareness in Generation

The VAE generates SELFIES/SMILES strings (1D text). It has no concept of how the
molecule fits in the pocket -- it only knows SMILES patterns correlated with EGFR
activity. Two molecules with similar SMILES can have very different 3D binding poses.
Generation is unguided in 3D space.

4 EGFR receptor structures are already prepared (PDBQT format with docking boxes)
for GNINA, so the infrastructure for 3D-aware generation exists.

### 3.2 Discrete 4-State Model

The conformational states are categorical (4 bins). Real kinase dynamics are
continuous -- the protein breathes through intermediate conformations. The 4-state
model is standard in kinase literature but is an acknowledged oversimplification.
Additionally, all 17 curated EGFR resistance mutations map to the same state
(DFGin/aCin), making the mutation-to-state prediction uninformative.

### 3.3 No Selectivity Analysis

The pipeline scores EGFR binding only. It does not check off-target kinases
(ABL, BRAF, ALK, SRC, etc.). A pan-kinase binder is not a useful drug. No
selectivity profiling exists.

### 3.4 Reference Similarity Uses Only 3 Molecules

The heaviest scoring component (35%) computes Tanimoto against only erlotinib,
gefitinib, and osimertinib. This biases toward known chemotypes and penalizes
novel scaffolds that might bind differently.

### 3.5 ADMET Not Integrated Into Scoring

ADMET predictions (hERG, CYP3A4, etc.) are informational only. Hard filtering
rejects ALL kinase inhibitors on hERG (known class liability). No kinase-calibrated
ADMET thresholds exist.

### 3.6 No Active Learning / Iterative Refinement

One-shot pipeline: generate -> score -> rank -> done. No mechanism to learn from
scoring results and generate better candidates in subsequent rounds.

### 3.7 No Uncertainty Quantification

All models produce point predictions with no confidence intervals. MPNN predicts
pIC50=6.3 but cannot distinguish high-confidence from low-confidence predictions.

### 3.8 No Molecular Dynamics

Pipeline uses static crystal structures. No ensemble docking, no flexibility, no
thermodynamic ensemble, no water interactions.

### 3.9 No Retrosynthetic Analysis

Generates structures but doesn't assess real synthesizability. SA score is a rough
heuristic with no actual retrosynthetic route analysis.

### 3.10 No SOTA Method Comparison

No benchmarking against published generative models (REINVENT, DrugEx, Pocket2Mol,
etc.). Reviewers will demand this.

---

## 4. Research Questions

Answer each question with **specific, actionable information**: model names, paper
citations (first author + year + journal), GitHub repos where available, dataset sizes,
reported metrics, computational requirements, and your assessment of feasibility for
a small academic team with HPC GPU access (NVIDIA H200s).

### Q1: 3D Structure-Based Molecular Generation

What are the current state-of-the-art models for generating molecules directly inside
protein binding pockets? For each model:
- Architecture (diffusion, autoregressive, flow-matching, etc.)
- Training data requirements (PDBbind, CrossDocked2020, etc.)
- Key performance metrics (validity, uniqueness, binding affinity of generated molecules)
- Whether it supports conditioning on multiple protein conformations
- Open-source availability and ease of integration
- GPU requirements for training and inference

Specific models to investigate: DiffSBDD, Pocket2Mol, TargetDiff, DecompDiff,
DrugGPS, ResGen, FLAG, SBDD-related diffusion models, 3D-SBDD, MolCRAFT. Also
investigate newer approaches from 2024-2025 that may not be in this list.

### Q2: Conformational Ensemble Methods

How do recent papers handle protein conformational flexibility in drug design?
- Ensemble docking approaches (docking against multiple conformations)
- Continuous conformational representations (beyond discrete state classification)
- Protein language model embeddings (ESM-2, ESMFold) for representing conformational states
- MD simulation-derived ensemble approaches
- How do state-of-the-art methods condition molecular generation on protein flexibility?

### Q3: Physics-Informed ML for Binding Affinity

What approaches go beyond classical docking (Vina/GNINA) for predicting binding affinity?
- Equivariant neural network potentials (PaiNN, NequIP, MACE applied to protein-ligand)
- Geometric deep learning for binding (e.g., TANKBind, EquiBind, DiffDock)
- Free energy perturbation (FEP) ML surrogates
- Protein-ligand interaction fingerprint models
- How do these compare to GNINA and MPNN in accuracy and speed?

### Q4: Multi-Objective Optimization in Drug Design

What frameworks exist beyond Pareto front analysis for balancing competing objectives
(affinity, selectivity, ADMET, novelty)?
- Bayesian multi-objective optimization (qEHVI, MORBO)
- Scalarization strategies with learned weights
- Constrained optimization (optimize affinity subject to ADMET constraints)
- How do published pipelines handle the affinity-safety tradeoff specifically for kinase inhibitors?

### Q5: Active Learning and Bayesian Optimization for Drug Design

What iterative design-make-test-analyze (DMTA) cycle implementations exist?
- Active learning with uncertainty-guided candidate selection
- Bayesian optimization over molecular space
- How many rounds of iteration are typical? What oracle costs are assumed?
- Specific tools/frameworks: REINVENT with active learning, Gauche, BOSS, etc.

### Q6: Uncertainty Quantification for Molecular Property Prediction

What methods are most effective and practical?
- Deep ensembles vs MC dropout vs evidential deep learning vs conformal prediction
- Computational cost relative to point prediction
- Which methods work well with GNN architectures specifically?
- Are there published UQ benchmarks for drug discovery tasks?

### Q7: Kinase Selectivity Scoring

How is selectivity computationally profiled across a kinase panel?
- Multi-target MPNN/GNN approaches
- Cross-docking against homologous structures
- Kinome-wide selectivity prediction models (KinomeScan predictions, etc.)
- Selectivity entropy and S-score metrics
- What selectivity data is publicly available?

### Q8: Retrosynthetic Analysis Integration

What tools and models exist for assessing synthesizability of generated molecules?
- ASKCOS, IBM RXN, Retro*, Chemformer for retrosynthesis
- SAScore vs SCScore vs other synthesizability metrics
- How do published pipelines integrate retrosynthetic feasibility into their workflow?
- Can retrosynthetic analysis run at the scale of hundreds of molecules?

### Q9: Protein-Ligand Interaction Fingerprints

How can binding modes be analyzed from docking poses (we have GNINA poses available)?
- PLIF (Protein-Ligand Interaction Fingerprints) tools and methods
- State-specific interaction patterns (contacts unique to DFGout vs DFGin)
- Integration of interaction analysis into scoring or filtering

### Q10: Water and Solvation Modeling

What practical approaches exist for incorporating water/solvation effects?
- WaterMap, 3D-RISM, SZMAP
- Implicit solvent corrections for docking scores
- ML approaches to water displacement prediction
- Feasibility for a pipeline that needs to score hundreds of molecules

---

## 5. Output Format

For each question, provide:
1. **Summary** (2-3 sentences: the landscape and your recommendation)
2. **Top 3-5 specific approaches** with: name, citation, key metrics, open-source status, GPU requirements
3. **Recommendation for StateBind** — which approach(es) best fit our context (EGFR kinase, 4 conformational states, ~10K training compounds, HPC with H200 GPUs, small academic team)
4. **Integration complexity** — Low / Medium / High, with justification
