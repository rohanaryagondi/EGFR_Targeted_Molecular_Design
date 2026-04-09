---
agent: Senior Drug Hunter
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: clinonc-P01
---

# Critique: Conformational State-Conditioned Generation of DFGout EGFR Inhibitors for C797S Resistance

## Reviewing Agent

**Senior Drug Hunter (drughunt)** -- 25+ years pharmaceutical drug discovery, TPP design,
competitive landscape analysis, IND-enabling strategy. Cohort2, StateBind IdeationDept.

## Proposal Summary

The clinonc-P01 proposal recommends a four-phase computational experiment applying
StateBind's conformational state-conditioned VAE to generate novel molecular scaffolds
predicted to bind the EGFR-C797S DFG-out conformation. The study would: (1) predict
mutant EGFR structures in DFG-out states using AlphaFold2 with MSA subsampling, (2)
generate molecules conditioned on those mutant DFG-out pockets vs. multiple controls,
(3) screen candidates against a clinically derived Target Product Profile, and (4) analyze
chemical space differentiation from approved/clinical-stage EGFR TKIs. Target venues are
JCIM (primary) and JMC (secondary). The paper claim would be that state-conditioned
generative design identifies novel DFG-out chemotypes structurally distinct from all
clinical-stage EGFR inhibitors.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The strongest proposal I have seen from this cohort -- it picks the
right clinical problem and frames it honestly -- but it underestimates the competitive
headwinds from BDTX-1535's momentum, overestimates the credibility of AF2-predicted
DFG-out pockets for medicinal chemistry audiences, and leaves IP freedom-to-operate
as an afterthought rather than an explicit analysis.

---

## Strengths

### 1. Clinical Anchoring Is Genuinely Compelling (High Value)

The proposal correctly identifies C797S resistance as the single most important unmet need
in EGFR-targeted therapy. The supporting evidence is specific and quantitative: 7-29%
incidence after osimertinib, zero approved type II EGFR inhibitors, BDTX-1535 as the sole
promising DFG-in candidate at 42% ORR. This is not hand-waving -- these are real clinical
data points that any pharma BD team would recognize. The framing of "zero type II EGFR
inhibitors have ever been tested clinically" is a powerful, factually correct claim that
immediately establishes the gap.

### 2. Controlled Experimental Design (High Value)

The four-condition design (mutant DFG-out, wild-type DFG-out, mutant DFG-in, wild-type
DFG-in) is exactly how a drug program would structure a computational experiment. Conditions
B-D serve as meaningful controls, and the study is designed to produce interpretable results
regardless of outcome. This is rare in computational chemistry proposals, most of which are
designed to succeed and have no plan for negative results.

### 3. Honest Risk Assessment (High Value)

The proposal identifies five concrete risks and provides genuine mitigations, including
the willingness to fall back to homology modeling if AF2 fails on DFG-out prediction.
The statement that "even negative results (DFG-out molecules are too large for CNS) are
publishable if characterized rigorously" reflects scientific maturity. The acknowledgment
that JMC reviewers will "near certainly" demand experimental validation is realistic.

### 4. Compute Feasibility Is Solid

The 185 GPU-hour estimate is well within Bouchet cluster capacity. The 6-8 week timeline
is aggressive but achievable for a single computational scientist. No external
collaborators or proprietary data required. This is genuinely executable.

### 5. TPP Is Better Than Most Computational Papers Attempt

The TPP table (Phase 3) is more detailed than what 95% of computational chemistry papers
include. The tiered CNS MPO approach (Tier 1 >= 4.0, Tier 2 >= 3.0) shows awareness of the
brain metastases relevance and the MW-BBB tradeoff for type II inhibitors. The hERG filter
calibrated against ES-072's QT failure is a nice translational touch.

---

## Weaknesses (with Severity and Addressable?)

### 1. The BDTX-1535 Competitive Threat Is Understated (Severity: HIGH, Addressable: YES)

The proposal treats BDTX-1535 as a comparator data point. It should treat it as an
existential framing risk.

