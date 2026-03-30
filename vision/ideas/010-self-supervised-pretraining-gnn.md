# 010: Self-Supervised Pre-Training for GNN Backbone

**Category:** ML Improvements
**Priority:** P1: High
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Large (2-4 weeks)

## Summary

Pre-train the GNN backbone (shared between MPNN and ADMET models) on millions of molecules from ChEMBL or PubChem using self-supervised tasks (masked atom prediction, graph contrastive learning) before fine-tuning on the small EGFR-specific datasets. This addresses the fundamental data scarcity problem: 1,678 EGFR compounds is tiny by modern ML standards. Pre-training captures general chemical knowledge (functional groups, ring systems, reactivity patterns) that transfers to the downstream EGFR task, dramatically improving generalization on novel chemical scaffolds.

## The Problem

Per `known-limitations.md` (Section 3.1), the MPNN and ADMET models will be trained from scratch on small datasets (1,678 compounds for MPNN, TDC benchmarks for ADMET). Per `remaining-goals.md` (Section, peer reviewer critique point 3), "Is 1,678 compounds enough to train a meaningful affinity predictor?" is an expected review question. Modern molecular property prediction routinely uses pre-training on 100K-10M molecules.

Per `current-progress.md`, the MPNN training data is 1,678 ChEMBL compounds with pIC50 values plus ~30 non-EGFR decoys. The ADMET data comes from TDC benchmarks which are also modestly sized per endpoint. Training from scratch on these datasets risks:
- **Overfitting** to the specific chemical scaffolds in the training set
- **Poor generalization** to structurally novel candidates (exactly the ones most interesting for drug design)
- **Calibration issues** where the model is confident but wrong on out-of-distribution inputs

## The Vision

After this improvement:

- **The GNN encoder understands chemistry before it sees EGFR.** Pre-training teaches it about aromatic systems, hydrogen bond donors/acceptors, lipophilicity patterns, and reactivity -- general chemical knowledge that applies to all molecules.
- **Fine-tuning on 1,678 EGFR compounds becomes sufficient.** The model only needs to learn EGFR-specific binding patterns, not general chemistry from scratch. This is analogous to how ImageNet pre-training enables fine-tuning on small medical imaging datasets.
- **Better uncertainty calibration.** Pre-trained models typically have better-calibrated predictions because the feature extractor has seen a diverse training distribution. Combined with Idea 004 (ensemble uncertainty), this gives more reliable confidence intervals.
- **Shared encoder between MPNN and ADMET.** The pre-trained backbone can be shared, with task-specific heads for affinity prediction (MPNN) and ADMET endpoints. This is more parameter-efficient and enables multi-task transfer.

## Impact Assessment

**Significant.** Pre-training is arguably the single most important ML technique for small-data regimes, which is exactly where this project operates. It directly addresses the "is 1,678 enough?" concern and will likely improve all downstream metrics (MPNN RMSE, ADMET AUROC, docking score quality). It is also a well-established technique -- peer reviewers would be surprised by its absence more than its presence.

Affects: MPNN performance, ADMET performance, scoring quality (docking and safety), all downstream evaluation metrics.

## Effort Estimate

Large. The pre-training dataset preparation (millions of molecules from ChEMBL/PubChem) and training (~24-48 hours on GPU) are the main costs. Implementing the self-supervised tasks (masked atom prediction, contrastive learning) requires moderate ML engineering. Fine-tuning on downstream tasks is fast once the pre-trained encoder exists. 2-3 weeks total.

## Dependencies

- ChEMBL or PubChem molecular datasets (millions of SMILES, freely downloadable)
- Significant GPU time (~24-48 hours for pre-training, additional for fine-tuning)
- The existing MPNN and ADMET architectures (to ensure compatibility)
- PyTorch + PyTorch Geometric (existing deps)
- RDKit for molecular graph construction at scale

## Implementation Sketch

1. **Pre-training dataset: `scripts/build_pretraining_dataset.py`** -- Download ChEMBL molecules (all, ~2.3M) or a curated subset (drug-like molecules only, ~500K). Convert SMILES to molecular graphs using the same featurization as the existing MPNN (35 atom features, 11 bond features). This ensures the pre-trained encoder is compatible with downstream fine-tuning.

2. **Self-supervised tasks: new `ml/pretraining.py`** -- Implement two complementary tasks:
   - **Masked atom prediction:** Randomly mask 15% of atom features, predict the original features from context. This forces the model to learn chemical valence rules, aromaticity, and functional group patterns.
   - **Graph contrastive learning:** Apply random augmentations (atom/bond deletion, subgraph sampling) to create two views of each molecule. Train the encoder to produce similar representations for two views of the same molecule (positive pair) and different representations for different molecules (negative pair). NT-Xpair loss.

3. **Pre-training loop: `scripts/pretrain_gnn.py`** -- Multi-task pre-training combining both losses. Hyperparameters: 100-200 epochs, batch_size=256, learning rate warmup + cosine decay, temperature for contrastive loss.

4. **Fine-tuning modification: modify `ml/trainer.py`** -- Add `pretrained_encoder_path` parameter to TrainerConfig. When provided, load encoder weights from pre-training checkpoint and fine-tune end-to-end (or freeze encoder for first N epochs then unfreeze). Both MPNN and ADMET trainers use this option.

5. **Shared encoder option: new `ml/shared_encoder.py`** -- A single pre-trained encoder with swappable prediction heads. The same molecule embedding feeds into affinity prediction (MPNN head) and ADMET prediction (per-task heads). This enables joint fine-tuning and reduces total model parameters.

6. **Testing** -- Compare fine-tuned-from-scratch vs fine-tuned-from-pretrained on the same EGFR test set. Measure: RMSE improvement, generalization to structurally novel test compounds (scaffold split), calibration quality. The pre-trained model should especially outperform on novel scaffolds.

## Open Questions

- Which pre-training strategy works better for this use case: masked atom prediction (BERT-style) or contrastive learning (SimCLR-style)? Literature suggests combining both is best.
- Should we use the full ChEMBL (~2.3M molecules) or filter to drug-like only? The full set captures more chemical diversity; the filtered set is more relevant to drug design.
- Could we leverage existing pre-trained molecular models (GEM, MolCLR, GraphMVP) instead of pre-training from scratch? This would save weeks of GPU time but requires architectural compatibility with the existing MPNN.
- What is the expected performance gain? Literature reports 5-20% improvement in downstream tasks, but this varies by dataset size and task.
