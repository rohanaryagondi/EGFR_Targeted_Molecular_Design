---
agent: Maverick Synth-Bio / DMPK Specialist
round: 1
date: 2026-04-08
type: research-note
topic: End-to-End Drug Design Pipeline Assessment -- Retrosynthesis, ADMET Integration, PK Prediction, and Synthesis Feasibility for StateBind
---

# Research Note: From Scored Molecules to Drug Candidates -- Closing StateBind's Translational Gap

## Summary

StateBind generates, scores, and ranks conformational-state-aware EGFR-targeted molecules,
achieving a compelling 10x retrospective enrichment over static design. But the pipeline
stops at scoring. It never asks: Can these molecules be synthesized? Will they survive
the ADMET gauntlet? What dose would a patient need? This research note surveys the
2024-2026 state of the art in retrosynthetic planning tools, ADMET prediction
benchmarks, in silico PK projection, and end-to-end AI drug design pipelines. The goal
is to identify specific, evidence-based integration points that would transform
StateBind from a computational proof-of-concept into a translatable drug design
platform -- and a far more publishable one.

**Key conclusions from this survey:**

1. StateBind's ADMET model (hERG AUROC=0.7745, CYP3A4 AUROC=0.7323) is significantly
   below TDC leaderboard SOTA (hERG: 0.880, CYP3A4 AUPRC: 0.916). However, the model
   is used informationally, not for scoring, so this gap is an opportunity, not a crisis.

2. AiZynthFinder 4.0 solves routes for 71-86% of drug-like molecules, with median
   search times of 40-90 seconds. RAscore provides a 4500x faster proxy that could
   serve as a scoring-tier equivalent to the MPNN/GNINA docking cascade.

3. Approved EGFR inhibitors have hERG IC50 values of 0.57-5.3 uM -- far below the
   standard 10 uM "safe" threshold. StateBind's ADMET model correctly flags these as
   hERG liabilities, which is a class-specific reality, not a model failure. Kinase-
   calibrated thresholds would fix the false-rejection problem.

4. End-to-end pipelines (Chemistry42, ADMETrix, PMMG, SynFormer) demonstrate that
   generation-ADMET-retrosynthesis integration is now standard practice in the field.
   StateBind's post-hoc-only approach is increasingly out of step.

5. A "synthesis-aware scoring" extension would be the highest-impact addition for
   publication -- no other conformational-state-aware pipeline has demonstrated
   retrosynthetic feasibility of its generated candidates.

---

## Research Questions

1. What are the current benchmarks for retrosynthetic planning tools (AiZynthFinder,
   ASKCOS, Syntheseus, RetroScore), and what success rates do they achieve on drug-like
   and AI-generated molecules?

2. How does StateBind's ADMET model compare to TDC leaderboard SOTA across key
   endpoints (hERG, CYP3A4, Caco-2, clearance, solubility)?

3. What ADMET profiles do approved EGFR kinase inhibitors actually have, and how should
   kinase-class-calibrated thresholds be defined?

4. Which published pipelines integrate ADMET into the scoring/optimization loop (not
   just post-hoc filtering), and what weighting schemes do they use?

5. What is the current state of in silico PK prediction (oral bioavailability, half-life,
   clearance), and can we project human doses from computational data alone?

6. How large is the commercially synthesizable chemical space (Enamine REAL, Mcule),
   and what fraction of AI-generated molecules have feasible synthesis routes?

7. What would a minimally viable "end-to-end" extension look like for StateBind,
   balancing publication impact against implementation effort?

---

## Methods

### Sources Consulted

- TDC (Therapeutics Data Commons) ADMET Benchmark leaderboards (tdcommons.ai)
- PubMed / PMC for pharmacology and DMPK literature
- arXiv / ChemRxiv / bioRxiv for preprints on retrosynthesis and ADMET
- GitHub repositories for AiZynthFinder, Syntheseus, REINVENT4, RetroScore, PKSmart
- Enamine website for REAL Space library statistics
- FDA NDA review documents for EGFR-TKI cardiac safety data
- Journal of Cheminformatics, JCIM, Journal of Medicinal Chemistry, PNAS, Nature
  Communications Chemistry, Advanced Science, Nucleic Acids Research

### Search Strategy

Conducted 18 targeted web searches and 6 page-level data extractions covering:
- Retrosynthetic planning benchmarks (AiZynthFinder 4.0, ASKCOS, Syntheseus, RetroScore)
- TDC ADMET leaderboard data (hERG, CYP3A4_Veith, all 22 endpoints)
- EGFR-TKI pharmacokinetic profiles and hERG IC50 values
- ADMET-aware molecular generation (ADMETrix, REINVENT4, PMMG)
- In silico PK prediction tools (PKSmart, Deep-PK, ADMETlab 3.0, pkCSM)
- End-to-end AI drug design pipelines (Chemistry42, SynFormer)
- Synthesizability scoring beyond SA score (RAscore, SCScore, SYBA, FSscore, RetroScore)
- Reproducibility assessment of TDC leaderboards

---

## Findings

### Finding 1: AiZynthFinder 4.0 -- The Reference Standard for Open-Source Retrosynthetic Planning

AiZynthFinder 4.0, released May 2024 by AstraZeneca's Molecular AI division, represents
the most mature open-source retrosynthetic planning tool available (Genheden et al.,
2020; Thakkar et al., 2024). It uses Monte Carlo Tree Search (MCTS) with neural
network expansion policies trained on USPTO reaction templates.

