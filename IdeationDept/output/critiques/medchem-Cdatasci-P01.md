---
agent: Senior Medicinal Chemist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: datasci-P01
---

# Critique: Multi-Kinase Retrospective Validation with Pre-Registered Statistical Design

## Reviewing Agent

Dr. Senior Medicinal Chemist -- 20+ years in kinase drug discovery, lead optimization
through clinical candidate selection. Reviewing this proposal through the lens of
clinical appropriateness of kinase selection, medicinal chemistry credibility of
reference molecules, and whether the per-kinase validation design tests what it claims
to test about conformational state-aware drug design.

## Proposal Summary

datasci-P01 proposes expanding StateBind's retrospective validation from EGFR alone to
6 kinases (EGFR, ABL1, BRAF, ALK, RET, JAK2), using BEDROC(alpha=20) as the primary
endpoint with BCa bootstrap confidence intervals, Benjamini-Hochberg correction for
multiple comparisons, and a 6-experiment ablation suite to isolate the contribution of
state-conditioning. The pre-2015 temporal cutoff serves as the primary analysis.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The statistical framework is rigorous and necessary, but the kinase
selection and reference molecule assignments reveal several medicinal chemistry blind
spots that could undermine the clinical credibility of the validation.

---

## Strengths

1. **Pre-registration eliminates the biggest publication risk.** The proposal correctly
   identifies that pre-specifying the analysis plan makes any outcome -- positive,
   negative, or mixed -- publishable. This is the single most important methodological
   decision in the entire IdeationDept agenda. A medicinal chemist reviewing a JCIM
   submission will be far more receptive to a pre-registered design than to a post-hoc
   analysis, regardless of the result. The CACHE Challenge precedent is well-cited.

2. **The ablation suite is exactly what was missing.** Experiment A (unconditioned VAE)
   is the experiment that should have been run from the beginning. Any medicinal chemist
   reviewing the current 10x enrichment claim will immediately ask: "Is this because of
   state-awareness, or because your VAE generates more diverse molecules than template
   modification?" The 6-experiment ablation hierarchy (F vs A vs D vs B vs C vs E) is
   well-designed to dissect this. The quantitative thresholds (Cohen's d >= 0.8 for
   "large gap") provide clear decision criteria.

3. **BEDROC is the right primary metric.** EF@10 is fragile at small sample sizes --
   moving one drug by 2 rank positions changes the metric by 20%. A medicinal chemist
   understands that small rank perturbations are meaningless noise (a 0.5 kcal/mol
   docking score difference, a 0.02 Tanimoto similarity difference). BEDROC uses the
   full ranking and is more robust to these perturbations. The proposal's analysis of
   EF@10 confidence intervals (spanning from below 1.0 to above 9.0 with N=5) is a
   sobering and honest assessment of the current data's statistical weakness.

