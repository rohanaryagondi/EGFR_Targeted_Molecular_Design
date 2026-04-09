---
agent: Senior Clinical Oncologist
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: kinpharm-P01
---

# Critique: Multi-Kinase Generalization of State-Aware Molecular Design -- From EGFR Case Study to Kinome-Wide Validation

## Reviewing Agent

Senior Clinical Oncologist (clinonc), Cohort2. 20+ years treating EGFR-mutant NSCLC and other kinase-driven malignancies. Perspective grounded in clinical unmet needs, resistance mechanisms, and translational feasibility.

## Proposal Summary

kinpharm-P01 proposes extending StateBind's retrospective validation from EGFR alone to 5 kinases (EGFR, ABL1, BRAF, ALK, JAK2). The work involves: (A) curating ChEMBL bioactivity data for 4 new kinases, (B) building a multi-kinase conformational state atlas using KLIFS and AlphaFold2-MSM, (C) training a multi-task state-conditioned MPNN across all 5 kinases, and (D) performing retrospective validation with pooled statistical testing and a DFG-out selectivity hypothesis test against PKIS2/KCGS datasets. The stated goal is a Nature Computational Science paper claiming generalization of state-aware design across the kinome.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** A well-engineered statistical strengthening of StateBind, but the proposal risks trading EGFR clinical depth for kinome-wide breadth that impresses computational reviewers more than it advances patient-relevant drug design.

---

## Strengths

### 1. The generalization question is legitimate and necessary

The proposal correctly identifies the most predictable reviewer objection: "Is this an EGFR artifact?" With only N=5 and N=3 held-out drugs in the current retrospective, the confidence intervals are indeed wide enough to drive a truck through. Expanding to 5 kinases with ~22 and ~15 held-out drugs (pre-2010 and pre-2015 splits respectively) is a statistically sound response. The power analysis (0.85 at alpha=0.05 with 5 kinases versus 0.60 with 3) is rigorous. No serious reviewer could dismiss a 5-kinase, 37-drug retrospective as easily as a single-target result.

### 2. The kinase selections are defensible from a structural biology standpoint

All 5 kinases have substantial PDB coverage and well-characterized conformational landscapes. ABL1 (350+ structures) and BRAF (150+ structures) have rich experimental DFG-out coverage, making the 4-state atlas feasible without heavy reliance on computational models. EGFR and ABL1 together have the two best-characterized DFG-in to DFG-out transitions in all of structural biology. The choice spans 3 kinase groups (TK, TKL, JAK), providing at least some taxonomic diversity.

### 3. The DFG-out selectivity hypothesis test is the proposal's strongest original contribution

Testing whether DFG-out-designed molecules are predicted to be more selective (Gini coefficients of 0.64-0.80 versus 0.49-0.52 for Type I from Ung et al., 2015) using PKIS2 and KCGS as external validation is the most clinically meaningful component. The selectivity question matters to patients because off-target kinase inhibition drives dose-limiting toxicities. If DFG-out state-conditioned generation systematically yields more selective chemotypes, that is a publishable finding with direct translational implications.

### 4. The statistical framework is thorough

Paired Wilcoxon on per-kinase enrichment, bootstrap meta-analysis with BCa confidence intervals, I-squared heterogeneity testing, and correlation of enrichment with conformational state diversity -- this is the kind of pre-registered statistical framework that Nature Computational Science reviewers respect. The proposal also wisely addresses the scenario where enrichment does not generalize to all 5 kinases (report honestly with random-effects model if I-squared > 50%).

### 5. Open Question 7 shows admirable self-awareness

Acknowledging that EGFR might contaminate the generalization claim because the method was originally developed and tuned on EGFR is a sophisticated concern. The recommendation to report 4-kinase (excluding EGFR) results separately is exactly what a careful reviewer would demand. This kind of methodological honesty strengthens the proposal.

---

## Weaknesses (with Severity and Addressable?)

