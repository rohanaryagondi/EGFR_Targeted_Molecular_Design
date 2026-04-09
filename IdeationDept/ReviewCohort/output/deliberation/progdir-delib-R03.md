---
agent: Program Director / Chief Scientist
round: 3
date: 2026-04-09
type: review-assessment
scope: deliberation
---

# Program Director Deliberation: Final Strategic Recommendation

## Executive Summary

After three rounds of review, verification, and deliberation across five expert
reviewers, the project picture is materially different from where the ideation
cohorts left it. The structural annotation errors (CF1) are serious but bounded.
The MPNN random split (CF2) and compute-unfair comparison (CF3) are embarrassing
but fixable in days. The novelty is definitively verified by 70+ combined
searches across two reviewers. The competitive window remains open with low
near-term scooping risk (15-20% at 6 months).

**My final call: Scenario B-revised at 18 weeks to JCIM submission (target:
mid-August 2026), with a ChemRxiv preprint at week 8-10 AFTER structural fixes
are complete. No preprint with known structural errors.** The original 16-week
Scenario B assumed structural fixes were trivial; they are not. Adding 2 weeks
for the structural cascade is cheaper than rushing a preprint that gets
retracted.

**Project viability: 7.5/10.** Strong enough to ship. Not without risk. The
structural issue downgrades this from the 8.5 I would have given pre-CF1, but
the fix path is clear and bounded.

---

## 1. Revised Timeline: 18 Weeks to JCIM Submission

### Why 18 Weeks, Not 16

The Round 2 structural annotation discovery (CF1) adds genuine work that was not
in my original Scenario B estimate:

| New Item | Effort | Why It Was Not In Scenario B |
|----------|--------|------------------------------|
| 4ZAU DFG 3D coordinate inspection | 2-4 hours | Not known to be needed |
| Fix 3W2R/5D41 mutation annotations | 1-2 days | Assumed correct |
| Fix 3iku PDB ID (likely 3IKA) | 1-2 hours | Assumed correct |
| Assess 3-state vs 4-state decision | 1-2 days | Not anticipated |
| Re-compute pocket descriptors if needed | 2-3 days | Depends on above |
| Re-run GNINA docking if pocket changes | 3-5 days | Conditional |
| Re-check VAE state labels | 1 day | Depends on 3-state decision |
| Rewrite conformational atlas narrative | 1-2 days | Writing |
| MPNN scaffold + temporal split | 2-3 days | Not known to be random |
| Compute-matched comparison (PMO-style) | 5-7 days | Not identified in R1 |
| Replace VAE validity with FCD etc. | 3-5 days | Not identified in R1 |

**Total new work: approximately 3-4 weeks of effort.** However, some of this
parallelizes with existing Scenario B work (the scaffold split can run while
kinase data is being curated; the compute-matched comparison can run while
REINVENT is being set up). Net timeline impact: +2 weeks.

### The 3-State vs 4-State Decision Is Quick

I agree with the Round 2 synthesis: the 4ZAU DFG conformation check is a 2-4
hour task. Inspect three distances in PyMOL/ChimeraX:

1. DFG Asp831-Phe832 chi1 torsion (DFGin: chi1 ~-60deg; DFGout: chi1 ~180deg)
2. Phe832 position relative to ATP site (DFGin: under P-loop; DFGout: flipped)
3. K745-E762 salt bridge distance (aC-in: <4A; aC-out: >6A)

If 4ZAU is DFGin (likely, given osimertinib is Type I covalent), the decision is
forced: adopt a 3-state model (DFGin/aCin, DFGin/aCout, DFGout/aCin) with
mutant structures disclosed for DFGout. This is scientifically honest and does
not invalidate the paper. The key claim becomes: "State-conditioning improves
enrichment even when DFGout structures are mutant-derived, and even with 3
states rather than 4."

This decision adds 1-2 days, not weeks. It does not delay the critical path.

### Revised Week-by-Week Milestone Table

