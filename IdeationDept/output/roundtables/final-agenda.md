---
agent: Orchestrator
round: final
date: 2026-04-08
type: roundtable
---

# Final Research Agenda: StateBind Publication Strategy

## Process Summary

This agenda synthesizes 3 rounds of multi-agent ideation:
- **Round 1:** 7 specialists, ~4,928 lines of deep research, 198 citations
- **Round 2:** 5 formal proposals, 2 focused research notes
- **Round 3:** 12 cross-domain critiques identifying 47 specific weaknesses

The result is a prioritized, evidence-based research plan that transforms StateBind from
a completed computational pipeline into a publication-ready contribution.

---

## The Paper

**Title (working):** "Does Conformational State-Awareness Improve Molecular Design?
A Multi-Kinase Retrospective Benchmark"

**Core claim:** Conditioning molecular generation on protein conformational states is a
transferable principle that improves prospective drug identification across kinase targets
and generation architectures.

**Novelty (verified):** No published paper conditions molecular generation on discrete
conformational states of the same protein. Exhaustive search across patents, preprints,
conferences, and industry (genai-R02, 30+ searches, 30 citations) confirms this as of
April 2026. Time pressure exists -- the field is converging (DynamicFlow, Apo2Mol,
DynamicBind all 2024-2025).

**Primary venue:** JCIM (framework/benchmark paper)
**Aspirational venue:** Nature Computational Science (if within-method ablations
demonstrate transferable principle across architectures)

---

## Critical Pre-Publication Fixes (Do Before Anything Else)

These are bugs, not enhancements. They must be fixed before any new experiments.

### Fix 1: Osimertinib Reference Leakage
**Source:** datasci-R01
**Issue:** Osimertinib (approved Nov 2015) is used as a reference molecule in the scoring
function for pre-2015 retrospective validation. The scoring function has information about
a "future" drug.
**Action:** Re-run pre-2015 validation using only erlotinib + gefitinib as reference
molecules. Pre-2010 validation is clean.
**Effort:** Hours. **Impact:** Eliminates a reviewer kill-shot.

### Fix 2: Verify Structural Data (3W2R, 4ZAU)
**Source:** structbio-R01
**Issue:** 3W2R is a T790M/L858R double mutant (not wild-type). 4ZAU ligand/state
assignment may be incorrect (osimertinib, not EAI045). Using mutant structures to
represent wild-type states conflates mutational and conformational effects.
**Action:** Check against KLIFS/KinCore. Find wild-type DFGout alternative if needed.
Verify 4ZAU conformational state independently.
**Effort:** Days. **Impact:** Prevents structural biology reviewers from dismissing the work.

### Fix 3: Bootstrap CIs on Current Results
**Source:** datasci-R01
**Issue:** No confidence intervals on any enrichment metric. EF@10 = 4.95 with N=5 has
95% CI spanning roughly [0.5, 9.4].
**Action:** Compute BCa bootstrap CIs (10,000 resamples) on all current enrichment
metrics. Add BEDROC(alpha=20) alongside EF@10.
**Effort:** Hours. **Impact:** Transforms anecdotal claims into statistical statements.

---

## Priority 0: The Three Pillars (Weeks 1-6)

These three workstreams run in parallel and together constitute the minimum viable paper.
Without ALL THREE, the paper is not submittable to JCIM.

### Pillar 1: Multi-Kinase Validation (Weeks 1-6)

**Revised kinase set (per structbio-R02 + critiques):**

| Kinase | KinCore Chains | DFGout | States | Held-Out Drugs (pre-2015) | Feasibility |
|--------|---------------|--------|--------|---------------------------|-------------|
| EGFR | 186+ | Yes | 4 | 3 (osimertinib, dacomitinib, lazertinib) | HIGH |
| ABL1 | 136 | 55 (40%) | 6 | 1-2 (asciminib***, ponatinib**) | HIGH |
| BRAF | 218 | 73 | 7 | 2 (encorafenib, tovorafenib) | HIGH |
| MET | 126 | Multiple | 7 | 2 (capmatinib, tepotinib) | HIGH |

***Asciminib binds myristate allosteric pocket (not ATP) -- exclude from enrichment or
pre-register as negative control (per medchem critique).
****Ponatinib approved 2012 -- in training set for pre-2015 split.

**Dropped kinases:**
- RET: 100% active-state structures, zero DFGout (structurally impossible)
- JAK2: 100% DFGin in catalytic domain, all drugs type I (no state diversity)
- ALK: Only 2 DFGout structures, all drugs type I (optional stretch only)

