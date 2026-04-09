---
agent: Senior ML Researcher
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: synthbio-P01
---

# Critique: End-to-End Drug-ability Assessment Pipeline

## Reviewing Agent
Senior ML Researcher -- expertise in publication strategy, benchmark methodology,
reviewer expectations at JCIM and Nature Computational Science, and how additional
scoring components interact with evaluation rigor and statistical claims.

## Proposal Summary
synthbio-P01 proposes a 4-tier post-scoring drug-ability assessment: (1) RAscore fast
screening for synthesis feasibility, (2) AiZynthFinder full retrosynthetic analysis on
top 50 candidates, (3) ADMETlab 3.0 comprehensive profiling against 119 endpoints with
kinase-calibrated thresholds, and (4) PKSmart PK projection for top 20 candidates.
Results produce a "survival funnel" figure and optionally integrate RAscore as a 5th
scoring component. Estimated cost: less than 2 hours of compute over 3-4 weeks.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The survival funnel is a genuinely differentiating publication figure
that no other conformational-state-aware pipeline has produced, but the proposal
overreaches by trying to simultaneously be a standalone analysis AND a scoring function
modification, and the ADMETlab 3.0 API dependency is a time bomb for reproducibility.

---

## Strengths

1. **The survival funnel is the proposal's killer feature.** No published
   conformational-state-aware molecular design paper includes an end-to-end attrition
   analysis. The figure showing 461 candidates entering and N survivors exiting through
   synthesis, ADMET, and PK filters is immediately compelling to any reviewer. At JCIM,
   where reviewers are practicing computational chemists, this is the figure they wish
   every AI drug design paper included. The framing is correct: most academic papers
   stop at scoring, and the field has increasingly recognized this as a credibility gap.
   The citations to Chemistry42, ADMETrix, PMMG, and REINVENT 4 as comparators are
   well-chosen and demonstrate awareness of the competitive landscape.

2. **Kinase-calibrated ADMET thresholds are a reusable contribution.** The table of
   approved EGFR-TKI ADMET profiles (erlotinib, gefitinib, afatinib, osimertinib,
   dacomitinib) with specific hERG IC50 values, oral bioavailability, and CYP
   metabolism data is well-researched. The insight that osimertinib has hERG IC50 as
   low as 0.57 uM -- far below the standard 10 uM threshold -- and is still the
   standard-of-care is a strong argument for kinase-calibrated thresholds. This
   reusable table would be cited by other groups working on kinase inhibitor design.
   It is the kind of practical contribution that JCIM values highly.

3. **The "3-22% synthesis feasibility for 3D methods" comparison is strategically
   valuable.** If StateBind's 1D SELFIES VAE achieves significantly higher synthesis
   feasibility than 3D structure-based methods, this is a novel and counter-narrative
   finding. The dominant narrative in the field is that 3D methods are superior. Showing
   that they fail the synthesis reality check while a simpler 1D method succeeds would
   attract citations and discussion. The proposal correctly identifies this as a
   potential publication differentiator.

4. **Compute cost is negligible.** At less than 2 hours total, this is the cheapest
   proposal in the entire set. Even if results are mixed, the opportunity cost of NOT
   running this analysis is hard to justify. The risk-reward ratio is favorable.

5. **Honest risk assessment for negative results.** The proposal explicitly
   acknowledges that state-aware candidates might have LOWER synthesis feasibility due
   to greater chemical diversity and frames this as an honest tradeoff rather than a
   failure. This is the right framing. A paper that says "state-aware design explores
   more chemical space at the cost of some synthesis feasibility, but the enrichment
   for known drugs holds" is more credible than one that hides the tradeoff.

## Weaknesses

