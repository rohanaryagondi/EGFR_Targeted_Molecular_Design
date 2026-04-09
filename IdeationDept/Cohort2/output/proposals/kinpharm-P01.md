---
agent: Maverick Kinome Pharmacologist
round: 2
date: 2026-04-09
type: proposal
proposal_id: kinpharm-P01
title: "Multi-Kinase Generalization of State-Aware Molecular Design: From EGFR Case Study to Kinome-Wide Validation"
---

# Proposal: Multi-Kinase Generalization of State-Aware Molecular Design -- From EGFR Case Study to Kinome-Wide Validation

## Proposing Agent

Maverick Kinome Pharmacologist (kinpharm), Cohort2. Domain expertise in kinome-wide selectivity profiling, polypharmacology, multi-target ML, and conformational state pharmacology.

## Problem Statement

StateBind's 10x retrospective enrichment for EGFR (EF@10 = 4.95/7.72 state-aware vs 0.47/0.79 static) is the strongest computational evidence that conformational state-aware molecular design outperforms static single-structure design. However, this remains a single-target case study. Reviewers at any venue above JCIM will ask: "Does this generalize, or is it an EGFR artifact?"

Three specific deficiencies constrain the current work:

1. **Statistical power**: N=5 held-out drugs (pre-2010) and N=3 (pre-2015) produce bootstrap 95% CIs of approximately [1.5, 10.0] and [2.0, 15.0] respectively -- so wide that the true enrichment advantage could plausibly be anywhere from modest to enormous.

2. **Generalization evidence**: EGFR is among the most structurally characterized kinases in the PDB (~250 structures, 4 well-defined conformational states). A method that works only on the kinase with the best structural data is unimpressive.

3. **No selectivity dimension**: StateBind currently scores affinity and ADMET properties but does not evaluate kinome selectivity. Since all approved EGFR inhibitors are Type I (active-state binders) and zero are Type II (DFG-out binders), the translational relevance of state-aware DFG-out generation remains untested.

This proposal addresses all three by extending the retrospective validation to 5 kinases (EGFR, ABL1, BRAF, ALK, JAK2), training a multi-task MPNN with conformational state conditioning, and testing the DFG-out selectivity hypothesis against public kinase profiling datasets.

## Vision

A single paper in Nature Computational Science that makes three claims:

1. **Generalization**: State-aware molecular design produces consistently higher retrospective enrichment than static design across 5 kinases spanning 3 kinase groups (TK, TKL, STK), with 20+ held-out approved drugs and CIs narrowed by ~59%.

2. **Selectivity dividend**: Molecules generated for DFG-out conformational states are predicted to be more selective (higher Gini coefficients) than DFG-in-targeted molecules, validated against PKIS2 (645 compounds, 392 kinases) and KCGS 2.0 (295 compounds, 262 kinases).

3. **Multi-task ML contribution**: A conformational state-conditioned multi-task MPNN achieves higher predictive accuracy than single-task models on data-sparse kinases through cross-kinase transfer learning.

This transforms StateBind from "an EGFR tool" to "a general framework for state-aware kinase drug design" -- a fundamentally different publication.

---

## Background and Evidence

### Key Evidence

**Multi-kinase data sufficiency is established.** Round 1 research (kinpharm-R01) compiled bioactivity counts from ChEMBL 34/35 for 12 candidate kinases. ABL1 (5,200+ compounds, 350+ PDB structures, 6 approved drugs), BRAF (2,968 compounds, 150+ structures, 4 approved drugs), ALK (1,800 compounds, 100+ structures, 6 approved drugs), and JAK2 (2,100 compounds, 80+ structures, 7+ approved drugs) all meet the minimum thresholds for MPNN training and retrospective validation. Data compiled from Miljkovic et al. (2021), Merget et al. (2020), and ChEMBL 34/35 release notes.

**The DFG-out selectivity hypothesis has quantitative support.** Ung et al. (J Med Chem 2015) profiled 13 structurally validated Type II inhibitors against kinase panels, finding Gini coefficients of 0.64-0.80 (mean ~0.72) versus 0.49-0.52 (mean ~0.51) for Type I controls (p < 10^-4). The allosteric pocket exposed by the DFG flip is less conserved than the ATP binding site: the DFG-1 residue shows 84% small hydrophilic, 15% bulky hydrophobic across the kinome (Fang et al., J Med Chem 2020), creating exploitable selectivity handles.

**Multi-task kinase MPNN methods are mature.** AMGU (Chen et al., JCIM 2023) trains across 204 kinases simultaneously with transfer learning that improves data-sparse targets. Chemprop v2 (Heid et al., JCIM 2024) provides production-grade multi-task D-MPNN with built-in uncertainty quantification. KinomeMETA (Ren et al., Briefings in Bioinformatics 2024) covers 661 kinases with meta-learning. Published multi-task kinase MPNN achieves R^2 = 0.5-0.7 on well-studied kinases in random splits and AUC 0.807 for kinase profiling (Li et al., J Cheminform 2024).