BDTX-1535 achieved 42% ORR (8/19 patients) in osimertinib-resistant patients with C797S
or PACC mutations, including 5 confirmed PRs, 1 unconfirmed CR at 8 months, and a DCR of
approximately 90.9%. Black Diamond reported a favorable tolerability profile at 200mg QD
with rash (70%) and diarrhea (35%) as the primary on-target AEs. Phase 2 frontline cohort
data were expected Q1 2025, and regulatory feedback on registration path was anticipated
in the same timeframe.

**The problem for this proposal:** If BDTX-1535 continues performing at this level, it will
become the de facto fourth-generation EGFR TKI -- and it is a DFG-in covalent inhibitor.
A paper arguing for DFG-out EGFR design will face the reviewer question: "Why pursue the
harder conformational state when a DFG-in solution is working clinically?" The proposal
mentions BDTX-1535 but does not explicitly rebut this objection.

**How to fix:** Add a dedicated subsection in Background and Evidence titled "Why DFG-out
Despite BDTX-1535?" addressing: (a) BDTX-1535's covalent mechanism still depends on a
reactive residue near the binding site -- what happens when the next resistance mutation
emerges? (b) Historical precedent: imatinib (DFG-out) was initially competing against
interferon-alpha (a working treatment), yet its conformational selectivity provided
durable responses and became the gold standard. (c) The DFG-out mechanism offers
fundamentally longer residence times (10-100x for type II vs type I, per Copeland et al.
2006), which should translate to different resistance evolution kinetics. (d) Even if
BDTX-1535 succeeds, resistance to fourth-generation TKIs will emerge -- DFG-out targeting
is the mechanistic hedge. Frame this not as "BDTX-1535 is bad" but as "conformational
diversity in the therapeutic armamentarium is a hedge against resistance evolution."

### 2. AF2-Predicted DFG-out Structures Lack Credibility for Medicinal Chemistry (Severity: HIGH, Addressable: PARTIALLY)

The proposal correctly notes that AF2 DFG-out predictions will have lower pLDDT (~75%
vs >85% for DFG-in). What it does not adequately address is that pharma medicinal
chemists -- the target audience for JCIM/JMC -- have deep skepticism about AF2 structures
for drug design, and this skepticism is evidence-based.

Recent evaluations (Karelina et al., Science 2023; JCIM 2022 multiple studies; bioRxiv
2026) consistently show that AF2-predicted structures exhibit limitations in binding pocket
local geometry that degrade docking performance. For DFG-out predictions specifically,
the challenge is compounded: AF2 was trained predominantly on DFG-in kinase structures
(87% of KLIFS entries are DFG-in), creating systematic training set bias against the exact
conformation this proposal needs.

The proposal's mitigation -- falling back to homology modeling -- is honest but incomplete.
Homology modeling using PDB 5ZWJ (which required a stabilizing V948R mutation for
crystallization) introduces its own artifacts. PDB 4I21 is a better template but is
wild-type, not C797S.

**How to fix:** (a) Add an explicit validation tier: dock known type II kinase inhibitors
(imatinib, ponatinib, sorafenib) into AF2-predicted DFG-out pockets of their cognate
targets (ABL, RAF) where experimental DFG-out structures exist, to calibrate the expected
pocket RMSD and docking score degradation. This cross-target validation is cheap
computationally and provides a credibility anchor. (b) Include molecular dynamics
refinement (even short 10-50ns runs) of AF2-predicted DFG-out structures to relax steric
clashes in the binding pocket. AlphaFold2-RAVE (Herron et al., 2024) already provides
a protocol. (c) Be explicit about what AF2 pocket errors mean for the generated molecules:
if the pocket is wrong by 1.5 Angstroms, the SELFIES VAE conditioning is less meaningful,
and the paper should quantify this sensitivity.

### 3. The TPP Screen Is Necessary But Not Sufficient for Industry Credibility (Severity: MODERATE, Addressable: YES)

