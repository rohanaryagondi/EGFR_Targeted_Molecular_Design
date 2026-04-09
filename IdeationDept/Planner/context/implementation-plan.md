---
agent: Orchestrator (Panel Chair)
round: 4
date: 2026-04-09
type: directive
scope: final-implementation-plan
panel:
  - Sr. Journal Reviewer -- Comp Bio (compbiorev)
  - Sr. Journal Reviewer -- ML & AI (mlrev)
  - Principal Computational Scientist (principal)
  - Associate Research Scientist (associate)
  - Program Director / Chief Scientist (progdir)
process:
  - "Round 1: Independent review (5 reviewers, parallel)"
  - "Round 2: Deep verification research (150+ searches, 15+ source files)"
  - "Round 3: Deliberation (cross-reviewer response, consensus building)"
  - "Round 4: Final implementation plan (this document)"
---

# StateBind: Final Implementation Plan

## Executive Summary

**The publication strategy in five sentences.** StateBind tests whether discrete
conformational state labels improve molecular generation for kinase inhibitors.
The project has a definitively novel contribution (verified by 70+ searches
across two reviewers), a compelling retrospective enrichment framework (EF@10 of
4.95-7.72 for state-aware vs 0.47-0.79 for static), and publication-quality
infrastructure (646 tests, 91 source files). However, six critical issues must
be fixed before any submission: structural annotation errors in the conformational
atlas, MPNN random-split evaluation, compute-unfair comparison, missing
confidence intervals, vacuous validity metrics, and a temporal data leak. The
plan targets JCIM submission in 18 weeks (mid-August 2026), with a ChemRxiv
preprint at week 8-10 to establish priority, contingent on passing five go/no-go
gates -- the most critical being Ablation C (conditioned vs unconditioned VAE)
at week 4-5.

**Project viability: 7.0/10** (panel consensus). Strong enough to pursue with
discipline. Novelty is 9/10; current scientific rigor is 4/10 but fixable to
7/10 with bounded work. Primary risk: Ablation C (20% probability of NO-GO).

---

## 1. Verified Claims

These facts were independently verified through internet research, codebase
inspection, and cross-reviewer confirmation during Rounds 1-2.

### 1.1 Novelty: VERIFIED

No published paper as of April 2026 conditions molecular generation on discrete
conformational state labels and benchmarks retrospective enrichment. Confirmed
by 70+ combined searches across compbiorev (40+) and progdir (30+). Seven
potential competitors analyzed (DynamicBind, Apo2Mol, DynamicFlow, FLOWR,
PLACER, PocketXMol, CSDesign) -- all use fundamentally different mechanisms.

**Correct framing:** "First systematic benchmark evaluating whether discrete
conformational state-conditioning improves molecular generation for kinases."
Not "first dynamics-aware design" (DynamicBind predates this in concept).

### 1.2 Competitive Landscape