**Key benchmark data from the AiZynthFinder 4.0 paper (Thakkar et al., 2024):**

| Dataset | Solve Rate | Avg Steps | Avg Starting Materials | Median Time |
|---------|-----------|-----------|----------------------|-------------|
| AZ internal designs | 80.3% | 4.40 | 4.31 | ~40-90 s |
| REINVENT-generated | 85.6% | 6.04 | 5.07 | ~90 s |
| ChEMBL drug-like | 71.0% | 1.97 | 2.67 | ~40 s |
| GDB MedChem | 10.1% | 2.98 | 2.93 | -- |

The ChEMBL solve rate of 71% is the most relevant benchmark for StateBind: these are
real drug-like molecules from the bioactivity database. The low GDB solve rate (10.1%)
reflects that highly novel structures outside known chemical space have poor coverage.

**Stock coverage matters enormously:** With E-Molecules building block stock, 80% of
starting materials are available; with ZINC stock, only 60%. The choice of building
block database directly determines retrosynthetic success.

**New in v4.0:** Support for any one-step retrosynthesis model (not just template-based),
a scoring framework for route quality assessment, multiple search algorithms beyond
MCTS, filter reaction policies, and ONNX conversion yielding 1.7x faster search times
and 2.4x faster startup compared to TensorFlow.

Between 12,000-25,000 USPTO templates are deployed for ChEMBL molecules; AstraZeneca's
internal model uses approximately 180,000 templates from Reaxys for higher coverage.

**Relevance to StateBind:** AiZynthFinder is the natural choice for retrosynthetic
validation of StateBind's top candidates. At 40-90 seconds per molecule, processing
the top 50-100 candidates is feasible (~1-2 hours). The 71% ChEMBL solve rate provides
a baseline expectation -- if StateBind's VAE-generated molecules achieve a comparable
solve rate, that validates chemical realism. A significantly lower rate would flag
issues with the generation process.

---

### Finding 2: RAscore -- A 4500x Faster Proxy for Retrosynthetic Feasibility

Full retrosynthetic planning (40-90 seconds per molecule) is too slow for scoring
461 candidates x 4 states. RAscore (Thakkar et al., 2021) provides a critical
shortcut: a machine learning classifier trained on 200,000 AiZynthFinder results
from ChEMBL that predicts whether a route can be found, computing at least 4500x
faster than the underlying CASP tool.

**RAscore characteristics:**
- Binary classification: 1 (route findable) vs 0 (no route)
- Trained on ChEMBL chemical space
- AUC and accuracy both above 0.81 (benchmarked against SAscore, SCScore, SYBA)
- Milliseconds per molecule -- suitable for scoring all candidates

**Critical benchmark comparison (Skoraczynski et al., 2023):**

| Score | AUC | Accuracy | Correlation with Route Complexity |
|-------|-----|----------|----------------------------------|
| RAscore | >0.81 | >0.81 | Significant (p < 0.04) |
| SAscore | >0.81 | >0.81 | Significant (p < 0.04) |
| SCScore | ~0.61 | ~0.61 | Significant (p < 0.04) |
| SYBA | ~0.61 | ~0.61 | Not significant |

RAscore and SAscore are the top performers, but RAscore has a conceptual advantage:
it directly models retrosynthetic planning outcomes, while SAscore uses heuristic
fragment-complexity rules.

**Key limitation:** SA score "fails to differentiate between feasible and infeasible
routes" -- average SA scores were 2.68 vs 2.73 for molecules with vs without feasible
routes (Gao et al., 2024). This directly undermines StateBind's current drug-likeness
component, which uses SA score with 25% weight within drug-likeness (itself 30% of
total), making SA score effectively 7.5% of the total score.

**Integration proposal for StateBind:** RAscore could serve as a Tier 1 proxy for
retrosynthetic feasibility (analogous to how MPNN serves as Tier 1 for docking), with
full AiZynthFinder analysis as Tier 0 for top candidates. This mirrors the existing
docking cascade architecture.

---

### Finding 3: RetroScore -- Route-Quality-Aware Synthesizability Scoring

RetroScore (2025) goes beyond binary "route found / not found" to assess route quality
using graph edit distance as a proxy for synthetic efficiency.

**RetroScore key features:**
- Integrates Graph2Edits (semi-template model) with Retro* (multi-step planning)
- Scores balance reliability (confidence score), synthetic efficiency (route length),
  and economic feasibility (graph edit distance)
- 97.37% planning success rate on its benchmark
- Outperformed 6 of 7 established SA metrics on molecular generation tasks
- Web server publicly accessible, source code on GitHub

**Why this matters for StateBind:** RetroScore provides not just "can it be made" but
"how efficiently can it be made" -- a continuous score suitable for integration into a
weighted scoring function. This is exactly what StateBind's architecture was designed
to accommodate: a new scoring component with a tunable weight.

---

### Finding 4: Synthesizability of AI-Generated Molecules -- Sobering Reality

A critical 2024 evaluation (Gao et al., arXiv:2411.08306) tested synthesis feasibility
of molecules from seven structure-based drug design models using a rigorous "round-trip"
metric (retrosynthesis followed by forward synthesis verification):

| Model | Top-5 Round-Trip Success Rate |
|-------|------------------------------|
| Pocket2Mol | 22.1% |
| FLAG | 15.2% |
| AR | 9.0% |
| DrugGPS | 8.4% |
| DecompDiff | 4.1% |
| TargetDiff | 3.4% |
| LiGAN | 2.9% |

