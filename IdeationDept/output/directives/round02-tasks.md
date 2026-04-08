---
agent: Orchestrator
round: 2
date: 2026-04-08
type: directive
---

# Round 2 Directives: Proposal Assignments

## Context

Round 1 produced 4,928 lines of research across 7 domains with 198 citations. The
synthesis identified 4 proposal-worthy directions and 2 deeper research needs. Round 2
assigns 5 agents to write formal proposals and 2 to conduct focused follow-up research.

---

## Proposal Assignments

### Proposal 1: Multi-Kinase Retrospective Validation with Pre-Registered Statistical Design

**Assigned to:** datasci (primary), with structbio providing structural feasibility data
**Output:** `output/proposals/datasci-P01.md`

**Why datasci:** This proposal lives or dies on statistical design. datasci identified the
enrichment CI problem, the confounding ablation matrix, and the multi-kinase power
analysis. structbio provides the structural data on which kinases have sufficient
conformational state coverage.

**Scope:** Design a pre-registered multi-kinase validation study. Specify primary endpoint
(BEDROC), kinase targets (ABL, ALK, BRAF, RET + 1-2 more), time-split design, ablation
matrix, success/failure criteria, and multiple testing correction. Include the osimertinib
leakage fix. Estimate compute and timeline.

**Must include from Round 1:**
- datasci's ablation matrix (6 experiments)
- datasci's CI width table by sample size
- datasci's time-split drug assignments (Appendix A)
- structbio's multi-kinase structural data (ABL1 best, then BRAF, Aurora A)
- medchem's selectivity-state connection data

---

### Proposal 2: External Baseline Comparison Framework

**Assigned to:** mlres (primary)
**Output:** `output/proposals/mlres-P01.md`

**Why mlres:** mlres identified the specific baselines needed (REINVENT 4, DiffSBDD/
MolCRAFT), assessed code availability, and understands what reviewers at each venue
will demand. This is about publication strategy as much as technical execution.

**Scope:** Design a comparison framework that evaluates StateBind's state-conditioned
generation against 3-4 external methods on the SAME EGFR task using the SAME evaluation
protocol. Specify: which methods, which metrics, which statistical tests, and what
outcomes would support which conclusions. Include the ablation of state-conditioning
(unconditioned VAE).

**Must include from Round 1:**
- mlres's external baseline assessment (REINVENT 4, DiffSBDD, MolCRAFT)
- genai's flow matching landscape (MolCRAFT, FLOWR as modern alternatives)
- genai's finding that 3D doesn't universally beat 1D
- datasci's ablation matrix (especially Experiment A: unconditioned VAE)
- The tiered strategy from genai: Tier 1 (REINVENT4 + MolCRAFT zero-shot), Tier 2 (multi-method comparison)

---

### Proposal 3: Scoring Function Revision with ADMET and Selectivity Integration

**Assigned to:** medchem (primary)
**Output:** `output/proposals/medchem-P01.md`

**Why medchem:** medchem provided the most detailed critique of the current scoring
function and proposed specific revised weights grounded in MPO practice. The proposal
needs med-chem credibility.

**Scope:** Design a revised scoring function that (a) reduces reference similarity weight,
(b) integrates ADMET with kinase-calibrated thresholds, (c) adds a selectivity proxy
(cross-docking or kinase panel), and (d) addresses the QED problem for kinase inhibitors.
Must report results under BOTH original and revised scoring to avoid bias.

**Must include from Round 1:**
- medchem's weight revision proposal (ref sim 0.10, ADMET 0.20, selectivity 0.15)
- medchem's BSI alternative to Tanimoto (12x improvement)
- synthbio's ADMETlab 3.0 integration (free API, 119 endpoints)
- synthbio's kinase hERG threshold data (osimertinib IC50 0.57-2.21 uM)
- compchem's GIST water analysis as physics-based scoring enhancement
- datasci's warning: must report under BOTH scoring regimes

---

### Proposal 4: End-to-End Drug-ability Assessment Pipeline

**Assigned to:** synthbio (primary)
**Output:** `output/proposals/synthbio-P01.md`

