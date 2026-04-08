---
agent: Maverick Generative AI Specialist
round: 1
date: 2026-04-08
type: research-note
topic: 3D Pocket-Conditioned Molecular Generation Landscape -- Evaluating Transformative Upgrades for StateBind's SELFIES VAE
---

# Research Note: The 3D Molecular Generation Landscape and StateBind's Path Forward

## Summary

This research note provides a comprehensive survey of the 3D pocket-conditioned molecular
generation landscape as of early 2026, with specific evaluation of how these methods could
strengthen or replace StateBind's current SELFIES VAE. The field has matured dramatically
since the Vision System's original idea 002 (3D Pocket-Conditioned Diffusion) was proposed.
Key findings:

1. **The SOTA has shifted from diffusion to flow matching.** MolCRAFT, FLOWR, MolFORM, and
   PropMolFlow represent the new generation, offering 10-70x faster sampling than diffusion
   baselines while matching or exceeding binding affinity metrics.

2. **3D methods do NOT universally dominate 1D/2D methods.** A critical June 2024 benchmark
   showed that SMILES-based and genetic algorithm approaches achieve competitive docking
   scores when using the same oracle (AutoDock Vina). This complicates the naive "3D > 1D"
   narrative.

3. **No existing method generates molecules conditioned on multiple conformational states of
   the same protein.** This is StateBind's unique opportunity. Apo2Mol (2025) handles
   apo-to-holo transitions but not multi-state conditioning. This gap is a genuine novelty
   claim.

4. **Pre-trained checkpoints exist for DiffSBDD, TargetDiff, and MolCRAFT.** Fine-tuning
   on EGFR-specific pockets is feasible on the Yale Bouchet HPC cluster (H200 GPUs) within
   hours, not days.

5. **REINVENT 4.0 + active learning is the pragmatic strong baseline.** A 2024 study
   combining REINVENT with physics-based binding free energy calculations found higher-scoring
   molecules in 3-7 active learning iterations. This is a direct threat to StateBind's
   one-shot pipeline if not addressed.

6. **PoseBusters/PoseCheck have fundamentally changed evaluation standards.** Only 0-11% of
   raw 3D-generated molecules have valid 3D conformations (GenBench3D, 2024). The field now
   requires PoseBusters validity alongside Vina scores. FLOWR achieves 92% validity.

7. **The publication opportunity is NOT "we used a better generator" but rather "we showed
   that conformation-conditioned generation enables state-specific molecular design."** The
   method novelty is the multi-pocket conditioning, not the generative architecture.

---

## Research Questions

1. What is the current SOTA for 3D pocket-conditioned molecular generation, and how do
   methods compare on standardized benchmarks (CrossDocked2020, SPINDR)?
2. Has any existing method generated molecules conditioned on multiple conformational states
   of the same protein target?
3. Which methods have usable code and pre-trained checkpoints that could be adapted for
   StateBind's EGFR pockets?
4. Under what conditions do 3D methods outperform 1D/2D methods, and when do they not?
5. What is the realistic compute cost of training or fine-tuning a 3D generation model on
   the Yale Bouchet HPC cluster?
6. How should REINVENT 4.0 be positioned -- as a baseline comparison or a complementary
   tool?
7. Could an active learning loop tighten StateBind's generate-score cycle?

---

## Methods

### Sources Consulted

- arXiv preprints (2024-2026) on 3D molecular generation
- Published papers in Nature Computational Science, Nature Communications, JCIM, Chemical
  Science, ICLR 2024-2026, ICML 2025, NeurIPS 2024-2025
- GitHub repositories for DiffSBDD, TargetDiff, MolCRAFT, REINVENT4, FLOWR, FlowMol,
  Apo2Mol, TacoGFN, IPDiff, 3DSMILES-GPT
- Benchmark datasets: CrossDocked2020, SPINDR, GenBench3D, Durian
- PubMed and PMC for peer-reviewed validation studies

### Search Strategy

Executed 20+ targeted web searches covering:
- Individual method benchmarks and latest updates (DiffSBDD, TargetDiff, MolCRAFT, FLOWR,
  MolFORM, FlowMol3, Pocket2Mol, DecompDiff, 3DSMILES-GPT, VoxBind, IPDiff, Apo2Mol)
- Head-to-head 1D vs 3D comparison studies
- Multi-conformation and ensemble pocket generation
- Active learning + molecular generation workflows
- REINVENT 4.0 architecture and applications
- Compute cost and training requirements
- PoseBusters/PoseCheck 3D validity evaluation
- Bayesian optimization for molecular design

---

## Findings

### Finding 1: The CrossDocked2020 Benchmark Leaderboard Has Been Reshaped

The CrossDocked2020 benchmark remains the standard evaluation dataset for structure-based
drug design, containing 22.5 million docked protein-ligand pairs. However, the leaderboard
has changed dramatically since the Vision System's original assessment.

**Comprehensive Benchmark Comparison Table (CrossDocked2020):**

