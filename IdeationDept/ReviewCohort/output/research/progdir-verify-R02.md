---
agent: Program Director / Chief Scientist
round: 2
date: 2026-04-09
type: review-assessment
scope: verification
---

# Program Director Verification Report: Competitive Landscape, Venue Strategy, and Publication Timing

## Executive Summary

After comprehensive competitive landscape research (30+ targeted web searches, analysis
of 7 direct competitors and 4 publication venues), I confirm the core finding from
Round 1: **StateBind's novelty window remains open but is narrowing faster than
previously estimated.** No published paper conditions molecular generation on discrete
conformational state labels (DFG/alphaC classifications) and benchmarks retrospective
enrichment factors. However, PocketXMol (Cell, February 2026), DynamicFlow (ICLR 2025),
and FLOWR.root (October 2025 preprint) represent a rapidly advancing field that will
close the gap between implicit and explicit conformational conditioning within 12-18
months. The optimal strategy is JCIM submission by mid-July 2026, preceded by a
ChemRxiv preprint by late May 2026 to establish priority. NeurIPS 2026 E&D (May 6
deadline) is infeasible. NeurIPS 2027 E&D (~May 2027) remains the benchmark paper
target.

---

## Task 1: Competitive Landscape -- Detailed Analysis

### 1.1 DynamicBind (Lu et al.)

**Status:** Published. Nature Communications 15, Article 1071, February 5, 2024.
Fully peer-reviewed and open access.

**Citations:** ~174 as of April 2026 (Nature Communications article page), making it
one of the most-cited dynamics-aware molecular design papers of 2024. High citation
velocity (~7/month since publication) indicates strong community interest in
dynamics-aware drug design.

**What it does:** Uses equivariant geometric diffusion networks to construct a smooth
energy landscape enabling transitions between protein equilibrium states. Given an
unbound (apo) protein structure and a ligand, DynamicBind predicts the ligand-specific
protein-ligand complex structure. It recovers ligand-specific conformations without
holo-structures or extensive MD sampling.

**Critical differentiation from StateBind:**
- DynamicBind models *ligand-induced* conformational changes implicitly through a
  learned diffusion process. It does NOT use discrete conformational state labels.
- It does NOT condition generation on DFG-in/out or alphaC-in/out classifications.
- It is a *docking/pose prediction* tool, not a *molecular generation* tool in the
  same sense as StateBind's VAE pipeline.
- It does NOT benchmark retrospective enrichment factors.
- **Overlap with StateBind: LOW.** Different question (pose prediction vs. molecular
  generation), different conditioning mechanism (implicit vs. explicit discrete states),
  different evaluation (docking accuracy vs. enrichment factors).

**Scooping risk: LOW.** DynamicBind and StateBind occupy different lanes. DynamicBind
would be cited as related work showing "the field recognizes conformational flexibility
matters," but it does not answer StateBind's specific question about discrete state
conditioning.

**Reference:** Lu, W. et al. DynamicBind: predicting ligand-specific protein-ligand
complex structure with a deep equivariant generative model. *Nat. Commun.* 15, 1071
(2024). https://doi.org/10.1038/s41467-024-45461-2

---

### 1.2 Apo2Mol

**Status:** Published. AAAI 2026 Proceedings, Vol. 40 No. 2, Article 37138. Published
March 14, 2026. Also available on arXiv (2511.14559, November 2025).

**What it does:** A diffusion-based generative framework that simultaneously generates
3D ligand molecules and corresponding holo pocket conformations from input apo protein
structures. Uses a full-atom hierarchical graph-based diffusion model with SE(3)-
equivariant attention layers. Curated dataset of >24,000 experimentally resolved
apo-holo structure pairs from the PDB.

**Critical differentiation from StateBind:**
- Apo2Mol models the apo-to-holo *transition* during generation. It learns what the
  pocket looks like when a ligand binds, starting from the unbound structure.
- It does NOT condition on discrete conformational states. There is no notion of
  DFG-in/out or alphaC-in/out as input labels.
- It is a *3D* molecular generation model (atom coordinates), whereas StateBind uses
  1D (SELFIES strings) conditioned on state labels.
- The paper does NOT benchmark retrospective enrichment factors. Evaluation focuses
  on standard SBDD metrics (binding affinity, molecular properties).
- **Overlap with StateBind: LOW-MEDIUM.** Both address protein flexibility in
  generation, but through fundamentally different mechanisms. Apo2Mol learns
  flexibility implicitly; StateBind provides explicit state labels.

**Scooping risk: LOW.** Apo2Mol is in a different methodological lane (3D diffusion
vs. 1D conditional VAE) and asks a different question (can we generate molecules for
apo pockets?) vs. StateBind's question (does explicit state conditioning improve
enrichment?).

**Reference:** Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion
Models. *Proc. AAAI Conference on Artificial Intelligence* 40(2), Article 37138 (2026).
https://ojs.aaai.org/index.php/AAAI/article/view/37138

---

### 1.3 DynamicFlow

**Status:** Published at ICLR 2025 (poster). arXiv preprint 2503.03989 (March 2025).

**What it does:** A full-atom flow model that transforms apo pockets and noisy ligands
into holo pockets and corresponding 3D ligand molecules. Uses flow matching as the
generative framework with a multiscale model treating proteins as both full-atom (for
interaction) and residue-level frames (for large-scale dynamics). Separate flow matching
objectives for backbone frames, side-chain torsions, and ligand atoms. Trained on 5,692
apo-holo-ligand interaction structures.

**Critical differentiation from StateBind:**
- Models backbone and side-chain dynamics during generation. Does NOT use discrete
  state labels.