**AlphaFold2 multi-state modeling fills structural gaps.** Song et al. (PLOS Comp Biol 2024) generated 6,297 AF2-MSM models in previously unobserved conformations for 398 kinases, achieving docking AUCs of 79.28 (PTK2) and 80.16 (JAK2) with AF2-generated DFG-out models. This resolves the structural bottleneck for kinases with limited experimental DFG-out coverage.

**Statistical power analysis demands 5 kinases.** With N=5 held-out drugs (EGFR alone, pre-2010), bootstrap 95% CIs span ~8.5 units. Pooling across 5 kinases (N~20 held-out drugs) narrows CIs to ~3.5 units (59% reduction). For testing H0: EF_state_aware <= EF_static, 5 kinases achieves power ~0.85 at alpha=0.05, compared to ~0.60 with 3 kinases.

**Public selectivity datasets enable rigorous validation.** PKIS2 (Wells et al., PLOS One 2017): 645 compounds, 86 chemotypes, profiled at 392 kinases. KCGS 2.0 (Elkins et al., Int J Mol Sci 2021): 295 narrow-spectrum probes covering 262 kinases. HMS LINCS KINOMEscan: profiling data for erlotinib, gefitinib, afatinib, etc. across ~440 kinases.

### Relationship to Existing Work

**Vision System ideas.** This proposal directly extends the existing pipeline (Vision Idea 009, implemented) and builds on the retrospective validation framework (Vision Idea 005, implemented). It does not duplicate any deferred vision idea; instead, it addresses the acknowledged gap of "multi-kinase validation" which no existing vision idea covers as a primary focus.

**Relay Therapeutics precedent.** Relay's commercial pipeline demonstrates that conformational-state-aware drug design has real-world value (RLY-2608, PI3Kalpha, Phase 3 registration). Their platform, Dynamo, integrates cryo-EM, MD simulation, and ML to exploit conformational dynamics. StateBind provides an open-source computational counterpart with a different methodological approach (discrete state conditioning vs continuous dynamics).

**Published multi-kinase benchmarks.** The Kinase200 benchmark (Martin et al., JCIM 2023) established that multi-task MPNN improves over single-task by +0.03-0.04 R^2 on random splits but only marginally on structure-based splits (R^2 = 0.23 vs 0.19). StateBind's conformational state conditioning is a novel dimension absent from all published multi-kinase benchmarks.

---

## Proposed Approach

### Overview

The proposal has four interlocking components executed in sequence over 10-14 weeks:

**Component A**: Multi-Kinase Data Curation (Weeks 1-3)
**Component B**: Multi-Kinase Conformational State Atlas (Weeks 2-4)
**Component C**: Multi-Task State-Conditioned MPNN (Weeks 4-8)
**Component D**: Retrospective Validation, Selectivity Analysis, and Statistical Testing (Weeks 7-12)

### Implementation Steps

#### Component A: Multi-Kinase Data Curation

**Objective**: Replicate StateBind's EGFR data curation protocol for ABL1, BRAF, ALK, and JAK2, producing standardized training sets for each kinase.

**Step A1: ChEMBL Bioactivity Extraction (per kinase)**

For each kinase, query ChEMBL 35 with the following filters (matching the EGFR protocol):
- Target type: SINGLE PROTEIN
- Assay confidence score >= 7
- Standard type: IC50, Ki, or Kd
- Standard relation: '='
- pChEMBL value not null
- Standard units: nM
- Remove duplicates: keep median pChEMBL per compound-target pair

Expected yields:

| Kinase | ChEMBL Target ID | Expected Compounds (filtered) | Pre-2010 Training Set | Pre-2015 Training Set |
|--------|-------------------|-------------------------------|----------------------|----------------------|
| EGFR | CHEMBL203 | ~10,466 (existing) | ~7,800 | ~9,200 |
| ABL1 | CHEMBL1862 | ~8,500 | ~5,500 | ~7,200 |
| BRAF | CHEMBL5145 | ~3,625 | ~1,800 | ~2,900 |
| ALK | CHEMBL4247 | ~2,700 | ~800 | ~1,900 |
| JAK2 | CHEMBL2971 | ~3,200 | ~1,200 | ~2,400 |

Note: Pre-2010 ALK data is sparse because the first ALK inhibitor (crizotinib) was approved in 2011 and the target emerged as oncologically relevant only after 2007 (Soda et al., Nature 2007). The pre-2010 training split for ALK will be N~800, which is borderline for single-task MPNN but adequate within a multi-task framework where transfer learning from EGFR/ABL1 compensates.

