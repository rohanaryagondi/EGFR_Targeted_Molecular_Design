---
agent: Senior Computational Chemist
round: 2
date: 2026-04-08
type: proposal
proposal_id: compchem-P01
title: "Physics-Based Validation via Water Thermodynamics and Free Energy Perturbation"
---

# Proposal: Physics-Based Validation via Water Thermodynamics and Free Energy Perturbation

## Proposing Agent
Senior Computational Chemist -- Expertise in free energy calculations, molecular
dynamics, force field development, water thermodynamics, and the physics of molecular
recognition.

## Problem Statement

StateBind's central thesis -- that different conformational states present different
binding pockets -- is currently supported only by docking scores from GNINA v1.1, an
empirical scoring function with RMSE ~2.5-3.0 kcal/mol that ignores explicit water,
protein flexibility, entropy, and long-range electrostatics (McNutt et al., 2021;
Sunseri & Koes, 2025). The 10x retrospective enrichment result is the project's
headline, but the underlying physics of WHY different states yield different binding
outcomes is never demonstrated. Reviewers at JCIM or Nature Computational Science will
ask two questions this proposal directly answers:

1. **"Are the 4 conformational states physically distinct binding environments, or just
   different coordinate sets?"** -- GIST water thermodynamics answers this by showing
   that the states have measurably different water networks, enthalpy landscapes, and
   numbers of displaceable high-energy hydration sites.

2. **"Are the top-ranked candidates genuinely better binders, or just scoring function
   artifacts?"** -- OpenFE relative binding free energy calculations answer this with
   physics-based binding free energies at ~1 kcal/mol RMSE, a 2-3x improvement over
   GNINA's thermodynamic accuracy.

Without physics-based validation, StateBind's scoring outputs are pattern-matched
numbers, not thermodynamic predictions. This proposal converts them into publishable
physical evidence.

## Vision

After executing this proposal, the StateBind publication will include:

- **Publication-quality figure** showing water thermodynamic maps for all 4 EGFR
  conformational states, with per-voxel enthalpy, entropy, and free energy density
  color-coded on the binding pocket surface. The figure will demonstrate at the atomic
  level that DFGin/aCin, DFGin/aCout, DFGout/aCin, and DFGout/aCout present
  physically distinct solvation environments.

- **Quantitative state-discrimination metrics** -- number of displaceable high-energy
  waters per state, total deltaG of water displacement, pocket desolvation free energy
  -- providing thermodynamic evidence for the state-aware hypothesis that goes beyond
  docking scores.

- **FEP-validated binding free energies** for the top 20 candidates, demonstrating
  that GNINA-favored state-aware candidates also have favorable computed binding free
  energies at a level of accuracy (RMSE ~0.7-1.7 kcal/mol) that approaches
  experimental error.

- **A physics-based narrative** that transforms the paper from "we ran a pipeline and
  got enrichment" to "we demonstrate that conformational states create physically
  distinct binding environments and that state-aware design exploits water
  thermodynamics and pocket-specific binding energetics."

---

## Background and Evidence

### The Accuracy Hierarchy: Why GNINA Is Insufficient

Published benchmarks across kinase systems establish a consistent accuracy hierarchy
for binding affinity prediction:

| Method | Typical RMSE (kcal/mol) | Correlation (R^2) | Source |
|--------|------------------------|-------------------|--------|
| Relative FEP (RBFE) | 0.68-1.73 | 0.5-0.8 | OpenFE benchmark; KLK6 study |
| Absolute FEP (ABFE) | 1.0-2.0 | variable | FEP-SPell-ABFE benchmarks |
| SQM2.20 (semi-empirical QM) | ~1.5 equiv. | 0.69 (PL-REX) | Pecina et al., 2024 |
| MM-GBSA | 1.5-3.0 | 0.0-0.9 | Hou et al., 2011 |
| Empirical docking (GNINA) | 2.0-3.0 | 0.3-0.5 | GNINA 1.0/1.3 benchmarks |