- Achieves best Vina scores (-7.65) compared to TargetDiff (-5.09) and Pocket2Mol
  (-5.50) on benchmarks.
- 3D generation approach (atom coordinates in 3D space) vs. StateBind's 1D approach.
- Does NOT benchmark retrospective enrichment.
- **Overlap with StateBind: LOW-MEDIUM.** Different mechanism, different evaluation.
  Both address "protein flexibility matters for generation" but through incompatible
  paradigms.

**Scooping risk: LOW.** No discrete states, no enrichment evaluation, different
architecture entirely.

**Reference:** Integrating Protein Dynamics into Structure-Based Drug Design via
Full-Atom Stochastic Flows. *ICLR 2025*. arXiv:2503.03989.
https://openreview.net/forum?id=9qS3HzSDNv

---

### 1.4 FLOWR and FLOWR.root

**Status:** FLOWR published at ICLR 2025 (arXiv 2504.10564, April 2025). FLOWR.root
is a preprint (arXiv 2510.02578, October 2025), not yet peer-reviewed.

**What FLOWR does:** Flow matching framework for structure-aware de novo, interaction-
and fragment-based ligand generation. Uses continuous/categorical flow matching with
equivariant optimal transport and Semla-style protein pocket encoder. Surpasses
state-of-the-art in PoseBusters validity, pose accuracy, and interaction recovery.
Up to 70x faster inference than diffusion baselines.

**What FLOWR.root adds:** Foundation model extension. Three-stage training: (1) large-
scale pre-training on billions of ligands and millions of complexes, (2) fine-tuning
on curated data, (3) project-specific adaptation via PEFT and importance sampling.
Outperforms Boltz-2 on FEP+/OpenFE benchmark.

**Critical differentiation from StateBind:**
- Pocket-conditioned but NOT state-conditioned. No discrete DFG/alphaC labels.
- 3D generation with flow matching, not 1D SELFIES VAE.
- Does NOT benchmark retrospective enrichment.
- FLOWR.root represents a trend toward foundation models that could subsume
  task-specific approaches like StateBind's VAE.
- **Overlap with StateBind: LOW.** Different architecture, different conditioning,
  different evaluation.

**Practical concern (Round 1 finding confirmed):** FLOWR's original GitHub repo now
directs users to FLOWR.root. FLOWR.root requires significant compute for training and
likely 40GB+ VRAM for the full foundation model. Not practical as a StateBind baseline
on RTX 5000 Ada (16GB VRAM). H200 (80GB) would be required.

**Scooping risk: LOW for the specific StateBind contribution.** HIGH for the broader
field trajectory -- foundation models like FLOWR.root will increasingly make task-
specific VAEs look dated. This is a long-term framing risk, not an immediate novelty
threat.

**References:**
- FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and Fragment-Based
  Ligand Generation. *ICLR 2025*. arXiv:2504.10564.
- FLOWR.root: A flow matching based foundation model for joint multi-purpose structure-
  aware 3D ligand generation and affinity prediction. arXiv:2510.02578 (October 2025).

---

### 1.5 PLACER (Baker Lab)

**Status:** Published. PNAS 122(45), e2427161122. Received January 3, 2025; accepted
September 22, 2025.

**What it does:** A graph neural network that generates conformational ensembles of
protein-small molecule systems using an entirely atomic representation. Trained on
structures from the Cambridge Structural Database and PDB. Used for docking, modeling
nonstandard residues, side chain conformations, and enzyme design. Sampling docks with
PLACER + GALigandDock increases docking success rate by 7.3%.

**Critical differentiation from StateBind:**
- PLACER generates *conformational ensembles* of protein-ligand complexes. It is an
  ensemble prediction tool, not a *molecular generation* tool.
- Does NOT condition on discrete conformational states.
- Does NOT generate novel molecules. Predicts conformations of given molecules/complexes.
- Does NOT benchmark retrospective enrichment.
- **Overlap with StateBind: VERY LOW.** Different problem entirely (ensemble prediction
  vs. state-conditioned generation).

**Scooping risk: VERY LOW.** Different problem domain.

**Reference:** Anishchenko, I. et al. Modeling protein-small molecule conformational
ensembles with PLACER. *PNAS* 122(45), e2427161122 (2025).
https://doi.org/10.1073/pnas.2427161122

---

### 1.6 PocketXMol (NEW -- not in Round 1 analysis)

**Status:** Published. Cell, February 18, 2026. This is a significant new competitor
not fully analyzed in Round 1.

**What it does:** A pocket-interacting molecular generative foundation model that
unifies 13 generative tasks including SBDD, fragment linking/growing, peptide design,
and molecular optimization. Atom-level SE(3)-equivariant architecture. Trained on
11.9M small molecules, 39.9K protein-peptide complexes, and 85.4K protein-small-
molecule complexes. Outperformed 55 baseline models on 11/13 benchmarks. Tested
robustness to apo pocket structures with "minimal shifts" in molecular properties.

**Critical differentiation from StateBind:**
- PocketXMol is pocket-conditioned (uses 3D pocket geometry as input) but does NOT
  condition on discrete conformational state labels.
- It is a *foundation model* approach -- one model for 13 tasks. StateBind is a
  *benchmark question* approach -- does discrete state information improve enrichment?
- PocketXMol does NOT benchmark retrospective enrichment factors.
- **Overlap with StateBind: MEDIUM.** Both concern pocket-aware molecular generation,
  but PocketXMol does not address the discrete state conditioning question.

