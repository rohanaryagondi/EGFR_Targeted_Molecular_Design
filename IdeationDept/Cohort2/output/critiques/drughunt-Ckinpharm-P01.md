---
agent: Senior Drug Hunter
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: kinpharm-P01
---

# Critique: Multi-Kinase Generalization of State-Aware Molecular Design -- From EGFR Case Study to Kinome-Wide Validation

## Reviewing Agent

Senior Drug Hunter (drughunt), Cohort2. 25+ years in drug discovery program leadership, Target Product Profile design, competitive landscape analysis, translational strategy, and IND-enabling decision-making. My critique is informed by my Round 1 research on the EGFR competitive landscape, the $7B+ TKI market, the 4th-generation EGFR TKI pipeline failures, the Type II (DFG-out) opportunity for EGFR, and publication strategy for computational drug design (drughunt-R01).

## Proposal Summary

kinpharm-P01 proposes extending StateBind's retrospective validation from EGFR alone to 5 kinases (EGFR, ABL1, BRAF, ALK, JAK2) to demonstrate that state-aware molecular design generalizes across the kinome. The proposal has four components: (A) multi-kinase data curation from ChEMBL, (B) a 5-kinase conformational state atlas using KLIFS + AF2-MSM supplementation, (C) a multi-task state-conditioned MPNN, and (D) retrospective validation with pooled statistical analysis plus a DFG-out selectivity hypothesis test against PKIS2/KCGS datasets. The target venue is Nature Computational Science with an estimated 10-14 week timeline and 20 GPU-days of compute.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The multi-kinase extension is scientifically necessary for a top-venue publication and addresses the single most damaging reviewer criticism (N=3-5 held-out drugs), but the proposal spreads itself too thin across 5 kinases at the expense of deep translational narrative on any single therapeutic area, and the kinase selection should be reconsidered from a drug program perspective.

---

## Strengths

### 1. Correctly identifies the statistical Achilles' heel (Critical)

The proposal accurately diagnoses the core vulnerability of the current StateBind manuscript: with N=3-5 held-out drugs, confidence intervals on the enrichment factor are too wide for Nature Computational Science. The power analysis (0.85 at alpha=0.05 with 5 kinases vs 0.60 with 3) is well-reasoned. From a drug program perspective, I would never take a go/no-go decision on N=5 data points, and reviewers will apply the same standard. The pooled meta-analysis approach with bootstrap CIs and heterogeneity testing (I-squared statistic) is exactly what the paper needs.

### 2. The DFG-out selectivity hypothesis is genuinely novel

The formal test of whether DFG-out-conditioned generation produces more selective molecules -- validated against PKIS2 (645 compounds, 392 kinases) and KCGS 2.0 (295 compounds, 262 kinases) -- is the strongest conceptual contribution of this proposal. The Ung et al. (2015) data showing Gini coefficients of 0.72 (Type II) vs 0.51 (Type I) provides a quantitative baseline for the expected effect size. This connects to a deep translational insight: selectivity is what separates a clinical candidate from a lab curiosity, and a computational method that systematically generates more selective molecules has immediate value to drug programs.

### 3. Multi-task MPNN with state conditioning is a publishable ML contribution

The architecture -- shared D-MPNN encoder with kinase embedding + 9D state vector concatenation -- is simple, interpretable, and well-justified. The ablation design (single-task vs multi-task vs multi-task + state conditioning) isolates each contribution cleanly. This is the kind of systematic ablation that reviewers demand and that many ML papers fail to provide.

### 4. Compute budget is realistic

20 GPU-days on H200 nodes for the entire project is modest and well within Yale Bouchet's capacity. The breakdown (14 GPU-days for GNINA docking as the bottleneck) is honest and accounts for the dominant cost correctly. From a program management perspective, compute is not the risk here.

### 5. Risk assessment is honest

The proposal's acknowledgment that enrichment may not generalize to all 5 kinases, with a pre-planned mitigation (report I-squared heterogeneity honestly, fall back to "kinases with rich conformational data" framing) is the kind of scientific maturity that distinguishes a strong proposal from a naive one. The AF2-MSM quality threshold (docking AUC >= 0.70 or fall back to 2-state analysis) is similarly well-thought-out.

---

## Weaknesses (with Severity and Addressable?)

### 1. Kinase selection prioritizes data availability over translational coherence (Severity: High, Addressable: Yes)

