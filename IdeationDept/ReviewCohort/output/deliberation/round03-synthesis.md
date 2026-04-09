---
agent: Orchestrator (Panel Chair)
round: 3
date: 2026-04-09
type: roundtable
scope: deliberation-synthesis
---

# Round 3 Synthesis: Deliberation Convergence

## Overview

All five reviewers have responded to each other's Round 2 findings and provided
final positions. This synthesis identifies consensus, resolves disagreements by
evidence weight, and establishes the definitive inputs for the Round 4
implementation plan.

**Net result: Strong convergence.** Of the 4 disagreements entering Round 3, 2
are fully resolved and 2 are narrowed to actionable decision rules. The panel
achieves 5/5 agreement on 14 of 16 mandatory work items, on JCIM as the primary
venue, and on the overall project viability (7.0-7.5/10 range).

---

## 1. Consensus Positions (5/5 Agreement)

### C1: Structural Atlas Fix Is Tier 0, Item 0

All reviewers agree this is the single highest priority. No other work produces
credible results until the structural annotations are corrected. The fix is
containable (4-6 hours for 4-state, 2-2.5 days for 3-state) and does not
require architectural changes. The existing curated features are internally
consistent with the intended pocket geometries; the error is in the PDB
metadata annotations, not in the pocket descriptions themselves.

**Key finding (principal):** The docking config (`configs/docking.yaml:24-25`)
already contains a comment acknowledging that 3iku is not EGFR -- someone
discovered this during workstream 11 but did not propagate the fix. This is a
process failure, not a conceptual one.

### C2: 4ZAU Verification Is a 1-2 Hour Task That Must Come First

Three DFG-motif measurements in PyMOL/ChimeraX determine the answer:
1. DFG-Asp831/Phe832 chi1 torsion (DFGin: ~-60deg; DFGout: ~180deg)
2. Phe832 position relative to ATP site
3. K745-E762 salt bridge distance (aCin: <4A; aCout: >6A)

This is not debatable and must not be deferred.

### C3: MPNN Random Split Is Publication-Blocking

All reviewers independently confirmed the random split at
`affinity_dataset.py:388-390`. R^2=0.69 on random split is uninformative for
novel scaffold generalization. Scaffold-split R^2 (estimated 0.45-0.55 by
mlrev and principal, based on Yang et al. 2019 benchmarks) must be reported.

**Go/No-Go consensus:**
- R^2 >= 0.35: MPNN is a credible scoring component (GO)
- R^2 in [0.20, 0.35]: MPNN is marginal; frame as "supplementary signal" (CONDITIONAL GO)
- R^2 < 0.20: Drop MPNN from scoring; use GNINA + descriptors + state_specificity (NO-GO)
- Probability of NO-GO: ~10% (small dataset of ~90 compounds hurts scaffold splits)

### C4: Bootstrap CIs + BEDROC Are Mandatory

No confidence intervals = no statistics = no publication. 1000-fold BCa bootstrap
on EF@10, BEDROC(alpha=20), and mean scores. Straightforward numpy implementation,
0.5-1 day effort.

### C5: Ablation C Is THE Make-or-Break Experiment

All reviewers agree this is the thesis test. If an unconditioned VAE (same
architecture, no state labels) achieves the same enrichment, the state-conditioning
contribution is null. Pre-registration of the threshold via timestamped git commit.

**Go/No-Go consensus (converged from initial disagreements):**
- Cohen's d >= 0.8: Strong effect, paper's thesis robustly supported (STRONG GO)
- Cohen's d in [0.5, 0.8): Moderate effect, publishable with tempered claims (GO)
- Cohen's d in [0.3, 0.5): Weak effect, paper pivots to "diversity + multi-pocket
  docking" framing rather than "state conditioning" (PIVOT)
- Cohen's d < 0.3: State conditioning provides no meaningful benefit (NO-GO for
  current thesis; pivot to negative result or benchmark contribution)
- Probability of NO-GO (d < 0.3): ~20%

**Critical dependency:** Ablation C is blocked on the structural fix. Running it
with incorrect state labels produces uninformative results. Fix first, then ablate.

