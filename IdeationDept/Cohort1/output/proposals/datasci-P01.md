---
agent: Maverick Data Scientist / Statistician
round: 2
date: 2026-04-08
type: proposal
proposal_id: datasci-P01
title: "Multi-Kinase Retrospective Validation with Pre-Registered Statistical Design"
---

# Proposal: Multi-Kinase Retrospective Validation with Pre-Registered Statistical Design

## Proposing Agent

Dr. Maverick Data Scientist / Statistician -- expertise in enrichment factor statistics,
causal inference, benchmark methodology, power analysis, and validation design for
computational drug discovery.

## Problem Statement

StateBind's headline result -- a 10x enrichment factor (EF@10 = 4.95/7.72 vs 0.47/0.79
for state-aware vs static) -- rests on N=3-5 held-out drugs from a single kinase target
(EGFR). This sample size is catastrophically underpowered for a publication claim.

**The core statistical problem:** With N=5 held-out drugs, the 95% confidence interval on
EF@10 spans approximately [0.5, 9.4]. The lower bound includes values below 1.0 (random
performance), meaning the data are statistically consistent with NO enrichment at all.
No credible venue -- not JCIM, not Nature Computational Science, not Bioinformatics --
will accept an enrichment claim with a confidence interval that fails to exclude the null.

Additionally, the comparison is confounded: the state-aware pipeline differs from the
static baseline in four simultaneous dimensions (state awareness, generation method,
candidate count, chemical diversity). Without ablations that isolate each factor, the
claim "conformational state-awareness drives enrichment" is unsupported.

**This proposal provides the statistical backbone of the publication.** It specifies the
exact experimental design, metrics, corrections, ablations, and success criteria needed
to transform a suggestive single-target case study into a rigorous multi-kinase finding.

## Vision

A pre-registered, multi-kinase retrospective validation study demonstrating that
conformational state-aware molecular design produces statistically significant enrichment
for approved kinase inhibitors across 5-6 kinase targets, with BEDROC(alpha=20) as the
primary endpoint, bootstrap confidence intervals on all metrics, a complete ablation
suite isolating the contribution of state-conditioning, and Benjamini-Hochberg correction
for multiple comparisons. The result -- whether positive, negative, or mixed -- is
publishable because the design is pre-specified and the analysis plan eliminates
selective reporting.

---

## Background and Evidence

### The Statistical Fragility of Single-Target Enrichment

Nicholls (2016) demonstrated in "The statistics of virtual screening and lead
optimization" (J Comput-Aided Mol Des, 29:1205) that with fewer than ~20 actives, the
uncertainty on enrichment factors is "extremely large." The enrichment factor is a ratio
statistic whose variance depends on the number of actives, inactives, and the measured
value. For StateBind's setting:

- **Pre-2010 split:** N_held_out = 5 (afatinib, dacomitinib, osimertinib, lazertinib,
  sunvozertinib). EF@10 = 4.95 vs 0.47. A shift of ONE drug from rank 45 to rank 47
  (2 positions out of 461) drops EF@10 by ~20%.
- **Pre-2015 split:** N_held_out = 3 (dacomitinib, lazertinib, sunvozertinib). Even
  less powered. The 95% CI on EF@10 with N=3 spans approximately [0.8, 14.6] --
  effectively uninformative.

Empereur-mot et al. (2022, J Cheminformatics 14:48) showed that proper inference on
enrichment curves is "almost never considered" in published virtual screening studies,
and introduced the EmProc method for confidence bands. StateBind would be among the
first generative design papers to report enrichment CIs rigorously.

### BEDROC as Superior Primary Metric

Truchon and Bayly (2007, JCIM 47:488-508) demonstrated that BEDROC (Boltzmann-Enhanced
Discrimination of ROC) is superior to EF for early recognition problems because:

1. EF@k is threshold-dependent and discards information about the full ranking
2. ROC AUC is insensitive to early recognition because it weights all positions equally
3. BEDROC uses exponential weighting with parameter alpha controlling emphasis on early
   ranks; at alpha=20, 80% of the weight comes from the top 8% of the ranked list
4. BEDROC ranges [0, 1] with well-understood null distributions amenable to hypothesis
   testing
5. BEDROC is "perhaps the most frequently adopted metric for measuring early recognition
   in virtual screening" and is standard in AlphaFold2 multi-state kinase validation
   studies (Grasso et al., 2024, Scientific Reports)

Clark and Webster-Clark (2016, J Cheminformatics 8:1-17) proposed the "power metric" as
an additional robust enrichment metric. However, BEDROC has broader adoption and
established comparison baselines, making it the better primary endpoint for StateBind.

### Multi-Kinase Data Availability

My Round 1 research (datasci-R01) established that 6 kinases beyond EGFR have sufficient
data for retrospective validation. The structbio Round 1 research (structbio-R01)
independently confirmed conformational state coverage:

- **ABL1:** Best-characterized conformational landscape. 150+ PDB structures across
  BLAminus (active), BBAminus (DFGout), and intermediates. Imatinib binds DFGout
  (inactive); dasatinib binds DFGin (active). 6 approved drugs: imatinib (2001),
  dasatinib (2006), nilotinib (2007), ponatinib (2012), bosutinib (2012), asciminib
  (2021). Asciminib is an allosteric STAMP inhibitor -- the ABL equivalent of
  state-specific design (Wylie et al., 2017).
