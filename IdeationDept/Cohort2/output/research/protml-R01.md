---
agent: Maverick Protein ML Expert
round: 1
date: 2026-04-09
type: research-note
topic: Protein language models, learned pocket representations, and structure prediction for StateBind
---

# Research Note: Protein Language Models, Learned Pocket Representations, and Structure Prediction for StateBind

## Executive Summary

StateBind's conformational state atlas uses 9 hand-crafted geometric features (DFG
distances, salt bridge lengths, helix angles, pocket volumes) to distinguish 4 EGFR
kinase states. This research note investigates whether protein language models (pLMs)
and modern learned representations could dramatically improve state discrimination,
scoring fidelity, and coverage of resistance-relevant mutations. The evidence is
strong: ESM-2 pocket embeddings provide 1280-dimensional representations that capture
evolutionary, structural, and functional information that 9 scalar features cannot;
protein-ligand co-embedding methods like DrugCLIP achieve 10-million-fold speedups
over docking while matching or exceeding enrichment factors; AlphaFold2 with MSA
subsampling can predict kinase conformational state populations with >80% accuracy;
and pre-trained molecular representations improve property prediction by 20-59% over
training from scratch. Each of these advances maps directly onto a specific StateBind
limitation and represents a concrete, publishable enhancement.

---

## 1. ESM-2 for Binding Site Representation

### 1.1 The Representation Gap: 9D vs 1280D

StateBind's current state atlas (see `src/statebind/structure/features.py`) encodes
each EGFR conformational state using 9 geometric measurements:

1. DFG Asp-Phe distance (5.2-11.0 A)
2. DFG-Phe displacement (0.3-7.2 A)
3. aC-helix salt bridge K745-E762 distance (2.7-10.5 A)
4. aC-helix rotation angle (1.0-22.0 degrees)
5. P-loop displacement RMSD (0.0-1.8 A)
6. Hinge angle (143-157 degrees)
7. Activation loop RMSD (0.0-5.5 A)
8. Gatekeeper sidechain chi1 angle (-172 to -55 degrees)
9. Pocket volume (420-850 A^3)

These features are interpretable and capture the known structural hallmarks of DFG/aC
conformational states. However, they compress the information content of an 85-residue
binding pocket (thousands of atoms, complex electrostatic surfaces, solvation
patterns) into just 9 numbers.

ESM-2, the 650M-parameter protein language model from Meta (Lin et al., 2023),
generates per-residue embeddings of dimension 1280. For the 85 KLIFS-defined pocket
residues of EGFR, this yields a representation of 85 x 1280 = 108,800 values before
any dimensionality reduction. Even after mean-pooling over pocket residues (the
standard approach), the result is a 1280-dimensional vector -- 142x richer than the
current 9D features.

### 1.2 ESM-2 Architecture and Model Variants

The ESM-2 family provides multiple model sizes (Lin et al., 2023):

| Model | Parameters | Layers | Hidden Dim | VRAM (inference) |
|-------|-----------|--------|-----------|-----------------|
| esm2_t6_8M | 8M | 6 | 320 | <1 GB |
| esm2_t12_35M | 35M | 12 | 480 | ~1 GB |
| esm2_t30_150M | 150M | 30 | 640 | ~2 GB |
| esm2_t33_650M | 650M | 33 | 1280 | ~4-6 GB |
| esm2_t36_3B | 3B | 36 | 2560 | ~12-16 GB |
| esm2_t48_15B | 15B | 48 | 5120 | >40 GB |

For StateBind, the 650M model (esm2_t33) provides the best cost-performance
trade-off. It fits comfortably on a single H200 GPU (141 GB VRAM) and generates
1280D embeddings that capture evolutionary conservation, structural context, and
implicit dynamics. The 3B model (esm2_t36) with 2560D embeddings could be used for
higher-fidelity representations at ~12-16 GB VRAM cost.

All checkpoints are freely available on HuggingFace under the Meta ESM repository.

### 1.3 ESM-2 for Kinase-Specific Tasks

Recent work demonstrates that ESM-2 embeddings capture kinase-relevant features:

- Mid-to-late transformer activations (layers 20-33 of the 33-layer 650M model)
  achieve 75.7% cross-validated kinase classification accuracy, compared to 70.2%
  for last-layer-only embeddings (Yang et al., 2026). This indicates that
  intermediate representations preserve both catalytic core motifs and global
  context.

- ESM-2 embeddings discover features corresponding to 143 distinct Swiss-Prot-
  annotated functional concepts, including kinase active-site motifs (Lin et al.,
  2023).

- Macro-F1 and top-3 metrics also improve with layer selection, demonstrating
  preservation of both catalytic core motifs and global context in intermediate
  representations.

### 1.4 EPoCS: ESM-2 Pocket Representations

The EPoCS method (Mapping the space of protein binding sites, 2025) combines ESM-2
embeddings with 3D Voronoi tessellation to create binding site representations:

- Uses the 3B-parameter ESM-2 model for residue-level embeddings
- Identifies pocket residues via radially truncated Voronoi tessellation around
  ligand atoms
