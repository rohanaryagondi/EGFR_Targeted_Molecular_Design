---
agent: Orchestrator
round: 1
date: 2026-04-09
type: roundtable
---

# Round 1 Synthesis: Deep Research Findings Across 7 Specialists

## Executive Summary

Seven domain specialists conducted independent deep research (4,800+ total lines,
190+ citations) across drug strategy, biophysics, cheminformatics, clinical oncology,
protein ML, kinome pharmacology, and benchmarking. Six major convergence themes
emerged, along with two productive tensions. This synthesis identifies 5 proposal
directions for Round 2.

---

## Theme 1: The Type II EGFR Gap Is StateBind's Strongest Argument

**Converging agents:** drughunt, clinonc, biophys, kinpharm

The single most striking finding across all agents: **zero approved type II (DFGout)
EGFR inhibitors exist.** Every approved EGFR TKI (erlotinib, gefitinib, osimertinib,
afatinib, dacomitinib, lazertinib, mobocertinib) binds the DFG-in active conformation.
Meanwhile, 9+ approved type II inhibitors exist for other kinases (imatinib, sorafenib,
etc.).

This creates a three-pronged argument for StateBind:

1. **Clinical (clinonc):** C797S resistance (7-29% of osimertinib patients) eliminates
   the covalent anchor used by all current TKIs. DFGout inhibitors bypass this
   resistance by binding a pocket that doesn't depend on Cys797. No DFGout EGFR
   candidate exists in any clinical pipeline.

2. **Kinetic (biophys):** DFGout inhibitors have 10-100x longer residence times than
   DFGin (lapatinib 430 min vs gefitinib <14 min). Residence time predicts in vivo
   efficacy better than equilibrium affinity (Copeland paradigm, K4DD consortium).

3. **Selectivity (kinpharm):** The DFGout pocket is less conserved across the kinome
   (Gini coefficient 0.64-0.80 for type II vs 0.49-0.52 for type I, p < 10^-4).
   State-aware DFGout design inherently produces more selective molecules.

**Publication impact:** StateBind is the first computational framework that explicitly
designs molecules for DFGout EGFR conformations. This is genuinely novel and
clinically relevant.

---

## Theme 2: Multi-Kinase Extension Is the Path to Nature Computational Science

**Converging agents:** kinpharm, drughunt, bencharch, clinonc

All four agents independently concluded that single-target (EGFR-only) validation
limits the publication to JCIM-level impact. Multi-kinase validation transforms a
case study into a general finding.

**Key data (kinpharm):**
- ABL1 ranked #1 extension target: 350+ PDB structures, 6 approved drugs (2001-2021),
  4 KLIFS-annotated conformational states, 5,200+ ChEMBL compounds
- Recommended first panel: ABL1, BRAF, ALK, JAK2, SRC
- Expanding from 1 to 5 kinases: CIs narrow ~59%, statistical power reaches ~0.85
- Combined held-out drugs: 20+ (vs 3-5 for EGFR alone)

**Validation resources identified (kinpharm):**
- PKIS2: 645 compounds profiled at 392 kinases (open data)
- KCGS 2.0: 295 narrow-spectrum compounds (open data)
- HMS LINCS KINOMEscan: selectivity profiles for EGFR drugs
- AF2-MSM: 6,297 predicted structures covering 398 kinases in previously unobserved
  conformations

**Compute estimate:** 4-6 weeks, ~5-20 GPU-days on H200.

---

## Theme 3: The Mean-Score Gap Is a Representation Artifact, Not a Scientific Failure

**Converging agents:** cheminfo, clinonc, drughunt

The cheminformatician's analysis is definitive: the mean-score gap (static 0.5437 vs
state-aware 0.4378, delta = 0.1059) is **more than fully explained** by the
reference_similarity component (35% weight, Morgan/Tanimoto to only 3 drugs).

**Quantitative decomposition (cheminfo):**
- Static reference_similarity contribution: ~0.35 * 0.7 = 0.245
- State-aware contribution: ~0.35 * 0.3 = 0.105
- Delta from reference_similarity alone: 0.140 (exceeds total gap of 0.1059)
- **State-aware wins on the other 3 components combined**