- **ALK:** 70+ PDB structures. Multiple DFGin structures with crizotinib, alectinib,
  lorlatinib. Less DFGout coverage than ABL but classified as type I-1/2 B inhibitor
  binding (inactive without back pocket extension). 6 approved drugs from 2011-2024.
- **BRAF:** 100+ PDB structures. Found in all 5 Ung conformational states (one of only
  2 kinases with complete coverage). Vemurafenib and dabrafenib bind DFGin/aCout;
  tovorafenib binds DFGout/aCin. 4 approved drugs from 2011-2024.
- **RET:** 30+ PDB structures including 7JU6 (selpercatinib, 2.06 A) and 7JU5
  (pralsetinib, 1.9 A). Novel binding mode wrapping around gate wall. 5 approved drugs
  from 2011-2020. Less conformational diversity than ABL/BRAF.
- **JAK2:** 60+ PDB structures. 12+ approved JAK inhibitors. Rich held-out set for
  pre-2015 split (8+ drugs). However, JAK selectivity is complex (JAK1/2/3/TYK2
  cross-reactivity) and may confound kinase-specific validation.

### The Confounding Problem Demands Ablation

The Round 1 synthesis (round01-synthesis.md) identified universal consensus across all
7 specialists that the state-aware vs static comparison conflates 4 factors. The causal
inference framework (Bender et al., 2023, Drug Discovery Today 28:103737) makes clear
that without controlling for generation method, candidate count, and chemical diversity,
the treatment effect of state-awareness cannot be isolated.

### Pre-Registration Eliminates Publication Risk

The CACHE Challenge (Critical Assessment of Computational Hit-finding Experiments)
demonstrates the power of prospective pre-registration in computational drug discovery.
CACHE organizes hit-finding challenges where computational teams predict hits before
experimental testing, with pre-specified evaluation criteria. This model ensures that
negative results are as publishable as positive ones (Ackloo et al., 2022, PLOS ONE).

The Polaris consortium (AstraZeneca, Pfizer, Novartis, Recursion) published "Practically
significant method comparison protocols" (JCIM 2025, 65:18) establishing that claims of
method superiority require: (a) pre-specified primary endpoints, (b) effect size
reporting, (c) multiple dataset evaluation, and (d) distinction between statistical and
practical significance. This proposal aligns with all four requirements.

### Key Evidence

1. **Nicholls (2016):** EF variance with <20 actives is "extremely large" -- CIs too
   wide for publication.
2. **Truchon & Bayly (2007):** BEDROC(alpha=20) is the recommended early recognition
   metric; 80% of weight in top 8% of ranked list.
3. **Empereur-mot et al. (2022):** Confidence bands for enrichment curves are "almost
   never reported" -- doing so is differentiating.
4. **Polaris Consortium (2025):** Multi-dataset evaluation with pre-specified endpoints
   is the new standard for method comparison.
5. **Backenkoehler et al. (2024):** 37 kinases have 3+ conformational states in PDB;
   ABL and BRAF have the richest multi-state structural data.
6. **Bayesian bootstrap (Pustejovsky, 2024):** BCa-CI achieves higher coverage than
   classical percentile CI at small n, with the advantage most pronounced at the
   smallest sample sizes.
7. **Grasso et al. (2024):** AlphaFold2 multi-state docking for kinases uses BEDROC and
   enrichment factors as standard validation metrics.
8. **CACHE Challenge (2024):** Prospective pre-registered evaluation of computational
   hit-finding demonstrates that pre-specification makes any outcome publishable.

### Relationship to Existing Work

- **StateBind current state:** Retrospective validation exists for EGFR only (pre-2010
  and pre-2015 cutoffs). Bootstrap CIs are not computed. BEDROC is not reported. No
  ablations exist. The comparison is confounded.
- **Vision System ideas:** This proposal operationalizes the multi-kinase direction
  implied by Vision Idea 003 (Kinome-Wide Selectivity Panel) but focuses on statistical
  validation rather than selectivity prediction. It does NOT duplicate Idea 003 because
  the goal is retrospective enrichment validation, not cross-docking selectivity.
- **Literature precedent:** No published generative molecular design paper has performed
  pre-registered multi-kinase retrospective validation with BEDROC as primary endpoint
  and full ablation controls. This would be a methodological first.

---

## Proposed Approach

### Overview

This proposal specifies a complete statistical design for multi-kinase retrospective
validation of StateBind's state-aware molecular design approach. The design has three
interlocking components: (1) a multi-kinase enrichment study with pre-registered primary
endpoint (BEDROC alpha=20), (2) a 6-experiment ablation suite applied first to EGFR then
to all targets, and (3) a pre-specified analysis plan with multiple testing correction
that makes any outcome -- positive, negative, or mixed -- publishable.

The pre-2015 time-split cutoff is selected as the primary analysis because it maximizes
the number of held-out drugs across targets (~21 total across 6 kinases) while retaining
sufficient training data for each target. The pre-2010 cutoff serves as a sensitivity
analysis.

### Target Kinase Selection

**Primary targets (5 kinases + EGFR = 6 total):**

