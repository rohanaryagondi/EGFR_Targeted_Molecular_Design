---
agent: Maverick Synth-Bio / DMPK Specialist
round: 2
date: 2026-04-08
type: proposal
proposal_id: synthbio-P01
title: "End-to-End Drug-ability Assessment Pipeline: From Scored Molecules to Synthesizable, ADMET-Profiled, PK-Projected Candidates"
---

# Proposal: End-to-End Drug-ability Assessment Pipeline

## Proposing Agent
**Dr. Maverick Synth-Bio / DMPK Specialist** -- Expertise in retrosynthetic planning,
DMPK, ADMET profiling, PK/PD modeling, and translational drug design.

## Problem Statement

StateBind demonstrates a compelling 10x retrospective enrichment for conformational
state-aware molecular design over static single-structure design. But the pipeline
stops at scoring. It never asks three questions that every medicinal chemist, every
DMPK scientist, and every reviewer at JCIM or Nature Computational Science will ask:

1. **Can these molecules be synthesized?** StateBind uses SA score (a heuristic proxy)
   contributing 7.5% of the total score. SA score "fails to differentiate between
   feasible and infeasible routes" -- average SA scores were 2.68 vs 2.73 for molecules
   with vs without feasible routes (Gao et al., 2024). No actual retrosynthetic
   analysis has been performed on any candidate.

2. **Will they survive the ADMET gauntlet?** The ADMET model (hERG AUROC=0.7745,
   CYP3A4 AUROC=0.7323) is informational only. When hard filtering was attempted, it
   rejected ALL kinase inhibitors on hERG -- a class liability, not a model failure.
   But without kinase-calibrated thresholds, ADMET provides zero discriminative value
   in candidate prioritization.

3. **What dose would a patient need?** No PK projections exist. No oral bioavailability
   estimates. No half-life predictions. The top-ranked molecule could require 2g daily
   dosing or have a 2-hour half-life, and StateBind would not know.

This is not a theoretical concern. Most AI drug design papers stop at generation +
scoring. The field has moved on: Chemistry42 (Insilico Medicine), ADMETrix (2026),
PMMG (Advanced Science, 2025), and REINVENT 4 (AstraZeneca, 2024) all integrate
ADMET and/or retrosynthesis into the optimization loop. StateBind's post-hoc-only
approach is increasingly out of step with the state of the art.

More critically, a devastating 2024 evaluation found that 3D structure-based
generative models produce molecules with only 3-22% true synthesis feasibility via
round-trip verification (Gao et al., arXiv:2411.08306). If StateBind's 1D SELFIES
VAE produces candidates with significantly higher synthesis feasibility, that is a
strong and novel publication point that no other conformational-state-aware pipeline
has demonstrated.

## Vision

A StateBind publication that presents not just "scored molecules" but **fully profiled
drug candidates** -- each with a synthesis route, comprehensive ADMET profile, and PK
projection. The end state is a single publication figure showing the "survival funnel":
461 candidates enter, and the reader can see exactly how many survive each filter
(scoring, ADMET, retrosynthesis, PK), with the final survivors presented as
translatable starting points for medicinal chemistry optimization.

This transforms the paper from a computational proof-of-concept into a practical
demonstration of AI-driven drug design with translational awareness.

---

## Background and Evidence

### Key Evidence

1. **AiZynthFinder 4.4.1** (Thakkar et al., 2024; MIT License) solves retrosynthetic
   routes for 71% of ChEMBL drug-like molecules and 80-86% of AI-designed compounds,
   with median search times of 40-90 seconds per molecule. Version 4.4.1 supports
   Python 3.10-3.12, multiple search algorithms beyond MCTS, ONNX conversion for 1.7x
   faster search, and any one-step retrosynthesis model. pip-installable.

2. **RAscore** (Thakkar et al., 2021) classifies retrosynthetic feasibility at least
   4500x faster than AiZynthFinder, with AUC and accuracy both above 0.81. Trained on
   200,000 AiZynthFinder results from ChEMBL. Milliseconds per molecule -- suitable
   for screening all 461 candidates.

3. **3D-generated molecules have 3-22% true synthesis feasibility** via round-trip
   retrosynthesis + forward verification (Gao et al., 2024). Best performer:
   Pocket2Mol at 22.1%. Worst: LiGAN at 2.9%. StateBind's 1D SELFIES VAE likely
   produces more drug-like and thus more synthesizable molecules, but this has not
   been verified. Demonstrating superior synthesis feasibility over 3D methods would
   be a strong differentiator.

