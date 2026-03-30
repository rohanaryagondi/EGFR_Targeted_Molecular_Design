# 002: 3D Pocket-Conditioned Diffusion Model for Molecular Generation

**Category:** ML Improvements, Novel Approaches
**Priority:** P1: High
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Epic (1+ months)

## Summary

Replace or complement the SMILES VAE with a 3D structure-based diffusion model that generates molecules directly inside the EGFR binding pocket. Instead of producing SMILES strings (1D text) and hoping they fit the pocket, generate atom coordinates in 3D space conditioned on the pocket geometry of each conformational state. This produces candidates with built-in shape complementarity -- the molecular generation and docking steps collapse into one.

## The Problem

Per `known-limitations.md` (Section 3.4), the VAE generates SMILES strings with no concept of how the molecule fits in the EGFR pocket. Two molecules with similar SMILES can have very different 3D binding poses. The generator is blind to the physical reality of protein-ligand binding. Per `architecture.md`, the VAE's state conditioning is a one-hot vector concatenated to the latent code -- it tells the generator "make a molecule for this state" but never shows it the pocket shape.

This means the pipeline relies entirely on post-hoc scoring (docking proxy, reference similarity) to determine whether generated molecules actually complement the pocket. The generation step is unguided in 3D -- it is throwing darts at a chemical space and then checking which ones happen to land near the target. Per `remaining-goals.md`, the current 49 candidates are all string modifications, not de novo designs. Even once the VAE is trained, it will generate SMILES from learned chemical patterns, not from structural reasoning.

## The Vision

After this improvement:

- **Molecules are born in the pocket.** Each generated molecule is a set of 3D atom coordinates placed inside a specific conformational state's binding pocket. Shape complementarity is guaranteed by construction.
- **Binding pose comes free.** No separate docking step needed -- the generated coordinates ARE the predicted binding pose. Interaction fingerprints (H-bonds, hydrophobic contacts, pi-stacking) can be computed directly from the generated output.
- **State conditioning is structural.** Instead of a one-hot or embedding vector, the conditioning signal is the actual 3D geometry of the pocket (represented as a point cloud, voxel grid, or atomic graph). Different conformational states produce visibly different pocket geometries and therefore different candidate molecules.
- **The comparison becomes dramatically more meaningful.** State-aware generation with pocket conditioning is a fundamentally different approach from static single-structure design -- the contrast is sharper and the scientific claim is stronger.

## Impact Assessment

**Transformative.** This moves StateBind from a first-generation pipeline (SMILES-based, 1D, post-hoc scoring) to a third-generation pipeline (structure-based, 3D, pocket-conditioned). It would place the project at the frontier of molecular generation research and provide a compelling answer to the peer review criticism "no comparison to state-of-the-art generative models" (per `known-limitations.md` Section 5, point 6).

Affects: generation module (complete replacement), scoring pipeline (docking score becomes intrinsic), evaluation (3D binding mode analysis), the scientific narrative.

## Effort Estimate

Epic. This is a significant ML engineering effort requiring expertise in 3D deep learning, equivariant neural networks, and protein structure representation. Estimated 4-6 weeks for a skilled agent. The main challenge is not the model architecture (several published implementations exist) but the data pipeline: converting EGFR pocket geometries into the format expected by diffusion models, and validating that generated molecules are chemically valid.

## Dependencies

- Pocket geometries for all 4 conformational states (from structure module)
- PDB structure files (existing in data/raw/)
- PyTorch + PyTorch Geometric (existing optional deps)
- Potentially: e3nn (equivariant neural network library) or additional 3D ML libraries
- Significant GPU time for training (longer than the current models)
- Reference implementation of DiffSBDD, Pocket2Mol, or TargetDiff (open-source)

## Implementation Sketch

1. **Evaluate published approaches.** DiffSBDD (denoising diffusion for structure-based drug design), Pocket2Mol (autoregressive 3D generation), and TargetDiff (SE(3)-equivariant diffusion) all have open-source implementations. Select the most suitable based on: pocket conditioning mechanism, generation quality, and ease of integration.

2. **New module: `ml/diffusion3d.py`** -- Implement or adapt the chosen diffusion model architecture. Key components: pocket encoder (GVP or EGNN on pocket atoms), molecule decoder (equivariant diffusion on atom coordinates + types), and sampling procedure.

3. **New module: `ml/pocket_prep.py`** -- Convert pocket geometries from the structure module into the format expected by the diffusion model (atomic coordinates, residue types, surface normals, etc.).

4. **Modify `generation/generator.py`** -- Add a `DiffusionGenerator` strategy alongside existing string modification and VAE strategies. Output: candidate molecules with 3D coordinates and predicted binding pose.

5. **New scoring integration** -- Since generated molecules come with binding poses, compute interaction fingerprints directly: H-bond count, hydrophobic contact area, shape complementarity score. This could become a new scoring component or enhance the docking proxy.

6. **Training data** -- Use PDBbind or CrossDocked2020 datasets for training the diffusion model. Fine-tune on EGFR-specific complexes.

7. **Testing** -- Validate chemical correctness (bond lengths, angles, charges), measure validity rate, diversity, and compare 3D-generated candidates to SMILES-generated candidates under the same scoring function.

## Open Questions

- Which diffusion model variant is most appropriate for this project's scale? DiffSBDD is simpler but less flexible; TargetDiff is more principled but harder to train.
- How much training data is needed? PDBbind has ~19,000 protein-ligand complexes. Is EGFR-specific fine-tuning necessary or would a general model suffice?
- Can the generated 3D molecules be reliably converted to canonical SMILES for compatibility with the existing scoring pipeline?
- What is the GPU budget? 3D diffusion models typically require more training time than sequence models.
- Should this replace the VAE or run alongside it? A comparison of SMILES-VAE vs 3D-diffusion generated candidates would itself be a publishable result.