### 1. The clinical unmet need narrative is diluted, not strengthened, by going broad

**Severity: High | Addressable: Yes, with reframing**

StateBind's most compelling clinical story is the EGFR C797S resistance crisis. As documented in my Round 1 research (clinonc-R01, Sections 2.2 and 5):

- C797S resistance affects 7-29% of osimertinib-treated patients
- The cis-configured triple mutant (activating + T790M + C797S) is truly undruggable by all approved TKIs
- Every small-molecule EGFR drug in clinical use binds DFG-in/alpha-C-in
- No DFG-out EGFR inhibitor has reached clinical development
- The 4th-generation pipeline (BDTX-1535, BLU-945, BBT-176, TQB3804) is entirely DFG-in focused

This is a concrete, urgent, patient-affecting gap. When the proposal pivots to "does this generalize across ABL1, BRAF, ALK, and JAK2?", the clinical urgency evaporates. A Nature Computational Science reviewer might find it impressive, but a clinical co-reviewer will ask: "So what does this mean for patients?" The answer becomes diffuse rather than sharp.

The proposal does not articulate a clinical unmet need for state-aware ABL1 design (asciminib, a STAMP inhibitor, already exploits the myristoyl pocket -- a different kind of allosteric approach), or for state-aware BRAF design (the vemurafenib-to-encorafenib evolution was driven by paradoxical activation biology, not conformational state selection), or for state-aware JAK2 design (JAK2 resistance is driven primarily by V617F reversion and off-target pathway activation, not binding site conformation).

### 2. The kinase choices are structurally convenient but clinically uneven

**Severity: Medium-High | Addressable: Yes, with explicit clinical justification per kinase**

Each kinase should be justified not just by "sufficient ChEMBL data and PDB structures" but by a specific clinical scenario where conformational state-aware design would address a gap that existing drugs do not:

- **ABL1**: The strongest clinical case after EGFR. The T315I gatekeeper mutation creates an unmet need analogous to C797S. Ponatinib (a Type II inhibitor) was developed specifically for T315I resistance. Asciminib targets the myristoyl pocket (allosteric). State-aware design for ABL1 DFG-out states has clear translational logic: finding Type II chemotypes distinct from ponatinib (which has serious vascular toxicity -- arterial occlusive events in 31% of patients at 45 mg, Cortes et al., 2018). **This clinical rationale is absent from the proposal.**

- **BRAF**: BRAF V600E is treated by Type I-and-a-half inhibitors (vemurafenib binds the alpha-C-out inactive conformation but with DFG-in). The resistance landscape is dominated by BRAF amplification, NRAS mutations, and MAPK pathway reactivation -- not binding-site mutations. State-aware design has a weaker clinical rationale here because the resistance problem is pathway-level, not pocket-level.

- **ALK**: ALK resistance is driven by kinase domain mutations (G1202R, compound mutations) that directly affect the binding pocket. State-aware design has moderate clinical relevance. However, the pre-2010 ALK data sparsity (N~800 compounds) is a genuine problem. ALK as an oncogene was only identified in 2007 (Soda et al., Nature 2007), and crizotinib was approved in 2011. The pre-2010 "retrospective validation" for ALK is conceptually strained: there was essentially no medicinal chemistry against ALK before 2007.

- **JAK2**: JAK2 inhibitors are used for myeloproliferative neoplasms, not solid tumors. The clinical landscape (ruxolitinib, fedratinib, pacritinib, momelotinib) is distinct from oncology kinase inhibitor design. Resistance to JAK2 inhibitors is primarily driven by clonal evolution and heterotypic signaling, not binding-site mutations amenable to conformational state selection. Including JAK2 risks making the paper's clinical narrative incoherent -- jumping from NSCLC to myelofibrosis is jarring for clinical reviewers.

### 3. Resistance mechanisms beyond EGFR are inadequately addressed

**Severity: Medium | Addressable: Yes**