The 5 kinases (EGFR, ABL1, BRAF, ALK, JAK2) were selected because they have the richest ChEMBL and PDB data. From a data science perspective, this makes sense. From a drug program perspective, it creates a confused translational narrative.

**The problem:** These 5 kinases span 4 completely different therapeutic areas with different patient populations, competitive landscapes, and development strategies:

- **EGFR**: NSCLC, C797S resistance (the StateBind core story)
- **ABL1**: CML, T315I resistance (well-solved by ponatinib and asciminib)
- **BRAF**: Melanoma and other solid tumors (combination therapy paradigm, not monotherapy)
- **ALK**: NSCLC ALK+ (lorlatinib dominates, resistance is different from EGFR)
- **JAK2**: Myeloproliferative neoplasms (JAK inhibitors are not kinase-selective in the traditional sense; ruxolitinib hits JAK1/JAK2 equally)

A pharma portfolio committee would ask: "What therapeutic hypothesis does this serve?" The answer is: none, specifically. It is a methods validation exercise.

**Why this matters:** Nature Computational Science will accept a methods paper. But the paper's real-world impact (and thus its citation count, media attention, and industry interest) depends on whether the reader can connect the method to a drug program they care about. Five scattered kinases dilute this connection.

**My recommendation:** Keep 3-4 kinases maximum. Prioritize kinases where the conformational state story directly connects to a clinical mechanism of resistance:

- **EGFR** (keep): Core story, C797S resistance, Type II opportunity
- **ABL1** (keep): Imatinib is the archetypal DFG-out drug, T315I resistance is conformational, asciminib (allosteric) validates state-selective design
- **BRAF** (keep with caveats): Vemurafenib binds DFG-out BRAF-V600E, paradoxical activation of WT BRAF is conformational, directly tests whether state-aware design can predict selectivity between mutant and WT
- **ALK** (downgrade or drop): Pre-2010 data is sparse (N~800), DFG-out structures require AF2 supplementation, and the clinical narrative is weaker because lorlatinib already addresses most resistance. If kept, relegate to supplementary analysis
- **JAK2** (drop or replace): JAK inhibitors are pan-JAK by design (ruxolitinib, fedratinib). Selectivity is not the clinical goal for JAK2 programs -- efficacy across JAK family members is. This fundamentally contradicts the DFG-out selectivity hypothesis

A focused 3-kinase panel (EGFR + ABL1 + BRAF) with a deep translational framing around "conformational resistance mechanisms" would be more compelling than a diffuse 5-kinase survey. Each of these 3 kinases has an approved drug that exploits the DFG-out conformation (imatinib for ABL1, vemurafenib for BRAF, none for EGFR -- making EGFR the prediction target).

### 2. No Target Product Profile framework for generated molecules (Severity: High, Addressable: Yes)

The proposal evaluates retrospective enrichment and predicted selectivity, but never asks: "Do the generated molecules look like real drug candidates?" My R01 research note defined a detailed TPP for state-selective EGFR inhibitors (IC50 < 100 nM target, > 10-fold WT selectivity, hERG > 10 uM, oral bioavailability > 20%, MW < 600, SA score < 6). None of these criteria appear in kinpharm-P01.

**Why this matters for publication:** Reviewers at Nature Computational Science will not only ask "does this method find known drugs?" but also "does it generate plausible new candidates?" Reporting that the top-ranked state-aware molecules meet 6/8 TPP criteria while top-ranked static molecules meet 3/8 would be a devastating additional figure supporting the state-aware advantage.

**Why this matters for industry translation:** Pharma companies do not care about enrichment factors. They care about whether a computational method generates molecules they can put into their pipeline. A TPP comparison directly answers this question.

**Recommendation:** Add a TPP evaluation component to Step D. For each kinase, define a literature-derived TPP (I have already drafted the EGFR version in drughunt-R01). Score the top 50 state-aware and top 50 static candidates against the TPP criteria. Report the fraction meeting minimum acceptable thresholds and ideal targets.

### 3. The Relay Therapeutics comparison is an opportunity being mishandled (Severity: Medium, Addressable: Yes)

The proposal mentions Relay once, in the Background section, as a precedent for conformational-state-aware drug design. This undersells the comparison and creates a vulnerability.

**The risk:** A reviewer familiar with Relay will ask: "How does StateBind compare to Relay's Dynamo platform? Why should I care about a discrete-state VAE when Relay uses continuous molecular dynamics?" If the paper does not preemptively and thoroughly address this, the reviewer will conclude that StateBind is an inferior version of an existing commercial platform.

