---
agent: Senior Structural Biologist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: compchem-P01
---

# Critique: Physics-Based Validation via Water Thermodynamics and Free Energy Perturbation

## Reviewing Agent

Dr. Senior Structural Biologist -- 20+ years in protein structure determination, kinase
conformational biology, and structure-based drug design. I assess this physics-based
validation proposal through the lens of structural data quality: are the input structures
appropriate for MD and GIST, are the crystal artifacts understood, and does the ensemble
docking component use the right KLIFS structures?

## Proposal Summary

compchem-P01 proposes a 3-tier physics-based validation of StateBind's conformational
state-aware hypothesis: Tier 1 (GIST water thermodynamic maps for all 4 EGFR states,
~2 GPU-days), Tier 2 (OpenFE RBFE for top 20 candidates, 120-180 GPU-hours), and
Tier 3 (SQM2.20 rescoring, ~3 CPU-days). An ensemble docking enhancement using 5 KLIFS
structures per state runs in parallel with Tier 1.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** This proposal provides exactly the physical mechanistic evidence the
publication needs -- GIST water maps would transform the paper from a pipeline report to
a physical chemistry contribution -- but the structural inputs require careful attention
to mutations, crystal artifacts, and ensemble selection before any MD is run.

---

## Strengths

1. **GIST water thermodynamics is the single highest-impact experiment per compute dollar
   in any proposal this round.** At less than 2 GPU-days, Tier 1 produces direct
   thermodynamic evidence that the 4 conformational states present physically distinct
   binding environments. The published literature (Robinson et al., 2010 on SRC; Cyphers
   et al., 2017 on Aurora; Kim et al., 2018 on PKA) consistently shows that kinase
   conformational states differ in their water networks. Demonstrating this for EGFR's
   4 states would be a novel result -- no prior study has applied GIST to compare water
   thermodynamics across multiple conformational states of the same kinase for the purpose
   of validating state-aware molecular design.

2. **The tiered architecture is well-conceived.** Tier 1 is cheap and fast (1 week),
   provides stand-alone publication value, and informs Tier 2 (which states matter most
   for FEP). Tier 2 is more expensive but provides the gold-standard computational
   validation. Tier 3 is optional and orthogonal. This allows the project to stop at any
   tier and still have publishable results. The ensemble docking enhancement running in
   parallel is efficient scheduling.

3. **The expected results section demonstrates deep physical intuition.** The prediction
   that DFGout/aCout (largest pocket, ~850 A^3) will have the most displaceable high-
   energy waters, while DFGin/aCin (smallest pocket, ~450 A^3) will have the fewest, is
   physically well-motivated. This prediction, if confirmed by GIST, provides the
   thermodynamic basis for why state-aware design matters -- different states have
   different water displacement driving forces.

4. **The evaluation criteria are concrete and testable.** Per-voxel Wilcoxon tests on
   deltaG distributions, Jaccard similarity of high-energy water positions, DFGout > DFGin
   displaceable water count -- these are well-specified success criteria that leave no
   room for post-hoc interpretation.

5. **Honest handling of negative outcomes.** The proposal explicitly states that if FEP
   disagrees with GNINA rankings, this is still valuable and publishable. Similarly, if
   GIST does not differentiate states, this is a mechanistic finding (state-aware advantage
   comes from geometry, not water thermodynamics). This scientific honesty strengthens the
   proposal.

6. **The software stack is entirely open-source and available on Bouchet.** AmberTools
   (cpptraj for GIST), OpenMM (MD engine), OpenFE (RBFE), OpenFF Sage (ligand force
   field) -- all freely installable via conda-forge. No proprietary software dependencies.

## Weaknesses