The proposal discusses EGFR resistance only implicitly (through the DFG-out selectivity hypothesis). For a multi-kinase paper claiming translational relevance, each kinase's resistance landscape should be mapped to conformational states:

- ABL1: T315I (gatekeeper), compound mutations (T315I/E255K, T315I/F317L) -- how do these affect conformational state preferences?
- BRAF: V600E itself stabilizes the active DFG-in conformation. Resistance via dimerization (splice variants) does not change the monomer conformation. What does state-aware design offer here?
- ALK: G1202R (solvent front), I1171N (hinge), compound mutations. Do these shift conformational equilibria toward DFG-out?
- JAK2: V617F is the activating mutation (paradoxically, this is the dominant mutation driving disease, not resistance). Resistance via JAK2 Y931C, L983F, or pathway switching.

Without this analysis, the multi-kinase extension lacks clinical grounding. It becomes a purely computational exercise in "does the method transfer to other targets?" rather than "does state-aware design address unmet clinical needs across multiple kinases?"

### 4. The 5-kinase MPNN selectivity panel is too narrow for clinical meaning

**Severity: Medium | Addressable: Partially**

The proposal acknowledges this in Open Question 4, but the core selectivity claim (DFG-out compounds are more selective) is tested on a 5-kinase panel. In clinical practice, kinase inhibitor toxicity is driven by off-target effects against dozens to hundreds of kinases. A molecule that appears "selective" across 5 kinases may be promiscuous across the broader kinome. The PKIS2/KCGS validation helps, but this is validation of the prediction, not of the design -- the generated molecules are scored only against 5 kinases during the design process.

From a clinical toxicity standpoint, the kinases that matter most for selectivity are often not the ones included in the panel. For EGFR inhibitors, the clinically relevant off-targets include: HER2 (diarrhea), VEGFR2 (hypertension), DDR1/DDR2 (hepatotoxicity), and wild-type EGFR itself (skin rash, which is actually a biomarker of efficacy). None of these would be captured by a panel of {EGFR, ABL1, BRAF, ALK, JAK2}.

### 5. The "case study to finding" framing is necessary but incompletely argued

**Severity: Medium-Low | Addressable: Yes**

The proposal frames the transformation as: EGFR alone = case study, 5 kinases = general finding. This is the right instinct, but N=5 kinases is still a small sample from the human kinome (~518 kinases). A clinical reviewer might argue: "You picked 5 kinases with the best structural data and the most approved drugs. Of course the method works on well-characterized targets. What about kinases with 10-20 PDB structures and a handful of ChEMBL compounds?"

The proposal should explicitly address this selection bias. The current kinase panel represents the best-case scenario for any structure-based method. The honest framing is: "We demonstrate generalization across the 5 kinases with the richest structural and bioactivity data, establishing a necessary (not sufficient) condition for kinome-wide applicability."

### 6. The JAK2 held-out drug list conflates indications

**Severity: Low-Medium | Addressable: Yes**

The proposal lists tofacitinib as a JAK2 held-out drug, but tofacitinib is primarily a JAK1/JAK3 inhibitor approved for rheumatoid arthritis, not a JAK2-selective agent approved for myeloproliferative neoplasms. Including it inflates the held-out drug count while weakening the clinical coherence. Similarly, baricitinib is a JAK1/JAK2 inhibitor approved for RA and COVID-19, not for MPN. Deuruxolitinib is for alopecia areata. The JAK2 "held-out drug" set mixes kinase-promiscuous autoimmune drugs with genuinely JAK2-targeted MPN drugs. This should be cleaned up: either restrict to JAK2-selective agents (ruxolitinib, fedratinib, pacritinib, momelotinib) or explicitly address the selectivity profiles.

---

## Feasibility Assessment

### Timeline: Realistic but tight

