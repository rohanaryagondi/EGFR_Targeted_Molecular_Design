---
agent: Sr. Journal Reviewer -- Comp Bio
round: 3
date: 2026-04-09
type: review-assessment
scope: deliberation
---

# Round 3 Deliberation: Final Assessment and Prioritization

## Executive Summary

After reviewing all five Round 2 verification reports and the synthesis, I update
my positions on four critical questions. (1) The compute-matched comparison
concern raised by mlrev is *partially* applicable to enrichment but less damaging
than mlrev suggests, because enrichment factors are rank-normalized within each
pipeline, not cross-pipeline counts; however, the *diversity confound* is the
real threat and must be addressed. (2) The structural annotation errors are
addressable without abandoning the 4-state model, but only if handled with full
transparency; using mutant DFGout structures is defensible given proper disclosure,
structural analysis showing conformational geometry dominates mutational
perturbation, and sensitivity analysis. (3) My final prioritization places
structural audit, MPNN scaffold split, and the unconditioned-VAE ablation as
the three blocking gates before submission. (4) JCIM is the correct venue with
estimated 55-65% acceptance probability given the proposed fixes; Nature Comp
Sci remains premature.

---

## 1. Response to mlrev: Compute-Matched Comparison and Enrichment

### 1.1 The Enrichment Factor Is Internally Normalized -- But Not Immune

mlrev correctly identifies that the 30 vs 461 candidate ratio is a 15:1 oracle
call imbalance and that PMO-style fixed-budget comparison is the accepted ML
standard. I agree this is a mandatory fix for the *mean score comparison* and
any head-to-head framing. However, mlrev's claim that the retrospective enrichment
result is "also affected" deserves careful unpacking, because enrichment factors
are not directly comparable to oracle call metrics.

The enrichment factor as implemented in `retrospective.py:159-197` is:

```
EF@K = (hits_in_top_K / K) / (total_hits / N)
```

where N is the total number of candidates in *that pipeline*, hits are candidates
with Tanimoto similarity >= 0.4 to a future drug, and K=10.

This metric is *internally normalized* within each pipeline. The denominator
`total_hits / N` is the expected hit rate under random ranking for that specific
pool. EF@10 = 4.95 for the state-aware pipeline means that the top-10 (out of
461) candidates are 4.95x more likely to be future-drug-similar than a random
draw from the same 461-candidate pool. Similarly, EF@10 = 0.47 for the static
pipeline means the top-10 (out of 30) candidates are 0.47x (i.e., worse than
random) at concentrating future-drug-similar molecules.

**What the 15:1 ratio does NOT affect in enrichment:**
- The enrichment factor is a ratio of internal concentrations, not a count.
  Adding more candidates to a pool does not mechanically increase EF unless
  those candidates are specifically enriched in the top ranks.
- Random addition of irrelevant molecules would *decrease* EF by diluting the
  hit rate denominator without adding hits to the top-K.

**What the 15:1 ratio DOES affect, indirectly:**
- A larger, more diverse pool has a higher probability of containing at least
  one molecule similar to any given future drug. This is a *coverage* effect,
  not an *enrichment* effect. With 461 candidates spanning 4 conformational
  states, the probability of sampling a molecule that happens to be structurally
  similar to osimertinib (a DFGin/aCin binder) or lapatinib (a DFGin/aCout
  binder) is higher than with 30 candidates clustered around erlotinib analogs.
- The total_hits count in the denominator will be higher for a larger pool,
  but only if the additional molecules include hits. If the VAE is generating
  random molecules, additional candidates would contribute non-hits and the
  enrichment factor would remain unaffected.

### 1.2 The Real Threat Is the Diversity Confound, Not the Count

The genuine concern is not "30 vs 461" per se but the confound between
*state-conditioning* and *diversity*. The state-aware pipeline generates
molecules conditioned on 4 different pocket geometries, producing structurally
diverse candidates spanning multiple pharmacological classes. The static
pipeline generates molecules from a single pocket (1M17), producing candidates
clustered in one chemical series.

The question a reviewer will ask is: "Does the enrichment advantage come from
*discrete state labels* specifically, or simply from *generating a more diverse
candidate pool*?" This is Kill Shot 3 from the Round 2 synthesis, and it is
more precisely stated than the oracle-call framing.