**Scooping risk: MEDIUM.** PocketXMol demonstrates that pocket-level conditioning
alone achieves strong performance without explicit state labels. A reviewer could ask:
"Why use discrete state labels when PocketXMol achieves SOTA with pocket geometry
alone?" StateBind's answer must be: "We show that discrete state labels improve
*retrospective enrichment* for specific kinase targets, which pocket geometry alone
does not capture."

**Framing implication:** PocketXMol strengthens the case for including a pocket-
conditioned baseline (DiffSBDD or similar) in the StateBind paper. If pocket-
conditioning alone matches state-conditioning on enrichment, the StateBind thesis is
weakened.

**Reference:** Unified modeling of 3D molecular generation via atomic interactions
with PocketXMol. *Cell* (2026). https://doi.org/10.1016/j.cell.2026.01.050

---

### 1.7 Relay Therapeutics

**Status:** Relay continues to publish clinical data (zovegalisib Phase 3 at ESMO TAT
2026, breakthrough therapy designation from FDA in February 2026) but NOT computational
methodology papers. The Dynamo platform remains proprietary. No peer-reviewed papers
describing Dynamo's computational methods were found in 2024-2026 searches.

**Scooping risk: VERY LOW for academic publication.** Relay is in a completely
different lane (clinical-stage drug development, proprietary platform). StateBind as
an open-source academic framework is complementary, not competitive.

**Strategic note:** Relay's clinical success validates the broader thesis that
"conformational awareness matters for drug design." StateBind should cite Relay as
commercial validation of the conformational design paradigm. Relay's proprietary
approach also strengthens the case for open-source alternatives.

---

### 1.8 Other Competitors Searched

**Insilico Medicine (Chemistry42):** Published "From Prompt to Drug" perspective in
ACS Central Science (2025-2026) and presented at NeurIPS 2025. Focus is generative
chemistry with multi-objective optimization, NOT conformational state conditioning.
Phase 2 clinical success with rentosertib (ISM001-055). Different lane entirely.

**Academic groups (Welling, Coley, Bronstein):** Welling and Bronstein published
DiffSBDD (Nature Computational Science, December 2024) and molecular linker design
(Nature Machine Intelligence 2024). Both are equivariant diffusion approaches for
structure-based design but do NOT condition on discrete conformational states. No
evidence of kinase-specific state-conditioning work from these groups as of April 2026.

**OMTRA (December 2025 preprint):** Multi-task generative model for SBDD using 500M
3D conformers. Pocket-conditioned, not state-conditioned.

**MolSnapper (JCIM 2025):** Pharmacophore-conditioned diffusion for SBDD. Different
conditioning mechanism.

**SynGFN (Nature Computational Science, January 2026):** Synthesizability-aware
molecular generation with GFlowNets. Not conformationally aware.

**MolPilot (ICML 2025):** VLB-optimal scheduling for SBDD. 95.9% PoseBusters valid.
Pocket-conditioned, not state-conditioned. Available on HuggingFace (GenSI/MolPilot).
VRAM requirements not explicitly documented but Docker-based setup with NVIDIA GPU
required. Batch size 16 suggests moderate-to-high memory needs.

---

### 1.9 Competitive Landscape Summary Table

| Method | Year | Venue | Discrete States? | Retrospective Enrichment? | Overlap | Scoop Risk |
|--------|------|-------|-------------------|---------------------------|---------|------------|
| DynamicBind | 2024 | Nat Commun | NO (implicit) | NO | LOW | LOW |
| Apo2Mol | 2026 | AAAI | NO (apo-holo) | NO | LOW-MED | LOW |
| DynamicFlow | 2025 | ICLR | NO (flow-based) | NO | LOW-MED | LOW |
| FLOWR/FLOWR.root | 2025 | ICLR/arXiv | NO (pocket) | NO | LOW | LOW |
| PLACER | 2025 | PNAS | NO (ensemble) | NO | V.LOW | V.LOW |
| PocketXMol | 2026 | Cell | NO (pocket) | NO | MED | MED |
| Relay (Dynamo) | ongoing | proprietary | unclear | NO | V.LOW | V.LOW |
| REINVENT 4 | 2024 | J Cheminf | NO | NO | BASELINE | N/A |
| Insilico (Chem42) | ongoing | various | NO | NO | V.LOW | V.LOW |

**Critical conclusion: No paper found that combines discrete conformational state
conditioning with retrospective enrichment evaluation.** StateBind's novelty is
intact as of April 9, 2026.

---

### 1.10 BMCS Conformational Design Symposium

The RSC-BMCS 3rd Conformational Design in Drug Discovery symposium was held March 2,
2026 at GSK Conference Centre, Stevenage, UK. Confirmed speakers included GSK, Leiden
UMCR, and NRG Therapeutics researchers. Topics included PROTAC conformational analysis,
free-energy perturbation, and ML-based rational drug design. Abstract submission is
now closed.

**Strategic implication:** The 3rd edition of this symposium confirms growing community
interest in conformational drug design. StateBind should cite this symposium as evidence
of field maturity and timeliness. The fact that a pharmaceutical symposium exists on
this topic validates the relevance of StateBind's benchmark question.

---

## Task 2: Venue Analysis

### 2.1 JCIM (Journal of Chemical Information and Modeling) -- PRIMARY TARGET

**Submission:** Rolling (no deadline). Submit any time.

**Impact Factor:** 5.3 (2025 JCR, released June 2025). Decreased ~10% from 2024.
Still strong for the cheminformatics/computational drug design niche.