### C6: JCIM Is the Correct Primary Venue

All reviewers agree. Estimated acceptance probability: 55-65% conditional on
Tier 0 + Tier 1 completion.

- JCIM publishes kinase computational chemistry papers routinely (6+ in 2026)
- The retrospective enrichment benchmark question is squarely in scope
- Rolling submission avoids deadline pressure
- JCIM reviewers are domain experts who will appreciate structural biology nuance

### C7: Nature Computational Science Is Premature

All reviewers agree. Estimated acceptance probability: 15-25% past desk rejection.
Would require 4+ kinases, cross-architecture validation, potentially wet-lab
validation. Achievable post-JCIM as a follow-up, not as the first submission.

### C8: DiffSBDD Is Deferred to Paper 2

All reviewers agree, including mlrev who reversed from Round 1. Reasons:
- Python 3.10 requirement, 29 open / 0 closed GitHub issues
- CrossDocked2020 near-certain EGFR training data overlap
- 2-3 weeks of effort on an unmaintained codebase
- JCIM will not demand a 3D baseline; NeurIPS would
- REINVENT 4 provides a sufficient external baseline for JCIM

### C9: Incremental ABL1 Over Full Multi-Kinase Refactoring

All reviewers agree. Principal's file-by-file analysis (15 source files, 8 configs,
14 test files, 162 EGFR references) definitively shows that full generalization is
16-22 weeks while incremental ABL1 is 6-9 weeks (code) to 10-14 weeks (including
data curation per associate's 2x warning).

Technical approach: Add `target_gene: str = Field(default="EGFR")` to
`StructureRecord` (backward-compatible). Create ABL1-specific functions alongside
EGFR ones. Retrain VAE and MPNN separately per target.

### C10: REINVENT 4 as External Baseline

All reviewers agree. GNINA integration via ExternalProcess is the right approach.
8-15 days effort. DockStream is archived and does not support GNINA.

**Go/No-Go (week 7):** If integration fails after 2 weeks, fall back to REINVENT
with Vina scoring. An imperfect baseline is better than no baseline and a delay.

### C11: Pre-Registration Is a Free Differentiator

All reviewers agree. Timestamped git commit documenting ablation hypotheses,
success thresholds (Cohen's d >= 0.5/0.8), and analysis decisions. Hours of effort,
significant credibility signal.

### C12: ChemRxiv Preprint AFTER Structural Fixes

All reviewers agree: no preprint with known structural errors. A flawed preprint
can permanently damage a project's reputation. Week 8-10 is the consensus timing
(see Section 3.2 for residual disagreement on exact week).

### C13: Osimertinib Reference Leak Fix Is Trivial and Blocking

All reviewers agree. Remove osimertinib from `_REFERENCE_BINDERS`
(`baselines/scoring.py:63`). 15-minute fix. Publication-blocking if not done.

### C14: VAE Validity Metric Is Vacuous

All reviewers agree that 99.9% validity for a SELFIES-based model is guaranteed
by the representation, not the model. Replace with FCD (via fcd_torch),
reconstruction accuracy (exact SMILES match), and novelty. 3-5 days effort.

---

## 2. Resolved Disagreements

### D1 (from R2): 3D Baseline for JCIM -- RESOLVED

**Round 2 position:** mlrev argued for including DiffSBDD; progdir/associate
argued against.

**Round 3 resolution:** mlrev reversed position. "Given the structural annotation
issue, the DiffSBDD setup time, the CrossDocked2020 EGFR overlap concern, and
the 16-week timeline pressure, I now agree with progdir that DiffSBDD should be
deferred to Paper 2 or revision response."

**Outcome:** 5/5 agree. DiffSBDD deferred. REINVENT 4 is sufficient for JCIM.

### D2 (from R2): Enrichment and Pool Size -- NARROWED

**Round 2 position:** mlrev argued enrichment is "partially or wholly explained
by the larger, more diverse candidate pool." compbiorev argued EF@K is internally
normalized and not directly affected.

**Round 3 resolution:** Both sides converge on the following:
- The *count* confound (30 vs 461) does NOT directly inflate EF@K because the
  metric is internally normalized within each pipeline
- The *diversity* confound IS real: a more diverse candidate pool has higher
  probability of containing any given future drug analog
- Ablation C (unconditioned VAE generating 461 candidates) directly addresses the
  diversity confound
- PMO-style fixed oracle call budget addresses the compute fairness concern for
  the mean score comparison
- Both ablation C AND compute-matched comparison are mandatory

**Outcome:** Agreement on what to do (both experiments required). Residual
disagreement on interpretation is academic and does not affect the work plan.

---

## 3. Remaining Disagreements (Narrowed but Unresolved)

### D3: 3-State vs 4-State Model Preference

**Positions:**
- **3-state preferred** (3 reviewers: mlrev, associate, progdir): If 4ZAU is
  confirmed DFGin, drop to 3 states. Cleaner than defending a dubious 4th state.
  "Three well-characterized states are stronger than four states where one is
  dubious" (progdir).
- **4-state with disclosure preferred** (2 reviewers: compbiorev, principal):
  Keep 4 states with full mutant disclosure, structural justification
  (conformational RMSD >> mutational RMSD), and 2-state/4-state sensitivity
  analysis. Preserves KLIFS framework and clinical relevance of T790M/L858R.

**Evidence assessment:** The 3-state position has the numerical majority (3/5)
AND the practical advantage (simpler narrative, fewer attack surfaces). The
4-state position has stronger biological reasoning (T790M/L858R are clinically
the most important EGFR variants) and preserves the KLIFS framework.

**Resolution rule:** This is empirically resolvable. Verify 4ZAU first (1-2
hours). If 4ZAU is DFGin:
1. Adopt 3-state model as PRIMARY analysis (majority position)
2. Include 4-state (with mutant DFGout/aCout) as SENSITIVITY analysis in the
   supplement (satisfies compbiorev/principal)
3. Include 2-state (WT-only, DFGin/aCin + DFGin/aCout) as ADDITIONAL sensitivity
   analysis
4. The paper presents a 3-layer structural analysis: 2-state, 3-state (primary),
   4-state -- demonstrating robustness

This resolution satisfies both camps: the majority gets the cleaner primary
model, and the minority's clinical relevance argument is preserved in the
supplement. Both compbiorev and principal's specific conditions (disclosure,
RMSD analysis, sensitivity analysis) are included.

If 4ZAU is confirmed DFGout: keep 4 states (no disagreement in this scenario).

### D4: ABL1 Timeline Estimate

**Positions:**
- Principal: 6-9 weeks (code changes)
- Associate: 10-14 weeks (including data curation 2x factor)
- Others accept principal's estimate

**Resolution:** Associate's caution is well-motivated (ChEMBL data curation
for ABL1 is messier than EGFR, state annotation verification needed, GNINA
receptor preparation). Budget **8-10 weeks** as the planning estimate, with a
data quality go/no-go checkpoint at the end of week 1 of curation. If ABL1
data quality is insufficient after 3-5 days of curation, pivot to BRAF or SRC.