1. **The 3W2R mutation problem is acknowledged but insufficiently addressed -- this is the
   most critical structural issue.**
   - **Severity:** Critical
   - **Addressable?** Yes -- with specific structural analysis.

   3W2R is a T790M/L858R double mutant structure used as StateBind's representative for
   the DFGout/aCin state. The proposal notes this (Step 1.1) and suggests checking KLIFS
   for a wild-type alternative. I can provide a definitive assessment:

   **There is no wild-type EGFR crystal structure in the DFGout/aCin conformation in
   the PDB.** This is because the DFGout conformation is thermodynamically disfavored
   for wild-type EGFR. The T790M mutation (gatekeeper) creates steric bulk that
   destabilizes the active DFGin conformation, shifting the equilibrium toward DFGout.
   The L858R mutation (activation loop) further alters the conformational landscape.
   Structures like 3W2R capture the DFGout state because the mutations stabilize it.

   For GIST analysis specifically, the T790M mutation matters because:
   - T790M introduces a methionine at the gatekeeper position, which is at the back of
     the ATP-binding pocket. This directly alters the water network in the hinge region.
   - The M790 side chain occupies space that is available for water in the WT structure,
     potentially displacing 1-2 water molecules and altering local solvation
     thermodynamics.
   - L858R in the activation loop changes the electrostatic environment near the DFG
     motif, potentially altering water stability in the allosteric extension pocket.

   **The GIST comparison between 1M17 (WT, DFGin/aCin) and 3W2R (T790M/L858R,
   DFGout/aCin) conflates conformational and mutational effects on water
   thermodynamics.** Differences in water maps may reflect the mutations rather than the
   conformational state change. This is a confound that weakens the central claim.

   **Mitigation options (in order of preference):**

   a. **Run GIST on both 3W2R and a computationally back-mutated structure (3W2R with
      M790T and R858L modeled in silico).** Compare the water maps of the back-mutated
      WT-DFGout to the actual 3W2R. If the water networks are similar (Jaccard similarity
      > 0.8 for high-energy water positions), the mutations have minimal impact on
      solvation and 3W2R is acceptable. If they differ substantially, the mutation effect
      must be reported.

   b. **Use an alternative DFGout EGFR structure.** While no WT DFGout crystal structure
      exists, there may be structures with only one of the two mutations (T790M alone,
      without L858R). PDB search: 4HJO is T790M/L858R with WZ4002, same mutation pair.
      2JIT is T790M only with an irreversible inhibitor. Using a single-mutant structure
      reduces the confound.

   c. **Use a homology-based DFGout model.** Build a WT EGFR DFGout model using a closely
      related kinase's DFGout structure as template (e.g., ABL1 2HYY DFGout + EGFR
      sequence). This introduces modeling uncertainty but eliminates the mutation confound.

   d. **Accept 3W2R with explicit caveats.** Document that the DFGout/aCin GIST results
      carry a mutation confound and that quantitative differences from DFGin states
      should be interpreted conservatively.

   I recommend option (a) as it provides direct evidence for or against the mutation
   confound without requiring a new crystal structure.

2. **10-20 ns may be insufficient for GIST convergence in the larger pockets.**
   - **Severity:** Major
   - **Addressable?** Yes -- with convergence checking and possible extension.

   The proposal specifies 10-20 ns restrained production MD per state. For the DFGin/aCin
   state (smallest pocket, ~450 A^3), this is likely sufficient. But the DFGout/aCout
   state (4ZAU, largest pocket, ~850 A^3) has nearly twice the solvent-accessible volume.
   Larger pockets require longer sampling because:

   - More water molecules need to be sampled for statistical convergence
   - The allosteric extension pocket in DFGout states is hydrophobic with slow water
     exchange kinetics
   - Trapped water molecules in hydrophobic pockets may have residence times of tens of
     nanoseconds, requiring longer trajectories to sample multiple exchange events

   The proposal mentions convergence checking (first half vs second half comparison) in
   the Open Questions section, which is good. But it should be upgraded to a mandatory
   protocol step, not an open question. The standard GIST convergence test:

   - Compute GIST on frames 1-N/2 and frames N/2+1-N separately
   - Compare per-voxel deltaG_sw values between halves
   - Require R^2 > 0.9 between half-trajectory GIST maps for the pocket region
   - If R^2 < 0.9, double the trajectory length and recheck

   Published benchmarks on kinase-sized systems suggest 10 ns is often sufficient for
   hinge-proximal water sites but may be marginal for deep hydrophobic pockets
   (Ramsey et al., 2016). I recommend starting at 20 ns (not 10) for all states, with
   convergence checking. If 20 ns is insufficient for the DFGout states, extend to 40 ns
   -- still well under 1 GPU-day on an H200 at 250 ns/day throughput.