**Review Timeline:** First review round approximately 6 weeks based on community-
reported data. Example verified: a paper received December 12, 2025 was accepted
March 4, 2026 (approximately 12 weeks total including revisions). This translates to:
- Submission to first decision: ~6 weeks
- Revision period: ~3-4 weeks
- Revised submission to acceptance: ~2-3 weeks
- Total: ~12-16 weeks submission to acceptance

**Acceptance Rate:** Not publicly reported by ACS. Community estimates suggest 30-40%
for initial submissions. Higher for well-known groups and timely topics.

**Special Issues:** No specific call found for kinase drug design or conformational
analysis in 2026. However, JCIM regularly publishes kinase-related computational
papers -- at least 6 kinase-focused papers published in 2026 issues already (kinCSM-
RTK, SIK inhibitor modeling, etc.).

**Fit for StateBind:** EXCELLENT. StateBind's benchmark question ("does discrete state
conditioning improve molecular generation?") is squarely in JCIM's scope. The
retrospective enrichment methodology is novel for this venue. The multi-kinase
expansion strengthens the contribution.

**Publication fee:** ACS open access (ASAP articles typically $3,500-5,000). Not a
constraint for this project.

**Recommendation: SUBMIT HERE. Rolling submission means no deadline pressure; the
only pressure is competitive timing.**

---

### 2.2 Nature Computational Science -- ASPIRATIONAL STRETCH

**Impact Factor:** 18.3 (2025 JCR). Q1 ranking. Launched in 2021 and rising rapidly.

**Submission:** Rolling. No deadlines. Invitation-encouraged but not required.

**Desk Rejection Rate:** Estimated 60-70% for Nature-family journals broadly. Nature
Computational Science is newer and slightly more accessible, but still highly selective.
Expect 50-60% desk rejection rate for unsolicited submissions.

**Review Timeline:** 3-4 weeks for reviewers to submit reviews (Nature standard).
Total process from submission to acceptance typically 4-8 months including revisions.

**Recent molecular design publications (2025-2026):**
- DiffSBDD (Schneuing et al., December 2024) -- equivariant diffusion for SBDD
- SynGFN (January 2026) -- synthesizability-aware GFlowNet generation
- Pharmacophore-oriented 3D molecular generation (August 2025)
- Several editorials on "generative molecular design on the rise" (2025)

**Bar for StateBind:** Nature Comp Sci publishes *novel methods* or *significant
biological insights*. StateBind is fundamentally a *benchmark question* paper, not a
novel architecture. The 10x retrospective enrichment is striking, but on 3-5 held-out
drugs for one kinase. For Nature Comp Sci:
- Multi-kinase validation across 3-4 kinases would be minimum
- Within-method state ablation succeeding across architectures (VAE + REINVENT)
  would be necessary
- The framing would need to be "conformational state labels are a general organizing
  principle for computational drug design," not just "here is a pipeline comparison"

**Recommendation: DO NOT submit directly to Nature Comp Sci as the primary target.**
The desk rejection risk is too high and the turnaround cost (2-3 months lost) is
unacceptable given competitive timing. Instead:
1. Submit to JCIM first
2. If within-method ablations succeed across kinases AND architectures, consider
   upgrading an expanded version to Nature Comp Sci after JCIM acceptance
3. Alternatively, the benchmark paper (NeurIPS 2027 E&D) could be expanded for
   Nature Comp Sci if it covers 5+ kinases

---

### 2.3 NeurIPS 2026 Evaluations & Datasets Track

**Key dates (VERIFIED from official NeurIPS 2026 website):**
- Portal opens: April 15, 2026 (6 days from now)
- Abstract submission: May 4, 2026 (25 days from now)
- Full paper + supplementary: May 6, 2026 (27 days from now)
- Author notification: September 24, 2026
- Conference: December 6-12, 2026

**Track scope (VERIFIED):** Renamed from "Datasets & Benchmarks" to "Evaluations &
Datasets." Expanded scope explicitly positions evaluation as a scientific object of
study. Welcomes benchmark analysis, new datasets, evaluation protocols, negative
results, and data-centric AI.

**Requirements:** Datasets and code must be properly hosted, accessible, and
documented *upon submission*. Croissant metadata format required. Code required for
benchmarks. Double-blind default; dataset-focused may request single-blind.

**Feasibility for StateBind benchmark paper: COMPLETELY INFEASIBLE.** 27 days is
insufficient to:
1. Complete multi-kinase codebase refactoring (4-6 weeks)
2. Curate ABL1/BRAF/MET datasets
3. Train per-kinase models
4. Run benchmark experiments
5. Build Docker containers and HuggingFace hosting
6. Write the benchmark paper
7. Prepare Croissant metadata

**Recommendation: DO NOT TARGET NeurIPS 2026 E&D.** This was already the consensus
from Round 1 and is now confirmed with verified deadlines.

---

### 2.4 NeurIPS 2027 Evaluations & Datasets Track

**Dates:** Not yet announced. Based on NeurIPS patterns:
- NeurIPS 2025: D&B deadline May 15, 2025
- NeurIPS 2026: E&D deadline May 6, 2026
- **NeurIPS 2027: Expected deadline ~May 2027** (extrapolated)

**Timeline:** This gives ~13 months from today (April 2026) to prepare the benchmark
paper. After Paper 1 (JCIM) is submitted by July 2026, there are ~10 months to:
1. Expand to 5+ kinases
2. Build benchmark infrastructure (Docker, leaderboard, HuggingFace dataset)
3. Run baseline methods (REINVENT, DiffSBDD, MolPilot)
4. Prepare Croissant metadata
5. Write the benchmark paper

**Recommendation: TARGET NeurIPS 2027 E&D for the benchmark paper.** This is realistic
and allows building on Paper 1 results. The 10-month window after JCIM submission is
sufficient with focused execution.