**Total held-out drugs:** ~8-10 (pre-2015 cutoff across 4 kinases)
- This is less than the originally estimated ~21 because RET/JAK2/ALK dropped
- Enrichment CIs will be moderate, not tight. Sufficient for JCIM but may need ALK
  (stretch) for Nature Comp Sci
- Consider pre-2010 cutoff as sensitivity analysis for additional held-out drugs

**Practical 3-state model:** DFGin/aCin, DFGin/aCout, DFGout/aCin works across all
4 kinases. DFGout/aCout (~1% of all kinase structures) is EGFR-only optional state.

**Per-kinase requirements:**
- Conformational state atlas (2-4 representative structures per state from KLIFS)
- ChEMBL bioactivity data for MPNN training
- Pre-cutoff reference molecules for similarity scoring (kinase-specific)
- GNINA receptor preparation for each state

**Pre-registration:** Lock all analysis decisions (primary endpoint BEDROC, secondary
EF@10, kinase set, time-split, reference molecules, success criteria) before running
experiments. Pre-specify 4 outcome scenarios with publication framings.

**Compute:** ~30-42 GPU-days (retraining VAE + MPNN per kinase + GNINA docking)

### Pillar 2: Ablation Suite (Weeks 1-3)

The comparison between state-aware and static is confounded. These ablations isolate
each factor. Run on EGFR first (fastest), then extend to multi-kinase.

| Experiment | State Conditioning? | Generator | N Candidates | Isolates |
|-----------|-------------------|-----------|-------------|----------|
| A. Static baseline | No | Template | 30 | (current) |
| B. State-aware full | Yes | VAE+Template | 461 | (current) |
| C. **Unconditioned VAE** | **No** | **VAE** | **~400** | **State effect** |
| D. State-aware template only | Yes | Template | ~36 | VAE contribution |
| E. Subsampled state-aware | Yes | VAE | 30 | Count effect |
| F. Shuffled state labels | Shuffled | VAE | ~400 | Label information |
| G. Random molecules | No | Random ChEMBL | 461 | Lower bound |

