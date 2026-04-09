---
agent: Orchestrator (Panel Chair)
round: 1
date: 2026-04-09
type: roundtable
scope: synthesis
---

# Round 1 Synthesis: Independent Review Consolidation

## Process

Five reviewers independently assessed both cohorts' research agendas, all 10 proposals,
and conducted deep internet research (250+ web searches total, 110+ citations across
all reviews). Three reviewers (principal, associate, mlrev) also read the StateBind
codebase directly. This synthesis identifies consensus, disagreements, and claims
requiring independent verification in Round 2.

---

## Areas of Consensus (4/5+ Reviewers Agree)

### C1: One-Paper Strategy, JCIM Primary Venue
**Reviewers:** compbiorev, mlrev, progdir, principal (associate did not take position)

All four reviewers who addressed venue strategy recommend a single paper targeting
JCIM as the primary venue. Nature Comp Sci is an aspirational stretch only, contingent
on within-method state ablation results. The benchmark paper (bencharch-P01) is deferred
to NeurIPS 2027 E&D. Reasoning:
- Nature Comp Sci desk rejection risk: 60-70% for this scope
- StateBind's contribution is a benchmark question, not a novel architecture
- The benchmark paper blocks on Paper 1 results
- Time-to-first-publication is paramount given competitive landscape

### C2: Novelty Is Verified but Must Be Narrowly Scoped
**Reviewers:** All 5

No published paper explicitly conditions molecular generation on discrete conformational
state labels (DFG/aC classifications) and benchmarks retrospective enrichment.
DynamicBind, Apo2Mol, DynamicFlow, FLOWR, and PLACER all handle conformational
flexibility through different mechanisms (learned dynamics, apo-holo transitions, MD
trajectories) but none use discrete state labels.

**Critical framing requirement:** Claim "first systematic benchmark evaluating whether
discrete conformational state-conditioning improves molecular generation," NOT "first
dynamics-aware molecular design." The broader claim would invite rejection.

### C3: Pre-Publication Fixes Are Non-Negotiable
**Reviewers:** All 5

Three fixes must be completed before any new experiments:
1. **Osimertinib reference leakage** -- remove from pre-2015 reference set
2. **3W2R mutant structure** -- verify, find WT alternative, or disclose and control
3. **Bootstrap CIs + BEDROC** -- no CIs = unpublishable

**Timeline disagreement:** Progdir says "hours." Associate says "5-8 days" after tracing
the actual code paths. The realistic estimate is 5-8 days (associate's assessment is
more grounded in codebase reality).

### C4: Ablation C (Unconditioned VAE) Is Thesis-Critical
**Reviewers:** All 5

