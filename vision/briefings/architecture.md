# Architecture

**Last updated:** 2026-04-07T20:00:00+00:00
**Briefing session:** 3

---

## Changes Since Last Briefing (Session 2)

- **Docking cascade expanded to 4 tiers:** GNINA physics-based docking added as tier 0
  (GPU-only, Vina + CNN scoring, normalized via sigmoid(-vina_score / 3))
- **New modules added:** chemistry/docking (GNINA wrapper), ranking/pareto (Pareto front,
  hypervolume), evaluation/pareto_comparison (pipeline comparison), evaluation/
  docking_analysis (state-specific docking), evaluation/retrospective (time-split
  validation)
- **Config system expanded:** 6 to 12 YAML files (added docking, retrospective, and 4
  pre-cutoff model configs)
- **ComparativeResult extended:** Now includes `pareto` (always populated if numpy
  available) and `retrospective` (optional) fields alongside existing statistical tests

---

## Pipeline Overview

StateBind is organized as a sequential, acyclic pipeline of 12 Python subpackages.
Data flows downward through 7 phases, from raw inputs to a head-to-head comparison.
Modules communicate exclusively via JSON artifact files on disk -- never through
in-memory shared state. This makes the pipeline resumable, debuggable, and allows
any phase to be re-run independently.

---

## The 12 Subpackages

### Infrastructure (shared by all phases)

- **data** -- Path resolution, source registry, data manifests, validation. Provides
  a central path resolver that auto-detects the project root and resolves all data
  and artifact paths. No hard-coded paths anywhere in the codebase.

- **utils** -- Configuration loading (YAML), JSON I/O helpers, directory management.
  Every module loads its config through this layer.

- **chemistry** -- RDKit-backed cheminformatics: Morgan fingerprints, molecular
  descriptors (MW, LogP, HBA, HBD, TPSA, QED), SMILES validation/canonicalization,
  synthetic accessibility scoring, a lightweight docking proxy MLP, and a GNINA
  docking wrapper. The GNINA wrapper provides physics-based docking against prepared
  EGFR receptor structures. All chemistry functions degrade gracefully when RDKit is
  not installed; GNINA functions degrade when the binary or GPU is unavailable.

### Phase 1: Data Processing

- **processing** -- Converts raw curated data (mutations, PDB structures, reference
  ligands) into validated, structured datasets. Handles 18 EGFR resistance mutations,
  16 PDB structures, and 9 reference ligands.

### Phase 2: Static Baseline

- **baselines** -- The single-structure pipeline. Uses one PDB structure (1M17,
  active-state EGFR), one pocket definition, and no conformational state information.
  Contains the component scoring functions (reference similarity, drug-likeness,
  docking) that are reused by the unified scorer. Produces 30 candidates.

### Phase 3-5: State-Aware Pipeline

- **structure** -- Builds a conformational state atlas by classifying PDB structures
  into the 4 canonical states using 9-dimensional feature vectors (distances, angles,
  dihedral measurements). Extracts pocket descriptors for each state.

- **context** -- Predicts which conformational states are relevant for specific
  mutations. Uses a 33-feature representation with 3 model tiers. Key finding: all 17
  curated resistance mutations map to the same state (DFGin/aCin), making the
  mutation-to-state mapping uninformative for the current dataset.

- **dynamics** -- Models inter-state transitions as a world model. Computes Markov
  transition matrices and contrastive state embeddings. Represents the probability
  of EGFR transitioning between conformational states.

### Phase 6: Candidate Generation

- **generation** -- Generates candidate molecules conditioned on specific conformational
  states. Uses template-based string-modification strategies (36 candidates) plus
  VAE-based generation (395 candidates from trained SELFIES VAE v3). Includes diversity
  computation and candidate filtering. ADMET safety profiling flags liabilities
  (informational only).

### Machine Learning

- **ml** -- Contains 3 neural network architectures (VAE, MPNN, ADMET), a shared
  training framework, molecular graph utilities, and SMILES tokenization. All ML
  dependencies (PyTorch, PyTorch Geometric) are optional -- the rest of the pipeline
  runs without them. Pydantic configuration classes are always importable regardless
  of whether ML libraries are installed.

### Phase 7: Scoring, Ranking, and Evaluation

- **ranking** -- The unified scoring function that scores BOTH pipelines identically.
  Computes 4 weighted components, validates weight constraints, and produces merged
  rankings. Also contains Pareto front computation: non-dominated sorting, hypervolume
  calculation (via pymoo or numpy fallback), and crowding distance for multi-objective
  evaluation without weight assumptions.

- **evaluation** -- Head-to-head comparison of the two pipelines. Computes overlap
  analysis, diversity comparison, score distributions, top-K composition, novelty
  analysis, statistical hypothesis testing, weight sensitivity analysis, Pareto
  front comparison (hypervolume, dominance fractions), state-specific docking analysis,
  and retrospective time-split validation (enrichment factors against held-out drugs).
  Includes visualization for all metrics.