| Rank | Kinase | Justification | Held-out (pre-2015) | Conformational States in PDB | Reference Molecules |
|------|--------|--------------|---------------------|------------------------------|---------------------|
| 1 | **ABL1** | Best conformational coverage; imatinib=DFGout, dasatinib=DFGin. 150+ PDB structures. 8000+ ChEMBL actives. Gold standard kinase for conformational studies. | asciminib (2021) = 1 | 3+ (BLAminus, BBAminus, BLBplus, intermediates) | imatinib, dasatinib, nilotinib |
| 2 | **BRAF** | All 5 Ung states; vemurafenib=DFGin/aCout, tovorafenib=DFGout/aCin. 100+ PDB structures. 5000+ ChEMBL actives. | encorafenib (2018), tovorafenib (2024) = 2 | 5 (all Ung states) | vemurafenib, dabrafenib |
| 3 | **ALK** | Most held-out drugs; type I-1/2 B binding mode. 70+ PDB structures. 3000+ ChEMBL actives. | alectinib (2015), brigatinib (2017), lorlatinib (2018), ensartinib (2024) = 4 | 2+ (DFGin, DFGin-inactive) | crizotinib, ceritinib |
| 4 | **RET** | Novel binding mode (gate wall wrapping); selective inhibitors. 30+ PDB structures. 1500+ ChEMBL actives. | lenvatinib (2015), pralsetinib (2020), selpercatinib (2020) = 3 | 2 (DFGin, some DFGout) | vandetanib, cabozantinib |
| 5 | **JAK2** | Largest held-out set; 12+ approved inhibitors. 60+ PDB structures. Rich bioactivity data. | baricitinib (2018), fedratinib (2019), upadacitinib (2019), pacritinib (2022), + others = 8+ | 2+ (DFGin variants) | ruxolitinib, tofacitinib |
| -- | **EGFR** | Current target, retained for continuity. | osimertinib (2015), dacomitinib (2018), lazertinib (2024) = 3 | 4 (current atlas) | erlotinib, gefitinib |

**Total held-out drugs (pre-2015 cutoff): ~21 across 6 kinases.**

**Excluded targets and rationale:**
- **MET:** Only 2 approved drugs (capmatinib 2020, tepotinib 2021), both post-2015.
  Zero training drugs for pre-2015 cutoff. Excluded.
- **CDK2:** No approved selective CDK2 inhibitor. Palbociclib targets CDK4/6. Excluded
  due to target ambiguity.
- **Aurora A:** No approved selective Aurora inhibitor. Excluded due to lack of approved
  drugs for retrospective validation.

### Implementation Steps

#### Step 0: Fix Known Data Issues (Days 1-3)

1. **Osimertinib reference leakage:** Remove osimertinib from reference molecules for
   ALL pre-2015 validations. Use only erlotinib + gefitinib as EGFR references.
   Re-run current EGFR retrospective with corrected references to establish the true
   baseline.

2. **Per-kinase reference molecules:** Define reference binder sets per kinase, using
   ONLY drugs approved before the cutoff date:
   - EGFR (pre-2015): erlotinib (2004), gefitinib (2003)
   - ABL (pre-2015): imatinib (2001), dasatinib (2006), nilotinib (2007)
   - ALK (pre-2015): crizotinib (2011), ceritinib (2014)
   - BRAF (pre-2015): vemurafenib (2011), dabrafenib (2013)
   - RET (pre-2015): vandetanib (2011), cabozantinib (2012)
   - JAK2 (pre-2015): ruxolitinib (2011), tofacitinib (2012)

3. **Verify structural assignments:** Confirm 3W2R (T790M/L858R mutant) and 4ZAU
   (contains osimertinib, not EAI045) assignments against KLIFS/KinCore per structbio
   findings.

#### Step 1: Conformational State Atlas Per Kinase (Weeks 1-2)

For each of the 5 new kinases:

1. **Identify representative structures per state** from PDB/KLIFS:
   - Minimum 2 conformational states per kinase (DFGin active + at least one inactive)
   - Prefer wild-type structures; document mutation status of all chosen structures
   - Prefer structures with resolution <= 2.5 A
   - Cross-validate assignments against KLIFS, KinCore, and Ung classifications

2. **Prepare receptor structures** for GNINA docking:
   - Remove ligands, add hydrogens, generate PDBQT files
   - Define binding site grids centered on the kinase ATP-binding pocket
   - Validate with known binder re-docking (expect RMSE < 2.0 A for pose recovery)

3. **Extract pocket descriptors** using StateBind's existing 9D feature vector pipeline
   per state.

**Expected structural atlas per kinase:**

| Kinase | State 1 (Active) | State 2 (Inactive 1) | State 3 (Inactive 2) | State 4 (if available) |
|--------|------------------|---------------------|---------------------|----------------------|
| ABL1 | 6XR6 (BLAminus) | 1IEP (BBAminus, imatinib) | 6XR7 (BLBplus) | 6XRG (intermediate) |
| BRAF | 3OG7 (DFGin/aCin) | 3C4C (DFGin/aCout) | 8F7O (DFGout/aCin, tovorafenib) | -- |
| ALK | 5AAB (DFGin, crizotinib) | 4CLI (DFGin inactive) | -- | -- |
| RET | 7JU6 (DFGin, selpercatinib) | 7JU5 (DFGin, pralsetinib) | -- | -- |
| JAK2 | 3FUP (DFGin active) | 3E62 (DFGin/aCout) | -- | -- |