These are devastating numbers. The best 3D structure-based generator (Pocket2Mol)
achieves only 22% true synthetic feasibility. The search success rate alone (without
round-trip verification) achieved 62.1% precision, meaning nearly 40% of "routes found"
would not actually work.

**Relevance to StateBind:** StateBind uses a SELFIES VAE (1D generation), which
generates molecules with guaranteed chemical validity (99.9%) but unknown synthetic
feasibility. The 1D SMILES/SELFIES approach likely produces more drug-like (and thus
more synthesizable) molecules than 3D pocket-based generators, but this has not been
verified. Demonstrating that StateBind's top candidates have significantly higher
synthesis feasibility than 3D generative models would be a strong publication point.

---

### Finding 5: SynFormer -- Generation with Built-In Synthesizability

SynFormer (PNAS, 2025) represents a paradigm shift: instead of generating molecules
and then checking synthesis, it generates synthetic pathways directly, ensuring every
molecule has a viable route by construction.

**Key features:**
- Scalable transformer architecture with a diffusion module for building block selection
- Two variants: SynFormer-ED (encoder-decoder for reconstruction) and SynFormer-D
  (decoder-only for generation)
- Building blocks selected from commercially available libraries
- Surpasses existing models in synthesizable molecular design benchmarks
- Highest sample efficiency even when constrained to single reaction types

**Publication implication:** SynFormer demonstrates that the field is moving toward
"synthesizable by design" rather than "generate then filter." StateBind's approach of
post-hoc SA score assessment is increasingly dated. Even adding retrosynthetic validation
post-hoc (as proposed here) is becoming the minimum bar.

---

### Finding 6: StateBind's ADMET Model vs TDC Leaderboard SOTA

The TDC ADMET benchmark provides standardized leaderboards across 22 endpoints with
scaffold-based splits. StateBind's multi-task ADMET model (GIN backbone, 187K params,
27,698 training molecules) can be directly benchmarked.

**hERG Leaderboard (Binary Classification, AUROC, 648 compounds):**

| Rank | Model | AUROC |
|------|-------|-------|
| 1 | MapLight + GNN | 0.880 +/- 0.002 |
| 2 | CFA | 0.875 +/- 0.014 |
| 3 | SimGCN | 0.874 +/- 0.014 |
| 4 | MapLight | 0.871 +/- 0.004 |
| 5 | ZairaChem | 0.856 +/- 0.009 |
| 6 | MiniMol | 0.846 +/- 0.016 |
| 7 | RDKit2D + MLP | 0.841 +/- 0.020 |
| 8 | Chemprop-RDKit | 0.840 +/- 0.007 |
| 9 | ADMETrix | 0.836 +/- 0.025 |
| 10 | AttentiveFP | 0.825 +/- 0.007 |
| -- | **StateBind ADMET** | **0.7745** |

StateBind's hERG model (AUROC=0.7745) would rank below the top 10 on TDC. The gap to
SOTA (MapLight + GNN: 0.880) is approximately 0.11 AUROC points -- significant but not
catastrophic for a multi-task model with a GIN backbone and only 187K parameters.

**CYP3A4_Veith Leaderboard (Binary Classification, AUPRC, 12,328 compounds):**

| Rank | Model | AUPRC |
|------|-------|-------|
| 1 | MapLight + GNN | 0.916 +/- 0.000 |
| 2 | ContextPred | 0.904 +/- 0.002 |
| 3 | AttrMasking | 0.902 +/- 0.002 |
| 4 | ADMETrix | 0.884 +/- 0.001 |
| 5 | MapLight | 0.881 +/- 0.001 |
| -- | **StateBind ADMET** | **0.7323** (AUROC, not AUPRC) |

Note: StateBind reports CYP3A4 AUROC (0.7323), while TDC uses AUPRC. These metrics are
not directly comparable -- AUPRC is typically lower than AUROC on imbalanced datasets.
A proper comparison requires re-evaluating StateBind's model on TDC's exact splits with
AUPRC. However, the gap is likely substantial.

**Reproducibility caveat (Critical Assessment, bioRxiv Feb 2026):** Only 3 of the top
TDC methods passed full reproducibility checks (CaliciBoost, MapLight, MapLight+GNN).
Data leakages were identified in MiniMol, GradientBoost, and XGBoost. This means the
"true" SOTA is likely narrower than the leaderboard suggests, and StateBind's gap may
be smaller than it appears.

**All 22 TDC ADMET endpoints:**

| Category | Endpoints | Metric |
|----------|-----------|--------|
| Absorption (6) | Caco2_Wang (906), HIA_Hou (578), Pgp (1212), Bioavailability (640), Lipophilicity (4200), Solubility (9982) | MAE/AUROC |
| Distribution (3) | BBB (1975), PPBR (1797), VDss (1130) | AUROC/MAE/Spearman |
| Metabolism (6) | CYP2C9 (12092), CYP2D6 (13130), CYP3A4 (12328), CYP2C9_sub (666), CYP2D6_sub (664), CYP3A4_sub (667) | AUPRC/AUROC |
| Excretion (3) | Half_Life (667), Clearance_Hep (1020), Clearance_Micro (1102) | Spearman |
| Toxicity (4) | LD50 (7385), hERG (648), AMES (7255), DILI (475) | MAE/AUROC |

