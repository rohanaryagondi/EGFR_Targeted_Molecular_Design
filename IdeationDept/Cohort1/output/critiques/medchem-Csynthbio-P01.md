---
agent: Senior Medicinal Chemist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: synthbio-P01
---

# Critique: End-to-End Drug-ability Assessment Pipeline

## Reviewing Agent

Dr. Senior Medicinal Chemist -- 20+ years in kinase drug discovery, lead optimization
through clinical candidate selection. Reviewing this proposal through the lens of
clinical translatability, ADMET threshold validity, synthesis feasibility realism, and
whether the "survival funnel" produces molecules a medicinal chemist would actually
pursue.

## Proposal Summary

synthbio-P01 proposes a 4-tier drug-ability assessment pipeline processing all
StateBind candidates through: (1) RAscore fast screening for synthesis feasibility,
(2) AiZynthFinder full retrosynthetic analysis of top candidates, (3) ADMETlab 3.0
comprehensive profiling with kinase-calibrated thresholds, and (4) PKSmart PK
projection. The output is a "survival funnel" figure and fully profiled drug-ability
cards for the top 10 candidates.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The right idea executed with several threshold choices that would
not survive scrutiny from an experienced medicinal chemistry team or a regulatory
toxicologist, and with a PK projection tier whose accuracy is insufficient to add
value beyond what already exists.

---

## Strengths

1. **This proposal addresses the most damaging reviewer critique.** The number one
   attack any drug discovery reviewer will make against an AI molecular design paper is:
   "These are not drugs. They are scored molecular graphs." By adding retrosynthesis,
   ADMET profiling, and PK projection, the paper moves from computational exercise to
   translational demonstration. This is the single most impactful addition to the
   publication narrative from a medicinal chemistry perspective.

2. **The survival funnel concept is a genuine contribution to the field.** Most AI drug
   design papers report generation statistics (validity rate, uniqueness, novelty) and
   scoring distributions, then stop. The funnel that tracks candidates through
   progressively more stringent real-world filters -- synthesis feasibility, ADMET
   acceptability, PK viability -- is a visualization that the field needs. If this
   becomes a standard figure in future AI drug design papers, that is a lasting
   contribution.

3. **The tiered architecture is well-designed.** The cascade from fast screening
   (RAscore: milliseconds per molecule) to full retrosynthetic analysis (AiZynthFinder:
   40-90 seconds per molecule) mirrors how a real medicinal chemistry team triages
   compounds. You do not run retrosynthetic planning on 461 molecules -- you filter
   first, then analyze deeply. The proposal correctly applies expensive tools only to
   the top candidates.

4. **Kinase-calibrated ADMET thresholds are necessary and well-motivated.** The
   proposal correctly identifies that StateBind's ADMET model rejects ALL kinase
   inhibitors on hERG because it uses absolute thresholds from general drug design
   that do not apply to kinase inhibitors as a class. Calibrating thresholds against
   approved EGFR-TKI profiles is the right conceptual approach. The compiled table of
   approved TKI properties (MW, oral F, T1/2, protein binding, hERG IC50, CYP
   metabolism) is a useful reference that could itself be a supplementary table in the
   publication.

5. **The state-dependent ADMET analysis is a mechanistically insightful secondary
   finding.** The proposal astutely notes that DFGout-targeting candidates tend to be
   larger and more lipophilic (the DFGout back pocket is deeper and more hydrophobic
   than the DFGin ATP site). This means DFGout candidates may systematically differ in
   ADMET profiles -- higher logP, higher hERG liability, lower aqueous solubility, but
   potentially longer half-life due to higher protein binding. If this pattern emerges,
   it connects conformational state targeting to practical drug properties in a way that
   no other paper has reported. This is the strongest novel finding the proposal could
   produce.

6. **Low compute cost is a major practical advantage.** Less than 2 hours of wall time
   (excluding scripting) for the entire pipeline. This means it can be iterated rapidly
   and does not compete for GPU allocation with the multi-kinase validation.

## Weaknesses

