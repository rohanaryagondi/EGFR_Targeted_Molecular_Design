# Deep Research Briefing: Foundation Models, ML Architecture & Benchmark Comparisons

**Agent mission:** Survey molecular foundation models, advanced ML architectures, and
published generative method benchmarks to identify what StateBind should upgrade to
and benchmark against for publication at a top venue (Nature Computational Science,
JCIM, Nature Methods, or similar).

**Read only this file.** It contains all the project context you need.

---

## 1. What StateBind Is

StateBind is a computational biology pipeline that tests whether **conformational
state-aware molecular design outperforms static single-structure design** for
EGFR-targeted small molecules.

EGFR has 4 conformational states (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout),
each with a different binding pocket. The state-aware pipeline generates molecules
conditioned on these states using a VAE, then scores them with a unified function that
includes docking, similarity, drug-likeness, and state specificity.

### Current ML Stack (all trained from scratch, no pre-training)

| Model | Architecture | Purpose | Training Data | Key Metrics | Params |
|-------|-------------|---------|---------------|-------------|--------|
| Conditional SELFIES VAE | Bidirectional GRU encoder, GRU decoder, 64D latent space, 4D one-hot state conditioning | Generate novel molecules per conformational state | 8,109 ChEMBL EGFR actives (SMILES converted to SELFIES) | 99.9% valid, 94.8% unique, 300 epochs | 9.5M |
| Affinity MPNN | NNConv message-passing (3 layers, 128 hidden) + global mean/max pool + MLP head | Predict pIC50 binding affinity | 10,466 ChEMBL EGFR compounds (pIC50 4.0-11.0) | RMSE=0.7182, R^2=0.6863, Pearson=0.8323 | 12.7M |
| Multi-task ADMET | GIN backbone (3 layers, 128 hidden) + 6 task-specific MLP heads | Predict 6 ADMET endpoints simultaneously | 27,698 TDC benchmark molecules | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 | 187K |
| GNINA v1.1 | Physics-based: Vina scoring + CNN rescoring | Molecular docking | N/A (physics-based) | Binders -7.32 vs non-binders -4.16 kcal/mol | N/A |

**Molecular featurization:**
- MPNN atom features: 35-dimensional (element, degree, charge, hybridization, aromaticity, etc.)
- MPNN bond features: 11-dimensional (bond type, conjugation, ring membership, stereo)
- VAE input: SELFIES token sequences (vocab size 150, max length 128)
- ADMET: Same atom/bond features as MPNN, GIN architecture

**Infrastructure:**
- Framework: PyTorch + PyTorch Geometric
- Hardware: Yale HPC cluster with NVIDIA H200 GPUs (8 per node), RTX 5000 Ada, B200
- Training time: VAE ~31 min (300 epochs on H200), MPNN and ADMET similar scale

### Key Results

**State-aware vs static comparison:**
- Static wins on mean unified score (0.5437 vs 0.4378, p<0.001)
- State-aware wins on retrospective enrichment: **10x better at identifying future approved drugs** (EF@10 = 4.95/7.72 vs 0.47/0.79)
- State-aware generates 461 candidates (431 novel) vs 30 for static
- Chemical diversity 59% higher for state-aware (0.9056 vs 0.5684)

**Pre-cutoff model performance (retrospective validation):**
- Pre-2010 MPNN (2,974 training compounds): RMSE=0.701, R^2=0.717, Pearson=0.854
- Pre-2015 MPNN (4,852 training compounds): RMSE=0.760, R^2=0.690, Pearson=0.832
- Pre-2010 VAE: 1,000/1,000 valid, 987 unique
- Pre-2015 VAE: 1,000/1,000 valid, 968 unique

Interestingly, the pre-2010 MPNN (2,974 compounds) outperforms the full MPNN
(10,466 compounds) on R^2 and Pearson, suggesting early curated data may be
higher quality.

---

## 2. Current Limitations Relevant to This Research

### 2.1 No Pre-Training or Foundation Models