**Relevance to StateBind:** The ADMET model does not need to be SOTA to be useful in
scoring. The question is whether it provides enough discriminative power to improve
candidate ranking when integrated into the scoring function. Even a model at rank 15-20
can meaningfully distinguish good from bad candidates.

---

### Finding 7: ADMET Profiles of Approved EGFR Kinase Inhibitors -- The Kinase-Calibrated Threshold Problem

This is perhaps the most critical finding for StateBind. Approved EGFR-TKIs have ADMET
profiles that would FAIL standard drug-likeness cutoffs:

**hERG IC50 values for approved EGFR inhibitors:**

| Drug | hERG IC50 (uM) | EGFR IC50 (nM) | Oral F (%) | T1/2 (h) | CYP3A4 Substrate |
|------|----------------|-----------------|-----------|----------|------------------|
| Erlotinib | ~5* | 80 | ~60 | >36 | Yes (primary) |
| Gefitinib | 1.91 | 23-79 | ~60 | 48 | Yes (CYP3A4/3A5) |
| Osimertinib | 0.57-2.21** | 12 | ~70 | 48 | Yes (CYP3A) |
| Lazertinib | 5.3 | -- | -- | -- | -- |
| Afatinib | -- | 0.5 | -- | -- | Minimal (P-gp substrate) |

*Erlotinib hERG IC50 estimated from literature context; direct measurement not found in open literature.
**Osimertinib IC50 varies by assay: 0.57 uM (HEK293/IonWorks), 0.69 uM (CHO), 2.21 uM (HEK293/manual patch).

**The critical insight:** Osimertinib, the current standard-of-care third-generation
EGFR-TKI, has a hERG IC50 as low as 0.57 uM. At 80 mg QD dosing (Cmax ~1270 nM,
95% protein binding, free Cmax ~64 nM), the safety margin (IC50/free Cmax) is
approximately 0.57 uM / 0.064 uM = ~9x. This is well below the 30x "safe" margin
recommended for non-oncology drugs. Yet osimertinib is approved and widely used
because oncology tolerates higher cardiac risk in exchange for efficacy.

Gefitinib (IC50 = 1.91 uM) was shown to increase QTc interval in guinea pig hearts
at concentrations of 1-30 uM (Wang et al., 2021). Clinical QT prolongation is a known
class effect of EGFR-TKIs.

**This means StateBind's ADMET model is CORRECT to flag kinase inhibitors as hERG
liabilities.** The problem is not the model -- it is the use of absolute thresholds
(e.g., hERG IC50 < 10 uM = reject) rather than kinase-calibrated thresholds that
account for the accepted risk-benefit in oncology.

**Proposed kinase-calibrated thresholds for EGFR-TKI design:**

| Property | Absolute "Safe" Threshold | Kinase-Calibrated Threshold | Basis |
|----------|--------------------------|---------------------------|-------|
| hERG IC50 | >10 uM | >0.5 uM (oncology) | Osimertinib approved at 0.57 uM |
| CYP3A4 inhibition | Avoid | Acceptable (managed by DDI) | All 1st/3rd gen EGFR-TKIs are CYP3A4 substrates |
| Oral F | >30% | >30% | Consistent with approved TKIs (60-70%) |
| T1/2 | >8h | >8h | Approved TKIs: 36-48h |

---

### Finding 8: ADMET-Aware Scoring in Published Pipelines

Multiple frameworks now integrate ADMET directly into the molecular optimization loop:

**ADMETrix (ICANN 2025 Workshop, published Jan 2026):**
- Combines REINVENT generative model with ADMET AI (geometric deep learning)
- First systematic evaluation of REINVENT in multi-objective ADMET context
- Optimizes across 27 ADMET properties and 10 physicochemical descriptors simultaneously
- Evaluated on GuacaMol benchmark
- Ranked 9th on TDC hERG leaderboard (AUROC = 0.836 +/- 0.025)
- Code publicly available on GitHub

**REINVENT 4 (AstraZeneca, Feb 2024):**
- RL-based molecular design with multi-component scoring
- Supports weighted arithmetic or geometric mean of scoring components
- Each endpoint gets a user-defined weight for relative importance
- Modular: any predictive model can be plugged into the scoring function
- Open source on GitHub, actively maintained

**PMMG -- Pareto MCTS Molecular Generation (Advanced Science, 2025):**
- Uses Pareto algorithm with Monte Carlo tree search for multi-objective optimization
- Simultaneously optimizes biological activity, ADMET properties, drug-likeness, and
  synthesizability
- 51.65% success rate for molecules meeting all objectives simultaneously
- Outperforms other methods on multi-objective metrics

**Chemistry42 (Insilico Medicine):**
- Industrial-scale platform: 7 applications including generation, ADMET, retrosynthesis
- ADMET profiling rebuilt in 2024-2025 with 70+ new GPCR inhibitor models
- Retrosynthesis module uses expert templates + AI Root Planner with cost-aware
  building block integration
- Produces >2,400 candidates in dozens of hours
- The Prompt-to-Drug vision (ACS Central Science, 2026) envisions fully autonomous
  pharmaceutical R&D

**Relevance to StateBind:** The field has clearly moved to ADMET-in-the-loop design.
StateBind's approach of ADMET as "informational only" is a recognized gap. However,
StateBind's architecture already supports multi-component weighted scoring -- adding
ADMET as a 5th component (after reference similarity, drug-likeness, docking,
state specificity) is architecturally straightforward.