---

### 2.5 ICML 2026

**Key dates (VERIFIED):**
- Abstract deadline: January 24, 2026 (ALREADY PASSED)
- Full paper deadline: January 29, 2026 (ALREADY PASSED)
- Conference: July 6-11, 2026, Coex Convention Center

**Relevance:** ICML 2026 has already closed. Not an option. ICML 2027 deadlines would
be approximately January 2027. The StateBind paper is not ML-method-novel enough for
ICML main track (the VAE is standard architecture). A workshop paper at ICML 2026
could theoretically be submitted if a relevant workshop (e.g., AI for Science) has a
later deadline.

---

### 2.6 ICLR 2026

**Status:** ICLR 2026 has already occurred (accepted papers listed, >5,300 papers).
Includes molecular design papers (FragFM, etc.) but no state-conditioned generation
papers.

**ICLR 2027:** Submission deadline expected September-October 2026 (based on ICLR 2026
pattern). This is a possible alternative venue for the benchmark paper if the ML
contribution is sufficiently novel. However, NeurIPS E&D is a better fit for a
benchmark.

---

### 2.7 Other Venues Considered

**Briefings in Bioinformatics:** IF ~13 (2025). Published several molecular generation
papers in 2026 including diffusion-based and fragment-based methods. Rolling submission.
A credible alternative to JCIM but lower prestige in the cheminformatics community.
Good option if JCIM rejects.

**Drug Discovery Today:** Commentary/perspective venue, not primary research. Could be
useful for a "conformational design perspective" piece after the main paper.

**ACS Omega, ACS Chemical Biology:** Lower tier. Backup only.

**Workshop papers (NeurIPS/ICML 2026):** The 7th AI for Science workshop is scheduled
for ICML 2026 (July 6-11, 2026). Workshop paper deadlines are typically 2-3 months
before the conference (April-May 2026). A 4-page workshop paper could establish
priority quickly. **Investigate submission deadlines for AI for Science @ ICML 2026.**

**Computational Biology and Bioinformatics conference (August 24-25, 2026, Singapore):**
An industry/academic event. Could be a presentation venue but not a priority publication
target.

---

### 2.8 Venue Strategy Summary

| Venue | Type | Deadline | Feasible? | Priority |
|-------|------|----------|-----------|----------|
| JCIM | Journal (rolling) | None | YES | PRIMARY |
| ChemRxiv preprint | Preprint | Self-imposed May 2026 | YES | PRIORITY CLAIM |
| Nature Comp Sci | Journal (rolling) | None | RISKY | STRETCH (post-JCIM) |
| NeurIPS 2026 E&D | Conference | May 6, 2026 | NO | SKIP |
| NeurIPS 2027 E&D | Conference | ~May 2027 | YES | BENCHMARK PAPER |
| ICML 2026 AI4Sci WS | Workshop | ~Apr-May 2026 | MAYBE | INVESTIGATE |
| Briefings in Bioinfo | Journal (rolling) | None | YES | BACKUP |

---

## Task 3: Publication Timing Strategy

### 3.1 Scooping Risk Assessment

**Probability of someone publishing discrete-state-conditioned generation within 6
months (by October 2026): LOW (15-20%)**

Reasoning:
- No preprint or paper found that conditions on discrete conformational states
- The field is moving toward implicit dynamics (DynamicBind, DynamicFlow, Apo2Mol)
  and foundation models (PocketXMol, FLOWR.root), not toward explicit discrete labels
- The groups most likely to produce such work (Welling/Bronstein, Baker Lab, Insilico)
  are pursuing different paradigms
- A kinase-specific conformational benchmark paper requires significant kinase biology
  expertise in addition to ML expertise, narrowing the pool of potential competitors

**Probability within 12 months (by April 2027): MODERATE (30-40%)**

Reasoning:
- Growing community interest (BMCS 3rd Conformational Design symposium, March 2026)
- KLIFS database (providing DFG/alphaC classifications) is increasingly used
- The question "do discrete state labels help?" is an obvious experiment once you have
  KLIFS data and any conditional generative model
- Groups combining structural biology and ML (e.g., Baker Lab, Schueler-Furman group,
  Volkamer group at Charite Berlin) could independently arrive at this question

**Which group is closest?**
The Volkamer group (Charite Berlin) published "A comprehensive exploration of the
druggable conformational space of protein kinases using AI-predicted structures"
(PLoS Computational Biology, 2024) using KLIFS classifications. They have the kinase
structural biology expertise AND ML capability to ask StateBind's question. However,
their work focuses on structure prediction, not molecular generation. Still, they are
the group I would watch most closely.

**Where is the novelty?**
The novelty is in the EVALUATION METHODOLOGY (retrospective enrichment benchmark for
state-conditioned generation), not just the generation approach (state-conditioned
VAE). The VAE architecture is standard; the question and the evaluation are novel.
This is important because it means a competitor would need to independently develop:
(a) the retrospective time-split evaluation framework, (b) per-kinase state-specific
data curation, and (c) the ablation suite proving state conditioning matters. This
is a significant research program, not a weekend experiment.

---

### 3.2 Timeline Scenarios

#### Scenario A: Minimum Viable Paper -- 12 weeks (target: July 1, 2026)

**Scope:**
- Pre-publication fixes (osimertinib leak, bootstrap CIs, structure verification): 1-2 weeks
- Ablation C (unconditioned VAE) on EGFR only: 1-2 weeks
- REINVENT 4 baseline on EGFR only: 2-3 weeks
- Multi-kinase: EGFR + ABL1 only (best-characterized DFGout): 3-4 weeks
- Paper writing: 2-3 weeks (parallel with late experiments)
- Scoring sensitivity analysis (Dirichlet 1,000+): 1 week