3. **Single crystal structures vs ensemble structures for GIST: a missed opportunity.**
   - **Severity:** Major
   - **Addressable?** Yes -- run GIST on ensemble-derived structures.

   The proposal runs GIST on 4 single crystal structures (1M17, 2GS7, 3W2R, 4ZAU). But
   the ensemble docking enhancement (Step E.1) selects 5 structures per state from KLIFS.
   These same ensemble structures could be used for GIST, providing an ensemble-averaged
   water thermodynamic map per state rather than a single-structure snapshot.

   Why this matters:
   - Crystal packing forces distort protein conformations. The aC helix position in a
     crystal structure may not accurately represent the solution-state orientation. For
     the DFGin/aCout state (2GS7), crystal contacts near the aC helix could artifactually
     stabilize a particular helix orientation, altering the water network in that region.
   - Different co-crystallized ligands induce slightly different pocket shapes (induced
     fit). GIST on a single structure captures one induced-fit snapshot. Averaging GIST
     maps across 5 structures per state captures the within-state pocket variability.
   - The DFGin/aCin state has 200+ EGFR structures in the PDB. Using one (1M17, with
     erlotinib) ignores the structural diversity within this state. Erlotinib's binding
     mode shapes the pocket in a specific way; a structure with gefitinib or lapatinib
     would present a slightly different pocket.

   **Recommendation:** Run GIST on the apo (ligand-stripped) versions of 3-5 structures
   per state. Average the GIST maps (or report the range of per-voxel deltaG values
   across the ensemble). This transforms the GIST analysis from "4 snapshots differ" to
   "4 conformational state basins differ even when sampled from multiple structures" --
   a much stronger claim.

   **Compute cost:** 3-5x more MD trajectories, but each is only 20 ns. Total: 12-20
   additional trajectories x 20 ns = 240-400 ns. At 250 ns/day on H200, this is 1-2
   GPU-days. The total Tier 1 cost increases from ~2 to ~4 GPU-days -- still very cheap.

4. **The 4ZAU structural assignment needs verification.**
   - **Severity:** Major
   - **Addressable?** Yes -- check KLIFS and KinCore.

   The proposal uses 4ZAU as the DFGout/aCout representative. In my R01 research, I
   flagged that 4ZAU's conformational assignment should be verified. Key questions:

   - Does KinCore classify 4ZAU as DFGout/aCout? KinCore uses strict dihedral angle
     criteria that may assign 4ZAU differently.
   - 4ZAU contains EAI045, an allosteric inhibitor that binds the dimer interface
     adjacent to the aC helix. EAI045 binding may stabilize an atypical conformation
     that does not cleanly map to the standard DFGout/aCout bin.
   - The CLAUDE.md project documentation mentions 4ZAU as "WT + EAI045 allosteric
     (DFGout/aCout, 2.55 A)" but also notes in the compchem-P01 risk section that
     "4ZAU may not be correctly classified as DFGout/aCout."

   If 4ZAU is misclassified, the entire DFGout/aCout state analysis is compromised.
   GIST water maps computed for a misassigned structure would be attributed to the wrong
   conformational state.

   **Recommendation:** Before running any GIST, verify 4ZAU against both KinCore and
   KLIFS. If the assignment is ambiguous, either (a) use the KLIFS/KinCore consensus
   assignment, or (b) exclude 4ZAU and run GIST on only 3 states (DFGin/aCin,
   DFGin/aCout, DFGout/aCin). A 3-state GIST analysis that is structurally sound is
   better than a 4-state analysis with a questionable 4th state.

5. **Crystal artifact concerns for 2GS7 (DFGin/aCout, Src-like inactive).**
   - **Severity:** Minor
   - **Addressable?** Yes -- document and mitigate.

   2GS7 is an apo (unliganded) structure of EGFR in the Src-like inactive conformation
   at 2.60 A resolution. Key structural biology concerns:

   - **Apo structures are more susceptible to crystal packing artifacts** than
     ligand-bound structures. Without a ligand occupying the binding site, the pocket
     may collapse or distort under crystal packing forces.
   - **2.60 A resolution is moderate.** B-factors in the activation loop region are likely
     elevated, meaning the DFG motif position and aC helix orientation have higher
     coordinate uncertainty than in a 1.5-2.0 A structure.
   - **The Src-like inactive state may be partially stabilized by crystal contacts.**
     Park et al. (2012) showed that erlotinib can bind both active and inactive EGFR
     conformations, suggesting the Src-like inactive state is not as distinct from the
     active state as crystallography implies.

   For GIST, these concerns translate to: water positions near the aC helix and
   activation loop regions of 2GS7 may reflect crystal artifacts rather than
   solution-state solvation. The restraints applied during GIST production MD (backbone
   restrained at 1 kcal/mol/A^2) will preserve the crystal conformation, including any
   artifacts.

   **Mitigation:** Compare GIST water density near the aC helix in 2GS7 with other
   DFGin/aCout structures (if available from KLIFS). If the water patterns are consistent
   across multiple aCout structures, crystal artifacts are unlikely. If they vary
   substantially, the single-structure GIST may not be representative.