**Step A2: SMILES Standardization and Deduplication**

Apply RDKit standardization pipeline matching StateBind's existing protocol:
- Canonicalize SMILES
- Remove salts and fragments (keep largest fragment)
- Neutralize charges
- Remove compounds with molecular weight < 200 or > 800 Da
- Remove compounds failing Lipinski Rule of 5 + 1 violation tolerance
- Convert to SELFIES for VAE compatibility

**Step A3: Temporal Split Definition**

For each kinase, define held-out drug sets:

| Kinase | Pre-2010 Held-Out Drugs | Pre-2015 Held-Out Drugs |
|--------|------------------------|------------------------|
| EGFR | Osimertinib (2015), Dacomitinib (2018) + development compounds | Osimertinib (2015), Dacomitinib (2018) |
| ABL1 | Ponatinib (2012), Bosutinib (2012), Asciminib (2021) | Asciminib (2021) |
| BRAF | Vemurafenib (2011), Dabrafenib (2013), Encorafenib (2018), Tovorafenib (2024) | Encorafenib (2018), Tovorafenib (2024) |
| ALK | Crizotinib (2011), Ceritinib (2014), Alectinib (2015), Brigatinib (2017), Lorlatinib (2018), Ensartinib (2024) | Brigatinib (2017), Lorlatinib (2018), Ensartinib (2024) |
| JAK2 | Ruxolitinib (2011), Tofacitinib (2012), Baricitinib (2018), Fedratinib (2019), Pacritinib (2022), Momelotinib (2023), Deuruxolitinib (2024) | Baricitinib (2018), Fedratinib (2019), Pacritinib (2022), Momelotinib (2023), Deuruxolitinib (2024) |

**Combined held-out drug count**: Pre-2010 split: ~22 drugs across 5 kinases. Pre-2015 split: ~15 drugs across 5 kinases. Total: 37 unique held-out evaluation points.

**Step A4: Quality Control**

- Cross-check all held-out drugs against training sets to confirm no temporal leakage
- Verify ChEMBL target annotations against UniProt (ABL1: P00519, BRAF: P15056, ALK: Q9UM73, JAK2: O60674)
- Flag compounds tested against multiple panel kinases for multi-task deduplication
- Generate data quality report per kinase: N compounds, temporal distribution, pChEMBL distribution, scaffold diversity (Murcko decomposition)

#### Component B: Multi-Kinase Conformational State Atlas

**Objective**: Build a 5-kinase state atlas using KLIFS annotations plus AF2-MSM supplementation, producing the 9-dimensional state feature vectors that StateBind's pipeline requires.

**Step B1: KLIFS Structure Retrieval and State Assignment**

For each kinase, download all structures from KLIFS (klifs.net) with conformational annotations:

| Kinase | Expected KLIFS Structures | DFGin/aCin | DFGin/aCout | DFGout/aCin | DFGout/aCout | Structural Gap? |
|--------|--------------------------|------------|-------------|-------------|-------------|-----------------|
| EGFR | ~250+ | Many | Many | Some | Some | No (4 states covered) |
| ABL1 | ~350+ | Many | Many | ~27 | Some | No (4 states covered) |
| BRAF | ~150+ | Many | Some | Some | Some | Minor (DFGout/aCout sparse) |
| ALK | ~100+ | Many | Some | Limited | Very limited | Yes (DFGout states sparse) |
| JAK2 | ~80+ | Many | Some | Limited | Limited | Yes (DFGout states sparse) |

**Step B2: Representative Structure Selection**

For each kinase-state combination with experimental structures:
- Cluster structures by pocket RMSD (cutoff 1.5 A) using KLIFS pocket alignment
- Select the highest resolution structure from the largest cluster as the representative
- Require resolution <= 3.0 A and R-free <= 0.30
- For states with no experimental structure, flag for AF2-MSM generation (Step B3)

**Step B3: AF2-MSM Supplementation for Missing States**

For ALK (DFGout/aCin, DFGout/aCout) and JAK2 (DFGout/aCout), generate AF2 multi-state models following the protocol of Song et al. (PLOS Comp Biol 2024):
- Use ColabFold with reduced MSA depth (16-64 sequences) to promote conformational diversity
- Generate 50 models per kinase, cluster by DFG/aC conformation
- Select the model closest to the cluster centroid for each missing state
- Validate by GNINA re-docking of known Type II inhibitors: require docking AUC >= 0.70 against random decoys

**Step B4: 9-Dimensional State Feature Computation**