**What is sacrificed:**
- BRAF and MET (only 2 kinases instead of 4)
- 3D baseline (MolPilot/DiffSBDD)
- Conformal prediction
- GIST water analysis
- Within-method state ablation on REINVENT
- Chemical space UMAP (can be added in revision)

**Scooping risk for Scenario A: LOW (15-20%).** The compressed timeline minimizes
exposure to competitors.

**Publication quality: ADEQUATE for JCIM but not compelling.** Two kinases is the
minimum for "multi-target validation." ABL1 has the strongest DFGout data and would
provide the cleanest second result. However, reviewers may request a third kinase
during revision, extending the total publication timeline by 2-3 months.

**My assessment: This scenario is too aggressive.** The 12-week estimate assumes no
refactoring delays, no failed experiments, and no unexpected tool incompatibilities.
The principal and associate identified 4-6 weeks for multi-kinase codebase refactoring
alone. Even with an incremental approach (adding kinase-specific code alongside EGFR
code), this adds 2-3 weeks minimum.

---

#### Scenario B: Full Paper -- 16 weeks (target: August 1, 2026)

**Scope:**
- Pre-publication fixes: 1-2 weeks
- Multi-kinase codebase extension (incremental, not full refactor): 3-4 weeks
- Ablation suite (C, E, F, G) on EGFR + ablation C on ABL1/BRAF: 2-3 weeks
- REINVENT 4 baseline on EGFR + ABL1: 2-3 weeks
- ABL1 + BRAF full pipeline: 3-4 weeks (overlapping with codebase work)
- MET: attempt but not required (contingent on data quality)
- Scoring sensitivity + conformal prediction: 1-2 weeks
- Chemical space UMAP + property distributions: 1 week
- Paper writing: 3-4 weeks (parallel with final experiments)
- ChemRxiv preprint: ~late May (with EGFR results + preliminary ABL1)

**What is sacrificed:**
- 3D baseline (deferred to revision or Paper 2)
- GIST water analysis
- MET (contingent)
- Full within-method state ablation on REINVENT (REINVENT runs only on EGFR)

**Scooping risk for Scenario B: LOW-MODERATE (20-25%).** 16 weeks is 4 months. With
a ChemRxiv preprint at week 6-8, priority is established by June 2026.

**Publication quality: STRONG for JCIM.** Three kinases (EGFR + ABL1 + BRAF) with
ablation suite, external baseline, scoring sensitivity, and conformal prediction is
a complete paper. Reviewers may suggest but not require a 3D baseline.

**My assessment: This is the recommended scenario.** It balances completeness,
quality, and competitive timing. The ChemRxiv preprint at week 6-8 establishes
priority while allowing the full paper to be polished.

---

#### Scenario C: Comprehensive Paper -- 24 weeks (target: October 1, 2026)

**Scope:**
- Everything in Scenario B, plus:
- MET as fourth kinase
- 3D baseline (DiffSBDD on EGFR)
- Within-method state ablation on REINVENT
- GIST water analysis
- Full FCD + SEDiv + novelty metrics suite
- Survival funnel (ADMETlab + AiZynthFinder)

**Scooping risk for Scenario C: MODERATE (30-35%).** 24 weeks is 6 months. Even with
a preprint, a competitor preprint could appear by October 2026.

**Publication quality: EXCELLENT for JCIM, possibly sufficient for Nature Comp Sci
stretch.** Four kinases, multiple baselines (REINVENT + DiffSBDD), comprehensive
ablations, and advanced analysis would make a very strong paper.

**My assessment: TOO SLOW unless the ChemRxiv preprint strategy mitigates scooping
risk.** The additional 8 weeks over Scenario B add quality but increase risk
disproportionately. The 3D baseline and within-method ablation are "nice to have"
for JCIM, not "must have."

---

### 3.3 Preprint Strategy

**Should the project preprint on ChemRxiv?**

**YES. Strongly recommended.**

Rationale:
1. **Priority establishment.** A ChemRxiv preprint with EGFR results and preliminary
   ABL1 results establishes the claim "we asked this question first and have initial
   results" before the full paper is ready.
2. **Community feedback.** A preprint invites comments that can strengthen the final
   paper.
3. **No journal conflict.** JCIM (ACS) accepts preprinted manuscripts. ACS policy
   explicitly permits preprints on recognized servers including ChemRxiv and bioRxiv.
4. **Competitor deterrence.** A visible preprint signals that this space is being
   actively worked on, potentially discouraging competitors from pursuing the same
   question.

**When?**

Target: **Late May 2026 (week 6-8 of Scenario B).**

**Minimum content for a credible preprint:**
1. EGFR retrospective enrichment with bootstrap CIs (existing result + fix)
2. Ablation C result (unconditioned vs. conditioned VAE) on EGFR
3. Preliminary ABL1 enrichment (even if on a smaller dataset)
4. Scoring sensitivity analysis
5. Clear statement of the multi-kinase expansion in progress

This is not the final paper -- it is a priority-establishing preprint that
demonstrates the question, the methodology, and the initial results. The full
paper with 3 kinases, REINVENT baseline, and complete ablations follows at JCIM
submission in August.

**ChemRxiv vs. bioRxiv?**

ChemRxiv preferred. StateBind is primarily a cheminformatics/computational chemistry
contribution. ChemRxiv reaches the target audience (JCIM reviewers, drug design
community). bioRxiv is acceptable but less targeted.