| Week | Phase | Milestones | GO/NO-GO |
|------|-------|-----------|----------|
| **0** | Setup | Read all Round 2/3 output. Create tracking spreadsheet. | -- |
| **1** | Tier 0 Fixes | 4ZAU coordinate check. Fix 3W2R/5D41/3iku annotations. 3-state vs 4-state decision. Fix osimertinib reference leak. | GATE 0: Structural atlas verified |
| **2** | Tier 0 Fixes | MPNN scaffold+temporal split. Re-evaluate R^2. Bootstrap CIs + BEDROC on existing EGFR results. Pre-registration document (git commit timestamp). | GATE 1: MPNN scaffold R^2 >= 0.35 |
| **3** | Tier 0 Continued | Pocket descriptor re-computation (if needed). Re-run GNINA docking (if pocket descriptors changed). Replace VAE validity metric with FCD + reconstruction + novelty. | -- |
| **4** | Critical Path | Ablation C: unconditioned VAE on EGFR. Begin multi-kinase codebase extension (ABL1 incremental). | GATE 2: Ablation C Cohen's d >= 0.5 |
| **5** | Critical Path | Ablation C results analyzed. REINVENT 4 setup + custom GNINA plugin (begin). Continue ABL1 codebase work. | -- |
| **6** | Critical Path | ABL1 data curation (ChEMBL, KLIFS, PDB structures). ABL1 model training (VAE + MPNN). REINVENT 4 GNINA integration complete. | -- |
| **7** | Critical Path | ABL1 pipeline execution. REINVENT 4 baseline on EGFR. Compute-matched PMO comparison (EGFR). | GATE 3: REINVENT 4 produces valid docked molecules |
| **8** | Multi-Kinase | ABL1 retrospective enrichment + bootstrap CIs. Begin BRAF data curation. Ablation E, F, G on EGFR. | GATE 4: ABL1 enrichment > 1.0 (positive signal) |
| **8-10** | **ChemRxiv** | **Write and submit ChemRxiv preprint** (EGFR fixed + Ablation C + ABL1 preliminary + scaffold split + CIs). | Preprint submitted |
| **9** | Multi-Kinase | BRAF data curation + model training. Conformal prediction via TorchCP. | -- |
| **10** | Multi-Kinase | BRAF pipeline execution + retrospective enrichment. Scoring sensitivity (Dirichlet 1000+). 3-component fairness check. | -- |
| **11** | Analysis | Chemical space UMAP + property distributions. FCD scores. PMO compute-matched results finalized. Conformational selection narrative (writing). | -- |
| **12** | Analysis | Gini selectivity analysis (with proper citations). Cross-kinase consistency analysis. Final figure generation. | GATE 5: >= 2/3 kinases show enrichment advantage |
| **13-14** | Writing | Full manuscript draft. Methods, Results, Discussion. Supplementary materials. | -- |
| **15-16** | Writing | Internal review. Revisions. Co-author feedback. | -- |
| **17** | Polish | Final figures. Supplementary tables. Code repository cleanup. Data availability statement. | -- |
| **18** | Submit | **JCIM submission** (target: mid-August 2026). | SUBMITTED |

### ChemRxiv Preprint Timing: Week 8-10

This is delayed 2 weeks from my Round 2 recommendation (originally week 6-8).
The reason: structural fixes must be fully resolved before any public document.
A preprint with known mutant-as-WT errors would be career-damaging if discovered.
The 2-week delay is a small price for credibility. See Section 6 for full
preprint strategy.

---

## 2. Scope Decision: IN vs OUT

### DEFINITIVELY IN (JCIM Submission)

