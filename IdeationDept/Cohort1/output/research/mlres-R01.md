---
agent: Senior ML Researcher
round: 1
date: 2026-04-08
type: research-note
topic: Publication strategy, external baselines, conformation-conditioned generation landscape, foundation model opportunities, enrichment validation, ablation design, and multi-target generalization for StateBind
---

# Research Note: StateBind Publication Readiness -- ML Landscape, Baselines, and Strategic Positioning

## Summary

This research note surveys the 2024--2026 ML and computational drug design landscape to determine StateBind's optimal publication strategy. The findings are sobering but constructive: StateBind's **question** (does conformational state-awareness improve molecular design?) remains timely and under-explored, but its **ML stack** (GRU-based SELFIES VAE, NNConv MPNN, GIN ADMET) is 4--6 years behind the current state of the art. The good news is that the framing as a **benchmark/framework paper** rather than a method paper sidesteps the architecture gap. The bad news is that external baselines are non-negotiable for any credible venue, and the retrospective validation on N=3--5 drugs is statistically fragile without multi-target expansion.

Key conclusions:

1. **Best venue: JCIM or Nature Computational Science**, framed as a benchmark study. NeurIPS/ICML are not viable without architectural novelty.
2. **Critical gap: zero external baselines.** REINVENT 4 and DiffSBDD are the two most feasible to run on the same EGFR task. Both have open-source code and pretrained models.
3. **The 10x enrichment headline is compelling but fragile.** Multi-kinase expansion (3--5 kinases) would transform it from a single-target anecdote to a generalizable finding.
4. **Foundation model integration is a high-leverage upgrade.** Uni-Mol pocket representations or ESM-2 protein embeddings could replace StateBind's hand-crafted 9D features with minimal code changes.
5. **Two new benchmarks (Durian, Kinase-Bench) provide ready-made evaluation infrastructure** that reviewers would expect StateBind to engage with.
6. **1D/2D methods remain competitive with 3D methods** in recent comprehensive benchmarks, which validates StateBind's SELFIES-based approach more than expected.

---

## Research Questions

1. What venue should StateBind target, and what framing survives peer review at that venue?
2. Which external baselines are required, and which are feasible to run on EGFR within months?
3. Is conformation-conditioned molecular generation a novel contribution, or has it been done?
4. Can foundation models provide drop-in improvements to StateBind's ML components?
5. How should the retrospective enrichment claim be statistically validated?
6. What ablation design isolates the state-conditioning contribution from confounds?
7. Does multi-target generalization strengthen the paper enough to change venue tier?

---

## Methods

### Sources Consulted

- Nature Computational Science (2024--2026 publications on molecular generation)
- Journal of Chemical Information and Modeling (2024--2025 benchmarking papers)
- NeurIPS 2024--2025, ICML 2024--2025 proceedings (molecular generation track)
- arXiv preprints (2024--2026, molecular generation and drug design)
- PubMed (biomedical literature on kinase conformational states and drug design)
- GitHub repositories (REINVENT4, DiffSBDD, TargetDiff, Pocket2Mol, mol_opt/PMO)
- TDC (Therapeutics Data Commons) ADMET leaderboards
- CrossDocked2020, Durian, and Kinase-Bench benchmark datasets

### Search Strategy

Conducted 20+ targeted web searches, fetched 10+ specific pages for quantitative data extraction, and queried PubMed for biomedical literature. Searches covered: conformational state-conditioned generation, external baseline benchmarks, foundation models for molecules, enrichment factor statistics, multi-target validation, ablation best practices, and venue-specific publication requirements.

---

## Findings

### Finding 1: Venue Analysis -- JCIM or Nature Computational Science, Not NeurIPS

**Nature Computational Science** published DiffSBDD in December 2024 (Schneuing et al., Nat. Comput. Sci., 2024), PropMolFlow, ECloudGen, and SynGFN in 2025, and a pharmacophore-oriented 3D generation method in 2025. The journal favors papers that: (a) introduce a framework with broad applicability, (b) demonstrate biological relevance beyond benchmark numbers, (c) tell a clear narrative about why the approach matters. StateBind fits this if framed as "Does conformational awareness improve molecular design? A systematic benchmark across kinase conformational states."

**JCIM** published the Durian benchmark (Nie et al., JCIM, 2025), the GSK SBDD benchmarking study (JCIM, 2025), Kinase-Bench (JCIM, 2024), and multiple conformational analysis papers. JCIM reviewers are computational chemists who value: domain depth, proper chemistry baselines, practical applicability, and reproducibility. StateBind's detailed scoring function, docking cascade, and retrospective validation speak this language.

**NeurIPS/ICML** require methodological novelty. A GRU-based SELFIES VAE is a 2019-era architecture by ML standards. The PMO benchmark (Gao et al., NeurIPS 2022 D&B) showed that REINVENT and Graph GA -- methods from 2017--2019 -- still outperform many "state-of-the-art" methods. However, NeurIPS reviewers would view StateBind's ML stack as a limitation rather than a feature. The NeurIPS Datasets & Benchmarks track is a possibility only if StateBind releases a multi-kinase benchmark dataset and evaluation suite.

**Key data points:**
- Nature Comp. Sci. published 5+ molecular generation papers in 2024--2025
- JCIM published 3 major SBDD benchmarking papers in 2024--2025 (Durian, GSK benchmark, Kinase-Bench)
- NeurIPS D&B track grew from 910 papers (2023) to 1,995 (2025)