The TPP table is good for an academic paper, but it would not pass scrutiny at a pharma
drug program review. Several critical gaps:

**Missing from the TPP:**
- **Metabolic stability**: No CYP inhibition or microsomal clearance prediction. This is
  table-stakes for any kinase inhibitor TPP. The ADMET model (hERG AUROC = 0.77) does not
  cover this.
- **Plasma protein binding**: Highly lipophilic type II inhibitors often have >99% PPB,
  which kills free fraction and effective concentration. No mention.
- **Kinome-wide selectivity**: The TPP includes WT-EGFR selectivity (>30-fold) but says
  nothing about off-target kinase activity. A DFG-out inhibitor that is selective for EGFR
  over WT-EGFR but hits 50 other kinases is a non-starter. The proposal should at minimum
  mention predicted selectivity against ABL, SRC, and MET (all of which have accessible
  DFG-out conformations).
- **Phospholipidosis risk**: Type II inhibitors with cationic amphiphilic character have
  elevated phospholipidosis risk, which is a regulatory flag. Not mentioned.
- **Efflux ratio**: Beyond P-gp substrate classification, the quantitative efflux ratio
  (Caco-2 B-A/A-B) is the standard BBB penetration metric. CNS MPO is a useful filter but
  not a substitute for efflux prediction.

**How to fix:** Add a paragraph acknowledging these limitations explicitly: "The TPP
presented here covers physicochemical and primary target criteria but does not address
metabolic stability, kinome selectivity, or transporter-mediated clearance, which would
require additional predictive models beyond StateBind's current ADMET capabilities. These
gaps are reported as a limitation and a direction for future pipeline development." This
turns a weakness into a research gap identification.

### 4. IP Freedom-to-Operate Is Mentioned but Not Analyzed (Severity: MODERATE, Addressable: YES)

The proposal references the DFG-out IP landscape as "relatively open" but provides no
specific patent analysis. A recent comprehensive patent review of fourth-generation EGFR
TKIs covering 2017-2024 (Expert Opinion on Therapeutic Patents, 2025) maps the active
patent families. The proposal should engage with this literature.

The assertion that DFG-out EGFR scaffolds have limited patent coverage is probably correct
(my own R01 research supports this), but it is stated as a claim without evidence. For a
paper targeting JCIM/JMC, this may not matter (patent analysis is not expected). For the
translational narrative the proposal emphasizes -- making this attractive to pharma BD
teams -- it matters significantly.

**How to fix:** Either (a) remove the IP claims entirely from the paper scope (they are
unnecessary for a methods paper at JCIM) or (b) include a brief structural IP analysis
comparing the Murcko scaffolds of generated DFG-out molecules against patent-protected
scaffolds in the EGFR inhibitor patent database. Option (a) is cleaner; option (b) would
be a differentiating contribution but adds scope.

### 5. The Gap Between Computational Hits and Clinical Candidates Is Acknowledged but Not Quantified (Severity: MODERATE, Addressable: YES)

The proposal states this is "NOT a drug discovery claim" and says "experimental validation
is required." This is honest, but the proposal should quantify the gap it is leaving open.

In the AI drug discovery field, the benchmark is Insilico Medicine's ISM001-055
(rentosertib): 30 months from target identification to IND filing, approximately $2.6M in
total cost. Relay Therapeutics invested $1.2B+ over 7 years to go from the Dynamo platform
to Phase 3 with zovegalisib. These numbers frame what happens AFTER a computational paper.

The proposal would benefit from an explicit "Distance to IND" section in the discussion:
"The candidates generated by this computational study represent starting points that
would require: (1) synthetic feasibility assessment (~3 months), (2) in vitro biochemical
validation of top 5-10 scaffolds (~6 months), (3) selectivity profiling (~3 months), (4)
in vivo PK and tolerability (~6 months), before any clinical development decision. The
estimated distance from computational hit to IND is 3-5 years and $10-50M, depending on
the scaffold optimization trajectory. This paper demonstrates the methodology, not the
endpoint."