---

### Finding 9: ADMETlab 3.0 and the External ADMET Prediction Ecosystem

Rather than retraining StateBind's ADMET model, external prediction services could
augment or replace it:

**ADMETlab 3.0 (Nucleic Acids Research, July 2024):**
- 119 endpoints (up from 88 in v2.0), over 400,000 training entries
- Multi-task DMPNN-Des architecture (DMPNN + RDKit descriptors)
- Classification AUC range: 0.72-0.99 across 60 endpoints
- Regression R^2 range: 0.75-0.95 across 18 endpoints
- Free public API (no registration required)
- Includes uncertainty estimates for confident compound selection

**Deep-PK (Nucleic Acids Research, July 2024):**
- 73 ADMET endpoints using graph neural networks
- Outperformed ADMETlab 2.0 on 46 of 53 compared endpoints
- Publicly accessible web tool

**pkCSM:**
- Graph-based signatures for ADMET prediction
- Free web server
- Generally outperformed by ADMETlab for most PK endpoints

**admetSAR 3.0 (Nucleic Acids Research, 2024):**
- Comprehensive platform for ADMET exploration, prediction, and optimization
- Complementary to ADMETlab

**Integration strategy for StateBind:** Use ADMETlab 3.0's API to generate multi-endpoint
ADMET profiles for all 461 candidates. This requires zero model training -- just
SMILES-in, profiles-out. The API nature makes this operationally trivial (a few hours
of scripting). The 119-endpoint coverage far exceeds StateBind's 6-endpoint model.

---

### Finding 10: In Silico PK Prediction -- Current Accuracy and Limitations

**PKSmart (bioRxiv, Feb 2024; PMC, 2025):**
- First publicly released PK models on par with industry-standard models
- Predicts VDss, CL, t1/2, fu, MRT for human PK
- Uses Morgan fingerprints + Mordred descriptors + predicted animal PK data
- Performance on external test set (315 compounds):
  - VDss: R^2 = 0.33, GMFE = 2.58
  - CL: R^2 = 0.45, GMFE = 1.98
- Pearson correlations with AstraZeneca proprietary models: 0.77-0.78 for VDss, fu
- Open source, pip-installable, web app available

**ADMETlab predictions for PK:**
- Bioavailability (F30%): Balanced accuracy 0.813
- Half-life regression: R^2 approximately 0.70
- Clearance prediction: moderate accuracy, slight overprediction observed

**DeepCt (Molecular Pharmaceutics, 2024):**
- Predicts full pharmacokinetic concentration-time curves from chemical structure
- Goes beyond single PK parameters to predict the entire PK profile
- Enables direct dose projection

**Honest assessment:** In silico PK prediction remains the weakest link in the
end-to-end chain. VDss R^2 = 0.33 means the model explains only 33% of variance --
essentially, predictions should be treated as directional (high/low/moderate) rather
than quantitative. GMFE of 2.58 means predictions are off by ~2.5-fold on average.

**For StateBind's purposes:** PK projections should be presented as "computational
estimates with acknowledged uncertainty" -- useful for ranking and triaging candidates,
not for predicting clinical doses. The publication should frame this honestly: "We
project approximate PK parameters to prioritize candidates with plausible oral
bioavailability and half-life, acknowledging the inherent limitations of in silico PK
prediction (GMFE ~2-3x)."

---

### Finding 11: Enamine REAL Space and Commercial Synthesizability

**Current scale (2025-2026):**
- Enamine REAL Space: 64.9-78.1 billion make-on-demand molecules
  (discrepancy likely reflects different catalog snapshots)
- Assembled via 172 well-validated parallel synthesis protocols
- Uses 181,288 in-stock qualified building blocks
- Synthesis feasibility: >80%
- Delivery time: 3-4 weeks
- Constantly expanding

**ZINC-22 database:** Multi-billion-scale database of tangible (purchasable or
synthesizable) compounds, complementary to Enamine REAL.

**Recursion + Enamine AI-enabled libraries (April 2025):**
- New targeted compound libraries designed using AI for specific target classes
- Demonstrates industry trend toward AI-curated make-on-demand libraries

**Relevance to StateBind:** The Enamine REAL Space provides a practical "ground truth"
for synthesis feasibility. A candidate molecule that can be matched to (or is a close
analog of) an Enamine REAL compound is demonstrably synthesizable. This provides an
independent validation of retrosynthetic predictions beyond computational tools alone.

StateBind could use Enamine REAL Space as the building block stock for AiZynthFinder,
which would give the most realistic assessment of actual synthesis feasibility.

---

### Finding 12: The NovoExpert-2 Approach -- What SOTA ADMET Looks Like

NovoExpert-2 (ChemRxiv, April 2026) achieves top-1 performance on 11 of 22 TDC
ADMET benchmarks and top-3 on 19 of 22. Its approach is instructive:

**Architecture:**
- CatBoost gradient-boosted trees (not deep learning for most endpoints)
- Molecular representations: combination of ECFP, Avalon, ErG fingerprints +
  200 molecular properties + GIN (supervised masking) embeddings
- Chemprop v2 used for DILI only (where end-to-end learned representations help)

**Key result:** CYP3A4_Veith AUPRC = 0.916, exceeding prior SOTA by 0.016.