---

## Dependency Graph

Dependencies flow strictly downward. No circular imports exist.

```
data + utils + chemistry        [Infrastructure: always available]
         |
    processing                  [Phase 1: raw -> structured]
    /    |    \
baselines  structure  context   [Phases 2-4: independent pipelines]
    |        |          |
    |     dynamics              [Phase 5: state transitions]
    |        |
    +--------+
         |
        ml                     [ML: optional neural networks]
       / | \
      /  |  \
generation  |                  [Phase 6: candidate production]
      \  |  /
       \ | /
      ranking                  [Phase 7a: unified scoring + Pareto]
         |
     evaluation                [Phase 7b: comparison + statistics +
                                retrospective + docking analysis]
```

Key dependency relationships:
- **baselines -> ranking:** The unified scorer imports component scoring functions
  from baselines (reference similarity, drug-likeness, docking)
- **ml -> ranking:** The MPNN affinity predictor provides tier 1 docking scores
- **ml -> generation:** The VAE produces state-conditioned candidate molecules
- **ml -> evaluation:** ADMET predictions feed into safety profiling
- **chemistry -> ranking:** GNINA provides tier 0 physics-based docking scores;
  Morgan fingerprints and descriptors upgrade scoring components

---

## The Scoring Function

### Unified Scoring (used for the head-to-head comparison)

Both pipelines are scored by the same function with 4 components:

| Component | Weight | How It Works |
|-----------|--------|-------------|
| Reference similarity | 0.35 | Computes Morgan fingerprint (ECFP4, radius 2, 2048 bits) Tanimoto similarity between the candidate and 3 known EGFR drugs (erlotinib, gefitinib, osimertinib). Takes the maximum similarity across the 3 references. Falls back to SMILES character 3-gram Tanimoto when RDKit is unavailable. |
| Drug-likeness | 0.30 | Weighted composite: QED score (50%) + Lipinski violation penalty (25%) + synthetic accessibility score (25%). QED is a quantitative estimate of drug-likeness from 0 to 1. Lipinski checks 4 rules (MW, HBA, HBD, LogP); score = (4 - violations) / 4. SA score ranges 1-10; normalized to 0-1. Falls back to heuristic linear scoring on MW/HBA/HBD/ring count. |
| Docking proxy | 0.20 | Cascading 4-tier fallback (see below). |
| State specificity | 0.15 | Geometric decay based on how many conformational states a candidate appears in. 1 state -> 1.0, 2 states -> 0.5, 3 states -> 0.25, 4 states -> 0.0. For the static baseline, this is always 0.0 (no state information). This is the only component where the state-aware pipeline has an advantage. |

### Docking Cascade (4 Tiers)

The docking score is computed by a cascading fallback chain. Each tier is attempted in
order; the first available tier provides the score.

| Tier | Method | Requirements | Score Normalization | Quality |
|------|--------|-------------|-------------------|---------|
| 0 | GNINA physics-informed docking | GPU available, GNINA binary at bin/gnina, PDBQT receptor prepared | sigmoid(-vina_score / 3) maps kcal/mol to [0,1] | Physics-based. Vina energy + CNN binding prediction. Validated: binders -7.32 kcal/mol vs non-binders -4.16 (delta -3.16). |
| 1 | MPNN affinity predictor | Trained checkpoint + PyTorch available | sigmoid((pIC50 - 5) / 2) maps pIC50 to [0,1] | Learned proxy. 12.7M params, RMSE=0.7182, R^2=0.6863, Pearson=0.8323 on 10,466 ChEMBL EGFR compounds. |
| 2 | DockingProxy MLP | Trained + RDKit available | Sigmoid output (built into MLP) | Lightweight proxy trained on 9 binders + 25 decoys using 13 Morgan fingerprint bits + 7 molecular descriptors. Overfits to small training set. |
| 3 | Constant 0.5 stub | Always | Returns 0.5 | Zero discriminative power. Last resort. |

A GPU guard function checks for CUDA availability before attempting GNINA. This prevents
slow CPU docking from blocking the cascade on login nodes or in test environments.

**Weight constraint:** All 4 weights must be present and sum to exactly 1.0 (tolerance
1e-4). This is validated at runtime before scoring.

**Composite score:** `sum(component_value * component_weight)` rounded to 4 decimal
places. Higher is better.

### Pareto Multi-Objective Analysis

In addition to the weighted-sum scoring, the pipeline performs Pareto front analysis
on the raw component scores (without weight assumptions):

- **Non-dominated sorting:** Identifies candidates that are not dominated on any
  objective (O(n^2) algorithm, suitable for <1000 candidates)