### D5: Preprint Timing (Week 6-8 vs 8-10)

**Positions:**
- CompBioRev/MLRev/Associate: Week 6-8 (after Tier 0 + Ablation C)
- ProgDir: Week 8-10 (delayed for structural fix cascade)
- Principal: Week 10-11

**Resolution:** ProgDir's reasoning is most compelling: structural fixes MUST be
complete before any public document, and the 2-week delay from the Round 2
recommendation reflects the discovered structural work. The preprint minimum
content checklist (corrected atlas, Ablation C result, scaffold-split MPNN, CIs,
preliminary ABL1) requires roughly 8 weeks to complete.

**Decision: Week 8-10.** This is early enough to establish priority (well within
the 6-month scooping window) and late enough to have credible content.

---

## 4. New Findings from Deliberation

### NF1: Docking Config Already Acknowledged 3iku Problem

Principal discovered that `configs/docking.yaml:24-25` contains a comment:
"3iku from the curated atlas is not EGFR; 3w2r is used instead for actual
docking." This means the docking results used the correct PDB file (3w2r), but
the metadata in `structures.py` and `features.py` was never corrected. The fix
cascade is shorter than feared for docking artifacts.

### NF2: VAE Retraining Is Only Needed for n_states Change

Principal and associate both independently confirmed: if keeping 4 states, no VAE
retraining is needed. The curated features describe idealized pocket geometries,
not specific PDB entries. Only a change in n_states (4 -> 3) invalidates the
checkpoint (GRU input dimension changes from embed_dim + 4 to embed_dim + 3).

