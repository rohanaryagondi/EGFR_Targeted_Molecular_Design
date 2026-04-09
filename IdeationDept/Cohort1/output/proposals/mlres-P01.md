---
agent: Senior ML Researcher
round: 2
date: 2026-04-08
type: proposal
proposal_id: mlres-P01
title: External Baseline Comparison Framework for StateBind Publication
---

# Proposal: External Baseline Comparison Framework for StateBind Publication

## Proposing Agent
Senior ML Researcher -- expertise in publication strategy, benchmark methodology, ablation
design, and reviewer expectations at top computational biology and ML venues.

## Problem Statement

StateBind currently compares only two pipelines: static (1M17 single-structure) and
state-aware (4-state conditioned). This internal comparison, while scientifically rigorous
in its use of a unified scoring function, is **insufficient for publication at any credible
venue**. Reviewers at JCIM, Nature Computational Science, or NeurIPS Datasets & Benchmarks
will ask a single question that the current manuscript cannot answer:

> "How does your state-aware VAE compare to REINVENT, DiffSBDD, or any other published
> generative method on the same EGFR task?"

Without external baselines, the paper is desk-rejected or returned with major revisions.
The comparison is not optional -- it is a publication prerequisite. The Round 1 synthesis
identified this as a P0 priority with universal agreement across all 7 specialists.

Beyond desk-rejection risk, external baselines serve three scientific purposes:

1. **Contextualization**: Where does state-conditioned generation sit relative to established
   methods? Is the 10x retrospective enrichment a property of state-conditioning, or would
   any reasonable generator achieve similar enrichment?

2. **Ablation of the generation method**: The current static vs state-aware comparison
   conflates generation method (VAE vs template), candidate count (461 vs 30), diversity
   (0.91 vs 0.57), and state-conditioning. External baselines, particularly the unconditioned
   VAE ablation, isolate these factors.

3. **Credibility**: Reviewers calibrate claims against known methods. A claim that
   "state-aware design achieves 10x enrichment" without showing what REINVENT achieves on
   the same task is not interpretable.

## Vision

A complete, pre-registered baseline comparison framework in which **5 methods generate
molecules for EGFR**, all evaluated under the **same unified scoring function** and the
**same retrospective time-split protocol**. The framework produces a single comparison table
that contextualizes StateBind's contribution, survives peer review, and enables honest
reporting regardless of outcome. The framework is designed so that any outcome is
publishable: state-conditioning wins, state-conditioning helps modestly, or
state-conditioning provides no benefit beyond diverse generation.

---

## Background and Evidence

### The Baseline Gap in Current AI Drug Design Literature

The PMO benchmark (Gao et al., NeurIPS Datasets & Benchmarks, 2022) evaluated 25 molecular
optimization methods across 23 tasks and found that REINVENT and Graph GA -- methods from
2017-2019 -- consistently outperformed many "state-of-the-art" competitors. Under a 10K
oracle budget, most newer methods failed to surpass these older approaches. This established
REINVENT as the de facto standard comparison for any molecular generation paper.

The GSK benchmarking study (JCIM, 2025) evaluated 3D structure-based methods and found
that deep learning methods frequently fail to generate structurally valid molecules: Pocket2Mol
achieves only 40.4% on all validity checks; DiffSBDD achieves 33.3%. The "Beyond Affinity"
benchmark (arXiv 2601.14283, 2025) showed that 1D/2D methods achieve the best drug-likeness
metrics (QED, SA, LogP consistency) while 3D methods achieve the best binding affinity but
worst structural validity and pose quality. These findings validate StateBind's SELFIES-based
approach more than expected: 99.9% chemical validity exceeds all 3D methods.

The Durian benchmark (Nie et al., JCIM, 2025) established 17 evaluation metrics across
binding affinity, drug-likeness, and structural quality, using 3 independent docking methods
(QuickVina2, Surflex, GNINA). This multi-metric evaluation approach should be adopted.

### Specific Baseline Evidence

**REINVENT 4** (Loeffler et al., J. Cheminform., 2024): Open source (Apache 2.0), 720
GitHub stars, v4.7 as of November 2025. Supports de novo design, scaffold hopping, and
molecular optimization via RNN and Transformer architectures with RL-based optimization.
Scoring supports 30+ components. Plugin architecture allows custom scoring components via
Python namespace packages in `reinvent_plugins/components/`. GNINA docking can be integrated
as a scoring plugin, making REINVENT directly compatible with StateBind's existing docking
infrastructure. Memory requirement: approximately 8 GB. RL fine-tuning converges in minutes.
In a PDK1 kinase application, REINVENT achieved 3.5% hit rate from a transfer learning
variant (Loeffler et al., 2024).