Compute StateBind's 9D feature vectors for each kinase-state representative structure:
- DFG-Asp chi1 angle
- DFG-Phe chi1 angle
- aC helix rotation angle
- Pocket volume (SiteMap or fpocket)
- DFG-Asp to catalytic Lys distance
- aC-Glu to catalytic Lys distance
- Hinge-DFG distance
- P-loop conformation metric
- Activation loop RMSD to active reference

Normalize all features using the same z-score parameters as the EGFR atlas. Cross-kinase normalization is critical: the same feature (e.g., pocket volume) must be on the same scale across kinases to enable multi-task learning.

**Deliverable**: A 5-kinase, 4-state atlas (20 state entries) with 9D feature vectors, representative PDB IDs, and provenance flags (experimental vs AF2-generated).

#### Component C: Multi-Task State-Conditioned MPNN

**Objective**: Train a single MPNN that predicts pIC50 for all 5 kinases simultaneously, conditioned on both kinase identity and conformational state.

**Step C1: Architecture Design**

Extend StateBind's existing D-MPNN (currently single-task EGFR, R^2=0.69) to multi-task with two modifications:

1. **Kinase identity conditioning**: Append a learned kinase embedding (5-dimensional, one per kinase) to the molecular representation before the readout layers. This enables shared molecular features with kinase-specific readout heads.

2. **Conformational state conditioning**: Concatenate the 9D state feature vector to the kinase-conditioned molecular representation. This is the critical innovation: the MPNN learns that the same molecule has different predicted affinities depending on which conformational state the target presents.

Architecture summary:
```
Input: SMILES -> Molecular graph
D-MPNN encoder (shared across kinases): 300-dim message passing, 3 iterations
Kinase embedding layer: 5-dim learned embedding per kinase
State feature layer: 9-dim state vector (from atlas)
Concatenation: [300-dim mol] + [5-dim kinase] + [9-dim state] = 314-dim
FFN readout: 314 -> 256 -> 128 -> 1 (pIC50 prediction)
```

Total parameters: ~350K (comparable to existing single-task MPNN).

**Step C2: Training Protocol**

- **Training data**: Combined ChEMBL datasets for all 5 kinases (total ~28,500 compounds in pre-2010 split, ~22,600 in pre-2015 split)
- **Multi-task loss**: Sum of per-kinase MSE losses, weighted by inverse dataset size to balance kinase contributions:
  - Weight_EGFR = 1.0 (reference)
  - Weight_ABL1 = 10466/8500 = 1.23
  - Weight_BRAF = 10466/3625 = 2.89
  - Weight_ALK = 10466/2700 = 3.88
  - Weight_JAK2 = 10466/3200 = 3.27
- **State conditioning during training**: For each compound-kinase pair, the training label is the measured pIC50. The state vector is assigned by: (a) if a co-crystal structure exists with that compound, use the observed state; (b) otherwise, use the predominant binding state for that compound class (Type I -> DFGin/aCin; Type II -> DFGout/aCin or DFGout/aCout). This approximation is necessary because most ChEMBL compounds lack co-crystal structures.
- **Hyperparameters**: Learning rate 1e-4, batch size 64, 100 epochs, early stopping on validation loss (patience 15), Adam optimizer. Chemprop v2 defaults for message passing depth (3) and hidden size (300).
- **Validation**: 80/10/10 train/val/test split stratified by scaffold (Murcko decomposition) within each kinase.

**Step C3: Baseline Models for Comparison**

Train 3 baseline models to demonstrate multi-task and state-conditioning advantages:

| Model | Architecture | Kinases | State Conditioning | Purpose |
|-------|-------------|---------|-------------------|---------|
| Baseline A | Single-task D-MPNN | 1 per kinase (5 models) | None | Current StateBind approach |
| Baseline B | Multi-task D-MPNN | 5 kinases jointly | None | Tests kinase transfer learning alone |
| Proposed | Multi-task D-MPNN | 5 kinases jointly | 9D state vector | Tests state conditioning on top of transfer |

Expected results based on published benchmarks:
- Baseline A: R^2 = 0.55-0.69 (EGFR: 0.69 known; ABL1: ~0.65; BRAF: ~0.55; ALK: ~0.50; JAK2: ~0.55)
- Baseline B: R^2 = 0.58-0.72 (+0.03-0.05 from transfer, largest gains on ALK and JAK2)
- Proposed: R^2 = 0.60-0.74 (+0.02 from state conditioning, evaluated on state-specific test sets)

**Step C4: Uncertainty Quantification**

Use Chemprop v2's built-in evidential uncertainty (Soleimany et al., ACS Cent Sci 2021):
- Train with evidential loss to produce per-prediction uncertainty estimates
- Calibrate on validation set using expected calibration error (ECE)
- Report uncertainty alongside all enrichment and selectivity predictions
- Critical for Nature Computational Science: reviewers will demand uncertainty quantification