### NF3: DFGout_aCout Candidates Contribute Minimally to Enrichment

Associate traced through `evaluation/retrospective.py`: all approved EGFR drugs
are annotated as `state: "DFGin_aCin"`. DFGout_aCout candidates (~25% of the 461
pool) likely contributed minimally to enrichment. Dropping them (3-state model)
should not significantly degrade the enrichment signal.

### NF4: StructureRecord Lacks target_gene Field

Associate identified a schema blocker for multi-kinase extension: `StructureRecord`
in `processing/models.py` has no `target_gene` field. Fix: add
`target_gene: str = Field(default="EGFR")` for backward compatibility. This is a
1-day task but must be done before ABL1 curation begins.

### NF5: Curated Features Not Directly Traceable to Measurements

Principal flagged that the specific numerical values in `features.py` (e.g.,
dfg_asp_phe_dist=10.2 for "3iku") are not directly traceable to any publication.
They are labeled "literature-curated" but the exact provenance is unclear.
Mitigation: compute actual geometric features from PDB coordinates using
BioPython for all remaining representative structures. If computed values match
curated values within 10-15%, the curation is validated.

### NF6: VAEConfig.n_states Is Already Configurable

Principal confirmed that `vae.py` uses `config.n_states` everywhere, not a
hardcoded 4. The 3-state switch requires only config changes and retraining,
not architecture modifications.

---

## 5. Consolidated Viability Assessment

| Dimension | CompBioRev | MLRev | Principal | Associate | ProgDir | Consensus |
|-----------|-----------|-------|-----------|-----------|---------|-----------|
| Novelty | 7/10 | (+2.0) | -- | -- | 9/10 | **8-9/10** |
| Current rigor | ~4/10 | (-3.0) | -- | -- | 4/10 | **4/10** |
| Rigor after fixes | 7/10 | 9.5 achievable | -- | -- | 7/10 | **7/10** |
| Feasibility | -- | -- | High | Viable w/ caution | 7/10 | **7/10** |
| Impact | -- | -- | -- | -- | 7/10 | **7/10** |
| Overall score | **7.0** | **6.5** | -- | -- | **7.5** | **~7.0** |

**Consensus assessment: 7.0/10.** Strong enough to pursue with discipline. Not
without risk. The novelty is definitively verified (9/10), but current scientific
rigor is only 4/10 (fixable to 7/10 with bounded work). The primary risk is
Ablation C (20% probability of NO-GO).

**Conditions for 8.5+:** Ablation C d >= 0.8, ABL1 replication positive, MPNN
scaffold R^2 >= 0.45, REINVENT 4 integration successful.

**Conditions for 5.0 (pivot territory):** Ablation C d < 0.3, MPNN scaffold
R^2 < 0.15, 4ZAU DFGin AND no DFGout representative findable (reduces to 2
states), ABL1 AND BRAF both negative.

---

## 6. Consolidated Scope Decision

### DEFINITIVELY IN (16 items, consensus 5/5)