---

### 3.4 Workshop Paper Option

**Should StateBind submit a workshop paper?**

**INVESTIGATE but likely YES for the 7th AI for Science Workshop at ICML 2026
(July 6-11, 2026, Hamburg).**

Rationale:
- Workshop papers are 4-6 pages and do not preclude journal submission
- A workshop paper at ICML would give a live presentation opportunity
- The deadline is likely April-May 2026 -- feasible with EGFR results only
- The audience (AI for Science community) is exactly the target readership

**Action item:** Check the AI for Science workshop deadline immediately. If it is
before May 15, 2026, submit a 4-page extended abstract with EGFR results.

---

### 3.5 Updated Strategic Recommendation

#### Publication Sequence

1. **ChemRxiv preprint: Late May 2026** (week 6-8)
   - EGFR results with bootstrap CIs + Ablation C + preliminary ABL1
   - Establishes priority

2. **ICML 2026 AI4Sci workshop paper: ~May 2026** (if deadline permits)
   - 4-page extended abstract with EGFR results
   - Live presentation in Hamburg, July 2026
   - Does not preclude JCIM submission

3. **JCIM full paper submission: Early August 2026** (week 16)
   - EGFR + ABL1 + BRAF, full ablation suite, REINVENT baseline
   - Scoring sensitivity, conformal prediction, chemical space analysis
   - Expected first decision: ~October 2026
   - Expected acceptance: ~December 2026 - January 2027
   - Expected publication: Q1 2027

4. **NeurIPS 2027 E&D benchmark paper: ~May 2027** (month 13)
   - Expand to 5+ kinases
   - Docker containers, HuggingFace dataset, Croissant metadata
   - Run additional baselines (MolPilot, DiffSBDD, REINVENT, GraphAF)
   - Leaderboard infrastructure

5. **Nature Comp Sci stretch: ~Q3 2027** (optional)
   - Only if within-method ablations succeed across kinases AND architectures
   - Expanded version with 4+ kinases, multiple generative models, biological insight

#### Critical Timeline

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 0 (Apr 9) | START | Pre-registration document committed to git |
| 1-2 | Pre-publication fixes | Osimertinib leak fixed, bootstrap CIs, structure verification |
| 2-4 | Multi-kinase extension | ABL1 data curated, codebase extended (incremental approach) |
| 3-5 | Ablation C | Unconditioned VAE trained and evaluated on EGFR |
| 4-6 | REINVENT 4 setup | REINVENT installed, GNINA scoring bridge built |
| 5-7 | ABL1 pipeline | ABL1 models trained, pipeline executed, enrichment computed |
| 6-8 | ChemRxiv preprint | Priority-establishing preprint posted |
| 7-10 | BRAF pipeline | BRAF data curated, models trained, pipeline executed |
| 8-12 | REINVENT baseline | REINVENT run on EGFR (and ABL1 if time permits) |
| 10-14 | Analysis suite | Scoring sensitivity, conformal prediction, UMAP, FCD |
| 12-16 | Paper writing | Full manuscript drafted, revised, finalized |
| 16 | JCIM submission | Full paper submitted |

#### Go/No-Go Gates