**Relevance to StateBind:** Target JCIM as the primary venue. Nature Comp. Sci. is aspirational but requires multi-target generalization and at least one external 3D baseline. NeurIPS D&B is viable only with a released benchmark dataset.

**Reviewer concerns by venue:**

| Venue | Likely Reviewer Concern | Mitigation |
|-------|------------------------|------------|
| JCIM | "No external baselines" | Run REINVENT 4 + DiffSBDD on same EGFR task |
| JCIM | "N=3-5 for enrichment" | Multi-kinase expansion or bootstrap CIs |
| JCIM | "Outdated VAE" | Frame as benchmark, not method |
| Nat. Comp. Sci. | "Single target, not general" | Must add 2+ kinases |
| Nat. Comp. Sci. | "No 3D baseline comparison" | Must run DiffSBDD |
| NeurIPS D&B | "No released dataset/code" | Must package as benchmark resource |

---

### Finding 2: External Baseline Landscape -- REINVENT 4 and DiffSBDD Are the Critical Comparisons

The PMO benchmark (Gao et al., NeurIPS 2022) evaluated 25 molecular optimization methods across 23 tasks. The headline result: **REINVENT and Graph GA consistently ranked as top performers**, despite being released years before many "state-of-the-art" competitors. Under a 10K oracle budget, most newer methods failed to outperform these older approaches.

**REINVENT 4** (Loeffler et al., J. Cheminform., 2024):
- Open source (Apache-2.0 license), GitHub: MolecularAI/REINVENT4
- Supports de novo design, scaffold hopping, R-group replacement, linker design, molecular optimization
- Uses RNN and Transformer architectures with RL-based optimization
- Scoring supports 30+ components including AutoDock Vina, Glide, GOLD docking
- ~8 GB memory requirement, runs on CPU or GPU
- PDK1 kinase demo: 3.5% hit rate from transfer learning variant
- **Feasibility for StateBind:** HIGH. Can define EGFR-specific scoring profile using Vina docking against the same 4 EGFR structures. Would require 1--2 weeks to set up and run.

**DiffSBDD** (Schneuing et al., Nat. Comput. Sci., 2024):
- Open source on GitHub: arneschneuing/DiffSBDD
- SE(3)-equivariant diffusion model for structure-based drug design
- Pretrained models available on Zenodo for CrossDocked2020
- Supports de novo generation, inpainting, and property optimization
- Benchmark: Vina Score avg -2.71, Vina Dock avg -6.51 on CrossDocked2020 (BInD paper data)
- QED 0.49, SA 0.62, Diversity 0.79
- Inference: ~2.5 sec/compound (41 min for 1000)
- **Feasibility for StateBind:** MODERATE. Need to prepare EGFR pockets in compatible format. Pretrained model may not be EGFR-specific. Could generate molecules per pocket and evaluate with StateBind's scoring function.

**TargetDiff** (Guan et al., ICLR 2023):
- Open source on GitHub: guanjq/targetdiff
- 3D equivariant diffusion model
- Benchmark: Vina Dock avg -7.46, QED 0.49, SA 0.61, Diversity 0.74 on CrossDocked2020
- **Feasibility for StateBind:** MODERATE. Similar setup requirements to DiffSBDD.

**Pocket2Mol** (Peng et al., ICML 2022):
- Autoregressive model, highest QED (0.57) and SA (0.74) among 3D methods
- Vina Dock avg -7.43, Diversity 0.73
- 81.2% MOSES validity pass rate (highest among 3D DL methods per GSK benchmark)
- **Feasibility for StateBind:** MODERATE-HIGH. Well-documented codebase.

**Key comparison table (CrossDocked2020 benchmark, from BInD paper):**

| Method | Vina Score | Vina Dock | QED | SA | Diversity | Type |
|--------|-----------|-----------|-----|-----|-----------|------|
| Pocket2Mol | -5.13 | -7.43 | 0.57 | 0.74 | 0.73 | Autoregressive |
| TargetDiff | -5.11 | -7.46 | 0.49 | 0.61 | 0.74 | Diffusion |
| DiffSBDD | -2.71 | -6.51 | 0.49 | 0.62 | 0.79 | Diffusion |
| DecompDiff | -3.91 | -8.51 | 0.49 | 0.61 | 0.74 | Diffusion |
| BInD | -5.64 | -7.46 | 0.50 | 0.65 | 0.75 | Diffusion |
| **StateBind VAE** | **N/A (1D)** | **GNINA proxy** | **varies** | **varies** | **0.91** | **SELFIES VAE** |

**Relevance to StateBind:** The minimum viable baseline set is: (1) REINVENT 4, (2) one 3D method (DiffSBDD or Pocket2Mol), (3) random generation (VAE without state conditioning), (4) fingerprint similarity search. REINVENT 4 is the highest priority because it is the most widely used molecular optimization tool and JCIM reviewers will specifically ask for it.

---

### Finding 3: Conformation-Conditioned Generation Is Under-Explored -- StateBind Has a Novelty Claim

Despite extensive searching, I found **no published paper that explicitly conditions molecular generation on discrete protein conformational states** in the way StateBind does. The existing landscape includes:

1. **Pocket-conditioned generation** (DiffSBDD, TargetDiff, Pocket2Mol): These condition on pocket 3D geometry but treat each pocket as an independent input. They do not model transitions between states or explicitly reason about conformational state labels. A user could generate molecules for each of 4 EGFR pockets, but the system has no concept of "state specificity."