| Method | Type | Vina Score | Vina Min | Vina Dock | QED | SA | Diversity | Year |
|--------|------|-----------|----------|-----------|-----|-----|-----------|------|
| MolFORM | Flow matching | **-7.60** | -- | -- | -- | -- | 0.75 | 2025 |
| 3DSMILES-GPT | LM hybrid | **-7.72** | -- | -- | **0.76** | 3.07 | 0.89 | 2025 |
| MolCRAFT | BFN | -6.59 | -7.05 | -7.24 | 0.69 | 0.50 | 0.36 | 2024 |
| Apo2Mol | Diffusion | -- | -6.79 | -- | 0.59 | -- | -- | 2025 |
| IPDiff | Diffusion | -6.42 | -- | -- | -- | -- | -- | 2024 |
| FLOWR | Flow matching | -6.29 | -6.48 | -- | -- | -- | -- | 2025 |
| TargetDiff | Diffusion | -5.47 | -6.30 | -6.64 | 0.48 | -- | -- | 2023 |
| DecompDiff | Diffusion | -5.19 | -5.27 | -6.03 | 0.56 | -- | -- | 2024 |
| Pocket2Mol | Autoregressive | -5.14 | -4.70 | -6.42 | 0.57 | -- | -- | 2022 |
| Reference | -- | -6.36 | -- | -- | 0.48 | -- | -- | -- |

**Key data points:**
- MolFORM achieves the best raw Vina Score (-7.60) using preference-aligned flow matching
  with DPO and online RL (ICML 2025).
- 3DSMILES-GPT achieves -7.72 Vina Score and 0.76 QED by treating 3D generation as a
  language modeling problem with 10M molecule pretraining (Chemical Science, 2025).
- MolCRAFT is the first method to achieve reference-level Vina Scores (-6.59 vs -6.36
  reference) with comparable molecule size, and is 30x faster than TargetDiff/DecompDiff
  (~141s vs 3400-6200s per 100 samples).
- TargetDiff and DiffSBDD, the methods originally proposed in Vision idea 002, are now
  1-2 kcal/mol behind the SOTA.

**Relevance to StateBind:** The generative architecture landscape has shifted. If StateBind
adopts a 3D method, it should target MolCRAFT, FLOWR, or MolFORM rather than the older
DiffSBDD/TargetDiff models. However, the more critical question is whether *any* 3D method
delivers enough improvement over the current SELFIES VAE to justify the implementation cost.

---

### Finding 2: 3D Methods Do NOT Universally Dominate 1D/2D Methods