The 10-14 week estimate is credible for a single experienced researcher with existing StateBind infrastructure. However, Component A (data curation for 4 new kinases) is often underestimated. ChEMBL data cleaning, particularly for ABL1 (where imatinib analogs create massive analog series) and JAK2 (where selectivity annotations are inconsistent), can consume weeks of manual curation. The EGFR curation took substantial effort; replicating it 4 times is not just 4x the compute but potentially 4x the human judgment calls.

### Compute: Adequate

20 GPU-days on H200 is modest and well within Yale Bouchet capacity. The GNINA docking bottleneck (14 GPU-days for 5 kinases x 4 states x 4000 candidates) is the dominant cost but is embarrassingly parallel via SLURM arrays.

### Data availability: Strong for 3, marginal for 2

EGFR, ABL1, and BRAF have ample data. ALK pre-2010 (N~800) is borderline even with multi-task transfer. JAK2 structural coverage for DFG-out states is limited and would rely on AlphaFold2 models of uncertain quality. The proposal's fallback plan (3-kinase minimum viable version for JCIM) is prudent.

### Risk that enrichment does not generalize

This is the make-or-break scientific risk. The proposal correctly identifies it as high-risk/high-reward and provides honest mitigation (report heterogeneity). From a clinical perspective, I would note that non-generalization is also scientifically interesting: if state-aware design works for EGFR and ABL1 (which have the richest conformational data) but not for ALK and JAK2 (which rely on AF2 models), that tells us something important about the structural data requirements for the approach. The proposal should frame this outcome as a positive result, not a failure.

---

## Suggested Modifications

### Modification 1: Add a clinical unmet need matrix (Essential)

For each of the 5 kinases, provide a structured analysis:

| Kinase | Disease | Dominant resistance mechanism | Does resistance involve conformation? | State-aware design rationale |
|--------|---------|------------------------------|---------------------------------------|------------------------------|
| EGFR | NSCLC | C797S (covalent bond loss) | Yes -- DFG-out avoids Cys797 dependence | Strong |
| ABL1 | CML | T315I (gatekeeper) | Yes -- Type II (DFG-out) bypasses gatekeeper | Strong |
| BRAF | Melanoma | Dimerization, pathway reactivation | Weak -- resistance is pathway-level | Moderate (αC-out may matter) |
| ALK | NSCLC | G1202R, compound mutations | Moderate -- solvent front mutations | Moderate |
| JAK2 | MPN | Clonal evolution, pathway switching | Weak -- resistance is not pocket-level | Weak |

This matrix makes the clinical logic transparent. Reviewers can then evaluate whether the kinase panel is clinically motivated or merely convenient.

### Modification 2: Lead with the EGFR C797S story, follow with generalization (Essential)

The paper structure in the proposal leads with the multi-kinase atlas (Figure 1) and treats EGFR as one of five equal targets. From a clinical impact standpoint, the paper should lead with the EGFR C797S narrative -- the most urgent unmet need -- and then demonstrate that the same approach generalizes. Suggested restructure:

- Figure 1: EGFR conformational state landscape and the DFG-out clinical gap (all approved TKIs bind DFG-in; no DFG-out clinical candidate exists)
- Figure 2: EGFR enrichment results with C797S resistance mutation docking analysis
- Figure 3: Multi-kinase generalization (forest plot of 5 kinases)
- Figure 4: Selectivity analysis (DFG-out Gini advantage)
- Figure 5: Multi-task MPNN ablation study

This preserves the generalization claim while anchoring the paper in a patient-relevant narrative that clinical reviewers can engage with.

### Modification 3: Add C797S-specific docking analysis for EGFR (Strongly recommended)

The proposal's EGFR analysis should include docking of top state-aware candidates into EGFR-C797S mutant structures (PDB: 7ZYM, EGFR-T790M/C797S). Reporting which candidates retain predicted binding in the resistance context transforms the enrichment result from "we can rediscover known drugs" to "we can identify chemotypes that might overcome the dominant resistance mechanism." This is the highest-impact addition per unit of effort.