2. **Ensemble-aware approaches** (PLACER, Boltzmann generators): Recent work models protein conformational ensembles (Anishchenko et al., 2025; EBA framework), but these focus on generating protein conformations, not on conditioning ligand generation on specific conformational states.

3. **Conformational profiling of kinase inhibitors** (Ung et al., PNAS 2018): Quantitative conformational profiling showed that selectivity originates from differential recognition of activation states. This provides biological validation for StateBind's thesis but is experimental, not computational generation.

4. **DFGmodel** (Brooijmans, ACS Chem. Biol., 2015): Computational protocol to predict DFG-out kinase conformations from DFG-in structures. Used for Type II inhibitor discovery but not for conditioned generation.

5. **Kinase-Bench** (JCIM, 2024): Benchmark for kinase selectivity with 6,875 selective ligands and 422,799 decoys across 75 kinases. Focuses on selectivity screening, not conditioned generation.

**Key data points:**
- Zero papers found that condition molecular generation on explicit conformational state labels (DFGin/out x aCin/out)
- Multiple papers condition on pocket shape, but none on state identity
- The closest work is conformational profiling + virtual screening, not generation

**Relevance to StateBind:** This is StateBind's strongest novelty claim. The explicit question "does state-conditioning improve generation outcomes?" has not been asked in the published literature. This positions the paper as a **first-of-kind benchmark study**, which is exactly the framing that works for JCIM or Nature Comp. Sci. However, reviewers will ask: "why not just run DiffSBDD on each pocket separately?" The answer must demonstrate that StateBind's state-aware scoring captures something that naive per-pocket generation does not.

---

### Finding 4: Foundation Model Integration -- Uni-Mol Is the Highest-Leverage Opportunity

**Uni-Mol** (Zhou et al., ICLR 2023; Uni-Mol2: Ji et al., NeurIPS 2024):
- Universal 3D molecular pretraining framework
- Pretrained on 209M molecular conformations (Uni-Mol) / 800M conformations (Uni-Mol2)
- Includes both molecular model AND pocket model (3M pocket data)
- SOTA on 14/15 molecular property prediction tasks
- Uni-Mol2 (1.1B params): 27% improvement on QM9, 14% on COMPAS-1D vs Uni-Mol
- Open source: GitHub deepmodeling/Uni-Mol
- **Integration path for StateBind:** Replace 9D hand-crafted pocket features with Uni-Mol pocket embeddings. Replace Morgan fingerprint similarity with Uni-Mol molecular embeddings. Could improve MPNN affinity prediction through pre-trained initialization.

**ESM-2** (Lin et al., Science 2023):
- Protein language model, 15B parameters largest variant
- Produces per-residue embeddings from sequence alone
- ESMFold achieves near-AlphaFold accuracy for structure prediction
- **Integration path:** Extract pocket residue embeddings as state descriptors instead of 9D geometric features. The 4 EGFR conformational states would have distinct ESM-2 representations.

**MoleculeSTM** (Liu et al., 2023):
- Cross-modal molecular representation learning (SMILES + text)
- Hit ratios in molecule editing tasks superior to genetic search baselines
- **Integration path:** Replace Morgan fingerprint similarity in scoring with MoleculeSTM embeddings. This could partially address the "only 3 reference molecules" weakness.

**ADMET-AI** (Swanson et al., Bioinformatics, 2024):
- Highest average rank on TDC ADMET Benchmark Leaderboard
- Chemprop-RDKit backbone
- **Integration path:** Drop-in replacement for StateBind's GIN multi-task ADMET model.

**TDC ADMET Leaderboard comparisons:**

| Task | StateBind | TDC #1 (MapLight+GNN) | TDC #2 | Gap |
|------|-----------|----------------------|--------|-----|
| hERG AUROC | 0.7745 | 0.880 +/- 0.002 | 0.875 +/- 0.014 | -0.106 |
| CYP3A4 AUPRC | 0.7323 | 0.916 +/- 0.000 | 0.904 +/- 0.002 | -0.184 |

**Key data points:**
- StateBind hERG AUROC of 0.775 ranks below TDC rank 12 (DeepMol 0.763 is below it, but most others are above)
- StateBind CYP3A4 AUPRC of 0.732 is significantly below SOTA (0.916)
- Uni-Mol pocket representations could replace 9D features with near-zero code changes
- ESM-2 residue embeddings for pocket description are a 1-week integration

**Relevance to StateBind:** Foundation model integration is the single highest-leverage improvement for publication. It addresses the "outdated architecture" concern without requiring a full model rewrite. The strategy: keep the VAE architecture but replace input representations with pre-trained embeddings. This also demonstrates extensibility -- a key selling point for a framework paper.

---

### Finding 5: Enrichment Factor Validation -- N=3-5 Is a Known Weakness Requiring Explicit Treatment

The enrichment factor literature provides clear guidance on statistical treatment:

1. **Analytic formulae** for EF confidence intervals exist (Nicholls, JCAMD, 2016): EF(f) * f is a probability, so binomial CIs apply. For small N, the CIs will be very wide.

2. **Bootstrap methods** (Truchon & Bayly, JCIM, 2007): Bootstrap resampling of the ranked list provides EF confidence intervals. These show "excellent agreement" with analytic estimates for AUC and "good agreement" for EF.