1. **RAscore as a 5th scoring component threatens the primary endpoint.**
   - **Severity:** Critical
   - **Addressable?** Yes -- by keeping RAscore as standalone analysis only

   The proposal recommends "Option A: RAscore as 5th Component" with weight
   redistribution across all 5 components. This is the single most dangerous suggestion
   in the proposal. Here is why:

   StateBind's primary endpoint is the retrospective enrichment comparison (EF@10)
   between state-aware and static pipelines. This comparison is ONLY valid under the
   SAME scoring function applied to both pipelines. Every time the scoring function
   changes, the retrospective validation must be re-run and the enrichment numbers
   change. The Round 2 synthesis explicitly identified this tension: "lock original
   scoring for primary endpoint, report revised scoring as secondary analysis."

   Adding RAscore as a 5th component changes the scoring function. The proposed weight
   redistribution reduces state specificity from 0.15 to 0.10 -- a 33% reduction in
   the component that most directly captures the state-aware advantage. If the
   enrichment drops after this change, the narrative collapses. If the enrichment
   increases, reviewers will suspect the weights were tuned to favor the state-aware
   pipeline.

   Furthermore, medchem-P01 already proposes adding ADMET and selectivity as scoring
   components (5-6 components). If synthbio-P01 adds RAscore on top of that, we are
   at 7 components. Every additional component multiplies the weight sensitivity
   surface and makes it harder to demonstrate robustness. The Dirichlet weight
   sensitivity analysis across 7 components with 100 random configurations is a
   7-dimensional space where "enrichment is maintained" becomes increasingly unlikely
   to hold for all configurations.

   **Recommendation:** RAscore should be a standalone analysis metric, reported
   alongside but NOT inside the scoring function. Option C (hard filter before
   scoring) is acceptable as a secondary analysis. Option A should be rejected for
   the primary paper.