#### Component D: Retrospective Validation, Selectivity Analysis, and Statistical Testing

**Step D1: Per-Kinase Retrospective Validation**

Replicate StateBind's existing EGFR retrospective protocol for each new kinase:

1. For each kinase, generate candidates using the SELFIES VAE conditioned on each of the 4 conformational states (4 x 1000 = 4000 candidates per kinase)
2. Score candidates with the multi-task state-conditioned MPNN
3. Score candidates with GNINA docking against each state's representative structure
4. Apply the unified scoring function (ranking/scoring.py) with identical weights
5. Compute enrichment factors EF@1, EF@5, EF@10 for held-out approved drugs
6. Compare state-aware pipeline (4 states, best-state scoring) vs static pipeline (single best-resolution structure)

**Step D2: Pooled Multi-Kinase Statistical Analysis**

**Primary test**: Paired Wilcoxon signed-rank test on per-kinase EF@10 values (state-aware vs static).
- H0: Median EF_state_aware <= Median EF_static
- H1: Median EF_state_aware > Median EF_static
- N = 5 paired observations (one per kinase)
- With the expected ~10x enrichment ratio, power ~0.85 at alpha=0.05

**Secondary test**: Bootstrap meta-analysis of pooled enrichment.
- Pool all held-out drugs across kinases (N~22 for pre-2010, N~15 for pre-2015)
- Compute pooled EF@10 with 10,000 bootstrap resamples
- Report 95% BCa (bias-corrected and accelerated) confidence intervals
- Expected CI width: ~3.5 units (vs ~8.5 for EGFR alone -- 59% narrower)

**Heterogeneity analysis**: Compute I^2 statistic across kinases to quantify whether enrichment effects are consistent or kinase-dependent. If I^2 > 50%, report random-effects pooled estimate. If I^2 < 25%, the effect is homogeneous and the general claim is strongest.

**Per-kinase subgroup analysis**: Report individual kinase EF@10 with CIs. Identify whether enrichment correlates with:
- Number of conformational states observed experimentally
- Structural diversity of states (RMSD between DFGin and DFGout representatives)
- ChEMBL data volume
- Fraction of AF2-generated vs experimental structures in the atlas

**Step D3: DFG-Out Selectivity Hypothesis Test**

This is the formal statistical test of the claim that state-aware DFG-out generation produces more selective molecules.

**Protocol**:
1. From the multi-task MPNN, predict pIC50 for all generated candidates against all 5 kinases
2. For each candidate, compute a selectivity profile: Gini coefficient across the 5-kinase panel
3. Partition candidates by their design state: DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout
4. Compare Gini coefficient distributions:
   - H0: Mean Gini (DFGout-designed) = Mean Gini (DFGin-designed)
   - H1: Mean Gini (DFGout-designed) > Mean Gini (DFGin-designed)
   - Test: Two-sample t-test (or Mann-Whitney U if non-normal) with Bonferroni correction
5. Expected effect size: Delta Gini ~0.15-0.20 based on the Ung et al. (2015) experimental data (Type II mean 0.72 vs Type I mean 0.51)

**Validation against PKIS2/KCGS**:
1. Download PKIS2 selectivity data (Wells et al., PLOS One 2017): 645 compounds profiled at 392 kinases
2. For PKIS2 compounds with known binding modes (Type I vs Type II from co-crystal structures), compute:
   - Predicted Gini using the multi-task MPNN
   - Measured Gini from the PKIS2 selectivity matrix
3. Test correlation: Spearman rho between predicted and measured Gini
4. Stratify by binding mode: Does the model correctly predict higher selectivity for Type II compounds?
5. Repeat with KCGS 2.0 (295 compounds, 262 kinases) as independent validation

**Step D4: Cross-Kinase Enrichment Correlation Analysis**

Test the mechanistic hypothesis that enrichment advantage scales with conformational state diversity:

| Kinase | N Experimental States | State RMSD Diversity | Predicted Enrichment Rank |
|--------|----------------------|---------------------|--------------------------|
| EGFR | 4 (all experimental) | High (~4.5 A DFGin-DFGout) | 1 (highest) |
| ABL1 | 4 (all experimental) | High (~4.2 A) | 2 |
| BRAF | 3-4 (mostly experimental) | Moderate (~3.8 A) | 3 |
| JAK2 | 2-3 (some AF2) | Moderate (~3.5 A) | 4 |
| ALK | 2-3 (some AF2) | Lower (~3.0 A) | 5 (lowest) |

Compute Spearman rank correlation between state structural diversity metrics and EF@10 improvement (state-aware minus static). If rho > 0.8 with p < 0.05 (even with N=5), this provides mechanistic support that the method works because of conformational state information, not despite it.

---

## Impact Assessment

### Publication Impact