4. **Handling of negative and mixed results is mature.** Scenario 2 ("ablation A kills
   the thesis") and Scenario 3 ("mixed results across kinases") are described with
   specific pivot narratives. This is exactly the kind of intellectual honesty that
   makes a proposal credible. A medicinal chemist is more likely to trust a paper that
   anticipated failure modes than one that presents only the positive story.

5. **The bootstrap protocol is technically sound.** BCa bootstrap with stratified
   resampling and jackknife-based acceleration correction is appropriate for ratio
   statistics at small sample sizes. The citation of DiCiccio and Efron (1996) and
   Pustejovsky (2024) demonstrates statistical rigor that exceeds what most computational
   chemistry papers provide.

## Weaknesses

1. **RET and JAK2 are structurally infeasible -- the proposal ignores structbio's critical
   finding.**

   structbio-R02 (incorporated into the Round 2 synthesis) showed definitively that RET
   has 0 DFGout PDB chains (100% active conformations) and JAK2 JH1 has 0 DFGout chains
   (100% DFGin). The entire thesis of StateBind is that conformational state-awareness
   drives enrichment. You cannot test state-aware design on kinases that lack the very
   conformational diversity the method exploits.

   Specifically:
   - **RET:** All 38 KinCore chains are in active conformations. There is no DFGout RET
     structure in the PDB. The proposal lists vandetanib and cabozantinib as reference
     molecules, but these are multi-kinase inhibitors (vandetanib hits EGFR/RET/VEGFR;
     cabozantinib hits MET/RET/VEGFR2) that bind DFGin conformations. There is no
     state-selectivity story to test for RET.
   - **JAK2:** All 61 JH1 domain chains are DFGin. The conformational landscape is flat.
     Moreover, the JAK inhibitor selectivity challenge is JAK1/2/3/TYK2 cross-reactivity,
     which is driven by sequence variation at the gatekeeper and hinge regions, NOT by
     conformational state differences. JAK2 is the wrong kinase to test the state-aware
     hypothesis.

   The Round 2 synthesis recommends EGFR + ABL1 + BRAF + MET as the feasible set. The
   proposal must adopt this revised selection.

   - **Severity:** Critical
   - **Addressable?** Yes -- replace RET and JAK2 with MET (126 KinCore chains, multiple
     DFGout structures, all 4+ Ung states) and optionally ALK (limited but nonzero DFGout
     coverage). Dropping to 4 kinases (EGFR, ABL1, BRAF, MET) with ~18 held-out drugs
     still exceeds the N >= 15 threshold. Alternatively, retain ALK with the explicit
     caveat that its 2-state coverage limits the state-aware signal.

2. **Per-kinase reference molecules have significant medicinal chemistry problems.**

   The reference similarity component accounts for 35% of the unified score. The choice
   of reference molecules directly determines what chemical space the scoring function
   rewards. Several choices need scrutiny:

   - **ABL1 references (imatinib, dasatinib, nilotinib):** This is actually the BEST
     reference set because these three drugs span different conformational states AND
     distinct chemotypes. Imatinib (2-phenylaminopyrimidine) binds DFGout/inactive.
     Dasatinib (thiazole/aminopyrimidine) binds DFGin/active. Nilotinib
     (aminopyrimidine, imatinib derivative) binds DFGout. This is exactly the kind of
     structural and conformational diversity needed for a meaningful reference set.
     However, the proposal does not call attention to this critical feature. The fact
     that the ABL references span different states means the reference similarity
     component may ALREADY encode state information implicitly. This should be analyzed
     and discussed.

   - **EGFR references (erlotinib, gefitinib):** Both are 4-anilinoquinazolines. Both
     bind the active (DFGin/aCin) conformation. Both are first-generation reversible
     inhibitors. This is a severely limited reference set -- it rewards only one
     chemotype targeting only one conformational state. A candidate targeting DFGout
     would be penalized by reference similarity despite being exactly the kind of
     molecule the state-aware pipeline should generate. The proposal acknowledges
     "limited diversity" but does not recognize the severity: if 35% of the score
     penalizes DFGout-targeting molecules because they look nothing like erlotinib/
     gefitinib, the state-aware pipeline is scoring against itself.

   - **JAK2 references (ruxolitinib, tofacitinib):** The proposal notes these are both
     pyrrolopyrimidines. Worse, tofacitinib is technically a pan-JAK inhibitor (approved
     primarily for JAK3 in rheumatoid arthritis), not a JAK2-selective inhibitor. Using
     it as a reference molecule for JAK2-targeted design is scientifically questionable.
     This is another reason JAK2 is problematic.

   - **RET references (vandetanib, cabozantinib):** Both are multi-kinase inhibitors
     with only modest RET selectivity. Vandetanib is primarily an EGFR/VEGFR inhibitor.
     Cabozantinib is primarily a MET/VEGFR2 inhibitor. Using these as RET-specific
     references would reward molecules that look like EGFR or MET inhibitors, not
     RET-selective compounds.

   - **Severity:** Major
   - **Addressable?** Partially. ABL1 references are strong. BRAF references
     (vemurafenib, dabrafenib) are adequate -- distinct scaffolds, both target the
     relevant kinase selectively. ALK references (crizotinib, ceritinib) are acceptable.
     The EGFR reference set problem is fundamental: with only 4-anilinoquinazolines
     available pre-2015, the reference similarity component penalizes the chemical
     novelty that third-generation inhibitors represent. This is a known limitation that
     must be explicitly discussed. Consider running a sensitivity analysis with reference
     similarity weight reduced to 0.20 to assess its distorting effect.

3. **The reference similarity component biases AGAINST the state-aware hypothesis.**

   This is a subtle but critical medicinal chemistry point that the proposal misses
   entirely. The reference similarity score (35% of total) rewards molecules that
   resemble pre-cutoff approved drugs. Pre-cutoff drugs are predominantly DFGin/active-
   state binders (erlotinib, gefitinib, crizotinib, ruxolitinib, vemurafenib). The
   state-aware pipeline's distinctive value is generating molecules for DFGout and
   other inactive states -- precisely the molecules that will be dissimilar to the
   reference set.

   This creates a paradox: the scoring function penalizes the very molecules that the
   state-aware pipeline uniquely produces. If the state-aware pipeline still shows
   enrichment despite this scoring penalty, the true effect is likely LARGER than the
   measured BEDROC suggests. This asymmetry needs to be analyzed and discussed.

   Conversely, for ABL1 where the reference set includes imatinib (DFGout binder),
   the state-aware pipeline might benefit from reference similarity when generating
   DFGout molecules. Comparing the per-state contribution of reference similarity
   across kinases would be an illuminating secondary analysis.

   - **Severity:** Major
   - **Addressable?** Yes -- add a secondary analysis that decomposes the unified score
     by component and by conformational state. Show that reference similarity is
     systematically lower for DFGout-targeting candidates than for DFGin candidates.
     This actually STRENGTHENS the paper: it demonstrates that the state-aware advantage
     survives a scoring bias against it.

4. **ALK conformational state coverage is overstated.**

   The proposal lists ALK with "2+ (DFGin, DFGin-inactive)" conformational states and
   4 held-out drugs (alectinib, brigatinib, lorlatinib, ensartinib). However:
   - All approved ALK inhibitors are type I or type I-1/2 B inhibitors -- they all bind
     DFGin conformations with varying degrees of back-pocket extension.
   - ALK has only 2 DFGout chains in 68 total KinCore chains (structbio-R02).
   - The "DFGin-inactive" classification (DFGin with C-helix out) is a relatively
     subtle conformational difference compared to the DFGin vs DFGout distinction that
     drives the EGFR and ABL state-aware narratives.

   Including ALK is acceptable but the held-out drug count is misleading: all 4 drugs
   target essentially the same conformational state. ALK tests whether the pipeline
   generates good DFGin binders from diverse training data, not whether state-awareness
   matters. This is useful but distinct from the primary hypothesis.

   - **Severity:** Minor
   - **Addressable?** Yes -- document ALK's limited conformational diversity explicitly.
     Classify it as a "control kinase" that tests the pipeline's general performance
     without the state-aware signal. If state-aware enrichment is similar on ALK and
     EGFR, that would actually suggest diversity (not states) drives the effect.

5. **The clinical significance of held-out drug selection is not discussed.**

   The proposal treats held-out drugs as interchangeable data points. They are not. From
   a medicinal chemistry perspective:

   - **Asciminib (ABL, 2021):** This is an allosteric STAMP inhibitor that binds the
     myristate pocket, NOT the ATP site. It is structurally and mechanistically entirely
     different from ATP-competitive inhibitors. Including it as a held-out drug tests
     whether the VAE generates myristate-pocket binders -- which it almost certainly does
     not, since the training data is ATP-competitive compounds and the structural atlas
     is built around ATP-site conformations. Asciminib should either be excluded or its
     expected failure to enrich should be pre-registered as a negative control.

   - **Tovorafenib (BRAF, 2024):** A DFGout/aCin binder -- exactly the type of molecule
     the state-aware pipeline should enrich. This is potentially the strongest individual
     data point for the state-aware hypothesis. Its enrichment or failure to enrich for
     the DFGout-conditioned candidates is a critical per-compound analysis.

   - **Lorlatinib (ALK, 2018):** A macrocyclic inhibitor with a distinctive ring-closed
     structure. It will have low Tanimoto similarity to most VAE-generated molecules
     simply because of its macrocyclic topology. Reference similarity will penalize it.

   - **Severity:** Major
   - **Addressable?** Yes -- add per-drug enrichment analysis (which drug is ranked
     highest by which pipeline and which state). Pre-register expected outcomes: DFGout
     drugs (imatinib analogs for ABL, tovorafenib for BRAF) should be enriched by
     DFGout-conditioned generation. DFGin drugs should be enriched by DFGin generation.
     Allosteric drugs (asciminib) should NOT be enriched by any ATP-site-based
     generation. This per-drug analysis is far more informative than aggregate BEDROC.

6. **No discussion of kinase-specific SAR considerations affecting scoring.**

   The unified scoring function uses the same weights and components across all kinases,
   but the SAR landscape varies dramatically:

   - **EGFR:** Hinge-binding 4-anilinoquinazoline is the dominant pharmacophore. SAR is
     well-characterized around C6/C7 substitution, aniline substitution, and covalent
     warhead attachment.
   - **ABL1:** Multiple distinct pharmacophores (type I, type II, allosteric). SAR at
     the DFG-binding region is the critical differentiator between type I and type II.
   - **BRAF:** The aC-helix-out pocket is a distinctive feature exploited by
     vemurafenib's sulfonamide moiety. SAR around this pocket interaction is
     BRAF-specific.

   A universal scoring function may miss these kinase-specific SAR features. The
   reference similarity component partially captures this (through kinase-specific
   references), but the drug-likeness, state specificity, and docking components are
   generic. Consider whether a per-kinase normalization of score components would be
   more appropriate.

   - **Severity:** Minor
   - **Addressable?** Partially -- per-kinase score normalization (z-score within each
     kinase) would address different baseline distributions. This should be a
     pre-specified secondary analysis.

---

## Feasibility Assessment

### Technical Feasibility

Strong. The proposal leverages existing StateBind infrastructure (VAE, MPNN, scoring,
retrospective evaluation) and extends it to new kinases. The main technical challenges
are: (a) preparing conformational state atlases for 3-4 new kinases, (b) retraining
MPNN on per-kinase ChEMBL data, and (c) GNINA receptor preparation and validation.
All are well within the team's demonstrated capability. The compute estimate of ~42
GPU-days (dominated by GNINA docking) is reasonable for H200 nodes on Bouchet.

The RET data scarcity concern (only ~800 pre-2015 compounds) becomes moot if RET is
replaced with MET per the revised kinase selection. MET has 126 KinCore chains and
substantially more ChEMBL bioactivity data.

### Scientific Feasibility

Moderate to strong, with caveats. The fundamental question -- does state-aware
generation improve retrospective enrichment across kinases? -- is scientifically
well-posed and testable. The ablation suite provides proper controls. However:

- The reference similarity bias against state-aware molecules (Weakness 3) means the
  measured effect may underestimate the true benefit of state-conditioning.
- If most held-out drugs for new kinases are DFGin binders (as for ALK), the state-aware
  signal may be diluted because the critical test is enrichment of DFGout drugs.
- The power analysis assumes independent per-kinase effects. In reality, kinases with
  richer conformational landscapes (ABL, BRAF) are more likely to show state-aware
  benefit. Per-kinase heterogeneity may be large.

### Timeline Feasibility

6 weeks is tight but achievable, assuming: (a) structural atlas preparation is
parallelized with MPNN retraining (Weeks 1-2), (b) the EGFR ablation gate (Week 2-3)
does not require redesign, and (c) GNINA docking is limited to top-50 candidates per
kinase rather than all candidates. The limiting factor is likely receptor preparation
and validation for new kinases -- this requires careful medicinal chemistry input to
ensure binding site definitions are correct.

---

## Suggested Modifications

1. **Replace RET and JAK2 with MET (and optionally retain ALK as a limited-signal
   control).** This is the single most important modification. The revised target set
   should be EGFR + ABL1 + BRAF + MET, with ALK as an optional 5th. MET has excellent
   conformational coverage (all 4+ Ung states), 126 PDB chains, and capmatinib (2020)
   + tepotinib (2021) as held-out drugs for pre-2015 cutoff. The reference set
   (crizotinib 2011, which cross-targets MET) needs careful handling since crizotinib
   is primarily an ALK drug but has well-characterized MET binding.

2. **Add a per-drug enrichment analysis as a pre-registered secondary endpoint.** For
   each held-out drug, report its rank in each pipeline and each state-conditioned
   generation batch. Pre-register expected outcomes: DFGout drugs should rank higher in
   DFGout-conditioned generation than in DFGin-conditioned generation. This is a more
   granular and mechanistically informative test than aggregate BEDROC.

3. **Pre-register the asciminib exclusion (or its expected non-enrichment).** Asciminib
   binds the myristate allosteric pocket, not the ATP site. The entire StateBind
   pipeline operates on ATP-site conformations and ATP-competitive training data.
   Either exclude asciminib from the ABL held-out set or pre-register that it serves
   as a negative control (expected to NOT be enriched).

4. **Add a reference similarity decomposition analysis.** Show how the 35% reference
   similarity component distributes across conformational states. Demonstrate that
   DFGout-targeting candidates receive systematically lower reference similarity scores
   when references are DFGin-binders (EGFR, ALK) but not when references include
   DFGout-binders (ABL1 with imatinib). This analysis directly connects scoring
   mechanics to the state-aware hypothesis.

5. **Run a sensitivity analysis at reference similarity weight = 0.20.** If the
   state-aware enrichment INCREASES when reference similarity weight is reduced, that
   provides evidence that the current 35% weight actively suppresses the state-aware
   signal. This is a powerful secondary finding.

6. **Classify kinases by conformational diversity and pre-register differential
   predictions.** Instead of treating all kinases as equivalent replicates, stratify:
   - "High conformational diversity" kinases (EGFR, ABL1, BRAF): expect strong
     state-aware signal
   - "Moderate conformational diversity" (MET): expect moderate signal
   - "Low conformational diversity" (ALK): expect weak or no state-aware signal
   This pre-registered stratification transforms heterogeneous results from a weakness
   into a mechanistic finding.

---

## Alternative Approaches

The proposal assumes a uniform pipeline across kinases. An alternative "best foot
forward" approach would first optimize the pipeline on EGFR (with ablations), then
apply the validated protocol to new kinases. This is essentially what the proposal
does with its Step 4 (EGFR ablation gate), which is the right sequencing.

However, a stronger alternative for the per-kinase analysis would be to use a
mixed-effects model rather than a paired t-test. A random-effects meta-analytic
framework, treating each kinase as a "study" with its own BEDROC effect estimate and
variance, would properly account for the expected between-kinase heterogeneity (some
kinases have 4 states, some have 2; some have 5 held-out drugs, some have 1). This
is more appropriate than assuming a common effect size across kinases.

DerSimonian and Laird random-effects meta-analysis (DerSimonian & Laird, 1986, Controlled
Clinical Trials 7:177) would provide a pooled effect estimate while quantifying
between-kinase heterogeneity (I-squared statistic). High heterogeneity (I-squared > 75%)
would indicate that state-awareness benefits depend on kinase-specific features -- which
is itself a publication-worthy finding.

---

## Impact on Publication Narrative

This proposal provides the essential statistical backbone of the publication. Without it,
the 10x enrichment on EGFR alone is anecdotal. With it, the paper becomes a rigorous
multi-kinase validation study.

From a medicinal chemistry perspective, the key publication impact depends on
WHICH kinases show the state-aware advantage:

- If ABL1 shows strong state-aware enrichment (especially for DFGout drugs like imatinib
  analogs), this validates the conformational targeting hypothesis on the gold-standard
  kinase for conformational studies. This is the strongest single data point.

- If BRAF shows state-aware enrichment for DFGout binders (tovorafenib analogs) vs
  DFGin binders (vemurafenib analogs), this demonstrates practical value: the pipeline
  identifies next-generation inhibitors that target drug-resistant conformations.

- If ALK shows no state-aware benefit (expected, given limited conformational diversity),
  this is actually informative: it suggests state-awareness matters only when the target
  has exploitable conformational diversity.

The per-drug analysis I propose (Suggested Modification 2) would make the narrative much
more concrete: "The state-aware pipeline ranked the DFGout-targeting drug tovorafenib
within the top 5% of BRAF candidates, while the static pipeline ranked it in the bottom
50%." That is a story a medicinal chemist can understand and evaluate.

---

## References

1. DerSimonian R, Laird N. (1986). Meta-analysis in clinical trials. Controlled
   Clinical Trials 7(3):177-188. DOI: 10.1016/0197-2456(86)90046-2.

2. Wylie AA, Schoepfer J, Jahnke W, et al. (2017). The allosteric inhibitor ABL001 is
   a potent bcr-abl1 inhibitor with ability to overcome resistance mutations. Nature
   543:733-737. DOI: 10.1038/nature21702.

3. Zhao Z, Wu H, Wang L, et al. (2014). Exploration of type II binding mode: a
   privileged approach for kinase inhibitor focused drug discovery? ACS Chem Biol
   9(6):1230-1241. DOI: 10.1021/cb500129t.

4. Roskoski R. (2025). Properties of FDA-approved small molecule protein kinase
   inhibitors: A 2025 update. Pharmacological Research 204:107083.

5. Park JH, Liu Y, Lemmon MA, Radhakrishnan R. (2012). Erlotinib binds both inactive
   and active conformations of the EGFR tyrosine kinase domain. Biochem J
   448(3):417-423. DOI: 10.1042/BJ20121513.

6. Modi V, Dunbrack RL Jr. (2019). Defining a new nomenclature for the structures of
   active and inactive kinases. PNAS 116(14):6818-6827.

7. Fang L, et al. (2022). KinCore: a web resource for structural classification of
   protein kinases and their inhibitors. Nucleic Acids Research 50(D1):D654-D664.

8. Nagar B, et al. (2002). Crystal structures of the kinase domain of c-Abl in complex
   with the small molecule inhibitors PD173955 and imatinib (STI-571). Cancer Research
   62(15):4236-4243.

9. Shah NP, Nicoll JM, Nagar B, et al. (2002). Multiple BCR-ABL kinase domain
   mutations confer polyclonal resistance to the tyrosine kinase inhibitor imatinib
   (STI571) in chronic phase and blast crisis chronic myeloid leukemia. Cancer Cell
   2(2):117-125.

10. Soverini S, Mancini M, Bavaro L, et al. (2018). Resistance to dasatinib in
    Philadelphia-positive leukemia patients and the presence or the selection of
    mutations at residues 299 and 315 of the BCR-ABL kinase domain. Haematologica
    103(12):e587-e590.
