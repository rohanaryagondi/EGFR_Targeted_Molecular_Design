---
agent: Orchestrator
round: 4
date: 2026-04-09
type: roundtable
---

# Cohort2 Final Agenda: Prioritized Research Plan for StateBind Publication

## Executive Summary

Three rounds of independent research, formal proposals, and cross-domain critique
by 7 domain specialists produced a converged research agenda for taking StateBind
from a completed computational pipeline to top-venue publication. This document
synthesizes 4,800+ lines of deep research (190+ citations), 5 formal proposals,
and 6 cross-domain critiques into a prioritized, actionable plan.

**The headline finding across all agents:** StateBind's 10x retrospective enrichment
for DFG-out EGFR inhibitors is a genuinely novel result targeting the single most
important unmet need in EGFR therapy (C797S resistance). The path to publication
requires: (1) fixing the scoring artifact that obscures the result, (2) demonstrating
generalization beyond EGFR, and (3) providing mechanistic and translational framing.

**Recommended strategy:** Two papers from a coordinated work program.

---

## Part I: Cross-Critique Convergence Analysis

### What All Reviewers Agreed On

Six critiques across 5 proposals produced remarkable convergence on several points:

1. **The scoring artifact must be resolved first.** The mean-score gap (static 0.5437
   vs state-aware 0.4378) is more than fully explained by reference_similarity (35%
   weight, Morgan/Tanimoto to 3 quinazoline drugs). Every critique touching scoring
   confirmed this is the #1 publication blocker. Until the scoring function is reformed,
   no other analysis is credible.

2. **JAK2 is the weakest kinase choice.** Both drughunt and clinonc independently
   concluded that JAK2 lacks a conformational-state-linked clinical rationale. JAK
   inhibitors are intentionally non-selective across JAK family members. The held-out
   drug list conflates indications (tofacitinib for RA, not MPN). Drop JAK2.

3. **Clinical narrative and computational breadth are in tension but resolvable.**
   Lead with the EGFR C797S resistance story (the sharpest clinical hook), then
   demonstrate generalization. Do not bury EGFR among 5 equal kinases.

4. **The conformational selection narrative is zero-cost, high-value, and
   publication-ready.** The biophys agent's draft Discussion text linking state-aware
   DFGout design to long residence time via conformational selection was endorsed by
   cheminfo as "essentially publication-ready."

5. **Pocket-aware scoring (DrugCLIP/ProFSA) is a cross-cutting upgrade.** protml
   independently recommended pocket-ligand co-embedding scores for both the benchmark
   (P2) and the scoring reform (P3). This addresses the fundamental criticism that the
   current scoring function is pocket-blind.

6. **All 5 proposals received "Support with Modifications."** No proposal was rejected.
   The modifications are substantial but tractable.

### Key Tensions Identified by Reviewers

| Tension | Agents | Resolution |
|---------|--------|------------|
| Kinase panel: data-driven vs clinical | drughunt vs kinpharm | 3-4 kinases with clinical rationale per kinase |
| Scoring: add kinetic component vs reform first | biophys vs cheminfo | Sequence: reform first, then kinetics |
| Uni-Mol: co-primary vs supplementary | protml vs cheminfo | Test both; let data decide |
| Venue: Nature Comp Sci vs JCIM | drughunt vs clinonc | Two-paper strategy resolves this |
| Tier 3 kinetic heuristic: synergy vs redundancy | biophys vs cheminfo | Eliminate Tier 3; use kinetics as post-hoc filter or merge with state_specificity |

---

## Part II: The Two-Paper Strategy

The strongest strategy, independently suggested by clinonc, drughunt, and protml,
is a coordinated two-paper approach targeting different audiences:

### Paper 1: Methods + Multi-Kinase Validation

**Target venue:** Nature Computational Science (primary) or JCIM (fallback)
**Title draft:** "Conformational State-Aware Molecular Design Generalizes Across
Therapeutically Relevant Kinases"
**Core claim:** State-conditioned generation produces enriched, selective molecules
across kinases with conformational resistance mechanisms.

**Draws from:** P1 (multi-kinase), P3 (scoring reform), P5 Component B (kinetic
narrative), P4 (C797S as translational highlight)

**Proposed figure set:**
1. EGFR conformational state landscape and the DFG-out clinical gap
2. Scoring reform: 6-configuration sensitivity table + reformed mean-score comparison
3. Multi-kinase enrichment forest plot (3-4 kinases)
4. DFG-out selectivity analysis (Gini advantage, PKIS2/KCGS validation)
5. Chemical space visualization (UMAP, scaffold diversity, per-state chemotype analysis)
6. Extended: Multi-task MPNN ablation, conformal prediction intervals, C797S docking