- Aggregates via mean pooling over surface residues
- Achieves rank correlation rho_onset = 0.677 with alignment-based structural
  similarity (APoc) on 3,500 PDB pockets
- Alignment-free and computationally cheap compared to structural alternatives
- For druggability prediction, ESM-MLP achieves test AUC = 0.81 on debiased
  validation sets

This demonstrates that ESM-2 pocket embeddings capture meaningful structural and
functional information about binding sites without requiring 3D alignment.

### 1.5 ESM Cambrian (ESM-C): Next Generation

ESM Cambrian (ESM-C), released in late 2024 by EvolutionaryScale, delivers
significant improvements over ESM-2:

- ESM-C 300M achieves similar performance to ESM-2 650M with dramatically reduced
  memory and faster inference
- ESM-C 600M with mean embeddings offers optimal balance of performance and
  efficiency for transfer learning in biological applications
- ESM-C scales up to 6B parameters with non-diminishing returns
- Drop-in replacement for ESM-2 in existing pipelines

For StateBind, ESM-C 600M would be the recommended starting point, providing ESM-2
650M-level performance at lower compute cost.

### 1.6 Extraction Protocol for EGFR Pocket Embeddings

For StateBind integration, the pocket embedding extraction would proceed as:

1. **Identify KLIFS 85 pocket residues** for EGFR kinase domain. KLIFS defines
   these as the residues interacting with any kinase inhibitor across the catalytic
   front cleft, gate area, and back cleft. Average binding pocket RMSD for KLIFS
   alignment is 2.2 +/- 0.2 A across all processed structures (van Linden et al.,
   2014).

2. **Extract per-residue embeddings** using ESM-2 650M (layer 33) or ESM-C 600M
   for the full EGFR kinase domain sequence (~300 residues).

3. **Select pocket residues** by mapping KLIFS 85-position numbering to EGFR
   sequence positions.

4. **Aggregate**: Mean-pool over 85 pocket residues to get a 1280D pocket vector,
   or use attention-weighted pooling for a learnable aggregation.

5. **Per-state embeddings**: Extract for each of the 4 representative structures
   (1M17, 2GS7, 3W2R, 4ZAU) using the sequence of the crystallized construct.

**Key insight**: Since ESM-2 is a sequence model, the embeddings for the same
wild-type EGFR sequence will be identical regardless of conformational state. To
capture state differences, we need either: (a) structure-conditioned embeddings via
ProstT5 or (b) per-structure geometric features combined with ESM-2 sequence
embeddings via concatenation or cross-attention.

### 1.7 ProstT5: Structure-Aware Protein Language Model

ProstT5 (Heinzinger et al., 2024) is a bilingual model that translates between
amino acid sequences and 3Di structural tokens (from Foldseek). This is critically
important for StateBind because:

- ProstT5 takes 3D structure as input (via 3Di tokens), so different conformational
  states of the same protein will produce DIFFERENT embeddings
- This directly addresses the limitation of sequence-only ESM-2 for state
  discrimination
- ProstT5 is based on ProtT5-XL-U50, fine-tuned on 17M proteins with AlphaFoldDB
  structures
- Embeddings capture both sequence and structural information simultaneously
- Open-source, available on HuggingFace (Rostlab/ProstT5)

**Recommendation**: For StateBind, ProstT5 3Di-conditioned embeddings would be the
ideal pocket representation, as they naturally capture conformational state
differences that sequence-only models cannot.

---

## 2. Protein-Ligand Co-Embedding Methods

### 2.1 DrugCLIP: Contrastive Protein-Molecule Representation Learning

DrugCLIP (Gao et al., 2023; published in Science, 2025) is the most significant
recent advance in computational virtual screening. Key performance metrics:

**DUD-E Zero-Shot Performance** (Gao et al., 2023):
- AUROC: 80.93%
- BEDROC: 50.52%
- EF@0.5%: 38.07
- EF@1%: 31.89
- EF@5%: 10.66
- Comparison: Glide-SP achieves 76.70% AUROC and 40.70% BEDROC

**DUD-E Fine-Tuned** (DrugCLIP-FT):
- AUROC: 96.59%
- RE@0.5%: 118.10
- RE@1%: 67.17

**LIT-PCBA Performance**:
- AUROC: 57.17%
- BEDROC: 6.23%
- EF@0.5%: 8.56
- EF@1%: 5.51
- EF@5%: 2.27

**Genome-Wide Screening (Science 2025)**:
- Screened ~10,000 human proteins against 500M compounds (>10 trillion pairs)
- Up to 10-million-fold faster than physics-based docking
- Wet-lab validation: 17.5% hit rate for TRIP12 (no prior structure/ligand known)
- 5HT2AR: Two agonists with EC50 < 100 nM
- NET: 15% hit rate, two inhibitors structurally validated by cryo-EM
- Human evaluation: DrugCLIP preferred over Glide for top-10 molecules in 80% of
  cases

**Relevance to StateBind**: DrugCLIP could serve as a protein-aware scoring
component, replacing or augmenting the docking cascade. It embeds pockets and
ligands in the same latent space, enabling direct pocket-ligand compatibility
scoring. For StateBind, each conformational state's pocket would be encoded
separately, and candidate molecules scored against all 4 state pockets.