| # | Item | Effort | Tier |
|---|------|--------|------|
| 1 | 4ZAU coordinate inspection | 2 hours | 0 |
| 2 | Structural annotations fix (3iku, 3W2R, 5D41) | 4-8 hours | 0 |
| 3 | 3-state vs 4-state decision + implementation | 1-2 days | 0 |
| 4 | Osimertinib reference leak fix | 15 minutes | 0 |
| 5 | MPNN scaffold + temporal split | 2-3 days | 0 |
| 6 | Bootstrap CIs + BEDROC | 0.5-1 day | 0 |
| 7 | Pre-registration document | 2-4 hours | 0 |
| 8 | Ablation C (unconditioned VAE) | 1-2 weeks | 1 |
| 9 | Compute-matched PMO comparison | 1-2 weeks | 1 |
| 10 | VAE metrics replacement (FCD + reconstruction) | 3-5 days | 1 |
| 11 | REINVENT 4 baseline on EGFR | 8-15 days | 1 |
| 12 | ABL1 incremental extension | 8-10 weeks | 1-2 |
| 13 | BRAF pipeline | 4-6 weeks | 2 |
| 14 | Scoring component ablation (Ablation E) | 2-3 days | 1 |
| 15 | 3-component scoring fairness check | 2-3 days | 1 |
| 16 | Dirichlet scoring sensitivity (1000+) | 3-5 days | 2 |

### PROBABLY IN (4 items, 4/5 agree)

| # | Item | Effort | Notes |
|---|------|--------|-------|
| 17 | Conformal prediction (TorchCP) | 5-7 days | Increasingly expected at JCIM in 2026 |
| 18 | Ablations F, G on EGFR | 1-2 weeks | Strengthens ablation story |
| 19 | Chemical space UMAP + property distributions | 3-5 days | Expected in 2026 generation papers |
| 20 | REINVENT 4 on ABL1 | 3-5 days | Incremental once EGFR works |

### DEFINITIVELY OUT (8 items, consensus 5/5)

| # | Item | Reason |
|---|------|--------|
| 21 | DiffSBDD 3D baseline | Unmaintained, CrossDocked overlap, not needed for JCIM |
| 22 | MET as 4th kinase | Contingent on data quality; 3 kinases sufficient |
| 23 | Within-method REINVENT ablation | Paper 2 / Nature Comp Sci material |
| 24 | Survival funnel (ADMETlab + AiZynthFinder) | Nice supplementary, not core claim |
| 25 | GIST water analysis | Enhancement, not required |
| 26 | Benchmark infrastructure (Docker, leaderboard) | NeurIPS 2027 target |
| 27 | OpenFE FEP validation | Paper 2 or beyond |
| 28 | Full multi-kinase generalization (>3 kinases) | 16-22 weeks, far too much scope |

---

## 7. Consolidated Go/No-Go Gates

| Gate | Week | Criterion | GO | CONDITIONAL GO | NO-GO |
|------|------|-----------|-----|----------------|-------|
| **G0** | 1 | Structural atlas verified | All PDB annotations correct | -- | Conceptual failure in state classification (<5% probability) |
| **G1** | 2 | MPNN scaffold-split R^2 | >= 0.35 | [0.20, 0.35]: frame as "supplementary signal" | < 0.20: drop MPNN from scoring (~10% probability) |
| **G2** | 4-5 | Ablation C Cohen's d | >= 0.5 (ideally >= 0.8) | [0.3, 0.5): reframe as diversity benefit | < 0.3: thesis not supported (~20% probability) |
| **G3** | 7 | REINVENT 4 GNINA integration | Produces 100+ valid docked molecules | Works but slow (reduce N) | Fails after 2 weeks: fall back to Vina scoring (~15% probability) |
| **G4** | 8 | ABL1 enrichment signal | EF@10 > 1.0 | Positive direction but wide CIs | < 1.0: investigate, may drop ABL1 (~25% probability) |
| **G5** | 12 | Cross-kinase consistency | 2/3+ kinases positive | 1/3 strong + informative negatives | 0/3 positive: pivot to negative result (~10% probability) |

---

## 8. Consolidated Timeline (18 Weeks to JCIM Submission)

```
Week  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18
      [Phase 0: Fixes          ]
      G0--+  G1-+
           |    |
           [Ablation C..........]
           |         G2-+
           [Oracle budget.......]
           [REINVENT 4 setup............]
           |                    G3-+
           [ABL1 data curation + code...........]
           |                         [ABL1 pipeline.....]
           |                              G4-+
           |                                  [BRAF...........]
           |                                       G5-+
           |                              [ChemRxiv....]
           |                                        [Analysis + Figs.......]
           |                                              [Manuscript...............]
           |                                                              [Buffer...]
```