6. **Ensemble docking structure selection from KLIFS needs quality criteria.**
   - **Severity:** Minor
   - **Addressable?** Yes -- specify selection criteria.

   The proposal states "Select 5 representative structures per state using KLIFS pocket
   RMSD clustering" and mentions prioritizing resolution < 2.5 A, wild-type or clinically
   relevant mutations, and diverse co-crystallized ligands. This is reasonable but
   incomplete. Additional criteria should include:

   - **R-free value < 0.30** (quality indicator; structures with R-free > 0.30 may have
     modeling errors)
   - **No unresolved regions in the binding pocket** (check for missing residues in the
     KLIFS 85-residue pocket definition)
   - **No steric clashes** in the pocket region (common in lower-resolution structures)
   - **Temperature:** Room-temperature structures (rare but available for some kinases)
     capture more conformational heterogeneity than cryo structures. If any EGFR
     room-temperature structures exist, they should be prioritized.
   - **Ligand diversity within state:** For DFGin/aCin, select structures with chemically
     diverse co-crystallized ligands (e.g., quinazoline, pyrimidine, covalent) to sample
     induced-fit diversity.

   The KLIFS database provides quality metrics and pocket completeness scores that can
   guide selection. Use the KLIFS quality filter before clustering by pocket RMSD.

   For EGFR DFGin/aCin, there are 200+ structures. Five representatives should span:
   - One apo or minimal-ligand structure (to represent unliganded pocket)
   - One with a type I inhibitor (erlotinib-like)
   - One with a type I.5 inhibitor (lapatinib-like, if DFGin/aCin assignment)
   - One with a covalent inhibitor (osimertinib-like)
   - One high-resolution structure (< 2.0 A)

7. **The FEP perturbation network may fragment for VAE-generated candidates.**
   - **Severity:** Minor
   - **Addressable?** Yes -- acknowledged in proposal; use ATM or ABFE as fallback.

   This is acknowledged in the proposal (Step 2.1 note on diverse chemotypes). StateBind's
   VAE generates SELFIES-encoded molecules that may span multiple Murcko scaffolds with
   limited pair-wise similarity. OpenFE's Kartograf atom mapper requires reasonable
   structural similarity between perturbation partners. If the top 20 candidates have
   5+ distinct scaffolds, the perturbation network fragments into disconnected components,
   and cross-component comparisons require ABFE (20-40 GPU-hours per compound).

   The proposal suggests ATM (Alchemical Transfer Method) as a fallback for diverse
   chemotypes. This is the right approach. ATM (Azimi et al., 2022) handles scaffold
   hopping without atom mapping. However, ATM is not yet integrated into OpenFE's
   standard protocol -- it would require custom implementation or use of the standalone
   ATM package from Gallicchio's group.

   **Recommendation:** Before committing to Tier 2, cluster the top 20 candidates by
   Murcko scaffold. If more than 3 disconnected scaffold clusters exist, plan for ABFE
   or ATM from the outset rather than discovering mid-execution that RBFE cannot connect
   the network.

---

## Feasibility Assessment

### Technical Feasibility

**Tier 1 (GIST): HIGH.** GIST is a mature method with established tutorials (AMBER-hub),
production-quality software (cpptraj in AmberTools), and straightforward setup. The
main technical challenge is system preparation (protonation states, force field
assignment), which is routine for an experienced computational chemist. The H200 GPUs
on Bouchet provide more than sufficient throughput.

**Tier 2 (OpenFE RBFE): MODERATE.** FEP is technically demanding. Parameterization of
diverse drug-like molecules with OpenFF Sage requires checking for coverage gaps (unusual
functional groups, charged species, tautomers). The perturbation network construction
for diverse chemotypes is the main technical risk. However, OpenFE v1.7+ has automated
much of the workflow, and the kinase RBFE benchmarks (KLK6, ABL, TYK2) demonstrate
that kinase systems are well-suited to FEP.

**Tier 3 (SQM2.20): HIGH.** Straightforward binary execution on CPU. Low technical risk.

**Ensemble docking: HIGH.** Re-runs existing GNINA infrastructure with additional
receptor structures. Straightforward.

