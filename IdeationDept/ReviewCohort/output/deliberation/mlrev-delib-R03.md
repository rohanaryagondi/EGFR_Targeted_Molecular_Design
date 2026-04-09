---
agent: Sr. Journal Reviewer -- ML & AI
round: 3
date: 2026-04-09
type: review-assessment
scope: deliberation
---

# Round 3 Deliberation: ML & AI Review

## 1. Executive Summary

After reading all five Round 2 verification reports and the Round 2 synthesis, I
update my positions on four assigned topics and provide my final assessment.

The structural annotation crisis discovered by compbiorev is the single most
consequential finding of this review process. From an ML perspective, it does not
invalidate the state-conditioned generation *mechanism* -- the VAE architecture
correctly learns to produce different molecular distributions per conditioning
label -- but it critically undermines the *semantic interpretation* of what those
labels mean. If the DFGout/aCout conditioning label actually corresponds to a DFGin
pocket (4ZAU), then the model has learned to generate molecules for "whatever
pocket 4ZAU represents," not for "the classical inactive DFGout/aCout conformation."
This distinction matters enormously for the paper's claims.

On the incremental refactoring approach, the compute-fairness question, and the
metric prioritization, I provide detailed positions below. My overall assessment:
the paper is publishable at JCIM if and only if the six Tier 0 items are completed.
The core idea (discrete state conditioning + retrospective enrichment) is sound
and verified as novel. The execution has real but fixable problems.

---

## 2. Response to Other Reviewers

### 2.1 Response to CompBioRev: Structural Annotation Errors

CompBioRev's discovery is the most important finding across both rounds. I want
to be precise about what it does and does not mean for the ML components.

**What it means for the VAE:**

The VAE's `generate()` method (vae.py:425-532) takes a `state_onehot` vector of
shape `(batch, n_states)` where `n_states=4`. During training, each molecule in
the training data is paired with a state label (vae_dataset.py:154-183). The
model learns to reconstruct molecules given their state label as a conditioning
signal, and during generation it produces molecules conditioned on a requested
state.

If 4ZAU is actually DFGin (not DFGout/aCout), then:

1. **Training data corruption:** Molecules assigned to state index 3 ("DFGout_aCout")
   based on 4ZAU's pocket were conditioned on a label that does not match the
   pocket's true conformation. The model learned "state 3 = molecules that score
   well in pocket 4ZAU" rather than "state 3 = molecules for DFGout/aCout pockets."

2. **Generation quality:** When we generate with `state_onehot[:, 3] = 1.0`
   (generate_vae_candidates.py:161-162), the model produces molecules tuned for
   pocket 4ZAU. If that pocket is DFGin, we are generating DFGin-like molecules
   while calling them DFGout/aCout candidates. The molecules themselves may be
   perfectly valid -- but our interpretation of *why* they work is wrong.

3. **Enrichment impact:** The retrospective enrichment calculation uses ALL
   state-aware candidates pooled together. If DFGout/aCout candidates are actually
   DFGin candidates (because the pocket was misclassified), they may still
   contribute to enrichment -- they are molecules designed for a real EGFR pocket,
   just not the one we claim. The enrichment *number* may hold up. The enrichment
   *narrative* ("state-aware design accesses inactive conformations that static
   design misses") is undermined.

**What it does NOT invalidate:**

- The VAE architecture itself: conditional generation on discrete labels is a
  valid ML technique regardless of what the labels represent.
- The training procedure: the model was trained correctly given its inputs.
- The ablation framework: comparing conditioned vs. unconditioned VAE remains
  the most important ablation regardless of label correctness.
- The enrichment calculation mechanics: EF@10 is computed correctly.
- The MPNN, ADMET, and docking components: these are independent of state labels.

**Bottom line:** The structural issue is a *data curation* error, not an
*algorithmic* error. It requires fixing the data and re-running, not redesigning
the architecture. I agree with compbiorev that this is Tier 0, Item 0.

### 2.2 Response to Principal: Incremental ABL1 Refactoring

The principal's file-by-file analysis (15 source files, 8 configs, 14 test files,
162 EGFR references) is the most useful artifact produced by any reviewer in this
process. The incremental approach (6-9 weeks alongside EGFR with backward-
compatible defaults) versus full generalization (16-22 weeks) is a clear win.

**From an ML rigor perspective, the incremental approach is acceptable IF:**