### Modification 4: Clean up the JAK2 held-out drug list (Required)

Remove or flag drugs with weak JAK2 selectivity (tofacitinib is JAK1/3-dominant; baricitinib is JAK1/2 non-selective with RA indication; deuruxolitinib targets JAK2 but for alopecia). Restrict to MPN-relevant JAK2-selective agents or explicitly annotate each drug's selectivity profile. This matters because a "retrospective validation" that tests whether the model ranks tofacitinib highly for JAK2 is testing something different from what it tests when it ranks ruxolitinib highly.

### Modification 5: Address the ALK pre-2010 anachronism (Recommended)

The pre-2010 ALK split is problematic because ALK medicinal chemistry barely existed before 2007. The proposal should either (a) drop ALK from the pre-2010 analysis, retaining it only for pre-2015, or (b) explicitly discuss why retrospective validation on a target that was not known during the "training period" is still meaningful (it could test whether multi-task transfer from EGFR/ABL1 enables prediction of a novel target with minimal direct training data -- this is actually a compelling claim if framed correctly).

### Modification 6: Report clinical toxicity correlates for selectivity results (Recommended)

If the DFG-out selectivity hypothesis is confirmed, link the selectivity improvement to specific clinical toxicities. For example: "DFG-out designed EGFR candidates showed reduced predicted ABL1 cross-reactivity, which is associated with cardiotoxicity (Kerkelä et al., Nat Med 2006)." This makes the selectivity result clinically tangible rather than an abstract statistical finding.

---

## Alternative Approaches

### Alternative A: Deep EGFR with clinical validation, then brief generalization

Instead of 5 kinases at equal depth, go deep on EGFR with:
1. C797S resistance mutation docking (as above)
2. CNS MPO scoring of all candidates (brain metastasis relevance)
3. Kinome selectivity prediction against a broader panel (20+ kinases from KinomeScan)
4. Then a brief "generalization" section showing 2-3 additional kinases

This puts clinical relevance first and statistical rigor second. It targets JCIM or JMC more naturally than Nature Computational Science, but might ultimately be more cited because it speaks directly to the EGFR clinical community.

### Alternative B: Clinically motivated kinase panel instead of structurally motivated

Replace JAK2 (weak clinical rationale for state-aware design) with a kinase that has a stronger conformational-state-linked clinical need:

- **MET**: MET amplification is the most common EGFR resistance mechanism (15-18%). MET has well-characterized active/inactive conformations. State-aware MET inhibitor design would be directly relevant to the EGFR resistance narrative and keep the paper focused on NSCLC.
- **RET**: RET fusions in NSCLC (1-2%) are treated by selpercatinib, a Type I inhibitor. RET has clear DFG-out structures. Adding RET would keep the paper in the thoracic oncology space.

This sacrifices some structural diversity for clinical coherence.

### Alternative C: Two-paper strategy

Paper 1 (JCIM, near-term): EGFR + ABL1 + BRAF state-aware generalization, with C797S analysis and selectivity validation. Targets the clinical-computational audience.

Paper 2 (NeurIPS/ICML, medium-term): Full kinome-wide multi-task MPNN with state conditioning as a general ML contribution. Targets the ML audience. Expands to 10-20 kinases using AF2-MSM atlas.

This avoids the tension between clinical depth and computational breadth by giving each audience its own paper.

---

## Impact on Publication Narrative

### The core tension

The proposal transforms StateBind from an "EGFR conformational drug design tool" into a "kinome-wide computational framework." This is undeniably a bigger computational contribution. However, the clinical narrative weakens in proportion to the breadth increase. A paper about EGFR C797S resistance and the DFG-out gap is immediately legible to clinicians and medicinal chemists. A paper about multi-kinase retrospective enrichment statistics is impressive to computational biologists but opaque to the clinical audience.

### Nature Computational Science considerations