**Lesson for StateBind:** The ADMET prediction SOTA is currently dominated by
gradient-boosted trees on diverse fingerprint ensembles, not by deep neural networks.
StateBind's GIN-based multi-task model (187K params) is architecturally reasonable but
may benefit from fingerprint augmentation. However, for the purposes of scoring
integration, using external ADMET predictions (from ADMETlab 3.0 or similar) is more
practical than retraining.

---

### Finding 13: Synthesis Route Lengths for Approved Kinase Inhibitors

FDA approved 73 small molecule kinase inhibitor drugs through September 2021 (Roskoski,
J Med Chem, 2021). Synthesis route data from the comprehensive review:

**Representative examples:**
- Imatinib (BCR-ABL): 6 convergent synthetic steps
- Crizotinib (ALK): Two convergent routes (estimated 5-8 steps total)
- Akt kinase inhibitor (process scale): 17 total steps for kilogram-scale production

**General principles:**
- Discovery-phase routes are typically longer (more linear, less optimized)
- Process chemistry routes are shorter (convergent, optimized)
- Median discovery-phase route: estimated 5-8 steps for kinase inhibitors
- Step-economical synthesis approaches use cycloadditions for rapid scaffold access

**AiZynthFinder data:** Average route length for ChEMBL molecules = 1.97 steps;
for REINVENT-generated molecules = 6.04 steps. The discrepancy reflects that ChEMBL
contains many fragment-like and simple drug-like molecules, while generative models
produce structurally more complex candidates.

**Relevance to StateBind:** If StateBind's top candidates require routes of 4-8 steps,
that is within the normal range for kinase inhibitors. Routes longer than 10 steps or
requiring non-commercial building blocks should be flagged as potentially impractical.

---

### Finding 14: The FSscore -- Personalized Synthesizability Assessment

FSscore (Chemistry-Methods, 2024) represents a recent advance in synthesizability
scoring: a machine learning model trained on reaction data that can be personalized by
fine-tuning to a specific chemical scope.

**Key features:**
- Trained on reaction databases
- Can be fine-tuned for kinase-inhibitor-specific chemistry
- Provides a continuous feasibility score
- More nuanced than binary RAscore or heuristic SAscore

**Relevance to StateBind:** FSscore fine-tuned on kinase inhibitor synthesis reactions
would provide the most relevant synthesizability assessment for StateBind's EGFR-targeted
candidates. However, the training data and fine-tuning process may require significant
effort compared to using off-the-shelf RAscore.

---

### Finding 15: Multi-Objective Pareto + ADMET + Synthesizability -- The Emerging Standard

The PMMG algorithm (Advanced Science, 2025) demonstrates what a state-of-the-art
multi-objective molecular design pipeline looks like:

- Simultaneously optimizes binding activity, ADMET, drug-likeness, and synthesizability
- Uses Pareto frontier to balance competing objectives without fixed weights
- 51.65% success rate for molecules meeting ALL objectives
- Significantly outperforms prior methods

**The five "essential considerations" for generative AI in drug discovery (JCIM, 2025):**
1. Chemical synthesizability
2. Favorable ADMET properties
3. Desirable target-specific binding
4. Appropriate multiparameter optimization functions
5. Human feedback

StateBind currently addresses #3 (binding via docking) and partially #4 (weighted scoring).
It does not address #1, #2 (in scoring), or #5. Addressing #1 and #2 would bring it
to 4/5, which would be highly competitive.

---

## Implications for StateBind

### Opportunities

**1. Retrosynthetic Feasibility as a Scoring Component (HIGH IMPACT, MODERATE EFFORT)**

Add a 5th scoring component: retrosynthetic feasibility.

*Architecture:*
```
Tier 0: AiZynthFinder 4.0 (40-90 s/mol, for top 50-100 candidates)
Tier 1: RAscore (ms/mol, for all 461 candidates)
Tier 2: SA score (current, as fallback)
```

This mirrors the existing docking cascade (GNINA -> MPNN -> proxy -> stub).

*Scoring function update:*
Current: 0.35 ref_sim + 0.30 drug_like + 0.20 docking + 0.15 state_spec
Proposed: 0.30 ref_sim + 0.25 drug_like + 0.20 docking + 0.10 state_spec + 0.15 synth_feas

Or alternatively, replace SA score within drug-likeness with RAscore (since SA score
is already 25% of drug-likeness = 7.5% of total), which requires no weight redistribution.

*Effort estimate:* 1-2 weeks for RAscore integration + scoring update; 1 week for
AiZynthFinder Tier 0 validation of top candidates.

*Publication value:* "State-aware molecular design with retrosynthetic validation" --
no competing pipeline does this. Demonstrating that X% of top state-aware candidates
have feasible synthesis routes (vs Y% of static candidates) adds an entirely new
dimension to the comparison.

**2. ADMET-Integrated Scoring with Kinase-Calibrated Thresholds (HIGH IMPACT, LOW EFFORT)**

Move ADMET from informational to scoring, using kinase-calibrated thresholds.

*Approach:*
- Use ADMETlab 3.0 API to generate 119-endpoint profiles for all candidates
- Define kinase-calibrated thresholds based on approved EGFR-TKI profiles
- Create a composite ADMET score: fraction of endpoints within kinase-calibrated
  acceptable ranges, weighted by clinical importance
- Integrate as 6th scoring component or replace the drug-likeness component