**Target venue**: Nature Computational Science

**Why this venue**: Nature Computational Science publishes work that demonstrates a general computational principle with broad impact. A single-kinase case study is insufficient, but a 5-kinase validation with statistical rigor, a selectivity hypothesis test, and an open-source framework matches their scope. Recent precedents: AlphaFold2 drug discovery applications, geometric deep learning for molecular property prediction, and de novo molecular generation papers have appeared here.

**Paper structure**:
- **Title**: "Conformational State-Aware Molecular Design Generalizes Across the Kinome"
- **Figure 1**: Multi-kinase state atlas visualization (5 kinases x 4 states = 20 pocket structures, colored by state)
- **Figure 2**: Per-kinase enrichment factor comparison (state-aware vs static, forest plot with CIs)
- **Figure 3**: Pooled meta-analysis of enrichment with bootstrap CIs
- **Figure 4**: DFG-out selectivity analysis (Gini distributions by design state, PKIS2 validation)
- **Figure 5**: Multi-task MPNN performance (per-kinase R^2, transfer learning gains, state conditioning ablation)
- **Main claim**: "Conformational state-aware molecular design produces 3-10x higher retrospective enrichment than static single-structure design across 5 kinases and generates more selective molecules for inactive-state pockets"
- **Supplementary**: Per-kinase data curation details, AF2-MSM validation, all individual enrichment curves, KCGS validation

**Reviewer concerns and preemptive responses**:

| Expected Criticism | Response |
|-------------------|----------|
| "Only 5 kinases" | 5 kinases across 3 kinase groups (TK: EGFR/ABL1/ALK, TKL: BRAF, JAK: JAK2) with 20+ held-out drugs. Power analysis shows adequate power (~0.85). |
| "No experimental validation" | Retrospective validation with approved drugs is the strongest computational evidence. Explicit acknowledgment in limitations. Relay Therapeutics validates the general approach commercially. |
| "AF2 structures for some states" | AF2-MSM validated by Song et al. 2024 with docking AUC >= 0.79. We flag AF2 vs experimental provenance and test whether enrichment correlates with structure quality. |
| "MPNN accuracy limited" | Published R^2 = 0.5-0.7 for well-studied kinases. We use selectivity ratios (Delta pIC50), which are more robust than absolute values. Uncertainty quantification included. |
| "Selectivity from 5-kinase panel is narrow" | PKIS2/KCGS validation against 392/262-kinase panels provides broader context. The 5-kinase MPNN is a proof of concept; the principle extends to larger panels. |
| "Mean score gap favors static" | Explicitly address: the static mean-score advantage (0.5437 vs 0.4378) reflects reference similarity bias to 3 known EGFR drugs. The enrichment metric (which asks "does the method find approved drugs?") is the correct evaluation. |

**Fallback venue**: JCIM (with 3-kinase minimum viable version if the full 5-kinase analysis encounters data quality issues for ALK or JAK2).

### Effort Estimate

| Component | Duration | Personnel | Compute (GPU-days on H200) |
|-----------|----------|-----------|---------------------------|
| A: Data Curation | 2.5 weeks | 1 researcher | 0 (CPU only) |
| B: State Atlas | 2 weeks (overlaps with A) | 1 researcher | 2 (AF2-MSM generation) |
| C: Multi-task MPNN | 4 weeks | 1 researcher | 8 (training + ablations + baselines) |
| D: Validation & Stats | 4 weeks (overlaps with C) | 1 researcher | 10 (GNINA docking, 5 kinases x 4 states) |
| Writing | 2 weeks | 1 researcher | 0 |
| **Total** | **10-14 weeks** | **1 researcher** | **~20 GPU-days** |

**Compute breakdown**:
- MPNN training: 5 kinases x 2 time splits x 3 model variants (baselines + proposed) x 2 hours = ~60 GPU-hours = ~2.5 GPU-days
- GNINA docking: 5 kinases x 4 states x 4000 candidates x ~30 seconds/compound = ~333 GPU-hours = ~14 GPU-days
- AF2-MSM generation: 2 kinases x 50 models x ~0.5 GPU-hours = ~50 GPU-hours = ~2 GPU-days
- Bootstrap/statistical analysis: ~1 GPU-day
- Total: ~20 GPU-days on H200 nodes (gpu_h200 partition, `--gpus=h200:1`)

SLURM strategy: Submit GNINA docking as array jobs (`--array=0-19`, one per kinase-state combination) on the `gpu` partition with `--gpus=rtx_5000_ada:1` to maximize throughput. MPNN training on `gpu_h200` for faster convergence.

### Risk Assessment

