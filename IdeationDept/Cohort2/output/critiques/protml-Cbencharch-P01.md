---
agent: Maverick Protein ML Expert
round: 3
date: 2026-04-09
type: critique
proposal_reviewed: bencharch-P01
---

# Critique: StateBind-Bench -- The First Benchmark for Conformational State-Conditioned Molecular Generation

## Reviewing Agent

Maverick Protein ML Expert (protml) -- expertise in protein language models, learned
pocket representations (ESM-2, ProstT5, EPoCS), protein-ligand co-embedding methods
(DrugCLIP, ProFSA), conformational ensemble prediction (AlphaFlow, AF2 subsampling),
and pre-trained molecular scoring (Uni-Mol, GEM, GROVER).

## Proposal Summary

bencharch-P01 proposes "StateBind-Bench," a four-task benchmark for evaluating
molecular generative models on their ability to produce conformational-state-appropriate
molecules for kinase targets. Phase 1 covers EGFR (4 DFG/aC states), Phase 2 extends
to ABL1 and BRAF, and Phase 3 launches a community challenge. The four tasks are:
(1) state-conditioned generation quality, (2) state specificity, (3) retrospective
enrichment, and (4) multi-objective Pareto optimization. The benchmark packages
StateBind's existing pipeline with 6 baseline methods, containerized evaluation
infrastructure, a HuggingFace dataset, and a PapersWithCode leaderboard. Primary venue
is JCIM; secondary is NeurIPS Evaluations and Datasets Track.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** A well-designed community resource that fills a genuine benchmark
gap, but it systematically undervalues the protein representation dimension -- the
benchmark measures whether methods are state-conditioned but never asks whether
*better pocket representations* improve state conditioning, which is arguably the more
important scientific question for the ML community.

---

## Strengths

### 1. The Benchmark Gap Is Real and Well-Documented

The proposal correctly identifies that no existing benchmark evaluates conformational
state-conditioned molecular generation. The systematic survey of CrossDocked2020,
MOSES, GuacaMol, TDC, DUD-E, PDBbind, GenBench3D, Durian, and Kinase-Bench is
thorough. The citation trajectory analysis (MoleculeNet 3,000+, DUD-E 2,500+, MOSES
770+) provides strong evidence that benchmark papers command outsized impact. This is
a genuine white-space opportunity.

### 2. Task Design Is Sound at the Molecular Level

The State Specificity Index (SSI), diagonal dominance metric, and cross-state docking
matrix are well-formulated. SSI = sigma(d_1,...,d_K)/|mean(d_1,...,d_K)| is a clean,
interpretable metric that directly measures what we care about: does the molecule
prefer one state over others? The diagonal dominance metric (fraction of rows where
designed-for state is the best score) has a clear random baseline (0.25 for K=4),
making it easy to interpret statistical significance.

### 3. Reproducibility Infrastructure Is Exemplary

The 15-item reproducibility checklist, Docker/Singularity containers, HuggingFace
dataset with Croissant metadata, Zenodo DOI archive, pre-computed scores for
GNINA-free evaluation, and pinned dependencies represent the gold standard for
benchmark design. The Singularity/Apptainer support is particularly important for
HPC adoption. This directly addresses the reproducibility concerns raised by the
TDC 2026 audit.

### 4. Honest Risk Assessment

The proposal acknowledges the possibility that all baselines may be state-agnostic
(a "null result") and correctly frames this as a positive finding rather than a
failure. This is scientifically honest and strategically sound -- it positions the
benchmark as revealing a capability gap, not as a competition StateBind must win.

### 5. Time-Split Methodology Is Appropriate

The dual time-split design (pre-2010/pre-2015 cutoffs) with Bemis-Murcko scaffold
exclusion follows Sheridan (2013) best practice and avoids the temporal leakage that
plagues many benchmarks. The bootstrap confidence intervals over 1,000 resamples
acknowledge the small-N limitation responsibly.

---

## Weaknesses (with Severity and Addressable?)

### W1. No Benchmark Task for Pocket Representation Quality [Severity: HIGH; Addressable: YES]

This is the central gap from a protein ML perspective. The four proposed tasks all
take a pocket structure + state label as input and evaluate the quality of the
*generated molecules*. None of them ask: given the same generative architecture, does
a richer pocket representation improve state-conditioned generation?

Specifically, the benchmark should include a "representation ablation" task:

- **Input variant A:** 9D hand-crafted geometric features (StateBind's current atlas)
- **Input variant B:** ESM-2 650M mean-pooled pocket embeddings (1280D, sequence-derived)
- **Input variant C:** ProstT5 3Di-conditioned pocket embeddings (1024D, structure-aware)
- **Input variant D:** KLIFS 85-residue interaction fingerprint
- **Input variant E:** Concatenated ESM-2 + 9D features (1289D)

The evaluation question: holding the generative model fixed (StateBind's VAE), does
the representation used to condition generation affect SSI, diagonal dominance, and
retrospective enrichment?

This is important because it addresses a question the ML community actually cares
about: does the protein representation matter for this task, or is any state signal
sufficient? If 9D features perform identically to 1280D ESM-2 embeddings, that tells
us something fundamental about the information content required for state conditioning.
If ProstT5 (structure-conditioned) dramatically outperforms ESM-2 (sequence-only),
that validates the structural conditioning hypothesis.

Without this task, the benchmark measures molecular generation capability but not the
protein understanding that should underpin state-conditioned design.

**Recommendation:** Add a Task 0 or Task 1b: "Pocket Representation Ablation" that
evaluates how pocket encoding quality affects downstream generation metrics. This
could be positioned as one of the benchmark's most novel contributions -- no existing
benchmark studies this axis.

### W2. Baseline Methods Omit Protein-Conditioned Generative Models [Severity: MEDIUM-HIGH; Addressable: YES]

The six proposed baselines (StateBind VAE, REINVENT 4, DiffSBDD, TargetDiff,
Pocket2Mol, Random) are all established methods but none of them use modern
protein-aware representations. This matters because:

- **DiffSBDD, TargetDiff, and Pocket2Mol** all condition on raw atomic coordinates of
  the pocket. They have no mechanism to incorporate learned pocket representations or
  protein language model features. They will condition on structure but will treat
  conformational states as geometric patterns, not as biologically meaningful entities.

- **REINVENT 4** uses a SMILES-based RL approach with a scoring function. It receives
  state information only through the docking score feedback, not through any pocket
  representation.

- No baseline uses DrugCLIP-guided generation, AlphaFold-informed pocket conditioning,
  or protein language model-conditioned architectures.

Missing baselines that would strengthen the benchmark:

| Method | Why Include |
|--------|-------------|
| DrugCLIP-guided generation | Tests whether co-embedding-informed scoring improves state specificity |
| PILOT (Cremer et al., NeurIPS 2024) | Equivariant diffusion with multi-objective guidance; tests whether richer conditioning helps |
| DecompDiff | Decomposed ligand generation with pocket awareness |
| A pLM-conditioned baseline | Any method that takes ESM-2/ProstT5 pocket embeddings as conditioning input |

Including at least one protein-language-model-conditioned method would make the
benchmark far more informative for the ML community. If such a method does not
currently exist for molecular generation (as opposed to virtual screening), that
itself is a finding worth highlighting: the benchmark reveals that the field lacks
protein-representation-aware generators.

### W3. GNINA-Only Scoring Creates a Single-Metric Bottleneck [Severity: MEDIUM; Addressable: YES]

The benchmark uses GNINA CNN affinity as the primary structural evaluation metric
across all four tasks. While GNINA is a reasonable choice (physics-informed, GPU-
accelerated, open-source), relying on a single scoring oracle creates several
problems:

1. **Metric gaming.** Methods can overfit to GNINA's learned scoring function without
   improving actual binding. The proposal acknowledges this with anti-gaming measures
   (hidden held-out metrics, score distribution reporting), but these are band-aids.

2. **GNINA's known limitations.** GNINA's CNN scoring was trained primarily on
   PDBbind, which skews toward high-affinity crystallized complexes. It may not
   accurately score state-specific interactions, particularly for DFG-out pockets
   where fewer training examples exist. The benchmark's core claim -- measuring
   state specificity -- rests entirely on GNINA's ability to discriminate state-
   appropriate from state-inappropriate molecules.

3. **Co-embedding scores as an orthogonal axis.** DrugCLIP (Gao et al., Science 2025)
   achieves 80.93% AUROC on DUD-E in zero-shot mode, comparable to GNINA. Its
   pocket-ligand embedding scores are computationally orthogonal to docking -- they
   capture different aspects of molecular compatibility. Including DrugCLIP scores as
   a secondary evaluation axis would: (a) provide a complementary signal that is harder
   to game, (b) test whether GNINA and co-embedding methods agree on state specificity,
   and (c) engage the representation learning community who are more likely to adopt
   the benchmark.

4. **Uni-Mol Docking V2** achieves 77+% of poses with RMSD < 2.0 A on PoseBusters
   and could serve as another orthogonal scoring method, since it uses a different
   architecture and training set than GNINA.

**Recommendation:** Report DrugCLIP co-embedding scores alongside GNINA for all tasks.
If DrugCLIP and GNINA disagree on which molecules are state-specific, that is itself
an interesting finding. If they agree, it strengthens the benchmark's conclusions.
This does not add significant compute cost (DrugCLIP scoring is ~1ms per pair vs
~30s for GNINA).

### W4. Multi-Kinase Extension Ignores the Structure Prediction Problem [Severity: MEDIUM; Addressable: YES]

Phase 2 proposes extending to ABL1 and BRAF, and Phase 3 envisions blind challenges
on ALK, JAK2, and SRC. The proposal states that pocket structures will be "extracted
from PDB using KLIFS state annotations." This works for well-characterized kinases
(ABL1 has 200+ PDB structures, BRAF 100+), but breaks down for:

- **Kinases with sparse structural coverage.** ALK has limited DFG-out crystal
  structures. JAK2 has few aC-out structures. SRC has reasonable coverage but
  specific mutant states may lack experimental data.

- **The blind challenge design.** Releasing pocket structures without state labels for
  participants to predict state-appropriate molecules assumes that high-quality
  experimental structures exist for all states of the challenge kinases. If they do
  not, the benchmark must either (a) use computationally predicted structures (AF2,
  ESMFold) or (b) restrict to kinases with complete experimental coverage.

The proposal should explicitly address how it will handle structural gaps:

1. **AlphaFold2 with MSA subsampling** (Wayment-Steele et al., Nature Communications
   2024) can predict kinase conformational state populations with >80% accuracy. For
   kinases lacking experimental structures in specific states, AF2-generated structures
   could fill the gap -- but with known caveats (default AF2 predicts only DFG-in;
   DFG-Phe/C-Glu regions have lower pLDDT ~75%).

2. **ESMFold** (Lin et al., 2023) could provide rapid initial structure screening at
   76% accuracy (vs AF2's 88%), with 10-30x speed advantage.

3. **AlphaFold2-RAVE** (Monteiro da Silva et al., JCIM 2024) combines AF2 subsampling
   with enhanced sampling to predict DFG conformation preferences, which is directly
   relevant for generating state-labeled structures computationally.

Without addressing this, the multi-kinase extension and community challenge are
aspirational rather than concrete.

### W5. Leaderboard Design May Not Attract the ML Community [Severity: LOW-MEDIUM; Addressable: YES]

The leaderboard uses PapersWithCode (primary) and HuggingFace Spaces (secondary).
This is reasonable for the cheminformatics community but may miss the broader ML
audience. Several design choices reduce ML-community friendliness:

1. **GNINA dependency for custom scoring.** While pre-computed scores are available as
   fallback, ML researchers who want to evaluate new generated molecules (not just
   compare against pre-computed baselines) must install GNINA. GNINA requires CUDA
   and specific library versions. Many ML labs work primarily with PyTorch and may not
   have the cheminformatics stack. The `statebind-bench evaluate` command requiring
   GNINA for full evaluation is a barrier.

2. **No standardized pocket conditioning format.** ML researchers need a clear API for
   how to condition their generative model on the pocket. The submission format (CSV
   with SMILES + state label) captures the output but not the input conditioning. The
   benchmark should provide standardized pocket representations (raw PDB, voxelized
   grid, graph, ESM-2 embedding, point cloud) so that diverse architectures can
   participate without each team needing to build their own pocket featurizer.

3. **No pre-trained model zoo.** The benchmark ships 6 baseline *results* but not
   easily runnable baseline *models*. For ML researchers, the most useful thing is a
   model checkpoint they can fine-tune or compare against. HuggingFace Model Hub
   hosting of baseline checkpoints (StateBind VAE, REINVENT 4 fine-tuned checkpoint)
   would dramatically lower the entry barrier.

**Recommendation:** (a) Provide pocket representations in multiple formats (PDB,
voxelized grid, ESM-2 embeddings, point cloud, graph) alongside the raw structures.
(b) Host baseline model checkpoints on HuggingFace Model Hub. (c) Provide a Python
API (`statebind_bench.load_pocket("EGFR", "DFGin_aCin", format="esm2_embedding")`)
that returns pocket features in the user's preferred format.

### W6. The 9D Features Are a Confound in the Scoring Function [Severity: LOW-MEDIUM; Addressable: YES]

The unified scoring function includes "state specificity" as a 0.15-weighted component.
This state specificity is computed using the 9D geometric feature atlas. If the
benchmark is testing whether generative models are state-conditioned, but the *scoring
function itself* uses hand-crafted state features, there is a circularity risk: the
benchmark rewards methods that produce molecules with different docking scores across
states, but the scoring function's own state-specificity component already biases
toward this outcome.

The proposal partially addresses this by recommending raw GNINA scores as the primary
leaderboard metric and composite scores as supplementary. But the paper's analysis
sections (Tasks 2 and 4) appear to use the composite score. The distinction should be
made sharper.

**Recommendation:** Use raw GNINA docking scores as the *only* metric for Tasks 1 and
2 (generation quality and state specificity). Reserve the composite scoring function
for Task 4 (Pareto optimization) where it is the explicit object of evaluation.

---

## Feasibility Assessment

The Phase 1 timeline of 8 weeks is aggressive but feasible, with caveats:

- **Data packaging (Weeks 1-2):** Realistic. StateBind's existing artifacts provide
  most of the required data. The main work is reformatting and documentation.

- **Baseline runs (Weeks 3-5):** This is the riskiest phase. Installing and running
  DiffSBDD, TargetDiff, and Pocket2Mol from published codebases is notoriously
  fragile. The proposal correctly identifies dependency conflicts as a risk and
  proposes dropping non-functional baselines. Having a minimum of 3 baselines is
  appropriate, but the time estimate may be optimistic.

- **Compute (1,300-2,500 GPU-hours):** Feasible on Bouchet. 288,000 GNINA docking
  evaluations at 30s each is the bottleneck. Using the `gpu` partition (RTX 5000 Ada)
  or `gpu_h200` (H200) and running as array jobs would parallelize this effectively.

- **NeurIPS 2026 deadline (May 6, 27 days):** Not feasible for a polished submission.
  The JCIM strategy is correct for Phase 1.

- **Phase 2 (Months 3-5):** Realistic for ABL1 (abundant data). BRAF may require more
  curation effort due to the paradoxical activation conformations. Adding structure
  prediction for gap-filling (my W4 concern) would add 2-4 weeks.

- **Phase 3 (Months 6-12):** The community challenge is aspirational and depends on
  Phases 1 and 2 succeeding. Targeting 10-20 groups is reasonable given CACHE's 23.

**Overall feasibility: 7/10.** Phase 1 is achievable. Phase 2 is achievable with
caveats. Phase 3 is speculative.

---

## Suggested Modifications

### Modification 1: Add a Pocket Representation Ablation Task (Priority: ESSENTIAL)

Add a "Task 1b: Representation Ablation" that holds the generative architecture fixed
(StateBind's VAE) and varies only the pocket conditioning input:

| Variant | Pocket Representation | Dimensionality |
|---------|----------------------|---------------|
| A | 9D geometric features (current) | 9 |
| B | KLIFS 85-residue interaction fingerprint | 85 |
| C | ESM-2 650M mean-pooled pocket embedding | 1280 |
| D | ProstT5 3Di-conditioned pocket embedding | 1024 |
| E | ESM-2 + 9D concatenation | 1289 |

Evaluate each variant on SSI, diagonal dominance, and EF@10 from Task 2 and Task 3.
This transforms the benchmark from "does state conditioning help?" (which StateBind
already showed) into "what information about the pocket is sufficient/necessary for
state conditioning?" -- a far more interesting question for the ML community.

**Compute cost:** Extracting ESM-2 and ProstT5 embeddings for 4 EGFR structures takes
minutes. Retraining the VAE with different conditioning inputs takes ~2 GPU-hours per
variant. Total additional cost: ~10 GPU-hours. Negligible compared to the 1,300+
GPU-hours for docking.

This modification would also make the benchmark paper significantly more novel. The
representation ablation results would be a standalone contribution even without the
full benchmark infrastructure.

### Modification 2: Include DrugCLIP Co-Embedding Scores as Secondary Evaluation Axis (Priority: HIGH)

For all four tasks, report DrugCLIP pocket-ligand co-embedding scores alongside GNINA
CNN affinity. DrugCLIP is:

- Open-source (GitHub: idruglab/DrugCLIP)
- Pre-trained on PDB protein-ligand complexes
- Computationally cheap (~1ms per molecule-pocket pair)
- Orthogonal to physics-based docking

The analysis section should include a correlation analysis: do GNINA and DrugCLIP
agree on which molecules are state-specific? If the two scoring methods disagree,
that exposes a fundamental question about what "state specificity" means at the
scoring level.

### Modification 3: Provide Multi-Format Pocket Representations (Priority: HIGH)

Ship the dataset with pre-computed pocket representations in multiple formats:

1. Raw PDB coordinates (current plan)
2. PDBQT (current plan)
3. ESM-2 650M pocket embeddings (1280D vector per state) -- new
4. ProstT5 3Di-conditioned embeddings (1024D vector per state) -- new
5. Voxelized 3D grid (32x32x32 at 1A resolution) -- new
6. Pocket graph (atoms as nodes, bonds/contacts as edges) -- new
7. Point cloud (atomic coordinates + features) -- new
8. KLIFS interaction fingerprint (85-bit) -- new

This lowers the entry barrier for diverse ML architectures (transformers, GNNs,
3D CNNs, point cloud networks, equivariant models) and positions the benchmark as
representation-agnostic rather than coordinate-only.

### Modification 4: Address Structure Prediction for Multi-Kinase Extension (Priority: MEDIUM)

For Phase 2 and especially Phase 3, explicitly document:

- Which kinase-state combinations have experimental structures vs. require prediction
- The AF2 subsampling protocol for generating missing state structures
- Quality thresholds (pLDDT cutoff, DFG-Phe confidence) for predicted structures
- A flag in the dataset distinguishing experimental from predicted structures

This prevents the multi-kinase extension from being blocked by structural gaps and
transparently handles the structure prediction uncertainty.

### Modification 5: Sharpen the Scoring Function Role (Priority: MEDIUM)

- Tasks 1 and 2: Use raw GNINA CNN affinity scores only. No composite scoring.
- Task 3: Use GNINA + enrichment metrics. Composite score as supplementary.
- Task 4: Composite scoring function is the explicit evaluation object. Weight
  sensitivity analysis is appropriate here.

This eliminates the circularity concern where the scoring function's built-in
state-specificity component biases the state specificity evaluation.

---

## Alternative Approaches

### Alternative A: Benchmark the Representation, Not the Generator

Instead of a benchmark that evaluates generative models, consider a benchmark that
evaluates *pocket representations* for state discrimination. The central question
becomes: which representation of a kinase pocket best captures conformational state
information for downstream molecular design?

Tasks:
1. State classification accuracy (can the representation predict DFG/aC state?)
2. State similarity ranking (do representations of similar states cluster?)
3. Binding affinity prediction (does the representation improve scoring?)
4. Downstream generation quality (does the representation improve generation?)

This would be a more focused contribution that directly engages the protein ML
community. However, it is a narrower paper than the proposed generative benchmark.

**Recommendation:** Do not replace the current proposal. Instead, incorporate this as
a subtask (my proposed Task 1b) within the broader benchmark.

### Alternative B: Paired Benchmark Paper

Publish two papers simultaneously:
1. StateBind-Bench (the generative benchmark, JCIM) -- the current proposal
2. KinaseRepBench (a pocket representation benchmark, NeurIPS E&D Track or
   Bioinformatics) -- evaluating ESM-2, ProstT5, EPoCS, 9D features, KLIFS
   fingerprints for kinase state discrimination

The second paper would use the first paper's infrastructure and data, with additional
representation-specific evaluation. This doubles the publication output and targets
two distinct communities (cheminformatics + protein ML).

**Risk:** Two papers from the same dataset may appear thin unless each has distinct,
substantial contributions.

---

## Impact on Publication Narrative

The modifications I propose would strengthen the publication narrative in several ways:

1. **Broader audience.** Including protein representation evaluation engages the
   protein ML community (ESM, AlphaFold, ProstT5 researchers), not just the molecular
   generation community. This widens the citation pool.

2. **Deeper scientific question.** "Does state conditioning help?" is a yes/no
   question the existing StateBind pipeline already answered (yes, 10x enrichment).
   "What representation of state information is optimal?" is a richer question that
   justifies a benchmark paper's existence.

3. **NeurIPS positioning.** If the benchmark includes a representation ablation task
   and multi-format pocket representations, it becomes substantially more appealing
   for NeurIPS E&D Track. The 2026 chairs explicitly favor papers that "articulate
   their evaluative role" -- a benchmark that evaluates both generators *and*
   representations has a stronger evaluative thesis.

4. **Reviewer preemption.** The most likely reviewer criticism from an ML perspective
   is: "This benchmark only tests docking scores, which are noisy and unreliable.
   Where is the learned scoring evaluation?" Including DrugCLIP scores and the
   representation ablation directly addresses this.

5. **Longevity.** As new protein language models emerge (ESM-3, ESM Cambrian, future
   ProstT5 variants), the representation ablation task becomes a recurring evaluation
   axis. Methods papers will cite StateBind-Bench not just for molecular generation
   evaluation but for pocket representation evaluation -- doubling the citation
   surface area.

The 10x enrichment headline result remains the anchor. But the story expands from
"state conditioning works" to "state conditioning works, the quality of state
representation matters, and here is how to measure both."

---

## References

1. Lin, Z., Akin, H., Rao, R., et al. (2023). Evolutionary-scale prediction of atomic-level protein structure with a language model. *Science*, 379(6637), 1123-1130.

2. Heinzinger, M., Weissenow, K., Kutuzova, S., et al. (2024). ProstT5: Bilingual Language Model for Protein Sequence and Structure. *bioRxiv/NAR*.

3. Gao, K., Wu, L., Zhu, J., et al. (2025). Genome-scale virtual screening with DrugCLIP. *Science*, 387, 531-537.

4. Gao, K., Wu, L., Zhu, J., et al. (2023). DrugCLIP: Contrastive Protein-Molecule Representation Learning for Virtual Screening. *NeurIPS 2023*.

5. Gao, Z., et al. (2024). ProFSA: Self-supervised pocket pre-training via protein fragment-surrogate alignment. *ICLR 2024*.

6. Wayment-Steele, H.K., et al. (2024). Predicting multiple conformations via sequence clustering and AlphaFold2. *Nature Communications*, 15, 6168.

7. Monteiro da Silva, G., et al. (2024). AlphaFold2-RAVE: Predicting kinase DFG conformation free energies. *JCIM*, 64(10), 4069-4080.

8. Jing, B., Erber, E., Guan, J., Drorr, O., Corso, G., Jaakkola, T. (2024). AlphaFlow: Autonomous iterative structure generation from sequence. *ICML 2024*.

9. Yang, K.K., et al. (2026). Kinase classification with ESM-2 layer selection. *Bioinformatics*.

10. Zhou, G., Gao, Z., Ding, Q., et al. (2023). Uni-Mol: A Universal 3D Molecular Representation Learning Framework. *ICLR 2023*.

11. Rong, Y., Bian, Y., Xu, T., et al. (2020). Self-Supervised Graph Transformer on Large-Scale Molecular Data. *NeurIPS 2020*.

12. Cremer, J., et al. (2024). PILOT: equivariant diffusion for pocket-conditioned de novo ligand generation with multi-objective guidance. *NeurIPS Workshop*.

13. Baillif, B., Cole, J., et al. (2024). Benchmarking structure-based three-dimensional molecular generative models using GenBench3D. *arXiv:2407.04424*.

14. EPoCS: Mapping the space of protein binding sites using ESM-2 and Voronoi tessellation. (2025).

15. AANet (2025). Virtual screening under structural uncertainty via alignment-and-aggregation.

16. Fang, X., Liu, L., et al. (2022). Geometry-enhanced molecular representation learning for property prediction. *Nature Machine Intelligence*, 4, 127-134.

17. van Linden, O.P.J., Kooistra, A.J., et al. (2014). KLIFS: A Knowledge-Based Structural Database To Navigate Kinase-Ligand Interaction Space. *J. Med. Chem.*, 57(2), 249-277.

18. ProteinBench (2024). Evaluation framework for conformational prediction methods.

19. Mirdita, M., Schutze, K., Moriwaki, Y., et al. (2022). ColabFold: making protein folding accessible to all. *Nature Methods*, 19, 679-682.

20. Abramson, J., et al. (2024). Accurate structure prediction of biomolecular interactions with AlphaFold 3. *Nature*, 630, 493-500.