**Experiment C is thesis-critical.** If unconditioned VAE matches state-conditioned on
enrichment (Cohen's d < 0.5), the state-awareness claim weakens and the paper pivots to
"diverse generation outperforms template-based design." Still publishable but a different
story. Pre-registered success threshold: Cohen's d >= 0.8 for state effect.

**Harmonized specification (per datasci critique of mlres-P01):** The unconditioned VAE
must use identical architecture with state vector zeroed out (not removed), trained on the
same data, generating the same number of candidates. This spec is shared between the
ablation suite and the baseline comparison.

**Compute:** ~2-5 GPU-days per kinase

### Pillar 3: External Baselines (Weeks 1-4)

**Revised baseline set (incorporating critique feedback):**

| Baseline | Type | Purpose | Setup Time |
|----------|------|---------|------------|
| **REINVENT 4** | 1D RL | Established molecular optimization standard | 1-2 weeks |
| **FLOWR** | 3D flow matching | Modern 3D pocket-conditioned (92% PB validity) | 1 week |
| **Unconditioned VAE** | 1D VAE | Critical ablation (shared with Pillar 2) | 1-2 days |
| **Random ChEMBL** | Random | Null distribution (sample 100x) | Hours |
| **Fingerprint search** | Retrieval | Tests if generation adds value over retrieval | Hours |

**Changes from mlres-P01 proposal:**
- FLOWR replaces MolCRAFT as primary 3D baseline (per genai critique: 92% PoseBusters
  validity vs MolCRAFT's lower validity, interaction conditioning available)
- MolCRAFT or DiffSBDD as documented fallback if FLOWR checkpoint unavailable
- Must check CrossDocked2020 training data for EGFR structure leakage before claiming
  "zero-shot" for any 3D method

**Within-method state ablations (per genai critique -- the Nature Comp Sci upgrade):**
- REINVENT 4-pocket (state-aware) vs REINVENT 1-pocket (1M17 only)
- FLOWR 4-pocket vs FLOWR 1-pocket
- If state-conditioning improves enrichment ACROSS architectures, the claim elevates from
  "our VAE benefits from state labels" to "state-conditioning is a transferable principle"

**Evaluation protocol:**
- ALL methods scored with BOTH 4-component (original) AND 3-component (no state
  specificity) scoring (per datasci critique: state-specificity creates 15% handicap
  for non-state-aware methods)
- Retrospective enrichment on same time-split, BEDROC + EF@10 with bootstrap CIs
- PoseBusters validity for all methods (not just 3D)
- Drug-likeness, diversity, validity, novelty distributions

**Compute:** ~40 GPU-hours + GNINA docking time

---

## Priority 1: Strengthening Experiments (Weeks 2-5)

These significantly strengthen the paper but are not absolute blockers for JCIM submission.

### GIST Water Thermodynamic Analysis
**Source:** compchem-P01
**What:** Short MD (20 ns minimum per structbio critique) for each EGFR state, then GIST
via cpptraj to map water thermodynamics in the binding pocket.
**Why:** Directly shows the 4 states present physically different solvation environments.
Validates the fundamental thesis at the atomic level.
**Critique feedback incorporated:**
- Use 20 ns (not 10 ns) for convergence in larger DFGout pockets
- Run back-mutation GIST control for 3W2R (T790M/L858R vs WT) per structbio critique
- Consider ensemble GIST (3-5 structures per state) for within-state variability
- Verify 4ZAU classification before running
**Cost:** 2-4 GPU-days. **Impact:** Publication-quality figure. Best cost-to-impact ratio.

### Survival Funnel (Applied to ALL Methods)
**Source:** synthbio-P01 + mlres critique
**What:** Pass ALL methods' candidates through: generation -> scoring -> ADMET filter ->
retrosynthetic validation -> end-to-end profile for top candidates.
**Why:** Differentiates from academic exercises. If state-aware candidates have higher
survival rates across the funnel, this is a strong practical argument.
**Tools:** ADMETlab 3.0 API (save results locally for reproducibility), AiZynthFinder
4.0 for top 50 per method, RAscore for all candidates.
**Critique feedback incorporated:**
- RAscore as filter/analysis, NOT as scoring component (per mlres critique)
- hERG threshold: 1.0 uM (not 0.5 uM, per medchem critique)
- Add HLM t1/2 as metabolic stability endpoint (per synthbio critique)
- PKSmart demoted to supplementary material (per medchem critique: R² too low)
- Save all API results locally with version stamps for reproducibility
**Cost:** <2 hours compute, 1-2 weeks integration. **Impact:** Novel figure standard.

---

## Priority 2: Publication Enhancements (Weeks 4-7)

### Scoring Sensitivity Analysis (Not Revision)

**Critical decision from critiques:** The scoring function should NOT be revised for the
primary comparison. Instead:

1. **Primary analysis:** Original 4-component scoring (0.35/0.30/0.20/0.15). Fair,
   pre-existing, no bias concerns.
2. **Secondary analysis (3-component):** Remove state-specificity (reweight to
   0.41/0.35/0.24). Shows baseline fairness -- non-state-aware methods don't have a
   15% handicap.
3. **Sensitivity analysis:** 1,000+ Dirichlet-sampled weight configurations (per datasci
   critique: 100 is insufficient for 4D simplex, let alone 6D).
4. **Pareto analysis as primary multi-objective:** Report hypervolume ratios and Pareto
   dominance fractions. StateBind already has this infrastructure. This avoids the
   "linear sum of incommensurable quantities" critique from compchem.
5. **Exploratory:** Test one alternative scoring config (e.g., with ADMET from ADMETlab
   3.0) as a "what-if" in supplementary, NOT as a primary result. Pre-specify via
   calibration on approved kinase inhibitors.

### Conformational State-Selectivity Argument

**Source:** medchem-R01, structbio-R01
**What:** Quantify how many state-aware candidates target DFG-out states. Cross-reference
with published type II selectivity data (Gini 0.76 vs 0.58).
**Why:** The strongest biological argument for state-aware design: DFG-out targeting
inherently favors selectivity because the DFG-out pocket is less conserved across kinases.
**Action:** Analysis only (no new experiments). Count DFG-out-targeting candidates,
compute expected selectivity improvement, cite structural biology literature.
**Cost:** Days. **Impact:** Addresses "so what?" question with biological mechanism.

### Conformational Classification Mapping

**Source:** structbio-R01
**What:** Table mapping StateBind's 4-state model to Modi/Dunbrack (8 states), Ung (5
states), and KLIFS nomenclature. Include structure counts per state.
**Why:** Pre-empts the "oversimplification" reviewer attack. Shows awareness of the
continuous landscape literature while justifying the discrete model for practical design.
**Cost:** Days. **Impact:** Reviewer defense.

---

## Priority 3: Nature Comp Sci Upgrades (Weeks 5-8+)

These are only worth pursuing if the JCIM-level results are strong.

### OpenFE RBFE Validation
**Source:** compchem-P01
**What:** FEP on a stratified sample of candidates (not just top-ranked -- per mlres
critique about selection bias). Include known binder positive controls.
**Cost:** 120-180 GPU-hours. **Impact:** Rigorous physics-based validation.

### Full Multi-Kinase Expansion (5+ Kinases)
**What:** Add ALK (stretch) and potentially Aurora A to reach 5-6 kinases and 15+ held-out
drugs for tight enrichment CIs.
**Depends on:** Pillar 1 results being positive.

### Conformation-Conditioned Flow Matching (Future Paper)
**Source:** genai-R01 Tier 3
**What:** Novel architecture conditioning flow matching on conformational state embeddings.
**Why:** NeurIPS/ICML paper if successful. But this is a separate publication, not part
of the current paper. The current paper's contribution is the QUESTION, not the MODEL.

---

## The Integrated Timeline

```
Week 0 (Immediate):
  [ ] Fix osimertinib reference leakage (hours)
  [ ] Verify 3W2R and 4ZAU structures (days)
  [ ] Compute bootstrap CIs on current results (hours)
  [ ] Add BEDROC to current evaluation (hours)

Week 1-2:
  [ ] Train unconditioned VAE for ablation (1-2 GPU-days)
  [ ] Set up REINVENT 4 with EGFR GNINA scoring (1-2 weeks)
  [ ] Begin ABL1 conformational atlas preparation (1 week)
  [ ] Start GIST water analysis on EGFR states (2-4 GPU-days)
  [ ] Run ablation suite Experiments C, F, G on EGFR (days)

Week 2-3:
  [ ] Complete ablation suite on EGFR (all experiments)
  [ ] Set up FLOWR with EGFR pockets (1 week)
  [ ] Begin BRAF and MET atlas preparation (1-2 weeks)
  [ ] Run REINVENT 4 generation + scoring
  [ ] Run ADMETlab 3.0 profiling on all current candidates
  [ ] RAscore + AiZynthFinder on top 50 candidates

Week 3-4:
  [ ] Complete external baseline comparison on EGFR
  [ ] Within-method state ablations (REINVENT 4-pocket vs 1-pocket)
  [ ] Begin multi-kinase VAE + MPNN training (ABL1, BRAF, MET)
  [ ] GIST analysis complete, generate water map figures
  [ ] State-selectivity analysis (DFG-out targeting fraction)

Week 4-6:
  [ ] Run full pipeline on ABL1, BRAF, MET
  [ ] Retrospective enrichment on all 4 kinases
  [ ] Pooled enrichment with bootstrap CIs
  [ ] Survival funnel applied to ALL methods
  [ ] Pareto analysis across kinases
  [ ] Sensitivity analysis (1000+ Dirichlet samples)

Week 6-8:
  [ ] Compile results, generate all figures
  [ ] Conformational mapping table (Modi/Dunbrack/Ung/KLIFS)
  [ ] Write manuscript (JCIM target)
  [ ] If results strong: OpenFE FEP validation (P3)
  [ ] If within-method ablations positive: upgrade to Nature Comp Sci framing
```

---

## Compute Budget Summary

| Workstream | GPU-Days | CPU-Days | Priority |
|-----------|----------|----------|----------|
| Multi-kinase (3 new kinases) | 30-42 | -- | P0 |
| Ablation suite (EGFR + 3 kinases) | 5-15 | -- | P0 |
| External baselines | 2-3 | -- | P0 |
| GIST water analysis | 2-4 | -- | P1 |
| Survival funnel (ADMETlab + AiZynthFinder) | <0.1 | 1-2 | P1 |
| Sensitivity analysis | 0.5 | -- | P2 |
| OpenFE FEP (if pursued) | 5-8 | -- | P3 |
| **Total P0-P1** | **~40-65** | **~2** | |

All feasible on Yale Bouchet with 2-4 H200 nodes over 6-8 weeks.

---

## Key Decisions Resolved by the Process

| Decision | Resolution | Source |
|----------|-----------|--------|
| Which kinases? | EGFR + ABL1 + BRAF + MET | structbio-R02 + critiques |
| Drop RET/JAK2? | Yes (structurally infeasible) | structbio-R02 |
| Primary metric? | BEDROC(alpha=20) with BCa bootstrap | datasci-P01 |
| Primary scoring? | Original 4-component (unchanged) | datasci critique of medchem-P01 |
| State-specificity bias? | Report 3-component as mandatory secondary | datasci critique of mlres-P01 |
| Scoring revision? | Supplementary/exploratory only, not primary | Cross-critique consensus |
| 3D baseline? | FLOWR (not MolCRAFT) | genai critique of mlres-P01 |
| RAscore in scoring? | No -- filter/analysis only | mlres critique of synthbio-P01 |
| hERG threshold? | 1.0 uM (not 0.5 or 10.0) | medchem + synthbio convergence |
| PKSmart? | Supplementary only | medchem critique |
| Pareto vs weighted sum? | Pareto primary, weighted sum secondary | compchem critique |
| 3 states vs 4? | 3-state model across kinases, 4 for EGFR | structbio-R02 |
| Asciminib? | Exclude or negative control | medchem critique |
| GIST priority? | P1 (best cost/impact) | mlres critique + compchem-P01 |
| Nature Comp Sci path? | Within-method state ablations across architectures | genai critique |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Ablation C shows diversity drives enrichment | Medium | High | Pre-register; reframe as "diverse generation" paper |
| Multi-kinase enrichment doesn't replicate | Low-Medium | Critical | Pre-register per-target reporting; some kinases may show null |
| FLOWR/MolCRAFT outperforms on all metrics | Low | Medium | Frame StateBind as evaluation framework, not generator |
| Osimertinib fix reduces enrichment | Medium | Medium | Pre-2010 validation unaffected; report both |
| CrossDocked2020 contains EGFR (3D leakage) | High | Medium | Check train split; disclose and discuss |
| 3W2R mutation affects results | Medium | Medium | Find WT DFGout structure; run with and without |
| Time pressure (field convergence) | Medium | High | Target submission within 3-4 months |

---

## What This Agenda Does NOT Include

The following were considered and explicitly deferred:

1. **Scoring function revision as primary analysis** -- Too high risk of bias perception.
   Scored function revision is scientifically motivated (medchem-P01 is compelling) but
   changing scoring to make state-aware win invites reviewer skepticism. Deferred to
   supplementary exploration.

2. **3D generation as replacement for SELFIES VAE** -- The paper's contribution is the
   QUESTION (state-conditioning), not the MODEL (a VAE). Including 3D methods as
   baselines is essential; replacing the VAE is a future paper.

3. **Retrosynthetic scoring component** -- RAscore as scoring inflates component count
   and threatens primary endpoint stability. Used as analysis/filter instead.

4. **FEP as primary validation** -- Selection bias concerns and cost. Deferred to P3 for
   Nature Comp Sci upgrade only.

5. **BSI similarity metric** -- Potential EGFR information leakage. Tanimoto is
   understood; changing it confounds the analysis.

---

## The Publication Narrative

**Paragraph 1 (the problem):** Most computational molecular design treats protein targets
as static structures. But kinases adopt multiple conformational states, each presenting a
different binding pocket. Does ignoring this cost us?

**Paragraph 2 (the approach):** We built StateBind, a framework for conformational
state-conditioned molecular generation. We test the hypothesis that state-awareness
improves molecular design by conducting the first systematic benchmark across 4 kinases.

**Paragraph 3 (the headline):** State-conditioned generation consistently enriches for
approved drugs in retrospective validation across EGFR, ABL1, BRAF, and MET
(BEDROC = X.XX, 95% CI [X.XX, X.XX]). Ablation shows this is driven by state
information, not generation diversity alone.

**Paragraph 4 (the transferable principle):** The state-conditioning advantage is not
architecture-specific. When we add per-state scoring to REINVENT 4 and per-pocket
conditioning to FLOWR, both show improved enrichment vs single-state versions. State-
awareness is a transferable design principle.

**Paragraph 5 (the biological mechanism):** State-aware candidates preferentially target
DFG-out conformations, which are structurally less conserved across kinases. This
inherently selects for more selective molecules (type II Gini 0.76 vs type I 0.58).

**Paragraph 6 (practical viability):** X% of top state-aware candidates have feasible
synthesis routes (AiZynthFinder), ADMET profiles comparable to approved drugs, and
predicted oral bioavailability > 30%.

---

*This agenda was produced by the IdeationDept orchestrator after 3 rounds of multi-agent
collaboration involving 21 specialist agent sessions, ~8,000 lines of research and
proposals, 12 cross-domain critiques, and 250+ internet research queries. All claims are
computational analyses and literature-based recommendations. No code was modified.*