A critical benchmark study from June 2024 ("Structure-based Drug Design Benchmark: Do 3D
Methods Really Dominate?") compared 16 methods across 7 protein targets using AutoDock Vina
as the docking oracle.

**Results across 7 targets:**

| Method | Type | Typical Vina Range (Top-10) | Key Observation |
|--------|------|---------------------------|-----------------|
| AutoGrow4 | 2D genetic algorithm | -13.2 to -8.8 | Best optimization overall |
| Pocket2Mol | 3D autoregressive | -12.3 to -9.7 | Competitive but not dominant |
| PocketFlow | 3D flow | -12.5 to -7.8 | Variable across targets |
| DST | 2D graph | -11.0 to -8.3 | Strong 2D baseline |
| MIMOSA | 2D graph | -11.0 to -8.3 | Matches DST |
| REINVENT | 1D RL | -9.9 to -7.3 | Moderate but consistent |
| SMILES-VAE-BO | 1D VAE+BO | variable | Competitive with Bayesian optimization |
| MolDQN | 2D RL | -7.1 to -5.9 | Weakest performer |

**Key conclusions from this study:**
1. "3D SBDD algorithms (using 3D target protein structure explicitly) do not demonstrate
   significant superiority over 2D methods."
2. "1D/2D ligand-centric drug design methods can be used in SBDD by treating the docking
   function as a black-box oracle."
3. Search-based algorithms (AutoGrow4) outperform generation-based methods on Top-10/50/100
   docking scores.

**Key data points:**
- AutoGrow4 (a 2D genetic algorithm with fragment-based evolution) achieves the best docking
  scores across most targets, beating all 3D diffusion methods.
- REINVENT with RL achieves -9.87 to -7.25 kcal/mol, competitive with 3D methods.
- The 96-hour computational limit per run is comparable to StateBind's pipeline runtime.

**Relevance to StateBind:** This is a sobering finding. The naive argument that "3D
generation is inherently better than 1D" does not hold when docking is the evaluation
metric. StateBind's SELFIES VAE + GNINA docking pipeline may be more competitive than
assumed. The advantage of 3D generation is NOT better docking scores but rather (a) the
generated poses are already in the pocket, eliminating the docking bottleneck, and (b) the
structural conditioning is richer than a 4D one-hot vector. The case for 3D must be made
on these grounds, not on raw Vina score improvements.

---

### Finding 3: No Existing Method Generates Molecules for Multiple Conformational States

After extensive searching, I found NO published method that explicitly generates molecules
conditioned on different conformational states of the same protein target. This is
StateBind's novelty gap.

**Closest existing work:**

1. **Apo2Mol (2025):** Generates molecules while transforming protein pockets from apo
   (unbound) to holo (ligand-bound) conformations using residue-level interpolation and
   spherical linear interpolation. However, it handles a single apo-to-holo transition,
   not multiple discrete conformational states. Average Vina Min: -6.79 (apo test), -7.86
   (holo test). Code available at https://github.com/AIDD-LiLab/Apo2Mol

2. **PocketXMol (Cell, 2026):** A unified framework for pocket-interaction tasks that was
   tested on "alternative pocket conformations" and showed "overall performance remaining
   largely consistent with results using the holo structures." This suggests robustness to
   conformational variation but not explicit multi-state conditioning.

3. **POLYGON (2024):** Multi-target polypharmacology via generative RL, generating molecules
   that bind two DIFFERENT protein targets simultaneously. Related but distinct from
   multi-conformation single-target design.

4. **Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design
   (2024):** Reprograms a pre-trained target-specific diffusion model for dual-target
   generation. Again, two different targets, not two conformations of the same target.

**Key data points:**
- Zero papers found on "multi-conformation pocket-conditioned generation" for kinases.
- Apo2Mol's dataset (24,601 apo-holo-ligand triplets from PLINDER) demonstrates that
  conformation-aware generation is tractable.
- The gap between "multi-target" and "multi-conformation" generation is precisely
  StateBind's novelty claim.

**Relevance to StateBind:** This is the strongest finding in this research note. StateBind's
thesis -- that conformational state awareness improves molecular design -- has NO direct
competitor in the 3D generation space. A 3D model that generates molecules conditioned on
each of EGFR's 4 conformational state pockets (1M17, 2GS7, 3W2R, 4ZAU) would be genuinely
novel. The paper's framing should be: "We introduce conformation-conditioned 3D generation
for kinase drug design" rather than "We replaced a VAE with a diffusion model."

---

### Finding 4: Pre-trained Checkpoints and Code Availability

**Code and Checkpoint Availability:**

| Method | GitHub | Stars | Checkpoints | Custom Pocket Inference | Last Active |
|--------|--------|-------|-------------|------------------------|-------------|
| DiffSBDD | github.com/arneschneuing/DiffSBDD | 499 | Yes (8 variants on Zenodo) | Yes (residue list or ref ligand) | 2024 |
| TargetDiff | github.com/guanjq/targetdiff | 329 | Yes (Google Drive) | Yes (PDB + 10A pocket) | 2023 |
| MolCRAFT | github.com/AlgoMole/MolCRAFT | 150 | Yes (HuggingFace) | Yes | 2025 (active) |
| REINVENT4 | github.com/MolecularAI/REINVENT4 | 720 | Pre-trained prior models | Yes (custom scoring) | v4.7, Nov 2025 |
| Apo2Mol | github.com/AIDD-LiLab/Apo2Mol | new | Unknown | Yes | 2025 |
| TacoGFN | github.com/tsa87/tacogfn | -- | -- | Yes | 2024 |
| FlowMol | github.com/Dunni3/FlowMol | -- | -- | Yes | 2025 |
| 3DSMILES-GPT | github.com/ashipiling/GPT_3DSMILES | -- | Unknown | Yes | 2025 |
| IPDiff | github.com/YangLing0818/IPDiff | -- | Yes | Yes | 2024 |
| PropMolFlow | github.com/Liu-Group-UF/PropMolFlow | -- | Yes | Yes | 2025 |

**Key data points:**
- DiffSBDD provides 8 pre-trained checkpoint variants (CrossDocked + BindingMOAD, C-alpha +
  full-atom, conditional + joint).
- MolCRAFT checkpoints are on HuggingFace (GenSI/MolCRAFT), the most accessible format.
- REINVENT4 v4.7 (Nov 2025) has 720 GitHub stars, making it the most actively maintained
  and community-supported tool.
- TargetDiff's checkpoint is 2+ years old with no updates since initial release.

**Relevance to StateBind:** For a rapid proof-of-concept, DiffSBDD or MolCRAFT checkpoints
could be used to generate molecules for each of the 4 EGFR pockets without any retraining.
For a publication-quality comparison, fine-tuning on EGFR-family data from CrossDocked2020
would be appropriate. REINVENT4's plugin architecture makes it the easiest tool to integrate
with StateBind's existing GNINA scoring.

---

### Finding 5: Compute Requirements for 3D Generation on Yale Bouchet

**Training Cost Estimates:**

| Method | Training Data | Approx. Training Time | GPU Memory | Hardware Reference |
|--------|--------------|----------------------|------------|-------------------|
| MolCRAFT | CrossDocked (100K pairs) | ~24-48h on 1x A100 | ~16-32 GB | Estimated from paper |
| DiffSBDD | CrossDocked + BindingMOAD | ~24-48h on 1x A100 | ~16-32 GB | Estimated from checkpoints |
| TargetDiff | CrossDocked | Similar to DiffSBDD | ~16 GB | Tested with PyTorch 1.13 + CUDA 11.6 |
| Pocket2Mol | CrossDocked | 72h on 1x V100 | ~16 GB | Reported in paper |
| REINVENT4 | Pre-trained prior | Minutes (RL fine-tuning) | ~8 GB | Documented: 8 GB CPU+GPU |
| 3DSMILES-GPT | 10M PubChem + CrossDocked | Unknown (large pretraining) | Likely 40+ GB | Not reported |

**Sampling Speed Comparison:**

| Method | Time per 100 Molecules | Notes |
|--------|----------------------|-------|
| MolCRAFT | ~141 seconds | 30x faster than diffusion baselines |
| FLOWR (20 steps) | ~2.4 seconds per target | 70x faster than Pilot baseline |
| 3DSMILES-GPT | ~45 seconds | 0.45s per molecule |
| TargetDiff | ~1,252 seconds | Slowest diffusion method |
| DiffSBDD | ~3,400-6,200 seconds | Standard diffusion sampling |
| REINVENT4 | Seconds per batch | RL sampling is fast |

**Key data points:**
- Yale Bouchet H200 GPUs (80 GB HBM3) exceed the memory requirements of all listed methods.
- For EGFR-specific fine-tuning (4 pockets, ~1000 known ligands from ChEMBL), training
  would likely take 4-8 hours on a single H200.
- MolCRAFT and FLOWR offer the best speed/quality tradeoff for sampling.
- REINVENT4 is by far the cheapest to deploy (minutes of RL fine-tuning, ~8 GB memory).

**Relevance to StateBind:** All methods are feasible on the Yale Bouchet cluster. The
question is not "can we run it?" but "is the improvement worth the implementation effort?"
A pragmatic approach: (1) Run REINVENT4 as a strong 1D baseline (days of effort), (2) Run
MolCRAFT or FLOWR with pre-trained checkpoints on each EGFR pocket (1-2 weeks of effort),
(3) Fine-tune on EGFR if initial results are promising (additional 1-2 weeks).

---

### Finding 6: PoseBusters and 3D Validity Have Changed the Evaluation Landscape

Two tools have fundamentally shifted how the community evaluates 3D-generated molecules:

**PoseBusters (Buttenschoen et al., 2024):** A Python package that checks generated poses
for physical plausibility -- bond lengths, bond angles, steric clashes, internal energy.
Named one of the "Most popular 2024 physical, theoretical and computational chemistry
articles."

**PoseCheck (Harris et al., 2024):** Evaluates steric clashes, ligand strain energy, and
intramolecular interactions to identify problematic structures.

**GenBench3D key finding:** "Only between 0% and 11% of generated molecules have valid
conformations" before local relaxation. After relaxation, validity improves by 40%+ for all
methods.

**PoseBusters Validity Comparison:**

| Method | PB Validity Rate | Notes |
|--------|-----------------|-------|
| MolPilot (VOS) | **95.9%** | SOTA, 10%+ improvement over prior SOTA |
| FLOWR | 92% +/- 22% | Flow matching achieves near-SOTA validity |
| Pilot | 83% +/- 33% | Strong baseline |
| Pocket2Mol | 76% +/- 39% | Autoregressive has higher validity than diffusion |
| TargetDiff | 57% +/- 46% | High variance, many invalid geometries |
| DiffSBDD | 38% +/- 46% | Worst among evaluated methods |

**Key data points:**
- DiffSBDD (the method proposed in Vision idea 002) has only 38% PoseBusters validity.
- Flow matching methods (FLOWR, MolPilot) achieve >90% validity.
- This shifts the recommendation away from DiffSBDD/TargetDiff toward FLOWR/MolCRAFT.

**Relevance to StateBind:** Any publication using 3D generation MUST report PoseBusters
validity. StateBind's current SELFIES VAE achieves 99.9% chemical validity (SELFIES
guarantees it), but this is 2D validity, not 3D pose validity. A 3D method must achieve
>90% PoseBusters validity to be credible, which rules out DiffSBDD and TargetDiff without
post-hoc relaxation. FLOWR or MolPilot are the recommended choices.

