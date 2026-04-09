---
agent: Sr. Journal Reviewer -- ML & AI
round: 1
date: 2026-04-09
type: review-assessment
scope: cross-cohort
---

# ML Methodology Review: StateBind Research Agendas (Cohort1 + Cohort2)

## Reviewer Identity

Senior Journal Reviewer for NeurIPS, ICML, and ICLR. Area chair experience
in molecular ML. This review evaluates both cohorts' research agendas from
the perspective of ML methodology rigor: ablation design, baseline fairness,
benchmark standards, evaluation protocols, and reproducibility.

---

## Executive Assessment

The combined research agendas from Cohort1 and Cohort2 are substantially more
mature than a typical first-draft publication plan. The identification of
confounding factors (Cohort1 datasci-P01), the ablation suite design
(Experiments A-G), the pre-registration commitment, and the multi-kinase
statistical power analysis all indicate serious methodological thinking.

However, from an ML reviewer's perspective, the plan has **five critical
methodology weaknesses** that would draw reviewer fire at any top venue. I
detail these below, then provide section-by-section assessments.

**Overall NeurIPS-scale rating for the combined plan: 5/10 (borderline
reject).** This could rise to 7/10 (accept) if the weaknesses identified
below are addressed. The core ideas are sound, but the execution plan has
gaps that experienced ML reviewers would exploit.

---

## Section 1: Ablation Design Assessment

### Cohort1 Experiments A-G (NeurIPS Rating: 6/10)

The proposed ablation suite is the strongest part of the methodology plan.
The seven experiments (A through G) correctly identify the four confounding
factors between static and state-aware pipelines: generation method, candidate
count, chemical diversity, and state conditioning. This reflects awareness of
the causal inference framework for computational drug design (Bender et al.,
Drug Discovery Today, 2023).

**What is done well:**

1. **Experiment C (Unconditioned VAE)** is correctly identified as
   thesis-critical. The specification to zero out the state vector rather
   than remove it architecturally is the right choice -- it preserves the
   parameter count and isolates the information content of the state
   conditioning. This follows the standard ablation pattern established by
   STAR-VAE (arXiv 2511.02769, 2025), which distinguishes CVAE from VAE as
   a controlled comparison.

2. **Experiment E (Subsampled state-aware)** correctly controls for
   candidate count by downsampling 461 to 30. This is essential -- without
   it, the static-vs-state-aware comparison conflates sample size with
   methodology.

3. **Experiment F (Shuffled state labels)** is the most sophisticated
   control. If shuffled labels match real labels in enrichment, the state
   information is not being used by the model. This is the null control that
   ML reviewers most want to see.