These items are mandatory. The paper is not submittable without them.

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| 1 | Structural atlas correction (3W2R, 5D41, 3iku, 4ZAU) | 1-2 weeks | Publication-blocking. Undisclosed errors = retraction. |
| 2 | 3-state vs 4-state decision + disclosure | 1-2 days | Defines the entire experimental framework. |
| 3 | Osimertinib reference leak fix | Hours | Publication-blocking. Data contamination. |
| 4 | MPNN scaffold + temporal split | 2-3 days | Publication-blocking. Random split R^2 is indefensible. |
| 5 | Bootstrap CIs + BEDROC | 2-3 days | Publication-blocking. No CIs = no statistics. |
| 6 | Ablation C (unconditioned VAE) | 1-2 weeks | Thesis-critical. GO/NO-GO for the entire paper. |
| 7 | REINVENT 4 baseline on EGFR | 8-15 days | Minimum external baseline for JCIM. |
| 8 | ABL1 full pipeline + enrichment | 6-9 weeks | Minimum multi-kinase for "generalizability" claim. |
| 9 | BRAF full pipeline + enrichment | 4-6 weeks | Third kinase makes the pattern convincing. |
| 10 | Compute-matched PMO comparison | 5-7 days | Compute fairness is mandatory since PMO (2022). |
| 11 | Replace VAE validity with FCD + reconstruction | 3-5 days | 99.9% SELFIES validity is misleading. Easy fix. |
| 12 | 3-component scoring fairness check | 2-3 days | Must show enrichment survives without state_specificity. |
| 13 | Dirichlet scoring sensitivity (1000+) | 3-5 days | Shows enrichment is robust to weight perturbation. |
| 14 | Chemical space UMAP + property distributions | 3-5 days | Standard in 2026 molecular generation papers. |
| 15 | Conformational selection narrative | 0 (writing) | Zero-cost differentiation. |
| 16 | Pre-registration document | Hours | Timestamped git commit. Differentiating. |

### PROBABLY IN (Include If Time Permits)

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| 17 | Conformal prediction (TorchCP) | 5-7 days | Expected at JCIM in 2026. Strong signal of rigor. |
| 18 | Ablations E, F, G on EGFR | 1-2 weeks | Strengthen the ablation story but C is sufficient for GO/NO-GO. |
| 19 | REINVENT 4 on ABL1 | 3-5 days | Incremental effort once EGFR integration works. |
| 20 | Gini selectivity analysis | 2-3 days | Adds pharmacological context. Need proper citations. |

### DEFINITIVELY OUT (Deferred to Revision or Paper 2)

| # | Item | Effort | Rationale |
|---|------|--------|-----------|
| 21 | 3D baseline (DiffSBDD) | 2-3 weeks | Python 3.10, unmaintained, CrossDocked overlap. Low ROI for JCIM. JCIM will not demand this; NeurIPS would. |
| 22 | MET as fourth kinase | 4-6 weeks | Contingent on data quality. Three kinases is sufficient for JCIM. Add in revision if requested. |
| 23 | Within-method REINVENT ablation (4-pocket vs 1-pocket) | 2-3 weeks | Important for Nature Comp Sci, not needed for JCIM. Paper 2 material. |
| 24 | Survival funnel (ADMETlab + AiZynthFinder) | 1-2 weeks | Nice supplementary. Not required for the core claim. |
| 25 | GIST water analysis | 2-3 weeks | CompBioRev wants it; I respect the suggestion but it is enhancement, not core. |
| 26 | Benchmark infrastructure (Docker, leaderboard) | 4-6 weeks | NeurIPS 2027 E&D target. |
| 27 | OpenFE FEP validation | 4-8 weeks | Paper 2 or beyond. |
| 28 | Full multi-kinase generalization | 16-22 weeks | Way too much scope. Incremental is sufficient. |

### Scope Rationale

I am cutting ruthlessly because scope creep kills papers. The IN list already
totals roughly 16-18 weeks of work for a single researcher. Adding DiffSBDD, MET,
GIST, and within-method ablations would push this to 28+ weeks and we would be
writing in November with a 30-40% scooping probability.

The core scientific contribution is: "Discrete conformational state labels
improve retrospective enrichment for kinase inhibitor generation, demonstrated
across 3 kinases with ablation-controlled evidence." Everything in the IN list
directly supports this claim. Everything in the OUT list is supplementary or
targets a different venue.

---

## 3. Priority Ordering with Expected Value

Expected Value = (Impact * P(Success)) / Effort

Impact: 1-10 (contribution to publishability)
P(Success): 0-1 (probability of completing successfully)
Effort: person-weeks