### Scientific Feasibility

The scientific logic is sound: GIST provides mechanistic evidence (why states differ),
FEP provides thermodynamic validation (are candidates truly better binders), and
ensemble docking addresses the single-structure limitation. Each tier produces
independently publishable results.

The main scientific risk is the 3W2R mutation confound for Tier 1. If not addressed,
the DFGout GIST results are confounded. With the back-mutation control (my recommended
mitigation a), this risk is manageable.

### Timeline Feasibility

**Tier 1: 1 week is realistic** if structures are pre-validated (which they must be).
With the ensemble GIST addition I recommend (3-5 structures per state), extend to 1.5-2
weeks.

**Tier 2: 2 weeks is tight but achievable** for an experienced FEP practitioner. The
bottleneck is system preparation and parameterization, not production runs. If the
candidates have challenging chemistry (unusual heterocycles, charged states), preparation
may take longer.

**Total: 3-4 weeks for Tiers 1+2** is realistic. Adding ensemble GIST pushes to 4-5
weeks. Still well within a reasonable timeline.

---

## Suggested Modifications

1. **Make GIST convergence checking a mandatory protocol step, not an open question.**
   Start all states at 20 ns production MD. Compute GIST on first 10 ns and last 10 ns
   independently. Require R^2 > 0.9 between half-trajectory maps for the binding pocket
   grid voxels. If convergence fails, extend to 40 ns. Document convergence metrics in
   the supplementary material.

2. **Address the 3W2R mutation confound with a back-mutation GIST control.** Run GIST on
   both 3W2R (T790M/L858R) and a computationally back-mutated WT version. Compare water
   maps. Report the Jaccard similarity of high-energy water positions between the mutant
   and back-mutated structures. If similarity > 0.8, the mutations have minimal impact
   and 3W2R is acceptable. If similarity < 0.8, report both sets of water maps and note
   the confound.

3. **Verify 4ZAU conformational assignment against KinCore and KLIFS before running any
   GIST.** If the assignment is ambiguous or incorrect, either substitute with the correct
   representative or reduce to a 3-state GIST analysis. A clean 3-state result is better
   than a questionable 4-state result.

4. **Extend Tier 1 to ensemble GIST.** Run GIST on 3-5 structures per state (using the
   same structures selected for ensemble docking). Average the GIST maps or report the
   within-state variance. This transforms the analysis from "4 snapshots" to "4
   conformational basins" -- a much stronger claim for publication. Additional cost: ~2
   GPU-days (total Tier 1 becomes ~4 GPU-days).

5. **Specify KLIFS quality criteria for ensemble docking structures.** Add R-free < 0.30,
   no missing pocket residues in KLIFS 85-position definition, and explicit documentation
   of mutation status for every selected structure. Create a supplementary table with:
   PDB ID, resolution, R-free, WT/mutant, KinCore state, KLIFS state, co-crystallized
   ligand, selection rationale.

6. **Cluster top 20 FEP candidates by Murcko scaffold before committing to RBFE.** If
   more than 3 disconnected scaffold clusters exist, plan for ABFE or ATM from the
   outset. Budget the additional compute (500-1200 GPU-hours for ABFE) as contingency.

7. **Consider running GIST on all 4 states with AND without the co-crystallized ligand
   removed.** Comparing the "apo-like" (ligand-stripped) GIST to the "holo" GIST reveals
   which water sites are displaced by ligand binding in each state. This provides an
   additional layer of analysis: which states have the most "displaceable" waters in the
   ligand-binding region? This directly connects to the state-aware design hypothesis.

---

## Alternative Approaches

**WaterMap (Schrodinger) vs GIST (AmberTools):** WaterMap provides similar water
thermodynamic information but is commercial software not available on Bouchet without a
license. GIST via cpptraj is the right choice for this project -- free, well-validated,
and produces equivalent physical quantities (per-voxel enthalpy, entropy, free energy).
SSTMap (Haider et al., 2018) is an open-source alternative to cpptraj GIST that may
provide cleaner Python-based analysis integration.

**Metadynamics / enhanced sampling instead of restrained MD for GIST:** The proposal uses
restrained MD (backbone restraints at 1 kcal/mol/A^2) because GIST requires the solute
in essentially one conformation. An alternative is enhanced sampling (metadynamics,
replica exchange) to compute the free energy landscape of water occupation, but this is
substantially more complex and expensive. For the purpose of comparing static snapshots
of each conformational state, restrained MD is the correct and standard approach.

