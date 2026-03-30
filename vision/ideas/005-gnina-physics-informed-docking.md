# 005: GNINA Integration for Physics-Informed Docking

**Category:** Pipeline Gaps, Scientific Rigor
**Priority:** P1: High
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Integrate GNINA (a CNN-scored molecular docking program built on AutoDock Vina) as a new tier in the docking fallback chain. GNINA provides physically interpretable binding poses AND a learned scoring function trained on PDBbind, bridging the gap between the current toy MLP proxy and full physics-based docking. This gives the docking component (20% of scoring weight) real discriminative power with actual protein-ligand structural modeling, at a computational cost of seconds per molecule.

## The Problem

Per `known-limitations.md` (Section 1.1), the docking component is currently served by a lightweight MLP trained on 9 binders and 25 decoys -- a toy model that has never seen a novel molecule. Even the planned MPNN replacement predicts pIC50 from molecular graphs alone with no concept of protein structure. Neither approach produces a binding pose -- they are property predictors, not docking programs.

Per `remaining-goals.md`, 20% of the unified scoring weight is dedicated to "docking" but no actual docking occurs anywhere in the pipeline. Per `current-progress.md`, the cascading fallback chain is: MPNN (untrained) -> proxy MLP (tiny dataset) -> constant 0.5. All three tiers are fundamentally ligand-only predictions. None of them model the protein-ligand interaction.

Peer reviewers will immediately ask: "You have 4 conformational states with different pocket geometries, but you never dock anything into those pockets? How do you know your candidates actually fit?" (per `known-limitations.md` Section 5, points 1 and 5).

## The Vision

After this improvement:

- **Every candidate is docked into its target pocket.** GNINA takes a receptor structure (EGFR pocket) and a ligand (candidate SMILES -> 3D conformer) and produces: a binding pose (3D coordinates of the ligand in the pocket), a Vina score (physics-based), and a CNN score (learned, trained on PDBbind).
- **State-specific docking.** Each conformational state has a different receptor structure. A candidate can be docked into all 4 pockets, producing 4 binding poses and 4 scores. This directly quantifies how well the candidate fits each state's pocket -- making the state-aware advantage concrete and visual.
- **Binding poses enable downstream analysis.** With a predicted binding pose, you can compute interaction fingerprints (H-bonds, hydrophobic contacts, pi-stacking), identify key residue contacts, visualize the binding mode, and compare how the same molecule binds differently in different conformational states.
- **The docking fallback chain becomes real.** New chain: GNINA (physics + CNN) -> MPNN (learned affinity) -> proxy MLP -> stub. GNINA is slow but accurate; MPNN is fast but less reliable.

## Impact Assessment

**Significant.** This activates 20% of scoring weight with a real docking method and unlocks binding pose analysis. It is the single most impactful improvement for making the pipeline physically interpretable and credible to structural biologists. It also provides a direct way to measure state-specific binding: does the same molecule dock better in the inactive pocket than the active pocket?

Affects: docking scoring component (20% weight), evaluation (binding pose analysis), visualization (3D binding modes), the scientific narrative (from "scoring proxies" to "docking predictions").

## Effort Estimate

Medium. GNINA is open-source, well-documented, and available as a conda package. The main work is: (1) preparing receptor files for each conformational state, (2) building the docking automation pipeline, and (3) integrating GNINA scores into the fallback chain. A single agent could complete this in 1-2 weeks. Main risk: GNINA requires pre-prepared receptor PDBQT files and correct protonation states, which requires some structural biology expertise.

## Dependencies

- GNINA installation (conda-forge or compiled binary)
- OpenBabel or Meeko for PDBQT conversion
- PDB structures for each conformational state (from structure module)
- RDKit for 3D conformer generation from SMILES
- Box definition (docking search space) for each pocket

## Implementation Sketch

1. **Receptor preparation: new `scripts/prepare_docking_receptors.py`** -- For each conformational state, take the representative PDB structure, extract the binding site, add hydrogens, compute Gasteiger charges, and convert to PDBQT format. Define a docking box centered on the pocket centroid with appropriate margins. Output: receptor PDBQT + box config per state.

2. **Docking wrapper: new `chemistry/docking.py`** -- Python wrapper around GNINA command-line. Input: SMILES + receptor PDBQT + box config. Pipeline: SMILES -> 3D conformer (RDKit) -> minimize -> dock with GNINA -> parse output (pose, Vina score, CNN score, CNN affinity). Supports batch docking with parallelization.

3. **Fallback integration: modify cascading docking chain** -- Add GNINA as tier 0 (highest priority). If GNINA is installed and receptor files exist, use it. Otherwise fall through to MPNN -> proxy MLP -> stub. The score normalization: `docking_score = sigmoid(-vina_score / 3)` maps Vina kcal/mol to [0, 1] where more negative (better binding) -> higher score.

4. **State-specific docking analysis: new `evaluation/docking_analysis.py`** -- For each candidate, dock into all 4 state pockets. Compare: does the candidate bind better to its intended state? Compute state-selectivity from docking scores: `selectivity = best_state_score - second_best_state_score`.

5. **Visualization: add to `evaluation/figures.py`** -- 3D binding pose visualization per state (optional, using py3Dmol or nglview). Score heatmaps showing candidate x state docking scores.

6. **Config: add `configs/docking.yaml`** -- GNINA binary path, exhaustiveness, number of poses, CNN model selection, box padding, timeout per molecule.

7. **Testing** -- Dock the 3 known EGFR binders (erlotinib, gefitinib, osimertinib) into 1M17 and verify reasonable poses (RMSD < 2.0 angstroms vs co-crystal). Verify the fallback chain correctly degrades when GNINA is unavailable.

## Open Questions

- What is the throughput of GNINA on CPU vs GPU? GNINA supports GPU acceleration for the CNN scoring. On CPU, typical throughput is ~10-30 molecules/hour with exhaustiveness=8. On GPU, it can be 10x faster.
- Can we dock all ~80 candidates (30 static + 49 state-aware) in a reasonable time? At 30 mol/hr on CPU, ~3 hours. With GPU or reduced exhaustiveness, under 1 hour.
- Which GNINA CNN model should we use? `default2018`, `dense`, or `crossdock_default2018`? The CrossDocked model may generalize better.
- How to handle GNINA failures (no pose found, timeout)? Fall through to next tier in the cascade.
- Should we also integrate AutoDock Vina standalone (pure physics scoring, no CNN) as a comparison point? This would separate the physics-based contribution from the learned contribution.