### Paper 2: Benchmark + Community Resource

**Target venue:** JCIM (primary), NeurIPS 2027 E&D Track (stretch)
**Title draft:** "StateBind-Bench: The First Benchmark for Conformational
State-Conditioned Molecular Generation"
**Core claim:** A four-task benchmark filling a confirmed gap, with containerized
evaluation and multi-format pocket representations.

**Draws from:** P2 (benchmark), P3 (scoring metrics), protml critique additions
(representation ablation, DrugCLIP scoring)

---

## Part III: Prioritized Work Items

### Priority 1: Scoring Reform (Essential -- Publication Blocker)

**Source:** cheminfo-P01, endorsed by all reviewers
**Effort:** ~5 person-weeks, ~8 GPU-hours
**Why first:** Until the scoring artifact is explained, no downstream analysis is
credible. Every reviewer identified this as the #1 issue.

**Work items:**

| # | Task | Details |
|---|------|---------|
| 1.1 | Expand reference set | 3 drugs -> 100-300 ChEMBL EGFR scaffold centroids |
| 1.2 | Multi-metric sensitivity | 6 configurations: {Tanimoto, Tversky, PheSA} x {3 drugs, ChEMBL centroids} |
| 1.3 | Pocket-aware scoring test | Add DrugCLIP pocket-ligand compatibility as 7th configuration (protml M1) |
| 1.4 | Uni-Mol comparison | Run parallel analysis with Uni-Mol 3D embeddings (protml M2) |
| 1.5 | Chemical space figures | UMAP (Morgan + Uni-Mol), property distributions, SEDiv/#Circles |
| 1.6 | Conformal prediction | Split CP on MPNN with 5-model ensemble for epistemic uncertainty |
| 1.7 | Co-embedding UMAP | Joint pocket + ligand embedding visualization (protml M4) |

**Key modification from critiques:** The protml critique's highest-priority
recommendation -- adding a pocket-aware scoring configuration (DrugCLIP) -- should be
included. If this single configuration shows qualitatively different results from all
ligand-only variants, it becomes the paper's strongest finding: "Pocket-aware scoring,
the appropriate metric for state-conditioned generation, reveals the true state-aware
advantage."

**Output:** Publication figures 2 and 5 for Paper 1. Complete scoring reform
codebase for all downstream analyses.

---

### Priority 2: Multi-Kinase Extension (Essential -- Statistical Credibility)

**Source:** kinpharm-P01, modified per drughunt + clinonc critiques
**Effort:** ~10-14 weeks, ~20 GPU-days
**Why second:** Addresses the #1 reviewer concern (N=3-5 held-out drugs) and
transforms a case study into a general finding.

**Critical modifications from Round 3 critiques:**

| Modification | Source | Impact |
|-------------|--------|--------|
| Drop JAK2, reduce to 3-4 kinases | drughunt + clinonc | Fixes clinical incoherence, JAK2 held-out drug list issues |
| Add clinical unmet need matrix | clinonc M1 | Justifies each kinase with resistance mechanism rationale |
| Add TPP evaluation for generated candidates | drughunt M2 | Answers "do generated molecules look like real drugs?" |
| Lead with EGFR C797S, then generalize | clinonc M2 | Preserves clinical hook while demonstrating breadth |
| Develop Relay Therapeutics comparison table | drughunt M3 | Preempts "how does this compare to Relay?" reviewer question |
| Add state assignment calibration | drughunt M4 | Quantifies heuristic misclassification per kinase |
| Address ALK pre-2010 anachronism | clinonc M5 | ALK medicinal chemistry barely existed before 2007 |

**Recommended kinase panel (revised):**

| Kinase | Rationale | Strength |
|--------|-----------|----------|
| EGFR | Core story. C797S resistance. Zero approved DFGout inhibitors. | Essential |
| ABL1 | Archetypal DFGout drug (imatinib). T315I resistance is conformational. 350+ PDB structures. | Strong |
| BRAF | Vemurafenib binds DFGout V600E. Paradoxical activation is conformational selectivity. | Moderate-Strong |
| MET or CDK2 | MET: most common EGFR resistance mechanism (15-18%), keeps NSCLC focus. CDK2: 400+ structures, well-characterized DFG states. | Optional 4th |

**Dropped:** JAK2 (weak clinical rationale, held-out drug list issues, resistance
is pathway-level). ALK downgraded to supplementary analysis only (pre-2010 data
too sparse, but pre-2015 analysis may be valuable).

**Work items:**