**MolCRAFT** (Qu et al., ICML 2024): The first SBDD model employing Bayesian Flow Networks
(BFNs) operating in a fully continuous parameter space. Achieves reference-level Vina Scores
on CrossDocked2020 (-6.59 vs -6.36 reference) with comparable molecule size, and is 30x
faster than diffusion baselines (approximately 141 seconds per 100 molecules vs 3400-6200
seconds for DiffSBDD/TargetDiff). Pre-trained checkpoint available on HuggingFace
(GenSI/MolCRAFT). The MolCRAFT series now includes MolJO (ICML 2025) and MolPilot
(ICML 2025), with MolPilot achieving 95.9% PoseBusters validity. Supports custom pocket
inference with PDB input.

**DiffSBDD** (Schneuing et al., Nature Computational Science, 2024): SE(3)-equivariant
diffusion model. 8 pre-trained checkpoint variants available on Zenodo (CrossDocked +
BindingMOAD, C-alpha + full-atom, conditional + joint). Inference approximately 2.5
seconds per compound. Published in the same journal we are targeting (Nature Comp. Sci.),
making it a particularly relevant comparison. However, PoseBusters validity is only 38%
(Buttenschoen et al., 2024), which is a known weakness.

**Unconditioned VAE ablation literature**: STAR-VAE (arXiv 2511.02769, 2025) distinguishes
between "CVAE" (conditioned) and "VAE" (unconditioned) as a standard ablation pattern.
Conditional beta-VAE (arXiv 2205.01592, 2022) explicitly compares beta-VAE with and without
latent space conditioning on pLogP, finding that conditioning improves targeted generation.
This establishes the unconditioned ablation as standard methodology.

### Key Evidence
1. **Gao et al. (2022)**: REINVENT and Graph GA outperform most newer methods in the PMO
   benchmark, establishing REINVENT as the minimum required baseline for any generation paper.
2. **GSK SBDD benchmark (JCIM, 2025)**: 3D methods achieve 33-40% full validity vs
   StateBind's 99.9% chemical validity, validating the 1D approach for a framework paper.
3. **"Do 3D Methods Really Dominate?" (arXiv 2406.03403, 2024)**: AutoGrow4 (2D) achieves
   top docking scores across 7 targets, and REINVENT achieves QED 0.91 -- competitive with
   all methods. "No methods can dominate structure-based drug design in all evaluation metrics."
4. **Truchon & Bayly (JCIM, 2007)**: Bootstrap resampling of ranked lists provides EF
   confidence intervals with "excellent agreement" with analytic estimates for AUC.
5. **Nicholls (JCAMD, 2016)**: Analytic formulae for EF confidence intervals via binomial
   CIs on EF(f)*f, applicable to small-N retrospective validation.
6. **Buttenschoen et al. (Chemical Science, 2024)**: PoseBusters validity ranges from 0-11%
   for raw 3D molecules before relaxation; FLOWR achieves 92%, DiffSBDD only 38%.
7. **Qu et al. (ICML, 2024)**: MolCRAFT achieves reference-level Vina scores with 30x
   faster sampling than diffusion, establishing it as the current practical SOTA for 3D SBDD.

### Relationship to Existing Work
- **StateBind current state:** Internal comparison (static vs state-aware) under unified
  scoring is complete. Retrospective validation yields 10x enrichment (EF@10 = 4.95/7.72).
  No external baselines exist.
- **Vision System ideas:** Vision idea 002 proposed DiffSBDD/TargetDiff as a 3D upgrade.
  This proposal does NOT replace the VAE; it runs external methods as comparison baselines.
  Vision idea 012 proposed REINVENT-style RL. This proposal runs REINVENT as a baseline,
  not a replacement. Both ideas are deferred; this proposal reframes them as comparison
  experiments rather than architecture changes.
- **Literature precedent:** The Durian benchmark (JCIM, 2025) and "Beyond Affinity" benchmark
  (2025) both compare multiple generation paradigms (1D, 2D, 3D) on standardized metrics.
  StateBind's contribution is the conformational-state dimension, which neither addresses.

---

## Proposed Approach

### Overview

Run 5 molecular generation methods on the EGFR task, all evaluated with StateBind's unified
scoring function and retrospective time-split protocol. The 5 methods span 4 paradigms:
RL-based 1D optimization (REINVENT 4), 3D pocket-conditioned generation (MolCRAFT),
conditioned 1D generation (StateBind VAE), unconditioned 1D generation (ablated StateBind
VAE), and naive retrieval (fingerprint similarity + random ChEMBL). Every method generates
molecules for each of EGFR's 4 conformational states where applicable, and all candidates
are rescored under the same function to ensure fair comparison.

The framework is designed with pre-registered outcome interpretations: every possible
result pattern maps to a specific, publishable narrative. This eliminates post-hoc
rationalization and strengthens the paper's scientific credibility.

### Baseline 1: REINVENT 4 -- State-Specific RL Optimization

**Justification:** REINVENT is the most widely used molecular optimization tool in
computational drug design (720 GitHub stars, Apache 2.0, v4.7). JCIM reviewers will
specifically ask for this comparison. It represents the strongest available 1D baseline
because it uses RL to directly optimize a scoring function, whereas StateBind's VAE
generates in one shot without iterative refinement.