This kind of calibrated honesty is what differentiates a credible computational paper from
a "we discovered drugs with AI" press release. It would also preempt reviewer criticism.

### 6. Venue Targeting Could Be More Ambitious with the Right Modifications (Severity: LOW, Addressable: YES)

The proposal targets JCIM (primary) / JMC (secondary). This is reasonable but potentially
underambitious. My R01 research identified that Nature Computational Science is actively
soliciting generative molecular design papers (editorial, 2025). The key barriers to
Nature Comp Sci are: (a) single-target scope (EGFR only) and (b) small N in retrospective
validation (3-5 drugs).

If the proposal were combined with extension to 1-2 additional kinases (ABL with
imatinib/ponatinib as DFG-out references, ALK with crizotinib/lorlatinib), the clinical
anchoring of the EGFR C797S case study PLUS a generalizability demonstration could
plausibly target Nature Computational Science. The EGFR C797S case becomes the
translational highlight of a broader methodology paper.

**Recommendation:** Keep JCIM as the primary target for the current scope. Add a section
discussing how the clinical case study component could be integrated into a broader
multi-kinase methodology paper for a higher-impact venue.

---

## Feasibility Assessment

**Overall: Feasible with caveats.**

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Compute** | HIGH feasibility | 185 GPU-hours is well within Bouchet capacity |
| **Timeline** | MODERATE feasibility | 6-8 weeks for a single person is tight but achievable if AF2 cooperates |
| **Data availability** | HIGH feasibility | All PDB structures, ChEMBL data, sequences are public |
| **Software** | MODERATE feasibility | AF2 + AFsample2 installation and MSA generation adds setup time |
| **Scientific risk** | MODERATE | AF2 DFG-out prediction is the critical path risk |
| **Publication risk** | LOW-MODERATE | JCIM is achievable with the controlled design; JMC requires more docking |

**Critical path item:** Phase 1 (AF2 DFG-out prediction). If AF2 with MSA subsampling
produces zero credible DFG-out conformations for any C797S mutant, the study falls back to
homology modeling, which weakens the novelty claim substantially. I would recommend running
a pilot AF2 prediction for one mutant (L858R/C797S, 40 models) before committing to the
full study. This takes approximately 3 GPU-hours and de-risks the entire project.

---

## Suggested Modifications

### Priority 1 (Essential for publication)

1. **Add the "Why DFG-out despite BDTX-1535?" argument.** This is the first question any
   informed reviewer will ask. Frame it around conformational diversity as a resistance hedge.

2. **Add cross-target AF2 validation.** Dock known type II inhibitors into AF2-predicted
   DFG-out pockets of ABL and RAF before using AF2 pockets for EGFR generation. This
   provides a credibility calibration that costs almost nothing computationally.

3. **Acknowledge TPP limitations explicitly.** List the missing dimensions (metabolic
   stability, kinome selectivity, PPB, efflux) as stated limitations and future work.

4. **Run a pilot AF2 prediction first.** 40 models of L858R/C797S with MSA subsampling,
   3 GPU-hours, answers the feasibility question before full commitment.

### Priority 2 (Strengthens the paper significantly)

5. **Add short MD refinement** of the top AF2-predicted DFG-out structures (10-50ns per
   structure) to relax binding pocket artifacts. This adds ~20 GPU-hours but substantially
   increases pocket credibility.

6. **Include a "Distance to IND" discussion section.** Quantify what remains between a
   computational hit and a clinical candidate. This is unusual in academic papers and would
   be noticed positively by pharma readers.

7. **Add kinome selectivity prediction** for top DFG-out candidates against at least ABL,
   SRC, MET, and WT-EGFR. Even a simple docking-based selectivity estimate across DFG-out
   structures of these kinases would be valuable.

### Priority 3 (Nice to have)

8. **Pre-register the computational experiment on OSF.** The proposal mentions this as
   an open question. I strongly support it. Pre-registration with defined success criteria
   signals methodological seriousness and is increasingly valued at top venues.