**Phase 0 (Weeks 0-2):** All structural fixes, MPNN scaffold split, bootstrap CIs,
pre-registration. Nothing else starts until Phase 0 completes.

**Phase 1 (Weeks 2-8):** Core experiments. Ablation C (weeks 2-5), REINVENT 4
(weeks 2-7), compute-matched comparison (weeks 2-5), ABL1 codebase extension
(weeks 2-8). Gate G2 (Ablation C) at week 4-5 determines narrative direction.

**Phase 2 (Weeks 8-12):** Multi-kinase execution. ABL1 pipeline (weeks 8-10),
BRAF (weeks 9-12). ChemRxiv preprint at weeks 8-10. Analysis and supplementary
experiments.

**Phase 3 (Weeks 12-18):** Writing, figures, supplementary, revision buffer.
JCIM submission target: mid-August 2026.

---

## 9. Publication Strategy (Consensus)

### Paper 1: JCIM (Target: August 2026)

**Title candidate:** "Conformational State-Conditioned Molecular Generation
Improves Retrospective Enrichment Across Kinase Targets"

**Core claim:** Discrete conformational state labels improve retrospective
enrichment for kinase inhibitor molecular generation, validated across 2-3
kinases with ablation-controlled evidence and compute-matched external baselines.

**Required content:** Corrected structural atlas, scaffold-split MPNN, bootstrap
CIs, BEDROC, Ablation C, compute-matched comparison, REINVENT 4 baseline, ABL1
extension, pre-registration.

### Preprint: ChemRxiv (Target: Week 8-10, ~June 2026)

**Minimum content:** Corrected atlas, Ablation C result, scaffold-split MPNN,
CIs, preliminary ABL1, compute-matched EGFR comparison. "Full multi-kinase paper
forthcoming."

### Paper 2: Nature Comp Sci or NeurIPS 2027 E&D (Future)

Full multi-kinase generalization (4+ kinases), 3D baselines (DiffSBDD/MolPilot),
cross-architecture validation (REINVENT within-method ablations), benchmark
infrastructure, Docker reproducibility.

---

## 10. Risk Register (Consolidated)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 4ZAU is DFGin (3-state needed) | 40% | Medium (2.5 days) | Budgeted in Phase 0; 3-state is publishable |
| MPNN scaffold R^2 < 0.20 | 10% | Medium | Drop MPNN; GNINA + proxy scoring |
| Ablation C d < 0.3 | 20% | High | Pivot to negative result or benchmark paper |
| REINVENT 4 GNINA integration fails | 15% | Low | Fall back to Vina scoring |
| ABL1 enrichment < 1.0 | 25% | Medium | EGFR-only paper with honest disclosure |
| ABL1 data curation takes 2x | 40% | Medium | Data quality checkpoint at day 3 |
| Scooped before preprint | 10-15% | High | Accelerate preprint to week 8 |
| Single-researcher capacity bottleneck | 60% | Medium | Ruthless scope discipline; cut PROBABLY IN items |

---

## 11. Inputs for Round 4 (Final Implementation Plan)

The Round 4 implementation plan will synthesize all three rounds into a single
actionable document. Based on this deliberation, the key decisions are:

1. **18-week timeline** to JCIM submission (mid-August 2026)
2. **16 mandatory items** organized in 3 phases with 5 go/no-go gates
3. **JCIM primary venue** with ChemRxiv preprint at week 8-10
4. **3-state model as primary** (if 4ZAU confirmed DFGin) with 2-state and
   4-state sensitivity analyses in supplement
5. **Ablation C at week 4-5** as the thesis gate (d >= 0.5 for GO)
6. **Incremental ABL1** (8-10 weeks) over full multi-kinase refactoring
7. **DiffSBDD, MET, GIST, benchmark infra definitively OUT**
8. **Project viability: 7.0/10** -- strong enough to pursue, requires discipline

The panel's work is complete. Round 4 is the orchestrator's sole responsibility.