- **Hypervolume computation:** Uses pymoo (primary) or numpy fallback (2D exact,
  >2D Monte Carlo) to measure the volume of objective space dominated by each
  pipeline's Pareto front
- **Crowding distance:** Measures diversity along the Pareto front
- **Pipeline comparison:** Computes hypervolume ratio, dominance fraction, and
  per-objective front ranges for both pipelines

This provides a weight-free comparison: which pipeline explores a larger region of the
multi-objective trade-off space?

### Baseline Scoring (standalone, not used in comparison)

The static baseline has its own scorer with different weights (0.4 / 0.3 / 0.3) and
only 3 components (no state specificity). This exists for Phase 2 standalone runs only.
The unified scorer is what matters for the head-to-head.

---

## ML Model Architectures

### Conditional SELFIES VAE

**Purpose:** Generate novel SMILES strings conditioned on a specific conformational state.

**Architecture:** Sequence-to-sequence with a latent bottleneck.
- Encoder: Bidirectional GRU. Input is embedded SELFIES tokens concatenated with a
  one-hot conformational state vector (4 dimensions) at every timestep.
- Latent space: The encoder's final hidden state is projected to mean (mu) and log-
  variance (logvar) vectors. A sample z is drawn via the reparameterization trick.
- Decoder: GRU. The latent code z, concatenated with the state vector, is projected
  to initialize the decoder's hidden state. The decoder autoregressively generates
  tokens with teacher forcing during training.
- Loss: Reconstruction (cross-entropy on token predictions) + KL divergence with
  linear annealing over 20 epochs.
- Key property: The same latent point z decoded with different state vectors produces
  different molecules -- this is how state conditioning works.
- SELFIES encoding guarantees that every generated token sequence decodes to a valid
  molecule (99.9% validity vs 0% with raw SMILES encoding).

**Hyperparameters (from config):** vocab_size=150, embed_dim=128, hidden_dim=256,
latent_dim=64, KL weight=0.01 with 20-epoch warmup.

**Status:** Trained. VAE v3 uses SELFIES encoding. 300 epochs on H200 (31 min). 9.5M
params. 99.9% valid, 94.8% unique. 395 candidates generated. Two pre-cutoff versions
also trained (pre-2010 and pre-2015) for retrospective validation.

### Affinity MPNN

**Purpose:** Predict binding affinity (pIC50) for a molecule against EGFR. Serves as
tier 1 in the docking cascade.

**Architecture:** Graph neural network with message passing.
- Input: Molecular graph where atoms are nodes (35-dimensional feature vector) and
  bonds are edges (11-dimensional feature vector).
- Message passing: Multiple NNConv layers with residual connections and batch
  normalization. Each layer learns an edge-conditioned message function.
- Readout: Concatenation of global mean pooling and global max pooling across all
  atoms, producing a fixed-size graph representation.
- Prediction head: 2-layer MLP mapping the graph representation to a single pIC50
  value (continuous).
- Output normalization: sigmoid((pIC50 - 5) / 2) maps to [0, 1] for scoring.

**Hyperparameters (from config):** hidden_dim=128, 3 message-passing layers,
mean_max readout.

**Training data:** 10,466 ChEMBL EGFR compounds with pIC50 values (range 4.0-11.0).
Originally 1,678 before a pagination fix expanded the dataset.

**Status:** Trained. 12.7M params. RMSE=0.7182, R^2=0.6863, Pearson=0.8323. Active
as tier 1 in the scoring cascade. Two pre-cutoff versions also trained: pre-2010
(2,974 compounds, R^2=0.717) and pre-2015 (4,852 compounds, R^2=0.690).

### Multi-task ADMET

**Purpose:** Predict 6 drug safety and pharmacokinetic endpoints simultaneously.

**Architecture:** Shared backbone with task-specific heads.
- Backbone: Graph Isomorphism Network (GIN) -- multiple GINConv layers with batch
  normalization, ReLU, and dropout.
- Readout: Same mean+max pooling scheme as the MPNN.
- Shared projection: Linear layer reducing the graph representation.
- Task heads: 6 independent 2-layer MLPs, one per endpoint.
- The 6 endpoints:
  - Caco-2 permeability (regression)
  - hERG channel inhibition (classification, safety-critical, 1.5x loss weight)
  - CYP3A4 metabolic inhibition (classification)
  - Hepatic clearance (regression)
  - Lipophilicity (regression)
  - Aqueous solubility (regression)
- Loss: Weighted sum of MSE (regression tasks) and BCE (classification tasks).

**Training data:** 27,698 molecules from Therapeutics Data Commons (TDC) ADMET benchmarks
covering 6 endpoints.

**Status:** Trained. 187K params. hERG AUROC=0.7745, CYP3A4 AUROC=0.7323. Used
informational only -- hard filtering rejects ALL kinase inhibitors on hERG (a known
class liability for kinase inhibitors).