9. **Include Tanimoto similarity matrix** between generated DFG-out scaffolds and all
   clinical-stage EGFR TKI scaffolds. Provides a quantitative chemical novelty claim.

10. **Consider ESMFold as a speed comparison.** Not essential, but if ESMFold produces
    reasonable DFG-out structures in 10 seconds vs 5 minutes for AF2, that is a practical
    finding for the field.

---

## Alternative Approaches

### Alternative 1: Skip AF2, Use Experimental DFG-out Structures Only

Rather than predicting mutant DFG-out structures, use the existing experimental DFG-out
structures (PDB 5ZWJ for T790M/C797S, PDB 4I21 for wild-type inactive) directly. This
eliminates the AF2 risk entirely and still demonstrates state-conditioned generation for
the clinical scenario. The downside: reduced novelty (no AF2 component) and inability
to model all four mutant genotypes. The upside: faster execution, higher confidence in
pocket quality, and the controlled experimental design still produces a publishable result.

**My assessment:** This is the fallback I would use if the AF2 pilot (suggested above)
produces discouraging results. The paper loses the AF2 angle but keeps the clinical
anchoring and state-conditioned generation novelty.

### Alternative 2: Comparative Generative Model Benchmarking + EGFR Case Study

Combine the EGFR C797S case study with a head-to-head benchmark of StateBind's SELFIES
VAE against REINVENT 4 and DiffSBDD on the same DFG-out generation task. This addresses
the reviewer expectation (noted in my R01 research) that any 2026 generative design paper
must compare against contemporary baselines. The EGFR case study provides the clinical
hook; the benchmark provides the methodology contribution.

**My assessment:** Significantly more work (requires running REINVENT 4 and DiffSBDD,
each of which has nontrivial installation and configuration), but produces a stronger
paper suitable for Nature Computational Science. This is the path to a higher-impact
venue but at the cost of 2-3 additional months.

### Alternative 3: Focus on the Bivalent ATP+Allosteric Design Space

Instead of pure DFG-out targeting, explore bivalent inhibitors that bridge the ATP and
allosteric pockets (following Engel et al., 2024, who achieved ~60 pM against the triple
mutant). StateBind's state conditioning could be reframed as conditioning on the
DFGout_aCout state, which provides the largest pocket (~1913 A^2), enabling generation
of bivalent-compatible molecules. This is pharmacologically closer to current research
trends but faces the molecular weight challenge (>700 Da for bivalent compounds).

**My assessment:** Interesting but niche. The MW problem is severe for oral bioavailability.
Better as a secondary analysis within the current proposal than as the primary focus.

---

## Impact on Publication Narrative

### What This Proposal Does Right for the StateBind Story

The EGFR C797S angle transforms StateBind from "we have a computational method that works
retrospectively" to "we applied our method to the most urgent clinical problem in EGFR
therapy." This is the difference between a methodology paper that gets cited for its method
and a methodology paper that gets cited because clinical researchers find it relevant.

The connection to Relay Therapeutics (cited in the proposal and elaborated in my R01) is
strategically important. Relay's Dynamo platform provides clinical proof-of-concept that
conformational state-aware drug design works. StateBind provides an open-source, ML-based
alternative. Positioning StateBind as "Relay for the rest of us" -- accessible,
reproducible, not behind a $1.2B proprietary wall -- is a narrative that resonates with
both academic and pharma audiences.

### What Needs Strengthening for Pharma BD Appeal

A pharma business development team evaluating this paper would ask three questions:

1. **"Can we make these molecules?"** The SA score filter (<5.0) is a start, but pharma
   wants retrosynthetic analysis. Can the top scaffolds be synthesized in 5-8 steps?
   Even a brief ASKCOS or RetroTFM analysis of the top 5 candidates would add enormous
   credibility.

2. **"Do these molecules hit anything else?"** Kinome selectivity is the second question.
   The proposal addresses WT-EGFR selectivity but not broader kinome selectivity. A type II
   inhibitor that is "selective for DFG-out EGFR" but hits 40 other kinases in DFG-out is
   a polypharmacology story, not a selective drug story.