*Kinase-calibrated thresholds (based on findings above):*
- hERG IC50: >0.5 uM (not >10 uM) -- based on osimertinib approval
- CYP3A4: Accept substrate status (managed by DDI monitoring)
- Oral F (predicted): >30%
- Caco-2: >-5.15 (log Papp)
- Solubility: >-4 log mol/L

*Effort estimate:* 1 week for ADMETlab API integration; 1 week for threshold
calibration and scoring integration.

*Publication value:* "ADMET-aware scoring with kinase-class-calibrated thresholds
resolves the false-rejection problem for kinase inhibitors" -- addresses a real
limitation that affects the entire kinase inhibitor design field.

**3. End-to-End Pipeline Demonstration (VERY HIGH IMPACT, MODERATE EFFORT)**

Demonstrate the full trajectory for top 10-20 candidates:
```
Generation -> Scoring -> ADMET Profile -> Retrosynthetic Route -> PK Projection
```

*Approach:*
- Take top 10-20 candidates from state-aware pipeline
- Generate ADMET profiles (ADMETlab 3.0 API)
- Compute retrosynthetic routes (AiZynthFinder)
- Project PK parameters (PKSmart)
- Present results in a single table showing each candidate's full drug-ability profile

*Effort estimate:* 2-3 weeks total.

*Publication value:* This transforms the paper from "computational scoring comparison"
to "practical drug design demonstration." Most AI drug design papers stop at generation
and scoring. Showing full ADMET + synthesis + PK profiles for top candidates
demonstrates translational awareness that reviewers at Nature Computational Science
or JCIM would reward.

**4. TDC Benchmark Comparison (MODERATE IMPACT, LOW EFFORT)**

Re-evaluate StateBind's ADMET model on TDC's exact benchmark splits and report properly
comparable metrics (AUPRC for CYP, AUROC for hERG, MAE for regression).

*Effort estimate:* 2-3 days.

*Publication value:* Contextualizes StateBind's ADMET performance against the field.
Even if below SOTA, honest reporting with proper benchmarking is expected by reviewers.

### Risks and Caveats

1. **RAscore is trained on ChEMBL chemical space.** StateBind's VAE-generated molecules
   may be out-of-distribution for RAscore. Applicability domain checking is essential.

2. **AiZynthFinder routes are computational predictions.** They have not been validated
   by wet-lab synthesis. The 62.1% precision (round-trip) vs ~70-85% search success rate
   shows that many "routes found" would not actually work in practice.

3. **In silico PK prediction is low-accuracy.** VDss R^2 = 0.33 (PKSmart) means
   predictions are directional, not quantitative. Overclaiming PK accuracy would
   undermine scientific credibility.

4. **Kinase-calibrated thresholds are a judgment call.** There is no consensus standard
   for kinase-specific ADMET thresholds. The thresholds proposed above are based on
   approved drug profiles but could be challenged by reviewers as too lenient.

5. **Scoring weight redistribution.** Adding retrosynthesis and ADMET to the scoring
   function requires re-running the weight sensitivity analysis and may change the
   static vs state-aware comparison results. This is scientifically appropriate but
   operationally significant.

6. **TDC reproducibility concerns.** The February 2026 critical assessment found that
   most top TDC entries are not reproducible. Comparisons should cite the reproducible
   methods (MapLight+GNN, CaliciBoost) as the true SOTA.

### Recommended Next Steps

1. **Immediate (Week 1):** Integrate ADMETlab 3.0 API calls for all 461 candidates.
   Generate 119-endpoint profiles. Compare against approved EGFR-TKI profiles.

2. **Short-term (Weeks 2-3):** Integrate RAscore as synthesis feasibility proxy in
   scoring cascade. Run AiZynthFinder on top 50 candidates for Tier 0 validation.

3. **Medium-term (Weeks 3-5):** Define kinase-calibrated ADMET thresholds. Integrate
   composite ADMET score into weighted scoring function. Re-run comparison with
   5-component or 6-component scoring.

4. **Medium-term (Weeks 4-6):** Run PKSmart for PK projection on top 20 candidates.
   Construct end-to-end drug-ability profiles.

5. **For publication (Week 6+):** Re-run weight sensitivity analysis with new scoring
   components. Update retrospective validation. Prepare end-to-end results table.
   Benchmark ADMET model against TDC properly.

---

## References

1. Thakkar, A., et al. (2024). "AiZynthFinder 4.0: developments based on learnings
   from 3 years of industrial application." *Journal of Cheminformatics*, 16, 56.
   DOI: 10.1186/s13321-024-00860-x

2. Genheden, S., et al. (2020). "AiZynthFinder: a fast, robust and flexible
   open-source software for retrosynthetic planning." *Journal of Cheminformatics*,
   12, 70. DOI: 10.1186/s13321-020-00472-1

3. Thakkar, A., et al. (2021). "Retrosynthetic accessibility score (RAscore) -- rapid
   machine learned synthesizability classification from AI driven retrosynthetic
   planning." *Chemical Science*, 12, 3339-3349. DOI: 10.1039/D0SC05401A

4. Skoraczynski, G., et al. (2023). "Critical assessment of synthetic accessibility
   scores in computer-assisted synthesis planning." *Journal of Cheminformatics*, 15, 6.
   DOI: 10.1186/s13321-023-00678-z

5. Gao, S., et al. (2024). "Evaluating Molecule Synthesizability via Retrosynthetic
   Planning and Reaction Prediction." *arXiv*:2411.08306v2.