*Note: Exact PDB codes require confirmation against KLIFS during implementation.*

#### Step 2: MPNN Retraining Per Kinase (Weeks 1-3, parallel with Step 1)

For each kinase, retrain the affinity MPNN on target-specific ChEMBL bioactivity data:

1. **Query ChEMBL v34** for compounds with pIC50/Ki/Kd data against the target
2. **Apply StateBind's existing data processing pipeline** (same filters, same splits)
3. **Time-split training data:** Use only compounds with first publication date <= 2014
4. **Train MPNN** with identical architecture and hyperparameters as EGFR MPNN
5. **Validate:** Report R^2, RMSE, Pearson correlation on held-out validation set

Expected data availability (from ChEMBL v34):

| Kinase | ChEMBL ID | Estimated pIC50 Compounds | Pre-2015 Training Set |
|--------|-----------|--------------------------|----------------------|
| ABL1 | CHEMBL1862 | ~8,000 | ~5,500 |
| BRAF | CHEMBL5145 | ~5,000 | ~3,000 |
| ALK | CHEMBL4247 | ~3,000 | ~1,500 |
| RET | CHEMBL2041 | ~1,500 | ~800 |
| JAK2 | CHEMBL2971 | ~4,000 | ~2,500 |

#### Step 3: VAE Training and Generation Per Kinase (Weeks 2-4)

For each kinase:

1. **Train conditional SELFIES VAE** with identical architecture to EGFR VAE:
   - Training data: ChEMBL compounds for the target with first_publication <= 2014
   - State conditioning: one-hot vector for number of conformational states
   - Hyperparameters: same as EGFR (latent_dim=64, 300 epochs on H200)

2. **Generate candidates** per state:
   - ~250 molecules per state (targeting ~400-500 total as in EGFR pipeline)
   - Filter for validity, uniqueness, and drug-likeness

3. **Generate template-based candidates** from pre-cutoff reference molecules
   (same string-modification strategy as EGFR baseline)

4. **Score ALL candidates** with the unified scoring function using:
   - Per-kinase reference molecules (pre-cutoff only)
   - Per-kinase MPNN (or GNINA if time permits)
   - Per-kinase state specificity scores from the conformational atlas

#### Step 4: Ablation Suite on EGFR First (Weeks 2-3)

Run the 6-experiment ablation matrix on EGFR before extending to other kinases.
This determines whether the full multi-kinase expansion is warranted.

| ID | Experiment | State Conditioning? | Generator | N Candidates | What It Tests |
|----|-----------|-------------------|-----------|-------------|---------------|
| A | **Unconditioned VAE** | NO | VAE (identical arch, no state vector) | ~400 | THE critical ablation: isolates state info from VAE diversity |
| B | **State templates only** | YES | Template modification (4 states) | ~36 | Isolates contribution of VAE from state awareness |
| C | **State-aware subsample** | YES | VAE + templates (subsampled) | 30 | Isolates candidate count effect |
| D | **Random state assignment** | SHUFFLED | VAE (random state labels) | ~400 | Tests whether state IDENTITY matters vs having ANY conditioning |
| E | **Random molecule baseline** | NO | Random SMILES from ChEMBL | 461 | Lower bound / sanity check |
| F | **Full state-aware** | YES | VAE + templates | 461 | Current pipeline (reference) |

**Critical comparison hierarchy:**

```
If F >> A (large gap): State-conditioning drives enrichment. Thesis supported.
If F ~ A (small gap):  VAE diversity drives enrichment. Thesis weakened.
                       The paper pivots to "diverse generation > template design."
If F >> D (vs shuffled): State IDENTITY matters, not just conditioning signal.
If A >> E (VAE >> random): VAE generates meaningful chemistry, not random noise.
If F >> C (full >> subsample): Candidate count contributes to enrichment.
```

**Quantitative thresholds for "large gap" vs "small gap":**
- Compute BEDROC(alpha=20) for each experiment
- Define "large gap" as Cohen's d >= 0.8 (large effect) between F and A
- Define "small gap" as Cohen's d < 0.5 (small/medium effect)
- The intermediate range (0.5-0.8) indicates a moderate contribution of state-conditioning

**Ablation A is the experiment that could kill the thesis.** If an unconditioned VAE
generating diverse molecules from the same training data shows comparable enrichment
to the state-conditioned VAE, then the 10x enrichment reflects chemical diversity,
not conformational state-awareness. This outcome is publishable (as a controlled
negative finding), but the paper's narrative changes fundamentally.

#### Step 5: Multi-Kinase Retrospective Validation (Weeks 3-6)

Apply the full pipeline (state-aware + static baseline) to all 6 kinases with the
pre-2015 cutoff:

1. **Per-kinase enrichment:** Compute BEDROC(alpha=20) and EF@10 for each kinase,
   each pipeline
2. **Bootstrap CIs:** BCa bootstrap with 10,000 stratified resamples per kinase
3. **Pooled analysis:** Compute mean BEDROC across kinases with paired comparison
4. **If EGFR ablation A shows state-conditioning matters:** Apply ablation A
   (unconditioned VAE) to all 6 kinases as the critical control

#### Step 6: Statistical Analysis (Week 6)

Execute the pre-registered analysis plan (detailed below in Technical Details).