2. **ADMETlab 3.0 API dependency is a reproducibility liability.**
   - **Severity:** Major
   - **Addressable?** Yes, with mitigation protocol

   The proposal relies on ADMETlab 3.0's free public API
   (https://admetlab3.scbdd.com) for 119 ADMET endpoint predictions. This introduces
   three risks that a Senior ML Researcher must flag:

   **Risk 2a: Version drift.** ADMETlab 3.0 (Fu et al., 2024) is a web service. The
   models behind the API can be updated silently. If a reviewer asks "we ran your
   molecules through ADMETlab and got different numbers," there is no defense. Unlike
   a pip-installed package with version pinning, an API has no reproducibility
   guarantee. The proposal mentions caching responses, which helps, but does not
   solve the fundamental problem: the paper's ADMET results are tied to a specific
   API snapshot that cannot be reproduced.

   **Risk 2b: API availability during review.** Peer review at JCIM or Nature
   Computational Science takes 3-6 months. If ADMETlab's API goes down, changes rate
   limits, or requires registration during this period, reviewers cannot validate
   results. The proposal's fallback (Deep-PK, admetSAR 3.0) is acknowledged but
   produces DIFFERENT predictions on DIFFERENT endpoints, making it an apples-to-oranges
   comparison, not a true fallback.

   **Risk 2c: Reviewer skepticism about external predictions.** A reviewer will ask:
   "You have your own ADMET model (GIN backbone, 6 endpoints). Why did you use an
   external API instead?" The honest answer -- "our model is below SOTA" -- raises
   the question of why the existing model was not improved rather than bypassed. This
   undermines confidence in the internal ML stack.

   **Mitigation:** Pin the API version in the methods section (ADMETlab 3.0 as of
   April 2026). Cache ALL raw API responses as a supplementary data archive. Run the
   internal ADMET model on the same candidates and report both sets of predictions
   as a concordance analysis. If ADMETlab and the internal model agree on broad
   categorizations (ADMET-clean vs flagged), that strengthens both. If they disagree,
   investigate why.

3. **The "3-22% synthesis feasibility" claim needs source scrutiny.**
   - **Severity:** Major
   - **Addressable?** Yes, with careful framing

   The proposal builds a key argument on Gao et al. (arXiv:2411.08306): "3D
   structure-based generative models produce molecules with only 3-22% true synthesis
   feasibility." This is cited as an arXiv preprint, not a peer-reviewed publication.
   The 3-22% range spans nearly an order of magnitude, and the best performer
   (Pocket2Mol at 22.1%) is not dramatically low.

   More importantly, the comparison is not apples-to-apples. Gao et al. evaluate
   synthesis feasibility via "round-trip verification" (retrosynthesis + forward
   synthesis prediction). StateBind's RAscore evaluation uses a different methodology
   (a classifier trained on AiZynthFinder results). Unless StateBind runs the SAME
   round-trip verification protocol on its own candidates, the comparison is
   methodologically invalid.

   Additionally, the 1D vs 3D framing is misleading. StateBind's VAE generates
   SELFIES strings that are then docked. The molecules themselves are not "1D" in
   any meaningful chemical sense -- they are 3D molecules represented as strings.
   The synthesis feasibility advantage (if it exists) would come from the VAE's
   training data distribution (ChEMBL drug-like molecules), not from the
   representation. A fairer comparison would be: "SELFIES VAE trained on ChEMBL vs
   3D methods trained on CrossDocked2020."

   **Recommendation:** If this comparison is pursued, run AiZynthFinder (not just
   RAscore) on StateBind candidates AND on a matched set of DiffSBDD/TargetDiff/
   Pocket2Mol-generated candidates for the same EGFR target. This head-to-head
   comparison using the same evaluation tool is the only way to make the claim
   credibly.

4. **The survival funnel comparison is asymmetric (461 vs 30).**
   - **Severity:** Major
   - **Addressable?** Yes, with normalization

   The state-aware pipeline produced 461 candidates; the static pipeline produced 30.
   The survival funnel comparing raw counts is misleading. If 50 state-aware
   candidates survive (10.8%) and 5 static candidates survive (16.7%), the static
   pipeline actually has a higher survival rate despite fewer absolute survivors. The
   proposal acknowledges this ("the state-aware-to-static ratio of end-to-end
   survivors relative to the input ratio"), but the figure design must foreground
   survival RATES, not absolute counts.

   A reviewer will also ask: why does the static pipeline produce only 30 candidates?
   Is this a design choice or a limitation? If the static pipeline were allowed to
   generate 461 candidates, would its survival rate hold? The 15.4:1 ratio in input
   sizes makes any downstream comparison confounded by sample size.

5. **PKSmart predictions are too uncertain to be informative.**
   - **Severity:** Minor
   - **Addressable?** Yes, by downscoping

   The proposal cites PKSmart external validation: VDss R^2=0.39, CL R^2=0.46. These
   are weak correlations. An R^2 of 0.39 means the model explains 39% of the variance
   in volume of distribution -- less than half. GMFE of 2-3x means predictions are
   routinely off by 2-3 fold. For a screening-stage analysis where the goal is to
   rank candidates, these correlations may suffice for gross categorization (acceptable
   vs unacceptable PK), but the proposal presents them alongside ADMET profiles as if
   they have comparable reliability.

   The risk: a reviewer who notices VDss R^2=0.39 in the methods section will
   question the rigor of the entire PK analysis. The honest approach is to present
   PKSmart results as "directional PK estimates" in supplementary material, not as a
   main-text tier of the assessment pipeline. The proposal partially acknowledges this
   ("present PK projections as directional only"), but then proceeds to set specific
   thresholds (oral F > 30%, half-life > 8 hours) that imply a precision the model
   cannot deliver.

---

## Feasibility Assessment

### Technical Feasibility
High. All tools (RAscore, AiZynthFinder, PKSmart) are pip-installable and CPU-only.
ADMETlab 3.0 requires internet access from Bouchet login nodes, which is the main
infrastructure uncertainty. The proposal correctly identifies the RAscore Python
compatibility concern (TensorFlow version conflicts with Python 3.10-3.12) and the
AiZynthFinder stock database selection as practical issues. These are solvable with
separate conda environments.

### Scientific Feasibility
The survival funnel will produce clear, interpretable results regardless of whether
they favor state-aware or static design. The ADMET profiling and retrosynthetic
analysis are well-established methods. The scientific risk is not whether the analysis
can be done, but whether the results support the narrative -- and the proposal handles
this honestly.

### Timeline Feasibility
3-4 weeks is realistic. The compute is negligible; the time is in scripting, API
integration, and figure generation. The AiZynthFinder stock database download and
setup may take longer than expected (the Enamine building block database can be large),
but this is a one-time cost.

---

## Suggested Modifications

1. **Decouple the survival funnel from scoring function modification.** The survival
   funnel is a standalone analysis that adds publication value without touching the
   scoring function. RAscore integration into scoring is a separate decision with
   different risks. Present them as independent contributions. The primary paper should
   report the survival funnel with the ORIGINAL 4-component scoring function. A
   supplementary analysis can show what happens with RAscore as a 5th component. This
   preserves the integrity of the retrospective enrichment comparison.

2. **Run ALL baselines through the survival funnel.** The proposal currently processes
   only StateBind's state-aware and static candidates. If mlres-P01 (external
   baselines) proceeds, REINVENT, DiffSBDD, and fingerprint similarity baselines
   should also go through the survival funnel. A figure showing survival rates for
   5-6 methods side-by-side is far more impactful than a 2-method comparison.
   This is where synthbio-P01 and mlres-P01 create maximum synergy: the baseline
   comparison framework produces candidates, and the survival funnel filters them.
   The combined figure -- "external baselines x end-to-end drug-ability" -- would be
   the paper's strongest contribution to the field.

3. **Replace ADMETlab 3.0 API with a locally reproducible alternative for core
   results.** Use ADMETlab 3.0 for the comprehensive 119-endpoint profile (reported
   in supplementary material), but use the internal StateBind ADMET model (6
   endpoints, GIN backbone) for the primary survival funnel filters. This keeps the
   core results reproducible without external dependencies. Then present a concordance
   analysis: "Our internal model and ADMETlab 3.0 agree on X% of categorizations."
   If concordance is high, this validates both models. If low, this is a finding
   about ADMET model uncertainty that is itself publishable.

   Alternatively, if the internal model is deemed insufficient, install a locally
   runnable open-source ADMET tool -- TDC's ADMET benchmark provides several
   models with downloadable checkpoints. The key principle: core publication results
   must not depend on an external API that cannot be version-pinned.

4. **Normalize the survival funnel for sample size asymmetry.** Report survival rates
   (percentages) as the primary metric, not absolute counts. Generate the same
   number of static candidates (resample or regenerate to match 461) so the funnel
   comparison is not confounded by input size. If resampling is not feasible, use
   bootstrap resampling on the static set to generate confidence intervals on the
   static survival rate.

5. **Move PKSmart to supplementary material.** Present Tiers 0-2 (RAscore,
   AiZynthFinder, ADMETlab) as the main-text drug-ability assessment. PKSmart PK
   projections go in supplementary material with explicit uncertainty disclaimers.
   This reduces the attack surface for reviewers questioning the precision of PK
   predictions while still demonstrating awareness of the PK dimension.

6. **For the 3D synthesis comparison, use AiZynthFinder on ALL methods.** If comparing
   StateBind's synthesis feasibility against 3D methods, run AiZynthFinder (not
   RAscore) on molecules generated by all methods on the same EGFR target. RAscore
   is a proxy; AiZynthFinder is the ground truth. Using the same evaluation tool
   across all methods eliminates the methodological confound. Generate or obtain
   DiffSBDD/TargetDiff/Pocket2Mol molecules for EGFR from publicly available
   pre-trained models and run them through the identical pipeline.