1. **The hERG threshold of > 0.5 uM is dangerously permissive and misuses the
   osimertinib precedent.**

   The proposal cites osimertinib's hERG IC50 of 0.57 uM as justification for a
   kinase-calibrated threshold of > 0.5 uM. This is a significant misreading of the
   clinical reality:

   - Osimertinib received FDA approval DESPITE its hERG liability, not because of it.
     The FDA required a REMS (Risk Evaluation and Mitigation Strategy) and a QTc
     prolongation warning in the label. Mean QTc prolongation is 14 ms at steady state,
     which exceeds the ICH E14 threshold of concern (10 ms). This was accepted only
     because osimertinib's efficacy benefit in T790M-mutant NSCLC is large (PFS 18.9
     months vs 10.2 months for chemotherapy, FLAURA trial).

   - A de novo computational candidate does not have this efficacy justification. A
     reviewer will ask: "Why would I tolerate a 0.5 uM hERG IC50 for an unvalidated
     compound when I can optimize it away?" The answer in real drug discovery is that
     you would NOT accept 0.5 uM hERG for a compound that has not demonstrated
     exceptional efficacy in vivo.

   - The more relevant metric is the hERG IC50:Cmax ratio (Lehmann et al., 2018). An
     IC50:Cmax ratio > 30 is generally considered low risk. Osimertinib achieves this
     because its clinical Cmax is low (~0.065 uM at 80 mg QD) relative to its hERG IC50
     (ratio ~8.7 -- which is actually in the moderate-risk zone). The FDA accepted this
     because the unbound Cmax is much lower (fraction unbound ~5%, so unbound Cmax ~3.2
     nM, giving a ratio of ~178, which is safer).

   - The proposal's threshold table lists hERG > 0.5 uM as the kinase-calibrated
     threshold. This is below the lowest hERG IC50 of ANY approved EGFR-TKI. Gefitinib
     has a hERG IC50 of 1.91 uM. A more defensible threshold would be hERG IC50 > 1.0
     uM, which still accommodates osimertinib (range 0.57-2.21 uM) and gefitinib (1.91
     uM) while filtering out compounds with extreme hERG potency.

   - **Severity:** Major
   - **Addressable?** Yes -- raise the threshold to > 1.0 uM and report results under
     both thresholds (1.0 uM and the standard 10 uM). Include a discussion of the
     hERG IC50:Cmax ratio framework and why absolute thresholds are an oversimplification.
     Present this as a limitation, not a solution.

2. **RAscore does not capture what makes synthesis actually hard.**

   As a medicinal chemist who has supervised hundreds of compound syntheses, I can
   identify several categories of "synthesis difficulty" that RAscore systematically
   misses:

   - **Stereochemistry:** RAscore predicts binary feasibility but does not distinguish
     between a 3-step synthesis of a flat achiral molecule and a 12-step asymmetric
     synthesis of a compound with 3 stereocenters. For kinase inhibitors, this matters
     less than for natural products, but some VAE-generated molecules may contain
     stereocenters that are trivial to draw but expensive to install.

   - **Scale-up feasibility:** A route that works on 10 mg scale may fail at 10 g scale
     (e.g., routes requiring cryogenic conditions, hazardous reagents, or chromato-
     graphic purification at every step). RAscore does not distinguish between robust
     and fragile routes.

   - **Building block availability and cost:** RAscore was trained on ChEMBL chemical
     space using AiZynthFinder with a specific stock database. If a route requires a
     building block that costs $500/g, the route is "feasible" by RAscore but
     impractical. This is why building block availability matters.

   - **Functional group incompatibilities:** Some generated molecules may contain
     functional groups that are incompatible in the same synthetic sequence (e.g., a
     free amine adjacent to an electrophilic carbonyl that would cyclize). RAscore
     treats the molecule as a whole but does not reason about step-wise compatibility.

   The proposal acknowledges that RAscore is a "fast proxy" and uses AiZynthFinder as
   ground truth for top candidates. This is the right architecture. But the paper should
   explicitly note that RAscore AUC of 0.81 means roughly 1 in 5 predictions is wrong.
   For publication purposes, the AiZynthFinder routes for the top 50 candidates are the
   credible evidence, not the RAscore screening.

   - **Severity:** Major
   - **Addressable?** Partially -- already mitigated by the tiered approach. Further
     strengthened by: (a) checking building block availability against Enamine's in-stock
     catalog (the proposal mentions this but does not specify it as a requirement), (b)
     counting synthetic steps and flagging routes > 8 steps as impractical for early-
     stage drug discovery, (c) noting which AiZynthFinder routes require protecting group
     chemistry, chromatographic separation, or other cost-intensive steps.