**Mitigations with estimated impact:**
- Expanded reference set (3 drugs -> 100-300 ChEMBL centroids): 50-70% gap reduction
- Tversky similarity (substructure-biased): 30-50% gap reduction
- PheSA (3D shape+pharmacophore): 40-60% gap reduction

**Benchmark context (cheminfo):** The 62,820-model mega-benchmark (Deng et al., 2023)
found Morgan/ECFP + RF still competitive with deep learning on moderate datasets. But
Morgan/Tanimoto to 3 references is a far more limited application than Morgan for
activity prediction. The scoring function penalizes novelty by design.

**Publication framing:** Report the gap transparently, then demonstrate it's an artifact
of scoring function design (similarity to 3 known drugs), not a failure of state-aware
generation. The enrichment factor (10x) is the true measure of prospective discovery value.

---

## Theme 4: No Conformational-State Benchmark Exists -- First-Mover Opportunity

**Lead agent:** bencharch

Systematic search across 12+ benchmark databases confirmed: **no benchmark for
conformational state-conditioned molecular generation exists anywhere.**

**Existing benchmarks and their gaps:**
- CrossDocked2020: multiple structures per protein, but no state annotations
- MOSES/GuacaMol: 2D generation, no target conditioning, saturated metrics
- MoleculeNet: tiny molecules (mean MW 203.9 Da), irrelevant to drug design
- TDC: 2026 audit found only 3 top-ranked methods reproducible
- KLIFS: structural database, not a generation benchmark

**Benchmark impact (bencharch):**
- MoleculeNet: ~3,000+ citations in 8 years
- Conservative projection for StateBind-Bench: 500-1,000 citations in 3-5 years
- Benchmark papers have 5-15x the citation impact of methods papers

**Proposed structure:** 4 tasks (state-conditioned generation, state specificity,
retrospective enrichment, multi-objective optimization) with open data on HuggingFace,
evaluation scripts, Docker containers, and baseline comparisons against REINVENT 4,
DiffSBDD, TargetDiff, Pocket2Mol.

**Venue target:** NeurIPS 2026 Evaluations & Datasets Track (deadline May 6, 2026)
or JCIM.

---

## Theme 5: Protein Language Models Offer Targeted Upgrades, Not Wholesale Replacement

**Lead agent:** protml, with supporting evidence from cheminfo

The protein ML expert identified a critical nuance: **ESM-2 is sequence-only and
cannot distinguish conformational states of the same protein.** ProstT5 (structure-
conditioned with 3Di tokens) is the right model for state discrimination.

**Key findings:**
- ESM-2 pocket embeddings (1280D) capture druggability (AUC 0.81) but not conformation
- ProstT5 processes 3D structure tokens, enabling state-specific embeddings
- DrugCLIP (Science 2025): 10M-fold faster than docking, 17.5% experimental hit rate,
  AUROC 80.93% on DUD-E
- Uni-Mol pre-training improves property prediction 20-59% over from-scratch training