**The ablation C (unconditioned VAE) directly addresses this.** If you train a
VAE without state labels but sample the same number of molecules (461), and the
unconditioned VAE achieves similar enrichment, then the state labels are not
contributing. If the conditioned VAE shows significantly higher enrichment
(Cohen's d >= 0.8, pre-registered), then state conditioning matters beyond
mere diversity.

### 1.3 My Updated Position

I partially agree with mlrev on the need for compute-matched comparison, but
I disagree that the enrichment result is "partially or wholly explained by
the larger, more diverse candidate pool." The enrichment factor formula
normalizes for pool size. The diversity confound is real but is addressed by
ablation C, not by PMO-style oracle budgets.

**What must be done:**
1. **Implement fixed oracle call budget for the mean-score comparison.**
   This is mandatory for any head-to-head claim. Use N=500 oracle calls per
   pipeline. Report AUC of top-10 average score vs oracle calls.
2. **Run ablation C (unconditioned VAE) for the enrichment comparison.**
   Generate 461 candidates from unconditioned VAE. Compute EF@10. If EF@10
   for conditioned > unconditioned at Cohen's d >= 0.8, the state-conditioning
   effect is real. Pre-register this threshold.
3. **Report both original (30 vs 461) and compute-matched results.** The
   original comparison has pedagogical value -- it shows the natural output of
   each pipeline -- but the compute-matched comparison is what proves fairness.
4. **Do NOT claim that EF@10 directly proves state-conditioning superiority
   without ablation C.** The EF@10 result is necessary but not sufficient.

### 1.4 Specific Recommendation for the Paper

The paper should present the enrichment story in three layers:

- **Layer 1 (Current pipeline output):** "The state-aware pipeline generates
  461 candidates across 4 conformational states; the static pipeline generates
  30 candidates from one state. EF@10 is 4.95 vs 0.47. We acknowledge the pool
  size difference."
- **Layer 2 (Compute-matched):** "Under a fixed 500-oracle-call budget, the
  state-aware pipeline achieves mean score X vs static Y. AUC top-10 is Z."
- **Layer 3 (Ablation):** "An unconditioned VAE generating the same number of
  candidates achieves EF@10 = W, demonstrating that the enrichment advantage is
  [attributable to / not attributable to] state conditioning specifically."

This three-layer presentation anticipates all reviewer objections and demonstrates
methodological rigor.

---

## 2. Structural Atlas Resolution: 4-State vs 3-State

### 2.1 Can Mutant DFGout Structures Be Used Defensibly?

After reflection on all Round 2 findings and my own verification, I conclude
that **using T790M/L858R mutant structures for the DFGout states is defensible,
provided three conditions are met:**

**Condition 1: Full disclosure.** The paper must explicitly state that no
wild-type EGFR DFGout crystal structure exists in PDB, that all DFGout
representatives carry T790M and/or L858R mutations, and that this is a known
limitation. This goes in both the Methods section and a dedicated Limitations
paragraph.

**Condition 2: Structural justification that conformational geometry dominates.**
The T790M mutation (gatekeeper) and L858R mutation (activation loop) affect
specific local regions of the binding pocket. The DFG motif conformation
(position of Asp855, Phe856) and the aC-helix position are determined by
backbone geometry that is largely conserved across mutants. The project must
compute:
- RMSD of the DFG motif region (residues 855-860) between WT DFGin structures
  and mutant DFGout structures, compared to RMSD between WT DFGin and WT DFGin.
  The conformational RMSD should be substantially larger than the mutational RMSD.
- Pocket volume comparison: DFGout pockets (even with mutations) should be
  geometrically distinct from DFGin pockets (with or without mutations). If the
  DFGout pocket volume is 600+ Angstrom^3 vs DFGin at 450 Angstrom^3 (as
  suggested by the conditioning.py pocket descriptors), the conformational
  difference dominates.
- Back-pocket accessibility: DFGout structures open a hydrophobic back pocket
  that DFGin structures do not, regardless of gatekeeper mutations.

If these analyses show that the DFGin-to-DFGout conformational change produces
larger structural differences than T790M/L858R mutations within a single DFG
state, then using mutant DFGout structures as proxies for the DFGout pocket
*geometry* is defensible.

**Condition 3: Sensitivity analysis.** The paper should include a supplementary
analysis: "What happens if we drop the DFGout states entirely and run a 2-state
model (DFGin/aCin vs DFGin/aCout)?" If the enrichment advantage persists with
only 2 wild-type states (1M17 for DFGin/aCin and 2GS7 for DFGin/aCout), this
demonstrates that the state-conditioning concept is sound even without DFGout.
Conversely, if the advantage disappears, it was driven by DFGout-generated
molecules and the mutant proxy question becomes critical.

### 2.2 Should We Drop to 3 States?

I do not recommend dropping to a 3-state model as the primary analysis for
several reasons:

1. **Clinical relevance.** T790M and L858R are the most clinically significant
   EGFR mutations. Roughly 50-60% of NSCLC patients with EGFR mutations harbor
   these variants (Soria et al., 2018; Sequist et al., 2011). Designing
   molecules that bind the DFGout conformation of T790M/L858R EGFR is arguably
   *more* clinically relevant than designing for wild-type DFGout, which has no
   experimental structure and may not be significantly populated in vivo.

2. **The project thesis can be reframed.** Instead of "state-conditioned
   generation for wild-type EGFR," the thesis becomes "state-conditioned
   generation across conformational states observed in clinically relevant EGFR
   variants." This is honest, clinically motivated, and experimentally grounded.

3. **4 states preserves the full KLIFS classification.** The KLIFS database
   defines 4 canonical kinase conformations: DFGin/aCin, DFGin/aCout,
   DFGout/aCin, DFGout/aCout (Kooistra et al., 2021). Dropping to 3 states
   abandons the KLIFS framework that motivates the project.

4. **A 2-state or 3-state sensitivity analysis is sufficient.** Rather than
   making 3 states the primary model, include 2-state and 3-state results as
   sensitivity analyses in the supplement. If enrichment persists at 2 states
   (both WT), the 4-state result with mutant DFGout structures is strengthened,
   not weakened.

### 2.3 What I Would Accept as a Journal Reviewer

As a reviewer at JCIM, I would accept the 4-state model with mutant DFGout
structures IF the paper:

1. **Discloses in the Abstract or Introduction** that DFGout structures use
   clinically relevant mutant proteins.
2. **Provides Table 1** listing all representative structures, their PDB IDs,
   mutations, resolution, DFG state, aC state, and source (PDB/KLIFS). The
   current codebase annotations must be corrected first.
3. **Shows RMSD analysis** demonstrating conformational change >> mutational
   perturbation for the binding pocket geometry.
4. **Reports 2-state and 4-state enrichment** side by side. If 2-state WT-only
   enrichment is positive, the 4-state mutant-inclusive result is further
   supported.
5. **Cites Ung & Schlessinger (2015)** and Shan et al. (2013) to acknowledge
   that WT DFGout EGFR is populated in MD simulations but not experimentally
   captured.

What I would **reject** is:
- Listing 3W2R as wild-type (current codebase)
- Using 3iku as a PDB ID (this is a bacterial protein, not EGFR)
- Listing 5D41 as wild-type
- Classifying 4ZAU as DFGout without 3D geometric verification

### 2.4 The 4ZAU Question

The 4ZAU classification is the most consequential single error. If 4ZAU is
confirmed as DFGin (which the circumstantial evidence strongly suggests), then:

- The DFGout/aCout state has *zero* representative structures (mutant or WT).
- The pocket descriptors, docking targets, and VAE conditioning for this state
  are all wrong.
- Either a legitimate DFGout/aCout structure must be found (I could not identify
  one in PDB for EGFR), or this state must be dropped, yielding a 3-state model.

If 4ZAU is confirmed as DFGin by direct 3D coordinate inspection, I would
recommend a 3-state model (DFGin/aCin, DFGin/aCout, DFGout/aCin) as the primary
analysis, with 4ZAU reclassified to its correct state. The 5D41 structure (L858R/
T790M mutant) could potentially serve as a DFGout/aCout representative with
proper mutation disclosure, but only after independent geometric verification
confirms its DFG conformation.

This 4ZAU verification is a 1-2 hour task and must be completed before any
other work proceeds.

---

## 3. Final Prioritization

I organize my prioritization into four tiers with explicit go/no-go gates.

### Tier 0: Publication-Blocking Prerequisites (Weeks 0-2)

These items must be completed before any other work. Failure at any gate
terminates or fundamentally restructures the publication plan.

**Item 0.1: 4ZAU 3D Coordinate Inspection**
- Effort: 1-2 hours
- Go/No-Go: If DFGin confirmed, reclassify. If DFGout confirmed, retain.
- Impact: Determines whether the model is 3-state or 4-state.
- Expected impact on reviewability: CRITICAL. Wrong classification is an
  immediate reject.

**Item 0.2: Correct Structural Annotations**
- Effort: 4-8 hours
- Actions: Fix 3iku -> 3IKA (or remove); add T790M to 3IKA, T790M/L858R to
  3W2R and 5D41; reclassify 4ZAU per Item 0.1; remove 3iku annotation.
- Go/No-Go: All annotations must match PDB records exactly. Verify with PDB
  API.
- Expected impact on reviewability: CRITICAL. Incorrect PDB annotations are
  unpublishable.

**Item 0.3: Assess Cascading Impact**
- Effort: 1-2 days
- Question: Do the corrected structures change pocket descriptors, GNINA
  docking scores, or VAE conditioning labels?
- If pocket descriptors change significantly: re-run docking and VAE
  conditioning (adds 1-2 weeks).
- If descriptors are stable: proceed with existing docking results but disclose
  the corrected annotations.
- Go/No-Go: Pocket descriptor changes < 10% from previous values = proceed.
  Changes > 20% = re-run.

**Item 0.4: Fix Osimertinib Reference Leakage**
- Effort: 2-4 hours
- Impact: Removes temporal leakage in baseline scoring.
- Go/No-Go: Binary. Either it is removed or not.

**Item 0.5: MPNN Scaffold Split Implementation**
- Effort: 2-3 days
- Actions: Implement Bemis-Murcko scaffold splitting in `split_dataset()`.
  Retrain MPNN with scaffold split. Report R^2 under random, scaffold, and
  temporal splits.
- Go/No-Go: Scaffold-split R^2 >= 0.35 = MPNN contributes meaningfully.
  R^2 < 0.25 = MPNN component should be downweighted or removed from scoring.
- Expected impact on reviewability: HIGH. Random-split R^2 is a known red flag.
  Reporting scaffold-split R^2 demonstrates awareness of the issue.

**Item 0.6: Bootstrap Confidence Intervals on Current Results**
- Effort: 4-8 hours
- Actions: Compute 1000-bootstrap 95% CIs on EF@10, BEDROC, mean scores.
- Go/No-Go: If static 95% CI overlaps state-aware 95% CI on the enrichment
  metric, the result is not statistically significant and the paper's central
  claim is undermined.
- Expected impact on reviewability: ESSENTIAL. No CIs = immediate major revision
  request at any venue.

**Item 0.7: Write and Timestamp Pre-Registration Document**
- Effort: 2-4 hours
- Actions: Document ablation hypotheses, success thresholds (Cohen's d >= 0.8
  for ablation C), and analysis plan before running experiments. Timestamp with
  git commit or OSF registration.
- Expected impact on reviewability: MODERATE-HIGH. Pre-registration transforms
  confirmatory claims from post-hoc to a priori, which is increasingly expected
  at top venues.

### Tier 1: Critical Path for Submission (Weeks 2-8)

**Item 1.1: Ablation C -- Unconditioned VAE**
- Effort: 3-5 days
- Actions: Train VAE without state conditioning. Generate 461 candidates.
  Score and compute EF@10.
- Go/No-Go: Cohen's d >= 0.8 between conditioned and unconditioned EF@10
  distributions (via bootstrap resampling). This is THE make-or-break gate
  for the entire publication.
- If d < 0.8: The paper pivots from "state conditioning improves enrichment"
  to "state conditioning improves diversity and specificity" -- a weaker but
  still publishable claim.
- Expected impact on reviewability: DECISIVE. This ablation is the single
  experiment most likely to determine accept/reject.

**Item 1.2: Compute-Matched Score Comparison**
- Effort: 1-2 weeks
- Actions: Implement fixed 500-oracle-call budget. Run static, state-aware,
  and unconditioned pipelines under budget constraint. Report PMO-style AUC.
- Go/No-Go: State-aware AUC >= static AUC under equal budget.
- Expected impact on reviewability: HIGH for ML-audience reviewers. JCIM
  reviewers may care less but will respect the rigor.

**Item 1.3: VAE Metric Replacement**
- Effort: 3-5 days
- Actions: Compute FCD (via fcd_torch), reconstruction accuracy, novelty,
  internal diversity (#Circles or SEDiv). Remove validity from headline metrics.
- Go/No-Go: FCD < 2.0 (reasonable for drug-like molecules). Reconstruction
  accuracy > 80%.
- Expected impact on reviewability: MODERATE. Necessary for ML rigor but not
  the central claim.

**Item 1.4: Structural RMSD Analysis**
- Effort: 1-2 days
- Actions: Compute DFG-motif RMSD and pocket-volume comparisons as described
  in Section 2.2.
- Go/No-Go: Conformational RMSD > 2x mutational RMSD for the DFG-motif region.
- Expected impact on reviewability: HIGH. Directly addresses the structural
  annotation concern.

**Item 1.5: Multi-Kinase Extension -- ABL1 (Incremental)**
- Effort: 6-9 person-weeks (largest single item)
- Actions: Curate ABL1 structures, drug approvals (imatinib 2001, dasatinib
  2006, nilotinib 2007, bosutinib 2012, ponatinib 2012, asciminib 2021), pocket
  descriptors. Run full pipeline. Compute EF@10.
- Go/No-Go: ABL1 EF@10 > 1.0 for state-aware pipeline AND ABL1 EF@10
  (state-aware) > ABL1 EF@10 (static).
- Expected impact on reviewability: VERY HIGH. Single-kinase results are the
  #1 weakness. A second kinase transforms the paper from "case study" to
  "systematic benchmark."

### Tier 2: Strengthening (Weeks 5-14)

**Item 2.1: BRAF Extension**
- Effort: 3-5 person-weeks
- Contingent on: Item 1.5 succeeding for ABL1.
- Expected impact: Moves from "two kinases" to "three kinases," which is the
  minimum for a convincing multi-kinase claim.

**Item 2.2: REINVENT 4 Integration**
- Effort: 8-15 days (per principal's estimate, which I trust)
- Purpose: Within-method ablation (does the advantage of state labels persist
  across architectures?).
- Go/No-Go: REINVENT state-conditioned EF@10 > REINVENT single-pocket EF@10.
- Expected impact: MODERATE-HIGH. Cross-architecture validation is powerful
  but not strictly necessary for JCIM.

**Item 2.3: Conformal Prediction via TorchCP**
- Effort: 1 week
- Purpose: Uncertainty quantification for MPNN predictions.
- Expected impact: MODERATE. Nice to have, demonstrates methodological
  sophistication.

**Item 2.4: Scoring Sensitivity Analysis (Dirichlet)**
- Effort: 3-5 days
- Purpose: Show results are robust to scoring weight choices.
- Expected impact: MODERATE. Addresses the "mean score gap" concern.

**Item 2.5: Chemical Space Visualization**
- Effort: 2-3 days
- Purpose: UMAP of generated molecules colored by state, overlaid with
  approved drugs. Visually compelling figure.
- Expected impact: MODERATE for scientific argument, HIGH for visual impact
  and accessibility.

### Tier 3: Enhancement / Post-Submission (Weeks 8-16+)

**Item 3.1: ChemRxiv Preprint**
- Timing: Week 6-8 (as soon as Tier 0 and Items 1.1-1.4 are complete)
- Purpose: Establish priority. progdir's scooping analysis is compelling.
- Expected impact: Priority claim. No effect on reviewability.

**Item 3.2: Survival Funnel (ADMETlab 3.0 + AiZynthFinder)**
- Effort: 1-2 weeks
- Purpose: "What fraction of top candidates pass ADMET filters and have
  retrosynthetic routes?" This adds translational relevance.
- Expected impact: MODERATE for JCIM (pharma-audience), LOW for ML venues.

**Item 3.3: Gini Selectivity Analysis with Proper Citations**
- Effort: 1-2 days (writing only)
- Purpose: Restate selectivity claim with ranges from Muller et al. (2015)
  and Davis et al. (2011) rather than unsourced point estimates.
- Expected impact: LOW-MODERATE. Fixes a citation issue.

### Tier 4: Deferred (Paper 2 / NeurIPS 2027)

**Item 4.1: 3D Baseline (DiffSBDD)**
- Rationale for deferral: associate's finding of 29 open / 0 closed issues,
  Python 3.10 requirement, and CrossDocked2020 EGFR overlap all increase the
  risk-to-benefit ratio for first submission. JCIM reviewers are unlikely to
  demand a 3D baseline. ML venues (NeurIPS 2027) will.
- I agree with progdir's recommendation to defer to revision or Paper 2.

**Item 4.2: Within-Method State Ablations (REINVENT Multi-Pocket)**
- Deferred unless REINVENT integration (Item 2.2) is completed early.

**Item 4.3: Full Multi-Kinase Generalization**
- principal's estimate of 16-22 person-weeks for full refactoring is realistic.
  Incremental ABL1 is the correct approach for Paper 1.

**Item 4.4: Benchmark Infrastructure**
- Docker containers, HuggingFace dataset, leaderboard. NeurIPS 2027 target.

---

## 4. Venue Recommendation

### 4.1 Primary: JCIM

**Estimated acceptance probability: 55-65% (conditional on Tier 0 and Item 1.1
succeeding)**

Rationale:
- JCIM publishes kinase computational chemistry papers routinely (6+ in 2026
  already, per progdir).
- The benchmark question ("does discrete state conditioning improve enrichment?")
  is squarely within scope.
- Rolling submission avoids deadline pressure; the only pressure is competitive
  timing.
- Retrospective enrichment with multi-kinase validation (EGFR + ABL1) is a
  solid contribution.
- JCIM reviewers are domain experts who will appreciate the structural biology
  nuance (4-state KLIFS model, DFGout mutant disclosure) rather than penalizing
  it.

**What would lower acceptance probability:**
- Ablation C failing (Cohen's d < 0.8): drops to 30-40% because the central
  claim becomes ambiguous.
- Structural annotation errors not fully corrected: drops to <20% (any reviewer
  checking PDB will find the 3iku error).
- MPNN random-split R^2 reported without scaffold-split comparison: drops to
  40-50% (increasingly unacceptable).

**What would raise acceptance probability:**
- ABL1 + BRAF multi-kinase validation: raises to 65-75%.
- REINVENT cross-architecture validation: raises to 70-80%.
- Pre-registration + bootstrap CIs: raises to 60-70% (baseline, without
  additional experiments).

### 4.2 Not Recommended at This Time: Nature Computational Science

**Estimated acceptance probability: 15-25% (past desk rejection)**

I agree with progdir's analysis. Nature Comp Sci requirements are:
- Multi-kinase validation across 4+ kinases (we will have 2-3).
- Cross-architecture validation (VAE + REINVENT + ideally a diffusion baseline).
- Biological insight beyond benchmarking ("conformational state labels encode
  information that pocket geometry does not" -- this is a strong claim requiring
  strong evidence).
- Publication of DiffSBDD in this venue (December 2024) sets a high bar for
  follow-up molecular design papers.

The 50-60% desk rejection rate, combined with 4-8 months total turnaround,
makes this a poor use of competitive time. I would consider submitting to
Nature Comp Sci only if:
1. ABL1 and BRAF both succeed with EF@10 > 3.0.
2. REINVENT cross-architecture validation succeeds.
3. JCIM accepts, establishing the base contribution.
4. Expanded version with 4+ kinases is prepared post-JCIM.

### 4.3 Aspirational: NeurIPS 2027 Evaluations & Datasets

**Estimated acceptance probability: 40-55% (if benchmark infrastructure is
built)**

This is the correct venue for the benchmark paper -- "ConformBench: A Benchmark
for Conformational State-Conditioned Molecular Generation." Target 5+ kinases,
3+ generation methods, Docker-reproducible, HuggingFace-hosted, Croissant
metadata. Timeline is feasible (13 months from now) post-JCIM.

### 4.4 Timeline Summary

| Milestone | Target Date | Gate |
|-----------|-------------|------|
| Tier 0 complete | April 23, 2026 | All structural fixes verified |
| Ablation C result | May 1, 2026 | Cohen's d >= 0.8 or pivot |
| ABL1 pipeline running | June 1, 2026 | EF@10 > 1.0 |
| ChemRxiv preprint | June 15, 2026 | EGFR + early ABL1 results |
| JCIM submission | August 1, 2026 | EGFR + ABL1 + (ideally BRAF) |
| JCIM first decision | September 15, 2026 | |
| JCIM acceptance | November 2026 | |
| NeurIPS 2027 preparation | January-April 2027 | |

This aligns with progdir's Scenario B (16 weeks) adjusted for the structural
audit adding 1-2 weeks at the front.

---

## 5. Overall Assessment

### 5.1 Review Score for the Proposed Plan (JCIM)

Using the standard journal review scale:

**If Tier 0 + Items 1.1-1.5 are completed as described:**

- **Novelty:** 7/10. Verified unique contribution (discrete state conditioning +
  retrospective enrichment). Not a new architecture, but a new question. The
  KLIFS-based framing is original.
- **Rigor:** 7/10 (post-fixes). The structural audit, scaffold splits, bootstrap
  CIs, and pre-registration bring rigor from ~4/10 (current state) to 7/10.
  The main weakness remains N=3-5 held-out drugs per kinase; this is inherent
  and acknowledged.
- **Significance:** 6/10. The answer to "does state conditioning help?" matters
  for the field, but the practical impact depends on whether the enrichment
  advantage is large and reproducible across kinases.
- **Reproducibility:** 8/10. 646 tests, open-source codebase, YAML configs,
  artifact-based pipeline. Strong infrastructure.
- **Presentation:** TBD (not yet written). The structural disclosure handling
  will be critical.

**Overall recommendation: Accept with minor revision (conditional on successful
ablation C and ABL1 validation).**

This corresponds to an overall score of approximately **7.0/10** -- above the
typical JCIM acceptance threshold of ~6.5 for computational drug design papers.

### 5.2 What Would Make This an 8/10 Paper

- REINVENT cross-architecture validation succeeding.
- Three kinases (EGFR + ABL1 + BRAF) all showing state-conditioning advantage.
- Survival funnel showing that state-aware candidates have higher synthesizability.
- Beautiful Figure 1 showing the conformational state landscape with UMAP-embedded
  generated molecules colored by state, overlaid with approved drug positions.

### 5.3 What Would Make This a 5/10 Paper (Major Concerns)

- Ablation C failing (state conditioning does not outperform unconditioned).
- ABL1 enrichment not replicating the EGFR result.
- Structural annotation errors not fully corrected.
- Any of these would require fundamental restructuring of the narrative.

### 5.4 Residual Concerns

1. **Small N problem.** With 3-5 held-out drugs per kinase, even with bootstrap
   CIs, the statistical power is inherently limited. The paper must acknowledge
   this honestly. The multi-kinase extension mitigates by providing independent
   replications.

2. **The "VAE is dated" perception.** SELFIES VAEs are increasingly viewed as
   superseded by diffusion models (DiffSBDD, FLOWR) and flow-matching methods
   (DynamicFlow). The paper must frame the VAE as a *probe* for the state-
   conditioning question, not as a claim of architectural innovation. "We use a
   deliberately simple architecture to isolate the effect of state conditioning"
   is a strong framing.

3. **The null retained on mean score.** Static wins 0.5437 vs 0.4378 on mean
   score. This cannot be hidden. The paper must present this honestly and explain
   it: the static pipeline optimizes for a single pocket (maximizing docking score
   against 1M17), while the state-aware pipeline distributes effort across 4
   pockets, necessarily spreading the per-pocket scores thinner. The enrichment
   metric, not mean score, is the appropriate measure of real-world utility.

4. **PocketXMol comparison.** progdir correctly identifies PocketXMol (Cell, Feb
   2026) as a medium-overlap competitor. The paper needs a clear paragraph
   explaining why discrete state labels add information beyond what 3D pocket
   geometry provides. The answer is: state labels encode *population dynamics*
   (which states are populated under specific mutations or drug resistance
   contexts) that geometry alone does not capture. A pocket geometry tells you
   what *shape* to design for; a state label tells you *which shapes matter*
   for a given clinical scenario.

---

## 6. Points of Agreement and Disagreement with Other Reviewers

### 6.1 Agreements

- **mlrev:** VAE validity metric is vacuous for SELFIES. Fully agree. FCD and
  reconstruction accuracy are the correct metrics. I endorse fcd_torch and
  #Circles.
- **mlrev:** MPNN random split is a blocking issue. Fully agree. Scaffold split
  is mandatory. I independently confirmed this assessment.
- **principal:** MPNN split confirmed at the same code location. Our findings
  are concordant.
- **principal:** Incremental ABL1 over full refactoring. Fully agree. 6-9
  person-weeks incremental vs 16-22 full. Incremental is the correct
  publication strategy.
- **associate:** DiffSBDD has significant practical barriers (29/0 issues,
  Python 3.10, GPU concerns). Agree to defer to Tier 4.
- **associate:** ADMETlab 3.0 and AiZynthFinder are both feasible and practical.
  Agree. The survival funnel is a worthwhile Tier 3 item.
- **progdir:** JCIM primary target, ChemRxiv preprint for priority, NeurIPS
  2027 for benchmark paper. Fully agree with the venue strategy.
- **progdir:** 15-20% scooping probability in 6 months. This aligns with my
  assessment of the competitive landscape.

### 6.2 Disagreements

- **mlrev on enrichment:** mlrev suggests the enrichment advantage "could be
  partially or wholly explained by the larger, more diverse candidate pool."
  I disagree with "wholly" -- the enrichment factor normalizes for pool size.
  The diversity confound is real but is not equivalent to the oracle-call
  confound. See Section 1 for my detailed reasoning.

- **mlrev on 3D baseline priority:** mlrev argues for including DiffSBDD for
  JCIM submission. I side with progdir and associate: JCIM does not require
  a 3D baseline, and the practical barriers (Python 3.10, 29 open issues,
  CrossDocked2020 overlap) make this a poor ROI for first submission. Include
  if time permits; do not make it a blocker.

- **progdir on 4ZAU handling:** progdir suggests "plan for 3 states, use 4 only
  if 4ZAU confirmed DFGout." I partially disagree -- the plan should be
  "verify 4ZAU first (1-2 hours), then decide." Making a decision before
  inspection invites confirmation bias.

---

## 7. References

1. Muller, S. et al. "Conformational Analysis of the DFG-Out Kinase Motif and
   Biochemical Profiling of Structurally Validated Type II Inhibitors." J. Med.
   Chem. 58, 1610-1629 (2015). PMC4326797.

2. Davis, M.I. et al. "Comprehensive analysis of kinase inhibitor selectivity."
   Nat. Biotechnol. 29, 1046-1051 (2011).

3. Kooistra, A.J. et al. "KLIFS: an overhaul after the first 5 years of
   supporting kinase research." Nucleic Acids Res. 49, D562-D569 (2021).

4. Ung, P.M.U. & Schlessinger, A. "DFGmodel: Predicting Protein Kinase
   Structures in Inactive States for Structure-Based Discovery of Type-II
   Inhibitors." ACS Chem. Biol. 10, 269-278 (2015).

5. Shan, Y. et al. "Transitions to catalytically inactive conformations in
   EGFR kinase." PNAS 110, 7270-7275 (2013).

6. Soria, J.C. et al. "Osimertinib in Untreated EGFR-Mutated Advanced
   Non-Small-Cell Lung Cancer." N. Engl. J. Med. 378, 113-125 (2018).

7. Sequist, L.V. et al. "Genotypic and Histological Evolution of Lung Cancers
   Acquiring Resistance to EGFR Inhibitors." Sci. Transl. Med. 3, 75ra26 (2011).

8. Yosaatmadja, Y. et al. "Binding mode of the breakthrough inhibitor AZD9291
   to epidermal growth factor receptor revealed." J. Struct. Biol. 192, 539-544
   (2015). PDB: 4ZAU.

9. Sogabe, S. et al. "Structure-Based Approach for the Discovery of
   Pyrrolo[3,2-d]pyrimidine-Based EGFR T790M/L858R Mutant Inhibitors." J. Med.
   Chem. 56, 7924-7940 (2013). PDB: 3W2R.

10. Gao, W. et al. "Sample Efficiency Matters: A Benchmark for Practical
    Molecular Optimization." NeurIPS 35 (2022).

11. Preuer, K. et al. "Frechet ChemNet Distance: A Metric for Generative Models
    for Molecules in Drug Discovery." JCIM 58, 1736-1741 (2018).

12. Blaschke, T. et al. "Diverse Hits in De Novo Molecule Design: Diversity-Based
    Comparison of Goal-Directed Generators." JCIM (2024). DOI: 10.1021/acs.jcim.4c00519.

13. Yang, K. et al. "Analyzing Learned Molecular Representations for Property
    Prediction." JCIM 59, 3370-3388 (2019).

14. Heid, E. et al. "A systematic study of key elements underlying molecular
    property prediction." Nat. Commun. (2024).

15. Sutto, L. & Gervasio, F.L. "Effects of oncogenic mutations on the
    conformational free-energy landscape of EGFR kinase." PNAS 110, 10616-10621
    (2013).

16. Modi, V. & Bhatt, R. "Pockets as structural descriptors of EGFR kinase
    conformations." PLOS ONE 12, e0189147 (2017).

17. Schneuing, A. et al. "Structure-based drug design with equivariant diffusion
    models." Nat. Comput. Sci. 4, 899-909 (2024). (DiffSBDD)

18. Lu, W. et al. "DynamicBind: predicting ligand-specific protein-ligand complex
    structure with a deep equivariant generative model." Nat. Commun. 15, 1071
    (2024).

19. Loeffler, H.H. et al. "REINVENT 4: Modern AI-Driven Generative Molecule
    Design." J. Cheminform. (2024).

20. Yun, C.H. et al. "The T790M mutation in EGFR kinase causes drug resistance
    by increasing the affinity for ATP." PNAS 105, 2070-2075 (2008). PDB: 3IKA.

21. Cheng, H. et al. "Discovery of PF-06459988, a Potent, WT Sparing,
    Irreversible Inhibitor of T790M-Containing EGFR Mutants." J. Med. Chem. 59,
    2005-2024 (2016). PDBs: 5HG5, 5HG7, 5HG8, 5HG9.