---

### Finding 7: REINVENT 4.0 as the Pragmatic Strong Baseline

REINVENT 4.0 (Blaschke et al., J. Cheminformatics, 2024) is the most widely used
open-source molecular optimization tool, with 720 GitHub stars and active development
(v4.7, November 2025).

**Architecture:** RNN and Transformer-based prior models, trained on large chemical
databases. RL fine-tuning with customizable multi-component scoring functions. Supports
de novo design, scaffold hopping, R-group replacement, and linker design.

**Compute requirements:** ~8 GB CPU and GPU memory. RL fine-tuning takes minutes.

**Scoring integration:** Plugin architecture allows custom scoring components. GNINA
docking could be integrated as a scoring plugin, making REINVENT directly compatible
with StateBind's existing infrastructure.

**Active learning integration (Bhati et al., JCTC, 2024):**
- Combined REINVENT RL with ESMACS binding free energy simulations.
- Targets: 3CLpro (SARS-CoV-2 protease) and TNKS2 (tankyrase-2).
- Convergence in 3-7 active learning iterations.
- Entire batch of compounds scored in ~50 minutes wall clock time per iteration on
  Frontier supercomputer.
- Found molecules 5 kcal/mol more favorable than initial seed compounds.
- Used ChemProp QSAR model as primary scoring (weight 0.6) with QED as secondary.

**Key data points:**
- REINVENT + active learning found higher-scoring molecules than one-shot generation.
- The methodology is target-agnostic and directly applicable to EGFR.
- StateBind could run REINVENT with GNINA scoring for each EGFR state as a strong baseline.
- If REINVENT + GNINA beats the SELFIES VAE on retrospective enrichment, it strengthens
  the argument that "better generation helps" and sets the stage for 3D methods.

**Relevance to StateBind:** REINVENT should be run as a COMPARISON BASELINE, not as a
replacement. The publication narrative becomes: "We compare three generation strategies:
(1) state-conditioned SELFIES VAE (current), (2) REINVENT with state-specific GNINA
scoring (strong 1D baseline), (3) 3D pocket-conditioned generation (novel). All three
evaluated on the same unified scoring function and retrospective validation."

---

### Finding 8: Flow Matching Is Replacing Diffusion for Molecular Generation

The generative modeling paradigm for 3D molecules has shifted from diffusion (2022-2023)
to flow matching (2024-2026).

**Key flow matching methods:**

1. **FLOWR (Cremer et al., 2025):** Combines continuous and categorical flow matching with
   equivariant optimal transport. PB validity: 92%. Vina: -6.29 to -7.22. 70x faster than
   Pilot at 20 sampling steps. Introduces SPINDR benchmark (35,666 high-quality complexes).
   Supports interaction-conditioned generation (FLOWR:multi).

2. **MolFORM (ICML 2025):** Preference-aligned multi-modal flow matching. Vina: -7.60.
   Incorporates DPO and online RL for preference alignment. Achieves SOTA Vina Score.