3. **EmProc approach** (Ash & Bhardwaj, J. Cheminform., 2022): Four approaches for hypothesis testing on hit enrichment curves were compared; EmProc was most effective. The paper explicitly states that "researchers almost never consider the uncertainty associated with estimating hit enrichment curves before declaring differences."

4. **Power metric** (Clark & Webster-Clark, J. Cheminform., 2016): Alternative to EF that accounts for expected variance in early enrichment.

**The core problem for StateBind:** With N=5 held-out drugs (pre-2010) and N=3 (pre-2015), the enrichment factor is computed from a tiny denominator. If even 1 drug's rank changes by 10 positions, EF@10 could swing from 4.95 to 2.5 or 7.5. Bootstrap CIs on N=5 will be extremely wide.

**What published papers use for enrichment validation:**
- Hong et al. (J. Cheminform., 2024, [DOI](https://doi.org/10.1186/s13321-024-00912-2)): EF@1% of 32.7 on CASF2016 (dataset: hundreds of actives) and 23.1 on DUD-E
- Typical CASF benchmarks: 285 complexes, 57 clusters
- DUD-E: 22,886 actives across 102 targets
- LIT-PCBA: 15 targets, hundreds of actives per target

**StateBind's situation is orders of magnitude smaller.** The EF@10 on N=3-5 is more like an anecdote than a statistic.

**Key data points:**
- Standard enrichment benchmarks use 100s--1000s of actives
- StateBind has 3--5 held-out drugs total
- Bootstrap CIs on N=5 will likely span EF 1--15 (very wide)
- Multi-kinase expansion to 3--5 kinases could provide 15--25 held-out drugs

**Relevance to StateBind:** The enrichment result MUST be accompanied by: (1) bootstrap confidence intervals, (2) acknowledgment that N=3-5 is underpowered, and (3) ideally, multi-kinase expansion to increase total held-out drugs. Reviewers at any venue will flag this. The mitigation is to frame the result as "consistent signal across multiple kinases" rather than "statistically significant on EGFR alone."

---

### Finding 6: The 1D vs 2D vs 3D Benchmark Surprise -- StateBind's Approach Is More Competitive Than Expected

Two landmark benchmarking studies published in 2024--2025 fundamentally challenge the assumption that 3D methods dominate:

**"Do 3D Methods Really Dominate?"** (arXiv 2406.03403, 2024):
- AutoGrow4 (2D genetic algorithm) achieved top docking scores across 7 targets
- REINVENT (1D SMILES) achieved QED 0.91, SA 1.85--1.88 -- competitive with all methods
- Conclusion: "No methods can dominate structure-based drug design in all evaluation metrics"
- 1D/2D methods treating docking as a black-box oracle achieve competitive binding affinity

**"Beyond Affinity"** (arXiv 2601.14283, 2025):
- Comprehensive benchmark of 1D, 2D, and 3D methods across multiple targets
- 3D methods: Best binding affinity but worst structural validity and pose quality
- 1D methods: Best drug-likeness metrics (QED, SA, LogP consistency) but lower affinity
- 2D methods: Best balance overall
- SMILES-VAE achieved QED 0.90--0.91, among the best across all method types
- TargetDiff showed worst strain energy (487.72 kcal/mol median) -- structural quality issues

**GSK Benchmarking Study** (JCIM, 2025):
- Deep learning methods failed to generate structurally valid molecules in many cases
- Pocket2Mol: 81.2% MOSES pass, but only 40.4% pass all validity checks
- DiffSBDD: 53.4% MOSES pass, 33.3% pass all checks
- AutoGrow4 (combinatorial): 32.5% pass all checks but 92.7% PoseBusters pass

**Relevance to StateBind:** This is unexpectedly good news. StateBind's SELFIES VAE guarantees 99.9% validity (by construction), which exceeds ALL 3D methods on structural validity. The trade-off is that StateBind lacks 3D pose awareness. But if framed correctly, this becomes: "Our 1D method achieves perfect validity while maintaining competitive drug-likeness, and state-conditioning provides the structure-awareness that 3D methods achieve through geometry." This reframing is powerful for JCIM.

---

### Finding 7: Ablation Design -- What Top-Venue Papers Ablate

From reviewing NeurIPS 2024--2025 and JCIM 2024--2025 molecular generation papers, the following ablation patterns emerge:

**Standard ablations in top-venue molecular generation papers:**
1. **Component ablation:** Remove each module/component and measure impact (e.g., remove state conditioning, remove scoring component)
2. **Architecture ablation:** Replace components with simpler alternatives (e.g., MLP instead of GNN, random embedding instead of learned)
3. **Data ablation:** Train on reduced dataset sizes to show scaling behavior
4. **Reward/scoring ablation:** Remove individual scoring terms to show contribution
5. **Baseline comparison:** Compare against naive versions (random generation, uniform sampling)
6. **Seed variation:** Multiple random seeds with error bars (3--5 seeds minimum)
7. **Pretraining ablation:** With vs. without pretrained representations

**StateBind needs the following ablation matrix:**

| Ablation | What It Tests | Expected Outcome |
|----------|--------------|-----------------|
| VAE without state vector | State conditioning value | Lower enrichment |
| Random state assignment | State specificity signal | Lower enrichment |
| Remove state specificity from scoring (0.85 -> 1.0 on other 3 components) | Scoring contribution | Different ranking |
| Remove reference similarity | Bias from known-drug similarity | State-aware mean score should improve |
| Single-pocket VAE (1M17 only) | Multi-pocket advantage | Lower diversity |
| REINVENT on same task | Generation method contribution | Architecture comparison |
| Fingerprint similarity search | Generation vs. search | Method category comparison |
| VAE + random scoring | Scoring function value | Should degrade to random |

**Relevance to StateBind:** The ablation design is straightforward but must be done. The single most important ablation is **VAE without state vector** -- this directly tests whether state-conditioning contributes anything beyond the VAE's generation capability. If state-aware EF@10 drops to near-static levels when the state vector is removed, that is the paper's proof point.

---

### Finding 8: Multi-Target Generalization -- The Highest-Impact Publication Upgrade

The field is moving toward multi-target validation:

- **MTMol-GPT** (Kong et al., PLoS Comput. Biol., 2024): Generative model for multi-target compounds, tested on DRD2/HTR1A and EGFR/Src kinase pairs
- **KinomePro-DL**: Multi-task DNN trained on 191 kinases, auROC ~0.95 for selectivity
- **AMGU**: Multi-task GIN for 204 kinases, outperformed single-task models
- **Kinase-Bench** (JCIM, 2024): 6,875 selective ligands, 422,799 decoys, 75 kinases
- **CDK2 active learning** (Comms. Chem., 2025): VAE + active learning on CDK2, 8/9 synthesized compounds active including 1 nanomolar hit

**Candidate kinases for StateBind expansion:**

| Kinase | DFG States in PDB | ChEMBL Data | Approved Drugs | Feasibility |
|--------|-------------------|-------------|----------------|-------------|
| EGFR | 4 states (current) | 10,466 | 8+ (erlotinib, gefitinib, osimertinib, etc.) | Done |
| ABL1 | 4 states (well-characterized) | ~8,000 | 4+ (imatinib, dasatinib, ponatinib, etc.) | HIGH |
| BRAF | 3+ states | ~5,000 | 3+ (vemurafenib, dabrafenib, encorafenib) | MODERATE |
| CDK2 | 2+ states | ~6,000 | 2 (palbociclib-related) | MODERATE |
| ALK | 3+ states | ~3,000 | 4+ (crizotinib, ceritinib, alectinib, lorlatinib) | MODERATE |

**Key data points:**
- ABL1 is the best second target: well-characterized DFG-in/out states, extensive ChEMBL data, multiple approved drugs
- 3 kinases (EGFR + ABL1 + BRAF) would provide ~15-20 held-out drugs total
- 5 kinases would provide ~25-30 held-out drugs, making enrichment statistics meaningful

**Relevance to StateBind:** Multi-kinase expansion is the single highest-impact improvement for publication. It transforms the narrative from "EGFR case study" to "kinome-wide principle." ABL1 should be first because it has the most similar conformational landscape to EGFR (DFGin/out clearly defined, multiple approved Type I and Type II inhibitors). The compute cost is manageable: retrain VAE and MPNN on each kinase's ChEMBL data (~1 week per kinase on H200 GPUs).

---

### Finding 9: Nature Computational Science Publication Requirements -- What Gets In

Analyzing the 2024--2025 Nature Comp. Sci. molecular generation publications:

**PropMolFlow** (Nat. Comput. Sci., 2025): Property-guided flow matching. SE(3)-equivariant. Competitive with diffusion models. Key selling point: faster sampling with fewer time steps.

**ECloudGen** (Nat. Comput. Sci., 2025): Electron cloud latent variables + Llama architecture + contrastive learning. Key selling point: bridges ligand-only and protein-ligand data.

**SynGFN** (Nat. Comput. Sci., 2025): Synthesis-aware GFlowNet. Key selling point: generates synthesizable molecules by construction (chemical reaction cascade).

**DiffSBDD** (Nat. Comput. Sci., 2024): Equivariant diffusion for SBDD. Key selling point: flexible framework supporting de novo, inpainting, and optimization.

**Common features of accepted papers:**
1. Novel architecture or formulation (not just application)
2. Multiple evaluation metrics (not just one benchmark)
3. Practical applicability argument (not just benchmark numbers)
4. Multi-target or broad evaluation (not single-target case study)
5. Open-source code + pretrained models
6. Clear "why this matters" narrative

**StateBind's gap:** It does not introduce a novel architecture. It introduces a novel **evaluation framework and question**. For Nature Comp. Sci., this would need to be framed as: "We present a systematic framework for evaluating conformational awareness in molecular design and demonstrate, across N kinases, that state-aware approaches consistently identify future drugs." The framework must be reusable by others (released code + data).

---

### Finding 10: The Scoring Function Dilemma -- Why State-Aware Loses on Mean Score

StateBind's most puzzling result: state-aware loses on mean unified score (0.4378 vs 0.5437) despite winning 10x on retrospective enrichment. The reason is well-understood: the reference similarity component (35% weight) rewards proximity to erlotinib/gefitinib/osimertinib, penalizing novel VAE-generated molecules.

**This is actually a publishable insight, not a weakness.** The framing should be:

> "Fixed scoring functions optimized for known-drug similarity systematically undervalue novel candidates. State-aware generation finds molecules resembling future drugs that fall below conventional scoring thresholds. This exposes a fundamental tension between exploitation (high-scoring known-drug-like) and exploration (lower-scoring but prospectively valuable)."

**Supporting evidence from the literature:**
- The PMO benchmark (Gao et al., 2022) showed that optimization methods converge to high-scoring but trivial solutions under simple oracles
- "Beyond Affinity" (2025) showed that high docking scores often correlate with poor drug-likeness
- Multiple papers on diversity-affinity trade-offs in molecular generation

**Relevance to StateBind:** Frame the mean-score loss as a feature, not a bug. It demonstrates exactly why retrospective validation matters: conventional scoring functions are biased toward the past. The enrichment metric is forward-looking. This insight is publication-worthy in itself.

---

### Finding 11: Code Availability and Reproducibility of External Baselines

| Method | GitHub | Pretrained Models | License | EGFR-Ready | Setup Effort |
|--------|--------|-------------------|---------|------------|-------------|
| REINVENT 4 | MolecularAI/REINVENT4 | Yes (general SMILES) | Apache 2.0 | Needs scoring setup | 1-2 weeks |
| DiffSBDD | arneschneuing/DiffSBDD | Yes (CrossDocked2020, Zenodo) | Available | Needs EGFR pocket prep | 1-2 weeks |
| TargetDiff | guanjq/targetdiff | Yes | Available | Needs EGFR pocket prep | 1-2 weeks |
| Pocket2Mol | pengxingang/Pocket2Mol | Yes | Available | Needs pocket extraction | 1-2 weeks |
| Graph GA | mol_opt benchmark | Yes (PMO repo) | MIT | Needs oracle setup | 1 week |
| MolDQN | mol_opt benchmark | Yes (PMO repo) | MIT | Needs oracle setup | 1 week |

**Recommendation:** Run REINVENT 4 and DiffSBDD first. These are the two baselines that cover the most critical comparisons: (1) REINVENT as the industry-standard 1D optimizer, (2) DiffSBDD as the state-of-the-art 3D structure-aware generator published in the same journal we're targeting (Nature Comp. Sci.).

---

### Finding 12: The ADMET Gap -- StateBind's Models Are Below TDC Leaderboard

The TDC ADMET Benchmark Group provides standardized evaluation. StateBind's performance:

**hERG Blocking Prediction:**
- StateBind GIN multi-task: AUROC 0.7745
- TDC Rank 1 (MapLight+GNN): AUROC 0.880 +/- 0.002
- TDC Rank 8 (Chemprop-RDKit): AUROC 0.840 +/- 0.007
- StateBind would rank approximately 11th-12th out of 12 models on the leaderboard

**CYP3A4 Inhibition Prediction:**
- StateBind GIN multi-task: AUPRC 0.7323
- TDC Rank 1 (MapLight+GNN): AUPRC 0.916 +/- 0.000
- TDC Rank 10 (Chemprop): AUPRC 0.862 +/- 0.003
- StateBind would rank below all 12 listed models

**Mitigation options:**
1. ADMET-AI (Swanson et al., Bioinformatics, 2024) provides a drop-in replacement with TDC-rank-1 performance. Open source, Chemprop-RDKit backbone.
2. NovoExpert-2 (ChemRxiv, 2026) achieves SOTA on multiple TDC tasks using gradient-boosted trees on MapLight fingerprints + GIN embeddings.
3. Since ADMET is "informational only" in StateBind, the gap matters less for the core paper -- but if ADMET is integrated into scoring, the model quality matters.

**Relevance to StateBind:** Do not claim ADMET model quality in the paper. Either upgrade to ADMET-AI/Chemprop-RDKit or keep ADMET as informational annotation. The ADMET gap is a distraction from the main contribution (state-conditioning) and should not become an attack surface for reviewers.

---

### Finding 13: Recent Conformational Ensemble Generation Methods

Several 2025 methods generate protein conformational ensembles:

- **PLACER** (Anishchenko et al., Baker Lab, 2025): Generates protein-ligand conformational ensembles; could provide state-specific pocket structures
- **EBA** (2025): Physics-informed alignment for ensemble generation using energy feedback
- **JAMUN** (arXiv 2024): Transferable molecular conformational ensemble generation, orders of magnitude faster than MD

**Relevance to StateBind:** These are complementary, not competitive. StateBind uses 4 discrete crystal structures; these methods could generate continuous ensembles per state. This is an extension opportunity (deferred Vision idea 001), not a current threat. If anything, the existence of these methods validates that conformational awareness is a growing priority in the field.

---

### Finding 14: Benchmark Infrastructure Available for Kinase-Focused Evaluation

Two recently published benchmark suites are directly relevant:

**Kinase-Bench** (JCIM, 2024):
- 6,875 selective ligands, 422,799 decoys for 75 kinases
- Designed specifically for selectivity-focused virtual screening
- Provides cross-kinase evaluation infrastructure
- **StateBind relevance:** Could use Kinase-Bench targets for multi-kinase expansion and selectivity evaluation

**Durian** (Nie et al., JCIM, 2025):
- Comprehensive benchmark for structure-based 3D molecular generation
- 17 evaluation metrics across binding affinity, drug-likeness, and structural quality
- Uses 3 independent docking methods (QuickVina2, Surflex, GNINA)
- 6 methods evaluated (LiGAN, Pocket2Mol, DiffSBDD, SBDD, GraphBP, SurfGen)
- **StateBind relevance:** Adopt Durian's evaluation protocol for comparing StateBind against 3D baselines. Using their metric suite strengthens reproducibility claims.

---

### Finding 15: The Retrospective Validation Framing -- From Weakness to Differentiator

Despite the small sample size, StateBind's time-split retrospective validation has a unique advantage: **very few published molecular generation papers perform any retrospective validation at all.**

Most papers evaluate on:
- CrossDocked2020 hold-out sets (different pockets, not time-split)
- MOSES/GuacaMol distribution metrics (unrelated to drug discovery utility)
- PMO oracle optimization (synthetic objectives, not real drugs)

StateBind asks: "Would this method have found drugs that were later approved?" This is closer to the actual drug discovery question than any benchmark metric. The weakness (small N) can be reframed as: "We evaluate on the hardest possible test -- predicting real approved drugs using only historically available data."

**Published enrichment factors for reference:**
- Hong et al. (2024): EF@1% = 32.7 (CASF2016, hundreds of actives)
- DUD-E benchmarks: EF@1% = 10--50 range (thousands of actives per target)
- StateBind: EF@10% = 4.95--7.72 (but on truly held-out future drugs, not benchmark decoys)

The apples-to-oranges nature of these comparisons is actually the point: StateBind's enrichment is on a harder, more realistic task.

---

## Implications for StateBind

### Opportunities

1. **Novel contribution confirmed.** No published paper conditions molecular generation on explicit conformational state labels. StateBind owns this niche.

2. **Framework paper framing works.** JCIM and Nature Comp. Sci. both accept benchmark/framework papers. The question "does conformational awareness help?" is timely and under-explored.

3. **1D methods validated.** Recent benchmarks show 1D SMILES methods are competitive with 3D on drug-likeness and validity. StateBind's SELFIES VAE is not as outdated as feared for a framework paper.

4. **External baselines are feasible.** REINVENT 4 and DiffSBDD both have open-source code and pretrained models. A 2--4 week effort could produce the required comparisons.

5. **Multi-kinase expansion is high-leverage.** ABL1 + BRAF or ALK would provide 15--25 total held-out drugs and transform the statistical story.

6. **Foundation model drop-ins exist.** Uni-Mol pocket embeddings and ADMET-AI are near-zero-effort improvements.

7. **The mean-score loss is actually publishable.** It demonstrates that conventional scoring undervalues exploration -- a known but under-documented problem.

### Risks and Caveats

1. **JCIM reviewers will demand REINVENT comparison.** This is non-negotiable. Without it, the paper is desk-rejected or gets a major revision.

2. **N=3-5 enrichment is statistically indefensible alone.** Bootstrap CIs will be very wide. Multi-kinase expansion is effectively required.

3. **The ablation removing state conditioning might show small effect.** If EF@10 drops from 4.95 to 3.5 (not to 0.47), the state-conditioning contribution is real but modest. This must be reported honestly.

4. **3D baselines may outperform on some metrics.** DiffSBDD generates 3D poses directly; StateBind does not. Pocket-aware generation may achieve higher docking scores. StateBind's advantage must be shown on the metrics that matter (enrichment, diversity, validity).

5. **Compute cost for multi-kinase.** Retraining VAE + MPNN + running GNINA docking for 3--5 kinases is ~2-4 weeks of GPU time on H200. Feasible but not trivial.

6. **Data leakage concern.** Recent work shows PDBbind train-test leakage inflated many binding affinity prediction benchmarks (Nat. Mach. Intell., 2025). StateBind's time-split avoids this, which is a strength -- but must be explicitly stated.

### Recommended Next Steps

**Priority 1 (Weeks 1-3): External Baselines**
- Set up REINVENT 4 with EGFR Vina docking oracle on all 4 conformational states
- Set up DiffSBDD with EGFR pocket structures (1M17, 2GS7, 3W2R, 4ZAU)
- Generate molecules from both and evaluate with StateBind's unified scoring
- Run retrospective enrichment on the same time-split protocol

**Priority 2 (Weeks 2-5): Multi-Kinase Expansion**
- Prepare ABL1 conformational atlas (DFGin/out structures from PDB)
- Download ABL1 ChEMBL binding data and train ABL1-specific VAE + MPNN
- Run full StateBind pipeline for ABL1
- Repeat for BRAF or ALK (at least one more kinase)
- Compute enrichment across all kinases with bootstrap CIs

**Priority 3 (Week 3-4): Ablation Suite**
- VAE without state vector (remove conditioning)
- Random state assignment (shuffle state labels)
- Remove reference similarity from scoring (reweight to 0/0.41/0.35/0.24)
- Single-pocket generation (1M17 only for state-aware)
- 3+ random seeds for each configuration

**Priority 4 (Week 4-5): Foundation Model Integration**
- Replace 9D pocket features with Uni-Mol pocket embeddings
- Evaluate impact on MPNN affinity prediction
- If significant improvement, add as optional pipeline enhancement

**Priority 5 (Week 5-6): Paper Writing**
- Frame as benchmark paper: "Does Conformational State-Awareness Improve Molecular Design? A Multi-Kinase Benchmark"
- Target JCIM primary, Nature Comp. Sci. aspirational
- Include comprehensive ablation table, external baseline comparison, multi-kinase enrichment with CIs
- Release code, data, and evaluation protocol as open benchmark

---

## References

1. Schneuing, A. et al. "Structure-based drug design with equivariant diffusion models." *Nature Computational Science* 4, 2024. https://doi.org/10.1038/s43588-024-00737-x

2. Loeffler, H.H. et al. "Reinvent 4: Modern AI-driven generative molecule design." *Journal of Cheminformatics* 16, 2024. https://doi.org/10.1186/s13321-024-00812-5

3. Gao, W. et al. "Sample Efficiency Matters: A Benchmark for Practical Molecular Optimization." *NeurIPS Datasets & Benchmarks*, 2022. https://arxiv.org/abs/2206.12411

4. Guan, J. et al. "3D Equivariant Diffusion for Target-Aware Molecule Generation and Affinity Prediction." *ICLR*, 2023. https://github.com/guanjq/targetdiff

5. Peng, X. et al. "Pocket2Mol: Efficient Molecular Sampling Based on 3D Protein Pockets." *ICML*, 2022.

6. Lee, J. et al. "BInD: Bond and Interaction-generating Diffusion Model for Multi-objective Structure-based Drug Design." *Advanced Science*, 2025. https://arxiv.org/abs/2405.16861

7. Guan, J. et al. "DecompDiff: Diffusion Models with Decomposed Priors for Structure-Based Drug Design." *ICML*, 2023. https://github.com/bytedance/DecompDiff

8. Nie, C. et al. "Durian: A Comprehensive Benchmark for Structure-Based 3D Molecular Generation." *JCIM* 65, 2025. https://doi.org/10.1021/acs.jcim.4c02232

9. "Kinase-Bench: Comprehensive Benchmarking Tools and Guidance for Achieving Selectivity in Kinase Drug Discovery." *JCIM* 64(24), 9528-9550, 2024. https://doi.org/10.1021/acs.jcim.4c01830

10. "Benchmarking 3D Structure-Based Molecule Generators." *JCIM* 65(15), 8006-8021, 2025. https://doi.org/10.1021/acs.jcim.5c01020

11. "Structure-based Drug Design Benchmark: Do 3D Methods Really Dominate?" arXiv:2406.03403, 2024.

12. "Beyond Affinity: A Benchmark of 1D, 2D, and 3D Methods Reveals Critical Trade-offs in Structure-Based Drug Design." arXiv:2601.14283, 2025.

13. Zhou, G. et al. "Uni-Mol: A Universal 3D Molecular Representation Learning Framework." *ICLR*, 2023. https://github.com/deepmodeling/Uni-Mol

14. Ji, Y. et al. "Uni-Mol2: Exploring Molecular Pretraining Model at Scale." *NeurIPS*, 2024. https://arxiv.org/abs/2406.14969

15. Swanson, K. et al. "ADMET-AI: A machine learning ADMET platform for evaluation of large-scale chemical libraries." *Bioinformatics* 40(7), 2024. https://doi.org/10.1093/bioinformatics/btae416

16. Hong, Y. et al. "Accurate prediction of protein-ligand interactions by combining physical energy functions and graph-neural networks." *J. Cheminformatics* 16, 121, 2024. https://doi.org/10.1186/s13321-024-00912-2

17. Clark, R.D. & Webster-Clark, D.J. "The power metric: a new statistically robust enrichment-type metric." *J. Cheminformatics* 8, 2016. https://doi.org/10.1186/s13321-016-0189-4

18. Nicholls, A. "Confidence limits, error bars, and method comparison in molecular modeling." *JCAMD* 30, 2016. https://doi.org/10.1007/s10822-015-9861-4

19. Ash, J.R. & Bhardwaj, R.M. "Confidence bands and hypothesis tests for hit enrichment curves." *J. Cheminformatics* 14, 2022. https://doi.org/10.1186/s13321-022-00629-0

20. Kong, X. et al. "MTMol-GPT: De novo multi-target molecular generation with transformer-based generative adversarial imitation learning." *PLoS Comput. Biol.* 20(7), 2024. https://doi.org/10.1371/journal.pcbi.1012229

21. Ung, P.M. et al. "Quantitative conformational profiling of kinase inhibitors reveals origins of selectivity for Aurora kinase activation states." *PNAS* 115(51), 2018. https://doi.org/10.1073/pnas.1811158115

22. "Generative molecular design and discovery on the rise." *Nature Computational Science* 5, 2025. https://doi.org/10.1038/s43588-025-00802-z

23. "PropMolFlow: property-guided molecule generation with geometry-complete flow matching." *Nature Computational Science*, 2025. https://doi.org/10.1038/s43588-025-00946-y

24. "SynGFN: learning across chemical space with generative flow-based molecular discovery." *Nature Computational Science*, 2025. https://doi.org/10.1038/s43588-025-00902-w

25. "ECloudGen: leveraging electron clouds as a latent variable to scale up structure-based molecular design." *Nature Computational Science*, 2025. https://doi.org/10.1038/s43588-025-00886-7

26. "Resolving data bias improves generalization in binding affinity prediction." *Nature Machine Intelligence*, 2025. https://doi.org/10.1038/s42256-025-01124-5

27. "NovoExpert-2: State-of-the-Art ADMET Prediction via Gradient-Boosted Trees on MapLight Fingerprints and GIN Embeddings." ChemRxiv, 2026.

28. Brooijmans, N. "DFGmodel: Predicting Protein Kinase Structures in Inactive States for Structure-Based Discovery of Type-II Inhibitors." *ACS Chem. Biol.* 10(1), 2015. https://doi.org/10.1021/cb500696t