All three models trained from scratch on moderate datasets (8K-28K molecules).
No self-supervised pre-training on large molecular databases (millions of molecules).
No transfer learning from pre-trained molecular representations. Modern approaches
leverage pre-trained backbones fine-tuned on task-specific data.

### 2.2 No Protein Language Model Integration

Conformational states encoded as 4D one-hot vectors -- the crudest possible
representation. Protein language models (ESM-2, ProtTrans) can produce rich,
continuous conformational embeddings that capture subtle structural variations.
The VAE conditioning would be dramatically more informative.

### 2.3 GRU VAE is Architecturally Dated

The VAE uses GRU encoder/decoder, which was standard circa 2019-2021 but has been
largely superseded by transformer-based generators, diffusion models, and flow-matching
approaches. SELFIES guarantees validity but also constrains the generator.

### 2.4 NNConv MPNN is a First-Generation GNN

NNConv (edge-conditioned convolution) was published in 2017. More expressive GNN
architectures exist: GATv2, PNA, GPS (Graph Transformer), SchNet, DimeNet++, PaiNN,
GemNet. Many pre-trained versions available.

### 2.5 No SOTA Method Comparison

No benchmarking against published generative methods. Without this, reviewers cannot
assess whether StateBind's results represent an advance over existing approaches.

### 2.6 No Protein-Ligand Co-Representation

MPNN scores molecules in isolation (molecular graph only). It does not model
protein-ligand interactions -- no protein structure information enters the affinity
prediction. True binding prediction should consider the binding interface.

---

## 3. Research Questions

Answer each question with **specific, actionable information**: model names, paper
citations (first author + year + journal), GitHub repos, pre-trained checkpoint
availability, architecture details, benchmark results, and your assessment of
integration feasibility.

### Q1: Pre-Trained Molecular Representations

What pre-trained molecular representation models exist that could replace our
scratch-trained GNN backbones? For each:
- Architecture (GNN type, transformer, etc.)
- Pre-training data (size, source)
- Pre-training objective (masked atom, contrastive, denoising, etc.)
- Downstream task performance on drug discovery benchmarks
- Checkpoint availability and license
- Fine-tuning requirements
- Compatibility with our featurization (35D atom, 11D bond features)

Models to investigate: Uni-Mol, GEM, GROVER, MolCLR, GraphMVP, MolBERT, ChemBERTa,
ChemBERTa-2, Graphormer, GPS++, MoLFormer, SELFormer, GIN pre-trained variants.
Also any newer (2024-2025) models not in this list.

### Q2: Protein Language Models for Conformational State Representation

How can protein language models represent kinase conformational states?
- ESM-2: What embedding dimensionality? Does it capture DFG/alphaC variation?
  Any published analysis of kinase conformational information in ESM embeddings?
- ESMFold: Can its internal representations distinguish conformational states?
- ProtTrans: How does it compare to ESM-2 for structural tasks?
- AlphaFold2 representations: Can AF2 predict multiple conformations?
- Structure-aware protein encoders: GVP-GNN, SE(3)-Transformers, Equiformer

Specifically: has anyone used protein language model embeddings to condition molecular
generation on protein conformation? Any published work on kinase-specific embeddings?

### Q3: Protein-Ligand Co-Representation Models

What models jointly represent proteins and ligands for binding prediction?
- DrugBAN, DeepDTA, GraphDTA, MGraphDTA
- TANKBind, EquiBind, DiffDock (pose prediction + scoring)
- Uni-Mol for protein-ligand binding
- Any model that takes both protein structure AND molecular graph as input
- How do they compare to our approach (molecular-only MPNN for affinity)?

### Q4: State-of-the-Art Molecular Generative Models

What are the leading molecular generation architectures as of 2024-2025?
For each, provide architecture details, training data, key metrics, and open-source status.

Categories to cover:
- **SMILES/SELFIES-based:** REINVENT (1, 2, 3, 4), DrugEx (v1, v2, v3), MolGPT,
  FREED, cMolGPT, ChemGPT. How do they compare to our GRU VAE?
