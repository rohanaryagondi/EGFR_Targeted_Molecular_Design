# Architecture

**Last updated:** 2026-04-07T00:00:00+00:00
**Briefing session:** 2 (final update)

---

## Pipeline Overview

StateBind is organized as a sequential, acyclic pipeline of 12 Python subpackages.
Data flows downward through 7 phases, from raw inputs to a head-to-head comparison.
Modules communicate exclusively via JSON artifact files on disk — never through
in-memory shared state. This makes the pipeline resumable, debuggable, and allows
any phase to be re-run independently.

---

## The 13 Subpackages

### Infrastructure (shared by all phases)

- **data** — Path resolution, source registry, data manifests, validation. Provides
  a central path resolver that auto-detects the project root and resolves all data
  and artifact paths. No hard-coded paths anywhere in the codebase.

- **utils** — Configuration loading (YAML), JSON I/O helpers, directory management.
  Every module loads its config through this layer.

- **chemistry** — RDKit-backed cheminformatics: Morgan fingerprints, molecular
  descriptors (MW, LogP, HBA, HBD, TPSA, QED), SMILES validation/canonicalization,
  synthetic accessibility scoring, and a lightweight docking proxy MLP. All functions
  degrade gracefully when RDKit is not installed.

### Phase 1: Data Processing

- **processing** — Converts raw curated data (mutations, PDB structures, reference
  ligands) into validated, structured datasets. Handles 18 EGFR resistance mutations,
  16 PDB structures, and 9 reference ligands.

### Phase 2: Static Baseline

- **baselines** — The single-structure pipeline. Uses one PDB structure (1M17,
  active-state EGFR), one pocket definition, and no conformational state information.
  Contains the component scoring functions (reference similarity, drug-likeness,
  docking) that are reused by the unified scorer. Produces 30 candidates.

### Phase 3-5: State-Aware Pipeline

- **structure** — Builds a conformational state atlas by classifying PDB structures
  into the 4 canonical states using 9-dimensional feature vectors (distances, angles,
  dihedral measurements). Extracts pocket descriptors for each state.

- **context** — Predicts which conformational states are relevant for specific
  mutations. Uses a 33-feature representation with 3 model tiers. Key finding: all 17
  curated resistance mutations map to the same state (DFGin/aCin), making the
  mutation-to-state mapping uninformative for the current dataset.

- **dynamics** — Models inter-state transitions as a world model. Computes Markov
  transition matrices and contrastive state embeddings. Represents the probability
  of EGFR transitioning between conformational states.

### Phase 6: Candidate Generation

- **generation** — Generates candidate molecules conditioned on specific conformational
  states. Uses template-based string-modification strategies (36 candidates) plus
  VAE-based generation (395 candidates from trained SELFIES VAE v3). Includes diversity
  computation and candidate filtering. ADMET safety profiling flags liabilities
  (informational only).

### Machine Learning

- **ml** — Contains 3 neural network architectures (VAE, MPNN, ADMET), a shared
  training framework, molecular graph utilities, and SMILES tokenization. All ML
  dependencies (PyTorch, PyTorch Geometric) are optional — the rest of the pipeline
  runs without them. Pydantic configuration classes are always importable regardless
  of whether ML libraries are installed.

### Phase 7: Scoring, Ranking, and Evaluation

- **ranking** — The unified scoring function that scores BOTH pipelines identically.
  Computes 4 weighted components, validates weight constraints, and produces merged
  rankings. This is the heart of the fair comparison.

- **evaluation** — Head-to-head comparison of the two pipelines. Computes overlap
  analysis, diversity comparison, score distributions, top-K composition, novelty
  analysis, and (optionally) statistical hypothesis testing and weight sensitivity
  analysis. Includes visualization for all metrics.

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
      ranking                  [Phase 7a: unified scoring]
         |
     evaluation                [Phase 7b: comparison + statistics]