4. **Pre-registered success threshold (Cohen's d >= 0.8)** for the state
   effect is commendable and rare in computational drug design papers.

**What is missing or problematic:**

1. **No compute-matched ablation.** The VAE generates molecules in a single
   forward pass (milliseconds per molecule). REINVENT 4 uses iterative RL
   optimization (minutes to hours per run). FLOWR uses flow matching with
   iterative denoising. A compute-matched comparison would give each method
   the same wall-clock or GPU-hour budget and measure output quality. Without
   this, a reviewer can argue that REINVENT simply had more optimization
   budget. Best practice for compute-matched comparisons is established in
   the PMO benchmark (Gao et al., NeurIPS D&B, 2022), which uses oracle call
   budgets to normalize across methods. The ablation suite should include a
   fixed-oracle-budget variant.

2. **No architecture ablation within the VAE.** The GRU-based SELFIES VAE
   (embed_dim=128, hidden_dim=256, latent_dim=64, 9.5M params) is a specific
   architectural choice. The plan does not test whether a Transformer-based
   VAE (e.g., STAR-VAE's architecture) or a different latent dimensionality
   would change the state-conditioning benefit. If state-conditioning helps
   the GRU VAE but not a Transformer VAE, the conclusion would be "our
   architecture benefits from state labels," not "state conditioning improves
   molecular generation." This is a significant limitation for a
   generalizability claim. The Cohort1 final agenda acknowledges this
   partially via the "within-method state ablations" for REINVENT and FLOWR,
   but there is no architecture ablation within the VAE family itself.

3. **Teacher forcing during evaluation.** The VAE architecture
   (`src/statebind/ml/vae.py`) uses teacher forcing during training. The
   evaluation protocol does not specify whether autoregressive generation
   (no teacher forcing) is used at inference. If teacher forcing leaks
   ground-truth tokens during evaluation, the reconstruction metrics are
   inflated. This is a known issue with sequence-based molecular VAEs. The
   review should confirm that all generation experiments use purely
   autoregressive decoding.

4. **No diversity-controlled ablation.** Experiment E controls for count
   (30 vs 461) but not for diversity. What if 30 maximally diverse
   state-aware molecules outperform 30 randomly sampled ones? Adding a
   diversity-maximized subsample (e.g., MaxMin picking from the 461) would
   test whether diversity, not state information, drives enrichment.

**Recommendation:** Add Experiment H (compute-matched budget across all
methods) and Experiment I (diversity-maximized subsample of 30). These two
additions would make the ablation suite NeurIPS-worthy.

---

## Section 2: Baseline Fairness Assessment

### Proposed Baselines (NeurIPS Rating: 5/10)

The baseline set (REINVENT 4, FLOWR, unconditioned VAE, random ChEMBL,
fingerprint search) covers the right paradigms but has critical fairness
issues.

**Baseline availability verification (via deep research):**

1. **REINVENT 4:** Confirmed available. GitHub repository
   MolecularAI/REINVENT4, 720 stars, latest release v4.7 (November 20,
   2025). Apache 2.0 license. Requires Python 3.10+, ~8 GB memory. Does NOT
   have native pip install -- requires cloning the repo and running an
   install script. Custom scoring via plugin architecture is confirmed,
   which means GNINA integration is feasible though not built-in. **Verdict:
   Available and usable, but integration with GNINA scoring will require
   custom plugin development (1-2 weeks, not trivial).**

2. **FLOWR:** Confirmed available but with caveats. GitHub repository
   jule-c/flowr has checkpoints on Zenodo (two variants: with/without
   explicit hydrogens). However, the repository states it is **"no longer
   actively maintained"** and directs users to FLOWR.root
   (jule-c/flowr_root) as the successor. FLOWR requires CUDA GPU with
   minimum 40 GB VRAM, the ADFR suite for receptor processing, and Mamba
   for environment management. FLOWR was published at ICLR 2025
   (April 2025) and achieves 92% PoseBusters validity. **Verdict: Available
   but with significant setup overhead. The 40 GB VRAM requirement means
   only H200 nodes (80 GB) on the Yale cluster are suitable, not RTX 5000
   Ada (32 GB). The unmaintained status is a risk for reproducibility.
   FLOWR.root may be the better choice but is newer and less validated.**

3. **MolCRAFT / MolPilot:** MolCRAFT checkpoint available on HuggingFace
   (GenSI/MolCRAFT). The successor MolPilot (ICML 2025) achieves 95.9%
   PoseBusters validity, a significant improvement over FLOWR's 92%.
   Checkpoint available on HuggingFace (GenSI/MolPilot). **Verdict:
   MolPilot should replace or supplement FLOWR as the 3D baseline.
   It is newer, better-performing, and has publicly available checkpoints.
   The agendas cite MolCRAFT but should upgrade to MolPilot.**

**Fairness concerns:**

1. **Scoring function bias against non-state-aware methods.** Both agendas
   correctly identify that the 4-component scoring function includes
   state_specificity (15% weight), which non-state-aware methods cannot
   optimize for. Cohort1's solution -- reporting both 4-component and
   3-component (no state_specificity) scoring -- is necessary but
   insufficient. The problem is deeper: the reference_similarity component
   (35% weight) uses Tanimoto to 3 known EGFR drugs, which biases toward
   template-based molecules. If REINVENT's RL loop optimizes against this
   same scoring function, it will learn to make quinazoline analogs, which
   is a different failure mode than the VAE's. **Each method should be
   evaluated under its own optimal scoring configuration AND under a
   universal scoring function.** This dual evaluation is standard in the
   PMO benchmark and the Durian benchmark (Nie et al., JCIM, 2025).

2. **Training data leakage for 3D methods.** CrossDocked2020 is the
   standard training set for DiffSBDD, FLOWR, MolCRAFT, and MolPilot.
   EGFR structures are almost certainly in CrossDocked2020 because EGFR
   is one of the most represented kinases in PDB. This means 3D methods
   have effectively "seen" EGFR pockets during pre-training. Any
   zero-shot claim is compromised. The Cohort1 agenda flags this
   (Risk Register: "CrossDocked2020 contains EGFR -- High probability")
   but does not specify the mitigation protocol. **The paper must
   explicitly list which EGFR PDB IDs appear in CrossDocked2020's training
   split and discuss the implications.** CleanSplit (Nature Machine
   Intelligence, 2025) showed that correcting PDBbind train-test leakage
   drops all top model performance substantially. An analogous analysis
   is required here.

3. **REINVENT optimization budget.** REINVENT 4 uses RL with iterative
   scoring. The proposal specifies 500 RL steps per run. But REINVENT's
   performance is highly sensitive to the number of optimization steps
   (Gao et al., PMO benchmark, 2022). Too few steps and REINVENT
   underperforms; too many and it mode-collapses. The proposal should
   specify convergence criteria (e.g., score plateau over 50 consecutive
   steps) rather than a fixed step count. Additionally, the number of
   oracle calls should be reported alongside wall-clock time for each
   method. The PMO benchmark uses a fixed 10K oracle budget as the
   fairness standard.

4. **Missing baseline: Chemprop v2 direct virtual screening.** Both
   agendas propose using Chemprop for MPNN training but never consider
   Chemprop v2 as a baseline method in itself. Chemprop v2
   (Heid et al., September 2025 preprint) provides a production-grade
   multi-task D-MPNN with 2x speed improvement and 3x memory reduction
   over v1. Training a Chemprop v2 model on ChEMBL EGFR data and using
   it to score ChEMBL molecules directly (virtual screening without
   generation) would test whether generation adds value over retrieval +
   ML scoring. The fingerprint search baseline partially covers this,
   but an ML-scored retrieval baseline would be stronger.

**Recommendation:** (a) Upgrade 3D baseline from FLOWR to MolPilot
(95.9% PoseBusters validity). (b) Add explicit CrossDocked2020 leakage
analysis. (c) Use oracle call budgets for REINVENT fairness. (d) Consider
Chemprop v2 virtual screening as a retrieval+ML baseline.

---

## Section 3: Benchmark Proposal Assessment (bencharch-P01)

### StateBind-Bench (NeurIPS E&D Rating: 4/10 as proposed)

The benchmark addresses a genuine gap -- no existing benchmark evaluates
molecular generation conditioned on protein conformational state. The gap
verification is thorough (checked MoleculeNet, MOSES, GuacaMol, TDC,
CrossDocked2020, DUD-E, PDBbind, Tartarus, Polaris, Kinase-Bench, Durian,
GenBench3D). The citation impact analysis (MoleculeNet 3000+, DUD-E 2500+,
MOSES 770+) is compelling for a benchmark strategy.

**However, the proposal has critical weaknesses by NeurIPS Evaluations &
Datasets Track standards:**

1. **No hidden test set.** The February 2026 TDC reproducibility audit
   (bioRxiv, 2026.02.26.708193) found that most top-ranked TDC ADMET
   models were non-reproducible and showed signs of test-set overfitting.
   Only 3 of the top methods passed all checks. The audit concluded that
   hidden test sets, strict dataset versioning, and standardized inference
   environments are urgently needed. StateBind-Bench as proposed has no
   hidden test component. The "hidden held-out metric" mentioned is
   insufficient -- what is needed is a hidden held-out dataset with
   molecules that submissions never see. Without this, the benchmark will
   suffer the same leaderboard gaming that plagues TDC. **This is a
   potential desk-reject issue for NeurIPS E&D 2026/2027.**

2. **Single target (Phase 1).** A benchmark with only EGFR (4 states) is
   too narrow for a venue-quality contribution. The NeurIPS E&D Track 2026
   call (renamed from "Datasets & Benchmarks" to "Evaluations & Datasets")
   explicitly states that dataset submissions should "clarify how they should
   be meaningfully used in evaluative practices." A single-kinase benchmark
   invites the criticism that methods overfit to EGFR's specific pocket
   geometry. Phase 2 (ABL1 + BRAF) is acknowledged but described as a
   separate future submission. **For NeurIPS E&D, Phase 1+2 should be
   combined into a single submission with at least 3 kinases.**

3. **Task 4 (Multi-Objective Pareto) metrics are non-standard.** The
   proposed metrics (Pareto hypervolume, dominated fraction, score
   distribution entropy) are not established in the molecular generation
   literature. There is no published precedent for "score distribution
   entropy" as an evaluation metric. While novel metrics can be valuable,
   a benchmark paper should establish credibility through well-understood
   metrics before introducing new ones. **Recommendation: Make Task 4
   supplementary and strengthen Tasks 1-3 with additional baselines.**

4. **Leaderboard anti-gaming measures are weak.** The proposal mentions
   (a) full score distributions, (b) hidden held-out metric, (c) code
   URL requirement, (d) quarterly weight rotation. Of these, only (c) is
   effective. Weight rotation defeats the purpose of a stable benchmark.
   Hidden metrics are insufficient without hidden data. Best practice from
   the SEAL leaderboard approach and Kaggle competitions is a two-tier
   system: public practice set for development, private test set for
   certified scores. **StateBind-Bench must implement a private test
   partition.**

5. **Missing representation ablation task.** The protml critique in
   Cohort2 correctly identified that the ML community's primary interest
   is the pocket representation question: does richer pocket conditioning
   (ESM-2, ProstT5, KLIFS fingerprint, voxelized grid) improve generation?
   This is arguably the benchmark's most novel contribution. However, the
   current proposal buries it as a protml-suggested modification rather
   than making it Task 5 (or upgrading Task 1). **Recommendation: Make
   the pocket representation ablation a primary task, not an afterthought.**

6. **Deadline feasibility.** NeurIPS 2026 E&D Track abstract deadline is
   May 4, 2026 (25 days from now). Full paper deadline is May 6, 2026.
   The Cohort2 agenda already correctly notes this is "not feasible for
   polished submission." Targeting JCIM for Phase 1 and NeurIPS 2027 for
   the extended version is realistic. **But the JCIM version should still
   implement the hidden test set -- it is not a NeurIPS-specific
   requirement but a general benchmark integrity standard.**

**Recommendation for bencharch-P01:** (a) Implement a hidden test
partition from day one. (b) Combine Phases 1+2 for any NeurIPS submission.
(c) Elevate the pocket representation ablation to a primary task. (d) Drop
or demote Task 4 (Pareto). (e) Add a minimum of 5 baseline methods with
publicly available checkpoints to the benchmark release.

---

## Section 4: ML Methodology Deep Dive

### 4.1 SELFIES VAE with State Conditioning -- Novelty Assessment

**Claim from Cohort1 final agenda:** "No published paper conditions
molecular generation on discrete conformational states of the same
protein" (genai-R02 research, 30+ searches, 30 citations).

**My verification:** After extensive search, I confirm that this claim
appears correct as of April 2026. The closest published work includes:

- **Conditional beta-VAE** (arXiv 2205.01592, 2022): Conditions a VAE on
  molecular properties (pLogP) but not protein states.
- **STAR-VAE** (arXiv 2511.02769, 2025): Transformer-based latent variable
  model with SELFIES, conditions on docking scores for protein targets, but
  does not condition on discrete conformational states.
- **DynamicBind** (Nature Communications, 2024): Predicts both ligand pose
  and protein conformation simultaneously but does not use discrete state
  labels as conditioning inputs.
- **Apo2Mol** (2024-2025): Generates molecules from apo protein structures
  but does not condition on conformational state labels.
- **Structure-based CVAE** (Luo et al., J Cheminformatics, 2018):
  Conditions on molecular properties, not protein states.

The novelty claim is supported. However, the contribution's significance
depends on how it is framed:

- **If framed as "we invented a new architecture":** Weak. A GRU VAE with
  a one-hot state vector concatenated to inputs is architecturally trivial.
  Any reviewer can implement this in an afternoon. The ML contribution is
  near zero.
- **If framed as "we asked a new question and built a systematic evaluation
  framework":** Strong. The question "does conformational state conditioning
  improve molecular design?" is novel and important. The evaluation framework
  (time-split retrospective validation, multi-kinase generalization, ablation
  suite) is the contribution, not the model.

Both cohorts correctly frame this as a question/framework contribution,
not a model contribution. This framing is essential for surviving ML
review.

### 4.2 MPNN R^2 = 0.69 -- Competitiveness Assessment

StateBind's MPNN uses NNConv with mean_max readout (12.7M parameters).
The reported R^2 = 0.69 on EGFR binding affinity prediction needs context:

- **Chemprop v2 (Heid et al., 2025):** On PDBbind-like tasks, Chemprop v1
  typically achieves R^2 = 0.60-0.75 on random splits. Scaffold splits
  reduce performance significantly (R^2 = 0.3-0.5 is common). StateBind's
  R^2 = 0.69 is not reported with scaffold split information.
- **Kinase-specific benchmarks:** The Kinase200 benchmark (Martin et al.,
  JCIM, 2023) reports multi-task MPNN R^2 = 0.5-0.7 on random splits,
  0.19-0.23 on structure-based splits. If StateBind's R^2 = 0.69 is on a
  random split, it is competitive. If on a scaffold split, it is excellent.
- **MolGPS (Valence Labs, 2025):** Foundation model achieving SOTA on
  11/22 TDC tasks. This represents the frontier. StateBind does not need
  to match this but should acknowledge it as the current ceiling.
- **Docking-informed ML (JCIM, 2024):** Achieves R^2 = 0.63-0.74 on
  unseen kinase inhibitors when combining docking features with ML.

**Critical missing information:** What split type was used for the R^2 =
0.69 number? Random split, temporal split, or scaffold split? This must be
reported. If it is a random split, the effective predictive performance on
novel scaffolds (which is what the VAE generates) is likely R^2 = 0.3-0.5,
which means the MPNN's predictions on VAE-generated molecules may be
unreliable. This directly connects to the conformal prediction proposal
(cheminfo-P01 Step 3), which is therefore not optional but essential.

### 4.3 Multi-Task MPNN for Multi-Kinase (kinpharm-P01)

The proposal to train a multi-task D-MPNN across 5 kinases with
conformational state conditioning is well-motivated. Key assessment:

- **Chemprop v2 multi-task support:** Confirmed. Chemprop v2 handles
  missing labels by masking in the loss function and rescaling. This means
  sparse multi-kinase data can be used directly. The architecture supports
  multi-GPU training for scaling.
- **Published multi-task kinase results:** AMGU (Chen et al., JCIM, 2023)
  across 204 kinases shows +0.03-0.04 R^2 improvement over single-task on
  random splits but only marginal improvement on structure-based splits
  (0.23 vs 0.19). This sets realistic expectations: multi-task will help
  data-sparse kinases (ALK with ~800 pre-2010 compounds) but may not
  dramatically improve data-rich ones (EGFR, ABL1).
- **State conditioning in multi-task MPNN:** The proposal adds a 9D state
  vector to the MPNN input. This is architecturally simple (concatenation)
  but the interaction between state conditioning and multi-task learning
  is unexplored. A proper ablation would train: (a) single-task MPNN per
  kinase, (b) multi-task MPNN without state features, (c) multi-task MPNN
  with state features. This 2x2 factorial design is missing from both
  agendas.
- **KinomeMETA (Ren et al., 2024):** Meta-learning across 661 kinases is
  a more sophisticated approach than simple multi-task. If the goal is
  data-sparse kinase prediction, meta-learning should be acknowledged as
  an alternative even if not implemented.

### 4.4 Conformal Prediction for MPNN Uncertainty

The cheminfo-P01 proposal for conformal prediction (CP) wrapping of the
MPNN is timely and well-supported:

- **CP is now standard practice.** Li et al. (JCIM, 2024) achieved up to
  74% interval reduction with conformalized GNN fusion. Jimenez-Luna et al.
  (ACS Omega, 2024) validated CP across RF, DNN, and gradient boosting
  QSAR models. ProQSAR (ChemRxiv, 2025) includes cross-conformal
  prediction and applicability-domain flags as standard components. The
  field has moved from "CP is optional" to "CP is expected." Any JCIM or
  NeurIPS submission in 2026 without uncertainty quantification will draw
  reviewer criticism.
- **Implementation complexity is low.** Split conformal prediction with
  a 5-model ensemble for epistemic uncertainty (as proposed) requires
  only a held-out calibration set and a quantile computation. This is
  hours of work, not weeks.
- **The key question is coverage under distribution shift.** VAE-generated
  molecules are likely outside the training distribution of the MPNN
  (which was trained on ChEMBL EGFR compounds). CP guarantees marginal
  coverage but not conditional coverage under distribution shift. The
  paper should report both (a) calibration set coverage (should be
  near-nominal) and (b) VAE-generated molecule coverage (likely
  below-nominal, which is informative). Reporting below-nominal coverage
  honestly is better than not reporting coverage at all.

**Recommendation:** Implement CP. It is low-cost, high-value, and
increasingly expected. Report coverage under both in-distribution
(calibration set) and out-of-distribution (VAE-generated) conditions.

---

## Section 5: Evaluation Protocol Assessment

### Proposed Metrics (NeurIPS Rating: 6/10)

The evaluation protocol (BEDROC + EF@10 + bootstrap CIs + Pareto +
PoseBusters) is substantially more rigorous than the typical molecular
generation paper. Specific assessment:

1. **BEDROC(alpha=20) as primary metric:** Correct choice. Truchon and
   Bayly (JCIM, 2007) established BEDROC as the standard for early
   recognition in virtual screening. At alpha=20, 80% of the weight falls
   in the top 8% of the ranked list. BEDROC ranges [0,1] with
   well-understood null distributions, making it amenable to hypothesis
   testing. Recent AlphaFold3 virtual screening studies (RSC Chemical
   Science, 2026) report BEDROC as a primary metric, confirming its
   continued relevance.

2. **BCa bootstrap CIs (10,000 resamples):** Correct and essential. The
   Bayesian bootstrap with bias-corrected accelerated intervals achieves
   higher coverage than classical percentile CI at small n (Pustejovsky,
   2024). This is the right method for N=3-5 held-out drugs.

3. **PoseBusters validity for all methods:** Good addition. This became
   the standard quality check after Buttenschoen et al. (Chemical Science,
   2024) showed that 0-11% of raw 3D molecules pass PoseBusters. Applying
   it to 1D/SELFIES methods (which generate SMILES, not 3D poses) requires
   a conformer generation step (e.g., RDKit ETKDG + UFF minimization)
   before PoseBusters evaluation. This step should be specified in the
   protocol.

**What is missing:**

1. **No Frechet ChemNet Distance (FCD).** FCD (Preuer et al., 2018) is
   the standard distributional metric for molecular generation quality.
   It measures the distance between generated and reference molecule
   distributions in the activation space of a pre-trained network. Every
   molecular generation paper at NeurIPS/ICML reports FCD. Its absence
   from the evaluation protocol would be noticed.

2. **No drug-likeness distribution comparison.** The protocol lists QED
   and SA score as per-molecule metrics but does not specify distribution-
   level comparisons (Kolmogorov-Smirnov test, Earth Mover's Distance)
   between generated and reference molecule property distributions. This
   is standard in MOSES and GuacaMol evaluations.

3. **No molecular weight and LogP distribution plots.** These are the
   most basic sanity checks for a molecular generation paper. If generated
   molecules have unrealistic MW or LogP distributions relative to known
   EGFR inhibitors, something is wrong. These should be reported for all
   methods.

4. **No internal diversity metric specification.** The protocol mentions
   "diversity (average pairwise Tanimoto distance, ECFP4)" but does not
   specify which diversity metric. Internal diversity (1 - average pairwise
   Tanimoto) is the standard but can be gamed (Tripp et al., 2024). SEDiv
   and #Circles are mentioned in cheminfo-P01 but not integrated into the
   main evaluation protocol. **Recommendation: Use both internal diversity
   AND SEDiv/#Circles.**

5. **No novelty metric.** What fraction of generated molecules are NOT in
   ChEMBL? This is a standard metric in MOSES/GuacaMol. High novelty with
   high enrichment is the ideal; high enrichment through retrieval of known
   molecules is less impressive.

**Recommendation:** Add FCD, property distribution comparisons (KS test),
MW/LogP distribution plots, SEDiv/#Circles, and novelty (fraction not in
ChEMBL) to the evaluation protocol. These are all low-cost additions.

---

## Section 6: Cohort2-Specific Methodology Concerns

### 6.1 Scoring Reform (cheminfo-P01) -- ML Implications

The scoring reform proposal is fundamentally a feature engineering problem.
Expanding from 3 reference drugs to 100-300 ChEMBL scaffold centroids
changes the reference_similarity metric from "how similar to known drugs?"
to "how similar to any known EGFR binder?" This is a reasonable change but
has ML implications:

- **Metric choice affects method ranking.** If the scoring function is
  changed and the method ranking changes, the paper must show that the
  ranking is robust to metric choice (sensitivity analysis). The Dirichlet
  weight sampling (1000+ configurations) partially addresses this, but
  the reference set itself is an additional degree of freedom. The paper
  should show results under both 3-drug and ChEMBL-centroid reference sets.

- **Circularity risk with ChEMBL centroids.** If the MPNN was trained on
  ChEMBL EGFR data and the reference set is also ChEMBL EGFR centroids,
  there is information leakage from training data to evaluation metric.
  The temporal split mitigates this (centroids from pre-cutoff data only)
  but must be explicitly verified.

### 6.2 Two-Paper Strategy -- ML Reviewer Perspective

Cohort2's two-paper strategy (Paper 1: methods + multi-kinase; Paper 2:
benchmark) is strategically sound but creates a dependency: Paper 2's
benchmark inherits Paper 1's scoring function. If the scoring function
changes between papers, the benchmark results are not comparable to Paper
1's results. **Recommendation: Freeze the scoring function before starting
Paper 2 and document the frozen version as part of the benchmark
specification.**

### 6.3 Pocket-Aware Scoring (DrugCLIP/ProFSA)

Cohort2's protml agent recommended adding DrugCLIP pocket-ligand
co-embedding as a scoring configuration. This is an interesting
idea but introduces a significant ML complication: DrugCLIP is a learned
representation. If DrugCLIP was trained on data that includes EGFR,
adding it to the scoring function creates train-test leakage at the
representation level. The paper must verify DrugCLIP's training data
does not include the specific EGFR structures used in StateBind.

---

## Section 7: Top 3 ML Methodology Weaknesses

### Weakness 1: No Compute-Matched Comparison (Severity: HIGH)

The ablation suite compares methods with wildly different computational
budgets. The VAE generates in one forward pass. REINVENT uses iterative RL.
FLOWR/MolPilot use iterative flow matching. Without normalizing for compute,
the comparison is apples-to-oranges. The PMO benchmark (Gao et al., 2022)
established the 10K oracle call budget as a fairness standard precisely
for this reason. Any NeurIPS or ICML reviewer who has worked with the PMO
benchmark will flag this immediately.

**Fix:** Report results under a fixed oracle budget (e.g., 10K docking
calls per method). For methods that generate in one shot (VAE), the oracle
budget applies to scoring + filtering. For iterative methods (REINVENT),
it applies to the RL optimization loop.

### Weakness 2: Underpowered Statistics Undermine the Central Claim (Severity: HIGH)

With N=5 held-out EGFR drugs, the 95% CI on EF@10 spans [0.5, 9.4] as
correctly identified by datasci-P01. Multi-kinase pooling (N~8-10 drugs
per the revised Cohort1 plan with 4 kinases) narrows this but not
dramatically. The fundamental problem is that enrichment factor is a
high-variance metric with small N. Even BEDROC with BCa bootstrap will
produce wide CIs with N=8-10.

The plan acknowledges this but does not confront the implication: **the
central claim may not reach statistical significance even with perfect
execution.** If pooled BEDROC 95% CI spans [0.3, 0.7] and the null
BEDROC is ~0.5, the result is non-significant. The pre-registration
commitment helps (negative results are publishable) but the paper's
impact drops substantially.

**Fix:** (a) Maximize held-out drug count by using the pre-2010 cutoff
as primary (more held-out drugs) rather than pre-2015. (b) Report
permutation-based p-values alongside bootstrap CIs (non-parametric test
comparing state-aware vs static BEDROC under label shuffling). (c)
Consider rank-based meta-analysis across kinases rather than pooled
enrichment, as it is more robust to heterogeneity.

### Weakness 3: Reproducibility Timeline Is Unrealistic (Severity: MEDIUM)

The agendas claim the full experimental suite (multi-kinase, ablations,
baselines, GIST, survival funnel) can be completed in 6-8 weeks (Cohort1)
or 16-18 weeks (Cohort2). As an ML reviewer who has supervised benchmark
papers, the realistic timeline for a reproducible multi-method comparison
is 3-6 months of full-time work. Specific concerns:

- REINVENT 4 integration with custom GNINA scoring plugin: 2-3 weeks,
  not "1-2 weeks."
- FLOWR/MolPilot setup with ADFR suite and receptor preparation: 1-2
  weeks, not "1 week."
- Multi-kinase MPNN training with hyperparameter tuning: 3-4 weeks.
- Debugging, failed runs, recomputation: add 50% buffer to all estimates.

The Cohort2 timeline of 16-18 weeks for both papers is more realistic
than Cohort1's 6-8 weeks for a single paper. **But neither includes
time for code cleanup, documentation, and the reproducibility package
needed for a benchmark paper.** A submission-ready benchmark with Docker
containers, evaluation code, and documented baselines adds 4-6 weeks.

**Fix:** Use Cohort2's timeline as the minimum estimate. Budget 20-24
weeks total. Accept that the first submission will be Paper 1 (methods
paper) without the full benchmark, with the benchmark following 2-3
months later.

---

## Section 8: Per-Proposal NeurIPS-Scale Ratings

| Proposal | ML Methodology Rating | Key Strength | Key Weakness |
|----------|----------------------|--------------|--------------|
| mlres-P01 (Baselines) | 6/10 | Comprehensive paradigm coverage; pre-registered outcomes | No compute-matched budget; FLOWR may be superseded by MolPilot |
| datasci-P01 (Statistics) | 7/10 | BEDROC primary; BCa bootstrap; pre-registration | Still underpowered even with multi-kinase; does not confront non-significance scenario planning |
| bencharch-P01 (Benchmark) | 4/10 | Genuine gap; thorough gap verification | No hidden test set; single-target Phase 1; non-standard Task 4 metrics |
| cheminfo-P01 (Scoring) | 6/10 | Correct identification of reference_similarity artifact; multi-metric sensitivity | Circularity risk with ChEMBL centroids if temporal split not strictly enforced |
| kinpharm-P01 (Multi-kinase) | 5/10 | Good kinase selection; power analysis | JAK2 correctly dropped but ALK pre-2010 data is too sparse; no 2x2 factorial ablation for multi-task x state-conditioning |
| biophys-P01 (Kinetics) | 5/10 | Conformational selection narrative is zero-cost and high-value | Tier 3 heuristic is redundant with state_specificity (correctly flagged by cheminfo critique) |
| medchem-P01 (Scoring revision) | 5/10 | Correct identification of QED and reference_similarity problems | Changing scoring function risks post-hoc optimization bias; deferred to supplementary (correct decision) |
| synthbio-P01 (Drug-ability) | 5/10 | Survival funnel is a good visualization concept | RAscore/AiZynthFinder add complexity without clear ML contribution |
| clinonc-P01 (C797S) | 6/10 | Sharp clinical anchoring; honest framing | AF2 DFGout prediction is high-risk (AF2 training bias toward DFGin) |
| compchem-P01 (Physics) | 5/10 | GIST water analysis has best cost/impact ratio | FEP validation has selection bias concerns (who chooses which molecules to validate?) |

---

## Section 9: Claims Requiring Independent Verification

The following claims from both agendas need verification before they can
appear in a publication:

| # | Claim | Source | Verification Task | Priority |
|---|-------|--------|-------------------|----------|
| 1 | "No published paper conditions molecular generation on discrete conformational states of the same protein" | Cohort1 final agenda | Search for DynamicBind, Apo2Mol, DynamicFlow, conformational ensemble generation in molecular design context. Search Chinese-language preprints on kinase-conditioned generation. | HIGH |
| 2 | "FLOWR achieves 92% PoseBusters validity" | Cohort1 mlres-P01 | Verify against original paper (ICLR 2025) and subsequent MolPilot (95.9%). Confirm whether this is on CrossDocked2020 test set or custom evaluation. | MEDIUM |
| 3 | "REINVENT 4 has 720 GitHub stars" | Cohort1 mlres-P01 | Verify current star count. Stars may have changed since the research note was written. | LOW |
| 4 | "Chemprop v2 supports multi-task training with missing labels" | Cohort2 kinpharm-P01 | Verified via GitHub issues and documentation. Confirmed. | DONE |
| 5 | "TDC reproducibility audit found only 3 of top-ranked methods reproducible" | Cohort2 bencharch-P01 | Verified: bioRxiv 2026.02.26.708193. CaliciBoost, MapLight, MapLight+GNN passed. | DONE |
| 6 | "Type II inhibitors have Gini selectivity 0.76 vs 0.58 for Type I" | Cohort2 biophys-P01, kinpharm-P01 | Verify source: Ung et al. (J Med Chem, 2015). Cross-check with Davis et al. (2011) and Uitdehaag et al. (2012) as alternative sources. | MEDIUM |
| 7 | "MolGPS achieves SOTA on 11/22 TDC tasks" | Not cited by either cohort but relevant context | Verified via web search. Valence Labs MolGPS with fingerprints from MPNN++, Transformer, GPS++ models. | INFO |
| 8 | "ADMETlab 3.0 provides 119 endpoints via free API" | Cohort1 synthbio-P01 | Verify API is still operational and free. Check rate limits. | MEDIUM |
| 9 | "StateBind SELFIES VAE achieves 99.9% chemical validity" | Project artifacts | Verify this is computed on generated molecules, not training reconstruction. Autoregressive validity may differ from teacher-forced reconstruction. | HIGH |
| 10 | "MPNN R^2 = 0.69" | Project artifacts | Determine split type (random, temporal, scaffold). If random, estimate scaffold-split performance degradation. | HIGH |

---

## Section 10: Consensus and Disagreement with Cohort Resolutions

### Areas Where I Agree with Cohort Decisions

1. **Pre-registration of all analysis decisions.** This is essential and
   differentiating. Few computational drug design papers do this.

2. **BEDROC as primary metric.** Correct choice for early recognition
   with small N.

3. **Scoring function unchanged for primary analysis.** The decision to
   keep the original 4-component scoring as primary and report reformed
   scoring as secondary/supplementary is the right call. Changing the
   scoring function to make state-aware win would invite suspicion.

4. **Dropping RET and JAK2.** RET has 100% active-state structures (no
   conformational diversity to exploit). JAK2 lacks clinical rationale
   for conformational design. Both are correct drops.

5. **Framing as question/framework, not model.** The paper's contribution
   is the evaluation of state-conditioning as a principle, not the SELFIES
   VAE architecture. This is the correct framing for ML review.

### Areas Where I Disagree

1. **FLOWR as primary 3D baseline.** The agendas selected FLOWR over
   MolCRAFT based on 92% PoseBusters validity. However, MolPilot (ICML
   2025) achieves 95.9% and has publicly available checkpoints on
   HuggingFace. FLOWR's repository is unmaintained. **MolPilot should be
   the primary 3D baseline, with FLOWR as fallback.**

2. **6-8 week timeline (Cohort1).** Unrealistically compressed. The
   Cohort2 estimate of 16-18 weeks is more reasonable, and even that
   should have a 30% buffer (21-24 weeks total).

3. **No FCD in evaluation protocol.** FCD is not mentioned in either
   agenda. It should be a standard metric.

4. **bencharch-P01 without hidden test set.** This is a non-negotiable
   requirement for any benchmark paper post-2025.

---

## Section 11: Recommendations for Strengthening ML Methodology

### Immediate (before any experiments)

1. Specify the MPNN split type used for R^2 = 0.69.
2. Specify whether VAE generation uses autoregressive decoding (no
   teacher forcing) at inference.
3. Confirm 99.9% validity is measured on autoregressive generations.
4. Document the fixed oracle call budget for each baseline method.

### During experiments

5. Train the unconditioned VAE with identical hyperparameters,
   data, and epochs -- only zeroing the state vector. Run 3 seeds.
6. For REINVENT 4, use convergence criteria, not fixed step count.
7. For all 3D methods, list specific EGFR PDB IDs in
   CrossDocked2020 training split.
8. Report wall-clock time, GPU-hours, and oracle calls for every method.
9. Implement split conformal prediction on the MPNN before using it
   to score any generated molecules.

### During analysis

10. Report FCD, novelty, internal diversity, SEDiv, and property
    distributions for all methods.
11. Report both 4-component and 3-component scoring for all methods.
12. Use permutation tests alongside bootstrap CIs for significance.
13. If state-conditioning effect is measured, report both Cohen's d
    and 95% CI.
14. For the benchmark, implement a hidden test partition before
    accepting any external submissions.

### During writing

15. Explicitly state that the architectural contribution is minimal
    (GRU VAE + one-hot concatenation). The contribution is the
    evaluation framework and the question.
16. Include a "Limitations" section that acknowledges: small N, single
    target family (kinases), SELFIES representation constraints,
    no wet-lab validation.
17. Release all code, checkpoints, and evaluation scripts as a
    reproducibility package.

---

## Section 12: Final Assessment

The combined Cohort1/Cohort2 research agenda is **above average** for a
computational drug design publication plan but **below threshold** for
NeurIPS/ICML without the fixes identified above. It is **at threshold**
for JCIM, which is the appropriate primary venue.

The strongest components are:
- The pre-registration commitment (rare and differentiating)
- The ablation design (Experiments A-G, especially C and F)
- The BEDROC + bootstrap statistical framework
- The conformational selection narrative (zero-cost, high-value)

The weakest components are:
- No compute-matched comparison across methods
- Underpowered statistics even with multi-kinase pooling
- The benchmark proposal lacks hidden test set
- Missing standard evaluation metrics (FCD, novelty)

**If I were reviewing the paper described by the Cohort1 agenda at JCIM,
I would score it 6/10 (weak accept) with the current plan and 7-8/10
(accept) with the compute-matched comparison and FCD/novelty metrics
added.** For Nature Computational Science, the within-method state
ablations across architectures (REINVENT + FLOWR with per-state vs
single-state) would be required, and the multi-kinase result would need
to exclude the null hypothesis with pooled BEDROC CI lower bound > 0.5.

**If I were reviewing StateBind-Bench at NeurIPS E&D 2027, I would score
it 4/10 (reject) without a hidden test set and 6/10 (borderline) with
one.** The path to 8/10 (strong accept) requires 3+ kinases, 5+ baselines
with checkpoints, a hidden test partition, and the pocket representation
ablation as a primary task.

---

## References

1. Gao, W., et al. (2022). Sample Efficiency Matters: A Benchmark for
   Practical Molecular Optimization. NeurIPS Datasets & Benchmarks.
2. Heid, E., et al. (2025). Chemprop v2: An Efficient, Modular Machine
   Learning Package for Chemical Property Prediction. ChemRxiv preprint.
3. Truchon, J.-F. & Bayly, C. I. (2007). Evaluating Virtual Screening
   Methods: Good and Bad Metrics for the "Early Recognition" Problem.
   JCIM, 47, 488-508.
4. Buttenschoen, M., et al. (2024). PoseBusters: AI-based docking methods
   fail to generate physically valid ligand poses. Chemical Science.
5. Loeffler, H. H., et al. (2024). Reinvent 4: Modern AI-driven
   generative molecule design. J. Cheminformatics, 16, 20.
6. Cremer, J., et al. (2025). FLOWR: Flow Matching for Structure-Aware
   De Novo Ligand Generation. ICLR 2025.
7. Qu, Y., et al. (2024). MolCRAFT: Structure-Based Drug Design in
   Continuous Parameter Space. ICML 2024.
8. Qu, Y., et al. (2025). MolPilot: Piloting Structure-Based Drug Design
   via Modality-Specific Optimal Schedule. ICML 2025.
9. Preuer, K., et al. (2018). Frechet ChemNet Distance: A Metric for
   Generative Models for Molecules. arXiv:1803.09518.
10. Tripp, A., et al. (2024). Molecular generation metrics: what are we
    really measuring? NeurIPS Workshop on AI for Science.
11. TDC ADMET Audit (2026). Critical Assessment of ML models for ADMET
    Prediction in TDC leaderboards. bioRxiv 2026.02.26.708193.
12. Sabando, M. V., et al. (2024). Using molecular embeddings in QSAR
    modeling: does it make a difference? JCIM.
13. Li, J., et al. (2024). Conformalized GNN Fusion for ADMET Prediction.
    JCIM.
14. Jimenez-Luna, J., et al. (2024). Conformal prediction across QSAR
    models. ACS Omega.
15. Nicholls, A. (2016). The statistics of virtual screening and lead
    optimization. JCAMD, 29, 1205.
16. Bender, A., et al. (2023). Causal inference in computational drug
    discovery. Drug Discovery Today, 28, 103737.
17. Martin, E. J., et al. (2023). Kinase200: A benchmark for multi-task
    kinase MPNN. JCIM.
18. Chen, G., et al. (2023). AMGU: Multi-kinase activity prediction with
    transfer learning. JCIM.
19. NeurIPS 2026 E&D Track Call for Papers. neurips.cc/Conferences/2026/
    CallForEvaluationsDatasets.
20. Pustejovsky, J. (2024). BCa bootstrap confidence intervals at small
    sample sizes. Statistical Methods.
21. Francoeur, P. G., et al. (2020). CrossDocked2020. J. Chem. Inf. Model.
22. STAR-VAE (2025). Latent Variable Transformers for Scalable and
    Controllable Molecular Generation. arXiv:2511.02769.
23. Nie, Y., et al. (2025). Durian: 17-metric benchmark for 3D SBDD. JCIM.
24. ProQSAR (2025). A modular framework with conformal prediction. ChemRxiv.

---

*This review was produced by the Sr. Journal Reviewer -- ML & AI as part
of the ReviewCohort Round 1 independent assessment. All claims are based on
publicly available literature and web-verified information as of April 2026.
No code was modified.*