### 2.2 ProFSA: Self-Supervised Pocket Pre-training

ProFSA (Gao et al., ICLR 2024) addresses the limited availability of pocket-ligand
complex structures (<100K non-redundant pairs) by generating >5M complexes from
protein fragments:

- Segments protein structures into drug-like fragments and their surrounding pockets
- Trains pocket encoder via contrastive alignment with pre-trained small molecule
  representations
- Outperforms Uni-Mol pocket in druggability prediction:
  - Fpocket RMSE: 0.1077 (ProFSA) vs 0.1140 (Uni-Mol)
  - Druggability RMSE: 0.0934 (ProFSA) vs 0.1001 (Uni-Mol)
  - Total SASA RMSE: 20.01 (ProFSA) vs 20.73 (Uni-Mol)

### 2.3 FABind and TankBind: Fast Binding Prediction

**FABind** (Pei et al., NeurIPS 2023): End-to-end model combining pocket prediction
and docking. FABind achieves binding pose prediction with RMSD of 3.9 A on average,
showing strong generalization to unseen targets. FABind+ (April 2024) further
improves performance.

**TankBind** (Lu et al., 2022): Trigonometry-aware neural network for binding
structure prediction. Uses P2Rank for pocket segmentation followed by confidence-
based ranking.

**DynamicBind** (Nature Communications, 2024): A deep equivariant generative model
that predicts ligand-specific protein-ligand complex structures, capturing
conformational changes during binding. Critical for StateBind because it explicitly
models induced-fit effects across conformational states.

### 2.4 AANet: Virtual Screening Under Structural Uncertainty

AANet (2025) is noteworthy for its performance under apo/predicted structure
conditions -- directly relevant to StateBind's use case:
- DUD-E EF@1% (apo-predicted, blind setting): 37.19 (AANet) vs 11.75 (DrugCLIP)
- BEDROC (same setting): 0.6232 (AANet) vs 0.1974 (DrugCLIP)

This demonstrates that when structures are imperfect (as they would be for
AlphaFold-predicted mutant structures), alignment-and-aggregation strategies
outperform simple contrastive approaches.

### 2.5 Implications for StateBind's Scoring Pipeline

StateBind's current docking cascade (scoring.py lines 38-79):
1. GNINA physics-informed docking (when GPU available)
2. MPNN affinity predictor (trained from scratch, 10,466 compounds)
3. DockingProxy MLP
4. Constant 0.5 stub

A co-embedding approach would add a 5th scoring tier between GNINA and MPNN, using
pre-trained pocket-ligand representations that capture protein context the MPNN
currently lacks. The compute cost would be minimal (milliseconds per molecule) vs
GNINA (seconds to minutes).

---

## 3. AlphaFold/ESMFold for Mutant Structure Prediction

### 3.1 The Mutant Structure Gap

StateBind currently has crystal structures for only wild-type EGFR in 4 states
(1M17, 2GS7, 3W2R, 4ZAU). The most clinically relevant resistance mutations lack
experimental structures in multiple conformational states:

- **C797S**: Third-generation TKI resistance (osimertinib), no crystal in all 4
  states
- **T790M/C797S**: Compound resistance, limited structural data
- **L718Q**: Fourth-generation TKI resistance, emerging clinical concern
- **L858R**: Activating mutation, structures available but only in active state
- **ex19del**: Most common EGFR mutation, deletion variants poorly characterized

### 3.2 AlphaFold2 for Kinase Structure Prediction

AlphaFold2 achieves remarkable accuracy for protein kinase domains:

- **Overall backbone RMSD**: 0.8 A vs experimental structures at CASP14 (Jumper
  et al., 2021)
- **Binding pocket RMSD**: Median 1.3 A for AF2 models vs experimental holo
  structures (Heo & Feig, 2022). For comparison, template-based models achieve
  median 3.3 A.
- **EGFR kinase domain**: AF2-modeled structures include EGFR alongside ABL1, BTK,
  DDR1, with pLDDT scores evaluated for the kinase domain.

**Critical limitation for conformational states**: Default AF2 predictions using
full MSAs consistently produce only the active DFG-in state for kinases, failing
to capture inactive conformations. The DFG-Phe and C-Glu motifs show higher
uncertainty on average (pLDDT ~75%) compared to the rest of the protein, indicating
lower confidence in these flexible regions.

### 3.3 MSA Subsampling for Conformational Diversity

Subsampled AlphaFold2 (Wayment-Steele et al., Nature Communications 2024)
demonstrates that reducing MSA depth induces conformational diversity:

- Predicted changes in relative state populations for Abl1 kinase with >80%
  accuracy
- Method: For each kinase, 1280 structures generated: 640 for MSAs of depth 16
  and 32, with 128 random seeds generating 5 structures each
- Successfully distinguished both functional states of EGFR by detecting
  characteristic activation loop rearrangements
- Biasing approaches allow user-defined structural properties for predictions
  (Del Alamo et al., 2023)

**Limitation**: While MSA subsampling increases conformational heterogeneity around
the ground active state, it cannot readily generate distinct low-populated inactive
conformations. Default AF2 with full MSAs consistently predicts the more commonly
found DFG-in structure.

