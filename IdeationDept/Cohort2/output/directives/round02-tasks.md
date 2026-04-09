---
agent: Orchestrator
round: 2
date: 2026-04-09
type: directive
---

# Round 2 Directives: Formal Proposals

## Overview

Round 1 produced 4,800+ lines of deep research across 7 specialists with 190+
citations. The Round 1 synthesis identified 5 proposal directions based on strong
cross-agent convergence. Round 2 assigns 5 specialists to write formal proposals.

Two agents (drughunt, protml) do NOT write proposals in this round. They will serve
as cross-domain reviewers in Round 3, bringing their competitive landscape / TPP
expertise (drughunt) and protein ML expertise (protml) to bear on the proposals.

---

## Assignments

### P1: Multi-Kinase Retrospective Validation
**Assigned to:** kinpharm (Maverick Kinome Pharmacologist)
**Deliverable:** `Cohort2/output/proposals/kinpharm-P01.md`

Write a formal proposal to extend StateBind's retrospective validation from EGFR
alone to 5 kinases (ABL1, BRAF, ALK, JAK2 + EGFR). Your proposal should:

- Specify data sources and curation protocol for each kinase (ChEMBL, KLIFS, PDB)
- Define the multi-kinase state atlas (structures per state per kinase)
- Propose a multi-task MPNN training strategy
- Estimate statistical power gain (CIs, N of held-out drugs)
- Include a selectivity prediction component using PKIS2/KCGS data
- Define the DFG-out selectivity hypothesis test
- Provide compute and timeline estimates
- Target venue: Nature Computational Science

**Include in your prompt:** Your own R01 research note + Round 1 synthesis.

---

### P2: StateBind-Bench Open Benchmark
**Assigned to:** bencharch (Maverick Benchmark Architect)
**Deliverable:** `Cohort2/output/proposals/bencharch-P01.md`

Write a formal proposal to release StateBind as a community benchmark for
conformational state-conditioned molecular generation. Your proposal should:

- Define 4 benchmark tasks with precise evaluation metrics
- Specify the data package (structures, features, ChEMBL data, time-splits)
- List baseline methods to run (REINVENT 4, DiffSBDD, TargetDiff, Pocket2Mol, etc.)
- Design the leaderboard structure
- Specify infrastructure (HuggingFace, Zenodo, Docker, Croissant metadata)
- Include a multi-kinase extension roadmap (starting EGFR, adding ABL1/BRAF)
- Provide a reproducibility checklist
- Target venue: NeurIPS 2026 E&D Track (deadline May 6, 2026) or JCIM

**Include in your prompt:** Your own R01 research note + Round 1 synthesis.

---

### P3: Scoring Reform and Chemical Space Analysis
**Assigned to:** cheminfo (Senior Cheminformatician)
**Deliverable:** `Cohort2/output/proposals/cheminfo-P01.md`

Write a formal proposal to reform StateBind's scoring function and produce
publication-quality chemical space analysis. Your proposal should:

- Propose expanding the reference set from 3 drugs to ChEMBL EGFR active centroids
- Propose multi-metric similarity (Morgan/Tanimoto, Tversky, PheSA)
- Design the chemical space visualization pipeline (UMAP, property distributions,
  scaffold analysis with SEDiv/#Circles)
- Propose conformal prediction wrapping for MPNN uncertainty quantification
- Estimate the impact on the mean-score gap (quantitative)
- Specify which figures are required for Nature Comp Sci vs JCIM submission
- Include the protml agent's recommendation for Uni-Mol pre-trained embeddings
  as an alternative molecular representation
- Provide compute and timeline estimates

**Include in your prompt:** Your own R01 research note + Round 1 synthesis +
protml's key finding about Uni-Mol (20-59% improvement over from-scratch training).

---

### P4: Resistance-Informed State-Aware Design
**Assigned to:** clinonc (Senior Clinical Oncologist)
**Deliverable:** `Cohort2/output/proposals/clinonc-P01.md`

Write a formal proposal to connect StateBind's conformational state-awareness to
the clinical unmet need of C797S resistance. Your proposal should:

- Define the clinical case for DFGout EGFR inhibitors targeting C797S
- Propose using AlphaFold2/ESMFold to predict C797S mutant structures in each
  conformational state
- Design a computational experiment: generate molecules conditioned on C797S-mutant
  DFGout structures and score against wild-type and mutant targets
- Propose a Target Product Profile screen of generated candidates
- Define CNS penetration criteria (BBB/MPO scoring) as an additional filter
- Frame the narrative for clinical relevance without overclaiming
- Include specific clinical trial data from your R01 research
- Target venue: JCIM or JMC (methods with clinical framing)

**Include in your prompt:** Your own R01 research note + Round 1 synthesis +
protml's finding about AlphaFold for mutant structures and ProstT5 for state
discrimination.

---

### P5: Kinetic Scoring and Conformational Selection Narrative
**Assigned to:** biophys (Senior Biophysicist)
**Deliverable:** `Cohort2/output/proposals/biophys-P01.md`

Write a formal proposal with two components:

**Component A: Kinetic Scoring (5th scoring component)**
- Propose the 3-tier kinetic scoring cascade (tauRAMD > ML koff > state-kinetic
  heuristic) at 10% weight
- Include the complete mathematical formulation
- Propose training data sources (KOFFI, K4DD, BindingDB kinetic data)
- Estimate compute cost for tauRAMD on Bouchet H200 GPUs
- Define the state-kinetic synergy (positive feedback with state_specificity)

**Component B: Conformational Selection Narrative (zero-compute)**
- Articulate the argument: state-aware DFGout design implicitly selects for long
  residence time via conformational selection mechanism
- Support with specific kinetic data (imatinib kon to ABL, lapatinib on EGFR)
- Frame the 10x enrichment as implicit kinetic optimization
- This is the "Discussion" section of the paper

**Component C: Experimental Validation Design**
- Include the 10-compound SPR panel design with cost and timeline
- Include the HDX-MS conformational validation design
- Frame as "future work" or "proposed experimental collaboration"

**Include in your prompt:** Your own R01 research note + Round 1 synthesis.

---

## Round 2 Non-Participants

### drughunt (Senior Drug Hunter)
**Role in Round 3:** Lead reviewer for P1 (multi-kinase) and P4 (resistance design).
Apply your TPP framework, competitive landscape analysis, and translational framing
expertise. Ask: "Would a pharma portfolio committee fund this?"

### protml (Maverick Protein ML Expert)
**Role in Round 3:** Lead reviewer for P3 (scoring reform) and P4 (resistance design).
Apply your pLM and pre-trained representation expertise. Ask: "Would learned
representations improve this further?"

---

## Round 2 Logistics

- All 5 proposals should follow the proposal template (YAML frontmatter, structured
  sections)
- Each proposal must include: Problem Statement, Evidence, Approach, Impact Assessment,
  Effort Estimate, Risk Assessment, Evaluation Criteria
- Proposals will be cross-reviewed in Round 3 by 2-3 agents from different domains
- The orchestrator will synthesize proposals and reviews into a final prioritized agenda