**The opportunity:** The comparison should be a featured section of the paper, framed as "closed-source continuous dynamics (Relay/Dynamo) vs open-source discrete-state ML (StateBind)." Key differentiation points:

- Relay requires cryo-EM + long-timescale MD ($1M+ per target); StateBind uses PDB crystal structures + 20 GPU-days
- Relay is proprietary; StateBind is open-source and reproducible
- Relay has validated one target (PI3K-alpha); StateBind validates across 5 kinases (if the multi-kinase analysis succeeds)
- The discrete-state assumption is a simplification but enables generalization to kinases without MD data

If this comparison is not handled carefully, it becomes the paper's biggest weakness instead of one of its most compelling framing elements.

### 4. The state assignment approximation for training compounds is under-addressed (Severity: Medium, Addressable: Partially)

The proposal acknowledges (Open Question 1) that most ChEMBL compounds lack co-crystal structures, requiring heuristic state assignment (Type I -> DFGin, Type II -> DFGout). But the sensitivity analysis is deferred as "should be done" rather than designed into the protocol.

**The drug program perspective:** In a hit-to-lead campaign, I would never accept an activity model trained on heuristically assigned binding modes without a thorough validation of that heuristic. The Type I/Type II classification itself is coarse -- many inhibitors bind intermediate conformations (DFGinter, as classified by KLIFS). Misassignment rates could easily be 15-30% for compounds without co-crystal structures.

**Recommendation:** Include a calibration experiment: for the subset of compounds in each kinase's ChEMBL set that DO have co-crystal structures (likely 5-15% of compounds for well-studied kinases), compute the misclassification rate of the heuristic assignment versus the crystallographically observed state. Report this rate per kinase and use it to parameterize the sensitivity analysis.

### 5. The selectivity analysis on a 5-kinase panel has limited translational meaning (Severity: Medium, Addressable: Partially)

The proposal's own Open Question 4 identifies this: a Gini coefficient computed across 5 kinases is not kinome selectivity. Real selectivity profiling (DiscoverX KINOMEscan, Eurofins kinase panel) uses 400+ kinases. The PKIS2/KCGS validation against broader panels partially mitigates this, but the core selectivity claim will still rest on 5-kinase predicted Gini values.

**The drug program perspective:** When I evaluate a hit series for selectivity, I need at minimum a 50-kinase panel to make a meaningful statement, and ideally the full kinome. A 5-kinase Gini coefficient could be high simply because the 5 kinases are structurally diverse, not because the molecule is genuinely selective.

**Recommendation:** Reframe the selectivity claim carefully. Use "within-panel selectivity" or "predicted target preference" rather than "kinome selectivity." Reserve the strong selectivity language for the PKIS2/KCGS validation results, where the panel breadth supports the claim.

### 6. JAK2 drug selection conflates JAK1/JAK2 selectivity with the DFG-out hypothesis (Severity: Medium, Addressable: Yes)

The JAK2 held-out drug list includes tofacitinib (a pan-JAK inhibitor developed primarily for JAK3 and approved for rheumatoid arthritis, not a JAK2-selective agent), baricitinib (JAK1/JAK2, approved for RA), and deuruxolitinib (JAK1/JAK2, approved for alopecia areata). These are not JAK2-selective drugs. Including them in a retrospective enrichment analysis for JAK2 introduces confounding: the enrichment factor reflects whether the model identifies compounds active against JAK2, not whether it identifies compounds designed for JAK2.

**For the DFG-out selectivity hypothesis specifically:** Most JAK inhibitors are Type I (DFG-in). Fedratinib is the only JAK2-selective Type II-like inhibitor in the list, and even its binding mode is debated. Testing the DFG-out selectivity hypothesis on JAK2 with a held-out set dominated by Type I inhibitors does not test the hypothesis -- it tests whether the state-aware approach can identify Type I inhibitors despite conditioning on DFG-out states.

---

## Feasibility Assessment

### Technical Feasibility

**Rating: High.** All components use existing tools and protocols. ChEMBL data curation replicates a proven EGFR workflow. KLIFS provides conformational annotations. Chemprop v2 is production-grade for multi-task MPNN. GNINA docking is established. AF2-MSM supplementation follows a published protocol (Song et al., 2024). The technical execution risk is low.

**One concern:** The cross-kinase feature normalization (Step B4) is more subtle than the proposal suggests. Z-score normalization using EGFR parameters means that if, say, ALK's DFG-out pocket volume falls outside the EGFR distribution, it will be an outlier in the normalized space. A global normalization across all 5 kinases is more principled but means re-normalizing EGFR's features, potentially changing the existing EGFR results. This needs a design decision before implementation, not during.