### 3.4 AlphaFold2-RAVE for Kinase DFG Conformations

AlphaFold2-RAVE (Monteiro da Silva et al., JCIM 2024) combines AF2 subsampling
with enhanced sampling to predict DFG loop stability:

- Studied DDR1 kinase in WT + 3 mutants (D671N, Y755A, Y759A)
- Predicted DFG conformation preference flipping upon mutation:
  - WT DDR1: +0.5 kBT (DFG-in favored)
  - D671N: -0.2 kBT (DFG-out favored)
  - Y755A: -0.42 kBT (DFG-out favored)
  - Y759A: -0.13 kBT (DFG-out favored)
- 2-3 orders of magnitude faster than unbiased MD simulations
- Qualitative agreement with benchmark MD data

**Relevance to StateBind**: This approach could predict how EGFR resistance mutations
shift the conformational equilibrium between DFG-in and DFG-out states, directly
informing state-aware molecular generation.

### 3.5 AlphaFold3 for Drug Discovery

AlphaFold3 (Abramson et al., Nature 2024) and its open derivative Protenix represent
the next frontier:

- Models protein-protein, protein-ligand, and protein-nucleic acid complexes
- AlphaRank (fine-tuned Protenix): Achieves 0.7533 accuracy and 0.7855 AUC on JACS
  benchmark for pairwise affinity ranking
- Comparable to FEP+ workflows at substantially lower compute cost
- DEKOIS2.0 benchmarks show exceptional screening capability using intrinsic
  confidence metrics
- Can predict structures of protein-ligand complexes without prior holo structures

### 3.6 ESMFold: Speed-Accuracy Trade-off

ESMFold (Lin et al., 2023) provides a faster alternative to AlphaFold2:

- Correctly predicted 76% of monomeric structures (vs AF2's 88%) based on 2022-2024
  PDB structures (2026 comparison study)
- Median pLDDT: 87.40 (vs AF2's 92.65)
- 10-30x faster than AF2 (no MSA computation required)
- Well-suited for rapid screening of mutant structures before AF2 refinement

### 3.7 MoDAFold: AF2 + MD for Mutant Structures

MoDAFold (Wang et al., Brief Bioinform 2024) combines AlphaFold2 with molecular
dynamics for predicting mutant protein structures:

- Uses AF2 as initial structure generator, then MD to refine mutant-specific
  conformational changes
- Addresses AF2's known limitation of predicting mutant structures nearly
  identically to wild-type (V210I example: AF2 RMSD 1.5 A from WT but 2.6 A from
  actual mutant)
- Could be applied to EGFR C797S/T790M mutant structure prediction

---

## 4. Conformational Ensemble Prediction

### 4.1 AlphaFlow

AlphaFlow (Jing et al., 2024) is the leading method for generating protein
conformational ensembles from sequence:

- Architecture: Modified AlphaFold fine-tuned with flow matching objective
- Three variants:
  - AlphaFlow-PDB: Trained on experimental structures
  - AlphaFlow-MD: Trained on MD trajectories at 300K
  - AlphaFlow-MD+Templates: Template-conditioned for specific conformations
- Distilled 12-layer variants: 2.5x faster at small accuracy cost
- Substantially surpasses MSA-based baselines for:
  - Conformational flexibility prediction
  - Distributional modeling of atomic positions
  - Higher-order ensemble observables (intermittent contacts, solvent exposure)
- Checkpoints available on HuggingFace

**For StateBind**: AlphaFlow could generate conformational ensembles for each of the
4 EGFR states, replacing single crystal structures with distributions. This addresses
the "static structure" limitation directly.

### 4.2 BBFlow: Faster Ensemble Generation

BBFlow (2025) is an order of magnitude faster than AlphaFlow at similar accuracy,
making it practical for high-throughput applications. If ensemble generation needs to
be performed for many mutant sequences, BBFlow would be the preferred choice.

### 4.3 Str2Str: Zero-Shot Conformation Sampling

Str2Str (Lu et al., 2023) is a score-based framework for zero-shot protein
conformation sampling:

- Learns conformation space exploration from PDB structures in an amortized way
- No reliance on simulation data during training or inference
- Outperforms previous generative structure prediction models
- Orders of magnitude faster than long MD simulations
- Roto-translation equivariant

**Relevance**: Could generate local conformational variations around each of
StateBind's 4 crystal structures, simulating pocket breathing and flexibility
without expensive MD.

### 4.4 EigenFold

EigenFold (Jing et al., 2023) is a diffusion generative framework:

- Achieves median TMScore of 0.84 on CAMEO targets
- Cannot yet accurately capture both conformations of fold-switching proteins
- Better suited for sampling around a known fold rather than predicting entirely
  new conformations

### 4.5 Comparison of Ensemble Methods

| Method | Speed | State Diversity | Accuracy | Data Requirement |
|--------|-------|----------------|----------|-----------------|
| AlphaFlow-PDB | Moderate | Good | Best | PDB structures |
| AlphaFlow-MD | Moderate | Best | Good | MD trajectories |
| BBFlow | Fast | Good | Good | Backbone geometry |
| Str2Str | Fast | Moderate | Good | PDB structures |
| EigenFold | Moderate | Limited | Moderate | Sequence only |
| MSA subsampling | Slow | Limited | Variable | MSA depth |
| MD simulation | Very slow | Best | Best | Force field params |

### 4.6 ProteinBench Evaluation (2024)

The ProteinBench benchmark (2024) evaluated multiple conformational prediction
methods, finding that ConfDiff-ESM-Force achieved the highest ensemble accuracy by
incorporating physical force information. This suggests that hybrid approaches
combining learned representations with physical constraints are the future direction.

---

## 5. Pre-trained Molecular Representations

### 5.1 The Case Against Training from Scratch

StateBind's MPNN was trained from scratch on 10,466 compounds for binding affinity
prediction, achieving R^2 = 0.69. Modern pre-trained molecular models are trained
on orders of magnitude more data:

| Model | Pre-training Data | Parameters | Task |
|-------|------------------|-----------|------|
| Uni-Mol | 209M conformations + 3M pockets | 48M | 3D molecular representation |
| Uni-Mol2 | 800M conformations | 84M-1.1B | Molecular foundation model |
| GEM | 20M molecules | - | Geometry-enhanced representation |
| GROVER | 10M molecules | 100M | Self-supervised GNN |
| MolCLR | - | - | Contrastive learning |

The improvement from pre-training is substantial and well-documented:

- **JMP (2024)**: Average improvement of 59% over training from scratch across 40
  tasks, matching or setting SOTA on 34/40 tasks
- **MLM-FG**: Error reduction from 0.9721 (scratch) to 0.3432 (pre-trained) on
  ESOL -- a 65% improvement
- **HOPV MAE**: 7.6 meV (scratch) to 6.1 meV (pre-trained) -- 20% improvement
- **Uni-Mol**: SOTA in 14/15 molecular property prediction tasks

### 5.2 Uni-Mol: Most Relevant Pre-trained Model

Uni-Mol (Zhou et al., ICLR 2023) is the most directly applicable model for
StateBind:

- **Pre-training**: 209M molecular 3D conformations + 3M protein pocket data
- **Architecture**: SE(3)-equivariant transformer incorporating 3D spatial
  information
- **Docking power**: 88.07% of poses with RMSD <= 2 A on CASF-2016 (22.81% better
  than popular docking methods), ranking 1st
- **Property prediction**: SOTA on 14/15 MoleculeNet tasks
- **Uni-Mol Docking V2**: 77+% of poses with RMSD < 2.0 A on PoseBusters, 75+%
  passing all quality checks
- **Uni-Mol2 (NeurIPS 2024)**: Scales to 1.1B parameters on 800M conformations
- **Checkpoints**: Freely available on GitHub (deepmodeling/Uni-Mol)

**For StateBind**: Uni-Mol's pocket pre-training model could serve as a drop-in
replacement for the from-scratch MPNN, providing pre-trained pocket-aware molecular
representations. The expected improvement based on literature is 20-59%.

### 5.3 GEM: Geometry-Enhanced Molecular Representation

GEM (Fang et al., Nature Machine Intelligence 2022) achieves SOTA on 14/15 datasets
through:
- Geometry-based GNN architecture
- Geometry-level self-supervised learning strategies
- Captures bond angles, dihedral angles, and spatial distances

### 5.4 GROVER: Self-Supervised GNN Pre-training

GROVER (Rong et al., NeurIPS 2020) integrates GNN into Transformer:
- 100M parameters
- Pre-trained on 10M unlabeled molecules
- Two self-supervised tasks: contextual property prediction and graph-level motif
  prediction

**Note**: Vision System idea 010 (Self-Supervised GNN Pre-Training) proposed this
direction. Our contribution would be to provide the specific benchmark evidence for
the improvement magnitude and the integration architecture with StateBind's existing
MPNN.

### 5.5 Practical Upgrade Path for StateBind's MPNN

The most practical upgrade path for StateBind's from-scratch MPNN:

1. **Stage 1 (Low effort)**: Replace MPNN's atom/bond features with Uni-Mol
   pre-trained embeddings. Fine-tune on StateBind's 10,466 compounds. Expected
   improvement: 20-40% in R^2.

2. **Stage 2 (Medium effort)**: Use Uni-Mol's pocket pre-training model to add
   protein context to the scoring function. This introduces pocket-awareness that
   the current MPNN lacks entirely.

3. **Stage 3 (High effort)**: Train a DrugCLIP-style pocket-ligand co-embedding
   model on StateBind's 4-state data, with state-conditioned pocket encodings.

---

## 6. Practical Integration Architecture

### 6.1 Proposed Architecture: ESM-2/ProstT5 + Uni-Mol for StateBind

The integration architecture has three components:

**Component A: Learned State Representation (replaces 9D features)**

```
EGFR crystal structure (PDB)
    |
    v
Foldseek 3Di tokenization
    |
    v
ProstT5 encoder (structure-aware)
    |
    v
Extract 85 KLIFS pocket residue embeddings
    |
    v
Attention-weighted pooling
    |
    v
State embedding vector (1024D)
```

Alternatively, using ESM-2:
```
EGFR sequence + per-state structural features
    |
    v
ESM-2 650M (layer 20-33 mean)
    |
    v
85 KLIFS pocket residue embeddings
    |
    v
Mean pooling -> 1280D pocket vector
    |
    v
Concatenate with 9D geometric features -> 1289D
    |
    v
MLP projection -> state embedding (128D)
```

**Component B: Pre-trained Molecular Scoring (replaces from-scratch MPNN)**

```
Candidate SMILES
    |
    v
Uni-Mol encoder (pre-trained on 209M conformations)
    |
    v
3D molecular representation
    |
    v
Fine-tune on StateBind's 10,466 compounds
    |
    v
pIC50 prediction
```

**Component C: Protein-Ligand Co-Scoring (new scoring dimension)**

```
State pocket embedding (from Component A)  +  Molecular embedding (from Component B)
    |                                              |
    v                                              v
Pocket encoder (ProFSA/DrugCLIP-style)    Ligand encoder (Uni-Mol)
    |                                              |
    +------------ Contrastive scoring ------------+
    |
    v
Pocket-ligand compatibility score (0-1)
```

### 6.2 Compute Cost Estimates (H200 GPU)

| Task | Time per Item | Items | Total | VRAM |
|------|-------------|-------|-------|------|
| ESM-2 650M embedding extraction (per protein) | ~0.5s | 4 states x 1 = 4 | 2s | 4-6 GB |
| ProstT5 embedding (per structure) | ~1s | 4 states + mutants (~20) | 20s | ~8 GB |
| Uni-Mol inference (per molecule) | ~10ms | 10,000 candidates | 100s | ~4 GB |
| DrugCLIP scoring (per pair) | ~1ms | 10,000 x 4 states | 40s | ~4 GB |
| AlphaFold2 mutant prediction | ~5min | 10 mutants x 4 states | ~3.3h | ~16 GB |
| AlphaFlow ensemble (per structure) | ~10min | 4 states x 100 samples | ~67h | ~16 GB |

**Total for minimal viable experiment**: <4 GPU-hours on H200 for Components A+B+C
(excluding ensemble generation). AlphaFlow ensemble generation is the most expensive
component but can be done once and cached.

### 6.3 Minimal Viable Experiment

The smallest publishable experiment that demonstrates pLM value for StateBind:

1. **Extract ESM-2 pocket embeddings** for the 4 representative EGFR structures
   (1M17, 2GS7, 3W2R, 4ZAU) -- 2 seconds of compute

2. **Cluster the 4 pocket embeddings** and compare to the 9D feature clustering
   -- do ESM-2 embeddings separate the 4 states more clearly?

3. **Train a linear probe** on ESM-2 pocket embeddings vs 9D features for state
   classification across all 16 atlas structures -- does higher dimensionality
   improve discrimination?

4. **Replace MPNN features** with Uni-Mol pre-trained embeddings and measure R^2
   on the same train/test split -- quantify the pre-training advantage

5. **Re-run the retrospective evaluation** with the improved scoring and report
   the change in EF@10 (currently 4.95/7.72 state-aware vs 0.47/0.79 static)

This experiment requires <1 GPU-day and produces a concrete comparison figure for
publication.

### 6.4 Integration with Existing Pipeline

The key files that would need modification:

- `src/statebind/structure/features.py`: Add ESM-2/ProstT5 embedding extraction
  alongside existing 9D features (backward compatible, new feature_source="esm2")
- `src/statebind/structure/models.py`: Extend StructuralFeatures with optional
  embedding field
- `src/statebind/ml/mpnn.py`: Add Uni-Mol pre-trained backbone option
- `src/statebind/ranking/scoring.py`: Add co-embedding scoring tier in cascade
- `configs/structure.yaml`: Add ESM-2 model selection and layer configuration

All changes would be backward-compatible, with the existing 9D pipeline remaining
the default and pLM-enhanced pipeline selectable via config.

---

## 7. Critical Assessment and Limitations

### 7.1 ESM-2 Embedding Limitations for Conformational States

The most critical limitation: **ESM-2 is a sequence model.** The same EGFR wild-type
sequence produces identical embeddings regardless of whether the protein is in
DFGin_aCin or DFGout_aCout. This means ESM-2 alone CANNOT distinguish conformational
states of the same sequence.

**Mitigation strategies**:
1. Use ProstT5 (structure-conditioned) instead of ESM-2 for state discrimination
2. Concatenate ESM-2 sequence embeddings with the existing 9D structural features
3. Use ESM-2 for mutation effect prediction (different mutant sequences produce
   different embeddings) rather than state discrimination

### 7.2 AlphaFold2 Conformational State Prediction Limitations

- Default AF2 consistently predicts only the DFG-in (active) state for kinases
- MSA subsampling helps but cannot reliably generate rare DFG-out conformations
- Predicted DFG-Phe/C-Glu regions have lower confidence (pLDDT ~75%)
- AF2 cannot capture small structural changes from point mutations (V210I example:
  AF2 predicts 1.5 A RMSD from WT, actual mutant differs by 2.6 A)

### 7.3 Data Leakage Concerns

Recent work (2025) has identified data leakage and redundancy issues in the LIT-PCBA
benchmark, which inflates performance metrics for methods like DrugCLIP. Benchmark
numbers should be interpreted with caution, and validation on held-out kinase-
specific data is essential.

### 7.4 Practical Risks

- **Model size**: ESM-2 15B cannot be fine-tuned even on H100 GPUs with LoRA,
  limiting us to 650M or 3B models
- **Ensemble generation cost**: AlphaFlow ensemble generation is expensive (~67h
  for full coverage), though it is a one-time cost
- **Integration complexity**: Adding pLM dependencies increases the project's
  software stack significantly
- **Diminishing returns**: If the 9D features already capture the key state
  differences (which the 10x enrichment result suggests), higher-dimensional
  embeddings may not add proportional value

### 7.5 What We Do NOT Know

- Whether ESM-2/ProstT5 pocket embeddings actually separate EGFR conformational
  states better than 9D features (this is the key experiment to run)
- Whether pre-trained molecular representations improve StateBind's specific MPNN
  task (the 10,466 compound dataset may be large enough for from-scratch training)
- Whether AlphaFold can reliably predict C797S mutant structures in inactive
  conformations
- Whether co-embedding scoring adds value beyond GNINA physics-based docking

---

## 8. Publication Framing

### 8.1 Paper Concept: "Protein Language Models Enhance Conformational State-Aware Molecular Design"

**Target venue**: Nature Computational Science or JCIM

**Main claim**: Replacing hand-crafted 9D pocket features with learned pLM
representations improves state discrimination and downstream enrichment for
conformational state-aware molecular design.

**Narrative**: StateBind demonstrated that state-awareness matters (10x enrichment).
But the state representation was crude (9D hand-crafted). Modern pLMs provide
dramatically richer representations. This paper asks: does representation quality
matter for the state-aware advantage?

**Key figures**:
1. State embedding UMAP: 9D features vs ESM-2 vs ProstT5 -- visualize state
   separation
2. Enrichment comparison: 9D vs pLM-enhanced across retrospective evaluation
3. Mutant structure coverage: Wild-type only vs AlphaFold-predicted mutants
4. Scoring improvement: From-scratch MPNN vs Uni-Mol pre-trained

**Reviewers would attack**:
- ESM-2 cannot distinguish conformational states of the same sequence (addressed
  by ProstT5)
- Benchmark inflation from data leakage (addressed by held-out evaluation)
- Whether the improvement justifies the added complexity
- Whether 9D features are already sufficient (the 10x enrichment suggests yes)

**Minimal baselines needed**:
1. StateBind with 9D features (current pipeline)
2. StateBind with ESM-2 + 9D concatenated features
3. StateBind with ProstT5 structure-conditioned embeddings
4. StateBind with Uni-Mol pre-trained MPNN
5. Static baseline with all enhancements (to confirm state-aware advantage persists)

---

## 9. Prioritized Recommendations

### Tier 1: High Impact, Low Effort (1-2 weeks)
1. **Extract ESM-2 pocket embeddings** for all 16 atlas structures and compare
   state separation to 9D features
2. **Replace MPNN atom features** with Uni-Mol pre-trained embeddings and measure
   R^2 improvement
3. **Benchmark ProstT5 3Di embeddings** for conformational state discrimination

### Tier 2: High Impact, Medium Effort (2-4 weeks)
4. **Predict mutant structures** for C797S, T790M/C797S, L718Q using AF2 with
   MSA subsampling across 4 conformational states
5. **Implement DrugCLIP-style scoring** as additional scoring tier in the cascade
6. **Generate AlphaFlow ensembles** for the 4 representative structures

### Tier 3: High Impact, High Effort (1-2 months)
7. **Train pocket-ligand co-embedding model** specific to EGFR conformational states
8. **Full retrospective evaluation** with pLM-enhanced pipeline vs current pipeline
9. **Extend to resistance mutations**: State-aware design for C797S-mutant EGFR

---

## 10. Connections to Existing Vision System Ideas

### Vision 001: Continuous Conformational Conditioning (DEFERRED)
Our ESM-2/ProstT5 pocket embeddings provide the natural continuous representation
that Vision 001 envisioned. Rather than replacing discrete states with a continuous
manifold of hand-crafted features, we replace them with a continuous manifold of
learned embeddings that inherently capture more information.

### Vision 002: 3D Pocket-Conditioned Diffusion (DEFERRED)
Co-embedding approaches (DrugCLIP, ProFSA) provide an alternative path to pocket-
conditioned generation that does not require full 3D diffusion models. The pocket
embedding could condition a simpler generative model (the existing VAE) rather than
requiring DiffSBDD/TargetDiff.

### Vision 010: Self-Supervised GNN Pre-Training (DEFERRED)
Our research provides concrete evidence that pre-training improves molecular property
prediction by 20-59%. Uni-Mol is the specific model to use, and the integration
architecture is now well-defined.

### Novel Contribution Beyond Vision System
The key new contribution is **ProstT5 for structure-conditioned state embeddings**
and **AlphaFold2 for resistance mutant structure prediction**. Neither was proposed
in the existing vision system, and together they address two of StateBind's most
significant limitations.

---

## References

1. Lin, Z., Akin, H., Rao, R., et al. (2023). Evolutionary-scale prediction of
   atomic-level protein structure with a language model. Science, 379(6637),
   1123-1130.

2. Gao, B., Qiang, B., Tan, H., et al. (2023). DrugCLIP: Contrastive Protein-
   Molecule Representation Learning for Virtual Screening. NeurIPS 2023.

3. Gao, B., Tan, H., Qiang, B., et al. (2025). Deep contrastive learning enables
   genome-wide virtual screening. Science.

4. Gao, B., Huang, T., Wen, Z., et al. (2024). ProFSA: Self-supervised Pocket
   Pretraining via Protein Fragment-Surroundings Alignment. ICLR 2024.

5. Zhou, G., Gao, Z., Ding, Q., et al. (2023). Uni-Mol: A Universal 3D Molecular
   Representation Learning Framework. ICLR 2023.

6. Lu, S., Gao, Z., He, D., et al. (2024). Uni-Mol2: Exploring Molecular
   Pretraining Model at Scale. NeurIPS 2024.

7. Jing, B., Berger, B., & Jaakkola, T. (2024). AlphaFold Meets Flow Matching for
   Generating Protein Ensembles. arXiv:2402.04845.

8. Lu, J., Zhong, B., & Zhang, Z. (2023). Str2Str: A Score-based Framework for
   Zero-shot Protein Conformation Sampling. arXiv:2306.03117.

9. Jumper, J., Evans, R., Pritzel, A., et al. (2021). Highly accurate protein
   structure prediction with AlphaFold. Nature, 596, 583-589.

10. Wayment-Steele, H.K., Ojoawo, A., Otten, R., et al. (2024). High-throughput
    prediction of protein conformational distributions with subsampled AlphaFold2.
    Nature Communications, 15, 2464.

11. Monteiro da Silva, G., Cui, J.Y., Dalgarno, D.C., et al. (2024). Exploring
    kinase DFG loop conformational stability with AlphaFold2-RAVE. J Chem Inf
    Model, 64(7), 2789-2797.

12. Heinzinger, M., Weissenow, K., Rost, B., et al. (2024). Bilingual Language
    Model for Protein Sequence and Structure (ProstT5). NAR Genomics and
    Bioinformatics, 6(4), lqae150.

13. van Linden, O.P.J., Kooistra, A.J., Leurs, R., et al. (2014). KLIFS: A
    Knowledge-Based Structural Database To Navigate Kinase-Ligand Interaction
    Space. J Med Chem, 57(2), 249-277.

14. Pei, Q., Gao, K., Wu, L., et al. (2023). FABind: Fast and Accurate Protein-
    Ligand Binding. NeurIPS 2023.

15. Corsello, A., et al. (2024). DynamicBind: predicting ligand-specific protein-
    ligand complex structure with a deep equivariant generative model. Nature
    Communications, 15, 1071.

16. Abramson, J., Adler, J., Dunger, J., et al. (2024). Accurate structure
    prediction of biomolecular interactions with AlphaFold 3. Nature, 630, 493-500.

17. Fang, X., Liu, L., Lei, J., et al. (2022). Geometry-enhanced molecular
    representation learning for property prediction. Nature Machine Intelligence,
    4, 127-134.

18. Rong, Y., Bian, Y., Xu, T., et al. (2020). Self-Supervised Graph Transformer
    on Large-Scale Molecular Data. NeurIPS 2020.

19. Reveguk, Z., Khrenova, M.G., Friedland, A., et al. (2024). Classifying protein
    kinase conformations with machine learning. Protein Science, 33(4), e4918.

20. Del Alamo, D., Sala, D., McShan, A.C., & Bhatt, D. (2023). Biasing AlphaFold2
    to predict GPCRs and kinases with user-defined functional or structural
    properties. PNAS, 120(13), e2214985120.

21. Wang, X., et al. (2024). MoDAFold: a strategy for predicting the structure of
    missense mutant protein based on AlphaFold2 and molecular dynamics. Briefings
    in Bioinformatics, 25(2), bbae006.

22. Yang, Q., et al. (2026). A survey of downstream applications of evolutionary
    scale modeling protein language models. Quantitative Biology.

23. Jing, B., Corso, G., Chang, J., et al. (2023). EigenFold: Generative Protein
    Structure Prediction with Diffusion Models. ICLR 2023 Workshop on Machine
    Learning for Drug Discovery.

24. EvolutionaryScale (2024). ESM Cambrian: Revealing the mysteries of proteins
    with unsupervised learning. Blog post.

25. Mapping the space of protein binding sites with sequence-based protein language
    models (EPoCS). (2025). PMC/12208174.

26. Heo, L. & Feig, M. (2022). How accurately can one predict drug binding modes
    using AlphaFold models? eLife, 11, e89386.

27. Reau, M., Langenfeld, F., Zagury, J.F., et al. (2023). Investigating the
    conformational landscape of AlphaFold2-predicted protein kinase structures.
    Bioinformatics Advances, 3(1), vbad129.