**3D-RISM instead of GIST:** 3D-RISM (3D Reference Interaction Site Model) computes
solvation thermodynamics without explicit MD, making it faster. However, 3D-RISM
accuracy for kinase binding sites is less validated than GIST, and it may miss
water-water correlations that GIST captures. I recommend GIST as the primary method
with 3D-RISM as an optional cross-check if convergence issues arise.

---

## Impact on Publication Narrative

This proposal transforms the publication narrative in a critical way. Without it,
StateBind's paper says: "We docked molecules into 4 structures and state-aware docking
produced better enrichment." With it, the paper says: "We demonstrate that EGFR's 4
conformational states present physically distinct water thermodynamic environments, with
DFGout states harboring more displaceable high-energy waters. State-aware molecular design
exploits these differences, and the top candidates are validated by physics-based free
energy calculations."

The GIST water maps would be the centerpiece figure of the paper -- a 4-panel layout
showing how water energetics differ across conformational states. This is the kind of
figure that makes reviewers say "now I understand why this works." It converts the
abstract concept of "conformational state-awareness" into concrete physical chemistry.

The integration with datasci-P01 is critical: the GIST results explain WHY state-aware
design works (or does not work), while the multi-kinase statistics demonstrate HOW WELL
it works. Together, they make a complete publication: mechanism (GIST) + validation
(multi-kinase BEDROC) + rigor (ablation + FEP).

For multi-kinase extension: if datasci-P01 expands to ABL1, BRAF, and MET (as I
recommend), running GIST on those kinases too would strengthen the generalizability
claim. The cost would be ~4 GPU-days per kinase (with ensemble GIST), or ~16 GPU-days
for all 4 kinases -- still very affordable on Bouchet.

---

## References

1. Robinson DD, Giovambattista N, Friesner RA, et al. Understanding kinase selectivity
   through energetic analysis of binding site waters. ChemMedChem. 2010;5(4):618-627.

2. Cyphers S, et al. A water-mediated allosteric network governs activation of Aurora
   kinase A. Nat Chem Biol. 2017;13:402-408.

3. Kim J, Ahuja LG, Chao FA, et al. Water-mediated conformational preselection mechanism
   in substrate binding cooperativity to protein kinase A. PNAS. 2018;115(36):8997-9002.

4. Park JH, Liu Y, Lemmon MA, Radhakrishnan R. Erlotinib binds both inactive and active
   conformations of the EGFR tyrosine kinase domain. Biochem J. 2012;448(3):417-423.

5. Ramsey S, et al. Solvation thermodynamic mapping of molecular surfaces in AmberTools:
   GIST. J Comput Chem. 2016;37(21):2029-2037.

6. Haider K, Cruz A, Ramsey S, et al. Solvation Structure and Thermodynamic Mapping
   (SSTMap): An open-source, flexible package for the analysis of water in molecular
   dynamics trajectories. J Chem Theory Comput. 2018;14(1):418-425.

7. Sutto L, Gervasio FL. Effects of oncogenic mutations on the conformational free-energy
   landscape of EGFR kinase. PNAS. 2013;110(26):10616-10621.

8. Modi V, Dunbrack RL Jr. Defining a new nomenclature for the structures of active and
   inactive kinases. PNAS. 2019;116(14):6818-6827.

9. Ung PMU, et al. Conformational analysis of the DFG-out kinase motif and biochemical
   profiling of structurally validated type II inhibitors. J Med Chem. 2014;58(1):167-179.

10. Azimi S, Khuttan S, Wu JZ, Deng N, Gallicchio E. Relative binding free energy
    calculations for ligands with diverse scaffolds with the alchemical transfer method.
    J Chem Inf Model. 2022;62(2):309-323.

11. Kanev GK, et al. KLIFS: an overhaul after the first 5 years of supporting kinase
    research. Nucleic Acids Research. 2021;49:D562-D569.

12. Riley BT, et al. qFit 3: Protein and ligand multiconformer modeling for X-ray
    crystallographic and single-particle cryo-EM density maps. Protein Science.
    2021;30:270-285.

13. Breiten B, et al. Contributions of water transfer energy to protein-ligand
    association and dissociation barriers. J Am Chem Soc. 2013;135(43):15579-15584.

14. Uehara S, Tanaka S. AutoDock-GIST: Incorporating thermodynamics of active-site water
    into scoring function. Molecules. 2016;21(11):1604.