3. **FlowMol3 (2025):** Open-source multi-modal flow matching achieving near 100% molecular
   validity with explicit hydrogens. Order of magnitude fewer parameters than comparable
   methods. Architecture-agnostic improvements via self-conditioning, fake atoms, and
   train-time geometry distortion.

4. **PropMolFlow (Nature Computational Science, Jan 2026):** Property-guided flow matching
   with SE(3)-equivariant geometry. 10x faster sampling than diffusion with 100 steps vs
   1000. Validated with DFT quantum chemistry calculations. Published in Nature Comp Sci.

**Key data points:**
- Flow matching offers 10-70x sampling speedup over diffusion.
- PoseBusters validity is consistently higher for flow methods (>90%) vs diffusion (<60%).
- The theoretical advantage: flow matching finds straighter transport paths from noise to
  molecules, requiring fewer integration steps.
- MolFORM's use of DPO for preference alignment is a methodological innovation from the
  LLM world applied to molecular generation.

**Relevance to StateBind:** If a 3D method is adopted, it should be flow-matching-based
(FLOWR or MolFORM), not diffusion-based (DiffSBDD or TargetDiff). The Vision System's
idea 002 specifically proposed DiffSBDD/TargetDiff -- this recommendation is now outdated.
FLOWR's support for interaction-conditioned generation (FLOWR:multi) is particularly
relevant: it could be extended to conformation-conditioned generation.

---

### Finding 9: The 3DSMILES-GPT Hybrid Approach Deserves Attention

3DSMILES-GPT (Chemical Science, 2025) represents a hybrid approach that treats both 2D
and 3D molecular representations as tokens in a language model.

**Architecture:** GPT-style autoregressive model pretrained on 10 million PubChem molecules,
fine-tuned on CrossDocked2020.

**Benchmark results vs baselines:**

| Method | Vina Score | QED | SAS | Speed (s/mol) | Drug-like % |
|--------|-----------|-----|-----|---------------|-------------|
| 3DSMILES-GPT | **-7.72** | **0.76** | **3.07** | **0.45** | **100%** |
| Pocket2Mol | -7.15 | 0.57 | 3.16 | 13.63 | -- |
| TargetDiff | -7.11 | 0.57 | 4.33 | 12.19 | -- |
| Lingo3DMol | -7.68 | 0.26 | 4.51 | 1.32 | -- |
| Reference | -7.45 | 0.48 | -- | -- | -- |

**Key data points:**
- QED improves by 33% over baselines.
- 3x faster than the next fastest method (0.45s vs 1.32s per molecule).
- 99% validity, 89% diversity.
- 53% of generated molecules have better binding affinity than reference compounds.

**Relevance to StateBind:** 3DSMILES-GPT is conceptually interesting for StateBind because
it bridges 1D (SMILES/SELFIES) and 3D representations. StateBind's current VAE generates
SELFIES strings; 3DSMILES-GPT shows that a language-model approach can incorporate 3D
pocket information while maintaining the computational efficiency of sequence generation.
A StateBind variant could: (1) Encode pocket conformation as 3D tokens, (2) Generate
molecules as 3DSMILES tokens, (3) Directly produce binding poses without separate docking.
This is a less radical change than adopting a full 3D diffusion/flow model.

---

### Finding 10: TacoGFN and GFlowNet-Based Methods Offer a Different Paradigm

TacoGFN (TMLR 2024) frames pocket-conditioned generation as an RL problem, using
GFlowNets to sample molecules with probabilities proportional to reward.

**CrossDocked2020 results:**
- Median Vina Dock: -8.44 kcal/mol (SOTA among RL methods)
- Success rate: 56.0%
- Novel hit rate: 52.63%
- Median docking score: -8.82 kcal/mol
- Fragment-based construction from synthetically accessible virtual library.

**Key advantage:** GFlowNets naturally explore diverse modes of the reward landscape,
generating structurally diverse molecules rather than mode-collapsing to a single optimum.
This is directly relevant to StateBind's diversity advantage (0.9056 vs 0.5684).

**Relevance to StateBind:** TacoGFN's reward-proportional sampling could be adapted to
a multi-pocket setting where the reward is state-specific. For each EGFR state, define
a separate GNINA docking reward; the GFlowNet would learn to generate diverse molecules
for each pocket configuration. This is a more natural framework for multi-state design
than conditioning diffusion/flow models on pocket coordinates.

---

### Finding 11: Active Learning and Iterative Generation Close the Loop

The field is moving from one-shot generation to iterative generate-score-refine loops.

**Key methods:**

1. **REINVENT + ESMACS active learning (Bhati et al., JCTC, 2024):**
   - 3-7 iterations to convergence on 3CLpro and TNKS2.
   - Batch scoring in ~50 minutes per iteration.
   - Found molecules 5 kcal/mol better than initial seeds.
   - Used ChemProp surrogate with ESMACS physics-based validation.

2. **Human-in-the-loop active learning (J. Cheminformatics, 2024):**
   - Goal-oriented molecule generation with human expert guidance.
   - Closely mimics the design-make-test-analyze cycle of wet lab experiments.

3. **Sample-efficient RL with active learning (Chemical Science, 2024):**
   - Combines RL molecular generation with active learning for oracle-efficient
     exploration.

4. **Bayesian optimization in VAE latent space (JCTC, 2024):**
   - Performs BO in the latent space of a VAE to efficiently navigate chemical space.
   - Applied to selective FLT3 kinase inhibitor generation.
   - Directly relevant: StateBind already has a VAE with a latent space.

5. **Generative multiobjective Bayesian optimization (I&EC Research, 2025):**
   - Modular "generate-then-optimize" framework for de novo multiobjective design.
   - Scalable batch evaluations for sample-efficient exploration.