3. **Building block availability is mentioned but not operationalized.**

   The proposal mentions using Enamine building blocks as the AiZynthFinder stock
   database but does not make this a hard requirement. It lists ZINC as a "fallback."
   This matters enormously:

   - Enamine's in-stock building block catalog represents molecules that can be purchased
     and delivered in 2-4 weeks. A route built on Enamine building blocks is actionable.
   - ZINC is a virtual catalog -- many molecules listed in ZINC are not commercially
     available. A route built on ZINC building blocks may require custom synthesis of
     starting materials, adding months and thousands of dollars.
   - The difference between 60% solve rate (ZINC) and 80% solve rate (Enamine or
     eMolecules) reflects the difference between virtual and real availability.

   For a paper claiming "translational drug-ability," using commercially available
   building blocks is essential. ZINC should not be the primary stock.

   - **Severity:** Major
   - **Addressable?** Yes -- require Enamine REAL (which is freely downloadable for
     academic use) as the primary stock database. Report solve rates against both Enamine
     and ZINC for transparency. Flag candidates whose routes require non-commercially-
     available building blocks.

4. **The survival funnel success thresholds are poorly calibrated against industry
   reality.**

   The proposal suggests that a 5-10% end-to-end survival rate "is a positive result"
   if comparable to published baselines. From a medicinal chemistry perspective:

   - Drug discovery attrition rates (the "95% failure" figure cited) refer to clinical
     trial failure, not computational filtering. These numbers are not comparable. A
     computational pipeline has a fundamentally different filter cascade than a clinical
     program.

   - A more relevant benchmark is hit-to-lead conversion rates in industry HTS campaigns.
     Typical hit rates from high-throughput screening are 0.1-1% of the library. Hit
     confirmation rates (dose-response, selectivity, ADMET counter-screening) retain
     about 10-30% of primary hits. Lead optimization selects about 1-5% of confirmed
     hits for advancement.

   - For an AI-generated candidate set (not a random screening library), the benchmark
     should be much higher than HTS: these are supposedly "designed" molecules. If only
     5% of AI-designed molecules survive basic ADMET filtering, that suggests the
     generation process is not learning drug-like properties effectively.

   - A more informative benchmark: REINVENT-generated molecules (Loeffler et al., 2024)
     with multi-component scoring typically produce 30-50% of candidates passing Ro5
     filters and ADMET soft checks. If StateBind's state-aware candidates fall below
     this, the generation method has a drug-likeness problem.

   - **Severity:** Minor
   - **Addressable?** Yes -- benchmark the funnel survival rate against REINVENT (multi-
     component scoring), Chemistry42 (Insilico), and any published 3D generative model
     survival rates. Define explicit benchmarks: > 50% passing RAscore, > 30% passing
     kinase-calibrated ADMET, > 20% with AiZynthFinder routes. Below these rates, the
     paper should discuss why.

5. **PKSmart projections add noise, not signal, at their reported accuracy.**

   The proposal reports PKSmart external validation: VDss R^2=0.39 (GMFE=2.46), CL
   R^2=0.46 (GMFE=1.95). Let me translate what these numbers mean in practice:

   - **VDss R^2=0.39:** The model explains 39% of variance in volume of distribution.
     A GMFE of 2.46 means predictions are on average 2.5-fold off from experimental
     values. For a compound with true VDss of 3 L/kg, the prediction could be anywhere
     from 1.2 to 7.4 L/kg. This is insufficient to distinguish between a compound that
     distributes to tissues (VDss > 2 L/kg, desirable for solid tumors) and one confined
     to plasma (VDss < 0.5 L/kg).

   - **CL R^2=0.46:** Similar. A GMFE of 1.95 means a predicted clearance of 10 mL/min/
     kg could be anything from 5 to 20 mL/min/kg. The difference between 5 (low
     clearance, long half-life) and 20 (high clearance, short half-life) is the
     difference between QD dosing and QID dosing.

   - **Half-life:** Derived from VDss and CL, compounding both errors. The prediction
     interval for half-life is likely 3-4 fold, making it uninformative for dose
     projection.

   The proposal acknowledges this and says it will present PK "as directional only" with
   categories ("favorable/acceptable/unfavorable"). But even categorical classification
   requires more accuracy than these models provide. A compound classified as "favorable
   PK" could easily have unfavorable real PK.

   From a publication perspective, including PKSmart projections that explain less than
   half the variance risks attracting reviewer criticism: "Why are you reporting PK
   predictions that are essentially uninformative?" The rebuttal ("they are directional")
   is weak.

   - **Severity:** Major
   - **Addressable?** Yes -- demote PKSmart from a formal pipeline tier to a
     supplementary analysis. Remove the "PK acceptable" row from the survival funnel.
     Report PKSmart predictions in a supplementary table with prominent uncertainty
     disclaimers. The survival funnel should end at "ADMET clean + AiZynthFinder route
     found." Alternatively, if PK data is retained, frame it explicitly as: "We include
     PK projections to demonstrate the principle of end-to-end profiling, while
     acknowledging that current open-source PK models have insufficient accuracy for
     clinical dose projection (R^2 = 0.39-0.46)."