**Configuration:**
- Install REINVENT 4 from `MolecularAI/REINVENT4` GitHub repository
- Define 4 state-specific scoring profiles, one per EGFR conformational state:
  - Each profile uses GNINA docking against the corresponding receptor (1M17, 2GS7, 3W2R,
    4ZAU) as the primary scoring component
  - Additional scoring components: QED, SA score, Tanimoto similarity to reference binders
  - Weight configuration mirrors StateBind's unified scoring: reference similarity 0.35,
    drug-likeness 0.30, docking 0.20, state specificity 0.15
- Use REINVENT's plugin architecture to integrate GNINA as a custom scoring component
- Generate 250 molecules per state (1000 total), matching StateBind's total candidate pool
- Use REINVENT's de novo design mode with the pre-trained SMILES prior
- Run 3 independent seeds per state to provide error bars
- RL convergence: allow up to 500 steps per run (typical convergence in 100-300 steps)

**Making REINVENT state-aware:** REINVENT does not natively understand conformational
states. The state-awareness is introduced through the scoring function: each state's
scoring profile docks against a different receptor structure. REINVENT optimizes molecules
toward each pocket independently. This is the "naive state-awareness" approach --
pocket-specific optimization without explicit state conditioning. Comparing this to
StateBind's explicit state-vector conditioning tests whether the conditioning mechanism
adds value beyond pocket-specific optimization.

**Output:** 1000 SMILES strings (250 per state), each with REINVENT's internal scores.
All SMILES are then rescored with StateBind's unified scoring function.

### Baseline 2: MolCRAFT -- 3D Pocket-Conditioned Generation

**Justification:** MolCRAFT represents the current practical SOTA for 3D structure-based
drug design: reference-level Vina scores, 30x faster than diffusion methods, pre-trained
checkpoint on HuggingFace. It tests whether 3D pocket-conditioning -- which uses the full
3D geometry of the binding site -- subsumes StateBind's 1D state-conditioning, which uses
only a 4-dimensional one-hot state label. If MolCRAFT beats StateBind, the implication is
that richer structural conditioning is required; if StateBind matches or beats MolCRAFT,
the implication is that discrete state labels capture sufficient information.

**Configuration:**
- Download pre-trained checkpoint from HuggingFace (GenSI/MolCRAFT)
- Prepare 4 EGFR pocket structures in MolCRAFT-compatible format:
  - Extract binding pockets from 1M17, 2GS7, 3W2R, 4ZAU (10 angstrom radius around
    co-crystallized ligand)
  - Convert to the coordinate + atom type format expected by MolCRAFT
- Zero-shot generation: no retraining on EGFR-specific data (tests generalization)
- Generate 250 molecules per pocket (1000 total)
- 3 independent sampling runs per pocket for error bars

**Handling MolCRAFT's 3D output:** MolCRAFT generates 3D molecular coordinates directly.
To evaluate with StateBind's unified scoring function (which operates on SMILES):
1. Extract SMILES from the 3D coordinates using RDKit's `MolToSmiles`
2. Validate chemical structure (reject molecules that fail RDKit sanitization)
3. Score with StateBind's unified function (which does its own GNINA docking)
4. Separately report MolCRAFT's native Vina scores for comparison
5. Apply PoseBusters validity checks to the 3D poses and report validity rates

**Note on DiffSBDD:** DiffSBDD was considered as an alternative 3D baseline (published in
Nature Comp. Sci., same target venue). However, its PoseBusters validity (38%) is
substantially below MolCRAFT's expected validity (MolPilot series achieves 95.9%). If
reviewers specifically ask for DiffSBDD, it can be added as a supplementary comparison,
but MolCRAFT is the stronger representative of the 3D paradigm. If MolCRAFT proves
difficult to set up, DiffSBDD serves as the fallback -- it has 8 pre-trained checkpoint
variants on Zenodo and well-documented inference scripts.

### Baseline 3: Unconditioned VAE -- The Critical Ablation

**Justification:** This is the single most important experiment in the entire framework.
The current StateBind comparison conflates state-conditioning with VAE-based generation,
candidate count, and chemical diversity. The unconditioned VAE ablation holds everything
constant except the state-conditioning signal. If the unconditioned VAE achieves similar
retrospective enrichment to the conditioned VAE, then the diversity of VAE generation --
not state-conditioning -- drives the enrichment. If enrichment drops substantially, state-
conditioning is the key ingredient. Either outcome is publishable; only one supports the
thesis.

**Configuration:**
- Retrain the StateBind SELFIES VAE architecture with identical hyperparameters but with
  the state-conditioning vector zeroed out (replaced with a constant zero vector)
- Same training data, same number of epochs (300), same latent dimension (z=64)
- Same GRU encoder/decoder architecture (9.5M parameters)
- Generate 1000 molecules (not per-state, since there is no state conditioning)
- Subsample to 461 to match the state-aware pipeline's candidate count
- Score all with the unified scoring function
- Run retrospective enrichment on the same time-split protocol
- Train 3 independent seeds for error bars