1. **The ABL1 parameterization is documented as ABL1-specific.** The pocket
   conditions in `conditioning.py` (lines 54-123) contain hardcoded EGFR pocket
   volumes, gatekeeper clearances, and hinge accessibilities. Adding ABL1
   alongside these requires creating a parallel set of ABL1-specific values.
   These must be sourced from published ABL1 crystallography (e.g., 1IEP for
   DFGin/aCin, 1OPJ for DFGout) with the same level of citation as the EGFR
   values should have had.

2. **The VAE is retrained per target, not shared.** A single VAE trained on EGFR
   molecules cannot be applied to ABL1 without retraining. The training data for
   ABL1 must be curated from ChEMBL ABL1 binders, with state labels assigned
   based on ABL1 pocket structures. This is not a refactoring task -- it is a
   data curation + training task (estimated: 1-2 weeks for ABL1 data curation,
   2-3 days for VAE retraining).

3. **The MPNN needs separate evaluation per target.** The MPNN trained on EGFR
   pIC50 data cannot predict ABL1 binding affinity without retraining on ABL1
   data. Either: (a) retrain a separate MPNN on ChEMBL ABL1 affinity data, or
   (b) use a pre-trained multi-target model (e.g., Chemprop with multi-task
   learning on multiple kinases). Option (a) is simpler and more controlled.

4. **Retrospective validation requires ABL1 drug timeline.** The principal
   identified this (section 3.4): ABL1 has an excellent drug timeline (imatinib
   2001, dasatinib 2006, nilotinib 2007, bosutinib 2012, ponatinib 2012,
   asciminib 2021). Pre-2010 cutoff gives 3 drugs as reference, 3 as "future."
   This is actually a better retrospective test than EGFR.

**Where the incremental approach creates ML debt:**

- Hard-coded defaults scattered across 15+ files are a reproducibility hazard.
  If a future user clones the repo and does not realize they need to set
  `target="ABL1"` in 8 different config files, they will silently run the EGFR
  pipeline on ABL1 data.
- The test suite (14 test files, 162 EGFR references) will need parallel ABL1
  test cases. Without these, regressions in ABL1 support will go undetected.

**My recommendation:** Accept the incremental approach for the first paper, but
add a `target` field to the top-level pipeline config (`configs/default.yaml`)
that propagates to all sub-configs. This is a 2-3 day refactoring that prevents
the scattered-default problem. The principal's approach of backward-compatible
defaults (EGFR if not specified) is correct.

### 2.3 Response to Associate: DiffSBDD Assessment

I agree with the associate's assessment that DiffSBDD is the most practical 3D
baseline despite its maintenance issues (29 open / 0 closed issues). The key
question for Round 3 is whether a 3D baseline is mandatory for JCIM. My position:

**For JCIM: a 3D baseline is NOT mandatory but IS recommended.** JCIM reviewers
will expect comparison against established SBDD methods, but these can be ligand-
based (REINVENT 4) rather than 3D structure-based. The REINVENT 4 comparison
(already planned, 8-15 days) provides a strong RL baseline. DiffSBDD adds value
primarily for NeurIPS / Nature Comp Sci, where 3D baselines are standard.

**Revised position from Round 1:** I initially advocated for including DiffSBDD
in the JCIM submission. Given the structural annotation issue, the DiffSBDD setup
time (1-2 weeks realistic), the CrossDocked2020 EGFR overlap concern, and the
16-week timeline pressure, I now agree with progdir that DiffSBDD should be
deferred to Paper 2 or revision response. The REINVENT 4 comparison is sufficient
for JCIM.

### 2.4 Response to ProgDir: Timeline and Publication Strategy

I endorse Scenario B (16 weeks) with the ChemRxiv preprint at week 6-8. The
progdir's scooping risk assessment (15-20% at 6 months) is reasonable given the
verified competitor landscape. The key constraint I add: the preprint must not
go up until the structural annotations are corrected and the ablation C result
(conditioned vs. unconditioned VAE) is known. A preprint with known structural
errors would be worse than no preprint.

**Minimum viable preprint content:**
- Corrected structural atlas (Tier 0 complete)
- Scaffold-split MPNN evaluation
- Ablation C result (conditioned vs. unconditioned)
- Compute-matched comparison on EGFR
- Bootstrap CIs on enrichment

**Content that can wait for the JCIM submission:**
- ABL1 extension
- REINVENT 4 comparison
- Full survival funnel
- FCD / #Circles analysis

---

## 3. Evaluation Metrics: Mandatory vs. Nice-to-Have

I categorize every discussed metric by venue requirement. The guiding principle:
JCIM reviewers care about chemical validity and practical drug design relevance;
NeurIPS reviewers care about fair ML evaluation and benchmarking rigor.

