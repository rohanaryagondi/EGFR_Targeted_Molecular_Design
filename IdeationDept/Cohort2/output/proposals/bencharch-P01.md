---
agent: Maverick Benchmark Architect
round: 2
date: 2026-04-09
type: proposal
proposal_id: bencharch-P01
title: "StateBind-Bench: The First Benchmark for Conformational State-Conditioned Molecular Generation"
---

# Proposal: StateBind-Bench -- The First Benchmark for Conformational State-Conditioned Molecular Generation

## Proposing Agent

Maverick Benchmark Architect -- expertise in reproducible benchmark design, community challenge architecture, open-science infrastructure, and meta-evaluation of computational biology evaluation frameworks.

## Problem Statement

The molecular generation field evaluates new methods against benchmarks that completely ignore protein conformational dynamics. CrossDocked2020 treats every pocket as a static snapshot. MOSES and GuacaMol measure distributional statistics of generated SMILES with no pocket conditioning at all. MoleculeNet tests property prediction on molecules averaging 204 Da -- irrelevant to real drug candidates. TDC's 2026 reproducibility audit found only 3 of the top-ranked ADMET methods were reproducible (bioRxiv, 2026). Meanwhile, the field is moving toward dynamics-aware molecular design: kinases occupy multiple conformational states (DFG-in/out, aC-helix-in/out), and state-appropriate drug design is critical for overcoming resistance. No existing benchmark can measure whether a generative model exploits this information.

This gap is not merely academic. Structure-based drug design papers routinely claim improvements on CrossDocked2020, yet none demonstrate that their models respond meaningfully to conformational state changes in the same target. The community cannot evaluate a capability it has no metric for. A benchmark that fills this gap would define a new evaluation axis, attract citations from every group working on conformation-aware generation, and establish StateBind as the reference standard for this capability.

## Vision

StateBind-Bench becomes the CrossDocked2020 of conformational-state-conditioned molecular generation: the standard dataset and evaluation framework that every new method in this space must report against. Within 3 years, any paper proposing a dynamics-aware generative model cites StateBind-Bench. Within 5 years, the benchmark has accumulated 500-1,000 citations and expanded to 5+ kinase targets, with community challenges running annually.

The concrete deliverable is a fully open benchmark comprising: (1) curated multi-state pocket structures with state labels, (2) four evaluation tasks with precisely defined metrics, (3) baseline results from 5+ published generative methods, (4) a reproducibility package with Docker/Singularity containers, and (5) a leaderboard for community submissions. The benchmark ships with a companion paper for JCIM (primary) or NeurIPS Evaluations and Datasets Track (secondary).

---

## Background and Evidence

### Key Evidence

1. **Verified benchmark gap.** A systematic search across all major benchmark databases and literature (MoleculeNet, MOSES, GuacaMol, TDC, CrossDocked2020, DUD-E, PDBbind, Tartarus, Polaris, Kinase-Bench, Durian, GenBench3D) confirmed that no existing benchmark evaluates molecular generation conditioned on protein conformational state. The closest work is KLIFS (kinase structure database with state annotations) and CrossDocked2020 (multiple structures but no state labels). Neither constitutes a generation benchmark.

2. **Benchmark papers command outsized citation impact.** MoleculeNet has 3,000+ citations in 8 years (~400/year). DUD-E has 2,500+ in 14 years. MOSES has 770+ in 6 years. GuacaMol has 700+ in 7 years. TDC has 500+ in 5 years. By contrast, a typical methods paper in the same journals accumulates 50-200 citations total (Wu et al., 2018; Polykovskiy et al., 2020; Brown et al., 2019; Huang et al., 2021).

3. **StateBind's 10x enrichment is a headline result.** The existing pipeline shows EF@10 of 4.95-7.72 for state-aware versus 0.47-0.79 for static design -- an order-of-magnitude retrospective enrichment improvement. This is the kind of result that anchors a benchmark paper: it demonstrates that state conditioning produces a measurable difference, justifying the need for a benchmark that measures it (StateBind evaluation artifacts, 2025-2026).

4. **Existing 3D generators largely fail on conformation quality.** GenBench3D (Baillif et al., 2024) found that only 0-11% of molecules from 6 major 3D generators have valid 3D conformations. Durian (Nie et al., 2024) showed no single method dominates across all metrics. This means a state-conditioned benchmark will expose further capability gaps, which is exactly what a good benchmark should do.

5. **Reproducibility crisis demands a new standard.** TDC's 2026 audit found most top-ranked methods non-reproducible: missing code, broken environments, runtime failures, methodological flaws (bioRxiv, 2026). PDBbind suffers severe train-test leakage; CleanSplit retraining drops all top model performance substantially (Nature Machine Intelligence, 2025). The field needs benchmarks built from the ground up with reproducibility as a design constraint.

6. **Community challenges amplify impact.** SAMPL has run for 18 years with cumulative participation from hundreds of groups. CACHE's first challenge attracted 23 groups and 1,955 predicted molecules, with experimental validation producing a 3.7% hit rate (Bender et al., JCIM 2024). DREAM challenges have produced 60+ crowdsourced studies and papers in Nature Methods, Cell Systems, and similar venues (Saez-Rodriguez et al., Cell Systems 2021).