| Priority | Item | Impact | P(Success) | Effort (wks) | EV | Notes |
|----------|------|--------|------------|--------------|-----|-------|
| **P0** | Structural atlas fix | 10 | 0.95 | 1.5 | 6.33 | Blocking. No paper without it. |
| **P1** | MPNN scaffold split | 9 | 0.99 | 0.5 | 17.82 | Highest EV. Trivial effort, blocks all ML claims. |
| **P2** | Osimertinib fix | 9 | 0.99 | 0.1 | 89.10 | Highest raw EV. Hours of work. |
| **P3** | Bootstrap CIs + BEDROC | 9 | 0.95 | 0.5 | 17.10 | No stats = no publication. |
| **P4** | Pre-registration document | 7 | 1.00 | 0.1 | 70.00 | Free differentiation. |
| **P5** | Ablation C (unconditioned VAE) | 10 | 0.80 | 1.5 | 5.33 | GO/NO-GO. Highest strategic impact. |
| **P6** | Compute-matched PMO comparison | 8 | 0.90 | 1.0 | 7.20 | Blocks any ML venue reviewer. |
| **P7** | Replace VAE validity metric | 6 | 0.95 | 0.7 | 8.14 | Easy win. Removes obvious weakness. |
| **P8** | ABL1 incremental extension | 9 | 0.85 | 7.0 | 1.09 | Critical path bottleneck. Low EV per week but mandatory. |
| **P9** | REINVENT 4 baseline | 8 | 0.75 | 2.0 | 3.00 | External baseline. Integration risk is real. |
| **P10** | BRAF pipeline | 8 | 0.80 | 5.0 | 1.28 | Third kinase. Adds conviction. |
| **P11** | 3-component scoring check | 7 | 0.95 | 0.5 | 13.30 | Quick analysis. Defuses kill shot 3. |
| **P12** | Dirichlet sensitivity | 6 | 0.95 | 0.7 | 8.14 | Supplementary defense. |
| **P13** | UMAP + property distributions | 6 | 0.95 | 0.7 | 8.14 | Expected in 2026 papers. |
| **P14** | Conformational narrative | 5 | 1.00 | 0.3 | 16.67 | Zero compute. Pure writing value. |
| **P15** | Conformal prediction (TorchCP) | 5 | 0.85 | 1.0 | 4.25 | Increasingly expected. Good signal. |
| **P16** | Ablations E, F, G | 6 | 0.85 | 1.5 | 3.40 | Strengthens ablation story. |

**Execution order** follows dependency, not raw EV:

1. P0 -> P1 -> P2 -> P3 -> P4 (all Tier 0, weeks 1-2, strict sequence)
2. P5 (week 4-5, blocks narrative direction)
3. P6 + P7 in parallel (weeks 3-5)
4. P8 (weeks 4-10, critical path, runs in background)
5. P9 (weeks 5-7, parallel with P8)
6. P10 (weeks 9-11, after P8 proves the incremental approach works)
7. P11 + P12 + P13 + P14 in parallel (weeks 10-12, analysis phase)
8. P15 + P16 if time allows (weeks 10-12)

---

## 4. Go/No-Go Gates

### GATE 0: Structural Atlas Verified (End of Week 1)
- **Criterion:** All PDB IDs verified against PDB/KLIFS. Mutation status
  corrected. 4ZAU DFG conformation determined. 3-state vs 4-state decision made.
- **GO:** Proceed with corrected atlas. Disclose mutant structure usage.
- **NO-GO condition:** A fundamental problem that makes the state classification
  scheme invalid (e.g., all DFGout structures are actually DFGin). This would
  require a complete rethinking of the project.
- **Probability of NO-GO:** <5%. The structural issues are annotation errors,
  not conceptual failures. DFGout as a conformational state is well-established
  in kinase biology.

### GATE 1: MPNN Scaffold Split Performance (End of Week 2)
- **Criterion:** MPNN retrained with Bemis-Murcko scaffold split. Test set R^2
  reported.
- **GO:** Scaffold R^2 >= 0.35 (indicating the model learns something beyond
  scaffold memorization).
- **CONDITIONAL GO:** Scaffold R^2 in [0.20, 0.35]. Report honestly, frame MPNN
  as "supplementary scoring signal" rather than primary predictor, emphasize that
  GNINA (physics-based) is the dominant scoring component.
- **NO-GO:** Scaffold R^2 < 0.20. Drop MPNN from scoring entirely. Re-score all
  candidates with 3-component function (GNINA + descriptors + state_specificity).
  This changes the narrative but does not kill the paper -- the enrichment
  comparison uses primarily docking scores anyway.