### Technical Details

#### Primary Endpoint

**BEDROC(alpha=20), averaged across kinases, comparing state-aware vs static.**

Justification: BEDROC uses the full ranking (not a binary threshold), has well-defined
null distributions, and gives 80% of weight to the top 8% of the ranked list. At
alpha=20, a random ranker scores ~0.0 for large databases. This makes BEDROC both more
statistically powerful and more interpretable than EF@10 for StateBind's setting.

Implementation: Use the `oddt.metrics.bedroc` function from the Open Drug Discovery
Toolkit, or implement directly from Truchon & Bayly (2007) Equation 7.

#### Secondary Endpoints

1. **EF@10** averaged across kinases (for comparability with existing literature)
2. **Per-kinase BEDROC(alpha=20)** with 95% BCa bootstrap CIs
3. **Per-kinase EF@10** with 95% BCa bootstrap CIs
4. **Mean unified score comparison** with Cohen's d and 95% CI
5. **Pareto hypervolume ratio** across kinases
6. **Chemical diversity** (mean pairwise Tanimoto distance) per pipeline per kinase

#### Bootstrap Protocol

```
BCa Bootstrap for BEDROC (per kinase):

For b = 1 to B (B = 10,000):
    1. Stratified resample: draw N_total candidates with replacement,
       stratified by active/inactive label (maintain exact N_active count)
    2. Re-rank by unified score within the bootstrap sample
    3. Compute BEDROC_b(alpha=20) for the resampled ranked list
    4. Compute EF@10_b for the resampled ranked list

Compute BCa adjustment:
    - Bias correction: z_0 = Phi^{-1}(proportion of bootstrap values < observed)
    - Acceleration: a = sum(jackknife_influence^3) / (6 * sum(jackknife_influence^2)^{3/2})
    - Adjusted percentiles: alpha_1 = Phi(z_0 + (z_0 + z_{alpha/2}) / (1 - a*(z_0 + z_{alpha/2})))
    - 95% CI: [BEDROC_(B*alpha_1), BEDROC_(B*(1-alpha_1))]
```

BCa is chosen over percentile bootstrap because DiCiccio and Efron (1996) showed BCa
intervals are second-order accurate for ratio statistics, and recent simulation studies
(Pustejovsky, 2024) confirm BCa achieves higher coverage at small sample sizes.

#### Multiple Testing Correction

**Tier 1 -- Primary endpoint:** Mean BEDROC across kinases (single test, no correction).

**Tier 2 -- Per-kinase BEDROC:** Apply Benjamini-Hochberg (BH) FDR control at q = 0.05.
BH is preferred over Bonferroni because the per-kinase tests are not independent (they
share the same pipeline) and BH provides higher power while controlling the expected
proportion of false discoveries (Benjamini & Hochberg, 1995).

Procedure for K = 6 kinases:
1. Compute p-values for each kinase (permutation test: state-aware vs static BEDROC)
2. Order p-values: p_(1) <= p_(2) <= ... <= p_(6)
3. Find largest k such that p_(k) <= (k/6) * 0.05
4. Reject H0 for all kinases with p_(i) <= p_(k)

**Tier 3 -- Exploratory:** All other metrics reported without correction, explicitly
labeled as "exploratory." This includes weight sensitivity, Pareto hypervolume,
diversity metrics, and ablation comparisons.

#### Expected Effect Sizes and Power

**Minimum detectable BEDROC difference:**

For a paired comparison across K=6 kinases with a one-sided paired t-test at alpha=0.05:
- To detect a mean BEDROC difference of 0.10 (small-to-moderate effect) with SD=0.08
  across kinases: power ~80%
- To detect a difference of 0.15 (moderate effect) with SD=0.10: power ~85%
- To detect a difference of 0.05 (very small effect): power ~45% (underpowered)

**Translation to enrichment ratio:**

| BEDROC Difference | Approximate EF@10 Ratio | Interpretation |
|-------------------|------------------------|----------------|
| < 0.05 | ~1.0-1.5x | Not practically significant |
| 0.05-0.10 | ~1.5-3.0x | Modest advantage |
| 0.10-0.20 | ~3.0-5.0x | Strong advantage |
| > 0.20 | > 5.0x | Very strong advantage |

The current EGFR result (EF@10 = 4.95 vs 0.47, ~10x ratio) would correspond to a BEDROC
difference of approximately 0.15-0.25, which is well within detectable range even with
K=6. However, we should NOT assume multi-kinase effects will be as large as EGFR. A
conservative planning estimate of BEDROC difference = 0.10 gives adequate power at K=6.

#### Per-Kinase Reference Molecule Design

Each kinase requires its own reference binders for the similarity component (35% of
unified score). The principle: use only drugs approved BEFORE the cutoff, with structural
diversity to represent the target's known pharmacology.

| Kinase | Reference Molecules (pre-2015) | Structural Diversity |
|--------|-------------------------------|---------------------|
| EGFR | Erlotinib, gefitinib | 4-anilinoquinazoline scaffold (limited diversity) |
| ABL1 | Imatinib, dasatinib, nilotinib | 3 distinct scaffolds: 2-phenylaminopyrimidine, thiazole, aminopyrimidine |
| ALK | Crizotinib, ceritinib | 2 distinct scaffolds: aminopyridine, diaminopyrimidine |
| BRAF | Vemurafenib, dabrafenib | 2 distinct scaffolds: 7-azaindole, aminopyrimidine |
| RET | Vandetanib, cabozantinib | 2 distinct scaffolds: 4-anilinoquinazoline, cabozantinyl |
| JAK2 | Ruxolitinib, tofacitinib | 2 distinct scaffolds: pyrrolopyrimidine, pyrrolopyrimidine (similar) |