**Why synthbio:** synthbio mapped the complete retrosynthesis + ADMET + PK landscape with
specific tool recommendations, benchmarks, and integration timelines. This is their core
domain.

**Scope:** Design an end-to-end assessment that takes StateBind's top candidates through
retrosynthetic validation, comprehensive ADMET profiling, and PK projection. Demonstrate
that state-aware candidates are not just computationally promising but practically
viable. Compare synthesis feasibility of 1D VAE vs 3D methods.

**Must include from Round 1:**
- synthbio's tool recommendations (RAscore -> AiZynthFinder cascade, ADMETlab 3.0, PKSmart)
- synthbio's finding that 3D-generated molecules have 3-22% true synthesis feasibility
- medchem's ADMET calibration data (hERG thresholds for approved kinase inhibitors)
- The integration timeline (6-week phased approach)

---

### Proposal 5: Physics-Based Validation via Water Thermodynamics and FEP

**Assigned to:** compchem (primary)
**Output:** `output/proposals/compchem-P01.md`

**Why compchem:** compchem provided detailed compute cost estimates for each physics method
and a tiered prioritization. The proposal needs physics rigor and feasibility grounding
on Yale Bouchet HPC.

**Scope:** Design a physics-based validation study with two tiers: (Tier 1) GIST water
thermodynamic analysis of all 4 EGFR states showing states present physically different
binding environments, and (Tier 2) OpenFE RBFE on top candidates providing rigorous
computational validation. Include compute costs, timeline, and expected outcomes.

**Must include from Round 1:**
- compchem's cost estimates (GIST 2 GPU-days, FEP 800-1400 GPU-hours)
- compchem's accuracy hierarchy (GNINA RMSE ~2.5-3.0 vs FEP ~0.7-1.1 kcal/mol)
- structbio's KLIFS ensemble data for multi-structure docking
- compchem's SQM2.20 rescoring as intermediate tier

---

## Additional Research Assignments

### Deep Research: Multi-Kinase Structural Feasibility (structbio)

**Output:** `output/research/structbio-R02.md`

**Assignment:** Conduct a detailed structural feasibility assessment for multi-kinase
validation. For each of ABL, ALK, BRAF, RET, MET, JAK2:
- How many PDB structures exist per conformational state?
- Which structures are best for each state (resolution, WT vs mutant, ligand)?
- Is KLIFS data available for each?
- What are the equivalent pocket definitions?
- Can the 4-state model be applied, or does the kinase require a different state scheme?

This data feeds directly into datasci's multi-kinase proposal.

### Deep Research: Conformation-Conditioned Generation Novelty Survey (genai)

**Output:** `output/research/genai-R02.md`

**Assignment:** Conduct a laser-focused search for ANY prior work that conditions
molecular generation on protein conformational states. Expand beyond the Round 1 search:
- Search patent databases for conformation-conditioned generation claims
- Check bioRxiv/medRxiv for preprints not yet indexed
- Look for industry reports (Insilico, Recursion, Schrödinger) mentioning multi-state generation
- Check NeurIPS/ICML/ICLR 2025-2026 workshop papers
- Document the novelty claim with comprehensive evidence

This is essential for the publication -- we need to be certain no prior work exists.

---

## Prompt Construction Notes for Each Agent

Each proposal agent should receive:
1. Their own Round 1 research note
2. The Round 1 synthesis document (this roundtable)
3. The proposal template from `templates/proposal.md`
4. Their specific assignment above
5. The project briefing (for reference)

The two research agents should receive their Round 1 notes + specific questions above.

---

## Round 2 Timeline

- **Phase A (parallel):** All 5 proposals + 2 research notes launch simultaneously
- **Phase B:** Orchestrator reads all output, writes Round 2 synthesis
- **Phase C:** Assign cross-domain reviews (Round 3)

## Key Decision Points for Round 3

After Round 2 proposals are in, the critical decisions are:
1. Which proposals to merge into a unified research plan?
2. What is the minimal viable set of experiments for a JCIM submission?
3. What additional experiments elevate to Nature Comp Sci?
4. What is the publication timeline?