4. **ADMETlab 3.0** (Fu et al., 2024; Nucleic Acids Research) offers 119 ADMET
   endpoints via free API (https://admetlab3.scbdd.com), no registration required,
   multi-task DMPNN-Des architecture with classification AUC 0.72-0.99 across 60
   endpoints and regression R^2 0.75-0.95 across 18 endpoints. Rate limit: 5
   requests/second. Batch processing supports up to 1000 SMILES per call.

5. **PKSmart** (Seal et al., 2024; Journal of Cheminformatics, 2025) is the first
   publicly available PK model with performance on par with industry-standard models.
   External validation: VDss R^2=0.39 (GMFE=2.46), CL R^2=0.46 (GMFE=1.95).
   Comparable to AstraZeneca's internal models (R^2=0.30 on matched external set).
   pip-installable (`pip install pksmart`).

6. **Approved EGFR-TKIs define kinase-calibrated thresholds:**

   | Drug | MW | Oral F | T1/2 (h) | Protein Binding | hERG IC50 (uM) | CYP Metabolism |
   |------|-----|--------|----------|----------------|----------------|----------------|
   | Erlotinib | 393 | ~60% | >36 | 95% | ~5 | CYP3A4, CYP1A2 |
   | Gefitinib | 447 | ~50% | 48-52 | 90% | 1.91 | CYP3A4, CYP3A5 |
   | Afatinib | 486 | -- | 37 | 95% | -- | Minimal CYP |
   | Osimertinib | 500 | ~70% | 48 | 95%* | 0.57-2.21 | CYP3A4, CYP3A5 |
   | Dacomitinib | 488 | ~80% | 70 | 98% | -- | CYP2D6 |

   *Osimertinib protein binding: 95% reported in FDA review; fraction unbound ~5%.

   Osimertinib, the current standard-of-care, has a hERG IC50 as low as 0.57 uM --
   far below the standard 10 uM "safe" threshold. QTc prolongation is a known class
   effect of EGFR-TKIs (Wang et al., 2021). This means StateBind's ADMET model is
   CORRECT to flag kinase inhibitors as hERG liabilities. The problem is using
   absolute thresholds rather than kinase-calibrated ones.

7. **ADMET-in-the-loop is now standard practice.** ADMETrix (ICANN 2025 Workshop)
   combines REINVENT with ADMET AI across 27 properties. PMMG (Advanced Science, 2025)
   simultaneously optimizes binding, ADMET, drug-likeness, and synthesizability via
   Pareto MCTS. REINVENT 4 supports weighted multi-component scoring with any
   predictive model. StateBind's architecture already supports multi-component weighted
   scoring -- adding new components is architecturally straightforward.

8. **Drug discovery attrition data:** Roughly 95% of candidates entering clinical
   trials fail. ADMET-related failures (poor PK, organ toxicity, metabolic instability)
   account for a substantial fraction of preclinical attrition. The FDA's April 2025
   announcement phasing out mandatory animal testing for specific drug categories
   increases the value of robust in silico ADMET profiling.

### Relationship to Existing Work

- **StateBind current state:** The unified scoring function has 4 components
  (reference similarity 0.35, drug-likeness 0.30, docking 0.20, state specificity
  0.15). ADMET model exists but is informational only. SA score is embedded within
  drug-likeness at 25% of that component (7.5% of total). No retrosynthetic analysis,
  no PK projections. The scoring architecture uses weighted sums with graceful
  degradation (cascade tiers), which maps perfectly to the tiered approach proposed
  here.

- **Vision System ideas:** This proposal directly builds on **Vision Idea 007:
  Retrosynthetic Feasibility Gate** (deferred at P2 priority). Vision 007 proposed
  ASKCOS/IBM RXN integration. This proposal updates the approach with AiZynthFinder
  4.4.1 (more mature, MIT license, pip-installable) and adds RAscore as a fast proxy
  tier -- a significant improvement over the original proposal. It also extends beyond
  Vision 007 by incorporating ADMETlab 3.0 profiling and PKSmart PK projections,
  which were not part of the original vision.

- **Literature precedent:** SynFormer (PNAS, 2025) generates molecules with built-in
  synthesis routes. The LFM2-2.6B-MMAI foundation model (March 2026) covers the
  entire drug discovery loop including retrosynthesis. These represent the direction
  the field is moving. StateBind's post-hoc approach is a pragmatic middle ground:
  less ambitious than synthesizable-by-design, but immediately implementable with
  existing infrastructure and sufficient for publication-grade demonstration.

---

## Proposed Approach

### Overview

Build a 4-tier drug-ability assessment pipeline that processes all 461 StateBind
candidates through progressively more expensive evaluations: (1) RAscore fast
screening of all candidates, (2) AiZynthFinder full retrosynthetic analysis of top
candidates, (3) ADMETlab 3.0 comprehensive profiling of all candidates against 119
endpoints with kinase-calibrated thresholds, and (4) PKSmart PK projection for final
top candidates. Results feed into both the scoring function (RAscore as a new
component) and a standalone "survival funnel" analysis that tracks how many candidates
from each pipeline (static vs state-aware) survive each filter.

The pipeline produces three publication-grade deliverables: (a) a comparative
synthesis feasibility analysis (state-aware vs static vs 3D generative baselines),
(b) ADMET profiles benchmarked against approved EGFR-TKI reference profiles, and
(c) an end-to-end drug-ability figure for the top 10 candidates.

### Implementation Steps

**Tier 0: RAscore Fast Screening (All 461 Candidates)**

1. Install RAscore from GitHub (`pip install -e .`; requires scikit-learn, xgboost,
   TensorFlow). Confirm compatibility with Python 3.10-3.12 on Bouchet cluster
   (CPU-only, no GPU needed).
2. Run RAscore on all 461 state-aware candidates and all 30 static candidates.
   Expected runtime: seconds to minutes for 491 molecules.
3. Record binary feasibility classification (0/1) and continuous score for each
   molecule. Compute summary statistics: mean RAscore by pipeline, by conformational
   state, by generation method (template vs VAE).
4. Identify the fraction of candidates with RAscore > 0.5 (likely synthesizable) vs
   < 0.5 (likely infeasible) for each pipeline.
5. Integration decision point: either (a) add RAscore as a 5th scoring component
   with a tunable weight, or (b) use as a hard filter (RAscore > 0.5) upstream of
   scoring, or (c) replace SA score within drug-likeness (swap the 25% SA component
   for RAscore within drug-likeness's 30% weight allocation).

**Tier 1: AiZynthFinder Full Retrosynthetic Analysis (Top 50 Candidates)**

6. Install AiZynthFinder 4.4.1 (`pip install aizynthfinder[all]`; Python 3.10-3.12,
   MIT License). Download stock building block database (Enamine building blocks
   preferred for realism; ZINC as fallback).
7. Select top 50 candidates by unified score (approximately top 25 state-aware +
   top 25 static for balanced comparison).
8. Run AiZynthFinder on each candidate with default MCTS settings. Record for each:
   - Route found (yes/no)
   - Number of synthesis steps
   - Number of starting materials
   - Starting material commercial availability (in-stock vs not)
   - Search time (seconds)
   - Route trees (for visualization of top candidates)
9. Compute solve rate by pipeline: What percentage of top-25 state-aware candidates
   have feasible routes vs top-25 static candidates? Benchmark against ChEMBL solve
   rate (71%) and REINVENT-generated solve rate (86%).
10. For candidates with routes found, assess route quality: mean steps, building block
    availability, convergent vs linear routes.

**Tier 2: ADMETlab 3.0 Comprehensive Profiling (All 461 Candidates)**

11. Write a Python script to batch-query the ADMETlab 3.0 API
    (https://admetlab3.scbdd.com) with SMILES strings for all 491 candidates. Rate
    limit: 5 requests/second. At ~1000 SMILES/batch, this requires a single batch
    call for all candidates.
12. Retrieve predictions for all 119 endpoints. Focus analysis on the 6 endpoints
    most relevant to kinase inhibitor drug design:
    - **Absorption:** Caco-2 permeability, oral bioavailability (F30%), P-gp substrate
    - **Metabolism:** CYP3A4 inhibition, CYP2D6 inhibition
    - **Toxicity:** hERG inhibition
    Plus secondary endpoints: solubility, hepatic clearance, AMES mutagenicity,
    hepatotoxicity, plasma protein binding.
13. Apply kinase-calibrated thresholds derived from approved EGFR-TKI profiles:

    | Endpoint | Standard Threshold | Kinase-Calibrated Threshold | Basis |
    |----------|-------------------|---------------------------|-------|
    | hERG | IC50 > 10 uM | IC50 > 0.5 uM | Osimertinib approved at 0.57 uM |
    | CYP3A4 inhibition | Avoid | Accept as manageable | All 1st/3rd-gen EGFR-TKIs are CYP3A4 substrates |
    | Oral F | > 30% | > 30% | Approved TKIs: 50-80% |
    | Caco-2 | > -5.15 log Papp | > -5.15 log Papp | Consistent with approved TKIs |
    | Solubility | > -4 log mol/L | > -4 log mol/L | Standard |
    | AMES | Negative | Negative | Non-negotiable |

14. For each candidate, compute a composite ADMET score: fraction of 6 priority
    endpoints within kinase-calibrated acceptable ranges. Candidates scoring 6/6 are
    "ADMET-clean"; those scoring < 4/6 are flagged.
15. Generate comparative ADMET "spider plots" for the top 10 state-aware candidates
    overlaid on the approved EGFR-TKI reference profile envelope. This is a
    publication-ready figure showing how generated candidates compare to real drugs.
16. Analyze state-dependent ADMET patterns: Do candidates targeting DFG-out
    conformations have different ADMET profiles than DFG-in candidates? DFG-out
    binders tend to be larger and more lipophilic (deeper pocket), which may affect
    absorption, metabolism, and hERG liability. This is a mechanistic insight that
    connects conformational targeting to practical drug properties.

**Tier 3: PKSmart PK Projection (Top 20 Candidates)**

17. Install PKSmart (`pip install pksmart`). Requires Morgan fingerprints + Mordred
    descriptors (both pip-installable).
18. Select top 20 candidates (by composite score incorporating docking + ADMET).
19. Predict for each: VDss, clearance (CL), half-life (t1/2), fraction unbound (fu),
    mean residence time (MRT).
20. Compare predicted PK parameters against approved EGFR-TKI reference ranges:
    - Oral F: > 30% (approved TKIs: 50-80%)
    - T1/2: > 8 h (approved TKIs: 36-70 h; target QD dosing)
    - Clearance: moderate (approved TKI range)
21. Present PK projections with explicit uncertainty disclaimers: "Predictions are
    directional (GMFE ~2-3x) and suitable for ranking, not dose projection."

**Tier 4: Integration and Survival Funnel**

22. Construct the survival funnel tracking all 461 state-aware and 30 static
    candidates through each filter:

    ```
    Stage                    | State-Aware | Static | Note
    -------------------------|-------------|--------|------------------
    Generated                | 461         | 30     | Input
    RAscore > 0.5            | ?           | ?      | Synthesis feasible
    ADMET 6/6 clean          | ?           | ?      | Kinase-calibrated
    AiZynthFinder route      | ?/25        | ?/25   | Top 50 only
    PK acceptable            | ?/10        | ?/10   | Top 20 only
    Full gauntlet survivors  | ?           | ?      | End-to-end viable
    ```

23. The survival funnel is itself a publication figure. The key question: does the
    state-aware pipeline produce a higher fraction of end-to-end viable candidates?
    Or does its greater chemical diversity come at the cost of practicality?

24. For the top 10 final survivors, construct complete "drug-ability profiles" in a
    single table: SMILES, unified score, target state, RAscore, AiZynthFinder route
    (steps, building blocks), ADMET composite score, key ADMET flags, predicted PK
    parameters. This table is the paper's most translatable deliverable.

### Technical Details

**Scoring Function Integration -- Three Options:**

*Option A: RAscore as 5th Component (Recommended)*

Redistribute weights to accommodate a synthesis feasibility component:

| Component | Current Weight | Proposed Weight |
|-----------|---------------|----------------|
| Reference similarity | 0.35 | 0.30 |
| Drug-likeness | 0.30 | 0.25 |
| Docking proxy | 0.20 | 0.20 |
| State specificity | 0.15 | 0.10 |
| Synthesis feasibility (RAscore) | -- | 0.15 |

This follows StateBind's cascade architecture: RAscore as Tier 1 (fast proxy),
AiZynthFinder as Tier 0 (full analysis for top candidates), SA score as Tier 2
(fallback). Mirrors the existing docking cascade (GNINA -> MPNN -> proxy -> stub).

Weight sensitivity analysis must be re-run with all 5 components across random
Dirichlet weight configurations to verify robustness.

*Option B: RAscore Replaces SA Score Within Drug-Likeness*

Replace the SA score contribution (25% of drug-likeness = 7.5% of total) with
RAscore. No weight redistribution needed. Minimal disruption to existing scoring.
Drug-likeness becomes: QED (50%) + Lipinski (25%) + RAscore (25%).

*Option C: Hard Filter Before Scoring*

Apply RAscore > 0.5 as a binary gate before scoring. Candidates below threshold
are excluded. No scoring function modification needed. Simpler but less nuanced --
loses continuous signal.

Recommendation: **Option A** for the primary analysis, with Option B as a robustness
check (reported in supplementary materials). The weight sensitivity analysis across
both configurations demonstrates that the state-aware advantage is robust to scoring
methodology.

**ADMET Integration -- Standalone Analysis, Not Scoring:**

ADMET profiling via ADMETlab 3.0 should be presented as a standalone post-scoring
analysis rather than integrated into the scoring function. Rationale:

- ADMETlab 3.0 predictions come from an external API (not a trained StateBind model),
  introducing a dependency on an external service.
- 119 endpoints require aggregation into a composite score, which introduces new
  subjective choices (which endpoints, what weights).
- The kinase-calibrated thresholds are novel and should be validated before being
  baked into the scoring function.
- As a standalone analysis, ADMET profiling provides an independent validation
  dimension without contaminating the existing fair comparison.

The existing StateBind ADMET model (6 endpoints, GIN backbone) could later be
upgraded or supplemented, but that is a separate workstream.

**Data Flow Architecture:**

```
All 461 + 30 candidates (SMILES)
        |
        v
[Tier 0: RAscore]  --> RAscore values for all 491 molecules
        |                   |
        v                   v
[Tier 2: ADMETlab API] --> 119-endpoint profiles for all 491
        |                   |
        v                   v
[Scoring: 5-component]     [ADMET analysis: kinase-calibrated]
        |                   |
        v                   v
    Top 50 by score     ADMET spider plots, state-dependent patterns
        |
        v
[Tier 1: AiZynthFinder] --> Routes for top 50
        |
        v
    Top 20 (score + route)
        |
        v
[Tier 3: PKSmart] --> PK projections for top 20
        |
        v
    Survival Funnel + Drug-ability Profiles (Top 10)
```

---

## Impact Assessment

### Publication Impact

- **Target venue:** JCIM (primary), Nature Computational Science (aspirational).
  Both venues value practical applicability and translational awareness. End-to-end
  profiling directly addresses what drug discovery practitioners find naive about
  academic AI drug design papers (Section 13 of the project briefing).

- **Main claim this enables:** "StateBind is the first conformational-state-aware
  molecular design pipeline to demonstrate end-to-end drug-ability assessment,
  showing that X% of top state-aware candidates have feasible synthesis routes,
  ADMET profiles comparable to approved EGFR-TKIs, and projected oral PK compatible
  with QD dosing."

- **Reviewer concerns this addresses:**
  - "Where is the practical applicability?" -- Full ADMET + retrosynthesis + PK
    profiles for top candidates. Most AI drug design papers stop at scoring.
  - "Can these molecules actually be made?" -- AiZynthFinder routes with building
    block availability for top candidates. Benchmarked against ChEMBL solve rate.
  - "What about ADMET?" -- 119-endpoint profiles from ADMETlab 3.0, compared
    against approved EGFR-TKI reference profiles with kinase-calibrated thresholds.
  - "SA score is a weak proxy" -- RAscore replaces or supplements SA score,
    providing a retrosynthesis-informed feasibility metric. AiZynthFinder validates
    top candidates at full depth.

- **Novel publication points:**
  1. First conformational-state-aware pipeline with retrosynthetic validation.
  2. Kinase-calibrated ADMET thresholds derived from approved drug profiles -- a
     reusable contribution beyond this paper.
  3. Comparative synthesis feasibility of 1D VAE-generated vs 3D-generated molecules
     (if StateBind's rate exceeds the 3-22% range, this is a strong result).
  4. State-dependent ADMET patterns: do DFG-out-targeting candidates have different
     ADMET profiles? (mechanistic insight connecting conformation to drug properties).
  5. The "survival funnel" as a new standard figure for AI drug design papers.

### Effort Estimate

- **Compute:**
  - RAscore: CPU-minutes for all 491 molecules. Trivial on any Bouchet node.
  - AiZynthFinder: 40-90 sec/molecule x 50 molecules = ~35-75 minutes. Single
    CPU node on `day` partition. No GPU needed.
  - ADMETlab 3.0: API calls at 5 req/sec. 491 molecules in a single batch or
    ~2 minutes of API calls. Requires outbound internet access from Bouchet
    (or run from a login node / local machine).
  - PKSmart: Minutes total for 20 molecules. CPU-only.
  - **Total compute: < 2 hours of wall time** (excluding scripting/debugging).

- **Data:**
  - All 461 state-aware + 30 static candidate SMILES (already generated,
    available in artifacts/).
  - AiZynthFinder stock database (Enamine building blocks or ZINC; downloaded
    once, ~GB scale).
  - ADMETlab 3.0 API access (public, free, no registration).
  - Approved EGFR-TKI reference ADMET data (from literature; compiled above).

- **Implementation:**
  - Week 1: Install RAscore + AiZynthFinder + PKSmart. Verify on Bouchet.
    Write ADMETlab 3.0 API client script. Run RAscore on all candidates. Run
    ADMETlab 3.0 API queries.
  - Week 2: Run AiZynthFinder on top 50. Run PKSmart on top 20. Compile
    kinase-calibrated ADMET thresholds. Generate comparative analyses.
  - Week 3: Integrate RAscore into scoring function (Option A). Re-run weight
    sensitivity analysis. Construct survival funnel. Generate publication
    figures (ADMET spider plots, survival funnel, drug-ability table).
  - Week 4 (buffer): Address edge cases, validate results, write up methods
    section for the paper.
  - **Total: 3-4 weeks.**

- **Dependencies:**
  - Candidate SMILES from existing pipeline output (available).
  - Internet access for ADMETlab 3.0 API (check Bouchet cluster policy;
    login nodes typically have internet access).
  - pip installability of RAscore, AiZynthFinder, PKSmart on Bouchet
    (all are pure Python or have conda-installable dependencies; RDKit
    already available in the project environment).

### Risk Assessment

- **Technical risks:**
  - *RAscore out-of-distribution for VAE-generated molecules:* RAscore was trained
    on ChEMBL chemical space. StateBind's VAE-generated molecules may be
    out-of-distribution, leading to unreliable predictions. **Mitigation:** Use
    applicability domain checking (Tanimoto distance to RAscore training set).
    Report out-of-domain fraction. AiZynthFinder Tier 1 provides ground truth
    for top candidates regardless.
  - *ADMETlab 3.0 API availability:* External API dependency. If the API is down or
    rate-limited during the analysis window, results are delayed.
    **Mitigation:** Cache all API responses. ADMETlab 3.0 has been operational since
    July 2024 with no reported extended outages. Alternatively, use Deep-PK (73
    endpoints) or admetSAR 3.0 as backup.
  - *AiZynthFinder stock database coverage:* Building block availability affects
    solve rates. Using ZINC stock (~60% coverage) vs E-Molecules (~80%) vs
    Enamine produces different solve rates. **Mitigation:** Report solve rates
    with multiple stock databases. Use Enamine building blocks as primary
    (most realistic for actual synthesis).
  - *Cluster internet access for API calls:* Bouchet login nodes may have restricted
    outbound access. **Mitigation:** Run API calls from login node or local machine;
    transfer results as JSON artifacts. ADMETlab 3.0 also offers a batch upload
    interface via the web frontend as a manual fallback.

- **Scientific risks:**
  - *State-aware candidates may have LOWER synthesis feasibility:* Greater chemical
    diversity (0.9056 vs 0.5684) could mean more exotic structures that are harder
    to synthesize. If static candidates have higher RAscore/AiZynthFinder solve
    rates, this undermines the narrative. **Mitigation:** Report honestly. Frame as
    a tradeoff: state-aware design explores more chemical space at the cost of
    some synthesis feasibility. The 10x enrichment result holds regardless of
    synthesis rates. The survival funnel would then show that state-aware design
    requires more filtering but produces better hits.
  - *PK predictions may be uninformative:* PKSmart VDss R^2=0.39 and CL R^2=0.46
    mean predictions explain less than half the variance. **Mitigation:** Present PK
    projections as directional only. Categorize candidates as "favorable" /
    "acceptable" / "unfavorable" PK rather than reporting precise parameter values.
    Explicitly state GMFE ~2-3x uncertainty in the methods section.
  - *Kinase-calibrated thresholds are a judgment call:* No consensus standard exists.
    Reviewers may challenge the thresholds as too lenient (especially hERG > 0.5 uM).
    **Mitigation:** Derive thresholds transparently from approved drug profiles with
    full citations. Report results under both standard and kinase-calibrated
    thresholds. Let the data speak.
  - *Negative result on end-to-end viability:* If very few candidates (<5%) survive
    the full gauntlet, this looks bad for the pipeline. **Mitigation:** A low
    survival rate is actually realistic -- drug discovery has >95% attrition.
    Compare survival rate against published rates for other generative models.
    Even a 5-10% end-to-end survival rate, if comparable to or better than
    published baselines, is a positive result.

---

## Evaluation Criteria

1. **RAscore screening coverage:** > 80% of all 461 state-aware candidates receive
   a valid RAscore prediction (not out-of-domain). Target: mean RAscore > 0.5 for
   candidates that pass the existing scoring threshold.

2. **AiZynthFinder solve rate:** Solve rate for top 50 candidates should be
   benchmarked against ChEMBL (71%) and REINVENT-generated (86%) baselines.
   Success: solve rate > 50% for top state-aware candidates. Strong result: > 70%.
   Publication-ready comparison: solve rate difference between state-aware and
   static candidates with statistical test (Fisher's exact, N=25 per group).

3. **ADMET profile comparability:** Top 10 state-aware candidates should have ADMET
   profiles within the "approved EGFR-TKI envelope" (defined by min/max of
   erlotinib, gefitinib, osimertinib, afatinib, dacomitinib) on at least 4 of 6
   priority endpoints. Success: > 50% of top 10 candidates are "ADMET-clean" (6/6
   priority endpoints within kinase-calibrated thresholds).

4. **State-dependent ADMET patterns:** Test whether DFG-out-targeting candidates
   have statistically different ADMET profiles than DFG-in-targeting candidates
   (Mann-Whitney U on composite ADMET score). Any significant difference is a
   publication-worthy mechanistic insight.

5. **PK projection acceptability:** > 50% of top 20 candidates should have predicted
   oral bioavailability > 30% and half-life > 8 hours (consistent with QD dosing).

6. **Survival funnel metrics:** Report the absolute number and percentage of
   candidates surviving each filter stage. Key metric: the state-aware-to-static
   ratio of end-to-end survivors relative to the input ratio (461:30 = 15.4x). If
   the survivor ratio is > 10x, state-aware design produces more viable candidates
   even after stringent filtering.

7. **Scoring function robustness:** After integrating RAscore as a 5th component,
   re-run weight sensitivity analysis (100 random Dirichlet weight configurations).
   The 10x retrospective enrichment advantage should be maintained (EF@10 > 3x for
   state-aware at both time-split cutoffs).

---

## Open Questions

1. **Bouchet cluster internet access policy:** Can API calls to external servers
   (ADMETlab 3.0) be made from compute nodes, or only login nodes? This determines
   whether the ADMETlab step can be submitted as a SLURM job or must be run
   interactively. Fallback: run locally and transfer JSON artifacts.

2. **RAscore Python compatibility:** The RAscore repository was built for Python 3.7+
   with TensorFlow. StateBind uses Python 3.10-3.12. TensorFlow version conflicts
   are possible. May need a separate conda environment for RAscore. Alternative:
   use the XGBoost-based RAscore model (also provided in the repository), which has
   fewer dependency conflicts.

3. **AiZynthFinder stock database selection:** Which building block stock database to
   use as the primary? Enamine is most realistic but may require a data license
   agreement. ZINC is freely available but has lower coverage (~60% vs ~80%).
   AiZynthFinder ships with a default stock file that can be supplemented.

4. **Scoring weight redistribution:** Adding RAscore as a 5th component requires
   reducing weights on existing components. Which component(s) should lose weight?
   The Round 1 synthesis identified reference similarity (0.35) as already too high.
   Reducing it to 0.30 and state specificity to 0.10 (freeing 0.10 for RAscore +
   borrowing 0.05 from drug-likeness) is one option, but this must be justified
   independently of whether it helps or hurts the state-aware pipeline.

5. **ADMETlab 3.0 vs StateBind ADMET model:** Should the paper use external ADMET
   predictions (ADMETlab 3.0, 119 endpoints, SOTA accuracy) or the internal ADMET
   model (6 endpoints, below TDC SOTA)? Using both and comparing provides the most
   complete picture, but increases analysis complexity.

6. **Retrospective validation impact:** If RAscore is integrated into the scoring
   function, the retrospective time-split validation must be re-run. Does adding
   synthesis feasibility to the scoring function maintain or improve the 10x
   enrichment? This is a critical test: if the enrichment drops, the synthesis
   component may need to remain a post-hoc analysis rather than a scoring component.

---

## References

1. Thakkar, A., et al. (2024). "AiZynthFinder 4.0: developments based on learnings
   from 3 years of industrial application." *Journal of Cheminformatics*, 16, 56.
   DOI: 10.1186/s13321-024-00860-x

2. Thakkar, A., et al. (2021). "Retrosynthetic accessibility score (RAscore) -- rapid
   machine learned synthesizability classification from AI driven retrosynthetic
   planning." *Chemical Science*, 12, 3339-3349. DOI: 10.1039/D0SC05401A

3. Gao, S., et al. (2024). "Evaluating Molecule Synthesizability via Retrosynthetic
   Planning and Reaction Prediction." *arXiv*:2411.08306v2.

4. Fu, L., et al. (2024). "ADMETlab 3.0: an updated comprehensive online ADMET
   prediction platform enhanced with broader coverage, improved performance, API
   functionality and decision support." *Nucleic Acids Research*, 52(W1), W422-W431.
   DOI: 10.1093/nar/gkae236

5. Seal, S., et al. (2025). "PKSmart: an open-source computational model to predict
   intravenous pharmacokinetics of small molecules." *Journal of Cheminformatics*,
   17. DOI: 10.1186/s13321-025-01066-5

6. Skoraczynski, G., et al. (2023). "Critical assessment of synthetic accessibility
   scores in computer-assisted synthesis planning." *Journal of Cheminformatics*, 15, 6.
   DOI: 10.1186/s13321-023-00678-z

7. Wang, Z., et al. (2021). "Mechanisms of gefitinib-induced QT prolongation."
   *European Journal of Pharmacology*, 910, 174467.
   DOI: 10.1016/j.ejphar.2021.174467

8. Zhong, Y., et al. (2023). "Acute osimertinib exposure induces electrocardiac
   changes by synchronously inhibiting the currents of cardiac ion channels."
   *Frontiers in Pharmacology*, 14, 1177003. DOI: 10.3389/fphar.2023.1177003

9. Mourdou, N., et al. (2026). "ADMETrix: ADMET-Driven De Novo Molecular Generation."
   *ICANN 2025 Workshop on AI for Drug Discovery*. ChemRxiv.
   DOI: 10.26434/chemrxiv-2025-3x5nq-v3

10. Loeffler, H., et al. (2024). "REINVENT 4: Modern AI-driven generative molecule
    design." *Journal of Cheminformatics*, 16, 20. DOI: 10.1186/s13321-024-00812-5

11. Liu, J., et al. (2025). "A Multi-Objective Molecular Generation Method Based on
    Pareto Algorithm and Monte Carlo Tree Search." *Advanced Science*, 12(23), 2410640.
    DOI: 10.1002/advs.202410640

12. Gao, W., et al. (2025). "Generative AI for navigating synthesizable chemical
    space." *Proceedings of the National Academy of Sciences*, 122(41), e2415665122.
    DOI: 10.1073/pnas.2415665122

13. Roskoski, R. (2021). "Small Molecule Kinase Inhibitor Drugs (1995-2021): Medical
    Indication, Pharmacology, and Synthesis." *Journal of Medicinal Chemistry*, 65(2),
    1003-1072. DOI: 10.1021/acs.jmedchem.1c00963

14. Gao, S., et al. (2025). "RetroScore: graph edit distance-guided retrosynthesis
    for accessibility scoring with route metrics." *Journal of Cheminformatics*, 17.
    DOI: 10.1186/s13321-025-01138-6

15. Myung, Y., et al. (2024). "Deep-PK: deep learning for small molecule
    pharmacokinetic and toxicity prediction." *Nucleic Acids Research*, 52(W1),
    W469-W475. DOI: 10.1093/nar/gkae254

16. Neeser, R., et al. (2024). "FSscore: A Personalized Machine Learning-Based
    Synthetic Feasibility Score." *Chemistry-Methods*, 4(6), e202400024.
    DOI: 10.1002/cmtd.202400024

17. Kang, S. P., et al. (2021). "Cardiac Safety Assessment of Lazertinib." *JTO
    Clinical and Research Reports*, 2(10), 100224. DOI: 10.1016/j.jtocrr.2021.100224

18. Cosme, J. (2019). "FDA- and EMA-Approved Tyrosine Kinase Inhibitors in Advanced
    EGFR-Mutated Non-Small Cell Lung Cancer: Safety, Tolerability, Plasma
    Concentration Monitoring, and Management." *International Journal of Molecular
    Sciences*, 20(23), 6052. DOI: 10.3390/ijms20236052

19. Isaev, D., et al. (2026). "Critical Assessment of ML models for ADMET Prediction
    in TDC leaderboards." *bioRxiv*. DOI: 10.64898/2026.02.26.708193v1

20. Huang, K., et al. (2022). "Artificial intelligence foundation for therapeutic
    science." *Nature Chemical Biology*, 18, 1033-1036.
    DOI: 10.1038/s41589-022-01131-2

21. NovoExpert Team (2026). "NovoExpert-2: State-of-the-Art ADMET Prediction via
    Gradient-Boosted Trees on MapLight Fingerprints and GIN Embeddings." *ChemRxiv*.

22. Zhavoronkov, A., et al. (2023). "Chemistry42: An AI-Driven Platform for Molecular
    Design and Optimization." *Journal of Chemical Information and Modeling*, 63(3),
    695-701. DOI: 10.1021/acs.jcim.2c01191

23. Gao, W., et al. (2020). "The Synthesizability of Molecules Proposed by Generative
    Models." *Journal of Chemical Information and Modeling*, 60(12), 5714-5723.
    DOI: 10.1021/acs.jcim.0c00174

24. Lehmann, H. A., et al. (2018). "Validation and Clinical Utility of the hERG
    IC50:Cmax Ratio to Determine the Risk of Drug-Induced Torsades de Pointes."
    *Pharmacotherapy*, 38(3), 341-348. DOI: 10.1002/phar.2087