### 3.1 MANDATORY for JCIM (Paper Will Be Rejected Without These)

| Metric | Justification | Effort | Status |
|--------|--------------|--------|--------|
| **BEDROC + bootstrap CIs** | Standard enrichment metric with uncertainty. Without CIs, enrichment factors are point estimates with unknown reliability. BEDROC is the standard for virtual screening enrichment at JCIM (Truchon & Bayly, 2007). | Hours | Planned |
| **Scaffold-split MPNN evaluation** | Random-split R^2=0.69 is scientifically meaningless for predicting performance on novel scaffolds. Every JCIM reviewer in 2026 knows to ask about split type. Report both random and scaffold R^2. | 2-3 days | Not started |
| **Fixed oracle call budget comparison** | The 30 vs. 461 candidate ratio is indefensible. PMO (Gao et al., NeurIPS 2022) established 10K-call budgets as the gold standard. At minimum: equalize the number of scored candidates across pipelines. Report AUC of top-10 average score vs. oracle calls. | 1-2 weeks | Not started |
| **Reconstruction accuracy for VAE** | JCIM reviewers will ask "does your VAE actually learn chemistry?" The cross-entropy loss (val_recon=2.26) is not interpretable. Report: fraction of training molecules perfectly reconstructed (encode -> decode -> exact SMILES match). | 1-2 days | Not started |

### 3.2 STRONGLY RECOMMENDED for JCIM (Paper Is Weaker Without Them)

| Metric | Justification | Effort | Status |
|--------|--------------|--------|--------|
| **FCD (Frechet ChemNet Distance)** | The single most informative generative quality metric. Measures distributional similarity in learned chemical feature space (Preuer et al., 2018). FCD < 1.0 is generally good. Compute between: generated vs. training, generated vs. ChEMBL EGFR actives, per-state generated vs. each other. `fcd_torch` is pip-installable. | 3-5 days | Not started |
| **Property distribution tests (KS/MMD)** | Compare MW, LogP, QED, TPSA distributions of generated vs. training molecules. KS test for individual properties, MMD for multivariate comparison. This is standard in MOSES (Polykovskiy et al., 2020) and expected at JCIM. | 2-3 days | Not started |
| **Conformal prediction via TorchCP** | Provides calibrated uncertainty intervals for MPNN predictions. "This molecule has predicted pIC50 = 7.2 +/- 0.8 at 90% coverage" is far more useful than a point estimate. TorchCP (Huang et al., 2024, JMLR) is PyTorch-native with GNN support. | 1 week | Not started |

### 3.3 NICE-TO-HAVE for JCIM (Differentiators, Not Requirements)

| Metric | Justification | Effort | Status |
|--------|--------------|--------|--------|
| **#Circles / SEDiv** | Modern diversity metric that measures chemical space coverage rather than mean pairwise distance (Blaschke et al., 2024, JCIM). IntDiv can be gamed; #Circles cannot. Becoming expected at NeurIPS D&B but not yet standard at JCIM. | 2-3 days | Not started |
| **Latent space interpolation** | Qualitative evidence that the VAE latent space is smooth: interpolate between two encoded molecules and show chemically sensible intermediates. Visual, not quantitative. | 1-2 days | Not started |
| **Per-state FCD comparison** | Compute FCD between state-specific generated sets. If the VAE truly learns state-specific chemistry, FCD between DFGin_aCin and DFGout_aCin generated sets should be meaningfully different from FCD between two random subsamples of the same state. | 1 day (if FCD already computed) | Not started |

### 3.4 MANDATORY for NeurIPS Upgrade (If Targeting NeurIPS 2027)

| Metric | Justification | Effort |
|--------|--------------|--------|
| **PMO-style AUC curves** | Full AUC of top-10 average score vs. oracle calls, plotted for all methods, with standard deviation across random seeds. PMO benchmark standard. | 2 weeks |
| **#Circles under fixed budget** | Diversity-quality tradeoff under compute constraints (Blaschke et al., 2024). | 1 week |
| **DiffSBDD or MolPilot 3D baseline** | 3D structure-conditioned baseline with training data overlap analysis. Expected at any ML venue for SBDD benchmarking. | 2-3 weeks |
| **Multi-seed evaluation** | All results reported as mean +/- std across 3-5 random seeds. Non-negotiable at NeurIPS. | 1-2 weeks extra |
| **Ablation over all components** | Full ablation table: conditioning, docking, MPNN, ADMET, pocket descriptors. | 2-3 weeks |

### 3.5 Metric Summary Table