### Scientific Feasibility

**Rating: Medium-High.** The core hypothesis -- that state-aware design generalizes across kinases -- is scientifically sound and supported by the mechanistic logic (less conserved DFG-out pocket enables selectivity). However, two scientific risks are substantive:

1. **The enrichment may be EGFR-specific.** EGFR has the richest structural and bioactivity data of any kinase. The 10x enrichment may reflect this data richness rather than the intrinsic value of state-aware design. If ALK and JAK2 (with sparser data and more AF2-supplemented structures) show no enrichment, the conclusion is that the method requires rich conformational data -- which limits its generalizability claim.

2. **The multi-task MPNN's expected improvement is modest.** Published benchmarks show +0.03-0.04 R-squared improvement from multi-task learning on random splits, and nearly zero on scaffold splits. The state conditioning adds another +0.02 expected. These are small effect sizes that may not be statistically significant with 5 kinases and may not translate into meaningful enrichment improvements.

### Timeline Feasibility

**Rating: Medium.** The 10-14 week estimate for a single researcher is optimistic for the full 5-kinase scope. In my experience managing drug discovery teams:

- **Data curation (2.5 weeks):** Realistic if the EGFR protocol is fully automated and can be templated. If manual curation decisions are needed per kinase (they always are), add 1-2 weeks.
- **State atlas (2 weeks):** KLIFS retrieval is fast, but AF2-MSM generation + validation (docking AUC) for ALK and JAK2 is at least 1 week of researcher time beyond the compute.
- **Multi-task MPNN (4 weeks):** Training is fast, but debugging multi-task loss balancing, diagnosing poor performance on individual kinases, and running ablations always takes longer than planned. Budget 5-6 weeks.
- **Validation + statistics (4 weeks):** GNINA docking across 20 kinase-state combinations with 4000 candidates each is the compute bottleneck (14 GPU-days), but the analysis, figure generation, and writing around those results is substantial. Budget 5-6 weeks.
- **Writing (2 weeks):** For a Nature Computational Science manuscript with 5 main figures, extended data, and supplementary methods, 2 weeks is aggressive. Budget 3-4 weeks.

**Revised estimate:** 14-20 weeks for a single researcher, or 10-14 weeks with two researchers splitting data curation / atlas construction (Researcher 1) and ML / validation (Researcher 2). The proposal's 10-14 week estimate is achievable only if everything goes right the first time, which never happens.

---

## Suggested Modifications

### Modification 1: Reduce to 3-4 kinases with translational coherence (Priority: High)

Drop JAK2. Consider dropping ALK or relegating it to supplementary. Focus on EGFR + ABL1 + BRAF as a panel united by the theme "conformational resistance mechanisms in kinase inhibitor therapy." Each of these kinases has clinical cases where the DFG-out conformation is therapeutically relevant:

- **EGFR**: No approved Type II inhibitor; DFG-out targeting could address C797S resistance
- **ABL1**: Imatinib (Type II) revolutionized CML; T315I resistance is a conformational problem solved by ponatinib (Type II) and asciminib (allosteric)
- **BRAF**: Vemurafenib binds DFG-out V600E; paradoxical activation of WT is a conformational selectivity challenge

This panel tells a coherent story about how state-aware design addresses conformational resistance. The statistical power with 3 kinases is lower (0.60 vs 0.85), but the narrative coherence compensates. If the enrichment generalizes even across these 3, the claim is strong.

If a 4th kinase is needed for statistical power, add CDK2 (CMGC group, 400+ structures, well-characterized DFG states) with a modified validation protocol using clinical candidates rather than approved drugs, as the proposal's own Open Question 3 suggests.

### Modification 2: Add TPP evaluation as a core component (Priority: High)

Add a Step D5: "Target Product Profile Concordance Analysis." For each kinase, define a literature-derived TPP with 6-8 quantitative criteria matching real drug program standards. Score the top N candidates from each pipeline (state-aware vs static) against the TPP. Report concordance rates.

For EGFR, use the TPP I defined in drughunt-R01:
- IC50 < 100 nM (target), hERG > 10 uM, MW < 600, QED > 0.3, SA < 6, Lipinski compliance, predicted oral bioavailability > 20%