3. **"What is the IP position?"** As noted above, the freedom-to-operate question. Pharma
   will not invest in scaffolds that are already covered by competitor patents. Even a
   cursory Tanimoto distance analysis from patented EGFR inhibitor cores would address this.

### Venue Assessment

JCIM is the right primary target. The controlled experimental design, clinical anchoring,
and honest failure mode analysis fit JCIM's methodology focus. JMC is a stretch without
experimental binding data but not impossible if the docking validation (Phase 4) is strong.

Nature Computational Science remains aspirational for this specific proposal as scoped, but
if combined with multi-kinase extension and generative model benchmarking (see Alternative
2), it becomes realistic.

---

## References

1. Black Diamond Therapeutics. (2024). Phase 2 data: BDTX-1535 in recurrent EGFRm NSCLC.
   Press release, November 2024. NCT05256290. ORR 42% (8/19), DCR ~90.9%.

2. Copeland RA, Pompliano DL, Meek TD. (2006). Drug-target residence time and its
   implications for lead optimization. Nat Rev Drug Discov. 5(9):730-739.

3. Engel J, et al. (2024). Linking ATP and allosteric sites to achieve superadditive
   binding with bivalent EGFR kinase inhibitors. Commun Chem. 7:108. ~60 pM triple mutant.

4. Expert Opinion on Therapeutic Patents. (2025). Overcoming triple mutant EGFR-tyrosine
   kinase barriers in the therapeutics of NSCLC: a patent review on fourth-generation
   inhibitors (2017-2024). Vol 35, No 9.

5. Fourth-generation EGFR-TKI to overcome C797S mutation: past, present, and future.
   (2025). J Enzyme Inhib Med Chem. PMC12172088.

6. Herron L, Mondal TK, Bhatt D. (2024). Exploring kinase DFG loop conformational
   stability with AlphaFold2-RAVE. J Chem Inf Model. 64(7):2789-2797.

7. JCIM Author Guidelines. (2026). Updated March 11, 2026. "JCIM will not consider
   straightforward applications of molecular docking methods to a single target system
   without adequate experimental validation."

8. JMC Author Guidelines. (2026). Updated February 19, 2026. Computational studies must
   "lead to experimental studies" or demonstrate "substantially novel computational
   chemistry methods."

9. Karelina M, et al. (2023). AlphaFold2 structures guide prospective ligand discovery.
   Science. doi:10.1126/science.adn6354.

10. Kooistra AJ, et al. (2021). KLIFS: an overhaul after the first 5 years. Nucleic Acids
    Res. 49(D1):D562-D569. 87% of kinase structures are DFGin.

11. Loeffler HH, et al. (2024). REINVENT 4: Modern AI-driven generative molecule design.
    J Cheminformatics. 16:20.

12. Naykwadi S, et al. (2026). Overcoming Resistance in EGFR-Mutant Cancers: A
    Comprehensive Review of Inhibitor Evolution and SAR-Based Design. Drug Dev Res.
    doi:10.1002/ddr.70220.

13. Relay Therapeutics. (2025). Updated data for RLY-2608 + Fulvestrant. ASCO 2025.
    mPFS 11.0 months in 2L PI3Ka-mutated breast cancer.

14. Schneuing A, et al. (2024). Structure-based drug design with equivariant diffusion
    models (DiffSBDD). Nature Computational Science. 4(12):737.

15. Su Y, et al. (2024). Fourth-generation EGFR-TKIs: hope and challenges. Transl Cancer
    Res. PMC11384918.

16. Wayment-Steele HK, et al. (2024). High-throughput prediction of protein conformational
    distributions with subsampled AlphaFold2. Nat Commun. 15:2464.

17. bioRxiv. (2026). Assessment of AlphaFold protein models for small-molecule ligand
    docking. doi:10.64898/2026.01.04.697577v1. Binding pocket local geometry limitations.