```

Key dependency relationships:
- **baselines → ranking:** The unified scorer imports component scoring functions
  from baselines (reference similarity, drug-likeness, docking)
- **ml → ranking:** The MPNN affinity predictor provides the top-tier docking score
- **ml → generation:** The VAE produces state-conditioned candidate molecules
- **ml → evaluation:** ADMET predictions feed into safety profiling
- **chemistry → baselines, ranking:** Morgan fingerprints and descriptors upgrade
  scoring components

---

## The Scoring Function

### Unified Scoring (used for the head-to-head comparison)

Both pipelines are scored by the same function with 4 components:

| Component | Weight | How It Works |
|-----------|--------|-------------|
| Reference similarity | 0.35 | Computes Morgan fingerprint (ECFP4, radius 2, 2048 bits) Tanimoto similarity between the candidate and 3 known EGFR drugs (erlotinib, gefitinib, osimertinib). Takes the maximum similarity across the 3 references. Falls back to SMILES character 3-gram Tanimoto when RDKit is unavailable. |
| Drug-likeness | 0.30 | Weighted composite: QED score (50%) + Lipinski violation penalty (25%) + synthetic accessibility score (25%). QED is a quantitative estimate of drug-likeness from 0 to 1. Lipinski checks 4 rules (MW, HBA, HBD, LogP); score = (4 - violations) / 4. SA score ranges 1-10; normalized to 0-1. Falls back to heuristic linear scoring on MW/HBA/HBD/ring count. |
| Docking proxy | 0.20 | Cascading 3-tier fallback. **Tier 1 (active):** MPNN affinity predictor — a 12.7M-param graph neural network trained on 10,466 ChEMBL EGFR compounds (RMSE=0.7182, R²=0.6863, Pearson=0.8323). Predicts pIC50, normalized to [0, 1] via sigmoid((pIC50 - 5) / 2). **Tier 2:** DockingProxy MLP — a lightweight numpy-based neural network trained on 9 known EGFR binders and 25 decoys, using 13 Morgan fingerprint bits + 7 molecular descriptors as input. Fallback when MPNN unavailable. **Tier 3:** Constant 0.5 stub — returns 0.5 for all inputs, zero discriminative power. Last resort. |
| State specificity | 0.15 | Geometric decay based on how many conformational states a candidate appears in. 1 state → 1.0, 2 states → 0.5, 3 states → 0.25, 4 states → 0.0. For the static baseline, this is always 0.0 (no state information). This is the only component where the state-aware pipeline has an advantage. |

**Weight constraint:** All 4 weights must be present and sum to exactly 1.0 (tolerance
1e-4). This is validated at runtime before scoring.

**Composite score:** `sum(component_value * component_weight)` rounded to 4 decimal
places. Higher is better.

### Baseline Scoring (standalone, not used in comparison)

The static baseline has its own scorer with different weights (0.4 / 0.3 / 0.3) and
only 3 components (no state specificity). This exists for Phase 2 standalone runs only.
The unified scorer is what matters for the head-to-head.

---

## ML Model Architectures

### Conditional SMILES VAE

**Purpose:** Generate novel SMILES strings conditioned on a specific conformational state.

**Architecture:** Sequence-to-sequence with a latent bottleneck.
- Encoder: Bidirectional GRU. Input is embedded SMILES tokens concatenated with a
  one-hot conformational state vector (4 dimensions) at every timestep.
- Latent space: The encoder's final hidden state is projected to mean (mu) and log-
  variance (logvar) vectors. A sample z is drawn via the reparameterization trick.
- Decoder: GRU. The latent code z, concatenated with the state vector, is projected
  to initialize the decoder's hidden state. The decoder autoregressively generates
  SMILES tokens with teacher forcing during training.
- Loss: Reconstruction (cross-entropy on token predictions) + KL divergence with
  linear annealing over 20 epochs.
- Key property: The same latent point z decoded with different state vectors produces
  different molecules — this is how state conditioning works.

**Hyperparameters (from config):** vocab_size=150, embed_dim=128, hidden_dim=256,
latent_dim=64, KL weight=0.01 with 20-epoch warmup.

**Status:** Trained. VAE v3 uses SELFIES encoding. 300 epochs on H200. 9.5M params.
99.9% valid, 94.8% unique. 395 candidates generated.

### Affinity MPNN

**Purpose:** Predict binding affinity (pIC50) for a molecule against EGFR. Replaces
the docking proxy stub in the scoring function.

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

**Status:** Trained. 12.7M params. RMSE=0.7182, R²=0.6863, Pearson=0.8323. Active
as tier 1 in the scoring cascade.

### Multi-task ADMET

**Purpose:** Predict 6 drug safety and pharmacokinetic endpoints simultaneously.

**Architecture:** Shared backbone with task-specific heads.
- Backbone: Graph Isomorphism Network (GIN) — multiple GINConv layers with batch
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
informational only — hard filtering rejects ALL kinase inhibitors on hERG.

---

## Configuration System

All parameters are driven by 6 YAML configuration files. No hard-coded thresholds,
paths, or hyperparameters exist in source code.

| Config | Purpose |
|--------|---------|
| default.yaml | Project-level: name, version, paths, logging |
| structure.yaml | PDB references, state classification thresholds |
| context.yaml | Target gene (EGFR), UniProt ID, mutation list |
| vae.yaml | VAE hyperparameters: dimensions, KL annealing schedule |
| mpnn.yaml | MPNN hyperparameters: layers, hidden dims, readout |
| admet.yaml | ADMET hyperparameters: GIN layers, task weights |

Convention: YAML files are structured as `model:` (hyperparameters), `training:`
(epochs, learning rate, device), `data:` (paths, splits). Device `auto` means
auto-detect GPU/CPU.

---

## Data Flow

Modules communicate via JSON artifacts on disk, organized by phase:

```
data/raw/                 → processing scripts →  data/processed/
data/processed/           → baseline scripts   →  artifacts/baselines/
data/processed/           → structure scripts  →  artifacts/structure/
data/processed/           → context scripts    →  artifacts/context/
artifacts/structure/      → dynamics scripts   →  artifacts/dynamics/
data/processed/           → training scripts   →  artifacts/models/{vae,mpnn,admet}/
artifacts/structure/      → generation scripts →  artifacts/generation/
artifacts/baselines/ +
artifacts/generation/     → ranking scripts    →  artifacts/ranking/
artifacts/ranking/        → evaluation scripts →  artifacts/evaluation/ + reports/
```

Every artifact file includes a `generated_at` timestamp and a `notes` field for
human-readable context. This makes the pipeline fully traceable — you can always
determine when and why an artifact was produced.

---

## Key Design Principles

1. **Acyclic dependencies.** The module graph has no cycles. Imports always flow
   downward. Shared types live in infrastructure modules (data, utils).

2. **Optional everything.** ML libraries (torch, torch_geometric), chemistry libraries
   (RDKit), and science libraries (scipy, scikit-learn) are all optional. The core
   pipeline runs on just numpy, pandas, pyyaml, pydantic, typer, and rich.

3. **Graceful degradation.** Every function that uses an optional dependency has a
   defined fallback: Morgan → n-gram, QED → heuristic, MPNN → proxy → stub,
   ADMET → permissive pass, validation → permissive True.

4. **Pydantic at boundaries.** All data crossing module boundaries is modeled as
   Pydantic BaseModel subclasses with validation, serialization, and type safety.
   Internal-only data uses dataclasses.

5. **Config-driven.** Zero hard-coded parameters. Everything is loaded from YAML at
   runtime and can be overridden via CLI arguments.