For ABL1 and BRAF, derive equivalent TPPs from the approved drug properties (imatinib/ponatinib for ABL1; vemurafenib/dabrafenib for BRAF).

This produces a compelling figure: "State-aware candidates meet X/8 TPP criteria vs Y/8 for static candidates" -- a message that resonates with both reviewers and industry readers.

### Modification 3: Develop the Relay comparison into a Discussion section centerpiece (Priority: Medium)

Transform the Relay mention from a one-paragraph background note into a structured comparison table:

| Feature | Relay/Dynamo | StateBind |
|---------|-------------|-----------|
| Conformational data | Cryo-EM + long-timescale MD | Crystal structures + AF2-MSM |
| State representation | Continuous dynamics | Discrete 4-state |
| Design approach | Physics-based + computational chemistry | Generative ML (VAE + MPNN) |
| Compute cost per target | $1M+ estimated | 20 GPU-days |
| Accessibility | Proprietary | Open-source |
| Clinical validation | RLY-2608 (PI3K-alpha, Phase 3) | Retrospective (5 kinases) |
| Kinase coverage | Single-target deep | Multi-target breadth |

Frame StateBind as the "accessible, generalizable alternative" to Relay's "deep, single-target platform." This positions the paper for maximum industry attention.

### Modification 4: Design the state assignment calibration experiment upfront (Priority: Medium)

For each kinase, identify the subset of ChEMBL compounds with co-crystal structures in the PDB. Compute the heuristic state assignment (Type I/II classification) and compare to the crystallographically observed DFG conformation. Report misclassification rates. Use these rates to parameterize the sensitivity analysis in Step D.

Expected misclassification rates: 10-15% for well-studied kinases (EGFR, ABL1), 20-30% for less-studied kinases (ALK, JAK2). This is honest, quantitative, and preempts the reviewer objection.

### Modification 5: Reframe selectivity claims to match panel breadth (Priority: Low)

Throughout the manuscript, use "within-panel target preference" when discussing 5-kinase MPNN predictions, and reserve "kinome selectivity" exclusively for the PKIS2/KCGS validation results. This is a framing change, not a scientific change, but it prevents reviewers from dismissing the selectivity analysis for overclaiming.

---

## Alternative Approaches

### Alternative 1: Deep EGFR-only paper with generative model benchmarking

Instead of going broad (5 kinases), go deep on EGFR with head-to-head comparison against REINVENT 4, DiffSBDD, and random generation on MolScore/GuacaMol standardized tasks. This addresses the reviewer concern about generative model comparison (which the current proposal ignores entirely) and produces a paper that is immediately actionable for EGFR drug programs.

**Pros:** Simpler execution, direct head-to-head with state-of-the-art, stronger translational narrative for the $7B EGFR market, could include TPP analysis and DFG-out selectivity on a deeper EGFR dataset.

**Cons:** Single-target limits generalizability claim, weaker statistical power, may not reach Nature Computational Science threshold.

**My assessment:** This is the JCIM-targeted version. If the team has bandwidth for only one paper, kinpharm-P01 is the right scope for Nature Comp Sci. But if two papers are possible, this EGFR-deep paper should be the second.

### Alternative 2: 3-kinase focused panel + resistance mechanism narrative

EGFR + ABL1 + BRAF, framed as "conformational state-aware design for kinases with conformational resistance mechanisms." Each kinase has approved drugs exploiting DFG-out conformations (ABL1: imatinib; BRAF: vemurafenib) or lacking them (EGFR: no Type II). The paper's narrative arc becomes: "State-aware design identifies DFG-out-exploiting drugs in kinases where they exist (ABL1, BRAF), and predicts which DFG-out molecules would be effective in EGFR, where no Type II inhibitor yet exists."

**Pros:** Tight translational narrative, each kinase has a clear clinical rationale, DFG-out selectivity hypothesis directly testable, smaller scope means faster execution.

**Cons:** N=3 kinases for statistical tests, fewer held-out drugs.

**My assessment:** This is my preferred approach. It sacrifices some statistical power for a dramatically stronger narrative. The kinase panel selection is not arbitrary (data-driven) but hypothesis-driven (conformational resistance). This is how drug programs select targets, and reviewers will respond to the logic.

---

## Impact on Publication Narrative

### Current narrative (EGFR-only): 
"State-aware design works 10x better than static for EGFR."

### Proposed narrative (kinpharm-P01, 5 kinases): 
"State-aware design generalizes across the kinome."