- **Graph-based:** GraphAF, MoFlow, GraphDF, GDSS. How do they compare?
- **3D structure-based:** DiffSBDD, Pocket2Mol, TargetDiff, DecompDiff, DrugGPS,
  MolCRAFT, FLAG. (Detailed in techniques doc, but summarize benchmark results here)
- **Diffusion/flow-matching on SMILES or graphs:** CDGS, DiGress, GRAPHARM
- **Transformer-based:** Chemformer, MolBART, MolT5

For each category: What are the reported metrics on standard benchmarks (MOSES,
GuacaMol, PMO)? What are the EGFR-specific results if any?

### Q5: Published Generative Model Comparisons

What papers directly compare multiple generative models head-to-head?
- Benchmark papers (e.g., MOSES paper, GuacaMol paper, PMO paper, TDC leaderboards)
- Review papers comparing architectures
- What metrics are standard? (Validity, uniqueness, novelty, FCD, KL divergence,
  internal diversity, QED distribution, SA distribution, etc.)
- What is considered "state-of-the-art" performance on each benchmark?
- Are there EGFR-specific or kinase-specific generation benchmarks?

This is critical: we need to know exactly what metrics to report and what baselines
to compare against for a top-venue publication.

### Q6: Self-Supervised Pre-Training Strategies for Molecular GNNs

What pre-training objectives work best for molecular property prediction?
- Masked atom/bond prediction
- Contrastive learning (atom-level, graph-level, cross-modal)
- Denoising (coordinate denoising, feature denoising)
- Multi-task pre-training
- 3D geometry prediction from 2D graphs (and vice versa)

For each strategy:
- What molecular database is used for pre-training? (PCQM4Mv2, ZINC, PubChem, ChEMBL-full)
- How much data is needed?
- What downstream improvements are observed?
- Is it compatible with NNConv architecture, or does it require architecture change?

### Q7: Transfer Learning for Low-Data Kinase Targets

How do published approaches handle kinase targets with limited training data?
- Pre-train on pan-kinase data, fine-tune on specific target
- Meta-learning across kinase families
- Few-shot learning for new kinase targets
- Domain adaptation from data-rich to data-poor targets
- What is the minimum training set size for reasonable MPNN affinity prediction?

This is relevant because some expansion targets may have fewer than 10,000 compounds.

### Q8: Multi-Task and Multi-Target Learning

How do published models jointly predict across multiple properties or targets?
- Multi-task property prediction (affinity + ADMET jointly)
- Multi-target affinity prediction (EGFR + ALK + BRAF in one model)
- Hard parameter sharing vs soft parameter sharing vs cross-attention
- Does multi-task/multi-target improve or hurt single-target performance?
- Published kinase-specific multi-target models

### Q9: Integration Patterns: Foundation Model + Task-Specific Head

How do recent papers combine pre-trained molecular encoders with downstream tasks?
- Freeze backbone + train head vs fine-tune all vs adapter layers
- What learning rates and schedules work for fine-tuning molecular foundation models?
- LoRA / adapter patterns for molecular models
- Best practices for combining pre-trained protein encoder + pre-trained molecule
  encoder for binding prediction

### Q10: Computational Requirements and Scaling

For the top recommended models/approaches from Q1-Q9:
- GPU memory requirements (our H200s have 80 GB HBM3e each, 8 per node)
- Training time estimates for our data scale (~10K molecules)
- Inference time per molecule
- Are there lightweight alternatives that achieve 80% of the benefit at 20% of the cost?

---

## 4. Output Format

For each question, provide:
1. **Summary** (2-3 sentences: the landscape and your recommendation)
2. **Top 3-5 specific models/approaches** with: name, citation, key metrics, open-source status, GPU requirements
3. **Recommendation for StateBind** — which model(s) best fit our context (scratch-trained models to replace, 10K training compounds, H200 GPUs, PyTorch + PyG stack)
4. **Integration path** — how to go from current architecture to recommended, what changes are needed