6. **The scoring function integration (Option A) conflicts with the fair comparison
   requirement.**

   The proposal recommends adding RAscore as a 5th scoring component (weight 0.15),
   reducing reference similarity from 0.35 to 0.30 and state specificity from 0.15 to
   0.10. This directly conflicts with datasci-P01's requirement for stable scoring
   across the multi-kinase validation.

   The Round 2 synthesis resolved this tension: "lock original scoring for primary
   endpoint, report revised scoring as secondary analysis." The proposal should adopt
   this resolution explicitly. RAscore integration into scoring is a secondary analysis
   ONLY, reported after the primary fair comparison is complete.

   Additionally, reducing state specificity from 0.15 to 0.10 to make room for RAscore
   specifically weakens the component that captures the state-aware signal. A reviewer
   who notices this will ask whether the weight change was designed to maintain the
   enrichment result. This should be avoided by instead presenting RAscore integration
   as a standalone supplementary analysis with its own weight sensitivity.

   - **Severity:** Major
   - **Addressable?** Yes -- adopt the Round 2 synthesis resolution. Primary analysis
     uses original 4-component scoring. RAscore integration is a supplementary analysis.
     If reported, the weight redistribution should be justified independently (e.g.,
     based on a weight sensitivity analysis across random Dirichlet configurations) and
     should not preferentially reduce state specificity.

7. **ADMETlab 3.0 as an external API dependency introduces reproducibility concerns.**

   The proposal relies on ADMETlab 3.0's public API for 119 ADMET endpoint predictions.
   Publication-grade reproducibility requires that any reader can reproduce the results.
   External APIs can change their models, update predictions, or go offline:

   - ADMETlab 3.0 was published in 2024. Its API has been operational for ~2 years. But
     there is no guarantee of version stability. If ADMETlab updates its models to v3.1
     in 2027, the predictions may change.
   - The batch web interface is a manual fallback, not a reproducible workflow.

   For the 6 priority endpoints, it would be stronger to use locally installable models
   where possible. The StateBind ADMET model (hERG, CYP3A4) already exists. For
   additional endpoints, open-source alternatives like TDC models or DeepPurpose can
   be installed locally.

   - **Severity:** Minor
   - **Addressable?** Yes -- record the exact ADMETlab 3.0 version and API endpoint used.
     Cache all raw API responses as JSON artifacts. Report the access date. Note in the
     methods section that predictions were obtained on a specific date from a specific
     API version. This is sufficient for publication-grade reproducibility in the
     cheminformatics community (similar to how PDB structures are cited by access date).

---

## Feasibility Assessment

### Technical Feasibility

Strong. All tools are pip-installable, CPU-only (except optional GPU acceleration for
AiZynthFinder with ONNX models), and well-documented. RAscore, AiZynthFinder, and
PKSmart have been used in numerous published studies. ADMETlab 3.0 has been online since
mid-2024. The compute requirements (< 2 hours) are trivial for Bouchet.

The primary technical risk is Python version compatibility. RAscore was built for Python
3.7+ with TensorFlow, which may conflict with StateBind's Python 3.10-3.12 environment.
The proposal correctly identifies the XGBoost-based RAscore model as a fallback. A
separate conda environment for RAscore is the safest approach.

### Scientific Feasibility

Moderate to strong. The pipeline will produce useful data regardless of the outcome.
Even if the state-aware candidates have poor ADMET profiles or low synthesis feasibility,
that is informative and publishable (with appropriate framing). The main scientific risk
is that the analysis reveals problems with the generation process (e.g., poor drug-
likeness, ADMET liabilities) that complicate the publication narrative. This is
addressable through honest reporting and framing as "areas for improvement" rather than
failures.

### Timeline Feasibility

3-4 weeks is realistic. The bottleneck is likely scripting the ADMETlab 3.0 API client
and analyzing 119 endpoints, not the computation itself. AiZynthFinder on 50 molecules
takes about 1 hour. RAscore on 491 molecules takes seconds. PKSmart on 20 molecules
takes minutes. The main time investment is analysis and figure preparation.