7. **NeurIPS E&D Track validates benchmark-as-contribution.** The 2026 track explicitly states that "evaluation as an object of scientific study in its own right" is welcomed, and papers that "articulate their evaluative role" rather than merely compiling data are favored (NeurIPS 2025 D&B chairs' blog post; NeurIPS 2026 Call for Papers).

### Relationship to Existing Work

- **StateBind current state:** The project has a complete computational pipeline: 4-state EGFR atlas (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout), SELFIES VAE (99.9% validity), MPNN scoring (R^2=0.69), ADMET prediction (hERG AUROC=0.77), unified scoring function with Pareto optimization, time-split retrospective validation, and 646 passing tests. The infrastructure for a benchmark already exists -- it needs to be packaged, documented, and opened.

- **Vision System ideas:** This proposal relates to but does not duplicate Vision System ideas. Idea 001 (continuous conformations) and Idea 005 (ML integration, implemented) provide upstream capabilities. This proposal addresses a downstream need the Vision System did not cover: releasing StateBind as a community benchmark resource. The Vision System focused on improving the pipeline; this proposal focuses on making the pipeline's evaluation framework a shared community artifact.

- **Literature precedent:** CrossDocked2020 (Francoeur et al., 2020) established the pattern: package an existing dataset with evaluation code and baselines, release openly, and watch the community adopt it. That paper has 300+ citations. GuacaMol (Brown et al., 2019) did the same for goal-directed generation. StateBind-Bench follows this established playbook but targets an unclaimed niche.

---

## Proposed Approach

### Overview

StateBind-Bench is a four-task benchmark for evaluating molecular generative models on their ability to produce conformational-state-appropriate molecules for kinase targets. The benchmark ships as a HuggingFace dataset + GitHub evaluation package + Zenodo archive, with Docker/Singularity containers for full reproducibility. Phase 1 (EGFR, 4 states) is a self-contained release targeting JCIM. Phase 2 (multi-kinase: ABL1, BRAF) extends to a NeurIPS E&D Track submission. Phase 3 is a community challenge modeled on SAMPL/DREAM.

The central evaluative claim is: **conformational state-conditioned generation is a distinct capability that existing benchmarks cannot measure, and StateBind-Bench is the first framework to measure it.**

### Implementation Steps

#### Step 1: Data Package Assembly (Weeks 1-2)

Assemble and validate the core dataset from existing StateBind artifacts and public databases.

**Structures:**
- 4 EGFR pocket structures (one representative per DFG/aC state) in PDB and PDBQT format
- Source: curated from PDB via KLIFS state annotations
- Each pocket defined by residues within 6 angstroms of co-crystallized ligand
- Full protein structures for context; extracted pockets for generation input

**Features:**
- 9-dimensional state feature vectors from StateBind's structure atlas (structure/features.py)
- KLIFS 85-residue interaction fingerprints per state
- Pocket volume, shape descriptors, and pharmacophoric features

**Bioactivity data:**
- ChEMBL 34 EGFR inhibitor activity data (IC50, Ki, Kd)
- Standardized to pIC50 using ChEMBL's standardization pipeline
- State annotations derived from co-crystal structures where available
- Time-split labels: pre-2010 training, 2010-2015 validation, post-2015 test

**Known drugs with state annotations:**
- Erlotinib, gefitinib (Type I, DFGin_aCin preferring)
- Lapatinib (Type I1/2, DFGin_aCout preferring)
- Osimertinib (covalent, Type I)
- Each annotated with first-reported year, approval date, mechanism, IC50

**Formats:**
- Structures: PDB, PDBQT, SDF (for pocket atoms)
- Molecules: SMILES, InChI, SELFIES, SDF (3D)
- Metadata: JSON (machine-readable) + YAML (human-readable)
- Splits: CSV with columns [smiles, split, year, pIC50, state_label]

#### Step 2: Define Four Benchmark Tasks (Week 2)

**Task 1: State-Conditioned Generation Quality**
- Input: pocket structure + state label for one of 4 EGFR states
- Output: 1,000 generated molecules per state (4,000 total)
- Primary metrics:
  - GNINA docking score (CNN affinity, kcal/mol) per state
  - QED (drug-likeness, 0-1 continuous)
  - SA score (synthetic accessibility, 1-10, lower is better)
  - Validity rate (fraction of chemically valid molecules)
  - Uniqueness rate (fraction of unique molecules in generated set)
  - Diversity (average pairwise Tanimoto distance, ECFP4)
- Success criterion: At least one baseline method achieves mean GNINA CNN affinity better than -6.0 kcal/mol across all 4 states, with validity >90% and uniqueness >80%

**Task 2: State Specificity**
- Input: same as Task 1 (generate for each of 4 states)
- Output: state specificity metrics per molecule and per method
- Primary metrics:
  - State Specificity Index (SSI): for each molecule, SSI = std_dev(docking_scores_across_4_states) / mean(|docking_scores_across_4_states|). Higher SSI means the molecule is more state-specific.
  - Cross-state docking matrix: 4x4 matrix where entry (i,j) = mean docking score of molecules designed for state i when docked into state j pocket
  - Diagonal dominance ratio: fraction of molecules where the designed-for state gives the best docking score
  - State-conditional enrichment: for each state, EF@10% of generated molecules vs. random
- Success criterion: state-aware methods achieve diagonal dominance ratio >0.5 (i.e., molecules dock best into the state they were designed for more than half the time); state-blind methods expected to show diagonal dominance near 0.25 (chance level)

**Task 3: Retrospective Enrichment**
- Input: training set of known EGFR binders reported before the cutoff year
- Output: generated and scored molecules ranked by unified scoring function
- Evaluation: recovery of post-cutoff approved drugs in top-ranked generated sets
- Primary metrics:
  - EF@1%, EF@5%, EF@10% (enrichment factor at given percentile)
  - AUROC for distinguishing post-cutoff actives from generated decoys
  - Precision@K for K = 10, 50, 100
- Time splits:
  - Split A: train on pre-2010 data, evaluate on 2010-2020 drugs
  - Split B: train on pre-2015 data, evaluate on 2015-2025 drugs
- Success criterion: state-aware pipeline achieves EF@10 >= 3.0 (StateBind's existing result is 4.95-7.72); static baseline expected at EF@10 ~0.5-0.8
- Note: small N (3-5 drugs per split) demands bootstrap confidence intervals reported over 1,000 resamples

**Task 4: Multi-Objective Pareto Optimization**
- Input: pocket structures + scoring function with configurable weights
- Output: Pareto-optimal molecule sets under the multi-objective scoring function
- Primary metrics:
  - Pareto hypervolume (higher = better coverage of objective space)
  - Dominated fraction (fraction of generated molecules that are Pareto-dominated)
  - Score distribution entropy (higher = better exploration of trade-offs)
  - Weight sensitivity: performance under 100 Dirichlet-sampled weight configurations
- Default scoring weights:
  - Docking: 0.35, Drug-likeness: 0.20, ADMET: 0.15, SA: 0.15, State specificity: 0.15
- Success criterion: Pareto hypervolume improvement of at least 10% for state-aware methods over state-blind methods under default weights

#### Step 3: Run Baseline Methods (Weeks 3-5)

Run 6 baseline methods on all 4 tasks. Each baseline generates 1,000 molecules per EGFR state.

| Baseline | Type | Source | Implementation Plan |
|----------|------|--------|-------------------|
| StateBind VAE | SELFIES VAE (project's own) | Existing codebase | Run as-is with state-conditioned latent sampling; already integrated |
| REINVENT 4 | RL + Transformer (SMILES) | GitHub: MolecularAI/REINVENT4 | Install from pip; configure scoring function to use GNINA docking per-state pocket; use transfer learning mode with pre-trained prior |
| DiffSBDD | 3D equivariant diffusion | GitHub: arneschneuing/DiffSBDD | Clone repo; provide each state's pocket PDB as conditioning input; generate 3D molecules; convert to SMILES for scoring |
| TargetDiff | 3D diffusion | GitHub: guanjq/targetdiff | Clone repo; same pocket-conditioning protocol as DiffSBDD; use pre-trained CrossDocked2020 checkpoint |
| Pocket2Mol | Autoregressive 3D GNN | GitHub: pengxingang/Pocket2Mol | Clone repo; feed pocket atoms as conditioning; use pre-trained checkpoint from CrossDocked2020 |
| Random baseline | Uniform sampling from ChEMBL drug-like space | Custom script | Sample 1,000 molecules from ChEMBL drug-like subset (MW 250-600, LogP -2 to 5); no pocket conditioning. This is the "no-information" baseline |

**Fair comparison protocol:**
- All methods receive identical pocket structures in their required input format
- All generated molecules scored by the same evaluation pipeline (GNINA docking + StateBind unified scoring)
- Same drug-likeness filters applied post-generation: Lipinski rule of 5, PAINS substructure filter, REOS reactivity filter
- State-blind control: each structure-based method also run on a single "canonical" EGFR structure (PDB 1M17, the static baseline pocket) to measure whether state conditioning helps
- Random seeds: 3 independent runs per method; report mean and standard deviation
- Compute budget reported: wall-clock time and GPU hours per method

#### Step 4: Evaluation Pipeline and Leaderboard (Weeks 4-5)

**Evaluation package:**
- Standalone Python package: `statebind-bench` (separate from main statebind, installable via `pip install statebind-bench`)
- Core dependencies only: numpy, pandas, rdkit, scipy
- Optional GNINA integration for docking (with pre-computed score fallback for users without GNINA)
- Entry point: `statebind-bench evaluate --submission submission.csv --task {1,2,3,4} --output results.json`
- Submission format: CSV with columns [smiles, designed_for_state, optional_3d_sdf_path]
- Output format: JSON with per-molecule scores and aggregate metrics

**Leaderboard design:**
- Platform: PapersWithCode (primary) + HuggingFace Spaces (secondary)
- PapersWithCode: register 4 tasks as separate benchmarks under a "StateBind-Bench" parent page; each task has its own metric and leaderboard
- HuggingFace Spaces leaderboard (Streamlit app): accepts JSON submission upload, runs evaluation offline, displays results table sortable by any metric
- Submission format for leaderboard:
  ```json
  {
    "method_name": "MyMethod",
    "paper_url": "https://arxiv.org/abs/...",
    "code_url": "https://github.com/...",
    "task_1_results": {
      "EGFR_DFGin_aCin": {"smiles": ["..."], "scores": [...]},
      "EGFR_DFGin_aCout": {"smiles": ["..."], "scores": [...]},
      "EGFR_DFGout_aCin": {"smiles": ["..."], "scores": [...]},
      "EGFR_DFGout_aCout": {"smiles": ["..."], "scores": [...]}
    }
  }
  ```
- Anti-gaming measures: (a) report full score distributions, not just means; (b) include a hidden held-out metric (not disclosed) to detect overfitting to public metrics; (c) require code URL for every submission; (d) rotate scoring function weights quarterly

#### Step 5: Infrastructure and Reproducibility Package (Weeks 5-6)

**HuggingFace dataset:**
- Dataset ID: `statebind/statebind-bench`
- Configs: `egfr-structures`, `egfr-actives`, `egfr-splits`, `scoring-weights`
- Auto-generated Croissant metadata (HuggingFace generates this automatically)
- RAI (Responsible AI) fields: intended use, known limitations, data provenance
- Loading: `from datasets import load_dataset; ds = load_dataset("statebind/statebind-bench", "egfr-actives")`

**Zenodo archive:**
- DOI-bearing archival deposit
- Contents: all data files, evaluation code snapshot, baseline results, Docker image tar
- Version DOIs for each release (v1.0 = EGFR only, v2.0 = multi-kinase)

**Containerization:**
- Dockerfile (multi-stage):
  - Stage 1: `nvidia/cuda:12.1-devel-ubuntu22.04` base with Python 3.12, RDKit, GNINA
  - Stage 2: install `statebind-bench` package + all dependencies
  - Stage 3: copy data and evaluation scripts
- Singularity/Apptainer definition file: converted from Dockerfile for HPC clusters
  - Critical for adoption: many HPC clusters (including Yale Bouchet) disallow Docker but support Singularity
- Conda `environment.yml`: for users who prefer Conda over containers
- GitHub Actions CI: automated tests on every PR; nightly build of container images

**Croissant metadata (beyond HuggingFace auto-generation):**
- Hand-curated fields for: data provenance (PDB, ChEMBL, KLIFS sources), licensing (CC-BY 4.0), task descriptions, evaluation metrics, known limitations
- Validated via `mlcroissant` Python library before release

#### Step 6: Write Benchmark Paper (Weeks 5-7)

**Paper structure (JCIM format, ~8,000 words + figures):**

1. Introduction: the conformational state gap in current benchmarks
2. Related Work: systematic comparison with CrossDocked2020, MOSES, GuacaMol, TDC, Kinase-Bench, GenBench3D, Durian
3. StateBind-Bench Design:
   - Data curation (structures, actives, state annotations, time splits)
   - Task definitions (4 tasks with metrics)
   - Evaluation protocol
4. Baseline Results:
   - Per-task results for 6 baselines
   - State specificity analysis: which methods are state-sensitive?
   - Cross-state docking matrix visualization
   - Retrospective enrichment comparison
5. Analysis:
   - Do existing 3D generators respond to state conditioning?
   - What properties distinguish state-specific from state-agnostic molecules?
   - Scoring function sensitivity analysis (100 Dirichlet-sampled weights)
   - Failure mode taxonomy
6. Discussion:
   - Why this gap matters for drug design
   - Limitations (EGFR-only, discrete states, computational scoring)
   - Multi-kinase extension roadmap
7. Data and Code Availability

**Key figures:**
- Figure 1: Benchmark landscape gap analysis (matrix of benchmarks vs. capabilities; StateBind-Bench fills the empty cell)
- Figure 2: 4 EGFR conformational state pockets overlaid (structural visualization)
- Figure 3: Cross-state docking matrix heatmap (6 baselines x 4 states)
- Figure 4: State specificity distribution per method (violin plots)
- Figure 5: Retrospective enrichment curves (EF@K for state-aware vs. static vs. random)
- Figure 6: Pareto front visualization (2D projection of multi-objective scores)

### Technical Details

**Scoring function architecture:**
The unified scoring function from StateBind's ranking/scoring.py serves as the primary evaluation metric. It combines docking score, drug-likeness (QED), synthetic accessibility (SA), ADMET predictions, and state specificity into a weighted sum. The default weights are configurable via YAML, and the benchmark reports sensitivity analysis across 100 Dirichlet-sampled weight vectors to demonstrate robustness.

For fair comparison, raw GNINA CNN affinity scores are also reported alongside the composite score, so users can evaluate against a structure-based metric that is independent of StateBind's specific scoring design.

**State Specificity Index (SSI) -- formal definition:**
For molecule m generated for target state s_target, dock into all K states to obtain scores {d_1, ..., d_K}. Then:
- SSI(m) = sigma({d_1, ..., d_K}) / |mean({d_1, ..., d_K})|
- Where sigma is the standard deviation
- Range: 0 (identical score across all states = state-agnostic) to unbounded positive (highly state-specific)
- A method's aggregate SSI is the median SSI across all its generated molecules

**Diagonal dominance -- formal definition:**
For method M generating molecules for each of K states, construct a KxK cross-docking matrix C where C[i,j] = mean score of molecules designed for state i docked into state j. Diagonal dominance = fraction of rows where the diagonal entry is the maximum. Perfect diagonal dominance = 1.0 (every set of molecules scores best in the state it was designed for). Random expectation = 1/K = 0.25 for K=4 states.

**Time-split protocol:**
Following the temporal split methodology of Sheridan (2013) and validated in StateBind's existing retrospective analysis. Activity data with first-reported dates from ChEMBL are split into training (pre-cutoff) and test (post-cutoff) sets. No compound in the test set shares a Bemis-Murcko scaffold with any training compound. The two splits (pre-2010, pre-2015) provide independent tests of generalization.

---

## Multi-Kinase Extension Roadmap

### Phase 1: EGFR Benchmark Release (Months 1-2)

The initial release covers EGFR with 4 conformational states as described above. This is a complete, self-contained benchmark sufficient for the JCIM paper.

### Phase 2: ABL1 and BRAF Extension (Months 3-5)

**ABL1 (Abelson tyrosine kinase):**
- Clinical relevance: CML (imatinib, dasatinib, ponatinib, asciminib)
- Conformational states: DFGin/DFGout well-characterized; imatinib binds DFGout (Nagar et al., Cancer Cell 2002)
- KLIFS structures: 200+ ABL1 structures in PDB with KLIFS state annotations
- ChEMBL actives: 3,000+ compounds with measured IC50/Ki
- Value: ABL1 is the textbook example of conformation-selective drug design (imatinib vs. dasatinib); including it makes the benchmark's claim to generality much stronger

**BRAF (B-Raf proto-oncogene):**
- Clinical relevance: melanoma (vemurafenib, dabrafenib, encorafenib)
- Conformational states: DFGin/DFGout + "alpha-C-out" paradox activator conformations
- KLIFS structures: 100+ BRAF structures
- ChEMBL actives: 2,000+ compounds
- Value: BRAF's paradoxical activation mechanism adds a clinically relevant dimension -- state selection has real pharmacological consequences

**Data curation for extension:**
- Extract pocket structures from PDB using KLIFS state annotations
- Curate ChEMBL bioactivity data with year-of-first-report for time splits
- Validate state assignments against published literature
- Generate 9D state feature vectors using the same pipeline as EGFR

**New benchmark capabilities enabled:**
- Task 5 (extension): Cross-kinase generalization -- train on EGFR states, generate for ABL1 states
- Task 6 (extension): Selectivity-aware generation -- generate molecules selective for one kinase's state over another kinase's state

### Phase 3: Community Challenge (Months 6-12)

Modeled on SAMPL/DREAM:

**Challenge structure:**
- Round 1 (Open): release ABL1/BRAF pocket structures + state labels. Participants generate molecules for each state. Evaluation on public metrics.
- Round 2 (Blind): release pocket structures for 1-2 additional kinases (candidates: ALK, JAK2, SRC). Hold back state labels and evaluation data. Participants predict state-appropriate molecules. Organizers evaluate against held-out data.
- Round 3 (Analysis): joint publication analyzing which methods, architectures, and conditioning strategies succeed or fail at state-conditioned generation.

**Infrastructure:**
- Submission portal: HuggingFace Spaces web app or Synapse (DREAM platform)
- Automated evaluation: Docker container running scoring pipeline
- Timeline: 3-month submission window per round
- Target participation: 10-20 groups (CACHE attracted 23 in its first challenge)

**Recruitment strategy:**
- Announce at MLDD workshop (ICLR/NeurIPS), ACS Fall Meeting computational chemistry division
- Contact labs directly: Barzilay (MIT), Coley (MIT), Jumper (DeepMind), Isayev (CMU), Jing (Stanford)
- Post on Twitter/X, Reddit (r/cheminformatics, r/MachineLearning), RDKit mailing list
- Partner with TDC or CACHE for visibility

---

## Reproducibility Checklist

The following checklist is embedded in the benchmark design. Every item must be satisfied before release.

| # | Requirement | Implementation | Status |
|---|-------------|---------------|--------|
| 1 | All data publicly accessible without personal request | HuggingFace + Zenodo | To do |
| 2 | Evaluation code open-source (MIT license) | GitHub repository | To do |
| 3 | Docker container reproduces all baseline results | Dockerfile + Singularity | To do |
| 4 | Conda environment.yml for HPC users | Tested on SLURM (Bouchet) | To do |
| 5 | Exact commands to reproduce every table/figure | README + Makefile | To do |
| 6 | Random seeds documented; 3 runs per baseline | Config files + scripts | To do |
| 7 | Standard deviations reported for all metrics | Evaluation pipeline | To do |
| 8 | Croissant metadata with RAI fields | Auto-generated + hand-curated | To do |
| 9 | Data provenance documented (PDB IDs, ChEMBL version, KLIFS version) | Dataset card | To do |
| 10 | CC-BY 4.0 license for data, MIT for code | LICENSE files | To do |
| 11 | Model checkpoints with model cards (VAE, MPNN, ADMET) | HuggingFace Hub | To do |
| 12 | SLURM job templates for HPC reproduction | slurm/ directory | To do |
| 13 | CI/CD: GitHub Actions runs tests on every PR | .github/workflows/ | To do |
| 14 | Version-pinned dependencies (exact pip freeze) | requirements-lock.txt | To do |
| 15 | Pre-computed scores available for users without GNINA | Included in dataset | To do |

---

## Impact Assessment

### Publication Impact

- **Primary target venue:** JCIM (Journal of Chemical Information and Modeling). JCIM published GuacaMol, DUD-E, Kinase-Bench, and Durian. Strong tradition of benchmark papers. No strict submission deadline -- submit when ready. Impact Factor ~6.2.

- **Secondary target venue:** NeurIPS 2027 Evaluations and Datasets Track. If the multi-kinase extension (Phase 2) is completed, the expanded benchmark is a strong NeurIPS submission. The 2026 deadline (May 6, 2026) is likely too tight for a polished multi-kinase release, but EGFR-only could be submitted if the team executes rapidly.

- **Backup venues:** Scientific Data (data descriptor, IF ~5.8), Nucleic Acids Research Database Issue (annual, IF ~14.9), Nature Computational Science (if combined with a methods paper).

- **Main claim this enables:** "Conformational state-conditioned generation is a distinct, measurable capability that existing benchmarks fail to evaluate. StateBind-Bench is the first benchmark to fill this gap, and reveals that most current 3D generative models are state-agnostic -- they do not meaningfully differentiate between conformational states of the same target."

- **Citation projection:** Conservative: 50-100 citations in Year 1, 100-200/year thereafter, 500-1,000 cumulative in 3-5 years. Upper bound (if adopted as community standard): 200+ citations/year once state-aware generation becomes mainstream. This projection is grounded in the trajectories of CrossDocked2020 (~300 citations in 6 years, and that benchmark was not the first in its niche) and MOSES (~770 in 6 years).

- **Reviewer concerns this addresses:**
  - "Why not just use CrossDocked2020?" -- Answered: CrossDocked2020 has no state annotations and cannot measure state conditioning.
  - "EGFR only is too narrow." -- Answered: Phase 1 is proof of concept; multi-kinase extension is described and KLIFS provides the data for rapid expansion.
  - "Small retrospective N." -- Answered: bootstrap confidence intervals; enrichment factors meaningful even at small N because base rates are extremely low.
  - "Scoring function is arbitrary." -- Answered: weight sensitivity analysis over 100 Dirichlet configurations; raw docking scores also reported.

### Effort Estimate

- **Compute (Phase 1 -- EGFR baselines):**
  - GNINA docking: ~4,000 molecules x 4 states x 6 methods x 3 runs = 288,000 docking evaluations. At ~30 seconds/dock on GPU, this is ~2,400 GPU-hours on RTX 5000 Ada. On H200, roughly 1,200 GPU-hours.
  - Generative model runs: REINVENT 4 (~2 GPU-hours per state), DiffSBDD (~4 GPU-hours per state), TargetDiff (~4 GPU-hours per state), Pocket2Mol (~2 GPU-hours per state), StateBind VAE (~0.5 GPU-hours per state). Total: ~50 GPU-hours for generation.
  - Evaluation pipeline: CPU-bound, ~10 hours on 4 CPUs.
  - **Total Phase 1 compute: ~1,300-2,500 GPU-hours** (feasible on Bouchet in 1-2 weeks using day/gpu partitions).

- **Compute (Phase 2 -- ABL1/BRAF):**
  - Roughly 2x Phase 1 (2 additional kinases x same protocol) = ~2,600-5,000 GPU-hours additional.

- **Data:** All required data is publicly available. EGFR structures from PDB (free). Bioactivity from ChEMBL 34 (free, CC-BY-SA 3.0). KLIFS annotations (free, academic use). No proprietary data required.

- **Implementation timeline:**
  - Weeks 1-2: Data package assembly and task definition
  - Weeks 3-5: Baseline method runs (parallelizable across GPU nodes)
  - Weeks 4-5: Evaluation pipeline and leaderboard
  - Weeks 5-6: Infrastructure (Docker, HuggingFace, Zenodo, Croissant)
  - Weeks 5-7: Paper writing
  - Week 8: Internal review and submission
  - **Total Phase 1: ~8 weeks** to JCIM submission
  - Months 3-5: Phase 2 (multi-kinase extension)
  - Months 6-12: Phase 3 (community challenge)

- **Dependencies:** Existing StateBind pipeline must be functional (it is -- 646 tests passing). GNINA must be installed (it is). External baselines (REINVENT 4, DiffSBDD, TargetDiff, Pocket2Mol) must be installable -- all are open-source with published installation instructions.

### Risk Assessment

- **Technical risks:**
  - External baseline methods may have dependency conflicts or fail to install. **Mitigation:** test installation early (Week 1); drop non-functional baselines and document why; a minimum of 3 baselines (StateBind VAE, REINVENT 4, one 3D method) is sufficient.
  - GNINA docking may produce noisy scores for some generated molecules. **Mitigation:** report score distributions, not just means; use 3 independent runs; include pre-computed scores for reproducibility.
  - Docker/Singularity container may not capture all GPU-dependent behavior. **Mitigation:** test on at least 2 platforms (Bouchet HPC + cloud VM); pin CUDA version and driver compatibility.

- **Scientific risks:**
  - All baselines may be equally state-agnostic, producing a "null result." **Mitigation:** this is actually a *positive* result for the benchmark -- it demonstrates that current methods lack state conditioning capability, validating the need for the benchmark. The paper's framing handles this: "we show that existing methods are state-agnostic, motivating future work on state-conditioned architectures."
  - StateBind's own VAE may not clearly outperform baselines on all metrics. **Mitigation:** the benchmark's value is in the evaluation framework, not in StateBind winning. Report results honestly. If StateBind's VAE underperforms on some metrics, that reveals areas for improvement -- which is exactly what benchmarks are for.
  - Retrospective enrichment may not replicate at the 10x level when using external methods. **Mitigation:** report confidence intervals; the 10x result is StateBind-specific and establishes an upper bound.

- **Adoption risks:**
  - Community may not adopt the benchmark if it is too complex or too EGFR-specific. **Mitigation:** make the evaluation pipeline trivially easy to use (single command); provide pre-computed features so users do not need GNINA; Phase 2 multi-kinase extension addresses specificity concern.
  - PapersWithCode leaderboard may not gain traction initially. **Mitigation:** seed with 6 baselines; publicize via conferences and social media; the community challenge (Phase 3) drives adoption.

---

## Evaluation Criteria

How would we know if StateBind-Bench succeeded?

1. **Benchmark release completeness.** All 4 tasks defined with evaluation code, 6+ baselines run, data on HuggingFace, archive on Zenodo, Docker/Singularity containers tested. Binary pass/fail per the 15-item reproducibility checklist above.

2. **Paper acceptance.** JCIM acceptance within 12 months of submission. Measured by peer review outcome.

3. **Discriminative power.** The benchmark produces meaningfully different rankings for different methods. Specifically: the variance in method performance across the 4 tasks should be large enough that the benchmark is informative. If all methods score identically, the benchmark fails to discriminate. Target: coefficient of variation >0.15 across methods for at least 3 of 4 tasks.

4. **State conditioning signal.** State-aware methods (StateBind VAE) achieve measurably higher SSI and diagonal dominance than state-blind methods (random baseline, unconditioned generators). Target: effect size (Cohen's d) >= 0.5 for SSI comparison.

5. **Community adoption.** Within 18 months of release: at least 3 external papers cite StateBind-Bench as an evaluation benchmark. Within 3 years: 10+ external papers. These are leading indicators of trajectory toward the 500-1,000 citation projection.

6. **Leaderboard submissions.** At least 5 external method submissions to the leaderboard within 12 months of release.

7. **Reproducibility verification.** At least 1 external group independently reproduces baseline results within 10% of reported values using the provided containers. This is the ultimate test of the reproducibility package.

---

## Open Questions

1. **NeurIPS 2026 feasibility.** Can an EGFR-only benchmark paper be assembled in time for the May 6 abstract deadline (27 days from today)? This requires data packaging, at least 3 baselines run, evaluation code written, and paper drafted. It is aggressive but not impossible if the team focuses exclusively on this. The question is whether EGFR-only is sufficient for NeurIPS or whether multi-kinase is required for acceptance.

2. **Separate package vs. extension of existing codebase.** Should `statebind-bench` be a standalone pip package (easier for external users, cleaner dependency tree) or a subpackage of the existing `statebind` package (easier to maintain, shares code)? Recommendation: standalone package that imports from `statebind` for internal use but can be installed independently by external users.

3. **GNINA dependency.** GNINA is not trivially installable on all platforms (requires CUDA, specific library versions). Should the benchmark require GNINA, or should pre-computed docking scores be the primary evaluation mode? Recommendation: pre-computed scores as default, GNINA as optional for users who want to dock their own molecules.

4. **Scoring function as part of the benchmark.** StateBind's unified scoring function is human-designed with specific weights. If the benchmark's evaluation metric IS the scoring function, methods could overfit to it. Should the benchmark use raw docking scores only (method-agnostic) or the full composite score (more informative but gameable)? Recommendation: report both; use raw docking scores as the primary leaderboard metric and composite score as supplementary.

5. **KLIFS licensing.** KLIFS data is freely available for academic use. Verify that redistribution within a CC-BY 4.0 benchmark dataset is compatible with KLIFS terms of use. If not, provide scripts that pull KLIFS data on-the-fly rather than redistributing it.

6. **Community challenge timing.** Should the challenge launch concurrently with the paper (maximizes exposure) or after paper acceptance (ensures the benchmark is peer-reviewed and stable)? Recommendation: launch after paper acceptance to avoid running a challenge on a benchmark that might change during peer review.

7. **Continuous state conditioning.** StateBind currently uses 4 discrete states (DFG x aC). Vision System idea 001 proposes continuous conformational conditioning. Should the benchmark include a continuous conditioning task from the start, or add it in v2.0? Recommendation: v2.0 -- the discrete task is already novel and sufficient for the initial release.

---

## References

1. Wu, Z., Ramsundar, B., Feinberg, E.N., et al. (2018). MoleculeNet: a benchmark for molecular machine learning. *Chemical Science*, 9, 513-530.

2. Polykovskiy, D., Zhebrak, A., Sanchez-Lengeling, B., et al. (2020). Molecular Sets (MOSES): A Benchmarking Platform for Molecular Generation Models. *Frontiers in Pharmacology*, 11, 565644.

3. Brown, N., Fiscato, M., Segler, M.H.S., Vaucher, A.C. (2019). GuacaMol: Benchmarking Models for de Novo Molecular Design. *JCIM*, 59(3), 1096-1108.

4. Huang, K., Fu, T., Gao, W., et al. (2021). Therapeutics Data Commons: Machine Learning Datasets and Tasks for Drug Discovery and Development. *NeurIPS D&B Track*.

5. Francoeur, P.G., Masber, T., Hajber, A.J., et al. (2020). Three-Dimensional Convolutional Neural Networks and a Cross-Docked Data Set for Structure-Based Drug Design. *JCIM*, 60(9), 4200-4215.

6. Mysinger, M.M., Carchia, M., Irwin, J.J., Shoichet, B.K. (2012). Directory of Useful Decoys, Enhanced (DUD-E). *J. Med. Chem.*, 55(14), 6582-6594.

7. Kooistra, A.J., Kanev, G.K., et al. (2021). KLIFS: an overhaul after the first 5 years of supporting kinase research. *Nucleic Acids Research*, 49(D1), D562-D569.

8. Critical Assessment of ML models for ADMET Prediction in TDC leaderboards. *bioRxiv*, 2026.

9. Bender, A., et al. (2024). CACHE Challenge #1 Results. *JCIM*.

10. Nie, Y., Zhao, J., et al. (2024). Durian: A Comprehensive Benchmark for Structure-Based 3D Molecular Generation. *JCIM*.

11. Baillif, B., Cole, J., et al. (2024). Benchmarking structure-based three-dimensional molecular generative models using GenBench3D. *arXiv:2407.04424*.

12. Loeffler, H.H., et al. (2024). Reinvent 4: Modern AI-driven generative molecule design. *Journal of Cheminformatics*, 16, 20.

13. Saez-Rodriguez, J., et al. (2021). Advances in systems biology modeling: 10 years of crowdsourcing DREAM challenges. *Cell Systems*, 12(6), 519-530.

14. Garbett, A., et al. (2022). CACHE (Critical Assessment of Computational Hit-finding Experiments). *Nature Reviews Chemistry*, 6, 287-295.

15. NeurIPS 2026 Evaluations and Datasets Track Call for Papers. https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets

16. Croissant: A Metadata Format for ML-Ready Datasets. *NeurIPS D&B Track*, 2024.

17. Weber, L.M., et al. (2023). Five pillars of computational reproducibility. *Briefings in Bioinformatics*, 24(6).

18. Resolving data bias improves generalization in binding affinity prediction. *Nature Machine Intelligence*, 2025.

19. Nagar, B., et al. (2002). Crystal structures of the kinase domain of c-Abl in complex with the small molecule inhibitors PD173955 and imatinib (STI-571). *Cancer Research*, 62(15), 4236-4243.

20. Sheridan, R.P. (2013). Time-Split Cross-Validation as a Method for Estimating the Goodness of Prospective Prediction. *J. Chem. Inf. Model.*, 53(4), 783-790.

21. Kinase-Bench: Comprehensive Benchmarking Tools and Guidance for Achieving Selectivity in Kinase Drug Discovery. *JCIM*, 2024.

22. Comprehensive Benchmark Study of Diffusion-Based 3D Molecular Generation Models. *ACS Omega*, 2025.

23. Schneuing, A., et al. (2022). Structure-based Drug Design with Equivariant Diffusion Models. *arXiv:2210.13695*.

24. Guan, J., et al. (2023). 3D Equivariant Diffusion for Target-Aware Molecule Generation and Affinity Prediction. *ICLR 2023*.

25. Peng, X., et al. (2022). Pocket2Mol: Efficient Molecular Sampling Based on 3D Protein Pockets. *ICML 2022*.

26. Cremer, J., et al. (2024). PILOT: equivariant diffusion for pocket-conditioned de novo ligand generation with multi-objective guidance. *NeurIPS Workshop on New Frontiers of AI for Drug Discovery and Development*.

27. Huse, M., Kuriyan, J. (2002). The conformational plasticity of protein kinases. *Cell*, 109(3), 275-282.

28. Shan, Y., et al. (2014). Transitions to catalytically inactive conformations in EGFR kinase. *PNAS*, 111(43), E4507-E4514.