---

## Alternative Approaches

1. **Synthesis-on-demand validation.** Instead of computational retrosynthesis only,
   submit the top 5 candidates to Enamine's REAL Space (28+ billion enumerated
   compounds) or Mcule's Quote system for actual synthesis quotation. A quote with
   a price and timeline is stronger evidence of synthesizability than any
   computational prediction. This is becoming standard in high-impact AI drug design
   publications (e.g., Insilico Medicine's Chemistry42 papers include synthesis
   quotes). Cost: free for quotation; synthesis costs would be borne only if the
   project proceeds to experimental validation.

2. **FSscore as an alternative to RAscore.** The FSscore (Neeser et al., 2024,
   cited in the proposal's references) is a personalized synthesis feasibility
   classifier that can be trained on a specific lab's synthesis capabilities. While
   RAscore is trained on generic ChEMBL feasibility, FSscore could be calibrated to
   Enamine building block availability, making it more relevant to actual synthesis
   planning. However, FSscore requires a training step that RAscore does not, adding
   complexity.

3. **ADMET fingerprinting without thresholds.** Instead of applying kinase-calibrated
   thresholds (which are judgment calls that reviewers will debate), compute
   ADMET-space Tanimoto similarity to approved EGFR-TKIs. Candidates whose ADMET
   profiles are most similar to approved drugs are ranked highest. This avoids the
   threshold debate entirely and frames ADMET assessment as "how drug-like are these
   candidates relative to approved drugs?" rather than "do they pass arbitrary
   cutoffs?"

---

## Impact on Publication Narrative

### Does the survival funnel differentiate from academic exercises?

Yes, but with important venue-dependent nuances:

**For JCIM:** The survival funnel is a strong differentiator. JCIM reviewers are
practicing computational chemists and medicinal chemists who routinely complain that
AI drug design papers are disconnected from real drug discovery. A paper that shows
the full attrition cascade from scoring through synthesis through ADMET through PK
directly addresses this complaint. The kinase-calibrated ADMET thresholds are
especially valuable at JCIM because they represent practical domain knowledge, not
just computational metrics. **Verdict: High impact at JCIM.**

**For Nature Computational Science:** The survival funnel adds practical credibility
to the narrative but is not the differentiator. Nature Computational Science cares
about the scientific insight (conformational states matter for design) and the
methodological contribution (a framework for state-aware design). The survival funnel
is supporting evidence, not the headline. **Verdict: Moderate impact. Good for
supplementary section or as one of several contributions.**

**For NeurIPS/ICML:** The survival funnel is irrelevant. ML venue reviewers do not
evaluate synthesis feasibility or ADMET profiles. They care about the ML methodology,
the benchmark, and the ablations. **Verdict: No impact.**

### Integration with baseline comparison

This is the critical strategic question. If the survival funnel processes only
StateBind's own candidates, it is a nice supplementary analysis. If it processes ALL
baselines from mlres-P01 (REINVENT, DiffSBDD, fingerprint search, unconditioned VAE),
it becomes a central contribution: the first head-to-head comparison of generative
methods on end-to-end drug-ability, not just generation quality. The answer to "should
ALL baselines go through the end-to-end assessment?" is unequivocally YES.

### Priority ranking

1. **mlres-P01 (External baselines):** P0. Non-negotiable.
2. **datasci-P01 (Multi-kinase expansion):** P0. Non-negotiable.
3. **medchem-P01 (Scoring revision):** P1. Addresses the mean-score inversion.
4. **compchem-P01, Tier 1 (GIST):** P1. Cheap, high narrative value.
5. **synthbio-P01 (Survival funnel ONLY, no scoring change):** P2 standalone, but
   P1 if combined with mlres-P01 baselines.
6. **compchem-P01, Tier 2 (FEP):** P2. Venue-dependent.

The survival funnel's priority increases from P2 to P1 if it is integrated with the
external baseline comparison. A figure showing "REINVENT vs StateBind-static vs
StateBind-state-aware vs DiffSBDD survival rates" is worth more than any individual
analysis in this proposal.

---

## References

1. Fu L, et al. ADMETlab 3.0: an updated comprehensive online ADMET prediction platform
   enhanced with broader coverage, improved performance, API functionality and decision
   support. Nucleic Acids Research. 2024;52(W1):W422-W431. doi:10.1093/nar/gkae236

2. Thakkar A, et al. Retrosynthetic accessibility score (RAscore) -- rapid machine
   learned synthesizability classification from AI driven retrosynthetic planning.
   Chemical Science. 2021;12:3339-3349. doi:10.1039/D0SC05401A

3. Gao S, et al. Evaluating Molecule Synthesizability via Retrosynthetic Planning and
   Reaction Prediction. arXiv:2411.08306v2. 2024.

4. Seal S, et al. PKSmart: an open-source computational model to predict intravenous
   pharmacokinetics of small molecules. Journal of Cheminformatics. 2025;17.
   doi:10.1186/s13321-025-01066-5

5. Neeser R, et al. FSscore: A Personalized Machine Learning-Based Synthetic Feasibility
   Score. Chemistry-Methods. 2024;4(6):e202400024. doi:10.1002/cmtd.202400024

6. Gao W, et al. Generative AI for navigating synthesizable chemical space. PNAS.
   2025;122(41):e2415665122. doi:10.1073/pnas.2415665122

7. Loeffler H, et al. REINVENT 4: Modern AI-driven generative molecule design. Journal
   of Cheminformatics. 2024;16:20. doi:10.1186/s13321-024-00812-5

8. Huang K, et al. Artificial intelligence foundation for therapeutic science. Nature
   Chemical Biology. 2022;18:1033-1036. doi:10.1038/s41589-022-01131-2

9. Gao W, et al. The Synthesizability of Molecules Proposed by Generative Models. J Chem
   Inf Model. 2020;60(12):5714-5723. doi:10.1021/acs.jcim.0c00174