**Issue: JAK2 reference molecules have limited scaffold diversity** (both are
pyrrolopyrimidines). This may make JAK2 reference similarity less discriminating.
Document this as a known limitation.

**Issue: EGFR reference set shrinks from 3 to 2 molecules** when osimertinib is removed.
This may alter the score distribution. The pre-2010 EGFR validation (which already
excludes osimertinib) serves as the clean reference.

#### Pre-Registration Protocol

All analysis decisions specified here are LOCKED before any multi-kinase experiments
are run. The protocol should be deposited on OSF (Open Science Framework) or included
as Supplementary Material with a timestamp predating the experimental runs.

**Pre-specified decisions:**
1. Primary endpoint: BEDROC(alpha=20) averaged across 6 kinases
2. Success criterion: One-sided paired t-test, p < 0.05, state-aware > static
3. Secondary endpoints: Per-kinase BEDROC with BH correction at q=0.05
4. Time-split cutoff: Pre-2015 (primary), pre-2010 (sensitivity)
5. Bootstrap: BCa with B=10,000, stratified by active/inactive
6. Exclusion: Kinases with <2 held-out drugs excluded from primary analysis
7. Ablation: Experiments A-E applied to EGFR first; extended to all kinases if
   Experiment A shows Cohen's d >= 0.5 (medium effect) between F and A on EGFR

**What is NOT pre-specified (exploratory):**
- Weight sensitivity analysis (reported for transparency, not for testing claims)
- Pareto hypervolume comparisons
- Chemical diversity comparisons
- Any new metric introduced after seeing results

#### Handling Negative or Mixed Results

**Scenario 1: State-aware wins on multi-kinase BEDROC (positive).**
Paper claim: "Conformational state-aware molecular design enriches for approved kinase
inhibitors across K kinases with mean BEDROC improvement of X (95% CI: [Y, Z])."

**Scenario 2: Ablation A kills the thesis (state-conditioning does not contribute).**
Paper pivots to: "Diverse generative design outperforms template-based design for
kinase inhibitor enrichment, but conformational state-conditioning provides no
additional benefit beyond chemical diversity." This is still a publishable and
informative finding -- it tells the field that diversity, not state-awareness, is
the active ingredient.

**Scenario 3: Mixed results (some kinases positive, some negative).**
Report per-kinase breakdown honestly. Analyze what distinguishes kinases where
state-awareness helps (e.g., conformational diversity, pocket volume differences
between states, number of PDB states available). This becomes a richer paper:
"Conformational state-awareness improves molecular design for kinases with large
inter-state pocket variability."

**Scenario 4: Multi-kinase BEDROC is not significant but per-kinase EGFR remains strong.**
Report EGFR as a case study with honest acknowledgment of non-generalization.
Investigate whether structural or pharmacological features predict which targets
benefit. This is publishable as a methodological study with partial positive results.

**The key insight: pre-registration makes ALL scenarios publishable.** The experimental
design is the contribution, not just the positive result.

---

## Impact Assessment

### Publication Impact

- **Target venue:** JCIM (primary), Nature Computational Science (aspirational if
  multi-kinase results are strong across 5+ targets)
- **Main claim this enables:** "Conformational state-aware molecular design produces
  statistically significant enrichment for approved kinase inhibitors across multiple
  kinase targets, with BEDROC(alpha=20) = X (95% CI: [Y, Z]) vs static baseline
  Z' (95% CI: [Y', Z'])."
- **Reviewer concerns this addresses:**
  1. "Where are the confidence intervals?" -- BCa bootstrap on every metric
  2. "This is only one target" -- 6 kinases with 21 held-out drugs
  3. "The comparison is confounded" -- 6-experiment ablation suite
  4. "Which metric was chosen post-hoc?" -- Pre-registered primary endpoint
  5. "How do you handle multiple comparisons?" -- BH FDR control at q=0.05
  6. "What if the result doesn't hold on other kinases?" -- Pre-specified mixed-result
     analysis plan

### Effort Estimate

- **Compute:**
  - VAE training: 5 kinases x 1 GPU-day (H200) = 5 GPU-days
  - Ablation VAE (unconditioned): 1 additional GPU-day per kinase = 6 GPU-days
  - MPNN retraining: 5 kinases x 0.5 GPU-day = 2.5 GPU-days
  - GNINA docking (optional): 5 kinases x 500 candidates x 4 states x ~2 min = ~28
    GPU-days (can be parallelized across 4 nodes for 1 week wall-time)
  - Bootstrap computation: Negligible (CPU-only, minutes per kinase)
  - **Total: ~42 GPU-days (or ~10 days wall-time with 4 parallel GPU nodes)**

- **Data:**
  - ChEMBL v34 bioactivity data for 5 kinases: freely available, download via API
  - PDB structures: freely available
  - KLIFS conformational annotations: freely available
  - FDA approval dates: BRIMR database (publicly available)
  - All data is publicly available. No proprietary data needed.