| Competitor | Overlap | Risk | Status |
|-----------|---------|------|--------|
| Volkamer group (Charite Berlin) | High (KLIFS-based kinase analysis) | Closest future competitor | No state-conditioned generation published |
| PocketXMol (Cell, Feb 2026) | Medium (pocket-conditioned foundation model) | Different mechanism (3D geometry, not discrete states) | Published |
| DynamicBind (Nat Commun, 2024) | Low (predicts structure, doesn't condition generation) | Different task | Published |
| PLACER (PNAS, 2025) | Low (conformational ensembles) | Not molecular generation | Published |

**Scooping risk:** 15-20% within 6 months, 30-40% within 12 months. ChemRxiv
preprint at week 8-10 mitigates.

### 1.3 Technical Facts Verified in Codebase

| Fact | Location | Verification |
|------|----------|-------------|
| MPNN uses random split | `affinity_dataset.py:388-390` | `np.random.permutation` confirmed by principal + mlrev |
| VAE validity from SELFIES | `vae.py:425-532` | Autoregressive generation confirmed; SELFIES guarantees validity |
| Osimertinib in reference set | `baselines/scoring.py:63` | Temporal leak confirmed |
| 3iku is not EGFR | `structures.py:176-187` | PDB 3iku is ParM (E. coli); docking.yaml already uses 3w2r |
| 3W2R listed as WT | `structures.py:189-199` | PDB 3W2R is T790M/L858R double mutant |
| 5D41 listed as WT | `structures.py:216-225` | PDB 5D41 is L858R/T790M double mutant |
| 4ZAU classified DFGout | `structures.py:203-213` | Osimertinib is Type I covalent; 4ZAU likely DFGin |
| No WT EGFR DFGout exists | PDB search (compbiorev) | All DFGout structures carry T790M and/or L858R |
| Curated features are literature-derived | `features.py` | Not computed from PDB coordinates; internally consistent with state archetypes |
| VAEConfig.n_states is configurable | `vae.py:83-84` | Uses `config.n_states` everywhere; 3-state needs only config change + retrain |
| docking.yaml acknowledges 3iku issue | `configs/docking.yaml:24-25` | Comment: "3iku is not EGFR; 3w2r used instead" -- knowledge not propagated |

### 1.4 Tool Availability Verified

| Tool | Status | Key Constraint |
|------|--------|---------------|
| ADMETlab 3.0 | Available, free, 119 endpoints | Service instability; retry logic needed |
| AiZynthFinder 4.4.1 | Available, Python 3.10-3.12 | CPU-only, ~10s/molecule |
| REINVENT 4 | Available, GNINA integration feasible | Custom ExternalProcess plugin needed, 8-15 days |
| fcd_torch | pip installable | Straightforward FCD computation |
| TorchCP | Available, PyTorch-native | GNN support, GPU acceleration |
| DiffSBDD | Available but problematic | Python 3.10 only, 29 open/0 closed issues, CrossDocked2020 overlap |
| RAscore | DEAD | Python 3.7-3.8 only; use AiZynthFinder instead |
| MolPilot | Available, ICML 2025 | VRAM undocumented, likely needs H200 |
| FLOWR | DROPPED | Unmaintained, 40GB VRAM, redirects to FLOWR.root |

---

## 2. Priority-Ordered Work Items

### Phase 0: Structural & Methodological Fixes (Weeks 0-2)

**Nothing else starts until Phase 0 is complete.** These are publication-blocking
issues that invalidate downstream results if unfixed.

#### P0: Verify 4ZAU DFG Conformation

- **Effort:** 2 hours
- **Method:** Download 4ZAU.pdb. Measure in PyMOL/ChimeraX:
  1. DFG-Asp831/Phe832 Ca-Ca distance (DFGin: ~5-6A; DFGout: ~9-12A)
  2. Phe832 position relative to ATP site (DFGin: under P-loop; DFGout: flipped)
  3. K745-E762 salt bridge NZ-OE distance (aCin: <4A; aCout: >6A)
- **Outcome:** Determines 3-state vs 4-state model for the rest of the project
- **Dependencies:** None. First task.
- **Go/No-Go:**
  - DFGout confirmed: Keep 4 states with mutant disclosure (no disagreement)
  - DFGin confirmed (expected): Adopt 3-state model as primary analysis. See P1.

#### P1: Fix Structural Annotations

- **Effort:** 4-8 hours (4-state) or 2-2.5 days (3-state switch)
- **Files affected (4-state fix only):**
  - `processing/structures.py:183-184` -- fix 3iku PDB ID (remove or replace with 3IKA + T790M annotation)
  - `processing/structures.py:196` -- fix 3W2R `mutations_present=[]` to `["T790M", "L858R"]`
  - `processing/structures.py:220` -- fix 5D41 `mutations_present=[]` to `["L858R", "T790M"]`
  - `structure/features.py:212-225` -- remove 3iku entry or replace with 3IKA features
  - `generation/conditioning.py:96` -- fix representative_pdb="3iku" reference
  - Tests: `test_structure.py:146,158,163`
- **Additional files for 3-state switch:**
  - `processing/structures.py:201-226` -- remove/reclassify 4ZAU, 5D41 from DFGout_aCout
  - `structure/features.py:242-269` -- remove DFGout_aCout features
  - `generation/conditioning.py:115-136` -- remove DFGout_aCout PocketCondition
  - `configs/vae.yaml`, `vae_pre2010.yaml`, `vae_pre2015.yaml` -- n_states: 3
  - `ml/vae_dataset.py:41-46` -- remove DFGout_aCout from DEFAULT_STATE_MAPPING
  - `ml/vae.py:84` -- n_states default to 3
  - `configs/docking.yaml:30` -- remove DFGout_aCout entry
  - 8 test files, 11 occurrences of DFGout_aCout or n_states=4
- **VAE retraining required ONLY if n_states changes** (checkpoint dimensions incompatible)
  - Training time: 15-30 min on H200
  - Then re-run generation + scoring + evaluation pipeline
- **Dependencies:** P0 result
- **Go/No-Go (Gate G0, end of week 1):**
  - All PDB annotations verified against PDB records: PROCEED
  - A fundamental problem making the state classification scheme invalid: STOP AND RETHINK (<5% probability)

#### P2: Fix Osimertinib Reference Leakage

- **Effort:** 15 minutes
- **File:** `baselines/scoring.py:63` -- remove osimertinib from `_REFERENCE_BINDERS`
- **Impact:** Removes temporal data leak in baseline scoring
- **Dependencies:** None. Can run in parallel with P1.

#### P3: MPNN Scaffold + Temporal Split

- **Effort:** 2-3 days
- **File:** `ml/affinity_dataset.py` -- replace `np.random.permutation` at line 388-390
- **Implementation:**
  - Add `scaffold_split()` using RDKit `MurckoScaffold.MakeScaffoldGeneric`
  - Group molecules by Bemis-Murcko scaffold
  - Split scaffolds (not molecules) into train/val/test
  - Keep backward compatibility: `split_type: str = "random"` default
  - Also add `temporal_split()` using activity year
- **Expected R^2 degradation:** 0.69 (random) -> 0.45-0.55 (scaffold)
- **Dependencies:** None. Can run in parallel with P1.
- **Go/No-Go (Gate G1, end of week 2):**
  - Scaffold R^2 >= 0.35: MPNN is credible scoring component (GO)
  - R^2 in [0.20, 0.35]: Frame MPNN as "supplementary signal," increase GNINA weight (CONDITIONAL GO)
  - R^2 < 0.20: Drop MPNN from scoring; use GNINA + descriptors + state_specificity (NO-GO, ~10%)

#### P4: Bootstrap Confidence Intervals + BEDROC

- **Effort:** 0.5-1 day
- **Implementation:**
  - 10,000-fold BCa bootstrap on EF@10, BEDROC(alpha=20), mean scores
  - Use `rdkit.ML.Scoring.Scoring.CalcBEDROC()` for BEDROC
  - Report: point estimate [95% CI lower, upper]
- **Dependencies:** None. Can run in parallel with P1 and P3.
- **Go/No-Go:** If static 95% CI overlaps state-aware 95% CI on enrichment,
  the central claim is statistically unsupported. Not fatal (CI width may be
  large due to small N) but must be disclosed honestly.

#### P5: Pre-Registration Document

- **Effort:** 2-4 hours
- **Content:**
  - Ablation C hypothesis: "State-conditioned VAE produces higher EF@10 than unconditioned VAE"
  - Success threshold: Cohen's d >= 0.5 (GO), d >= 0.8 (STRONG GO)
  - Analysis plan: bootstrap resampling, BEDROC with alpha=20, BCa CIs
  - Covariates: pool size, chemical diversity (#Circles), FCD
- **Method:** Timestamped git commit before any ablation experiments
- **Dependencies:** All other Phase 0 items should be decided first

### Phase 1: Core Experiments (Weeks 2-8)

#### P6: Ablation C -- Unconditioned VAE

- **Effort:** 1-2 weeks
- **THE THESIS TEST.** If an unconditioned VAE (same architecture, no state
  labels) achieves the same enrichment, state conditioning provides no value.
- **Implementation:**
  - Use n_states=1 with all molecules assigned to state 0 (constant one-hot [1.0])
  - This is mathematically equivalent to no conditioning (constant input adds
    no information) while preserving the same architecture and parameter count
  - Train for the same number of epochs with the same hyperparameters
  - Generate the same total number of candidates (matching conditioned total)
  - Score with the same unified scoring function
  - Compute EF@10, BEDROC with bootstrap CIs
  - Report across 3+ random seeds
  - Compute Cohen's d between conditioned and unconditioned enrichment distributions
- **CRITICAL DEPENDENCY:** BLOCKED on P1 (structural fix). Running ablation
  with incorrect state labels is uninformative. Fix first, then ablate.
- **Go/No-Go (Gate G2, week 4-5):**
  - d >= 0.8: Strong effect. Paper's thesis robustly supported. (STRONG GO)
  - d in [0.5, 0.8): Moderate effect. Publishable with tempered claims. (GO)
  - d in [0.3, 0.5): Weak effect. Pivot to "diversity + multi-pocket docking"
    framing rather than "state conditioning drives enrichment." (PIVOT)
  - d < 0.3: State conditioning provides no meaningful benefit. Pivot to negative
    result or benchmark-only contribution. (NO-GO, ~20% probability)
- **Note:** This ablation remains valid even with partially wrong state labels.
  We test "does ANY conditioning help?" not "are the labels correct?" If
  conditioned beats unconditioned even with imperfect labels, it would perform
  even better with correct labels.

#### P7: Compute-Matched PMO Comparison

- **Effort:** 1-2 weeks
- **Purpose:** Address the 30 vs 461 candidate ratio (15:1 oracle call imbalance)
- **Implementation:**
  - Define "oracle call" as one GNINA docking evaluation (~30s per molecule)
  - Fix budget at N=500 oracle calls per pipeline
  - Run static pipeline with 500 docked candidates (generate more analogs)
  - Run state-aware pipeline with 500 docked candidates
  - Report AUC of top-10 average score vs oracle calls
  - Use PMO benchmark framework (Gao et al., 2022) reference implementations
- **Dependencies:** Phase 0 complete
- **Go/No-Go:** State-aware AUC >= static AUC under equal budget. If not, the
  enrichment advantage may be explained by sample diversity.

#### P8: VAE Metrics Replacement

- **Effort:** 3-5 days
- **Replace:** 99.9% validity (vacuous for SELFIES)
- **With:**
  - FCD via `fcd_torch` (distributional quality, FCD < 1.0 is generally good)
  - Reconstruction accuracy (encode -> decode -> exact SMILES match rate)
  - Novelty (fraction of generated molecules not in training set)
  - Internal diversity (Tanimoto-based or #Circles if time permits)
- **Dependencies:** Phase 0 complete

#### P9: REINVENT 4 Baseline on EGFR

- **Effort:** 8-15 days
- **Purpose:** External baseline using the same scoring function (GNINA docking)
  but without state conditioning
- **Implementation:**
  - Install REINVENT 4 (`pip install reinvent`)
  - Write custom ExternalProcess component wrapping GNINA command-line
  - Configure REINVENT to optimize against single EGFR pocket (1M17, same as static)
  - Generate candidates, score with the same unified scoring function
  - Compare enrichment: StateBind state-aware vs REINVENT (no state labels)
- **Dependencies:** Phase 0 complete. Can run in parallel with P6.
- **Go/No-Go (Gate G3, week 7):**
  - REINVENT produces 100+ valid docked molecules with GNINA scores: GO
  - Integration works but slow (>10 min/mol): Reduce N, still include (CONDITIONAL GO)
  - GNINA plugin fails after 2 weeks: Fall back to REINVENT + Vina scoring (NO-GO for GNINA integration, ~15%)

#### P10: Scoring Component Ablation (Ablation E)

- **Effort:** 2-3 days
- **Purpose:** Identify which scoring component drives enrichment
- **Implementation:**
  - Systematically zero each component weight: GNINA, MPNN, drug-likeness, ADMET
  - Re-rank candidates with each ablated scoring function
  - Report EF@10 with CIs for each ablation
- **Why this matters:** If GNINA (physics-based) drives enrichment, the result is
  robust. If MPNN (learned) drives it, data leakage concerns increase.
- **Dependencies:** Phase 0 complete (corrected scores needed)

#### P11: 3-Component Scoring Fairness Check

- **Effort:** 2-3 days
- **Purpose:** Show enrichment survives without the state_specificity component
  (which directly encodes state information)
- **Implementation:** Re-run scoring with state_specificity weight = 0. If
  enrichment persists, the advantage comes from multi-pocket docking diversity,
  not from the state-aware scoring component.
- **Dependencies:** Phase 0 complete

#### P12: Multi-Kinase Extension -- ABL1 (Incremental)

- **Effort:** 8-10 weeks (largest single item; critical path bottleneck)
- **Approach:** Incremental addition alongside EGFR with backward-compatible defaults.
  NOT full multi-kinase refactoring (16-22 weeks).
- **Steps:**
  1. **Schema update (1 day):** Add `target_gene: str = Field(default="EGFR")` to
     `StructureRecord` in `processing/models.py`. Backward-compatible.
  2. **ABL1 data curation (3-5 days):** ChEMBL ABL1 (CHEMBL1862) bioactivity data.
     IC50 assays, single protein, exact measurements. Curate ~100-500 compounds.
     Data quality checkpoint at day 3. If insufficient, consider BRAF or SRC.
  3. **ABL1 structures (2-3 days):** PDB structures across conformational states.
     ABL1 has genuine DFGout structures (imatinib-bound, PDB 1IEP). DFGin
     (dasatinib, PDB 2GQG). Cross-reference with KLIFS. VERIFY annotations
     (lesson from EGFR errors).
  4. **ABL1 features + conditioning (2-3 days):** ABL1-specific pocket descriptors
     in `features.py` or new file. ABL1 pocket conditions in `conditioning.py`.
     Same 3-state (or 4-state) framework with different pocket geometries.
  5. **ABL1 model training (2-3 days):** Separate VAE + MPNN trained on ABL1 data.
     Scaffold-split MPNN from day 1.
  6. **ABL1 pipeline execution (2-3 days):** Generate, score, compute enrichment.
     GNINA docking against ABL1 receptor structures.
  7. **ABL1 retrospective evaluation (1-2 days):** Drug timeline: imatinib (2001),
     dasatinib (2006), nilotinib (2007), bosutinib (2012), ponatinib (2012),
     asciminib (2021). Pre-2010 cutoff: 3 drugs reference, 3 drugs "future."
     Better retrospective test than EGFR.
  8. **Cross-kinase analysis (1-2 days):** Compare EGFR vs ABL1 enrichment patterns.
- **Known blockers:**
  - `StructureRecord` lacks `target_gene` field (associate finding)
  - ChEMBL ABL1 data curation is messier than EGFR (assay heterogeneity, different constructs)
  - State annotations must be carefully verified (lesson from EGFR)
  - GNINA receptor preparation for each ABL1 structure: 2-3 days
- **Dependencies:** Phase 0 complete (corrected codebase needed). ABL1 data
  curation (steps 1-4) can start in parallel with Phase 0.
- **Go/No-Go (Gate G4, week 8):**
  - ABL1 EF@10 > 1.0 for state-aware: Multi-kinase generalization alive (GO)
  - Positive direction but wide CIs: Report honestly; two kinases same direction
    is more convincing than one with tight CIs (CONDITIONAL GO)
  - ABL1 EF@10 < 1.0: Investigate why. If data quality issue, disclose.
    If genuine no-effect, report as important negative result. (NO-GO for
    ABL1; proceed with BRAF as critical second kinase, ~25% probability)

### Phase 2: Multi-Kinase & Strengthening (Weeks 8-12)

#### P13: BRAF Pipeline

- **Effort:** 4-6 weeks
- **Purpose:** Third kinase makes the pattern convincing
- **Approach:** Same incremental method as ABL1. BRAF follows ABL1 template.
- **Dependencies:** P12 (ABL1 proves the incremental approach works)
- **Go/No-Go (Gate G5, week 12):**
  - 2/3 or 3/3 kinases show positive enrichment advantage: Paper writes itself (GO)
  - 1/3 strong advantage + informative negatives: Report mixed picture honestly.
    Publishable at JCIM. (CONDITIONAL GO)
  - 0/3 positive: Kill the paper as currently conceived. Pivot to negative
    result: "Discrete state labels do not consistently improve molecular
    generation across kinases." Still publishable at JCIM. (NO-GO, ~10%)

#### P14: Dirichlet Scoring Sensitivity

- **Effort:** 3-5 days
- **Purpose:** Show enrichment is robust to scoring weight perturbation
- **Implementation:** Sample 1,000+ random weight vectors from Dirichlet
  distribution. Re-rank candidates with each. Report enrichment distribution.
- **Dependencies:** Phase 0 complete

#### P15: Chemical Space UMAP + Property Distributions

- **Effort:** 3-5 days
- **Purpose:** Visualize generated molecules in chemical space. Compare MW, LogP,
  QED, TPSA distributions of generated vs training molecules.
- **Implementation:** UMAP on Morgan fingerprints. KS test per property. MMD for
  multivariate comparison. Color by state, overlay approved drug positions.
- **Dependencies:** Phase 0 complete

#### P16: Conformational Selection Narrative

- **Effort:** 0 compute, 1-2 days writing
- **Purpose:** Frame the paper around conformational selection biology:
  "State labels encode which conformations are populated under specific mutation
  and drug resistance contexts. A pocket geometry tells you what shape to design
  for; a state label tells you which shapes matter for a given clinical scenario."
- **Differentiator vs PocketXMol:** PocketXMol uses 3D pocket geometry alone.
  StateBind adds the dimension of *population dynamics* -- which states are
  clinically relevant. This framing is zero-cost and unique.

### Phase 2.5: Probably-In Items (Weeks 10-12, If Time)

#### P17: Conformal Prediction via TorchCP

- **Effort:** 5-7 days
- **Purpose:** Calibrated uncertainty intervals for MPNN predictions
- **Expected at JCIM in 2026.** Strong signal of methodological rigor.

#### P18: Additional Ablations (F, G) on EGFR

- **Effort:** 1-2 weeks total
- **Ablation F:** Fingerprint radius sensitivity (Morgan radius 2 vs 3)
- **Ablation G:** Docking exhaustiveness sensitivity

#### P19: REINVENT 4 on ABL1

- **Effort:** 3-5 days
- **Purpose:** Cross-architecture validation on second kinase
- **Dependencies:** P9 (REINVENT 4 working on EGFR) and P12 (ABL1 pipeline)

### Phase 3: Writing & Submission (Weeks 12-18)

#### P20: ChemRxiv Preprint (Weeks 8-10)

- **Minimum content checklist:**
  - [ ] Structural atlas corrected and disclosed (3-state if applicable)
  - [ ] EGFR retrospective enrichment with BCa bootstrap CIs + BEDROC
  - [ ] Ablation C result with effect size (Cohen's d)
  - [ ] MPNN scaffold-split R^2 (both splits reported)
  - [ ] Compute-matched comparison (PMO-style) on EGFR
  - [ ] At least preliminary ABL1 result
  - [ ] FCD scores replacing validity as quality metric
  - [ ] Statement: "Full multi-kinase paper with external baselines in preparation"
- **Venue:** ChemRxiv (not bioRxiv). ACS explicitly permits preprinted manuscripts
  for JCIM submission.
- **CRITICAL:** No preprint before structural atlas is fully corrected.

#### P21: Full Manuscript (Weeks 12-18)

- **Target venue:** JCIM (Journal of Chemical Information and Modeling)
- **Title candidate:** "Conformational State-Conditioned Molecular Generation
  Improves Retrospective Enrichment Across Kinase Targets"
- **Core claim:** Discrete conformational state labels improve retrospective
  enrichment for kinase inhibitor molecular generation, validated across 2-3
  kinases with ablation-controlled evidence and compute-matched external baselines.
- **Structure:**
  - Table 1: Representative structures (PDB IDs, mutations, resolution, DFG/aC state)
  - Honest disclosure of mutant DFGout structures in Methods + Limitations
  - Three-layer enrichment presentation: original, compute-matched, ablation
  - Multi-kinase results with per-kinase CIs
  - RMSD analysis: conformational change >> mutational perturbation
  - 2-state/3-state/4-state sensitivity analysis in supplement
  - Pre-registration timestamped before ablation experiments
- **Figures (key):**
  - Figure 1: Conformational state landscape with UMAP-embedded generated
    molecules colored by state, overlaid with approved drug positions
  - Figure 2: Retrospective enrichment (EF@10, BEDROC) with bootstrap CIs across
    kinases
  - Figure 3: Ablation C -- conditioned vs unconditioned enrichment
  - Figure 4: Compute-matched PMO comparison
  - Figure 5: Scoring component ablation (which component drives enrichment)
- **Revision buffer:** 2 weeks (weeks 17-18) for internal review and revision

---

## 3. Timeline (18 Weeks)

### Week-by-Week Milestones

| Week | Phase | Activities | Gate |
|------|-------|-----------|------|
| **0** | Setup | Read implementation plan. Create tracking system. | -- |
| **1** | Phase 0 | 4ZAU coordinate check (P0). Fix 3iku/3W2R/5D41 annotations (P1). Fix osimertinib leak (P2). 3-state vs 4-state decision. Start MPNN scaffold split (P3). Start bootstrap CIs (P4). | **G0:** Structural atlas verified |
| **2** | Phase 0 | Complete MPNN scaffold split. Re-evaluate R^2. Complete bootstrap CIs + BEDROC. VAE retrain (if 3-state). Pre-registration document (P5). | **G1:** MPNN scaffold R^2 >= 0.35 |
| **3** | Phase 1 | Begin Ablation C (P6). Begin compute-matched comparison (P7). Begin REINVENT 4 setup (P9). Start ABL1 data curation (P12, steps 1-4). | -- |
| **4** | Phase 1 | Ablation C training + generation. Continue REINVENT 4. Continue ABL1 curation. Replace VAE validity metrics (P8). | -- |
| **5** | Phase 1 | Ablation C results analyzed. Scoring component ablation (P10). 3-component fairness check (P11). Continue ABL1 codebase. | **G2:** Ablation C Cohen's d >= 0.5 |
| **6** | Phase 1 | ABL1 model training (P12, step 5). REINVENT 4 GNINA integration complete. Continue compute-matched comparison. | -- |
| **7** | Phase 1 | ABL1 pipeline execution (P12, step 6). REINVENT 4 baseline on EGFR complete. Compute-matched PMO finalized. | **G3:** REINVENT 4 produces valid docked molecules |
| **8** | Phase 2 | ABL1 retrospective enrichment + CIs (P12, step 7). Begin BRAF data curation (P13). Begin ChemRxiv preprint draft (P20). | **G4:** ABL1 enrichment > 1.0 |
| **9** | Phase 2 | Continue BRAF. Conformal prediction (P17, if time). Dirichlet sensitivity (P14). | -- |
| **10** | Phase 2 | BRAF pipeline execution. Chemical space UMAP (P15). Submit ChemRxiv preprint. | Preprint submitted |
| **11** | Phase 2 | BRAF enrichment + CIs. Cross-kinase analysis. Additional ablations (P18, if time). FCD scores per state. | -- |
| **12** | Phase 2 | Cross-kinase consistency check. Final figure generation. Conformational narrative (P16). | **G5:** >= 2/3 kinases positive |
| **13** | Phase 3 | Full manuscript draft: Methods + Results. | -- |
| **14** | Phase 3 | Full manuscript: Discussion + Supplementary. | -- |
| **15** | Phase 3 | Internal review. Co-author feedback. | -- |
| **16** | Phase 3 | Revisions. Final figures. Supplementary tables. | -- |
| **17** | Phase 3 | Code repository cleanup. Data availability statement. | -- |
| **18** | Phase 3 | **JCIM submission.** Target: mid-August 2026. | SUBMITTED |

### Timeline Visual

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
           [ABL1 curation + code............]
           |                         [ABL1 pipeline....]
           |                              G4-+
           |                                  [BRAF...........]
           |                                       G5-+
           |                              [ChemRxiv....]
           |                                        [Analysis........]
           |                                              [Manuscript...............]
           |                                                              [Buffer...]
```

### Parallel Execution (Single Researcher)

Since this is a 1-person project, true parallelism is limited. Interleaving
strategy for weeks 1-2:

- **Stream 1 (primary):** Structural annotation fix (P1) -- 2-3 days
- **Stream 2 (parallel):** MPNN scaffold split (P3) -- 2-3 days (independent of P1)
- **Stream 3 (parallel):** Bootstrap CIs (P4) -- 0.5-1 day (independent of P1, P3)

After week 2: execute in priority order with interleaving. ABL1 data curation
(long-running, low intensity) runs in background while Ablation C (compute-intensive,
short bursts) uses GPU time.

---

## 4. Resource Allocation

### Compute (Yale Bouchet HPC)

| Task | GPU Type | GPU-Hours | Partition |
|------|----------|-----------|-----------|
| VAE retrain (3-state) | H200 | 0.5 | gpu_h200 or gpu_devel |
| Ablation C VAE training (3+ seeds) | H200 | 1.5 | gpu_h200 |
| Ablation C generation + scoring | H200 | 4-8 | gpu_h200 |
| MPNN scaffold-split retraining | RTX 5000 Ada | 1-2 | gpu |
| ABL1 VAE training | H200 | 0.5 | gpu_h200 |
| ABL1 MPNN training | RTX 5000 Ada | 1-2 | gpu |
| BRAF models | H200 | 1 | gpu_h200 |
| GNINA docking (all kinases) | CPU | 100-200 CPU-hours | day |
| REINVENT 4 runs | H200 | 8-16 | gpu_h200 |
| **Total GPU** | | **~20-35 GPU-hours** | |
| **Total CPU** | | **~200-400 CPU-hours** | |

Cluster allocation: `-A pi_mg269`, priority queue `-p priority -A prio_gerstein`
for time-sensitive jobs.

### Person-Time (Single Researcher)

| Phase | Weeks | Person-Weeks | Notes |
|-------|-------|-------------|-------|
| Phase 0: Fixes | 0-2 | 2 | Blocking; highest intensity |
| Phase 1: Core experiments | 2-8 | 6 | Interleaved with ABL1 curation |
| Phase 2: Multi-kinase + strengthening | 8-12 | 4 | BRAF + analysis |
| Phase 3: Writing + submission | 12-18 | 6 | Includes revision buffer |
| **Total** | | **18 person-weeks** | |

---

## 5. Go/No-Go Gates

| Gate | Week | Criterion | GO | CONDITIONAL GO | NO-GO | P(NO-GO) |
|------|------|-----------|-----|----------------|-------|----------|
| **G0** | 1 | Structural atlas verified | All annotations match PDB | -- | State classification scheme fundamentally invalid | <5% |
| **G1** | 2 | MPNN scaffold-split R^2 | >= 0.35 | [0.20, 0.35]: "supplementary signal" | < 0.20: drop MPNN from scoring | ~10% |
| **G2** | 4-5 | Ablation C Cohen's d | >= 0.5 (ideally >= 0.8) | [0.3, 0.5): reframe as diversity benefit | < 0.3: thesis not supported | ~20% |
| **G3** | 7 | REINVENT 4 integration | 100+ valid docked molecules | Slow but functional | Fails after 2 weeks: Vina fallback | ~15% |
| **G4** | 8 | ABL1 enrichment | EF@10 > 1.0 | Positive direction, wide CIs | < 1.0: investigate; may drop ABL1 | ~25% |
| **G5** | 12 | Cross-kinase consistency | 2/3+ kinases positive | 1/3 strong + informative negatives | 0/3 positive: pivot to negative result | ~10% |

### Gate Interaction

- G0 NO-GO is extremely unlikely but project-ending if triggered
- G1 NO-GO is survivable (GNINA + descriptors + state_specificity still work)
- G2 NO-GO is the highest-impact risk. At 20% probability, it fundamentally
  changes the paper. The PIVOT outcome (d in [0.3, 0.5)) is still publishable
  at JCIM but with a different thesis.
- G3 NO-GO is low-impact (Vina fallback is acceptable for JCIM)
- G4 NO-GO triggers BRAF as the critical second kinase
- G5 NO-GO triggers a negative-result paper (still publishable)

---

## 6. Risk Register

| # | Risk | P | Impact | Mitigation | Contingency |
|---|------|---|--------|------------|-------------|
| R1 | 4ZAU confirmed DFGin, need 3-state switch | 40% | Medium (2.5 days) | Budgeted in Phase 0 | 3-state model is publishable; include 2/3/4-state sensitivity analysis |
| R2 | MPNN scaffold R^2 < 0.20 | 10% | Medium | Well-tested fallback: GNINA + proxy scoring | Drop MPNN component; 3-component scoring |
| R3 | Ablation C d < 0.3 | 20% | **HIGH** | Pre-registered threshold; multiple seeds | Pivot to negative result or benchmark paper |
| R4 | REINVENT 4 GNINA integration fails | 15% | Low | 2-week time cap | REINVENT + Vina scoring (less comparable but valid) |
| R5 | ABL1 enrichment < 1.0 | 25% | Medium | Data quality checkpoint at day 3 | Try BRAF instead; or EGFR-only paper |
| R6 | ABL1 data curation takes 2x | 40% | Medium | Budget 8-10 weeks (not 6-9) | Cut scope to EGFR + one other kinase |
| R7 | Scooped before preprint | 10-15% | **HIGH** | ChemRxiv at week 8-10 | Accelerate to week 8; differentiate on ablation methodology |
| R8 | Single-researcher capacity bottleneck | 60% | Medium | Ruthless scope discipline | Cut PROBABLY-IN items first; extend timeline to 20 weeks |
| R9 | Curated features not traceable to measurements | 30% | Low | BioPython validation script | Measure from PDB coordinates; 2-3 days |
| R10 | ADMETlab 3.0 service instability | 30% | Low | Not on critical path | Local ADMET models as fallback |

---

## 7. Kill Criteria

### When to Abandon the Current Paper Thesis

The paper's thesis ("discrete state labels improve molecular generation for
kinases") should be abandoned if:

1. **Ablation C fails decisively** (Cohen's d < 0.2 across 3+ seeds). This means
   state conditioning provides zero benefit over unconditioned generation.
2. **All three kinases show no enrichment advantage** (EF@10 < 1.0 for state-aware
   in EGFR, ABL1, and BRAF). This means the pipeline doesn't work.
3. **Structural atlas errors are deeper than metadata** -- e.g., the curated
   pocket features are inconsistent with the actual structures in a way that
   invalidates the docking and generation. This would require
   re-measuring all features from PDB coordinates and re-running the entire
   pipeline. Estimated probability: <5%.

### Pivot Options

| Trigger | Pivot | Venue | Timeline Impact |
|---------|-------|-------|----------------|
| Ablation C d < 0.3 | "Negative result: state labels do not improve generation" | JCIM (negative results valued) | +2 weeks (rewrite) |
| Ablation C d in [0.3, 0.5) | "Multi-pocket diversity, not state labels, drives enrichment" | JCIM | +1 week (reframe) |
| ABL1 + BRAF both fail | "EGFR case study with methodological contribution" | J. Cheminform. or Brief. Bioinform. | +0 weeks (reduce scope) |
| MPNN R^2 < 0.15 | Drop MPNN; 3-component scoring | JCIM | +0 weeks (simplifies scoring section) |

---

## 8. Minimum Viable Paper (JCIM)

The absolute minimum for a submittable JCIM paper:

- [ ] Corrected structural atlas with full PDB annotation table
- [ ] Honest disclosure of mutant DFGout structures
- [ ] EGFR retrospective enrichment with BCa bootstrap CIs + BEDROC(alpha=20)
- [ ] Ablation C result with Cohen's d and pre-registration timestamp
- [ ] MPNN scaffold-split R^2 (both splits reported)
- [ ] Compute-matched comparison (PMO-style fixed oracle budget)
- [ ] FCD scores replacing validity as quality metric
- [ ] Scoring component ablation (which component drives enrichment)
- [ ] At least one additional kinase (ABL1 preferred)
- [ ] REINVENT 4 external baseline
- [ ] Pre-registration document timestamped before experiments

**Without ABL1 or BRAF:** The paper is still submittable to JCIM as an EGFR case
study with strong ablation methodology, but acceptance probability drops from
55-65% to ~40-50%.

**Without REINVENT 4:** The paper lacks an external baseline. Less defensible but
potentially acceptable at JCIM if the ablation battery is comprehensive. Not
recommended.

---

## 9. Nature Computational Science Upgrade Path

After JCIM acceptance, the path to Nature Comp Sci requires:

| Requirement | Current State | Work Needed |
|-------------|--------------|-------------|
| Multi-kinase (4+) | 2-3 kinases | Add MET, SRC, or additional targets |
| Cross-architecture validation | VAE + REINVENT 4 | Add DiffSBDD or MolPilot 3D baseline |
| Within-method state ablation | Not done | REINVENT 4 multi-pocket vs single-pocket |
| Wet lab or strong computational validation | None | OpenFE FEP on top candidates |
| "Computational framework" framing | Benchmark paper | Reframe as "ConformState framework" |

**Estimated additional work:** 12-16 weeks after JCIM paper.

**Alternative upgrade venue:** NeurIPS 2027 Evaluations & Datasets track (deadline
~May 2027). Requires benchmark infrastructure: Docker containers, HuggingFace
dataset, Croissant metadata, leaderboard. 5+ kinases, 3+ generation methods.
Estimated acceptance probability: 40-55% with full infrastructure.

---

## 10. Open Questions (Deferred to Implementation)

These decisions cannot be made in advance and require empirical results:

1. **4ZAU conformation:** DFGin or DFGout? Determines 3-state vs 4-state model.
   Resolved by P0 (2 hours of coordinate inspection).

2. **MPNN scaffold-split R^2:** How much does it degrade? Determines whether MPNN
   stays in the scoring function. Resolved by P3 (2-3 days).

3. **Ablation C magnitude:** Strong, moderate, weak, or null effect? Determines
   the paper's narrative direction. Resolved by P6 (1-2 weeks).

4. **ABL1 data quality:** Is ChEMBL ABL1 data clean enough for curation? Resolved
   by P12 step 2 (3-5 days, with checkpoint at day 3).

5. **REINVENT 4 GNINA integration feasibility:** Does the ExternalProcess
   component work with GNINA command-line? Resolved by P9 (8-15 days, with
   2-week time cap).

6. **Optimal number of kinases:** Will BRAF replicate the enrichment pattern?
   Resolved by P13 + Gate G5 (week 12).

7. **Preprint scope:** Should preliminary ABL1 results be included in the
   ChemRxiv preprint, or only EGFR? Depends on ABL1 progress by week 8.

8. **Scoring weight optimization:** Should scoring weights be re-optimized after
   removing osimertinib from reference binders? Resolved empirically during P11.

---

## 11. What NOT to Do

These are explicit anti-patterns identified across three rounds of review:

1. **Do NOT touch DiffSBDD, MET, GIST, or benchmark infrastructure until JCIM
   is submitted.** Every hour spent on deferred items is an hour not spent on the
   three things that matter: fixing the foundation, running the ablation, and
   extending to ABL1/BRAF.

2. **Do NOT submit to Nature Comp Sci directly.** Desk rejection probability is
   50-70%. Turnaround cost: 2-4 months. Submit to JCIM; upgrade later.

3. **Do NOT attempt NeurIPS 2026 E&D.** Deadline is May 6, 2026 (27 days).
   Impossible.

4. **Do NOT publish a preprint before the structural atlas is corrected.** A
   preprint with known mutant-as-WT errors would be career-damaging if discovered.

5. **Do NOT report MPNN R^2 under random split as a primary metric.** Report
   scaffold-split R^2 as primary; random split in supplement for transparency.

6. **Do NOT claim "zero-shot generalization" for any baseline trained on
   CrossDocked2020.** EGFR overlap is near-certain.

7. **Do NOT change n_states without retraining the VAE.** Checkpoint dimensions
   are incompatible across n_states values.

8. **Do NOT run Ablation C before fixing structural annotations.** Comparing
   "wrong conditioning" vs "no conditioning" is uninformative.

9. **Do NOT add a fourth kinase (MET) to the initial submission.** Three kinases
   is the sweet spot for JCIM. Four adds 4-6 weeks for marginal benefit.

10. **Do NOT spend more than 2 weeks on REINVENT 4 integration.** If it doesn't
    work by week 7, fall back to Vina scoring. An imperfect baseline beats no
    baseline and a 3-week delay.

---

## 12. Three Things to Remember

1. **The structural fix is your first priority, not your first annoyance.** It
   gives you confidence in every downstream result and an honest narrative:
   "We discovered annotation errors during our review process, corrected them,
   and re-evaluated our claims." This is a strength, not a weakness.

2. **Ablation C is the most important experiment you will run.** If d >= 0.8,
   you have a strong paper. If d >= 0.5, you have a publishable paper. If d < 0.3,
   you have a different but still publishable paper. In all cases, you need
   to know the answer before investing 12 more weeks.

3. **Report honestly.** The MPNN R^2 will drop with scaffold splits. The
   enrichment may narrow with compute matching. The structural atlas has errors
   you didn't catch initially. Report the favorable AND unfavorable numbers.
   Honest reporting of imperfect results is stronger than cherry-picked metrics.
   Pre-registration transforms this honesty from post-hoc rationalization into
   a priori scientific rigor.

---

*This implementation plan was produced by a 5-reviewer panel through 4 rounds of
independent review, deep verification research (150+ web searches, 100+ citations),
deliberation across reviewers, and synthesis. It reflects consensus positions where
4/5+ reviewers agree and evidence-weighted resolutions where disagreement persists.
Total panel output: 20+ documents, 6,000+ lines, 100+ unique references.*