**Gate 1 (Week 5): Ablation C result on EGFR**
- GO if unconditioned VAE has lower enrichment than conditioned (Cohen's d >= 0.5)
- PIVOT if no difference: reframe as "diverse generation > template-based" paper
- KILL if unconditioned VAE has HIGHER enrichment: fundamental thesis failure

**Gate 2 (Week 7): ABL1 enrichment result**
- GO if state-aware enrichment >= 2x static on ABL1
- CAUTIOUS if 1-2x: continue but frame as "kinase-dependent effect"
- CONCERN if < 1x: EGFR-only paper with ABL1 as negative control

**Gate 3 (Week 10): BRAF enrichment result**
- GO if 2/3 kinases show state-aware advantage
- ACCEPTABLE if 1/3: report honestly with analysis of why
- REFRAME if 0/3: the paper becomes "when does state conditioning help?"

**Gate 4 (Week 12): REINVENT baseline on EGFR**
- GO if StateBind outperforms REINVENT on enrichment
- ACCEPTABLE if comparable: frame as "explicit state labels achieve comparable
  results with simpler architecture"
- CONCERN if REINVENT wins: requires careful framing

---

### 3.6 Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Competitor preprint appears | 20-25% (16 wk) | HIGH | ChemRxiv preprint at week 6-8 |
| Ablation C shows no effect | 30% | CRITICAL | Pre-registered pivot narrative |
| Multi-kinase refactoring takes >6 weeks | 40% | HIGH | Incremental approach (no full refactor) |
| REINVENT 4 integration fails | 20% | MEDIUM | Fallback: skip REINVENT, use ablation suite only |
| ABL1 lacks sufficient DFGout structures | 15% | MEDIUM | ABL1 has best DFGout data; low risk |
| GNINA docking compute exceeds budget | 30% | MEDIUM | Prioritize EGFR + ABL1; BRAF on MPNN proxy |
| JCIM reviewers request 4th kinase | 50% | LOW | MET data curation as contingency |
| Nature Comp Sci desk rejects | 60% | LOW (if JCIM-first) | JCIM is primary; Nat Comp Sci is stretch only |

---

## Revised Strategic Recommendation

### What Changed from Round 1

1. **PocketXMol (Cell, Feb 2026)** is a new competitor not fully analyzed in Round 1.
   It strengthens the need for a pocket-conditioned baseline in the paper, but does
   not threaten StateBind's discrete state conditioning novelty.

2. **DynamicBind citations (~174)** confirm high community interest in dynamics-aware
   drug design, supporting StateBind's timeliness claim.

3. **NeurIPS 2026 E&D deadline (May 6, 2026)** is now confirmed as 27 days away --
   completely infeasible. This was the consensus from Round 1 and is now verified.

4. **JCIM review timeline (~12-16 weeks)** is verified. A July submission would yield
   first decision by October 2026.

5. **Preprint strategy** is now a firm recommendation, not just a consideration.
   ChemRxiv at week 6-8 is the priority-establishing move.

6. **Timeline revised from 12 to 16 weeks** based on Round 1 codebase analysis.
   Scenario B (16 weeks to JCIM submission) is the recommended path. Scenario A
   (12 weeks) is too aggressive given the multi-kinase refactoring reality.

### What Stays the Same

1. One-paper JCIM-first strategy (confirmed)
2. Multi-kinase panel: EGFR + ABL1 + BRAF (+ MET contingent)
3. REINVENT 4 as essential external baseline
4. Pre-publication fixes as immediate priority
5. Ablation C as thesis-critical gate
6. NeurIPS 2027 E&D as benchmark paper target
7. Novelty claim: "first systematic benchmark evaluating discrete conformational
   state-conditioning in molecular generation" (verified as unique)

### Bottom Line

**Submit a ChemRxiv preprint by late May 2026. Submit the full paper to JCIM by
early August 2026. Target NeurIPS 2027 E&D for the benchmark paper. The novelty
window is open but will not stay open indefinitely. Execute Scenario B (16 weeks)
with the go/no-go gates defined above.**

---

## References

1. Lu, W. et al. DynamicBind: predicting ligand-specific protein-ligand complex
   structure with a deep equivariant generative model. *Nat. Commun.* 15, 1071 (2024).
   https://doi.org/10.1038/s41467-024-45461-2

2. Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion Models.
   *Proc. AAAI* 40(2), Article 37138 (2026).
   https://ojs.aaai.org/index.php/AAAI/article/view/37138

3. Integrating Protein Dynamics into Structure-Based Drug Design via Full-Atom
   Stochastic Flows [DynamicFlow]. *ICLR 2025*. arXiv:2503.03989.

4. FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and Fragment-Based
   Ligand Generation. *ICLR 2025*. arXiv:2504.10564.

5. FLOWR.root: A flow matching based foundation model for joint multi-purpose
   structure-aware 3D ligand generation and affinity prediction. arXiv:2510.02578
   (October 2025).

6. Anishchenko, I. et al. Modeling protein-small molecule conformational ensembles
   with PLACER. *PNAS* 122(45), e2427161122 (2025).
   https://doi.org/10.1073/pnas.2427161122

7. Unified modeling of 3D molecular generation via atomic interactions with PocketXMol.
   *Cell* (February 2026). https://doi.org/10.1016/j.cell.2026.01.050

8. Loeffler, H. H. et al. Reinvent 4: Modern AI-driven generative molecule design.
   *J. Cheminformatics* 16, 20 (2024). https://doi.org/10.1186/s13321-024-00812-5

9. Schneuing, A. et al. Structure-based drug design with equivariant diffusion models
   [DiffSBDD]. *Nat. Comput. Sci.* (December 2024).
   https://doi.org/10.1038/s43588-024-00737-x

10. Piloting Structure-Based Drug Design via Modality-Specific Optimal Schedule
    [MolPilot]. *ICML 2025*. arXiv:2505.07286.

11. Insilico Medicine. From Prompt to Drug: Toward Pharmaceutical Superintelligence.
    *ACS Central Science* (2025-2026).

12. Chemistry42: An AI-Driven Platform for Molecular Design and Optimization. *JCIM*
    (2023). https://doi.org/10.1021/acs.jcim.2c01191

13. Broomhead, N. K. & Soliman, M. E. Exploring Kinase DFG Loop Conformational
    Stability with AlphaFold2-RAVE. *JCIM* (2024).
    https://doi.org/10.1021/acs.jcim.3c01436

14. Volkamer, A. et al. A comprehensive exploration of the druggable conformational
    space of protein kinases using AI-predicted structures. *PLoS Comput. Biol.* (2024).
    https://doi.org/10.1371/journal.pcbi.1012302

15. NeurIPS 2026 Evaluations & Datasets Track Call for Papers.
    https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets

16. JCIM Author Guidelines. ACS Publications.
    https://pubs.acs.org/page/jcisd8/submission/authors.html

17. Nature Computational Science Journal Metrics.
    https://www.nature.com/natcomputsci/journal-impact

18. BMCS 3rd Conformational Design in Drug Discovery 2026.
    https://www.rscbmcs.org/events/conformationaldesign26/

19. Relay Therapeutics Dynamo Platform.
    https://relaytx.com/dynamo-platform/

20. Gao, W. et al. Sample Efficiency Matters: A Benchmark for Practical Molecular
    Optimization [PMO]. *NeurIPS 2022*.

21. FragFM: Hierarchical Framework for Efficient Molecule Generation via Fragment-Level
    Discrete Flow Matching. *ICLR 2026*.

22. SynGFN: learning across chemical space with generative flow-based molecular
    discovery. *Nat. Comput. Sci.* (January 2026).

23. Pharmacophore-oriented 3D molecular generation toward efficient feature-customized
    drug discovery. *Nat. Comput. Sci.* (August 2025).

24. A large language model-guided reinforcement learning framework for EGFR anticancer
    drug design. *J. Comput.-Aided Mol. Des.* (January 2026).
    https://doi.org/10.1007/s10822-025-00753-7