- **Implementation:**
  - Week 1-2: Structural atlas + MPNN retraining (parallel)
  - Week 2-3: EGFR ablation suite (decisive gate)
  - Week 3-5: Multi-kinase VAE training + generation + scoring
  - Week 5-6: Statistical analysis + manuscript preparation
  - **Total: 6 weeks**

- **Dependencies:**
  - Existing StateBind infrastructure (VAE, MPNN, scoring, retrospective evaluation)
  - GNINA v1.1 on GPU nodes
  - ChEMBL v34 access
  - No external collaborations required

### Risk Assessment

- **Technical risks:**
  - Some kinases may have insufficient ChEMBL data for MPNN training (RET with ~800
    pre-2015 compounds is the weakest). Mitigation: Use transfer learning from EGFR
    MPNN, fine-tuning on target-specific data.
  - ALK and RET may lack sufficient DFGout crystal structures for a clean multi-state
    atlas. Mitigation: Use at minimum 2 states (active + one inactive); document
    limited conformational coverage as a target-specific limitation.
  - GNINA docking across 5 kinases x 4 states is computationally expensive. Mitigation:
    Use MPNN as primary scoring tier; reserve GNINA for top-50 candidates per kinase.

- **Scientific risks:**
  - **The unconditioned VAE ablation may show diversity alone drives enrichment.**
    This is the single largest scientific risk. Mitigation: Pre-register the analysis
    plan so this outcome is publishable. Reframe the paper around the diversity finding
    if needed.
  - **Multi-kinase enrichment may not be significant.** Some kinases may not benefit
    from state-awareness because their conformational landscapes are less druggable.
    Mitigation: Pre-specify that per-kinase heterogeneity is expected and that the
    paper will analyze which kinase features predict benefit.
  - **Osimertinib leakage correction may reduce EGFR enrichment.** Removing osimertinib
    from pre-2015 references changes the scoring function. The clean pre-2010 result
    (which never included osimertinib) serves as the uncontaminated reference.

- **Mitigation summary:** Pre-registration is the master mitigation strategy. By
  specifying ALL analysis decisions before running experiments, any outcome becomes
  a legitimate scientific contribution.

---

## Evaluation Criteria

1. **Primary success criterion:** Mean BEDROC(alpha=20) for state-aware pipeline
   exceeds static baseline across 6 kinases (one-sided paired t-test, p < 0.05).
   This requires BEDROC_state_aware - BEDROC_static >= ~0.10 given expected variance.

2. **Ablation criterion:** Cohen's d >= 0.8 (large effect) between full state-aware
   (Experiment F) and unconditioned VAE (Experiment A) on EGFR BEDROC. This confirms
   that state-conditioning -- not just VAE diversity -- drives enrichment.

3. **CI criterion:** Lower bound of 95% BCa bootstrap CI on pooled EF@10 excludes
   1.0 (random performance). If the CI includes 1.0, the enrichment is not
   statistically significant.

4. **Generalization criterion:** At least 4 of 6 kinases show BEDROC(state-aware) >
   BEDROC(static) in the expected direction (sign test, p < 0.10).

5. **Leakage correction criterion:** EGFR enrichment remains significant (BEDROC CI
   excludes null) after removing osimertinib from pre-2015 reference set.

6. **Reproducibility criterion:** All code, data, pre-registration document, and
   intermediate artifacts are provided as supplementary material, enabling
   independent replication.

---

## Open Questions

1. **Should JAK2 be included or excluded?** JAK inhibitors have complex selectivity
   profiles (JAK1/2/3/TYK2 cross-reactivity). Including JAK2 maximizes held-out drug
   count (8+ drugs) but introduces selectivity confounding. A conservative option:
   include JAK2 in the primary analysis but run a sensitivity analysis excluding it.
   I recommend inclusion with sensitivity analysis.

2. **Pre-2010 vs pre-2015 as primary cutoff?** Pre-2015 gives more held-out drugs
   (21 vs ~12) but ALK has only 2 training drugs (crizotinib, ceritinib) -- possibly
   insufficient for a meaningful VAE. Pre-2010 is cleaner for EGFR (no osimertinib
   leakage) but many kinases have zero training drugs before 2010. I recommend
   pre-2015 as primary with pre-2010 as sensitivity.

3. **How many conformational states per kinase?** EGFR has 4 states, ABL has 3-4,
   BRAF has 3-5, but ALK and RET may only have 2. Should we require a minimum of 3
   states per kinase, or accept 2-state kinases with documented limitations? I
   recommend accepting 2+ states with explicit documentation of per-kinase structural
   coverage.

4. **Transfer learning for data-scarce kinases?** RET has only ~800 pre-2015 ChEMBL
   compounds. Training a MPNN from scratch on 800 samples may underperform. Should we
   use a kinome-wide pre-trained MPNN and fine-tune? This interacts with Vision Idea
   010 (Self-Supervised GNN Pre-Training). I recommend per-kinase training with
   transfer learning as fallback for targets with <1,000 training compounds.

5. **GNINA vs MPNN-only for multi-kinase?** GNINA docking across 5 new kinases
   requires receptor preparation and validation for each. MPNN-only scoring is faster
   but less physics-based. Should we run both and compare? I recommend MPNN as primary
   (for speed and consistency) with GNINA on top-50 candidates per kinase as
   validation layer.