---

## Configuration System

All parameters are driven by 12 YAML configuration files. No hard-coded thresholds,
paths, or hyperparameters exist in source code.

| Config | Purpose |
|--------|---------|
| default.yaml | Project-level: name, version, paths, logging |
| structure.yaml | PDB references, state classification thresholds |
| context.yaml | Target gene (EGFR), UniProt ID, mutation list |
| vae.yaml | VAE hyperparameters: dimensions, KL annealing schedule |
| mpnn.yaml | MPNN hyperparameters: layers, hidden dims, readout |
| admet.yaml | ADMET hyperparameters: GIN layers, task weights |
| docking.yaml | GNINA config: binary path, exhaustiveness, box size, state receptor map |
| retrospective.yaml | Cutoff years, enrichment thresholds, reference binder config |
| mpnn_pre2010.yaml | MPNN hyperparameters for pre-2010 retrospective training |
| mpnn_pre2015.yaml | MPNN hyperparameters for pre-2015 retrospective training |
| vae_pre2010.yaml | VAE hyperparameters for pre-2010 retrospective training |
| vae_pre2015.yaml | VAE hyperparameters for pre-2015 retrospective training |

Convention: YAML files are structured as `model:` (hyperparameters), `training:`
(epochs, learning rate, device), `data:` (paths, splits). Device `auto` means
auto-detect GPU/CPU.

---

## Data Flow

Modules communicate via JSON artifacts on disk, organized by phase:

```
data/raw/                 -> processing scripts ->  data/processed/
data/processed/           -> baseline scripts   ->  artifacts/baselines/
data/processed/           -> structure scripts  ->  artifacts/structure/
data/processed/           -> context scripts    ->  artifacts/context/
artifacts/structure/      -> dynamics scripts   ->  artifacts/dynamics/
data/processed/           -> training scripts   ->  artifacts/models/{vae,mpnn,admet}/
data/processed/           -> docking prep       ->  data/processed/docking/receptors/
artifacts/structure/      -> generation scripts ->  artifacts/generation/
artifacts/baselines/ +
artifacts/generation/     -> ranking scripts    ->  artifacts/ranking/
artifacts/ranking/        -> evaluation scripts ->  artifacts/evaluation/ + reports/
data/processed/ +
artifacts/models/         -> retro scripts      ->  artifacts/evaluation/retrospective/
```

Every artifact file includes a `generated_at` timestamp and a `notes` field for
human-readable context. This makes the pipeline fully traceable -- you can always
determine when and why an artifact was produced.

---

## Evaluation Framework

The head-to-head comparison computes metrics at multiple levels:

1. **Overlap analysis** -- SMILES-level comparison (shared, unique counts, Jaccard index)
2. **Diversity comparison** -- Internal diversity (mean pairwise Tanimoto distance) per pipeline
3. **Score distribution** -- Mean, median, std, min, max per pipeline with delta
4. **Top-K dominance** -- Which pipeline owns positions in global top-K
5. **Novelty detection** -- Candidates unique to state-aware pipeline
6. **Mean ranks** -- Average rank per pipeline in merged ranking
7. **Statistical testing** -- Mann-Whitney U, bootstrap CI, Cohen's d, weight sensitivity
8. **Pareto analysis** -- Hypervolume comparison, dominance fraction, Pareto front plots
9. **Retrospective validation** -- Enrichment factors against held-out approved drugs at time-split cutoffs

All metrics are computed identically for both pipelines, ensuring fair comparison.

---

## Key Design Principles

1. **Acyclic dependencies.** The module graph has no cycles. Imports always flow
   downward. Shared types live in infrastructure modules (data, utils).

2. **Optional everything.** ML libraries (torch, torch_geometric), chemistry libraries
   (RDKit), science libraries (scipy, scikit-learn), and docking software (GNINA) are
   all optional. The core pipeline runs on just numpy, pandas, pyyaml, pydantic,
   typer, and rich.

3. **Graceful degradation.** Every function that uses an optional dependency has a
   defined fallback: GNINA -> MPNN -> proxy -> stub for docking, Morgan -> n-gram
   for fingerprints, QED -> heuristic for drug-likeness, ADMET -> permissive pass,
   pymoo -> numpy for hypervolume.

4. **Pydantic at boundaries.** All data crossing module boundaries is modeled as
   Pydantic BaseModel subclasses with validation, serialization, and type safety.
   Internal-only data uses dataclasses.

5. **Config-driven.** Zero hard-coded parameters. Everything is loaded from YAML at
   runtime and can be overridden via CLI arguments.

6. **Environment-aware execution.** The scoring cascade adapts to the execution
   environment: GNINA activates only on GPU nodes, MPNN activates only with trained
   checkpoints, and the pipeline produces valid (if less informative) results on any
   machine with just the core dependencies.