---

## Suggested Modifications

1. **Raise the hERG threshold to > 1.0 uM and report under dual thresholds.** Use
   1.0 uM as the "kinase-calibrated" threshold and 10 uM as the "standard" threshold.
   Report results under both. Discuss the hERG IC50:Cmax ratio framework (Lehmann et al.,
   2018) as the more pharmacologically relevant metric, noting that absolute thresholds
   are oversimplifications. This demonstrates ADMET sophistication that reviewers will
   respect.

2. **Require Enamine REAL as the primary building block database for AiZynthFinder.**
   Report solve rates against Enamine (commercially available building blocks) as the
   primary metric. ZINC solve rates as secondary. Flag candidates whose routes require
   non-commercial building blocks. For the top 10 candidates, manually verify that all
   building blocks are in the 2026 Enamine REAL catalog.

3. **Demote PKSmart from a pipeline tier to a supplementary analysis.** Remove the "PK
   acceptable" filter from the survival funnel. Report PKSmart predictions in a
   supplementary table with explicit uncertainty bounds (GMFE 2-3x). The survival
   funnel should have 3 stages: RAscore screening, ADMET profiling, AiZynthFinder
   retrosynthesis. This avoids presenting predictions of questionable accuracy as a
   formal filter.

4. **Add synthetic step count as a practical feasibility metric.** For AiZynthFinder
   routes, report the number of synthetic steps. Flag routes > 8 steps as "complex"
   and routes > 12 steps as "impractical for early-stage drug discovery." A medicinal
   chemist in a lead optimization program will not pursue a 15-step synthesis for a
   first-round candidate. The median synthetic step count (state-aware vs static) is
   a useful publication metric.

5. **Adopt the Round 2 synthesis resolution for scoring integration.** RAscore
   integration into the scoring function is a supplementary analysis only, reported
   after the primary 4-component comparison. Do not reduce state specificity weight to
   accommodate RAscore -- this creates an appearance of scoring manipulation.