### My preferred narrative (3 kinases, resistance-focused): 
"State-aware design exploits conformational resistance mechanisms across therapeutically relevant kinases, generating selective molecules for DFG-out pockets that static approaches cannot access."

The third framing is the one that would get a drug program leader's attention. It connects the methodology to a clinical problem (resistance), a mechanistic hypothesis (DFG-out selectivity), and a drug design strategy (state-conditioned generation). The 5-kinase version is broader but shallower -- it demonstrates generalization but does not explain why a medicinal chemist should care.

For Nature Computational Science, the 5-kinase statistical rigor is important. But the narrative must be the resistance/selectivity story, not just "we tested on more kinases." The kinase selection should serve the narrative, not the other way around.

### Industry impact consideration

A pharma company reading this paper will ask three questions:
1. "Can I use this on my kinase target?" -- Answered by multi-kinase generalization (any panel addresses this).
2. "Will it generate molecules I can actually develop?" -- Answered ONLY if the paper includes TPP analysis (currently missing from the proposal).
3. "Does it solve a problem I cannot solve with existing tools?" -- Answered by the DFG-out selectivity dividend (the proposal's strongest contribution).

The proposal addresses questions 1 and 3 but completely ignores question 2. Adding TPP evaluation transforms the paper from a methods paper into a translational methods paper -- a much more impactful publication.

---

## References

1. Ung, P.M.U., et al. "Conformational analysis of the DFG-out kinase motif and biochemical profiling of structurally validated Type II inhibitors." *J Med Chem* 58(4), 1569-1585 (2015).
2. Wells, C.I., et al. "Progress towards a public chemogenomic set for protein kinases and a call for contributions." *PLOS One* 12(8), e0181585 (2017).
3. Elkins, J.M., et al. "The Kinase Chemogenomic Set (KCGS): An open science resource for kinase vulnerability identification." *Int J Mol Sci* 22(2), 566 (2021).
4. Song, Y., et al. "A comprehensive exploration of the druggable conformational space of protein kinases using AI-predicted structures." *PLOS Comp Biol* 20(8), e1012302 (2024).
5. Heid, E., et al. "Chemprop: A machine learning package for chemical property prediction." *J Chem Inf Model* 64(1), 9-17 (2024).
6. Schindler, T., et al. "Structural mechanism for STI-571 inhibition of Abelson tyrosine kinase." *Science* 289, 1938-1942 (2000).
7. Relay Therapeutics. Updated data for RLY-2608 + Fulvestrant. ASCO 2025. mPFS 11.0 months in 2L PI3Ka-mutated breast cancer.
8. Roskoski, R. Jr. "Properties of FDA-approved small molecule protein kinase inhibitors: A 2025 update." *Pharmacological Research* 200, 107483 (2025).
9. AstraZeneca. Full Year and Q4 2024 Results. Tagrisso revenue $7.25B (2025).
10. Su, Y., et al. "Fourth-generation epidermal growth factor receptor-tyrosine kinases inhibitors: hope and challenges." *Translational Cancer Research* (2024). PMC11384918.
11. Cho, B.C., et al. "Overall Survival with Amivantamab-Lazertinib in EGFR-Mutated Advanced NSCLC." *NEJM* (2025). HR 0.75, 3-year OS 60% vs 51%.
12. Oxnard, G.R., et al. "Assessment of Resistance Mechanisms and Clinical Implications in Patients With EGFR T790M-Positive Lung Cancer and Acquired Resistance to Osimertinib." *JAMA Oncology* 4(11), 1527-1534 (2018).
13. Martin, E., et al. "Large-scale modeling of sparse protein kinase activity data." *J Chem Inf Model* 63(11), 3451-3465 (2023).
14. Fang, Z., et al. "DFG-1 residue controls inhibitor binding mode and affinity." *J Med Chem* 63(21), 13124-13143 (2020).
15. Engel, J., et al. "Linking ATP and allosteric sites to achieve superadditive binding with bivalent EGFR kinase inhibitors." *Commun Chem* 7, 108 (2024).
16. Redfern, W.S., et al. "Relationships between preclinical cardiac electrophysiology, clinical QT interval prolongation and torsade de pointes." *Br J Pharmacol* 139, 533-541 (2003).
17. Loeffler, H.H., et al. "REINVENT 4: Modern AI-driven generative molecule design." *J Cheminformatics* 16, 20 (2024).
18. Schneuing, A., et al. "Structure-based drug design with equivariant diffusion models (DiffSBDD)." *Nature Computational Science* 4(12), 737 (2024).