**Why this is decisive:** The unconditioned VAE generates molecules from the same learned
chemical space as the conditioned VAE. It will produce diverse, valid molecules (SELFIES
guarantees validity). The question is whether state-conditioning causes the VAE to generate
molecules that are more likely to resemble future approved drugs for specific conformational
states. This is the direct test of StateBind's thesis.

**Expected outcomes and interpretation:**
- If conditioned EF@10 approximately equals unconditioned EF@10: diversity, not
  conditioning, drives enrichment. Publishable as "diverse generation is sufficient."
- If conditioned EF@10 is approximately 2x unconditioned: modest but real contribution from
  conditioning. Publishable as "state-conditioning provides incremental but statistically
  significant improvement."
- If conditioned EF@10 is approximately 5-10x unconditioned: strong state-conditioning
  effect. Publishable as "conformational conditioning is the key ingredient."

### Baseline 4: Random ChEMBL Baseline -- Lower Bound

**Justification:** Every comparison needs a lower bound. Random drug-like molecules from
ChEMBL establish the floor: what enrichment do you get by chance? If any generative method
fails to beat this baseline, that method provides no value for the EGFR task.

**Configuration:**
- Query ChEMBL for compounds with drug-like properties:
  - Molecular weight 200-600 Da
  - LogP -1 to 6
  - Rotatable bonds <= 10
  - Exclude molecules with known EGFR activity (to avoid trivial enrichment)
- Sample 461 molecules (matching state-aware candidate count)
- Repeat 100 times for robust confidence intervals on EF@10
- Score all with unified scoring function

