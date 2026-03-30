# 001: Continuous Conformational Conditioning via Protein Language Models

**Category:** Novel Approaches, Scientific Rigor
**Priority:** P0: Critical
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Large (2-4 weeks)

## Summary

Replace the discrete 4-state conformational model (DFGin/out x aCin/out) with continuous conformational embeddings derived from a protein language model (ESM-2 or ESMFold). Instead of classifying EGFR structures into 4 bins, embed the full kinase domain into a latent space where conformational states exist on a continuous manifold. Condition the generative model on these continuous embeddings rather than one-hot state vectors. This is the single most impactful change for the project's scientific thesis because the central hypothesis -- state-aware design outperforms static design -- is currently crippled by a discretization that collapses a rich conformational landscape into 4 categories.

## The Problem

Per `known-limitations.md` (Section 2.2), the 4-state model is a gross oversimplification. Real kinase dynamics are continuous -- the protein breathes through a landscape of intermediate conformations. The 4 discrete bins miss intermediate geometries, transition states, and the subtle pocket reshaping that occurs between canonical states. Per `known-limitations.md` (Section 2.3), all 17 curated resistance mutations map to the same state (DFGin/aCin), making the mutation-to-state prediction completely uninformative. The context module is functionally dead weight.

This is not a minor limitation. Per `remaining-goals.md`, the state specificity component is only 15% of the scoring weight. If the states themselves are an inadequate representation of reality, even a perfectly trained pipeline is testing a weakened version of the hypothesis. Peer reviewers will demolish this (per `known-limitations.md` Section 5, point 4).

## The Vision

After this improvement:

- **Conformational embeddings** from ESM-2 (or ESMFold's structure module) replace the 4 one-hot vectors. Each PDB structure maps to a dense vector (e.g., 1280-dimensional from ESM-2 large) that captures subtle structural variations within and between canonical states.
- **The VAE conditions on continuous embeddings** instead of one-hot state vectors. The same latent point z decoded with different conformational embeddings produces molecules optimized for different points on the conformational landscape -- including intermediate states that the discrete model cannot represent.
- **The context module becomes meaningful** because mutations shift the protein's position in embedding space rather than flipping between 4 bins. T790M might shift the embedding toward a region between DFGin/aCin and DFGin/aCout, rather than mapping to exactly one state.
- **State specificity becomes a continuous metric** -- measured as the gradient of the generator's output with respect to the conformational embedding, or as the variation in docking score across a sampled ensemble of conformations.

## Impact Assessment

**Transformative.** This redefines the project's central hypothesis from "discrete state-awareness helps" to "conformational landscape-awareness helps" -- a much stronger and more defensible claim. It directly addresses the 2 most damaging peer review criticisms (discretization and uninformative mutation mapping). It also differentiates StateBind from every other state-aware design pipeline in the literature, which all use discrete states.

Affects: state specificity scoring (15% weight), VAE conditioning, context module, the scientific narrative of every evaluation artifact.

## Effort Estimate

Large. Requires ML expertise (embedding extraction, architecture modification) and structural biology knowledge (interpreting conformational embeddings). A single agent could handle the implementation in 2-3 weeks if the embedding extraction pipeline (PDB -> ESM-2 -> embedding) is straightforward. Main risk: the ESM-2 embeddings may not capture DFG/alphaC variations well for kinase domains specifically -- they are trained on general protein sequences.

## Dependencies

- ESM-2 model weights (publicly available from Meta, ~5GB for esm2_t33_650M)
- The existing structure module (provides PDB structures for embedding extraction)
- Trained VAE (to have a baseline before modifying the conditioning)
- PyTorch (already an optional dependency)

## Implementation Sketch

1. **New module: `structure/embeddings.py`** -- Extract ESM-2 embeddings for each EGFR PDB structure. Input: PDB file or FASTA sequence + structure. Output: conformational embedding vector per structure.

2. **Modify `structure/atlas.py`** -- Add a `conformational_embedding` field to each state atlas entry alongside the existing discrete state label. The discrete states remain for backward compatibility and as human-readable labels.

3. **Modify `ml/vae.py`** -- Replace the `state_dim=4` one-hot conditioning with `state_dim=embedding_dim` continuous conditioning. The encoder and decoder concatenation logic stays the same; only the dimensionality changes. Add a linear projection layer if the raw embedding is too high-dimensional (1280 -> 64 or 128).

4. **Modify `context/features.py`** -- Predict conformational embedding from mutation features instead of discrete state class. This turns the context model from a classifier into a regressor, which may actually resolve the "all mutations map to one state" problem.

5. **Modify `ranking/scoring.py`** -- Redefine state specificity as a continuous metric. One approach: for each candidate, sample N conformational embeddings uniformly, generate docking/affinity predictions at each, and measure variance. Low variance = broadly active (low specificity). High variance = state-selective (high specificity).

6. **New config: `configs/embeddings.yaml`** -- ESM model name, embedding dimension, projection dimension, cache directory.

7. **Testing:** Verify embeddings cluster by known state labels (sanity check). Verify modified VAE trains and generates valid SMILES. Verify new state specificity metric correlates with the old discrete metric on existing data.

## Open Questions

- Does ESM-2 capture DFG/alphaC variation well? The model was trained on sequences, not explicitly on kinase conformation. The structure module of ESMFold might be better -- need the Assistant AI to investigate what conformational information is captured in these embeddings for kinase domains specifically.
- What dimensionality should the projected embedding be? Too high (1280) may make the VAE harder to train. Too low (4-8) may lose conformational information.
- Should we use sequence-based embeddings (ESM-2) or structure-based embeddings (ESMFold, GVP-GNN, or SE(3)-Transformers)? Structure-based would capture 3D geometry directly but requires more compute.