**High risk, high mitigation**:
- *Enrichment does not generalize to all 5 kinases*: This is the central scientific risk. Mitigation: even if 2 of 5 kinases show no enrichment, the heterogeneity analysis (I^2 statistic) reveals this honestly, and 3/5 positive results are still publishable with appropriate framing ("generalizes to kinases with rich conformational data").
- *ALK/JAK2 data sparsity causes poor MPNN performance*: Multi-task transfer learning specifically addresses this. If single-task R^2 < 0.3 for a kinase, the multi-task improvement is the story.

**Medium risk**:
- *AF2-MSM DFG-out structures are poor quality for ALK/JAK2*: Validate with GNINA re-docking of known inhibitors before using in pipeline. If docking AUC < 0.70, fall back to experimental DFGin structures only (reduces from 4-state to 2-state analysis for affected kinases).
- *PKIS2/KCGS selectivity data does not correlate with MPNN predictions*: The selectivity component becomes negative result. Publish as "multi-kinase enrichment generalizes but selectivity prediction requires broader training panels."

**Low risk**:
- *ChEMBL data curation problems*: Well-established protocols exist. StateBind's EGFR curation is the template.
- *Compute availability*: 20 GPU-days is modest for Yale Bouchet (9 H200 nodes, 8 GPUs each = 72 H200s available).

---

## Evaluation Criteria

The proposal succeeds if it achieves the following measurable outcomes:

1. **Multi-kinase enrichment** (primary): State-aware EF@10 > static EF@10 for >= 4 of 5 kinases, with pooled bootstrap 95% CI excluding 1.0 (i.e., the lower bound of the CI is above chance enrichment).

2. **Statistical power** (primary): Paired Wilcoxon test p < 0.05 for the state-aware vs static comparison across 5 kinases.

3. **CI narrowing** (primary): Pooled enrichment 95% CI width < 4.0 units (vs ~8.5 for EGFR alone).

4. **Multi-task MPNN improvement** (secondary): Multi-task R^2 > single-task R^2 for at least 3 of 5 kinases, with largest improvements on data-sparse kinases (ALK, JAK2).

5. **State conditioning improvement** (secondary): State-conditioned multi-task R^2 > unconditioned multi-task R^2 on state-specific test sets.

6. **DFG-out selectivity** (secondary): DFGout-designed candidates have significantly higher predicted Gini coefficients than DFGin-designed candidates (p < 0.01, effect size Delta Gini > 0.10).

7. **PKIS2/KCGS validation** (tertiary): Spearman rho > 0.3 between predicted and measured Gini coefficients for the overlapping compound set.

8. **Mechanistic correlation** (tertiary): Enrichment improvement correlates with conformational state diversity across kinases (Spearman rho > 0.6).

---

## Open Questions

1. **State assignment for training compounds**: Most ChEMBL compounds lack co-crystal structures. The proposal assigns states based on compound class (Type I -> DFGin, Type II -> DFGout), but this is an approximation. How sensitive are the results to misassignment? A sensitivity analysis varying the assignment noise (10%, 20%, 30% random state reassignment) should quantify this.

2. **Cross-kinase normalization of state features**: The 9D feature vectors must be comparable across kinases. Should we normalize per-kinase (preserving within-kinase relative differences) or globally (enabling cross-kinase comparisons)? The answer affects whether the MPNN learns kinase-specific or kinase-general state effects. Recommend testing both.

3. **Kinase group confounding**: EGFR, ABL1, and ALK are all tyrosine kinases. BRAF is a serine/threonine kinase (TKL group). JAK2 is a tyrosine kinase but with a pseudokinase domain. Is the enrichment effect driven by the TK group specifically, or does it generalize across kinase groups? The 5-kinase panel includes some diversity but ideally would include a CMGC or AGC kinase. CDK2 (CMGC, 400+ structures, but no approved inhibitor) could be added as a 6th kinase with a modified validation protocol using clinical candidates instead of approved drugs.

4. **Selectivity panel breadth**: A 5-kinase MPNN predicts selectivity across only 5 kinases. Real selectivity profiling uses 400+ kinases. Is a 5-kinase Gini coefficient meaningful? The PKIS2/KCGS validation partially addresses this, but the core selectivity claim should be framed carefully as "within-panel selectivity" rather than "kinome-wide selectivity."

5. **Continuous vs discrete states**: StateBind uses 4 discrete conformational states. Some kinases (especially CDK2) exhibit a continuum of conformations rather than discrete clusters. Does the discrete-state assumption break down for these kinases? This is a known limitation but not addressed in this proposal -- it is better suited for a separate follow-up study.

6. **Multi-task loss balancing**: The proposed inverse-frequency weighting (Section C2) is standard but may not be optimal. Uncertainty-weighted multi-task learning (Kendall et al., CVPR 2018) or GradNorm (Chen et al., ICML 2018) could improve balance. Worth testing if the baseline weighting produces poor results on any single kinase.