6. Gao, S., et al. (2025). "RetroScore: graph edit distance-guided retrosynthesis
   for accessibility scoring with route metrics." *Journal of Cheminformatics*, 17.
   DOI: 10.1186/s13321-025-01138-6

7. Neeser, R., et al. (2024). "FSscore: A Personalized Machine Learning-Based
   Synthetic Feasibility Score." *Chemistry-Methods*, 4(6), e202400024.
   DOI: 10.1002/cmtd.202400024

8. Huang, K., et al. (2022). "Artificial intelligence foundation for therapeutic
   science." *Nature Chemical Biology*, 18, 1033-1036.
   DOI: 10.1038/s41589-022-01131-2 (TDC benchmark)

9. Mourdou, N., et al. (2026). "ADMETrix: ADMET-Driven De Novo Molecular Generation."
   *ICANN 2025 Workshop on AI for Drug Discovery*. ChemRxiv.
   DOI: 10.26434/chemrxiv-2025-3x5nq-v3

10. Loeffler, H., et al. (2024). "Reinvent 4: Modern AI-driven generative molecule
    design." *Journal of Cheminformatics*, 16, 20.
    DOI: 10.1186/s13321-024-00812-5

11. Fu, L., et al. (2024). "ADMETlab 3.0: an updated comprehensive online ADMET
    prediction platform." *Nucleic Acids Research*, 52(W1), W422-W431.
    DOI: 10.1093/nar/gkae236

12. Myung, Y., et al. (2024). "Deep-PK: deep learning for small molecule
    pharmacokinetic and toxicity prediction." *Nucleic Acids Research*, 52(W1),
    W469-W475. DOI: 10.1093/nar/gkae254

13. Seal, S., et al. (2024). "PKSmart: An Open-Source Computational Model to Predict
    in vivo Pharmacokinetics of Small Molecules." *bioRxiv*.
    DOI: 10.1101/2024.02.02.578658

14. Zhong, Y., et al. (2023). "Acute osimertinib exposure induces electrocardiac
    changes by synchronously inhibiting the currents of cardiac ion channels."
    *Frontiers in Pharmacology*, 14, 1177003.
    DOI: 10.3389/fphar.2023.1177003

15. Wang, Z., et al. (2021). "Mechanisms of gefitinib-induced QT prolongation."
    *European Journal of Pharmacology*, 910, 174467.
    DOI: 10.1016/j.ejphar.2021.174467

16. Roskoski, R. (2021). "Small Molecule Kinase Inhibitor Drugs (1995-2021): Medical
    Indication, Pharmacology, and Synthesis." *Journal of Medicinal Chemistry*, 65(2),
    1003-1072. DOI: 10.1021/acs.jmedchem.1c00963

17. Zhavoronkov, A., et al. (2023). "Chemistry42: An AI-Driven Platform for Molecular
    Design and Optimization." *Journal of Chemical Information and Modeling*, 63(3),
    695-701. DOI: 10.1021/acs.jcim.2c01191

18. Gao, W., et al. (2025). "Generative AI for navigating synthesizable chemical space."
    *Proceedings of the National Academy of Sciences*, 122(41), e2415665122.
    DOI: 10.1073/pnas.2415665122 (SynFormer)

19. Liu, J., et al. (2025). "A Multi-Objective Molecular Generation Method Based on
    Pareto Algorithm and Monte Carlo Tree Search." *Advanced Science*, 12(23), 2410640.
    DOI: 10.1002/advs.202410640 (PMMG)

20. NovoExpert Team (2026). "NovoExpert-2: State-of-the-Art ADMET Prediction via
    Gradient-Boosted Trees on MapLight Fingerprints and GIN Embeddings." *ChemRxiv*.
    DOI: 10.26434/chemrxiv.15000061/v2

21. Isaev, D., et al. (2026). "Critical Assessment of ML models for ADMET Prediction
    in TDC leaderboards." *bioRxiv*. DOI: 10.64898/2026.02.26.708193v1

22. Lehmann, H. A., et al. (2018). "Validation and Clinical Utility of the hERG
    IC50:Cmax Ratio to Determine the Risk of Drug-Induced Torsades de Pointes: A
    Meta-Analysis." *Pharmacotherapy*, 38(3), 341-348. DOI: 10.1002/phar.2087

23. Gintant, G. A., et al. (2006). "Utility of hERG Assays as Surrogate Markers of
    Delayed Cardiac Repolarization and QT Safety." *Toxicologic Pathology*, 34(1),
    81-90. DOI: 10.1080/01926230500431376

24. Kang, S. P., et al. (2021). "Cardiac Safety Assessment of Lazertinib." *JTO
    Clinical and Research Reports*, 2(10), 100224.
    DOI: 10.1016/j.jtocrr.2021.100224

25. Kramer, C. (2024). "Comprehensive benchmarking of computational tools for
    predicting toxicokinetic and physicochemical properties of chemicals." *Journal
    of Cheminformatics*, 16, 170. DOI: 10.1186/s13321-024-00931-z

26. Gao, W., et al. (2020). "The Synthesizability of Molecules Proposed by Generative
    Models." *Journal of Chemical Information and Modeling*, 60(12), 5714-5723.
    DOI: 10.1021/acs.jcim.0c00174

27. Koscher, B. A., et al. (2024). "ASKCOS: Open-Source, Data-Driven Synthesis
    Planning." *Accounts of Chemical Research*. DOI: 10.1021/acs.accounts.5c00155