| Metric | JCIM | NeurIPS | Priority |
|--------|------|---------|----------|
| BEDROC + bootstrap CIs | MANDATORY | MANDATORY | Tier 0 |
| Scaffold-split MPNN | MANDATORY | MANDATORY | Tier 0 |
| Fixed oracle call budget | MANDATORY | MANDATORY | Tier 1 |
| Reconstruction accuracy | MANDATORY | MANDATORY | Tier 0 |
| FCD | RECOMMENDED | MANDATORY | Tier 1 |
| Property distributions (KS/MMD) | RECOMMENDED | MANDATORY | Tier 2 |
| Conformal prediction (TorchCP) | RECOMMENDED | RECOMMENDED | Tier 2 |
| #Circles / SEDiv | NICE-TO-HAVE | MANDATORY | Tier 2 |
| Latent interpolation | NICE-TO-HAVE | NICE-TO-HAVE | Tier 3 |
| Per-state FCD | NICE-TO-HAVE | RECOMMENDED | Tier 2 |
| PMO AUC curves | NICE-TO-HAVE | MANDATORY | Tier 3 |
| 3D baseline | NICE-TO-HAVE | MANDATORY | Tier 4 |
| Multi-seed | NICE-TO-HAVE | MANDATORY | Tier 3 |

---

## 4. Structural Issue: ML Impact Assessment

### 4.1 Precise Scope of Contamination

The structural annotation errors affect the ML pipeline through exactly two
pathways:

**Pathway 1: VAE training data state labels.**

The VAE training data (loaded via `vae_dataset.py:257-343`) associates each
molecule with a state label string (e.g., "DFGout_aCout"). These labels
determine the one-hot conditioning vector during training. If 4ZAU is DFGin,
then molecules assigned to "DFGout_aCout" based on 4ZAU were trained with an
incorrect label. The model learned to associate those molecules' chemical
features with state index 3, but that state index actually represents a DFGin
pocket.

**Quantitative impact estimate:** The DFGout_aCout state contributes
approximately 25% of the state-conditioned training signal (1 of 4 states).
If 4ZAU is confirmed DFGin, approximately 25% of the conditional training
data has corrupted labels. The other 75% (DFGin_aCin via 1M17, DFGin_aCout
via 2GS7, and DFGout_aCin via 3iku/3W2R) is also problematic because:

- DFGout_aCin structures (3iku, 3W2R) are mutants, not WT. The molecules
  assigned to this state were matched against mutant pockets. The state
  label is directionally correct (these ARE DFGout structures) but the
  pocket descriptors reflect mutant geometry.

**Net assessment: 2 of 4 states have significant label/pocket issues.**
DFGout_aCin has correct conformation but mutant pockets; DFGout_aCout may
have wrong conformation entirely. DFGin_aCin (1M17, WT) and DFGin_aCout
(2GS7, WT) appear correct.

**Pathway 2: GNINA docking receptor structures.**

The docking cascade uses PDBQT files prepared from the representative structures.
If 3W2R (mutant) was used for DFGout_aCin docking, the docking scores reflect
binding to a mutant pocket. This affects the docking component of the unified
score but not the MPNN or ADMET components.

### 4.2 Does This Invalidate State-Conditioned Results?

**No, but it severely limits what can be claimed.**

The state-conditioning mechanism works correctly at the ML level: the VAE
demonstrably produces different molecular distributions for different state
indices (the per-state candidate sets have different property profiles). The
question is whether these differences are *meaningful* -- i.e., whether they
correspond to real conformational biology.

**What can still be claimed:**
- "The VAE learns to produce distinct molecular populations when conditioned on
  different labels" -- this is an architecture/ML claim, verifiable by comparing
  per-state FCD.
- "The pooled state-conditioned candidates achieve higher retrospective enrichment
  than unconditioned candidates" -- this is the ablation C result, which tests
  whether ANY state conditioning helps, regardless of label correctness.
- "Conditioning on pocket-specific labels improves generation diversity compared
  to single-pocket design" -- this is a diversity claim, testable via #Circles.

**What CANNOT be claimed until structures are fixed:**
- "Molecules conditioned on DFGout states are suitable for Type II inhibitor
  design" -- cannot claim if DFGout pockets are mutants.
- "State-conditioning captures the biology of conformational selection" -- cannot
  claim if state labels do not match conformations.
- "The four-state model reflects the EGFR conformational landscape" -- cannot
  claim if 4ZAU may be misclassified.

### 4.3 Remediation Path

**Scenario A: 4ZAU confirmed as DFGout (KLIFS classification is correct).**