GNINA v1.1 (StateBind's Tier 0) sits near the bottom of this hierarchy. Its CNN
scoring function improves pose prediction (73% Top1 redocking vs 58% for Vina) but not
thermodynamic ranking accuracy (Sunseri & Koes, 2025). The delta between StateBind's
known binders (-7.32 kcal/mol) and non-binders (-4.16 kcal/mol) is only 3.16 kcal/mol
-- within the noise floor of empirical docking. Moving up the accuracy hierarchy is
essential for publication credibility.

### Water Thermodynamics Differentiates Kinase Conformational States

Published evidence directly supports using water analysis to discriminate between
kinase states:

1. **WaterMap on SRC kinase** (Robinson et al., 2010; Robinson et al., 2014):
   Identified 36 hydration sites in the ATP pocket, 21 with positive (unfavorable)
   free energy. Water displacement energetics in the selectivity pocket: deltaG = 2.6-6.6
   kcal/mol per displaced water. Different kinase conformations present distinct water
   patterns that explain selectivity differences.

2. **Water-mediated conformational selection in PKA** (Kim et al., 2018, PNAS): Water
   affinity to binding sites increases by almost 4 kcal/mol upon ligand binding,
   contributing to stabilizing specific conformational states. Water is not a passive
   medium but an active participant in conformational selection.

3. **Water-mediated allosteric networks in Aurora kinase** (Cyphers et al., 2017):
   A water-mediated allosteric network links the C-helix to the active site, directly
   demonstrating that water networks differ between active and inactive conformations
   and mediate conformational coupling.

4. **p38alpha MAP kinase WaterMap study** (Breiten et al., 2013): Water displacement
   contributions to binding free energy quantified at 0.5-3.0 kcal/mol per displaced
   water for congeneric inhibitor series. Demonstrated that water transfer energy
   dominates residence time differences.

5. **AutoDock-GIST on Factor Xa** (Uehara & Tanaka, 2016): Incorporating GIST water
   thermodynamics into AutoDock4 scoring improved R^2 from ~0.3 to 0.41-0.50 and
   improved docking success rate. Direct evidence that water terms improve scoring
   accuracy.

6. **DFG-out pocket water displacement physics** (Ung et al., 2014): The DFG-out
   allosteric pocket is hydrophobic with trapped high-energy waters. Type II inhibitors
   gain potency primarily through displacing these waters. This pocket does NOT exist
   in DFGin states, providing a clear physical basis for state-dependent binding.

### Open-Source FEP Is Production-Ready

The OpenFE consortium benchmark (Gapsys et al., 2025/2026) -- the largest collaborative
FEP study to date, involving 15 pharmaceutical companies -- demonstrates that
open-source FEP is ready for production use:

- **Public dataset** (58 targets, 876 ligands, >7,000 calculations): Weighted RMSE =
  1.73 [1.53, 1.96] kcal/mol. 10 of 58 systems achieved sub-kcal/mol accuracy.
- **Private dataset** (37 targets, 864 ligands, real pharma campaigns): Weighted RMSE =
  2.44 [1.94, 3.06] kcal/mol. Reflects real-world complexity.
- **KLK6 kinase RBFE** (Menke et al., 2023): MUE = 0.53, RMSE = 0.68 kcal/mol --
  substantially outperforming MM-GBSA on the same system.
- **Schrodinger FEP+ prospective validation** (Wang et al., 2015): 78% of predicted
  tight binders (<100 nM) confirmed; 69% within 1 log unit. Kinase-specific RBFE RMSE:
  0.68-1.03 kcal/mol across Abl, TYK2, and other systems.

OpenFE is MIT-licensed, uses OpenMM as its backend, installs via conda
(`conda install -c conda-forge openfe`), and runs on GPU. Wall time per pairwise RBFE
transformation: ~3 hours on a single GPU (OpenFE v1.7).

### Key Evidence
1. GIST water analysis costs <2 GPU-days for all 4 states yet provides direct
   thermodynamic evidence for state discrimination (Ramsey et al., 2016; Haider et al.,
   2018).
2. OpenFE RBFE achieves 0.68-1.73 kcal/mol RMSE on kinase systems -- 2-3x better than
   GNINA -- and is now production-ready at 15 pharma companies (Gapsys et al., 2025).
3. Water displacement energetics of 2.6-6.6 kcal/mol per water in kinase selectivity
   pockets (Robinson et al., 2010) provide the physical mechanism for state-dependent
   binding.
4. SQM2.20 achieves R^2 = 0.69 across 10 diverse targets at ~20 min/complex, providing
   an orthogonal physics-based validation tier (Pecina et al., 2024).

### Relationship to Existing Work
- **StateBind current state:** 4 EGFR crystal structures (1M17, 2GS7, 3W2R, 4ZAU)
  prepared for GNINA docking. GNINA scores normalized to [0,1] via sigmoid. No water
  analysis. No free energy calculations. No explicit solvent treatment of any kind.
- **Vision System idea 011 (Water Thermodynamics):** Deferred at P2 with "Large" effort
  estimate. The original idea sketched a grid-based crystallographic water approach.
  This proposal substantially extends it by: (a) using MD-based GIST rather than
  crystallographic water parsing, which is far more rigorous; (b) framing water analysis
  as a state-discrimination tool rather than a scoring component; (c) coupling it with
  FEP for a complete physics-based validation stack; (d) providing precise compute costs
  and a concrete protocol.
- **Literature precedent:** WaterMap studies on kinases (Robinson et al., 2010, 2014),
  GIST on Factor Xa (Uehara & Tanaka, 2016), and PKA water-mediated conformational
  selection (Kim et al., 2018) establish the methodology. No prior study has applied
  GIST water thermodynamics to compare binding environments across multiple
  conformational states of the same kinase for the purpose of validating state-aware
  molecular design. This is a novel application.

---

## Proposed Approach

### Overview

This proposal is structured in three tiers of increasing cost and rigor. Tier 1 (GIST
water thermodynamics) is the highest-value experiment per compute dollar -- cheap, fast,
and directly validates the core thesis. Tier 2 (OpenFE RBFE) provides the most rigorous
computational binding validation possible. Tier 3 (SQM2.20 rescoring) adds an
orthogonal physics-based validation layer. Ensemble docking enhancement runs in parallel
with Tier 1 to address the single-structure limitation.

### Implementation Steps

#### Tier 1: GIST Water Thermodynamic Analysis (Week 1)

**Goal:** Produce publication-quality evidence that the 4 EGFR conformational states
present physically distinct water networks in their binding pockets.

**Step 1.1: System Preparation (Day 1)**
- Obtain structures: 1M17 (DFGin/aCin), 2GS7 (DFGin/aCout), 3W2R (DFGout/aCin),
  4ZAU (DFGout/aCout). Note: 3W2R is a T790M/L858R double mutant; if structbio
  identifies a clean wild-type DFGout/aCin alternative, use that instead.
- Strip ligands but retain crystallographic waters for initial solvation.
- Add hydrogens with tleap (AmberTools) using ff19SB protein force field and TIP3P
  water model.
- Solvate in an orthorhombic box with 12 A buffer. Neutralize with Na+/Cl- at 0.15M.
- Each system: ~60,000-80,000 atoms.

**Step 1.2: Equilibration MD (Day 1-2)**
- Minimize: 5000 steps steepest descent, 5000 steps conjugate gradient.
- Heat: 0 to 300 K over 100 ps with 10 kcal/mol/A^2 restraints on protein heavy atoms.
- Equilibrate: 5 ns NPT at 300 K, 1 atm. Gradually reduce restraints to 1 kcal/mol/A^2
  on backbone only (GIST requires restrained solute).
- Platform: OpenMM 8 on H200 GPU. Estimated speed: 200-300 ns/day for this system size.
  Total equilibration: ~2 hours per system, 8 hours for all 4 states.

**Step 1.3: Production MD for GIST (Days 2-3)**
- Run 10-20 ns restrained production MD per state (backbone restrained at 1 kcal/mol/A^2).
  GIST requires the solute to be in essentially one conformation -- the restraints are
  not a limitation but a requirement (AMBER-hub GIST tutorial).
- Save coordinates every 1 ps (10,000-20,000 frames per trajectory).
- Total production time: 40-80 ns across 4 states. At 250 ns/day on H200, this is
  <1 GPU-day.
- Output: 4 trajectory files (netcdf) + 4 topology files (prmtop).

**Step 1.4: GIST Computation (Day 3-4)**
- Tool: cpptraj (AmberTools, conda installable via `conda install -c conda-forge
  ambertools`).
- GIST parameters:
  - `gridcntr`: center of binding pocket (determined from co-crystallized ligand
    coordinates or KLIFS pocket residue centroids)
  - `griddim`: 60 x 60 x 60 (30 A cube centered on pocket)
  - `gridspacn`: 0.5 A (recommended for binding site analysis)
  - `refdens`: 0.0334 molecules/A^3 (bulk TIP3P at 300K, 1 atm)
  - `temp`: 300
- GIST output per voxel: gO (oxygen density), Esw-dens (solute-water energy density),
  Eww-dens (water-water energy density), dTStrans-dens (translational entropy density),
  dTSorient-dens (orientational entropy density).
- Post-processing: convert density maps to per-water thermodynamic quantities by
  dividing by local density and multiplying by reference density. Reference to bulk
  values using TIP3P reference tables from AmberTools documentation.
- Runtime: minutes to hours per system. Negligible compared to MD.

**Step 1.5: Analysis and Figure Generation (Days 4-5)**
- For each state, compute:
  - Total number of hydration sites with deltaG_sw > +1.0 kcal/mol (high-energy,
    displaceable)
  - Total number of hydration sites with deltaG_sw < -1.0 kcal/mol (low-energy,
    conserved)
  - Total desolvation free energy: sum of positive deltaG sites in the binding pocket
  - Entropy-enthalpy decomposition: fraction of unfavorable solvation that is enthalpic
    vs entropic
- Cross-state comparison metrics:
  - Jaccard similarity of high-energy water positions between states
  - Per-voxel correlation of solvation free energy between all 6 state pairs
  - Pocket volume occupied by unfavorable water (A^3) per state
- Generate publication figure: 4-panel layout, one panel per state, showing the binding
  pocket surface colored by water free energy (blue = favorable, red = unfavorable).
  VMD or PyMOL for rendering with .dx grid file overlay.

**Expected Results:**
- DFGin/aCin (active, smallest pocket, ~450 A^3): fewest displaceable waters, most
  conserved hinge water network. Limited room for type II extension.
- DFGout/aCout (fully inactive, largest pocket, ~850 A^3): most displaceable
  high-energy waters in the allosteric extension. Highest desolvation free energy --
  strong thermodynamic driving force for type II inhibitors.
- DFGin/aCout and DFGout/aCin: intermediate water network complexity. The aC-out
  rotation rearranges waters near the helix, while DFG-out creates the hydrophobic
  allosteric extension.
- This gradient directly mirrors StateBind's pocket volume gradient and provides the
  thermodynamic basis for why state-aware design matters.

**Compute cost:** <2 GPU-days total (MD + GIST analysis).
**Timeline:** 5 working days including setup, production, and analysis.

---

#### Tier 2: OpenFE RBFE on Top Candidates (Weeks 2-3)

**Goal:** Demonstrate that top state-aware candidates have favorable computed binding
free energies, not just favorable scoring function values, using the gold-standard
open-source FEP methodology.

**Step 2.1: Candidate Selection and Grouping (Day 1)**
- Select top 10 state-aware candidates by unified score.
- Select top 10 static candidates by unified score.
- Group into chemical series where possible (RBFE requires a perturbation network within
  structurally related molecules).
- Note on diverse chemotypes: OpenFE uses the Kartograf atom mapper for geometric
  atom mapping. Ring-breaking transformations are currently not supported. If StateBind's
  candidates span diverse scaffolds, the perturbation network may need to be split into
  multiple disconnected series. Within each series, RBFE is highly accurate; across
  series, absolute binding free energy (ABFE) would be needed, which is more expensive
  (~20-40 GPU-hours per compound).

**Step 2.2: System Preparation (Days 2-3)**
- For each conformational state used in the comparison (at minimum: 1M17 for static,
  plus the primary state targeted by each state-aware candidate):
  - Prepare protein with OpenFE's Protein Component (PDB to OpenMM system)
  - Generate 3D conformers for each candidate using RDKit ETKDG
  - Dock conformers into the appropriate receptor using GNINA to obtain binding poses
  - Parameterize ligands using OpenFF (Open Force Field) Sage 2.0.0 or later
- OpenFE installation: `conda install -c conda-forge openfe` (supports OpenMM 8.0-8.2)

**Step 2.3: Perturbation Network Construction (Day 3)**
- Use OpenFE's LigandNetwork planner with LOMAP scoring to generate a minimal spanning
  tree perturbation network within each chemical series.
- Aim for 3-5 transformations per ligand in the network for redundancy (star graph
  with a central reference compound + additional edges for cycle closure).
- Estimated transformations: 40-60 total for 20 candidates.

**Step 2.4: Production FEP Runs (Days 4-10)**
- OpenFE RBFE protocol with default settings (these are the settings validated in the
  large-scale benchmark):
  - 11 lambda windows per transformation
  - 5 ns per lambda window (total 55 ns per edge)
  - Replica exchange between lambda windows for enhanced sampling
  - OpenMM backend on H200 GPU
- Wall time per transformation: ~3 hours on a single H200 GPU.
- Total: 40-60 transformations x 3 hours = 120-180 GPU-hours.
- With 16 GPUs (2 H200 nodes), wall time: ~8-12 hours.

**Step 2.5: Analysis (Days 11-14)**
- Compute relative binding free energies using MBAR (Multistate Bennett Acceptance
  Ratio) -- built into OpenFE.
- Compare FEP-derived rankings to:
  - GNINA Vina score ranking
  - GNINA CNN affinity ranking
  - MPNN pIC50 ranking
  - Unified score ranking
- Metrics: Spearman rho, Kendall tau, RMSE between methods.
- Test hypothesis: do state-aware candidates have statistically more favorable binding
  free energies than static candidates? Mann-Whitney U test on FEP deltaG values.

**Expected Results:**
- If FEP confirms GNINA ranking: the scoring function is reliable, and the 10x
  enrichment rests on solid thermodynamic ground.
- If FEP disagrees with GNINA: this reveals scoring function limitations and provides
  FEP-corrected rankings. Either way, this is a publishable and scientifically
  valuable outcome.
- Expected FEP accuracy: RMSE ~1.0-1.7 kcal/mol (based on OpenFE kinase benchmarks).

**Compute cost:** 120-180 GPU-hours for RBFE. If ABFE needed for cross-series
comparison: add 600-1200 GPU-hours. Total RBFE-only: ~1 day on 2 H200 nodes.
Total with ABFE: 2-4 days on 2 H200 nodes.
**Timeline:** 2 weeks including setup, parameterization, production, and analysis.

---

#### Tier 3 (Optional): SQM2.20 Rescoring (Parallel with Tier 2)

**Goal:** Provide an orthogonal physics-based validation tier between docking and FEP.

**Step 3.1: Structure Preparation**
- Take GNINA-docked poses for the top 50 candidates (top 35 state-aware + top 15
  static).
- Optimize hydrogen positions using the MOPAC MOZYME linear-scaling algorithm.

**Step 3.2: SQM2.20 Scoring**
- Run SQM2.20 on each protein-ligand complex.
- Runtime: ~20 minutes per complex.
- Total: 50 complexes x 4 states = 200 complexes x 20 min = ~67 CPU-hours (~3
  CPU-days, parallelizable to hours on multi-core nodes).

**Step 3.3: Analysis**
- Compare SQM2.20 scores to GNINA scores and FEP results (if available).
- SQM2.20 achieves R^2 = 0.69 on the PL-REX benchmark (Pecina et al., 2024),
  coincidentally matching StateBind's MPNN R^2 = 0.69 -- but SQM2.20 is physics-based
  and generalizes to novel chemotypes without training data.

**Compute cost:** ~3 CPU-days (parallelizable). No GPU required.
**Timeline:** 3-5 days, can run fully in parallel with Tier 2.

---

#### Ensemble Docking Enhancement (Parallel with Tier 1)

**Goal:** Move from 1 crystal structure per state to 5-10 structures per state, capturing
within-state pocket flexibility.

**Step E.1: Structure Selection from KLIFS**
- KLIFS database contains 100+ EGFR crystal structures across conformational states
  (Modi & Dunbrack, 2019 report 107 BLAminus chains, 79 BLBplus chains).
- Select 5 representative structures per state using KLIFS pocket RMSD clustering.
- Prioritize: resolution <2.5 A, wild-type or clinically relevant mutations, diverse
  co-crystallized ligands (to sample induced fit diversity).

**Step E.2: Structure Preparation and Docking**
- Prepare all 20 structures (5 per state x 4 states) as PDBQT for GNINA.
- Re-dock StateBind's top 50 candidates against all 20 structures.
- GNINA runtime: ~23 seconds per complex. 50 x 20 = 1,000 dockings = ~6.4 GPU-hours.
- Consensus scoring: take the best score across the ensemble for each state (max
  enrichment protocol, per Rueda et al., 2014).

**Step E.3: Analysis**
- Compare ensemble docking rankings to single-structure rankings.
- Published improvements: 3-24% relative improvement in enrichment factor with ensemble
  approaches (Rueda et al., 2014; Vijayan et al., 2024).
- AlphaFold2 multi-state modeling achieved EF1% of 8.2 vs 6.6 for single structures
  across 25 kinases (Vijayan et al., 2024).

**Compute cost:** ~1 GPU-day (structure prep + docking).
**Timeline:** 3-5 days, parallel with Tier 1.

---

### Technical Details

**Software stack (all freely available via conda-forge):**

| Tool | Purpose | Install |
|------|---------|---------|
| AmberTools (cpptraj) | GIST water analysis | `conda install -c conda-forge ambertools` |
| OpenMM 8.x | MD engine for GIST trajectories | `conda install -c conda-forge openmm` |
| OpenFE 1.9 | RBFE/ABFE free energy | `conda install -c conda-forge openfe` |
| OpenFF Sage 2.0 | Small molecule force field | Bundled with OpenFE |
| SSTMap | Alternative GIST (if cpptraj issues) | `pip install sstmap` |
| VMD or PyMOL | Visualization of water maps | Available on Bouchet |
| SQM2.20 / MOPAC | Semi-empirical QM scoring | Standalone binary |
| GNINA v1.1 | Ensemble docking | Already deployed on Bouchet |

**Force fields:**
- Protein: ff19SB (AMBER) -- current best practice for kinase simulations.
- Water: TIP3P -- standard for GIST analysis, consistent with GNINA's implicit treatment.
- Ligands: OpenFF Sage 2.0 -- superior to GAFF2 for drug-like molecules, directly
  supported by OpenFE.

**Data requirements:**
- 4 EGFR crystal structures (already available in StateBind pipeline)
- Top 20 candidates with SMILES (from existing ranked output)
- KLIFS structures for ensemble docking (freely downloadable)
- All data is publicly available; no proprietary data needed.

---

## Impact Assessment

### Publication Impact
- **Target venue:** JCIM (primary), Nature Computational Science (aspirational with
  multi-kinase expansion)
- **Main claim this enables:** "Conformational state-aware molecular design exploits
  state-specific water thermodynamics and is validated by physics-based free energy
  calculations" -- transforms the paper from a pipeline report to a physical chemistry
  contribution.
- **Reviewer concerns this addresses:**
  - **"Where is the experimental validation?"** -- FEP is the gold-standard
    computational substitute, with prospective success rates of 78% true positive
    (Wang et al., 2015). While not experimental, FEP is universally accepted as the
    most rigorous computational evidence.
  - **"Are the 4 states really different?"** -- GIST water maps provide direct
    thermodynamic proof at the atomic level.
  - **"GNINA is just docking, not binding free energy"** -- FEP provides actual
    binding free energies with quantified uncertainty.
  - **"4 static crystal structures"** -- Ensemble docking with KLIFS structures
    addresses this directly.

### Effort Estimate

| Tier | Compute | Wall Time (2x H200 nodes) | Implementation |
|------|---------|--------------------------|----------------|
| Tier 1: GIST | <2 GPU-days | 1 week (incl. setup) | Moderate (MD setup + cpptraj) |
| Tier 2: OpenFE RBFE | 120-180 GPU-hours | 2 weeks (incl. setup) | Moderate-High (FEP parameterization) |
| Tier 3: SQM2.20 | 3 CPU-days | 3-5 days | Low (standalone binary) |
| Ensemble docking | ~1 GPU-day | 3-5 days | Low (GNINA re-run) |
| **Total Tiers 1+2** | **~5-7 GPU-days** | **~3 weeks** | |
| **Total all tiers** | **~6-8 GPU-days + 3 CPU-days** | **~3-4 weeks** | |

- **Compute:** All tiers fit within standard Bouchet allocation. No special allocation
  request needed. Tier 1+2 combined: ~200-400 GPU-hours on H200.
- **Data:** All publicly available (PDB, KLIFS, StateBind existing outputs).
- **Implementation:** Moderate. The hardest part is FEP setup and parameterization for
  diverse chemotypes. GIST is straightforward with established tutorials. Ensemble
  docking reuses existing GNINA infrastructure.
- **Dependencies:** Tier 1 is independent and should start immediately. Tier 2 benefits
  from Tier 1 results (understanding which states matter most) but is not blocked by
  it. Tier 3 and ensemble docking are fully independent.

### Risk Assessment

**Technical risks:**

1. **FEP may not converge for diverse chemotypes.** StateBind's VAE-generated candidates
   may span multiple scaffolds with limited structural similarity. Standard RBFE
   requires congeneric series with small perturbations. If candidates are too diverse,
   ring-breaking transformations may be needed (not supported in OpenFE's current
   protocol), or ABFE must be used instead (higher cost).
   - *Mitigation:* Group candidates by Murcko scaffold first. Run RBFE within groups.
     For cross-group comparison, use the ATM (Alchemical Transfer Method), which
     handles diverse chemotypes without atom mapping (Azimi et al., 2022). Budget ABFE
     compute as contingency.

2. **GIST results may not show clear state differentiation.** If the 4 states have
   similar water networks (e.g., the binding pocket region probed by current ligands is
   the same across states), this weakens the state-aware hypothesis.
   - *Mitigation:* A negative result here is still valuable -- it would indicate that
     the state-aware advantage comes from pocket geometry or electrostatics rather than
     water thermodynamics. This is publishable as a mechanistic finding.

3. **3W2R structural concerns.** 3W2R is a T790M/L858R double mutant, not wild-type.
   Using it for the DFGout/aCin state conflates mutational and conformational effects.
   - *Mitigation:* Check KLIFS for a wild-type DFGout/aCin alternative. If none exists,
     run GIST on both 3W2R and the closest wild-type structure and report the
     difference. Flag the mutation issue explicitly in the paper.

4. **4ZAU state assignment.** Structbio flagged that 4ZAU may not be correctly classified
   as DFGout/aCout.
   - *Mitigation:* Verify against KLIFS and KinCore databases before starting. If
     4ZAU is misclassified, substitute with the correct representative structure.

5. **Force field limitations for FEP.** OpenFF Sage 2.0 may have limited coverage for
   some kinase inhibitor functional groups (e.g., covalent warheads, unusual
   heterocycles).
   - *Mitigation:* Check OpenFF coverage for each candidate before committing to FEP.
     Fall back to GAFF2 parameterization if needed.

**Scientific risks:**

6. **FEP may disagree with GNINA rankings.** If FEP shows that static candidates bind
   as well or better than state-aware candidates, this weakens the publication
   narrative.
   - *Mitigation:* This is actually a valuable finding. FEP-GNINA disagreement reveals
     scoring function limitations and motivates the delta-ML approach (training an ML
     correction from GNINA to FEP). Report honestly. A paper that says "our scoring
     function has limitations and here is how physics-based validation reveals them" is
     more credible than one that cherry-picks confirmatory results.

---

## Evaluation Criteria

1. **Tier 1 success: GIST differentiates states.** The 4 conformational states should
   show statistically significant differences in at least 2 of: (a) number of
   high-energy hydration sites, (b) total desolvation free energy, (c) per-voxel
   solvation free energy spatial correlation (<0.7 between most dissimilar states).
   Threshold: p < 0.05 for pairwise Wilcoxon tests on per-voxel deltaG distributions.

2. **Tier 1 success: DFG-out has more displaceable waters.** DFGout states should have
   measurably more high-energy hydration sites than DFGin states (consistent with the
   larger, more hydrophobic allosteric pocket). Expected: 5-15 additional displaceable
   waters in DFGout/aCout vs DFGin/aCin, corresponding to 15-100 kcal/mol additional
   desolvation free energy.

3. **Tier 2 success: FEP validates top candidates.** Top state-aware candidates should
   have computed binding free energies within 2 kcal/mol of reference drugs (erlotinib
   deltaG ~ -10 to -11 kcal/mol). FEP-GNINA rank correlation (Spearman rho) should be
   > 0.4, indicating that GNINA rankings are at least partially physics-grounded.

4. **Tier 2 success: State-aware candidates bind favorably.** Mean FEP deltaG for top
   10 state-aware candidates should be at least 1.0 kcal/mol more favorable than mean
   FEP deltaG for top 10 static candidates. This corresponds to ~5-fold difference in
   binding affinity.

5. **Publication-quality figure.** Water thermodynamic maps for all 4 states rendered
   at sufficient resolution for journal publication (300+ DPI, clear color scale,
   annotated pocket features).

6. **Ensemble docking improvement.** Ensemble docking should improve EF@10 by at least
   5% relative to single-structure docking, consistent with published benchmarks.

---

## Open Questions

1. **Which DFGout/aCin structure to use?** 3W2R carries T790M/L858R mutations. Is there
   a wild-type EGFR crystal structure in DFGout/aCin in KLIFS? If not, should we model
   back-mutations computationally, or use 3W2R with explicit caveats?

2. **RBFE or ABFE for cross-series comparison?** If StateBind's top candidates span
   multiple scaffolds, RBFE within series + ABFE for cross-series anchoring is the
   standard approach, but ABFE adds significant compute (20-40 GPU-hours per compound).
   Is the additional cost justified by the publication venue target?

3. **Should GIST water scores enter the scoring function?** Tier 1 produces water
   thermodynamic maps. These could be converted into a solvation scoring component.
   However, datasci cautions (Round 1 synthesis) that changing the scoring function to
   make state-aware win is scientifically questionable. Resolution: report water
   analysis as independent validation evidence, not as a scoring component. If the
   community demands it, provide results under both original and water-augmented scoring.

4. **How to handle the 3D requirement?** GIST analysis produces 3D water maps. Comparing
   candidates to these maps requires 3D poses (from GNINA docking). StateBind already
   has GNINA docked poses for candidates run through Tier 0. Confirm these are archived
   and accessible for overlay with GIST maps.

5. **Convergence checking for GIST.** GIST results must be converged. The standard check
   is to compute GIST on the first half vs second half of the trajectory and compare
   maps. If 10 ns is insufficient, extend to 20 ns (still cheap). How much trajectory
   is needed for the EGFR pocket size (~850 A^3 at largest)?

6. **Integration with multi-kinase expansion.** If the project expands to additional
   kinases (ABL, etc.), should GIST and FEP be run on those kinases too? This would
   strengthen the generalizability claim but multiply compute costs proportionally.

---

## References

1. McNutt AT, Francoeur P, Aggarwal R, et al. GNINA 1.0: molecular docking with deep
   learning. J Cheminform. 2021;13:43. doi:10.1186/s13321-021-00522-2

2. Sunseri J, Koes DR. GNINA 1.3: the next increment in molecular docking with deep
   learning. J Cheminform. 2025;17:19. doi:10.1186/s13321-025-00973-x

3. Gapsys V, et al. Large-scale collaborative assessment of binding free energy
   calculations for drug discovery using OpenFE. ChemRxiv. 2025/2026.
   doi:10.26434/chemrxiv-2025-7sthd

4. Wang L, Wu Y, Deng Y, et al. Accurate and reliable prediction of relative ligand
   binding potency in prospective drug discovery by way of a modern free-energy
   calculation protocol and force field. J Am Chem Soc. 2015;137(7):2695-2703.

5. Menke J, et al. Assessing the performance of docking, FEP, and MM/GBSA methods on
   a series of KLK6 inhibitors. J Comput Aided Mol Des. 2023;37:515-530.
   doi:10.1007/s10822-023-00515-3

6. Robinson DD, Giovambattista N, Friesner RA, et al. Understanding kinase selectivity
   through energetic analysis of binding site waters. ChemMedChem. 2010;5(4):618-627.
   doi:10.1002/cmdc.200900526

7. Robinson DD, et al. Application of MM-GB/SA and WaterMap to SRC kinase inhibitor
   potency prediction. J Comput Aided Mol Des. 2014. doi:10.1007/s10822-014-9735-9

8. Kim J, Ahuja LG, Chao FA, et al. Water-mediated conformational preselection mechanism
   in substrate binding cooperativity to protein kinase A. PNAS. 2018;115(36):8997-9002.
   doi:10.1073/pnas.1720024115

9. Cyphers S, et al. A water-mediated allosteric network governs activation of Aurora
   kinase A. Nat Chem Biol. 2017;13:402-408. doi:10.1038/nchembio.2296

10. Uehara S, Tanaka S. AutoDock-GIST: Incorporating thermodynamics of active-site
    water into scoring function for accurate protein-ligand docking. Molecules. 2016;
    21(11):1604.

11. Breiten B, et al. Contributions of water transfer energy to protein-ligand
    association and dissociation barriers: WaterMap analysis of a series of p38alpha MAP
    kinase inhibitors. J Am Chem Soc. 2013;135(43):15579-15584.

12. Ung PMU, et al. Conformational analysis of the DFG-out kinase motif and biochemical
    profiling of structurally validated type II inhibitors. J Med Chem. 2014;58(1):
    167-179. doi:10.1021/jm501603h

13. Ramsey S, et al. Solvation thermodynamic mapping of molecular surfaces in
    AmberTools: GIST. J Comput Chem. 2016;37(21):2029-2037.

14. Haider K, Cruz A, Ramsey S, et al. Solvation Structure and Thermodynamic Mapping
    (SSTMap): An open-source, flexible package for the analysis of water in molecular
    dynamics trajectories. J Chem Theory Comput. 2018;14(1):418-425.

15. Pecina A, Fanfrlik J, et al. SQM2.20: Semiempirical quantum-mechanical scoring
    function yields DFT-quality protein-ligand binding affinity predictions in minutes.
    Nat Commun. 2024;15:1127. doi:10.1038/s41467-024-45431-8

16. Rueda M, et al. Assessing an ensemble docking-based virtual screening strategy for
    kinase targets by considering protein flexibility. J Chem Inf Model. 2014;54(10):
    2826-2836. doi:10.1021/ci500414b

17. Vijayan RK, et al. Improving docking and virtual screening performance using
    AlphaFold2 multi-state modeling for kinases. Sci Rep. 2024;14:24654.
    doi:10.1038/s41598-024-75400-6

18. Modi V, Dunbrack RL Jr. Defining a new nomenclature for the structures of active
    and inactive kinases. Proc Natl Acad Sci USA. 2019;116(14):6818-6827.
    doi:10.1073/pnas.1814279116

19. Sutto L, Gervasio FL. Effects of oncogenic mutations on the conformational
    free-energy landscape of EGFR kinase. PNAS. 2013;110(26):10616-10621.
    doi:10.1073/pnas.1221953110

20. Aldeghi M, Heifetz A, Bodkin MJ, et al. Predicting kinase inhibitor resistance:
    physics-based and data-driven approaches. ACS Cent Sci. 2019;5(8):1468-1474.
    doi:10.1021/acscentsci.9b00590

21. Hou T, et al. Assessing the performance of the MM/PBSA and MM/GBSA methods. 1.
    The accuracy of binding free energy calculations based on molecular dynamics
    simulations. J Chem Inf Model. 2011;51(1):69-82. doi:10.1021/ci100275a

22. Azimi S, Khuttan S, Wu JZ, Deng N, Gallicchio E. Relative binding free energy
    calculations for ligands with diverse scaffolds with the alchemical transfer method.
    J Chem Inf Model. 2022;62(2):309-323. doi:10.1021/acs.jcim.1c01129

23. De Ruiter A, Boresch S, Kartograf: A geometrically accurate atom mapper for hybrid-
    topology relative free energy calculations. J Chem Theory Comput. 2024;20(1):
    431-441. doi:10.1021/acs.jctc.3c01206

24. Eastman P, et al. OpenMM 8: Molecular dynamics simulation with machine learning
    potentials. J Phys Chem B. 2024;128:109-118.

25. Boyles F, et al. Delta machine learning to improve scoring-ranking-screening
    performances of protein-ligand scoring functions. J Chem Inf Model. 2022;62(12):
    2965-2978. doi:10.1021/acs.jcim.2c00485