If the unconditioned VAE matches state-conditioned VAE on enrichment (Cohen's d < 0.5),
the paper pivots to "diverse generation outperforms template-based design." Still
publishable at JCIM but a fundamentally different narrative. Pre-registered success
threshold (Cohen's d >= 0.8) is commended as rare and differentiating.

### C5: REINVENT 4 Is the Essential External Baseline
**Reviewers:** All 5

REINVENT 4 v4.7 is confirmed available (Apache 2.0, GitHub MolecularAI/REINVENT4).
Custom scoring integration with GNINA is feasible via plugin architecture but non-trivial
(2-4 weeks, not "1-2 weeks"). REINVENT is the minimum viable baseline for JCIM
submission.

### C6: FLOWR Should Be Replaced or Downgraded
**Reviewers:** mlrev, principal, associate (3/5)

FLOWR is unmaintained (repo directs to FLOWR.root), requires 40GB VRAM (RTX 5000 Ada
has 16GB), and has integration risks. Recommended replacements:
- **mlrev:** MolPilot (ICML 2025, 95.9% PoseBusters validity, HuggingFace checkpoint)
- **associate:** DiffSBDD (Zenodo checkpoints, 16GB compatible, published in Nat Comp Sci)
- **principal:** acknowledges constraint; recommends H200-only fallback

**Resolution for Round 2:** Verify MolPilot and DiffSBDD availability and VRAM requirements.

### C7: Scoring Function Unchanged for Primary Analysis
**Reviewers:** compbiorev, mlrev, progdir (3/5; principal leans toward scoring reform)

The primary comparison MUST use the original 4-component scoring (0.35/0.30/0.20/0.15).
Changing scoring to favor state-aware invites "you gamed the metric" perception. Report:
1. Original 4-component as primary
2. 3-component (no state_specificity) as mandatory fairness check
3. 1,000+ Dirichlet sensitivity analysis as supplementary
4. Scoring gap decomposition showing reference_similarity explains the entire gap

### C8: Multi-Kinase Panel: EGFR + ABL1 + BRAF + MET
**Reviewers:** All 5

All reviewers endorse this kinase set. JAK2 and RET correctly dropped. ABL1 should be
first (most data, best-characterized DFGout). MET is contingent on structural data
quality. Three kinases with strong results > four kinases with one weak result.

### C9: Kinetic Scoring (tauRAMD) Should Be Cut
**Reviewers:** All 5

150-250 GPU-days for uncertain results. Tier 3 heuristic is redundant with
state_specificity (correctly identified by cheminfo critique). The conformational
selection *narrative* (zero-cost writing) is endorsed; the kinetic *scoring component*
is unanimously rejected for this paper.

### C10: Benchmark Infrastructure Deferred
**Reviewers:** All 5

The benchmark paper (bencharch-P01) is premature. Docker containers, leaderboards,
and HuggingFace hosting distract from the primary scientific contribution. Target
NeurIPS 2027 E&D after Paper 1 is published.

### C11: Pre-Registration Is Differentiating
**Reviewers:** All 5

Locking analysis decisions (primary endpoint BEDROC, kinase set, success criteria)
before experiments is rare in computational drug design and will be noted favorably
by reviewers. Should be formalized with a timestamped git commit or OSF registration.

---

## Areas of Disagreement

### D1: Realistic Timeline
| Reviewer | Estimate | Basis |
|----------|----------|-------|
| progdir | 12 weeks | Strategic optimization (scope-cut aggressively) |
| associate | 14-18 weeks | Single-researcher implementation experience |
| principal | 20-26 weeks | Codebase analysis (EGFR-hardcoded refactoring) |
| mlrev | 20-24 weeks | Benchmark reproduction experience |

**Key divergence:** Principal and associate identified a critical issue the other
reviewers did not: the codebase is deeply EGFR-hardcoded across 9+ files
(ConformationalState enum, pocket conditions, reference binders, data registry, VAE
config). "Adding a kinase" requires 4-6 weeks of refactoring, which is invisible in
both cohorts' agendas. Progdir's 12-week estimate assumes this refactoring doesn't
exist.

**Resolution needed in Round 2:** Principal should verify exact refactoring scope.
Is incremental extension (add kinase-specific code alongside EGFR code) faster than
full refactoring?

### D2: Scoring Reform Priority
| Position | Reviewers |
|----------|-----------|
| Keep original scoring as primary, sensitivity as secondary | compbiorev, progdir, mlrev |
| Scoring reform should be Priority 1 | principal (sides with Cohort2) |

**The tension:** Principal argues the mean-score gap is the #1 publication blocker and
must be resolved before anything else. The other three argue that resolving it by
changing the scoring function creates a "post-hoc optimization" perception. The
sensitivity analysis approach (showing the gap is explained by reference_similarity
without changing it) is the majority position.

### D3: 3D Baseline Choice
| Reviewer | Recommendation |
|----------|---------------|
| mlrev | MolPilot (95.9% PB, ICML 2025, HuggingFace) |
| associate | DiffSBDD (16GB, Zenodo, Nat Comp Sci) |
| compbiorev | FLOWR (if SPINDR avoids EGFR leakage) |
| principal | H200-only FLOWR fallback |

**Resolution for Round 2:** Verify MolPilot VRAM requirements, DiffSBDD current
availability, and SPINDR/CrossDocked2020 EGFR overlap.

### D4: GIST Water Analysis Priority
| Reviewer | Priority |
|----------|----------|
| compbiorev | P1 (best cost/impact ratio) |
| principal | Should-Do (strongly recommended) |
| progdir | Tier 3 (nice to have, not required for JCIM) |

---

## New Critical Issues Raised by Reviewers

### N1: EGFR-Hardcoded Codebase (Principal, Associate)
The codebase has EGFR-specific content in 9+ files: `processing/models.py` (enum),
`generation/conditioning.py` (pocket conditions), `baselines/scoring.py` (reference
binders), `evaluation/retrospective.py` (drug approvals), `data/registry.py` (data
manifests), `configs/vae.yaml` (state mapping), and others. Multi-kinase extension
requires a refactoring project that neither cohort acknowledged. **This is the critical
path bottleneck.**

### N2: Candidate Count Discrepancy: 431 vs 461 (Associate)
Both agendas cite 461 state-aware candidates. The actual comparison artifact shows 431.
Must be reconciled before any new work begins.

### N3: RAscore Is Python 3.7-3.8 Only (Associate)
Completely incompatible with Python 3.12. Must be skipped or run in separate environment.
Recommendation: skip RAscore, use AiZynthFinder directly.

### N4: No Compute-Matched Comparison (MLRev)
The PMO benchmark (Gao et al., NeurIPS 2022) established fixed oracle call budgets as
the fairness standard. The ablation suite compares methods with wildly different
computational budgets. This is a NeurIPS/ICML reviewer kill shot.

### N5: Missing Evaluation Metrics (MLRev)
FCD (Frechet ChemNet Distance), novelty fraction, SEDiv/#Circles, and property
distribution tests are expected in 2026 molecular generation papers. All are low-cost
additions.

### N6: Within-Method State Ablation Misconception (CompBioRev)
Running REINVENT on 4 pockets sequentially is "pocket-specific optimization," not
"state-conditioning." The paper must distinguish between these concepts and not overclaim
that REINVENT is "state-conditioned" when it simply docks against 4 structures.

### N7: GNINA Docking Is the Dominant Compute Cost (Associate)
Re-docking all methods across all states and kinases costs ~900-1,000 GPU-hours, far
exceeding the cohorts' baseline estimates. This was drastically underestimated.

### N8: Conformal Prediction Is Now Expected, Not Optional (MLRev)
CP is standard practice in 2026. Any JCIM or NeurIPS submission without uncertainty
quantification will draw reviewer criticism. Implementation is straightforward
(MAPIE/split CP).

### N9: MPNN Split Type Unknown (MLRev)
R²=0.69 -- is this random split, temporal, or scaffold? If random, the effective
predictive performance on novel scaffolds (VAE-generated molecules) is likely R²=0.3-0.5.
This directly affects the reliability of MPNN scores on generated molecules.

### N10: CrossDocked2020 Leakage Must Be Checked Pre-Experiment (Associate)
Concrete check: download CrossDocked2020 PDB ID list, grep for EGFR structures (1M17,
2GS7, 3W2R, 4ZAU). If found, any 3D baseline trained on CrossDocked2020 is not "zero-
shot" for EGFR. This 30-minute check should be done before choosing the 3D baseline.

---

## Master Claims Verification List (for Round 2)

| # | Claim | Status | Assigned To | Priority |
|---|-------|--------|-------------|----------|
| 1 | No paper conditions generation on discrete conformational states | Partially verified (all 5) | compbiorev | HIGH |
| 2 | Type II Gini 0.76 vs Type I 0.58 | Needs page-level verification | compbiorev | MEDIUM |
| 3 | MPNN R²=0.69 split type (random/scaffold/temporal) | Unknown | principal | HIGH |
| 4 | VAE 99.9% validity: autoregressive or teacher-forced? | Unknown | mlrev | HIGH |
| 5 | CrossDocked2020 contains EGFR structures | Highly likely, needs confirmation | associate | HIGH |
| 6 | MolPilot availability, VRAM, checkpoint access | Unverified | mlrev | HIGH |
| 7 | DiffSBDD current availability, 16GB feasibility | Unverified | associate | HIGH |
| 8 | REINVENT 4 GNINA scoring plugin: feasible? | Architecturally yes; untested | principal | MEDIUM |
| 9 | Candidate count: 431 vs 461 | Discrepancy found | associate | HIGH |
| 10 | ADMETlab 3.0 API operational and free | Assumed | associate | MEDIUM |
| 11 | AiZynthFinder 4 conda install feasibility | Assumed | associate | MEDIUM |
| 12 | EGFR WT DFGout structure exists in PDB/KLIFS | Unknown | compbiorev | HIGH |
| 13 | Codebase refactoring scope for multi-kinase | Identified but not quantified | principal | HIGH |
| 14 | MolPilot vs FLOWR vs DiffSBDD training data overlap | Unknown | mlrev | HIGH |
| 15 | Chemprop v2 multi-task with missing labels | Verified | -- | DONE |

---

## Revised Priority Ranking (Reviewer Consensus)

### Tier 0: Immediate (Before Any Experiments)
1. Fix osimertinib reference leakage
2. Bootstrap CIs + BEDROC on current results
3. Verify 3W2R and 4ZAU structures
4. Reconcile 431 vs 461 candidate count
5. Check CrossDocked2020 for EGFR PDB IDs
6. Determine MPNN R²=0.69 split type
7. Write and timestamp pre-registration document

### Tier 1: Critical Path (Weeks 1-6)
8. Ablation C: unconditioned VAE (GO/NO-GO at Cohen's d threshold)
9. Multi-target codebase refactoring (critical path bottleneck)
10. REINVENT 4 setup and GNINA scoring bridge
11. Ablation E, F, G on EGFR

### Tier 2: Multi-Kinase Execution (Weeks 4-12)
12. Per-kinase data curation (ABL1, BRAF, MET)
13. Per-kinase model training (VAE + MPNN)
14. Per-kinase pipeline execution and retrospective enrichment
15. 3-component scoring fairness check
16. Conformal prediction for MPNN (MAPIE)
17. Dirichlet scoring sensitivity analysis (1,000+ samples)

### Tier 3: Enhancement (Weeks 8-14)
18. Conformational selection narrative (zero compute)
19. Chemical space UMAP + property distributions (mandatory for venue)
20. FCD + SEDiv + novelty metrics (low-cost additions)
21. GIST water analysis (if time permits)
22. Survival funnel (ADMETlab + AiZynthFinder)

### Tier 4: Deferred (Paper 2 / Nature Comp Sci Upgrade)
23. 3D baseline (MolPilot or DiffSBDD)
24. Within-method state ablations (REINVENT multi-pocket vs single-pocket)
25. Benchmark infrastructure (Docker, leaderboard)
26. OpenFE FEP validation
27. tauRAMD kinetic scoring
28. Pocket-aware scoring (DrugCLIP)

---

## Top 3 Reviewer Kill Shots (Unanimous)

### Kill Shot 1: "Enrichment is driven by diversity, not state-conditioning"
**Defense:** Ablation C (unconditioned VAE). If it matches state-conditioned on
enrichment, the reviewer is right and the paper pivots. Pre-register the threshold.

### Kill Shot 2: "With N=5-10 held-out drugs, no statistical conclusion is possible"
**Defense:** BEDROC (uses full ranking, higher power than EF). BCa bootstrap CIs.
Multi-kinase pooling. Honest reporting of wide CIs. Pre-registration.

### Kill Shot 3: "The scoring function rewards similarity to known drugs; the static
pipeline trivially wins because it generates similar molecules"
**Defense:** Gap decomposition showing reference_similarity explains 100%+ of the gap.
3-component scoring as fairness check. Dirichlet sensitivity analysis. Frame as
methodological insight. Use enrichment (not mean score) as primary comparison.

---

## Round 2 Assignments

Based on reviewer expertise and the verification needs identified above, Round 2 will
assign each reviewer 3-5 specific verification tasks. See orchestrator's Round 2
directive for details.

---

*This synthesis consolidates 5 independent reviews totaling 3,100+ lines and 110+
citations. All conclusions represent majority positions except where disagreements are
explicitly noted.*