**Key data points:**
- Active learning consistently outperforms one-shot generation across all studies.
- Bayesian optimization in VAE latent space is the lowest-effort upgrade for StateBind
  (the VAE already exists; add BO on top).
- The REINVENT + FEP study on Frontier supercomputer suggests that large-scale active
  learning is feasible with HPC resources.

**Relevance to StateBind:** StateBind's current pipeline is one-shot: generate 1000
molecules, score them, rank them. An active learning loop would: (1) Generate initial batch,
(2) Score with GNINA, (3) Select most promising + most uncertain, (4) Retrain/refine
generator, (5) Repeat. This could be implemented with the existing SELFIES VAE using
Bayesian optimization in latent space, requiring minimal new infrastructure.

---

### Finding 12: Apo2Mol Provides a Template for Conformation-Aware Generation

Apo2Mol (2025) is the closest existing method to what StateBind needs.

**Architecture:**
- Full-atom SE(3)-equivariant diffusion framework.
- Hierarchical graph with 4 edge types (intra-ligand, ligand-residue, intra-residue,
  inter-residue).
- Message passing with attention-based SE(3)-equivariant GNN.
- Residue-level transformations: translations, quaternion rotations, chi angle updates.
- Pocket interpolation from apo to holo via linear interpolation + Slerp (spherical linear
  interpolation of quaternions).

**Dataset:** 24,601 apo-holo-ligand triplets from PLINDER (protein-ligand interaction
dataset). Train: 23,052, Val: 1,071, Test: 478. Chronologically split.

**Results comparison:**

| Method | Avg Vina Min | QED | High Affinity Rate |
|--------|-------------|-----|-------------------|
| Apo2Mol | **-6.79** (apo), **-7.86** (holo) | **0.59** | **42.7%** (apo), **52.9%** (holo) |
| IPDiff | -6.40 | 0.51 | 29.6% (apo), 44.9% (holo) |
| TargetDiff | -5.19 | 0.37 | -- |
| DecompDiff | -6.37 | 0.56 | -- |

**Key insight:** Apo2Mol's pocket interpolation mechanism could be adapted for StateBind's
multi-state setting. Instead of interpolating from apo to holo, interpolate between
conformational states (DFGin/aCin <-> DFGin/aCout <-> DFGout/aCin <-> DFGout/aCout).

**Relevance to StateBind:** Apo2Mol demonstrates that conformation-aware 3D generation is
tractable and produces meaningful improvements (1.4 kcal/mol better than IPDiff on apo
structures). Its architecture could be extended to a multi-state formulation where the
conformational state is an explicit input to the diffusion process. This is the most
promising technical direction for a high-impact publication.

---

### Finding 13: FLOWR's Interaction-Conditioned Generation Opens New Doors

FLOWR (Cremer et al., 2025) introduces FLOWR:multi, a variant that generates molecules
conditioned on predefined interaction profiles.

**SPINDR benchmark results:**

| Metric | FLOWR (100 steps) | Pilot |
|--------|-------------------|-------|
| PB Validity | 0.88 +/- 0.21 | 0.71 +/- 0.18 |
| Vina Score | -6.93 +/- 0.92 | -6.30 +/- 0.96 |
| Vina Minimized | -7.22 +/- 0.92 | -- |
| Interaction Recovery (no H) | 47.1% | 43.2% |
| Success Rate | 90.4% | 75.5% |
| FLOWR:multi Interaction Recovery | **76.1%** | -- |
| Inference Time | 12.05s/target | 295.42s/target |

**Key data points:**
- FLOWR:multi achieves 76.1% interaction recovery when given a target interaction profile.
- Standard FLOWR achieves 47.1% interaction recovery without conditioning.
- 24.5x faster than Pilot at 100 steps; 70x faster at 20 steps.
- SPINDR dataset (35,666 complexes) is higher quality than CrossDocked2020.

**Relevance to StateBind:** FLOWR:multi's interaction conditioning could be extended to
conformation conditioning. Each EGFR state has a characteristic interaction profile
(different hydrogen bonds, hydrophobic contacts due to DFG/alphaC positions). Conditioning
on the state-specific interaction profile would produce molecules that form the correct
interactions for each conformational state. This is a more sophisticated conditioning
strategy than a one-hot state vector.

---

### Finding 14: BoKDiff Shows Alignment Methods Can Boost Existing 3D Models

BoKDiff (2025) adapts LLM alignment techniques (Best-of-K selection) to molecular diffusion.

**CrossDocked2020 results:**
- Average Vina Dock: -8.58 kcal/mol
- Success rate: 26%
- QED > 0.6, SA > 0.75
- Built on top of DecompDiff (no retraining needed).

**Key insight:** Best-of-K selection and preference alignment (also used by MolFORM with
DPO) can improve any existing 3D generator without changing the model architecture. This
is a post-hoc improvement that could be applied to any model StateBind adopts.

**Relevance to StateBind:** Even if StateBind adopts a simpler 3D generation method,
BoK-style selection using GNINA scores as the selection criterion could improve results
without additional training. Generate K=10 molecules for each pocket, select the best by
GNINA score. Simple, effective, and leverages existing infrastructure.

---

### Finding 15: The Evaluation Standards for Publication Have Evolved

Any 2026 publication on molecular generation MUST include:

1. **PoseBusters validity** (not just 2D chemical validity)
2. **Multiple docking programs** (Durian benchmark uses QuickVina2, Surflex, and GNINA)
3. **Interaction recovery metrics** (FLOWR's SPINDR benchmark standard)
4. **Realistic molecule sizes** (generated molecules should match reference molecule sizes)
5. **Diversity alongside affinity** (mode collapse must be checked)
6. **Retrospective or prospective validation** beyond CrossDocked2020

**The Durian benchmark (JCIM, Jan 2025)** evaluated 6 methods using 17 metrics across
affinity, physicochemical properties, and geometric quality, using 3 independent docking
programs to reduce false positives.

**The ICLR 2025 paper "Reframing Structure-Based Drug Design"** introduced new metrics
correlated to practical drug discovery needs rather than just Vina scores.

**Relevance to StateBind:** StateBind's evaluation framework (unified scoring, Pareto
analysis, retrospective validation, weight sensitivity) is already more rigorous than most
published 3D generation work. The retrospective enrichment evaluation is a significant
strength that most 3D generation papers lack entirely. Adding PoseBusters validity and
interaction recovery would make the evaluation comprehensive.

---

## Implications for StateBind

### Opportunities

1. **Genuine novelty in multi-conformation-conditioned 3D generation.** No existing method
   does what StateBind proposes. A 3D model that generates molecules for each of 4 EGFR
   conformational state pockets, evaluated with the existing comparison framework, is a
   publishable contribution to NeurIPS/ICML or Nature Computational Science.

2. **The existing evaluation framework is a major asset.** Most 3D generation papers only
   report CrossDocked2020 metrics. StateBind has: unified scoring, Pareto analysis,
   retrospective time-split validation, weight sensitivity analysis, and statistical testing.
   This framework applied to 3D generation would produce the most rigorous evaluation in the
   field.

3. **Pre-trained models reduce implementation effort.** MolCRAFT checkpoints on HuggingFace,
   DiffSBDD checkpoints on Zenodo, and REINVENT4 on GitHub provide ready-to-use starting
   points. Zero-shot generation for each EGFR pocket is possible within days.

4. **Active learning with existing VAE is the easiest upgrade.** Bayesian optimization in
   the SELFIES VAE latent space requires minimal new code and could improve retrospective
   enrichment.

5. **REINVENT4 comparison strengthens the narrative.** Running REINVENT4 with GNINA scoring
   for each EGFR state provides a strong 1D baseline that contextualizes both the existing
   VAE and any new 3D method.

6. **Flow matching methods are fast enough for iterative design.** FLOWR at 20 steps
   generates molecules in seconds per target, enabling active learning loops that were
   impractical with diffusion methods taking minutes per molecule.

### Risks and Caveats

1. **3D methods may not improve retrospective enrichment.** The 10x enrichment result is
   StateBind's headline finding. If a 3D method does not improve this metric, the
   architectural change adds complexity without clear benefit.

2. **The "Do 3D Methods Really Dominate?" finding is concerning.** 1D/2D methods with
   docking oracles achieve competitive results. StateBind must demonstrate that 3D
   conditioning provides value BEYOND what docking-in-the-loop can achieve.

3. **PoseBusters validity is a new requirement.** DiffSBDD (38% validity) and TargetDiff
   (57% validity) would embarrass the project if used without post-hoc relaxation. Only
   FLOWR (92%) and MolPilot (96%) meet the standard.

4. **Implementation complexity.** Moving from SELFIES VAE to a 3D equivariant model is a
   substantial engineering effort. The SELFIES VAE is ~300 lines of PyTorch; a full FLOWR
   implementation is thousands of lines with complex geometric operations.

5. **Scope creep risk.** The project's strength is the comparison framework, not the
   generative model. Spending months on a state-of-the-art 3D generator could delay
   publication without corresponding scientific insight.

6. **Training data limitation.** CrossDocked2020 contains docked poses, not crystallographic
   poses. Fine-tuning on EGFR specifically requires curating high-quality protein-ligand
   complexes from PDB, which is additional effort.

### Recommended Next Steps

**Tier 1: Minimum Viable Experiments (1-2 weeks each)**

1. **Run REINVENT4 on EGFR states.** Configure REINVENT4 with GNINA docking as a scoring
   component for each EGFR state pocket. Generate 1000 molecules per state. Score with the
   existing unified scoring function. Compare to SELFIES VAE. This establishes a strong 1D
   baseline and directly addresses reviewer concern #6 ("No comparison to existing
   generative models").

2. **Zero-shot MolCRAFT on EGFR pockets.** Use MolCRAFT pre-trained checkpoint to generate
   molecules for each of the 4 EGFR pockets. No retraining -- just inference with different
   pocket conditioning. Score and compare.

3. **Bayesian optimization in VAE latent space.** Implement BO over the existing SELFIES VAE
   latent space using GNINA score as the acquisition function. This tests whether iterative
   refinement improves retrospective enrichment without changing the generator.

**Tier 2: Publication-Quality Experiments (1-2 months)**

4. **Conformation-conditioned FLOWR.** Adapt FLOWR to condition on pocket conformation by
   encoding the conformational state as part of the pocket representation. Train on
   CrossDocked2020 with EGFR family structures. Evaluate with PoseBusters validity +
   interaction recovery + retrospective enrichment.

5. **Multi-method comparison paper.** Compare: (a) SELFIES VAE + one-hot state, (b) SELFIES
   VAE + BO active learning, (c) REINVENT4 + GNINA per-state, (d) MolCRAFT zero-shot per-
   pocket, (e) Conformation-conditioned FLOWR. All evaluated on the unified scoring function,
   Pareto analysis, and retrospective validation. This is a complete benchmark paper.