Nature Computational Science is a computational journal, not a clinical one. From that venue's perspective, the multi-kinase generalization strengthens the paper substantially. The question is whether the clinical framing is needed at all for that venue, or whether it is decorative rather than structural. My recommendation: include the clinical framing as motivation (Introduction and Discussion) but do not let it drive the paper's main claims. The main claims should be computational: generalization, multi-task learning, state conditioning ablation.

### The enrichment narrative must survive the expansion

The headline result -- 10x enrichment -- is currently EGFR-specific. If the multi-kinase analysis shows heterogeneous results (e.g., EGFR 10x, ABL1 5x, BRAF 3x, ALK 1.5x, JAK2 1.2x), the headline becomes "3-10x enrichment depending on structural data richness." This is still positive but less punchy. The proposal should prepare for this narrative and frame it as informative rather than disappointing.

### Resistance to narrative diffusion

The strongest version of the StateBind story has a clear protagonist (EGFR), a clear villain (C797S resistance), a clear weapon (DFG-out state-conditioned generation), and a clear outcome (10x enrichment for novel conformational chemotypes). Adding 4 more kinases introduces subplots. If the paper is not carefully structured, the reader leaves confused about what the main finding is. The Modification 2 (EGFR-first structure) addresses this directly.

---

## References

1. Cho BC, et al. Amivantamab plus lazertinib in previously untreated EGFR-mutated advanced NSCLC (MARIPOSA). Ann Oncol. 2024;35(1):77-88.

2. Chmielecki J, et al. Analysis of acquired resistance mechanisms to osimertinib in patients with EGFR-mutated advanced NSCLC from the AURA3 trial. Nat Commun. 2023;14(1):1071.

3. Cortes JE, et al. Ponatinib efficacy and safety in Philadelphia chromosome-positive leukemia: final 5-year results of the phase 2 PACE trial. Blood. 2018;132(4):393-404.

4. Felip E, et al. Overall survival with amivantamab-lazertinib in EGFR-mutated advanced NSCLC. N Engl J Med. 2025;393(1):49-61.

5. Jia Y, et al. Overcoming EGFR(T790M) and EGFR(C797S) resistance with mutant-selective allosteric inhibitors. Nature. 2016;534(7605):129-132.

6. Kerkelä R, et al. Cardiotoxicity of the cancer therapeutic agent imatinib mesylate. Nat Med. 2006;12(8):908-916.

7. Leonetti A, et al. Resistance mechanisms to osimertinib in EGFR-mutated non-small cell lung cancer. Br J Cancer. 2019;121(9):725-737.

8. Planchard D, et al. Osimertinib with or without chemotherapy in EGFR-mutated advanced NSCLC: overall survival from FLAURA2. N Engl J Med. 2025;393(7):608-619.

9. Soda M, et al. Identification of the transforming EML4-ALK fusion gene in non-small-cell lung cancer. Nature. 2007;448:561-566.

10. Soria JC, et al. Osimertinib in untreated EGFR-mutated advanced non-small-cell lung cancer. N Engl J Med. 2018;378(2):113-125.

11. Ung PMU, et al. Conformational analysis of the DFG-out kinase motif and biochemical profiling of structurally validated Type II inhibitors. J Med Chem. 2015;58(4):1569-1585.

12. Chitnis SS, et al. Structure-Activity Relationships of Inactive-Conformation Binding EGFR Inhibitors: Linking the ATP and Allosteric Pockets. Arch Pharm (Weinheim). 2025;358:e70027.

13. Ramalingam SS, et al. Overall survival with osimertinib in untreated, EGFR-mutated advanced NSCLC. N Engl J Med. 2020;382(1):41-50.

14. Wells CI, et al. Progress towards a public chemogenomic set for protein kinases and a call for contributions. PLOS One. 2017;12(8):e0181585.

15. Davis MI, et al. Comprehensive analysis of kinase inhibitor selectivity. Nature Biotechnology. 2011;29(11):1046-1051.