| # | Task | Details |
|---|------|---------|
| 2.1 | Data curation | ChEMBL extraction + quality filtering for ABL1, BRAF, (+MET or CDK2) |
| 2.2 | State atlas | KLIFS structures + AF2-MSM supplementation with quality thresholds |
| 2.3 | State assignment calibration | Validate heuristic Type I/II assignment against co-crystal structures |
| 2.4 | Multi-task D-MPNN | Shared encoder + kinase embedding + 9D state vector; ablation study |
| 2.5 | Retrospective validation | Per-kinase EF@10, pooled meta-analysis, I-squared heterogeneity |
| 2.6 | Selectivity analysis | DFGout Gini advantage, PKIS2/KCGS external validation |
| 2.7 | TPP concordance | Score top-50 per pipeline against literature-derived TPP per kinase |
| 2.8 | C797S docking | Dock top EGFR DFGout candidates into C797S mutant structures |

**Output:** Publication figures 1, 3, 4, 6 for Paper 1.

---

### Priority 3: Conformational Selection Narrative (Zero-Compute, High-Value)

**Source:** biophys-P01 Component B, endorsed by cheminfo critique
**Effort:** ~1 person-week (writing only)
**Why parallel:** Requires no code or compute. Can be written simultaneously with
Priorities 1-2. Adds mechanistic depth that elevates the paper from "method works"
to "method works because of conformational selection biophysics."

**Work items:**

| # | Task | Details |
|---|------|---------|
| 3.1 | Draft Discussion section | Conformational selection causal chain (5 steps) with literature support |
| 3.2 | Lapatinib vs gefitinib case study | 430 min vs <14 min RT despite weaker equilibrium affinity |
| 3.3 | 10x enrichment reframing | Explicit argument that DFGout enrichment = implicit kinetic optimization |
| 3.4 | Relay Therapeutics positioning | "Open-source, generalizable alternative to proprietary platform" |
| 3.5 | Wording precision | "Predicted to" not "expected to" (cheminfo W6) |

**Minor modification from cheminfo critique:** Soften one overclaim -- "expected to
inherit favorable kinetic properties" should be "predicted to inherit" or
"hypothesized to inherit." Also verify Gini coefficient citation (Zhao et al., 2017
studied cysteine-targeting compounds, not all Type II -- use Uitdehaag et al., 2012
or Davis et al., 2011 instead).

**Output:** Discussion section text for Paper 1.

---

### Priority 4: Kinetic Scoring Component (Deferred -- Requires Scoring Reform First)

**Source:** biophys-P01 Component A, substantially modified per cheminfo critique
**Effort:** ~3-6 person-weeks, ~150-250 GPU-days for Tier 1 (tauRAMD)
**Why deferred:** The cheminfo critique identified critical issues that must be
resolved before this component can be added:

1. **Tier 3 heuristic is redundant with state_specificity.** At Tier 3, the kinetic
   score is a monotone function of conformational state -- identical information to
   state_specificity, repackaged. Adding it with 10% weight is equivalent to increasing
   state_specificity's effective weight by ~7%. Reviewers trained in multivariate
   statistics will identify this immediately.

2. **Weight allocation must be coordinated with scoring reform.** biophys-P01 reduces
   reference_similarity 0.35->0.30 and druglikeness 0.30->0.25. cheminfo-P01 changes
   what reference_similarity *means*. These cannot proceed independently.

3. **5 scoring components exacerbates Pareto curse of dimensionality.**

**Recommended approach (from cheminfo critique alternatives):**

**Option A (preferred): Kinetics as post-hoc analysis, not scoring component.**
Compute kinetic predictions for all candidates. Analyze correlation between StateBind
scores and predicted kinetics. If state-aware candidates have significantly better
predicted kinetics, this validates the conformational selection narrative without
modifying the scoring function. Present as independent validation dimension.

**Option B: Merged state-kinetic component.** If kinetic scoring is added, merge it
with state_specificity into a single component (20-25% combined weight) to avoid
redundancy. Derive weight via grid search optimizing EF@10.

**Sequencing:** (1) Complete scoring reform (Priority 1). (2) If kinetics is added,
run joint weight optimization across all components. (3) Report sensitivity curves
as a publication figure.

**tauRAMD validation prerequisite (from cheminfo A3):** Before committing 150-250
GPU-days, validate tauRAMD on known drugs (erlotinib, gefitinib, lapatinib) to
confirm it correctly ranks lapatinib >> gefitinib in residence time. This costs ~3
GPU-days and de-risks the entire investment.

---

### Priority 5: Benchmark (Independent Track -- Paper 2)

**Source:** bencharch-P01, modified per protml critique
**Effort:** ~8 weeks for Phase 1, ~1,300-2,500 GPU-hours
**Why independent:** Can proceed in parallel with Paper 1 work. Targets a different
audience and venue.