**Tier 3: High-Impact Novel Contribution (2-4 months)**

6. **StateBind-3D: Conformation-conditioned flow matching.** Design a novel architecture
   that takes pocket coordinates + conformational state embedding as input and generates 3D
   molecules via flow matching. The conformational state embedding captures the DFG/alphaC
   classification beyond raw pocket coordinates. Train on kinase structures from KLIFS/PDB.
   Evaluate on EGFR + 2-3 additional kinases for generalization. This is a NeurIPS/ICML
   paper.

---

## References

1. Schneuing, A., Du, Y., Harris, C., et al. "Structure-based drug design with equivariant
   diffusion models." Nature Computational Science (2024). [DiffSBDD]

2. Guan, J., Qian, W.W., Peng, X., et al. "3D Equivariant Diffusion for Target-Aware
   Molecule Generation and Affinity Prediction." ICLR (2023). [TargetDiff]

3. Peng, X., Luo, S., Guan, J., et al. "Pocket2Mol: Efficient Molecular Sampling Based on
   3D Protein Pockets." ICML (2022). [Pocket2Mol]

4. Guan, J., Qian, W.W., et al. "DecompDiff: Diffusion Models with Decomposed Priors for
   Structure-Based Drug Design." ICML (2024). [DecompDiff]

5. Qu, Y., Qiu, T., et al. "MolCRAFT: Structure-Based Drug Design in Continuous Parameter
   Space." ICML (2024). [MolCRAFT]

6. Cremer, J., et al. "FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and
   Fragment-Based Ligand Generation." arXiv:2504.10564 (2025). [FLOWR]

7. "MolFORM: Preference-Aligned Multimodal Flow Matching for Structure-Based Drug Design."
   ICML (2025). [MolFORM]

8. Zeng, C., Jin, J., Ambrose, C., et al. "PropMolFlow: Property-guided molecule generation
   with geometry-complete flow matching." Nature Computational Science (2026). [PropMolFlow]

9. Dunn, I. & Koes, D.R. "FlowMol3: Flow Matching for 3D De Novo Small-Molecule
   Generation." JCIM (2025). [FlowMol3]

10. Shi, Y., et al. "3DSMILES-GPT: 3D molecular pocket-based generation with token-only
    large language model." Chemical Science (2025). [3DSMILES-GPT]

11. Pinheiro, V.L.S., et al. "Structure-based drug design by denoising voxel grids."
    arXiv:2405.03961 (2024). [VoxBind]

12. Yang, Z., et al. "Protein-Ligand Interaction Prior for Binding-aware 3D Molecule
    Diffusion Models." ICLR (2024). [IPDiff]

13. Li, et al. "Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion Models."
    arXiv:2511.14559 (2025). [Apo2Mol]

14. Shen, T., et al. "TacoGFN: Target-conditioned GFlowNet for Structure-based Drug
    Design." TMLR (2024). [TacoGFN]

15. Blaschke, T., et al. "Reinvent 4: Modern AI-driven generative molecule design." Journal
    of Cheminformatics 16:20 (2024). [REINVENT4]

16. Bhati, A.P., et al. "Optimal Molecular Design: Generative Active Learning Combining
    REINVENT with Precise Binding Free Energy Ranking Simulations." JCTC (2024).

17. Harris, C., et al. "GenBench3D: Benchmarking structure-based three-dimensional molecular
    generative models using ligand conformation quality matters." arXiv:2407.04424 (2024).

18. Buttenschoen, M., et al. "PoseBusters: AI-based docking methods fail to generate
    physically valid poses." Chemical Science (2024).

19. Gao, W., et al. "Structure-based Drug Design Benchmark: Do 3D Methods Really Dominate?"
    arXiv:2406.03403 (2024).

20. Nie, Z., Zhao, Z., et al. "Durian: A Comprehensive Benchmark for Structure-Based 3D
    Molecular Generation." JCIM (2025).

21. "MolPilot: Piloting Structure-Based Drug Design via Modality-Specific Optimal Schedule."
    ICML (2025). [MolPilot]

22. Zhou, G., et al. "PocketXMol: Unified modeling of 3D molecular generation via atomic
    interactions." Cell (2026). [PocketXMol]

23. "BoKDiff: Best-of-K diffusion alignment for target-specific 3D molecule generation."
    Bioinformatics Advances (2025). [BoKDiff]

24. Korshunova, M., et al. "FREED++: Improving RL Agents for Fragment-Based Molecule
    Generation by Thorough Reproduction." arXiv:2401.09840 (2024). [FREED++]

25. "A large language model-guided reinforcement learning framework for EGFR anticancer drug
    design." J. Computer-Aided Molecular Design (2025).

26. "Human-in-the-loop active learning for goal-oriented molecule generation." J.
    Cheminformatics (2024).

27. "Sample efficient reinforcement learning with active learning for molecular design."
    Chemical Science (2024).

28. "Bayesian Optimization in the Latent Space of a Variational Autoencoder for the
    Generation of Selective FLT3 Inhibitors." JCTC (2024).

29. "De novo generation of multi-target compounds using deep generative chemistry." Nature
    Communications (2024). [POLYGON]

30. "Reprogramming Pretrained Target-Specific Diffusion Models for Dual-Target Drug Design."
    arXiv:2410.20688 (2024).

31. "Comprehensive Benchmark Study of Diffusion-Based 3D Molecular Generation Models." ACS
    Omega (2025).

32. "Benchmarking 3D Structure-Based Molecule Generators." JCIM (2025).