- **Probability of NO-GO:** ~10%. Published D-MPNN benchmarks on binding
  affinity typically report scaffold-split R^2 of 0.35-0.55 (Yang et al., 2019).
  StateBind's curated dataset is small (~90 compounds), which hurts scaffold
  splits disproportionately.

### GATE 2: Ablation C Result (End of Week 5)
- **Criterion:** Unconditioned VAE (same architecture, no state labels) evaluated
  on EGFR retrospective enrichment with bootstrap CIs.
- **GO:** Cohen's d >= 0.5 between conditioned and unconditioned enrichment
  (practical significance). Ideally d >= 0.8 (large effect).
- **PIVOT:** Cohen's d < 0.5 but conditioned is numerically superior. Paper
  pivots to "diversity-driven generation outperforms template-based design."
  Still publishable at JCIM but different thesis.
- **NO-GO:** Unconditioned VAE matches or exceeds conditioned VAE on enrichment.
  State information provides no value. Paper becomes "negative result: discrete
  state labels do not improve molecular generation for kinases." Publishable at
  JCIM (negative results are valuable) but requires complete narrative rewrite.
- **Probability of NO-GO:** ~20%. This is the highest-risk gate. The 10x
  enrichment headline result might be driven by the VAE's diversity rather than
  state conditioning. However, the pipeline also includes state-specific docking
  (GNINA against 4 pockets) which is orthogonal to the VAE's generative behavior.
  Even if the VAE's state conditioning provides no benefit, the docking cascade
  should still show state-dependent ranking effects.

### GATE 3: REINVENT 4 Integration (End of Week 7)
- **Criterion:** REINVENT 4 produces valid molecules docked against EGFR with
  GNINA scoring via the custom plugin.
- **GO:** REINVENT produces 100+ valid docked molecules with GNINA scores.
- **CONDITIONAL GO:** Integration works but is slow (>10 min/molecule). Reduce
  the number of REINVENT-generated candidates but still include the baseline.
- **NO-GO:** GNINA plugin fails despite 2 weeks of effort. Fall back to
  REINVENT with Vina scoring (less directly comparable but still a valid external
  baseline). Report the scoring difference in methods.