6. **Benchmark survival rates against REINVENT and Chemistry42 published results.**
   Define explicit a priori benchmarks for each funnel stage. If StateBind's survival
   rates are comparable to or better than these published baselines, that is a positive
   result. If worse, discuss why (e.g., VAE generation is less constrained than
   REINVENT's reinforcement learning).

7. **For the top 10 candidates, add a brief qualitative medicinal chemistry assessment.**
   Have the pipeline flag: (a) the number of rotatable bonds (> 10 is a flexibility
   concern), (b) the presence of known PAINS motifs or medicinal chemistry exclusion
   filters (Baell & Holloway, 2010), (c) the presence of reactive functional groups
   (Michael acceptors, acyl halides, epoxides) that may be artifacts of SELFIES
   decoding rather than intentional design features, (d) the number of stereocenters.
   These are the first things a medicinal chemist looks at when evaluating a virtual
   hit list.

---

## Alternative Approaches

An alternative to the post-hoc drug-ability assessment would be to integrate
synthesizability and ADMET into the generation loop itself. REINVENT 4, PMMG, and
ADMETrix all do this. However, the proposal correctly identifies that this would be a
much larger engineering effort (months, not weeks) and that StateBind's post-hoc
approach is "a pragmatic middle ground" that is sufficient for publication.

A stronger alternative for the retrosynthesis component specifically would be to use
SynFormer (Gao et al., PNAS 2025), which generates molecules with built-in synthesis
trees. This would make the retrosynthesis step trivial (every generated molecule has a
route by construction) but would require replacing the SELFIES VAE with a
fundamentally different generation architecture. This is a major infrastructure change
that is not justified for the current publication timeline.

A third alternative for ADMET profiling is to use the Therapeutic Data Commons (TDC)
ADMET benchmark models locally rather than the ADMETlab 3.0 API. TDC provides
standardized benchmarks for 22 ADMET endpoints with published performance metrics. The
advantage is full local reproducibility; the disadvantage is fewer endpoints (22 vs 119)
and potentially lower accuracy than ADMETlab 3.0's multi-task model. Using both and
comparing would be the most thorough approach, but may be beyond scope for the 3-4 week
timeline.

---

## Impact on Publication Narrative

This proposal transforms the paper from a computational proof-of-concept ("we generate
and score molecules") to a translational demonstration ("we generate, score, profile,
and route-plan molecules"). For a JCIM submission, this is exactly what distinguishes a
solid methods paper from a forgettable one.

The survival funnel figure, if well-executed, could become the paper's most cited
contribution. It provides a template for how AI drug design papers should report results
-- not just generation metrics, but end-to-end viability.

However, the narrative depends critically on what the funnel reveals. Three scenarios:

1. **State-aware candidates have higher survival rates:** Strongest narrative. State-
   aware design produces both better-enriched and more drug-like candidates. The paper
   becomes: "State-aware design wins on every dimension."

2. **State-aware candidates have similar or lower survival rates:** The diversity-
   drugability tradeoff narrative. The paper becomes: "State-aware design explores more
   chemical space, which improves enrichment but requires more stringent filtering.
   The net effect is still positive because the starting enrichment advantage (10x) is
   large enough to survive attrition."

3. **Very few candidates survive from either pipeline:** The generation method needs
   improvement. The paper becomes: "We demonstrate the principle of end-to-end
   assessment and identify ADMET and synthesizability as the key bottlenecks for future
   work." Less impactful but still publishable.

The proposal should pre-register which scenario it expects and how the narrative will
adapt. This parallels the datasci-P01 approach of pre-registering positive, negative,
and mixed outcomes.

---

## References

1. Lehmann HA, Kotz M, Patel M, et al. (2018). Validation and clinical utility of the
   hERG IC50:Cmax ratio to determine the risk of drug-induced torsades de pointes.
   Pharmacotherapy 38(3):341-348. DOI: 10.1002/phar.2087.

2. Baell JB, Holloway GA. (2010). New substructure filters for removal of pan assay
   interference compounds (PAINS) from screening libraries and for their exclusion in
   bioassays. J Med Chem 53(7):2719-2740. DOI: 10.1021/jm901137j.

3. Loeffler H, He J, Tibo A, et al. (2024). REINVENT 4: Modern AI-driven generative
   molecule design. J Cheminformatics 16:20. DOI: 10.1186/s13321-024-00812-5.

4. Gao W, Mercado R, Coley CW. (2025). Generative AI for navigating synthesizable
   chemical space. PNAS 122(41):e2415665122. DOI: 10.1073/pnas.2415665122.

5. Metz JT, Johnson EF, Soni NB, et al. (2011). Navigating the kinase genome: an
   interactive pharma perspective. Mol Informatics 30(1):12-18.

6. Roskoski R. (2021). Small molecule kinase inhibitor drugs (1995-2021): medical
   indication, pharmacology, and synthesis. J Med Chem 65(2):1003-1072.
   DOI: 10.1021/acs.jmedchem.1c00963.

7. Zhong Y, et al. (2023). Acute osimertinib exposure induces electrocardiac changes
   by synchronously inhibiting the currents of cardiac ion channels. Front Pharmacol
   14:1177003. DOI: 10.3389/fphar.2023.1177003.

8. Redfern WS, Carlsson L, Davis AS, et al. (2003). Relationships between preclinical
   cardiac electrophysiology, clinical QT interval prolongation and torsade de pointes
   for a broad range of drugs. Cardiovasc Res 58(1):32-45.

9. Thakkar A, Chadimova V, Bjerrum EJ, et al. (2021). Retrosynthetic accessibility
   score (RAscore) -- rapid machine learned synthesizability classification from AI
   driven retrosynthetic planning. Chem Sci 12:3339-3349. DOI: 10.1039/D0SC05401A.

10. Fu L, et al. (2024). ADMETlab 3.0: an updated comprehensive online ADMET prediction
    platform. Nucleic Acids Research 52(W1):W422-W431. DOI: 10.1093/nar/gkae236.

11. Seal S, et al. (2025). PKSmart: an open-source computational model to predict
    intravenous pharmacokinetic parameters of small molecules. J Cheminformatics 17.
    DOI: 10.1186/s13321-025-01066-5.

12. Gao S, et al. (2024). Evaluating molecule synthesizability via retrosynthetic
    planning and reaction prediction. arXiv:2411.08306v2.

13. Neeser R, et al. (2024). FSscore: a personalized machine learning-based synthetic
    feasibility score. Chemistry-Methods 4(6):e202400024. DOI: 10.1002/cmtd.202400024.

14. Wang Z, et al. (2021). Mechanisms of gefitinib-induced QT prolongation. European
    Journal of Pharmacology 910:174467. DOI: 10.1016/j.ejphar.2021.174467.