7. **Independence from EGFR**: Since the method was originally developed and tuned on EGFR, there is a risk of overfitting to EGFR-specific characteristics. Should EGFR be excluded from the multi-kinase analysis and used only as a positive control? This would make the generalization claim stronger but reduces statistical power. Recommend including EGFR in the pooled analysis but also reporting the 4-kinase (excluding EGFR) result separately.

---

## References

1. Chen, J., et al. "Kinome-wide polypharmacology profiling of small molecules by multi-task graph isomorphism network approach." *J Chem Inf Model* 63(8), 2496-2508 (2023).
2. Chen, Z., Badrinarayanan, V., Lee, C.Y., Zisserman, A. "GradNorm: Gradient normalization for adaptive loss balancing in deep multitask networks." *ICML* (2018).
3. Davis, M.I., et al. "Comprehensive analysis of kinase inhibitor selectivity." *Nature Biotechnology* 29(11), 1046-1051 (2011).
4. Elkins, J.M., et al. "The Kinase Chemogenomic Set (KCGS): An open science resource for kinase vulnerability identification." *Int J Mol Sci* 22(2), 566 (2021).
5. Fabian, M.A., et al. "A small molecule-kinase interaction map for clinical kinase inhibitors." *Nature Biotechnology* 23(3), 329-336 (2005).
6. Fang, Z., et al. "DFG-1 residue controls inhibitor binding mode and affinity, providing a basis for rational design of kinase inhibitor selectivity." *J Med Chem* 63(21), 13124-13143 (2020).
7. Heid, E., et al. "Chemprop: A machine learning package for chemical property prediction." *J Chem Inf Model* 64(1), 9-17 (2024).
8. Karaman, M.W., et al. "A quantitative analysis of kinase inhibitor selectivity." *Nature Biotechnology* 26(1), 127-132 (2008).
9. Kendall, A., Gal, Y., Cipolla, R. "Multi-task learning using uncertainty to weigh losses for scene geometry and semantics." *CVPR* (2018).
10. Kooistra, A.J., et al. "KLIFS: an overhaul after the first 5 years of supporting kinase research." *Nucleic Acids Research* 49(D1), D562-D569 (2021).
11. Li, Z., et al. "Large-scale comparison of machine learning methods for profiling prediction of kinase inhibitors." *J Cheminformatics* 16, 20 (2024).
12. Martin, E., et al. "Large-scale modeling of sparse protein kinase activity data." *J Chem Inf Model* 63(11), 3451-3465 (2023).
13. Merget, B., et al. "Successive statistical and structure-based modeling to identify chemically novel kinase inhibitors." *J Chem Inf Model* 60(1), 310-323 (2020).
14. Miljkovic, F., et al. "Analyzing kinase similarity in small molecule and protein structural space to explore the limits of multi-target screening." *Molecules* 26(3), 629 (2021).
15. Ren, Q., et al. "KinomeMETA: meta-learning enhanced kinome-wide polypharmacology profiling." *Briefings in Bioinformatics* 25(1), bbad461 (2024).
16. Reveguk, I., et al. "Classifying protein kinase conformations with machine learning." *Protein Science* 33(3), e4918 (2024).
17. Roskoski, R. "Properties of FDA-approved small molecule protein kinase inhibitors: A 2025 update." *Pharmacological Research* 200, 107483 (2025).
18. Soda, M., et al. "Identification of the transforming EML4-ALK fusion gene in non-small-cell lung cancer." *Nature* 448, 561-566 (2007).
19. Soleimany, A.P., et al. "Evidential deep learning for guided molecular property prediction and discovery." *ACS Cent Sci* 7(8), 1356-1367 (2021).
20. Song, Y., et al. "A comprehensive exploration of the druggable conformational space of protein kinases using AI-predicted structures." *PLOS Computational Biology* 20(8), e1012302 (2024).
21. Ung, P.M.U., et al. "Conformational analysis of the DFG-out kinase motif and biochemical profiling of structurally validated Type II inhibitors." *J Med Chem* 58(4), 1569-1585 (2015).
22. Wells, C.I., et al. "Progress towards a public chemogenomic set for protein kinases and a call for contributions." *PLOS One* 12(8), e0181585 (2017).
23. Sydow, D., et al. "KiSSim: Predicting off-targets from structural similarities in the kinome." *J Chem Inf Model* 62(10), 2600-2616 (2022).
24. Uitdehaag, J.C.M., et al. "A guide to picking the most selective kinase inhibitor tool compounds for pharmacological validation of drug targets." *British Journal of Pharmacology* 166(3), 858-876 (2012).
25. Klaeger, S., et al. "The target landscape of clinical kinase drugs." *Science* 358, eaan4368 (2017).