- **Probability of NO-GO:** ~15%. The ExternalProcess component in REINVENT 4
  is designed for exactly this use case, but GNINA command-line integration has
  not been validated by anyone else. DockStream (REINVENT's docking wrapper) is
  archived and does not support GNINA, so this is custom work.

### GATE 4: ABL1 Enrichment Signal (End of Week 8)
- **Criterion:** ABL1 state-aware pipeline produces enrichment factor > 1.0
  (better than random) on held-out approved drugs.
- **GO:** EF@10 > 1.0 with overlapping CIs with EGFR result direction.
- **CONDITIONAL GO:** ABL1 shows positive direction but wide CIs due to few
  approved drugs. Report honestly with uncertainty. Two kinases showing same
  direction (even with wide CIs) is more convincing than one kinase with tight CIs.
- **NO-GO:** ABL1 enrichment < 1.0 (worse than random). Investigate why. If the
  ABL1 data is lower quality, disclose this. If ABL1 genuinely shows no state
  effect, this is an important negative result. Report it and proceed with
  BRAF as the critical second kinase.
- **Probability of NO-GO:** ~25%. ABL1 has excellent DFGout data (imatinib-bound
  structures), but the retrospective evaluation depends on having enough approved
  drugs with known binding modes. ABL1 has imatinib, dasatinib, nilotinib,
  bosutinib, ponatinib -- a reasonable held-out set. The risk is that ABL1's
  strong DFGout preference makes the "state-aware vs static" comparison less
  dramatic (static on the active state might already be good for ABL1).

### GATE 5: Cross-Kinase Consistency (End of Week 12)
- **Criterion:** At least 2 of 3 kinases (EGFR, ABL1, BRAF) show enrichment
  advantage for state-aware over static.
- **GO:** 2/3 or 3/3 kinases show positive enrichment advantage with overlapping
  CI directions. Paper writes itself.
- **CONDITIONAL GO:** Only 1/3 shows strong advantage but the negative results
  are informative (e.g., ABL1 shows no advantage because it is dominated by a
  single DFGout state). Report the mixed picture honestly. Publishable at JCIM
  as "state-conditioning helps for X but not Y, here is why."
- **NO-GO:** 0/3 kinases show state-aware enrichment advantage. Kill the paper
  as currently conceived. Pivot to negative result: "Discrete state labels do
  not consistently improve molecular generation across kinases." Still
  publishable at JCIM.
- **Probability of NO-GO:** ~10%. The EGFR enrichment advantage is 10x. Even
  with structural corrections and proper CIs, a complete collapse to zero
  advantage is unlikely. The question is whether ABL1 and BRAF replicate the
  direction.

---

## 5. Responses to Other Reviewers

### CompBioRev (Structural Annotations)

CompBioRev's structural findings are the most important discovery in this review
process. I fully agree that this is publication-blocking and must be resolved
first. However, I want to push back on one point: CompBioRev suggests this "may
fundamentally undermine the project." I disagree. The errors are annotation
errors, not conceptual failures.

The key insight: no WT EGFR DFGout crystal structure exists. This is a fact
about structural biology, not a flaw in the project design. The correct response
is disclosure and control, not abandonment. Every kinase conformational study
that uses DFGout structures (including KLIFS itself) implicitly uses mutant
structures for targets where WT DFGout has not been crystallized. This is
standard practice. The error was in not disclosing it, not in using mutant
structures.

The 3-state model (dropping DFGout/aCout if 4ZAU is DFGin) is cleaner than
trying to defend a questionable 4th state. Three well-characterized states are
stronger than four states where one is dubious.

### MLRev (Compute Fairness)

MLRev is correct that the 30 vs 461 comparison is indefensible at any ML venue.
I add it to the IN list (P6). The PMO-style fixed oracle call budget is the
right approach. However, I want to emphasize: the retrospective enrichment
metric (which uses held-out drugs, not generated candidates) is naturally
compute-agnostic. The enrichment factor asks "of the top-ranked molecules, how
many are approved drugs?" -- this does not directly depend on how many molecules
were generated. The compute-matched comparison is needed for the head-to-head
mean score comparison, but the retrospective enrichment result may be robust to
candidate pool size. This should be tested empirically.

### MLRev (3D Baseline for JCIM)

I maintain my Round 2 position: DiffSBDD is OUT for the initial JCIM submission.
The argument for including it rests on the assumption that JCIM reviewers will
demand a 3D structure-based baseline. Based on my experience reviewing for JCIM,
they will not. JCIM reviewers will want: (1) an external baseline that uses the
same scoring function (REINVENT satisfies this), (2) ablation evidence that state
information matters (Ablation C), and (3) statistical rigor (CIs, BEDROC). A 3D
baseline is expected at NeurIPS/ICML, not at JCIM. If a JCIM reviewer requests
it, it can be added in revision (the deferred DiffSBDD setup). The risk of
including it now is 2-3 weeks of effort on an unmaintained codebase that may not
work at all (29 open issues, 0 closed).

### Principal (Incremental ABL1)

Fully agree with the incremental approach. 6-9 weeks beats 16-22 weeks. The
full multi-kinase generalization is Paper 2 infrastructure. For the JCIM paper,
ABL1 added alongside EGFR with backward-compatible defaults is the right
architecture. BRAF follows the same pattern. This technical debt is acceptable
for a first paper.

### Associate (Tool Verification)

Associate's practical findings on DiffSBDD (problematic), ADMETlab (confirmed),
and AiZynthFinder (confirmed) are directly actionable. The DiffSBDD finding
reinforces my decision to defer the 3D baseline. ADMETlab and AiZynthFinder are
useful for a supplementary "survival funnel" but are OUT of scope for the initial
submission.

---

## 6. Preprint Strategy: Final Call

### Decision: ChemRxiv preprint at week 8-10, AFTER structural fixes.

Three options were considered:

**Option A: Preprint with known limitations and forthcoming corrections.**
REJECTED. A preprint stating "we know our structures are wrong but here are
results anyway" is worse than no preprint. It invites immediate criticism
and establishes a damaged first impression that persists. In the era of
Twitter/X-driven science commentary, a flawed preprint can define a project's
reputation permanently.

**Option B: Wait until structural issues are fully resolved.**
ACCEPTED. By week 8-10, the structural atlas will be corrected, the MPNN will
have scaffold-split R^2, CIs will be computed, and Ablation C results will be
in hand. This is credible preprint material:

- EGFR enrichment with corrected structures + bootstrap CIs
- Ablation C result (state-conditioned vs unconditioned VAE)
- Scaffold-split MPNN R^2 (honest reporting)
- Preliminary ABL1 enrichment (even partial results)
- Compute-matched comparison on EGFR
- Clear roadmap: "Full 3-kinase paper forthcoming"

**Option C: Delay preprint until full paper is ready.**
REJECTED. This sacrifices the priority-establishing function of a preprint.
The whole point is to plant the flag before the full paper is polished. Waiting
until week 18 means the preprint adds no priority value over the journal
submission itself.

### Preprint Minimum Content Checklist

- [ ] Structural atlas corrected and disclosed
- [ ] EGFR retrospective enrichment with BCa bootstrap CIs + BEDROC
- [ ] Ablation C result with effect size
- [ ] MPNN scaffold-split R^2 (both splits reported)
- [ ] Compute-matched comparison (PMO-style) on EGFR
- [ ] At least preliminary ABL1 result (even one kinase adds credibility)
- [ ] FCD scores replacing validity as quality metric
- [ ] Statement: "Full multi-kinase paper with external baselines in preparation"

### Preprint Venue

ChemRxiv, not bioRxiv. The JCIM reviewer pool reads ChemRxiv. The drug design
community indexes ChemRxiv. ACS explicitly permits preprinted manuscripts for
JCIM submission. No conflict.

---

## 7. Project Viability Assessment: 7.5/10

### Scoring Breakdown

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Novelty | 9/10 | Definitively verified by 70+ searches. No competitor in this exact space. |
| Scientific rigor (current) | 4/10 | Structural errors, random splits, misleading metrics, compute unfairness. |
| Scientific rigor (after fixes) | 7/10 | All issues are fixable in bounded time. |
| Feasibility | 7/10 | Yale Bouchet HPC is well-equipped. Incremental approach is practical. Main risk: REINVENT integration. |
| Impact | 7/10 | JCIM publication would be solid. Not a paradigm shift but a useful benchmark contribution. |
| Competitive timing | 7/10 | 15-20% scooping risk at 6 months is manageable. Preprint at week 8-10 reduces this further. |
| Team capacity | 6/10 | Single researcher. 18 weeks is tight. No buffer for unexpected problems. |
| Data quality | 6/10 | Structural annotation errors dent confidence. Small retrospective drug sets (~5-10 per kinase). |

**Composite: 7.5/10** -- strong enough to pursue with discipline, not strong
enough to be complacent about execution.

### What Would Move This to 8.5+

- Ablation C showing Cohen's d >= 0.8 (large effect of state conditioning)
- ABL1 enrichment replicating EGFR direction
- MPNN scaffold-split R^2 >= 0.45 (not catastrophic)
- REINVENT 4 integration working without major hacks

### What Would Drop This to 5.0 (Pivot Territory)

- Ablation C showing Cohen's d < 0.3 (state conditioning provides no benefit)
- MPNN scaffold-split R^2 < 0.15 (model learns nothing)
- 4ZAU being DFGin AND no other DFGout state representative findable (reduces to
  2 states, which is too few for "multi-state conditioning")
- ABL1 AND BRAF both showing no enrichment advantage

---

## 8. Final Strategic Recommendation

### The Paper in One Sentence

"Discrete conformational state labels improve retrospective enrichment for kinase
inhibitor molecular generation, validated across three kinases with
ablation-controlled evidence and compute-matched external baselines."

### The Publication Path

1. **Weeks 1-3:** Fix everything. Structural atlas, MPNN split, osimertinib leak,
   CIs, pre-registration. This is the foundation. No experiments until the
   foundation is solid.

2. **Weeks 4-7:** Core experiments. Ablation C (GO/NO-GO). REINVENT 4 baseline.
   ABL1 pipeline. Compute-matched comparison. These four items determine whether
   the paper exists.

3. **Weeks 8-10:** ChemRxiv preprint + BRAF execution. Plant the flag. Continue
   multi-kinase work.

4. **Weeks 11-12:** Analysis and supplementary experiments. UMAP, scoring
   sensitivity, conformal prediction if time.

5. **Weeks 13-18:** Write, polish, submit to JCIM.

### Three Things I Would Tell the Researcher

1. **Do not touch DiffSBDD, MET, GIST, or benchmark infrastructure until the
   JCIM paper is submitted.** These are all post-submission items. Every hour
   spent on them is an hour not spent on the three things that matter: fixing the
   foundation, running the ablation, and extending to ABL1/BRAF.

2. **The structural fix is your first priority, not your first annoyance.** It
   is tempting to treat CF1 as a bureaucratic obstacle and rush past it to "real"
   experiments. Do not. The fix gives you confidence in every downstream result.
   And it gives you an honest narrative: "We discovered annotation errors during
   our review process, corrected them, and re-evaluated our claims. Our results
   hold." This is a strength, not a weakness.

3. **Ablation C is the most important experiment you will run.** If state
   conditioning provides a large effect (d >= 0.8), you have a strong paper. If
   it provides a moderate effect (d >= 0.5), you have a publishable paper. If it
   provides no effect, you have a different but still publishable paper (negative
   result). In all cases, you need to know the answer before investing 12 more
   weeks. Run it in week 4 and let the result guide everything that follows.

### What NOT to Do

- Do not submit to Nature Comp Sci directly. The desk rejection probability is
  50-70% and the turnaround cost is 2-4 months. Submit to JCIM and upgrade later
  if the within-method ablations across architectures succeed.
- Do not attempt NeurIPS 2026 E&D. The deadline is May 6 (27 days). Impossible.
- Do not add a fourth kinase (MET) to the initial submission. Three kinases is
  the sweet spot for JCIM. Four kinases adds 4-6 weeks for marginal benefit.
- Do not spend more than 2 weeks on REINVENT 4 integration. If it does not work
  by week 7, fall back to REINVENT with Vina scoring. An imperfect baseline is
  better than no baseline and a 3-week delay.
- Do not publish a preprint before the structural atlas is corrected.

---

## References

1. Gao, W. et al. Sample efficiency matters: a benchmark for practical molecular
   optimization. *Proc. NeurIPS 35*, 21342-21357 (2022). [PMO benchmark]

2. Lu, W. et al. DynamicBind: predicting ligand-specific protein-ligand complex
   structure with a deep equivariant generative model. *Nat. Commun.* 15, 1071
   (2024).

3. Schneuing, A. et al. Structure-based drug design with equivariant diffusion
   models. *Nat. Comput. Sci.* 4, 899-909 (2024). [DiffSBDD]

4. PocketXMol: Unified modeling of 3D molecular generation via atomic
   interactions. *Cell* (2026).

5. Yang, K. et al. Analyzing learned molecular representations for property
   prediction. *J. Chem. Inf. Model.* 59(8), 3370-3388 (2019). [D-MPNN]

6. Krenn, M. et al. Self-referencing embedded strings (SELFIES): A 100% robust
   molecular string representation. *Mach. Learn.: Sci. Technol.* 1(4), 045024
   (2020).

7. Loeffler, H. H. et al. REINVENT 4: Modern AI-driven generative molecule
   design. *J. Cheminform.* 16, 20 (2024).

8. Huang, J. et al. TorchCP: A library for conformal prediction based on
   PyTorch. *JMLR* 26, 1-7 (2024).

9. Muller, S. et al. The ins and outs of selective kinase inhibitor development.
   *Nat. Chem. Biol.* 11(11), 818-821 (2015).

10. Anishchenko, I. et al. Modeling protein-small molecule conformational
    ensembles with PLACER. *PNAS* 122(45), e2427161122 (2025).

11. Volkamer, A. et al. A comprehensive exploration of the druggable
    conformational space of protein kinases using AI-predicted structures. *PLoS
    Comput. Biol.* (2024).

12. Francoeur, P. G. et al. Three-dimensional convolutional neural networks and
    a cross-docked data set for structure-based drug design. *J. Chem. Inf.
    Model.* 60(9), 4200-4215 (2020). [CrossDocked2020]