**Critical modifications from protml critique:**

| Modification | Priority | Impact |
|-------------|----------|--------|
| Add pocket representation ablation task | Essential | Tests whether richer pocket representations improve generation -- the question ML community cares about |
| Add DrugCLIP co-embedding as secondary scoring | High | Orthogonal to GNINA, harder to game, engages representation learning community |
| Provide multi-format pocket representations | High | PDB + ESM-2 + ProstT5 + voxelized grid + graph + point cloud + KLIFS fingerprint |
| Use raw GNINA only for Tasks 1-2 | Medium | Eliminates circularity from composite score's built-in state_specificity |
| Address structure prediction for multi-kinase | Medium | Document which kinase-state combos need AF2 supplementation |
| Host baseline model checkpoints | Medium | HuggingFace Model Hub for runnable baselines |

**Pocket representation ablation (protml's top recommendation):**
Holding the VAE architecture fixed, vary the pocket conditioning input:
- 9D geometric features (current)
- ESM-2 650M pocket embedding (1280D)
- ProstT5 3Di-conditioned pocket embedding (1024D)
- KLIFS 85-residue interaction fingerprint
- ESM-2 + 9D concatenation

This is arguably the benchmark's most novel contribution. Cost: ~10 GPU-hours
additional (negligible vs. 1,300+ for docking).

**NeurIPS 2026 deadline (May 6):** Not feasible for polished submission. Target
JCIM for Phase 1, then NeurIPS 2027 E&D with multi-kinase extension.

---

### Priority 6: Resistance-Informed Design (Integration into Paper 1)

**Source:** clinonc-P01, modified per drughunt critique
**Effort:** ~6-8 weeks, ~185 GPU-hours standalone; reduced if integrated
**Recommendation:** Do not pursue as standalone paper. Instead, integrate the
C797S resistance angle as a translational highlight within Paper 1.

**What to integrate into Paper 1:**
- C797S docking of top DFGout EGFR candidates (Priority 2.8)
- Clinical framing of the DFGout gap in Introduction
- "Distance to IND" discussion section (drughunt M6)
- "Why DFGout despite BDTX-1535?" argument (drughunt M1)

**What to defer:**
- AF2 prediction of mutant DFGout structures (high risk -- drughunt noted AF2
  training bias toward DFGin; 87% of KLIFS entries are DFGin)
- Full 4-condition experimental design (too much scope for Paper 1)
- AF2 pilot validation should be run first if pursued later (3 GPU-hours)

**drughunt's assessment:** "The strongest proposal I have seen from this cohort --
it picks the right clinical problem and frames it honestly." The clinical anchoring
is extremely valuable as Paper 1's translational motivation, even if the full
standalone experiment is deferred.

---

### Priority 7: Experimental Validation Design (Future Collaboration)

**Source:** biophys-P01 Component C
**Effort:** $40-100K, 4-8 weeks (external)
**Status:** Correctly prioritized last by the original proposal. Frame as "proposed
experimental collaboration" in Paper 1's Discussion.

**SPR panel:** 10 compounds, 4 EGFR variants, $10-52K
**HDX-MS:** Conformational state confirmation, $30-50K

These are the gold-standard validations of StateBind's central hypothesis but
require a wet-lab collaborator or CRO. Include the experimental design in Paper 1
as evidence of scientific seriousness and a concrete path to validation.

---

## Part IV: Coordinated Timeline

```
Weeks 1-5:   Priority 1 (Scoring Reform) -- clears the publication blocker
             Priority 3 (Narrative) -- in parallel, writing only
             Priority 5 (Benchmark) -- in parallel, data packaging + baseline setup

Weeks 3-5:   Priority 2 starts (Data Curation) -- overlaps with scoring reform tail

Weeks 5-12:  Priority 2 continues (Atlas, MPNN, Validation)
             Priority 5 continues (Baseline runs, evaluation)
             Priority 4 decision point: pilot tauRAMD validation (3 GPU-days)

Weeks 12-16: Paper 1 writing + figure generation
             Priority 5 Phase 1 completion

Weeks 16-18: Paper 1 submission (Nature Computational Science)
             Paper 2 submission (JCIM)
```

**Total estimated effort:** ~20-26 person-weeks for both papers
**Total compute:** ~25-30 GPU-days for Paper 1, ~1,300-2,500 GPU-hours for Paper 2
**Infrastructure:** Yale Bouchet HPC (H200 + RTX 5000 Ada), existing StateBind
pipeline, public data (ChEMBL, PDB, KLIFS, PKIS2, KCGS)

---

## Part V: Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Enrichment does not generalize to all kinases | 30% | High | Report I-squared heterogeneity honestly; fall back to "kinases with rich conformational data" |
| Scoring reform closes the gap but does not reverse it | 20% | Medium | The 10x enrichment factor is the true metric, not mean score |
| AF2-MSM structures for sparse kinases are poor quality | 40% | Medium | Quality threshold (docking AUC >= 0.70); fall back to 2-state analysis |
| Multi-task MPNN shows negligible improvement | 25% | Medium | Ablation study is pre-planned; report honestly |
| BDTX-1535 phase 2 data undermine DFGout argument | 15% | Low | Frame DFGout as complementary mechanism, not replacement |
| NeurIPS 2026 deadline too tight for benchmark | 90% | Low | Target JCIM instead; NeurIPS 2027 for extended version |
| tauRAMD fails to reproduce known kinetics | 30% | Medium | Validates before committing 150+ GPU-days; fall back to ML koff or post-hoc analysis |

---

## Part VI: What Not To Do

The critiques also converged on several things to avoid:

1. **Do not add a 5th scoring component before reforming the existing 4.** (cheminfo
   critique of biophys-P01)
2. **Do not include JAK2 in the kinase panel.** (drughunt + clinonc)
3. **Do not claim "kinome selectivity" from a 5-kinase panel.** Use "within-panel
   target preference" and reserve selectivity language for PKIS2/KCGS results.
   (drughunt M5)
4. **Do not use AF2 DFGout structures without cross-target validation first.**
   (drughunt critique of clinonc-P01)
5. **Do not overclaim.** "Predicted to" not "expected to." "Computational hypothesis"
   not "result." (cheminfo W6, project CLAUDE.md Rule 1)
6. **Do not bury EGFR among equal kinases.** The clinical narrative demands EGFR
   leads. (clinonc M2)
7. **Do not ignore the Relay Therapeutics comparison.** If the paper does not
   preemptively address it, reviewers will use it against the submission.
   (drughunt W3)

---

## Part VII: Summary Decision Matrix

| Proposal | Verdict | Disposition | Paper |
|----------|---------|-------------|-------|
| P1: Multi-Kinase (kinpharm) | Support w/ Mods | Core of Paper 1 (reduced to 3-4 kinases) | Paper 1 |
| P2: Benchmark (bencharch) | Support w/ Mods | Core of Paper 2 (add representation ablation) | Paper 2 |
| P3: Scoring Reform (cheminfo) | Support w/ Mods | Priority 1 for Paper 1 (add pocket-aware scoring) | Paper 1 |
| P4: Resistance Design (clinonc) | Support w/ Mods | Integrated as translational highlight in Paper 1 | Paper 1 |
| P5: Kinetic Scoring (biophys) | Support w/ Mods | Component B integrated; Component A deferred/redesigned | Paper 1 (narrative) |

---

## Appendix: Agent Contributions Summary

| Agent | R01 Lines | R01 Citations | Proposal | Critiques Written | Key Contribution |
|-------|----------|---------------|----------|-------------------|------------------|
| drughunt | 560+ | 28 | -- | kinpharm-P01, clinonc-P01 | TPP framework, competitive landscape, Relay comparison, venue strategy |
| biophys | 786 | 32 | P5 (kinetic + narrative) | -- | Residence time data, conformational selection narrative, SPR/HDX-MS design |
| cheminfo | 650+ | 30 | P3 (scoring reform) | biophys-P01 | Mean-score gap decomposition, multi-metric sensitivity, Tier 3 redundancy catch |
| clinonc | 815 | 31 | P4 (resistance design) | kinpharm-P01 | C797S clinical case, honest framing, clinical unmet need matrix |
| protml | 908 | 27 | -- | cheminfo-P01, bencharch-P01 | ESM-2 limitation (critical), ProstT5 for states, DrugCLIP scoring, pocket representation ablation |
| kinpharm | 508 | 26 | P1 (multi-kinase) | -- | Kinase data availability, power analysis, PKIS2/KCGS validation design |
| bencharch | 586 | 28 | P2 (benchmark) | -- | Benchmark gap confirmation, 4-task design, reproducibility infrastructure |

**Total Cohort2 output:** 7 research notes (4,800+ lines, 190+ citations),
5 proposals, 6 cross-domain critiques, 2 synthesis documents, 2 directives,
1 final agenda.

---

*This agenda represents the synthesized judgment of 7 independent domain specialists
across 3 rounds of research, proposal writing, and cross-domain critique. All
recommendations are computational hypotheses informed by published evidence. No
experimental claims are made.*