**Note:** The 100 random draws provide a null distribution for enrichment, allowing
statistical testing (is any method's EF@10 significantly above the random baseline?).

### Baseline 5: Fingerprint Similarity Search -- Naive Retrieval Baseline

**Justification:** Before any generative model, the simplest approach to finding drug
candidates is to search existing databases for molecules similar to known drugs. This tests
whether generation adds any value over retrieval. If similarity search matches or beats
generative methods, the case for computational generation is weakened.

**Configuration:**
- Use Morgan fingerprints (radius 2, 2048 bits) -- the same fingerprint StateBind uses for
  reference similarity scoring
- Compute Tanimoto similarity of all ChEMBL drug-like compounds to the 3 reference
  molecules (erlotinib, gefitinib, osimertinib)
- Select the top 461 most similar compounds (excluding the reference molecules themselves)
- For the pre-2010 retrospective: search against erlotinib and gefitinib only (osimertinib
  not yet approved); for pre-2015: search against erlotinib, gefitinib, and lapatinib
  (excluding osimertinib to avoid leakage identified in Round 1)
- Score all with unified scoring function

**Expected outcome:** High reference similarity scores (by construction) but low docking
scores and low state specificity. The similarity search is biased toward the past. If it
achieves high enrichment, this undermines all generative approaches equally.

### Implementation Steps

**Phase 1: Infrastructure Setup (Week 1)**
1. Install REINVENT 4 in a dedicated conda environment on Bouchet
2. Write a GNINA scoring plugin for REINVENT's namespace package system
3. Prepare 4 EGFR pocket files in MolCRAFT-compatible format
4. Download MolCRAFT checkpoint from HuggingFace
5. Verify both tools can generate molecules on a GPU node (gpu_devel partition)
6. Create the unconditioned VAE training configuration (zero state vector)

**Phase 2: Generation Runs (Weeks 2-3)**
7. Run REINVENT 4 on 4 EGFR states (3 seeds each, 250 molecules/state/seed)
8. Run MolCRAFT on 4 EGFR pockets (3 seeds each, 250 molecules/pocket/seed)
9. Train 3 unconditioned VAE seeds (300 epochs each), generate 1000 molecules each
10. Sample 100 random ChEMBL sets (461 molecules each)
11. Run fingerprint similarity search (top 461 from ChEMBL)

**Phase 3: Unified Evaluation (Week 3-4)**
12. Score ALL generated molecules with StateBind's unified scoring function
13. Run GNINA docking for all candidates on all 4 EGFR receptors
14. Compute retrospective enrichment (pre-2010 and pre-2015 time-splits)
15. Apply PoseBusters validity checks to MolCRAFT's 3D outputs
16. Compute all metrics: BEDROC, EF@10, Vina score distributions, QED distributions,
    diversity, validity, novelty, SA scores

**Phase 4: Statistical Analysis (Week 4)**
17. Mann-Whitney U tests between every method pair on unified scores
18. Bootstrap confidence intervals (BCa, 10,000 resamples) on all enrichment metrics
19. Bonferroni correction for multiple comparisons (10 pairwise tests)
20. Compute effect sizes (Cohen's d) for all significant differences
21. Weight sensitivity analysis: 100 random Dirichlet weight configurations

**Phase 5: Pre-Cutoff Validation (Week 4, in parallel with Phase 4)**
22. For REINVENT: train pre-2010 and pre-2015 scoring profiles (exclude future drugs
    from reference molecules, retrain MPNN on pre-cutoff ChEMBL data)
23. For unconditioned VAE: train pre-2010 and pre-2015 versions on pre-cutoff data
24. For similarity search: restrict to pre-cutoff ChEMBL compounds only
25. MolCRAFT: use pre-trained checkpoint (no temporal leakage since it was trained on
    CrossDocked2020 structural data, not EGFR activity data)
26. Random: sample from pre-cutoff ChEMBL only

### Technical Details

**Fair candidate-count comparison:** All methods evaluated at N=461 candidates to match
StateBind's current pool. For methods that generate more (REINVENT with 3 seeds x 250 x 4
states = 3000), subsample to 461 using top-scoring candidates per the method's native
scoring. This tests: given a budget of approximately 461 candidates, which method finds the
best molecules?

**Handling failed generations:** Track and report failure rates:
- Invalid SMILES (REINVENT): expected < 5% based on published data
- Invalid chemistry from 3D extraction (MolCRAFT): expected 10-30% based on GSK benchmark
- Failed docking (all methods): molecules where GNINA crashes or returns no pose
- Report the valid-candidate yield as a metric: of 1000 attempted generations, how many
  produce scoreable molecules?

**PoseBusters for 3D methods:** Apply PoseBusters validity checks (Buttenschoen et al.,
Chemical Science, 2024) to MolCRAFT outputs. Report: bond length validity, bond angle
validity, steric clash rate, internal energy, and overall PoseBusters pass rate. This
addresses the standard now expected for any 3D generation method. StateBind's 1D SELFIES
approach sidesteps PoseBusters entirely (no 3D poses generated), which is either a
limitation (no structural poses) or an advantage (no invalid poses), depending on framing.

**Retrospective protocol alignment:** All methods use the same time-split:
- Pre-2010 cutoff: training data up to 2009, held-out drugs approved 2010+
- Pre-2015 cutoff: training data up to 2014, held-out drugs approved 2015+
- Critical: remove osimertinib from reference molecules in pre-2015 validation (Round 1
  data leakage finding)
- Each method retrained/reconfigured using only pre-cutoff data where applicable

---

## Impact Assessment

### Publication Impact
- **Target venue:** JCIM (primary), Nature Computational Science (aspirational)
- **Main claim this enables:** "We present the first systematic comparison of molecular
  generation paradigms conditioned on protein conformational states. Across 5 methods
  spanning RL optimization, 3D pocket-conditioning, VAE-based generation, and retrieval,
  conformational state-awareness consistently improves retrospective enrichment for approved
  EGFR drugs. The improvement is robust to scoring function weights, generation method, and
  time-split cutoff."
- **Reviewer concerns this addresses:**
  1. "No external baselines" -- directly solved (5 methods compared)
  2. "How does this compare to REINVENT?" -- REINVENT 4 included as primary external baseline
  3. "Is this just diversity, not state-conditioning?" -- unconditioned VAE ablation isolates
     the effect
  4. "What about 3D methods?" -- MolCRAFT provides direct comparison
  5. "Is the enrichment better than random?" -- random ChEMBL baseline provides null
     distribution
  6. "Is this better than simple similarity search?" -- fingerprint baseline included

### Effort Estimate

**Compute:**
- REINVENT 4 generation: approximately 4 GPU-hours on H200 (4 states x 3 seeds x
  approximately 20 min convergence)
- MolCRAFT generation: approximately 2 GPU-hours on H200 (4 pockets x 3 seeds x
  approximately 10 min sampling)
- Unconditioned VAE training: approximately 12 GPU-hours on H200 (3 seeds x 300 epochs x
  approximately 80 min each -- same as current VAE)
- GNINA docking for all candidates: approximately 20 GPU-hours (approximately 5000 unique
  molecules x 4 states x approximately 3.5 min/molecule, with parallelization)
- Total GPU: approximately 40 GPU-hours, easily accommodated in 1-2 days on a single H200
  node

**Data:**
- ChEMBL EGFR binding data: already available in StateBind's data pipeline (10,466 compounds)
- ChEMBL drug-like compounds for random baseline: query via ChEMBL API, approximately 2M
  compounds, filter to approximately 100K drug-like
- EGFR receptor structures: already prepared (1M17, 2GS7, 3W2R, 4ZAU in PDBQT format)
- Pre-trained MolCRAFT checkpoint: HuggingFace download, approximately 500 MB
- Pre-trained REINVENT prior: included in REINVENT4 package

**Implementation:**
- REINVENT 4 setup + GNINA plugin: 1-2 weeks (includes debugging scoring integration)
- MolCRAFT zero-shot setup: 2-3 days (download checkpoint, prepare pockets, test inference)
- Unconditioned VAE: 1-2 days (modify config to zero state vector, retrain)
- Random/similarity baselines: hours (ChEMBL query + scoring)
- Unified evaluation pipeline: 1 week (scoring, docking, metrics computation)
- Statistical analysis: 2-3 days (bootstrap CIs, Mann-Whitney, Bonferroni)
- **Total: 3-4 weeks**

**Dependencies:**
- GNINA v1.1 binary (already available on Bouchet cluster)
- GPU access (gpu or gpu_h200 partition, account pi_mg269)
- Existing StateBind scoring infrastructure (ranking/scoring.py, evaluation/retrospective.py)
- Pre-cutoff VAE and MPNN checkpoints (already trained for WS12/WS13)

### Risk Assessment

**Technical risks:**
- REINVENT 4 + GNINA integration may require significant debugging. REINVENT's plugin
  system expects specific input/output formats; wrapping GNINA docking may take longer than
  estimated. **Mitigation:** If GNINA integration stalls, use REINVENT with AutoDock Vina
  scoring (natively supported) as a temporary substitute, then add GNINA later.
- MolCRAFT pocket preparation may fail for non-standard EGFR structures (3W2R is a mutant,
  4ZAU has an unusual ligand). **Mitigation:** Use DiffSBDD as fallback (8 checkpoint variants,
  well-documented pocket input format). If both fail, report the 3D baseline as infeasible
  and document the attempt.
- GNINA docking for approximately 5000 molecules x 4 states may exceed allocated GPU time.
  **Mitigation:** Use MPNN proxy (tier 1) for initial screening; dock only top 500 candidates
  per method with GNINA for publication-quality scores.

**Scientific risks:**
- **Unconditioned VAE matches conditioned VAE on enrichment:** This would mean diversity,
  not state-conditioning, drives the result. **Mitigation:** Pre-register this as a valid
  outcome. The paper becomes "Diverse molecular generation identifies future drugs, but
  state-conditioning does not provide additional benefit." This is a publishable null result
  that advances understanding.
- **REINVENT beats all VAE variants:** This would mean RL optimization > one-shot generation
  for this task. **Mitigation:** Frame as "State-awareness improves ANY generator -- even
  REINVENT benefits from per-pocket optimization." Compare REINVENT-single-pocket vs
  REINVENT-4-pocket.
- **MolCRAFT beats all 1D methods:** This would mean 3D pocket-conditioning subsumes 1D
  state-conditioning. **Mitigation:** Pre-register and report honestly. The contribution
  shifts to "We demonstrate that 3D pocket-conditioning outperforms discrete state labels,
  motivating pocket-conditioned state-aware generation." This connects to Vision idea 002.
- **Random baseline matches generative methods:** This would undermine all generation
  approaches. **Mitigation:** Extremely unlikely given the random baseline's lack of
  structural information, but if it occurs, investigate whether the scoring function
  is non-discriminating.

---

## Pre-Registered Framing Strategy

The following outcome-to-narrative mapping is defined before any experiments run. This
eliminates post-hoc rationalization and is itself a publishable methodological contribution
(pre-registration is increasingly valued at top venues).

### Outcome 1: State-Aware VAE Beats All Baselines
**Condition:** State-aware EF@10 > unconditioned VAE EF@10 > REINVENT EF@10 > MolCRAFT
EF@10 > random/similarity baselines, with non-overlapping bootstrap 95% CIs.
**Narrative:** "Conformational state-conditioning is the key ingredient. Neither diverse
generation alone (unconditioned VAE), RL optimization (REINVENT), nor 3D pocket-conditioning
(MolCRAFT) matches the explicit state-aware approach. The discrete state label captures
pharmacologically relevant information not available in the pocket geometry alone."
**Venue implication:** Nature Computational Science candidate (if multi-kinase validates).

### Outcome 2: State-Conditioning Helps But Does Not Dominate
**Condition:** State-aware EF@10 > unconditioned VAE EF@10, but REINVENT or MolCRAFT
achieves comparable EF@10.
**Narrative:** "State-conditioning provides a measurable improvement over unconditioned
generation, but established methods can partially compensate through RL optimization or
3D pocket awareness. State-conditioning is complementary, not superior, to these approaches.
The greatest impact would come from combining state-awareness with stronger generation
methods."
**Venue implication:** JCIM -- solid benchmark contribution.

### Outcome 3: Diversity Drives Enrichment (Unconditioned = Conditioned)
**Condition:** State-aware EF@10 approximately equals unconditioned VAE EF@10 (overlapping 95%
CIs), both significantly above static baseline.
**Narrative:** "Diverse molecular generation, not conformational state-conditioning, drives
retrospective enrichment. The state-aware pipeline's advantage over the static baseline
stems from the VAE's chemical diversity, not its state labels. This is a cautionary finding:
researchers must ablate conditioning signals before attributing performance to them."
**Venue implication:** JCIM -- negative result with methodological contribution. Still
novel because no one has tested this question.

### Outcome 4: 3D Pocket-Conditioning Subsumes 1D State Labels
**Condition:** MolCRAFT EF@10 > state-aware VAE EF@10, with significant difference.
**Narrative:** "Full 3D pocket-conditioning captures conformational information more
effectively than discrete state labels. However, state-aware 1D generation achieves
competitive enrichment at a fraction of the computational cost and with guaranteed chemical
validity. The practical trade-off favors 1D methods when 3D pocket structures are
unavailable or unreliable."
**Venue implication:** JCIM -- practical insight paper.

### Outcome 5: REINVENT Dominates
**Condition:** REINVENT EF@10 > all VAE variants.
**Narrative:** "RL-optimized molecular design outperforms one-shot VAE generation for
retrospective drug identification. However, state-specific optimization (REINVENT with
per-pocket scoring) outperforms single-pocket optimization, confirming that conformational
awareness improves molecular design across generation paradigms."
**Venue implication:** JCIM -- the contribution shifts from "our VAE is better" to
"state-awareness is a transferable principle."

---

## Evaluation Criteria

### Primary Success Criteria (Required for Publication)
1. **All 5 baselines produce at least 300 valid, scoreable molecules for EGFR.** Threshold:
   >= 300 unique valid SMILES per method after filtering. If any method fails to meet this,
   document the failure and report on the methods that succeed.
2. **Bootstrap 95% CIs computed for all enrichment metrics with 10,000 resamples.** CIs must
   be reported for EF@10, EF@5, BEDROC(alpha=20), and AUC at both time-split cutoffs.
3. **At least one pairwise comparison achieves statistical significance** (Mann-Whitney U,
   p < 0.05 after Bonferroni correction for 10 comparisons, effective alpha = 0.005).
4. **Unified scoring applied consistently to all methods.** No method receives a different
   scoring function or different weights. Same 4 components, same weights (0.35/0.30/0.20/0.15).

### Secondary Success Criteria (Strengthen the Paper)
5. **Unconditioned VAE ablation resolves the confound.** The conditioned vs unconditioned
   comparison produces either a significant difference (state-conditioning contributes) or a
   non-significant difference (diversity dominates). Either is informative; ambiguity is not.
6. **MolCRAFT 3D outputs achieve >= 70% PoseBusters validity.** If below 70%, the 3D comparison
   is weakened; report with appropriate caveats.
7. **Weight sensitivity analysis confirms robustness.** The ranking of methods should be
   consistent across >= 60% of 100 random Dirichlet weight configurations.
8. **Retrospective enrichment directionally consistent at both time-splits.** If Method A
   beats Method B at pre-2010, it should also beat Method B at pre-2015 (or the inconsistency
   must be explained).

### Metrics Reported Per Method

| Metric Category | Specific Metrics |
|-----------------|-----------------|
| Enrichment | EF@5, EF@10, BEDROC(alpha=20), AUC with bootstrap 95% CIs |
| Binding | Vina score distribution (mean, median, std), GNINA CNN score |
| Drug-likeness | QED distribution, SA score distribution, Lipinski pass rate |
| Diversity | Mean pairwise Tanimoto distance, scaffold diversity (Bemis-Murcko) |
| Validity | Chemical validity %, unique %, novel % (vs training data) |
| Synthesis | SA score, RAscore if available |
| Statistical | Mann-Whitney U p-values, Cohen's d, Bonferroni-corrected significance |
| 3D quality | PoseBusters validity % (MolCRAFT only) |

---

## Open Questions

1. **Should REINVENT use GNINA or AutoDock Vina for docking scoring?** GNINA is what
   StateBind uses, making the comparison most fair. But REINVENT natively supports Vina.
   Using GNINA requires a custom plugin. Recommendation: implement GNINA plugin for primary
   results; report Vina as supplementary for transparency. If GNINA plugin proves infeasible,
   Vina is acceptable since both are physics-based docking tools.

2. **Should MolCRAFT be fine-tuned on EGFR?** Zero-shot (pre-trained checkpoint, no
   EGFR-specific training) is the cleanest comparison: it tests what MolCRAFT can do
   out of the box on a new pocket. Fine-tuning would improve MolCRAFT's performance but
   complicates the comparison (is it the architecture or the fine-tuning that helps?).
   Recommendation: primary results with zero-shot; supplementary with fine-tuning if
   zero-shot performance is anomalously low.

3. **How to handle the state-specificity score for non-state-aware methods?** The unified
   scoring function assigns state specificity = 0.0 to methods without state labels (same
   as the static baseline). For REINVENT with per-pocket scoring, molecules can be assigned
   to the pocket they were optimized for, giving state specificity = 1.0 for single-state
   molecules. For MolCRAFT, each molecule is generated for one pocket, similarly assignable.
   For the unconditioned VAE and random/similarity baselines, state specificity = 0.0.
   This is consistent with the current framework but means non-state-aware methods lose
   15% of the maximum score. An alternative is to report results both with and without the
   state specificity component to separate this effect.

4. **Should DiffSBDD be included alongside MolCRAFT?** DiffSBDD was published in Nature
   Computational Science, the aspirational target venue, making it particularly relevant.
   However, its 38% PoseBusters validity weakens it as a representative 3D method. Including
   both adds approximately 1 week of effort. Recommendation: include as supplementary if
   time permits; prioritize MolCRAFT for the main comparison.

5. **Pre-registration: formal or informal?** Should the outcome-to-narrative mapping be
   posted on a preprint server (e.g., Authorea or OSF) before experiments run? Formal
   pre-registration strengthens credibility but delays the timeline by approximately 1 week.
   Recommendation: post on OSF with a timestamp; this takes hours, not weeks.

---

## References

1. Gao, W. et al. "Sample Efficiency Matters: A Benchmark for Practical Molecular
   Optimization." *NeurIPS Datasets & Benchmarks*, 2022. https://arxiv.org/abs/2206.12411

2. Loeffler, H.H. et al. "Reinvent 4: Modern AI-driven generative molecule design."
   *Journal of Cheminformatics* 16, 2024. https://doi.org/10.1186/s13321-024-00812-5

3. Qu, Y. et al. "MolCRAFT: Structure-Based Drug Design in Continuous Parameter Space."
   *ICML*, 2024. https://arxiv.org/abs/2404.12141

4. Schneuing, A. et al. "Structure-based drug design with equivariant diffusion models."
   *Nature Computational Science* 4, 2024. https://doi.org/10.1038/s43588-024-00737-x

5. Nie, C. et al. "Durian: A Comprehensive Benchmark for Structure-Based 3D Molecular
   Generation." *JCIM* 65, 2025. https://doi.org/10.1021/acs.jcim.4c02232

6. "Benchmarking 3D Structure-Based Molecule Generators." *JCIM* 65(15), 8006-8021, 2025.
   https://doi.org/10.1021/acs.jcim.5c01020

7. "Structure-based Drug Design Benchmark: Do 3D Methods Really Dominate?"
   arXiv:2406.03403, 2024.

8. "Beyond Affinity: A Benchmark of 1D, 2D, and 3D Methods Reveals Critical Trade-offs in
   Structure-Based Drug Design." arXiv:2601.14283, 2025.

9. Buttenschoen, M. et al. "PoseBusters: AI-based docking methods fail to generate
   physically valid poses or generalise to novel sequences." *Chemical Science* 15, 2024.
   https://doi.org/10.1039/D3SC04185A

10. Truchon, J.-F. & Bayly, C.I. "Evaluating Virtual Screening Methods: Good and Bad
    Metrics for the 'Early Recognition' Problem." *JCIM* 47(2), 488-508, 2007.
    https://doi.org/10.1021/ci600426e

11. Nicholls, A. "Confidence limits, error bars, and method comparison in molecular
    modeling." *JCAMD* 30, 2016. https://doi.org/10.1007/s10822-015-9861-4

12. Ash, J.R. & Bhardwaj, R.M. "Confidence bands and hypothesis tests for hit enrichment
    curves." *J. Cheminformatics* 14, 2022. https://doi.org/10.1186/s13321-022-00629-0

13. Clark, R.D. & Webster-Clark, D.J. "The power metric: a new statistically robust
    enrichment-type metric." *J. Cheminformatics* 8, 2016.
    https://doi.org/10.1186/s13321-016-0189-4

14. Perme, M.P. & Manevski, D. "Confidence intervals for the Mann-Whitney test."
    *Statistical Methods in Medical Research* 28(12), 2019.
    https://doi.org/10.1177/0962280218814556

15. "Kinase-Bench: Comprehensive Benchmarking Tools and Guidance for Achieving Selectivity
    in Kinase Drug Discovery." *JCIM* 64(24), 9528-9550, 2024.
    https://doi.org/10.1021/acs.jcim.4c01830

16. Zhou, G. et al. "Uni-Mol: A Universal 3D Molecular Representation Learning Framework."
    *ICLR*, 2023. https://github.com/deepmodeling/Uni-Mol

17. Swanson, K. et al. "ADMET-AI: A machine learning ADMET platform for evaluation of
    large-scale chemical libraries." *Bioinformatics* 40(7), 2024.
    https://doi.org/10.1093/bioinformatics/btae416

18. Ung, P.M. et al. "Quantitative conformational profiling of kinase inhibitors reveals
    origins of selectivity for Aurora kinase activation states." *PNAS* 115(51), 2018.
    https://doi.org/10.1073/pnas.1811158115

19. "STAR-VAE: Latent Variable Transformers for Scalable and Controllable Molecular
    Generation." arXiv:2511.02769, 2025.

20. "Conditional beta-VAE for De Novo Molecular Generation." arXiv:2205.01592, 2022.

21. "MolecularAI/REINVENT4." GitHub, v4.7, 2025. https://github.com/MolecularAI/REINVENT4

22. "GenSI/MolCRAFT." HuggingFace, 2024. https://huggingface.co/GenSI/MolCRAFT

23. "GNINA 1.3: the next increment in molecular docking with deep learning."
    *J. Cheminformatics*, 2025. https://doi.org/10.1186/s13321-025-00973-x

24. Cremer, J. et al. "FLOWR: Flow matching for structure-based drug design."
    arXiv, 2025.

25. "PropMolFlow: property-guided molecule generation with geometry-complete flow matching."
    *Nature Computational Science*, 2025. https://doi.org/10.1038/s43588-025-00946-y