**Critical tension with cheminfo:** The 62,820-model mega-benchmark shows ECFP+RF
still competitive with deep learning on moderate datasets. The protml agent's strongest
case is for pre-trained molecular representations (Uni-Mol), not necessarily replacing
the ECFP-based scoring. The two perspectives complement: use learned representations
for binding prediction (where pre-training helps) while keeping fingerprints for
chemical space analysis (where they're proven).

**Minimal experiment (protml):** <4 GPU-hours on H200 to compare ESM-2/ProstT5 pocket
embedding state separation against 9D features.

---

## Theme 6: Kinetic Scoring and Experimental Validation Design

**Lead agent:** biophys

The biophysicist proposed a concrete 5th scoring component and validation experiments:

**Proposed kinetic scoring (10% weight):**
- 3-tier cascade: tauRAMD (best) -> ML koff (medium) -> state-kinetic heuristic (fallback)
- DFGout binders: 0.7, DFGin/aCout: 0.5, DFGin/aCin: 0.3
- Creates positive feedback with state_specificity component

**The conformational selection narrative (zero-compute):**
State-aware design targeting DFGout states *implicitly selects for long residence
time* because DFGout inhibitors bind through conformational selection (slow kon, very
slow koff). The 10x enrichment can be reframed as implicit kinetic optimization. This
is publication-ready and requires no new computation.

**Experimental validation designs:**
- SPR 10-compound panel: $10-20K in-house, $33-52K CRO, 4 weeks
- HDX-MS conformational validation: $30-50K, 6-8 weeks
- Both would directly validate StateBind's central hypothesis

---

## Key Precedent: Relay Therapeutics

**Agent:** drughunt

Relay Therapeutics' Dynamo platform produces conformation-selective inhibitors using
cryo-EM + MD simulations. Their lead compound zovegalisib (RLY-2608, PI3Ka) entered
Phase 3 in mid-2025 with 11.0-month mPFS. Relay's $3.5B+ valuation validates the
conformational state-aware paradigm commercially.

**Framing for StateBind:** Open-source, ML-based, reproducible alternative to Relay's
proprietary platform. Same principle (conformational state-awareness improves drug
design), different execution (generative ML vs physics-based).

---

## Cross-Agent Tensions (Productive Disagreements)

### Tension 1: Publication Venue
- **drughunt:** Nature Comp Sci (requires multi-kinase extension)
- **clinonc:** JCIM/JMC (computational methodology, not clinical claims)
- **bencharch:** NeurIPS E&D Track (benchmark framing) or JCIM

**Resolution:** These are not mutually exclusive. The strongest strategy is a
**dual-publication approach**:
- Paper 1: Methods + multi-kinase validation paper (Nature Comp Sci or JCIM)
- Paper 2: Benchmark + community resource paper (NeurIPS E&D or JCIM)

### Tension 2: ML Upgrade Priority
- **protml:** Replace 9D features with pLM embeddings, upgrade MPNN with Uni-Mol
- **cheminfo:** ECFP still competitive; focus on scoring reform (metrics, references)

**Resolution:** Both are right for different problems. pLM embeddings help with
state discrimination and mutation coverage (protml's strengths). Scoring reform
(expanded references, multi-metric similarity) helps explain the mean-score gap and
produce publication figures (cheminfo's strengths). Do both -- they're complementary
and each requires modest compute.

---

## Proposal Directions for Round 2

Based on convergence themes, I identify 5 proposal directions:

| # | Title | Lead Agent | Core Argument |
|---|-------|-----------|---------------|
| P1 | Multi-Kinase Retrospective Validation | kinpharm | Extend to 5 kinases, transform case study into general finding |
| P2 | StateBind-Bench Open Benchmark | bencharch | First conformational-state generation benchmark, community resource |
| P3 | Scoring Reform + Chemical Space Analysis | cheminfo | Multi-metric similarity, expanded references, publication figures |
| P4 | Resistance-Informed State-Aware Design | clinonc | C797S mutant structures via AlphaFold, DFGout targeting |
| P5 | Kinetic Scoring + Conformational Selection Narrative | biophys | 5th scoring component, zero-compute kinetic reframing |

**drughunt** serves as strategic advisor (TPP, competitive landscape, venue framing)
for all proposals. **protml** contributes pLM integration details to P3 and P4.

---

## Priority Ranking

1. **P1 (Multi-Kinase)** -- Highest impact for Nature Comp Sci. Addresses the #1
   reviewer concern (generalizability) and the #1 statistical weakness (small N).
2. **P3 (Scoring Reform)** -- Essential for honest publication. Explains the mean-score
   gap, produces required figures, and addresses the "only 3 references" criticism.
3. **P2 (Benchmark)** -- Highest long-term citation impact. First-mover in unclaimed
   niche. Can be a separate publication.
4. **P5 (Kinetic Narrative)** -- Zero-compute, publication-ready. Strengthens the
   story without any new code. Kinetic scoring component adds discriminative power.
5. **P4 (Resistance Design)** -- Strongest translational argument but requires
   AlphaFold structure prediction for mutants (some risk).
