# 011: Water Thermodynamics and Solvation Analysis

**Category:** Pipeline Gaps, Scientific Rigor
**Priority:** P2: Medium
**Status:** deferred
**Date proposed:** 2026-03-30
**Effort:** Large (2-4 weeks)

## Summary

Add water thermodynamics analysis to the binding pocket characterization. Map crystallographic water positions in each conformational state's pocket, compute their thermodynamic properties (entropy, enthalpy, free energy), and score candidates by their ability to displace high-energy ("unhappy") waters. Displacing trapped, unfavorable water molecules is one of the strongest thermodynamic driving forces for ligand binding, and pocket water landscapes differ dramatically across conformational states -- making this a powerful new axis for state-aware design.

## The Problem

Per `known-limitations.md` (Section 4.4), the pipeline treats binding as a gas-phase interaction -- molecule meets pocket in vacuum. In reality, every binding pocket is filled with water molecules. Some of these waters are thermodynamically unfavorable (trapped in hydrophobic regions, restricted in orientation, unable to form optimal hydrogen bonds). When a ligand binds, it displaces these waters. If the displaced waters were "unhappy" (high free energy), the displacement releases that energy, contributing to binding affinity. If the displaced waters were "happy" (well-coordinated, low free energy), displacing them costs energy and opposes binding.

This physics is completely absent from the current pipeline. No scoring component accounts for solvation. The docking proxy (even with GNINA, per Idea 005) typically uses implicit solvent models that poorly capture specific water effects. WaterMap-style analysis on crystal structures has shown that water thermodynamics can explain >50% of the variance in binding affinity across congeneric series -- more than any other single factor.

## The Vision

After this improvement:

- **Every conformational state has a water map.** Crystallographic waters from PDB structures are analyzed to identify: favorable waters (structural, well-coordinated, hard to displace), unfavorable waters (trapped, high energy, easy to displace), and mixed waters (partially favorable).
- **Candidates are scored by water displacement.** A molecule that overlaps with high-energy water sites gains a favorable solvation score. A molecule that disrupts favorable water networks is penalized.
- **State-specific water patterns become a design tool.** The inactive-state pocket (DFGout/aCout) likely has a very different water network than the active-state pocket. Designing molecules that exploit state-specific water thermodynamics could be the strongest argument for conformational-aware design.
- **New scoring component or enhancement to docking.** Water displacement can be integrated as a new scoring component (solvation score) or as a correction to docking scores.

## Impact Assessment

**Moderate to significant.** Water thermodynamics is a domain-expert feature that would strongly impress structural biologists and medicinal chemists. It demonstrates sophistication beyond typical ML-driven pipelines. For the state-aware hypothesis specifically, differences in water networks across conformational states could provide the most physically meaningful argument for state-specific design. However, the analysis requires careful structural biology work and may be limited by the available crystal structures.

Affects: scoring (new solvation component), structure module (water analysis), evaluation (solvation-driven state preference), scientific credibility.

## Effort Estimate

Large. Requires structural biology expertise for water analysis and careful handling of crystallographic data. Two approaches:
- **Grid-based (WaterMap-lite):** Discretize the pocket into a grid, compute water occupancy from crystal structures, estimate free energy from density. 2-3 weeks.
- **MD-based (full WaterMap):** Run short MD simulations, analyze water thermodynamics using inhomogeneous solvation theory. 3-4 weeks, more compute-intensive but more rigorous.

## Dependencies

- PDB structures with crystallographic waters (available in the existing dataset)
- BioPython for PDB parsing (existing optional dep)
- Molecular dynamics software for MD-based approach (OpenMM, GROMACS)
- Force field parameters (AMBER, CHARMM)
- RDKit for 3D pharmacophore overlaps between candidates and water sites

## Implementation Sketch

1. **Water extraction: new `structure/water_analysis.py`** -- Parse crystallographic waters from PDB files for each conformational state. Compute: water density in the binding pocket, water-protein hydrogen bonds, water-water networks, B-factors (indicator of water mobility).

2. **Thermodynamic scoring: new `structure/water_thermodynamics.py`** -- For each water site, estimate thermodynamic favorability:
   - **Hydrophobic pocket waters:** High energy (unfavorable). Identified by: surrounded by hydrophobic residues, limited hydrogen bond partners, high B-factor.
   - **Bridging waters:** Low energy (favorable). Identified by: multiple hydrogen bonds to both protein and other waters, low B-factor, conserved across multiple structures.
   - Score each site: positive = favorable to displace, negative = costly to displace.

3. **Candidate-water overlap: new function in scoring** -- For each candidate, generate a 3D conformer (RDKit), align to the pocket (from docking pose if available, or pharmacophore alignment), compute overlap between candidate atoms and water sites. `solvation_score = sum(water_energy * overlap_fraction)` normalized to [0, 1].

4. **State comparison: `evaluation/water_comparison.py`** -- Compare water landscapes across conformational states. Identify state-unique water patterns (waters present in one state but not another). This directly motivates state-aware design: "the DFGout pocket has 3 high-energy waters absent from the active state -- molecules designed to displace them would be state-selective."

5. **Testing** -- Verify crystallographic water parsing on known PDB structures. Validate that known EGFR drugs overlap with unfavorable water sites (literature confirmation available for erlotinib). Compare water maps across states and verify they differ meaningfully.

## Open Questions

- How many PDB structures per state have well-resolved crystallographic waters? Structures with resolution > 2.5 angstroms may have unreliable water positions. Need the Assistant AI to check.
- Is the grid-based approach (no MD) sufficient, or does the project need MD simulations for reliable water thermodynamics? Grid-based is faster but less rigorous.
- How to handle the 3D requirement? This analysis requires 3D coordinates for both the pocket (from PDB) and the candidate (from RDKit conformer generation or docking). This introduces a dependency on 3D structure generation that doesn't currently exist in the scoring pipeline.
- Can water thermodynamics explain why the state-aware pipeline performs differently from the static baseline? This would be the most impactful finding -- a physical mechanism for the observed score differences.