This is the optimistic scenario. Impact is limited to the mutation annotation
errors (3W2R, 5D41, 3iku). Fix: disclose that DFGout structures are from
clinically relevant mutants (T790M/L858R), argue that the conformational
difference dominates the mutational difference (pocket volume analysis), and
proceed with corrected annotations. Re-run: only docking against corrected
receptors (if receptor preparation was affected). VAE retraining: not required.

**Scenario B: 4ZAU confirmed as DFGin (compbiorev's hypothesis is correct).**

This is the harder scenario. The DFGout_aCout state has no valid representative
structure. Options:

1. **3-state model:** Drop DFGout_aCout entirely. Retrain VAE with `n_states=3`.
   Re-generate candidates. Re-run enrichment. This is the cleanest approach.
   Effort: 1-2 weeks. Risk: lower -- 3 states are still more than 1 (static
   baseline). The paper becomes "3-state model vs. static" which is still novel.

2. **DFGmodel homology model:** Use a computationally generated DFGout/aCout
   structure from DFGmodel (Ung & Schlessinger, 2015). Disclose this explicitly.
   Risk: reviewers may question docking against a homology model. But this is
   defensible if the homology model is validated against known DFGout kinases
   (e.g., ABL1 DFGout structures exist for WT).

3. **Use mutant DFGout/aCout with disclosure:** Keep 5D41 (L858R/T790M) but
   disclose mutations. Argue that the pocket geometry is similar enough. Risk:
   high -- conflates mutational and conformational effects.

**My recommendation:** Pursue Scenario B, Option 1 (3-state model) as the default
plan. If the 4ZAU 3D inspection (1-2 hours) confirms it is DFGin, drop to 3
states immediately. The 3-state model is still novel (no one does even 2-state
conditioning), the enrichment should still hold (the DFGin_aCin and DFGin_aCout
states are unaffected), and the paper is more honest. Report the 4ZAU issue as
a "lesson learned" in the discussion.

---

## 5. Critical Ablations (Ranked)

These are the three ablations that the paper absolutely must contain, in order
of importance. Without any one of these, a reviewer at JCIM or above can reject
the paper on methodological grounds.

### 5.1 Ablation C: Conditioned vs. Unconditioned VAE (RANK 1)

**What:** Train an identical VAE architecture without the state conditioning
vector. Generate the same number of candidates. Score and compute enrichment.

**Why this is #1:** This is the paper's thesis test. If an unconditioned VAE
(same architecture, same training data, no state labels) achieves the same
enrichment, the entire state-conditioning contribution is null. Every reviewer
will ask for this.

**Go/no-go criterion:** Cohen's d >= 0.8 between conditioned and unconditioned
enrichment distributions (pre-registered). If Cohen's d < 0.5, the paper's
thesis is not supported and needs major revision. If 0.5 <= d < 0.8, the effect
is present but modest -- reframe claims accordingly.

**Implementation:** Remove `state_onehot` from the `generate()` call (replace
with zeros or remove the concatenation). Train for the same number of epochs.
Generate the same number of candidates per random seed. Compute EF@10, BEDROC
with bootstrap CIs. Report across 3+ seeds.

**Effort:** 1-2 weeks (retrain VAE without conditioning, generate, score, compute).

**Note on structural issue interaction:** This ablation remains valid even if
the structural annotations are wrong. We are testing "does ANY conditioning
help?" not "are the labels correct?" If the conditioned VAE beats the
unconditioned VAE even with partially wrong labels, it suggests that the
conditioning mechanism has value and would perform even better with correct
labels.

### 5.2 Ablation E: Scoring Component Contribution (RANK 2)

**What:** Systematically remove each of the 4 scoring components (GNINA docking,
MPNN affinity, drug-likeness, ADMET) one at a time and re-rank candidates.
Report enrichment change per component removal.

**Why this is #2:** Reviewers will ask "which component drives the enrichment?"
If removing GNINA (physics-based docking) has no effect but removing MPNN
(learned) has large effect, this suggests the enrichment is driven by the
learned component, which raises questions about data leakage. If the opposite,
the enrichment is driven by physics, which is more defensible.

**Go/no-go criterion:** No single component removal should cause enrichment to
drop below 1.0 (random). If it does, the pipeline is fragile and depends
entirely on that one component -- this is a concern but not fatal.

**Implementation:** Modify scoring weights to zero one component at a time.
Re-rank. Report EF@10 with CIs for each ablation.

**Effort:** 2-3 days (scoring is fast; this is mostly analysis).

### 5.3 Ablation on Candidate Pool Size (RANK 3)

**What:** Fix the candidate pool size across pipelines. Generate N candidates
from the unconditioned static pipeline and N candidates from the state-aware
pipeline. Compare enrichment at matched N.

**Why this is #3:** This directly addresses the compute-fairness concern (CF3).
If the state-aware pipeline's advantage disappears when both pipelines generate
the same number of candidates, the enrichment is explained by diversity/quantity,
not state-awareness. This is closely related to the fixed oracle call budget
requirement (Section 3.1) but conceptually distinct: oracle call budget controls
compute cost, while pool size ablation controls sample diversity.

**Go/no-go criterion:** State-aware enrichment must exceed static enrichment at
matched pool sizes of N=100, N=250, and N=500. If advantage holds only at
N=500, the effect is driven by diversity; if it holds at N=100, the effect is
driven by state conditioning.

**Implementation:** Subsample state-aware candidates to match static pool size.
Or generate more static candidates to match state-aware pool size (preferred --
tests the static pipeline at scale). Report EF@10 at each N.

**Effort:** 1 week (requires generating more static candidates or careful
subsampling with multiple seeds).

---

## 6. NeurIPS-Scale Rating for JCIM Submission

**Rating: 6.5 / 10** (Conditional Accept at JCIM, assuming Tier 0 items completed)

### 6.1 Justification

**Strengths (what earns points):**

- **Verified novelty (S1).** No published paper conditions on discrete
  conformational state labels for molecular generation. CompBioRev's exhaustive
  40+ search verification and progdir's competitive landscape analysis both
  confirm this. This alone merits publication as a benchmark/methodology paper.
  (+2.0 points)

- **Retrospective enrichment framework (S2).** Using approved drug timelines
  as ground truth for evaluating molecular generation is a compelling evaluation
  strategy. EF@10 of 4.95-7.72 (state-aware) vs 0.47-0.79 (static) is a large
  effect if it holds under fair comparison. (+1.5 points)

- **Engineering quality (S3).** 646 passing tests, 91 source files, 12
  subpackages, typed Python, Pydantic models. This is publication-quality
  infrastructure. The principal's code inspection confirms real software
  engineering discipline. (+1.0 point)

- **Practical kinase biology framing (S4).** The connection between DFG/aC
  conformational states and Type I/II inhibitor selectivity is well-established
  in medicinal chemistry literature (Davis et al., 2011; Muller et al., 2015).
  Framing the ML problem around real pharmacological categories adds biological
  relevance. (+1.0 point)

- **Extensibility to multiple kinases (S5).** ABL1 has excellent retrospective
  validation potential (6 approved drugs, 2001-2021). Demonstrating the same
  approach on a second target substantially strengthens the paper. (+1.0 point)

**Weaknesses (what loses points):**

- **Structural annotation errors (W1).** 3W2R and 5D41 are mutants listed as WT.
  3iku may be wrong PDB ID entirely. 4ZAU may be misclassified DFGin. This is a
  data integrity problem that undermines the biological narrative. Fixable but
  currently a serious concern. (-1.5 points)

- **MPNN random split (W2).** R^2=0.69 on random split is uninformative for
  assessing generalization to novel scaffolds. This is a known pitfall and the
  fact that it was not caught during development suggests insufficient ML
  evaluation rigor. Easy fix (2-3 days) but currently published-blocking.
  (-1.0 point)

- **Compute-unfair comparison (W3).** 30 vs 461 candidates is a 15:1 ratio.
  PMO (500+ citations) established fixed oracle call budgets as the standard
  in 2022. This comparison would be immediately flagged by any ML-aware
  reviewer. (-1.0 point)

- **Vacuous validity metric (W4).** Reporting 99.9% validity for a SELFIES-based
  model is like reporting that a calculator gives correct arithmetic -- it is
  the representation that guarantees this, not the model. Minor issue but signals
  insufficient awareness of generative model evaluation standards. (-0.5 points)

### 6.2 Conditions for Rating Improvement

| Action | Rating Improvement |
|--------|-------------------|
| Fix structural annotations + disclose | +0.5 -> 7.0 |
| Scaffold-split MPNN + report both | +0.5 -> 7.5 |
| Compute-matched comparison | +0.5 -> 8.0 |
| Ablation C positive result (d >= 0.8) | +1.0 -> 9.0 |
| ABL1 replication | +0.5 -> 9.5 |
| FCD + proper VAE metrics | +0.5 -> 10.0 |

With all Tier 0 + Tier 1 items completed and a positive ablation C result, this
paper reaches 9.0-9.5 -- a strong accept at JCIM and competitive for Nature
Computational Science.

### 6.3 Venue Recommendation

| Venue | Current Readiness | After Tier 0+1 | After Full Plan |
|-------|-------------------|----------------|-----------------|
| JCIM | Reject | Accept | Strong Accept |
| J. Cheminform. | Weak Accept | Accept | Strong Accept |
| Nature Comp Sci | Reject | Borderline | Competitive |
| NeurIPS D&B | Reject | Reject | Borderline |
| ICML | Reject | Reject | Weak Accept |

**Primary target: JCIM.** This is the right venue for a benchmark paper
comparing molecular generation strategies for kinase targets. JCIM reviewers
will appreciate the medicinal chemistry framing, the retrospective validation,
and the practical focus.

**Aspirational target: Nature Computational Science.** Achievable if: (a)
ablation C shows strong effect, (b) ABL1 + BRAF replication succeeds, (c)
3D baseline comparison is included, (d) the paper is framed as a
"computational framework" contribution rather than a methods paper.

---

## 7. Final Recommendations

### 7.1 Priority-Ordered Action Items (My Final Ranking)

**Tier 0: Publication blockers (must complete before any submission)**

1. Verify 4ZAU DFG conformation via 3D coordinate inspection (1-2 hours)
2. Fix structural annotations: mutation status for 3W2R, 5D41; PDB ID for 3iku (days)
3. Decide 3-state vs 4-state model based on 4ZAU inspection result (hours)
4. Fix osimertinib reference leakage (hours)
5. Implement MPNN scaffold + temporal splitting; report both R^2 values (2-3 days)
6. Compute VAE reconstruction accuracy (exact SMILES match rate) (1-2 days)
7. Bootstrap CIs + BEDROC on current enrichment results (hours)
8. Write pre-registration document for ablation C (hours)

**Tier 1: Critical path for JCIM submission**

9. Ablation C: conditioned vs. unconditioned VAE (1-2 weeks) -- GO/NO-GO GATE
10. Fixed oracle call budget comparison (1-2 weeks)
11. FCD computation via fcd_torch (3-5 days)
12. Multi-kinase ABL1 extension: data curation + VAE retraining (3-4 weeks)
13. REINVENT 4 GNINA integration (8-15 days)
14. Ablation E: scoring component contribution (2-3 days)

**Tier 2: Strengthening for JCIM + preparation for aspirational venues**

15. ABL1 full pipeline + retrospective enrichment
16. Ablation on candidate pool size at matched N (1 week)
17. Conformal prediction for MPNN via TorchCP (1 week)
18. Property distribution tests (KS/MMD for MW, LogP, QED, TPSA) (2-3 days)
19. Per-state FCD comparison (1 day after FCD infrastructure exists)
20. Dirichlet scoring sensitivity analysis (3-5 days)
21. Chemical space UMAP visualization (2-3 days)

**Tier 3: Enhancement / Paper 2**

22. ChemRxiv preprint (week 6-8 of Scenario B)
23. #Circles / SEDiv diversity analysis (2-3 days)
24. Survival funnel (ADMETlab 3.0 + AiZynthFinder) (1-2 weeks)
25. BRAF extension (contingent on ABL1 success)
26. 3D baseline (DiffSBDD) -- deferred to revision or Paper 2

**Tier 4: Post-publication**

27. PMO benchmark integration
28. Multi-seed evaluation (3-5 seeds, all results)
29. Full multi-kinase generalization beyond incremental
30. NeurIPS 2027 submission with full benchmark suite

### 7.2 Go/No-Go Gates

| Gate | Criterion | Consequence of Failure |
|------|-----------|----------------------|
| 4ZAU conformation | DFG-Asp/Phe distance + aC K745-E762 salt bridge | If DFGin: drop to 3-state model |
| Ablation C | Cohen's d >= 0.8 conditioned vs unconditioned | If d < 0.5: major revision needed; fundamental question about state conditioning value |
| Scaffold-split MPNN | R^2 >= 0.35 on scaffold split | If R^2 < 0.25: MPNN contribution to scoring is noise; consider removing or replacing |
| Compute-matched enrichment | State-aware EF@10 > 2.0 at matched oracle calls | If EF@10 < 1.5: enrichment advantage may be explained by sample diversity, not state conditioning |
| ABL1 enrichment | EF@10 > 1.5 on ABL1 pre-cutoff validation | If EF@10 < 1.0: generalization claim fails; reframe as EGFR-specific case study |

### 7.3 Final Position Statement

The StateBind project has a genuinely novel contribution (verified) embedded in
an execution that has real but fixable problems (structural annotations, random
splits, compute-unfair comparison). The core ML architecture (conditional
SELFIES VAE with state-specific generation) is sound. The retrospective
enrichment framework is compelling. The engineering quality is high.

The path to a strong JCIM paper is clear: fix the data issues (Tier 0), run the
key ablation (Tier 1, item 9), extend to ABL1 (Tier 1, item 12), and report
proper metrics. If ablation C is positive and ABL1 replicates, this is a 9/10
paper at JCIM and competitive at Nature Computational Science.

The three things I would tell the authors:

1. **Fix your data before running more experiments.** The structural annotations
   are the foundation. Everything built on incorrect labels is wasted compute.

2. **Ablation C is your thesis test.** If conditioned beats unconditioned, you
   have a paper. If not, you have an infrastructure contribution, not a science
   contribution. Run this early.

3. **Report honestly.** The MPNN R^2 will drop with scaffold splits. The
   enrichment may narrow with compute matching. Report both the favorable and
   unfavorable numbers. Honest reporting of imperfect results is stronger than
   cherry-picked metrics.

---

## 8. References

1. Gao, W., Fu, T., Sun, J., & Coley, C. W. (2022). Sample Efficiency Matters:
   A Benchmark for Practical Molecular Optimization. *NeurIPS*, 35.

2. Preuer, K., et al. (2018). Frechet ChemNet Distance: A Metric for Generative
   Models for Molecules in Drug Discovery. *JCIM*, 58(9), 1736-1741.

3. Blaschke, T., et al. (2024). Diverse Hits in De Novo Molecule Design:
   Diversity-Based Comparison of Goal-Directed Generators. *JCIM*.
   DOI: 10.1021/acs.jcim.4c00519.

4. Huang, W., et al. (2024). TorchCP: A Python Library for Conformal Prediction.
   *JMLR*, 26, 1-7.

5. Polykovskiy, D., et al. (2020). Molecular Sets (MOSES): A Benchmarking
   Platform for Molecular Generation Models. *Front. Pharmacol.*, 11, 565644.

6. Truchon, J.F. & Bayly, C.I. (2007). Evaluating Virtual Screening Methods:
   Good and Bad Metrics for the "Early Recognition" Problem. *JCIM*, 47(2),
   488-508.

7. Yang, K., et al. (2019). Analyzing Learned Molecular Representations for
   Property Prediction. *JCIM*, 59(8), 3370-3388.

8. Heid, E., et al. (2024). A systematic study of key elements underlying
   molecular property prediction. *Nat. Commun.*, 15, 7555.

9. Gorantla, R., et al. (2024). Scaffold Splits Overestimate Virtual Screening
   Performance. *RECOMB*, Springer.

10. Wu, Z., et al. (2018). MoleculeNet: A Benchmark for Molecular Machine
    Learning. *Chem. Sci.*, 9(2), 513-530.

11. Krenn, M., et al. (2020). Self-referencing embedded strings (SELFIES): A 100%
    robust molecular string representation. *MLST*, 1(4), 045024.

12. Davis, M.I., et al. (2011). Comprehensive analysis of kinase inhibitor
    selectivity. *Nat. Biotechnol.*, 29, 1046-1051.

13. Muller, S., et al. (2015). Conformational Analysis of the DFG-Out Kinase
    Motif and Biochemical Profiling. *J. Med. Chem.*, 58, 1610-1629.

14. Ung, P.M.U. & Schlessinger, A. (2015). DFGmodel: Predicting Protein Kinase
    Structures in Inactive States. *ACS Chem. Biol.*, 10, 269-278.

15. Loeffler, H.H., et al. (2024). REINVENT4: Modern AI-driven generative
    molecule design. *J. Cheminform.*, 16, 20.

16. Pham, T.H., et al. (2025). Fuzz Testing Molecular Representation Using Deep
    Variational Anomaly Generation. *JCIM*. DOI: 10.1021/acs.jcim.4c01876.

17. Schneuing, A., et al. (2024). Structure-based drug design with equivariant
    diffusion models. *Nat. Comput. Sci.*, 4, 899-909.

18. Guo, J., et al. (2024). Augmented Memory: Sample-Efficient Generative
    Molecular Design with Reinforcement Learning. *JACS Au*, 4(6), 2159-2172.

19. fcd_torch: Frechet ChemNet Distance on PyTorch. GitHub:
    insilicomedicine/fcd_torch.

20. TorchCP: PyTorch Conformal Prediction. GitHub: ml-stat-Sustech/TorchCP.