6. **Should the pre-registration be deposited on OSF before running experiments?**
   Formal pre-registration on OSF provides the strongest methodological credibility
   but requires a public commitment. An alternative is timestamped supplementary
   material. For maximal reviewer credibility, I recommend OSF pre-registration.

---

## References

1. Truchon JF, Bayly CI. (2007). Evaluating Virtual Screening Methods: Good and Bad
   Metrics for the "Early Recognition" Problem. J Chem Inf Model 47(2):488-508.
   DOI: 10.1021/ci600426e.

2. Nicholls A. (2016). The statistics of virtual screening and lead optimization.
   J Comput-Aided Mol Des 30:1205-1213. DOI: 10.1007/s10822-016-9932-7.

3. Empereur-mot C, Guillemain H, Latouche A, et al. (2022). Confidence bands and
   hypothesis tests for hit enrichment curves. J Cheminformatics 14:48.
   PMC: PMC9334420.

4. Clark RD, Webster-Clark DJ. (2016). The power metric: a new statistically robust
   enrichment-type metric for virtual screening applications with early recovery
   capability. J Cheminformatics 8:1-17. DOI: 10.1186/s13321-016-0189-4.

5. DiCiccio TJ, Efron B. (1996). Bootstrap confidence intervals. Statistical Science
   11(3):189-228.

6. Benjamini Y, Hochberg Y. (1995). Controlling the false discovery rate: a practical
   and powerful approach to multiple testing. J Royal Statistical Soc B 57(1):289-300.

7. Polaris Consortium. (2025). Practically significant method comparison protocols for
   machine learning in small molecule drug discovery. J Chem Inf Model 65(18).

8. Bender A, et al. (2023). Causal inference in drug discovery and development. Drug
   Discovery Today 28(10):103737. DOI: 10.1016/j.drudis.2023.103737.

9. Backenkoehler M, et al. (2024). A comprehensive exploration of the druggable
   conformational space of protein kinases using AI-predicted structures. PLoS Comput
   Biol 20:e1012302. DOI: 10.1371/journal.pcbi.1012302.

10. Grasso M, et al. (2024). Improving docking and virtual screening performance using
    AlphaFold2 multi-state modeling for kinases. Scientific Reports 14:24305.
    DOI: 10.1038/s41598-024-75400-6.

11. Modi V, Dunbrack RL Jr. (2019). Defining a new nomenclature for the structures of
    active and inactive kinases. PNAS 116(14):6818-6827.
    DOI: 10.1073/pnas.1814279116.

12. Ung PMU, Rahman R, Schlessinger A. (2018). Redefining the Protein Kinase
    Conformational Space with Machine Learning. Cell Chem Biol 25(7):916-924.
    DOI: 10.1016/j.chembiol.2018.05.002.

13. Tropsha A. (2010). Best Practices for QSAR Model Development, Validation, and
    Exploitation. Mol Informatics 29(6-7):476-488. DOI: 10.1002/minf.201000061.

14. Joeres R, et al. (2025). Data splitting to avoid information leakage with DataSAIL.
    Nature Communications 16:3474. PMC: PMC11978981.

15. Wallach I, et al. (2024). Coverage bias in small molecule machine learning. Nature
    Communications 15:11389. PMC: PMC11718084.

16. Ackloo S, et al. (2022). CACHE (Critical Assessment of Computational Hit-finding
    Experiments): a public-private partnership benchmarking initiative. PLOS ONE.
    PMC: PMC9246350.

17. Wylie AA, et al. (2017). The allosteric inhibitor ABL001 is a potent bcr-abl1
    inhibitor with the ability to overcome resistance mutations. Nature
    543(7647):733-737.

18. Park JH, Liu Y, Lemmon MA, Radhakrishnan R. (2012). Erlotinib binds both inactive
    and active conformations of the EGFR tyrosine kinase domain. Biochem J
    448(3):417-423. DOI: 10.1042/BJ20121513.

19. Pustejovsky JE. (2024). Bootstrap confidence interval variations: simulation study.
    Blog + technical report. URL: https://jepusto.com/posts/Bootstrap-CI-variations/.

20. Clyde A, et al. (2024). Benchmarking Cross-Docking Strategies in Kinase Drug
    Discovery. J Chem Inf Model. DOI: 10.1021/acs.jcim.3c01913.

21. Roskoski R. (2025). Properties of FDA-approved small molecule protein kinase
    inhibitors: A 2025 update. Pharmacol Res 204:107083.

22. Zhao Z, et al. (2014). Conformational Analysis of the DFG-Out Kinase Motif and
    Biochemical Profiling of Structurally Validated Type II Inhibitors. J Med Chem
    58(2):466-479.

23. Fang L, et al. (2022). KinCore: a web resource for structural classification of
    protein kinases and their inhibitors. Nucleic Acids Res 50(D1):D654-D664.

24. Van Noorden R, et al. (2024). Kinase-Bench: benchmarking kinase selectivity with
    structure-based virtual screening. J Chem Inf Model (2024).

25. Helal KY, et al. (2026). From Latent Manifolds to Targeted Molecular Probes: An
    Interpretable, Kinome-Scale Generative ML Framework. Biomolecules 16(2):209.
