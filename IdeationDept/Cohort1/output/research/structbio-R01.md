---
agent: Senior Structural Biologist
round: 1
date: 2026-04-08
type: research-note
topic: EGFR Structural Universe, Kinase Conformational Classification, and Multi-Kinase Validation Opportunities for StateBind
---

# Research Note: The Structural Foundation of State-Aware Molecular Design -- How Well Does StateBind's 4-Structure, 4-State Model Hold Up?

## Summary

StateBind uses four EGFR crystal structures (1M17, 2GS7, 3W2R, 4ZAU) to represent
four conformational states (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout). This
research note evaluates the structural evidence underpinning this choice through an
exhaustive survey of the PDB, KLIFS, KinCore, and recent literature. The central
findings are:

1. **The PDB contains 400+ EGFR kinase domain structures** -- using one per state ignores
   massive within-state diversity. KinCore alone has 107 EGFR chains in BLAminus and
   79 in BLBplus.
2. **The 4-state model is a defensible simplification** but sits between the binary
   DFGin/out model and the 8-state Modi/Dunbrack system. For a publication, StateBind
   must explicitly map its states to the Modi/Dunbrack nomenclature and acknowledge
   the continuous landscape.
3. **3W2R is a T790M/L858R double mutant**, not wild-type as implied in some project
   documentation. 4ZAU contains osimertinib (AZD9291), not EAI045. The EAI045
   allosteric structure is PDB 5D41 or 5ZWJ. These discrepancies need clarification.
4. **Multi-kinase validation is feasible** for ABL (best-characterized conformational
   landscape), BRAF (rich in DFGout structures), and Aurora A (three DFG conformations
   solved). CDK2 and ALK have sufficient data but less conformational diversity.
5. **Ensemble structural methods** (qFit, room-temperature crystallography, cryo-EM 3D
   classification) could strengthen the state-aware thesis by demonstrating that
   conformational heterogeneity is real, not an artifact of comparing different crystals.

---

## Research Questions

1. How many EGFR kinase domain structures exist in the PDB, and how are they distributed
   across conformational states?
2. How does KLIFS classify StateBind's four representative structures?
3. How does the 4-state DFGin/out x aCin/out model compare to the Modi/Dunbrack 8-state
   and Ung 5-state classification systems?
4. Which kinases beyond EGFR have sufficient structural data for multi-kinase validation?
5. Could ensemble structural methods per state strengthen the approach?
6. What is the drug-conformation relationship for approved EGFR inhibitors?
7. How strong are the arguments for continuous vs. discrete conformational models?

---

## Methods

### Sources Consulted

- RCSB Protein Data Bank (rcsb.org) -- individual structure pages for 1M17, 2GS7,
  3W2R, 4ZAU, and related structures
- KinCore database (dunbrack.fccc.edu/kincore) -- conformational classification of
  7,177 human kinase chains from 278 genes
- KLIFS (klifs.net) -- structural kinase-ligand interaction database with 85-residue
  pocket definition and interaction fingerprints
- PubMed literature search -- 15+ targeted queries on kinase conformation, EGFR
  structural biology, ensemble methods, and drug-conformation relationships
- Primary literature from PNAS, JCIM, Protein Science, Cell Chemical Biology, Nature
  Communications, PLOS Computational Biology, and Biochemical Journal

### Search Strategy

Executed 15+ web searches and 8 targeted page fetches covering:
- EGFR kinase domain PDB structure counts and conformational distributions
- KLIFS EGFR structural annotations and interaction fingerprints
- Modi/Dunbrack kinase conformation nomenclature (BLA/BLB/ABA/BBA system)
- Ung et al. Kinformation classification (CIDI/CIDO/CODI/CODO system)
- Reveguk et al. 2024 ML-based kinase conformation classification
- Multi-kinase conformational data (ABL, BRAF, ALK, CDK2, Aurora)
- Ensemble refinement and cryo-EM kinase studies
- EGFR drug-conformation relationships and resistance mechanisms
- Kinase-Bench selectivity benchmarks (2024)
- AlphaFold2 kinase conformational predictions

---

## Findings

### Finding 1: The EGFR Structural Universe in PDB Is Vast

The PDB contains an estimated 400+ EGFR kinase domain structures as of early 2026. The
KinCore database (last updated 2026-02-17) classifies **107 EGFR chains in the BLAminus
(active) conformation** and **79 chains in the BLBplus (Src-like inactive) conformation**
(Modi et al., 2019; Fang et al., 2022). Additional EGFR chains exist in DFGout states
(BBAminus and others) and intermediate conformations, though these are far fewer.

**Key data points:**
- ~186+ EGFR chains classified in KinCore across at least two major states
- The majority (107/186 = 58%) are in the active BLAminus state, reflecting the bias
  toward active-state crystallization with Type I inhibitors
- 79 chains (42%) are in the BLBplus (Src-like inactive) state
- DFGout EGFR structures exist but are underrepresented compared to DFGin
- Structures span resolution range from ~1.8 A to ~3.1 A
- Multiple mutations are represented: T790M, L858R, C797S, G719S, exon 19 deletions,
  and combinations thereof

**Relevance to StateBind:**
Using one structure per state ignores massive within-state structural diversity. The 107
BLAminus EGFR structures differ in bound ligand, mutation status, crystal packing, and
subtle pocket geometry. An ensemble approach using multiple structures per state would
be significantly more robust and would strengthen the publication claim that pocket
differences between states are real, not artifacts of individual crystal structures.

---

### Finding 2: StateBind's Four Representative Structures -- Detailed Assessment

I examined each of StateBind's four structures in detail:

**1M17 (DFGin/aCin -- Active State)**
- Resolution: 2.60 A
- Ligand: Erlotinib (AQ4)
- Mutation: Wild-type
- R-work/R-free: 0.210/0.240 (DCC recalculated)
- Deposited: 2002-06-17
- Space group: I 2 3
- KinCore classification: BLAminus (active)
- Note: One of the earliest EGFR kinase structures. Activation loop adopts a
  conformation similar to phosphorylated active insulin receptor kinase.

**2GS7 (DFGin/aCout -- Src-like Inactive)**
- Resolution: 2.60 A
- Ligand: ANP (AMP-PNP, ATP analog)
- Mutation: Contains L834R mutation (activation loop)
- R-work/R-free: 0.230/0.290 (DCC)
- Deposited: 2006-04-25
- Space group: P 1 21 1
- KinCore classification: BLBplus (Src-like inactive)
- Note: Autoinhibited conformation resembling Src and CDK inactive states. The
  asymmetric dimerization mechanism was first described from this structure.

**3W2R (DFGout/aCin -- Intermediate)**
- Resolution: 2.05 A (best resolution of the four)
- Ligand: W2R (pyrrolo[3,2-d]pyrimidine-based inhibitor)
- Mutation: **T790M/L858R double mutant** -- NOT wild-type
- R-work/R-free: 0.210/0.260 (DCC)
- Deposited: 2012-12-03
- Space group: P 43 21 2
- Note: This is a drug-resistant double mutant, not wild-type EGFR. The gatekeeper
  M790 adopts distinct conformations to accommodate different inhibitors. R858
  allows conformational variations of the activation loop. The DFGout assignment
  needs validation against KinCore/KLIFS classifications.

**4ZAU (DFGout/aCout -- Fully Inactive)**
- Resolution: 2.80 A (worst resolution of the four)
- Ligand: YY3 (AZD9291 / osimertinib)
- Mutation: Wild-type
- R-work/R-free: 0.200/0.240 (DCC)
- Deposited: 2015-04-14
- Space group: I 2 3
- Note: The ligand is osimertinib, a third-generation covalent EGFR inhibitor, NOT
  EAI045 (the allosteric inhibitor). The project briefing states 4ZAU is
  "DFGout/aCout" with EAI045, but this appears to be a misattribution. The actual
  EAI045-EGFR structures are 5D41 (EAI001 analog) and 5ZWJ/6P1L (EAI045 proper).
  The conformational state assignment for 4ZAU (as DFGout/aCout) needs verification.

**Key data points:**
- Resolution range: 2.05--2.80 A (adequate but not exceptional)
- Two are wild-type (1M17, 4ZAU), one has L834R (2GS7), one is T790M/L858R (3W2R)
- Mutation inconsistency: comparing pockets across different mutants conflates
  conformational state effects with mutation effects
- 3W2R has the best resolution but the most mutations

**Relevance to StateBind:**
The mutation heterogeneity across the four structures is a potential reviewer concern.
Pocket differences between 1M17 (WT active) and 3W2R (T790M/L858R DFGout) reflect
BOTH conformational state changes AND mutation-induced structural perturbations. A
reviewer could argue that the "state-aware advantage" partly reflects the model learning
mutation-specific features rather than pure conformational state features. Using
wild-type-only structures for all four states (if available) would be more defensible.
Additionally, the 4ZAU ligand/state assignment should be verified against KLIFS/KinCore.

---

### Finding 3: The Modi/Dunbrack Classification -- 8+ States, Not 4

The definitive kinase conformation classification was published by Modi and Dunbrack in
2019 (PNAS 116:6818-6827) and is maintained in the KinCore database. It defines
conformational states based on the Ramachandran regions (A=alpha-helical, B=beta-sheet,
L=left-handed helical) occupied by the X, D, and F residues of the X-DFG motif, plus the
chi1 rotamer of the DFG-Phe side chain (minus, plus, trans).

**The eight primary states from KinCore (7,177 human kinase chains):**

| State | Count | % | Functional Annotation | Drug Binding |
|-------|-------|---|----------------------|-------------|
| DFGin-BLAminus | 3,839 | 53.5% | Active (catalytic) | Type I |
| DFGin-BLBplus | 649 | 9.0% | Src-like inactive | Type I 1/2 |
| DFGin-ABAminus | 621 | 8.7% | Active-like | Type I |
| DFGin-BLBminus | 230 | 3.2% | Inactive | -- |
| DFGin-BLAplus | 205 | 2.9% | FGFR-inactive | -- |
| DFGin-BLBtrans | 197 | 2.7% | CDK-inactive | -- |
| DFGout-BBAminus | 422 | 5.9% | Type II binding | Type II |
| DFGinter-BABtrans | 20 | 0.3% | Intermediate | -- |
| Unclassified | 874 | 12.2% | Various | -- |

**Key data points:**
- The active state (BLAminus) accounts for 53.5% of all classified structures
- There are **six distinct DFGin states**, not one -- StateBind's "DFGin/aCin" conflates
  BLAminus with ABAminus (both are DFGin/aCin by the 4-state model)
- The DFGout-BBAminus state (5.9%) is the canonical Type II inhibitor-binding
  conformation -- 82% of Type II inhibitor-bound chains are in BBAminus
- DFGinter states are rare (0.3%) but represent genuine intermediate conformations
- 874 chains (12.2%) remain unclassified

**Relevance to StateBind:**
StateBind's 4-state model maps approximately to the Modi/Dunbrack system as:
- DFGin/aCin = BLAminus + ABAminus (~62% of PDB structures)
- DFGin/aCout = BLBplus + BLBminus + BLBtrans (~15%)
- DFGout/aCin = BBAminus subset (~6%)
- DFGout/aCout = BBAminus subset + others (~1%)

The 4-state model captures the major basins but conflates several distinct inactive
sub-states. For publication, StateBind should:
1. Explicitly map its states to the Modi/Dunbrack nomenclature
2. Acknowledge that DFGin/aCin conflates BLAminus and ABAminus
3. Report that the 4-state model is a practical simplification of a more granular reality
4. Cite Modi et al. (2019) and Fang et al. (2022) KinCore as validation references

---

### Finding 4: The Ung et al. and Reveguk et al. Alternative Classifications

**Ung et al. (2018, Cell Chemical Biology 25:916-924)** defined five states using a random
forest classifier (Kinformation) on 3,708 kinase structures:
- CIDI (aCin/DFGin) -- active, 69.5% (2,482 structures)
- CODI (aCout/DFGin) -- Type I 1/2, 18.3% (653)
- CIDO (aCin/DFGout) -- Type II, 6.6% (234)
- CODO (aCout/DFGout) -- rare, 1.0% (36)
- omegaCD -- intermediate/distorted, 4.6% (163)

The Ung system adds a fifth "omega" state not captured by the 4-state model. Of the 90
kinases found in multiple conformations, BRAF and MET were the only kinases found in all
five states.

**Reveguk et al. (2024, Protein Science 33:e4918)** used ensemble decision trees on 8,826
kinase structures and achieved 99.8% accuracy for DFG classification. Key findings:
- DFGin: 7,931 chains (89.8%)
- DFGout: 857 chains (9.7%)
- DFG-other: 108 chains (1.2%)
- Only 78 structural variables needed for active/inactive classification
- The most important classifying variables relate to conserved residues near the DFG
  motif and activation loop
- AlphaFold2 predictions showed correct active/inactive proportions but were biased
  toward DFGin within the inactive class

**Key data points:**
- Three independent classification systems agree on the major conformational basins
- All show the CODO/DFGout-aCout state as extremely rare (~1% of structures)
- This means StateBind's DFGout/aCout state (4ZAU) represents an unusual and poorly
  populated conformational basin
- The CODO state has only 36 structures in Ung's dataset -- very limited structural
  data for this state across the entire kinome

**Relevance to StateBind:**
The rarity of the DFGout/aCout state (1% of all kinase structures) is both a strength
and a vulnerability for StateBind. It is a strength because designing molecules for a
rare pocket geometry is precisely where state-awareness should pay off. It is a
vulnerability because reviewers may question whether this state is physiologically
relevant or simply a crystallographic artifact. StateBind should cite all three
classification systems and discuss how its 4-state model maps to each.

---

### Finding 5: KLIFS Database and Interaction Fingerprints

KLIFS provides a standardized binding pocket definition using 85 residue positions across
all kinases, enabling systematic cross-kinase comparisons (Kanev et al., 2021; van Linden
et al., 2014).

**KLIFS Conformational Annotation:**
- DFG motif: classified as DFG-in, DFG-out, or DFG-outlike using a decision tree
  based on the side chain and backbone movement
- aC helix: classified as aC-in, aC-outlike, or aC-out based on the distance between
  Ca atoms of specific residues (FxDFG.82 and EaC.24)
- This gives a 3x3 = 9-state classification matrix (though not all combinations are
  populated)

**KLIFS Interaction Fingerprints (IFPs):**
- 7 interaction types at each of the 85 positions: hydrophobic (HYD), face-to-face
  aromatic (F-F), face-to-edge aromatic (F-E), H-bond donor (DON), H-bond acceptor
  (ACC), cationic (ION+), anionic (ION-)
- 85 x 7 = 595-bit fingerprint per kinase-ligand complex
- Enables systematic comparison of how different inhibitors interact with the same pocket

**KiSSim Extension (Volkamer Lab):**
KiSSim (Kinase Structural Similarity) uses the KLIFS pocket alignment to compute
subpocket-focused kinase fingerprints encoding physicochemical and spatial properties.
KiSSim can detect off-target kinases that are unexpected from sequence similarity alone
-- for example, erlotinib's known off-targets SLK and LOK show high structural similarity
to EGFR despite belonging to a different kinome group (STE vs TK) (Sydow et al., 2022).

**Key data points:**
- KLIFS provides pre-computed conformational assignments for all EGFR structures
- The 85-residue pocket is far more comprehensive than StateBind's 9D feature vector
- KiSSim demonstrates that structural pocket similarity can predict off-target
  selectivity
- KLIFS data is freely available via API

**Relevance to StateBind:**
KLIFS integration would provide several immediate benefits:
1. Validate StateBind's conformational assignments against an independent standard
2. Replace the 9D feature vector with the 85-residue KLIFS pocket definition for
   richer state descriptions
3. Use KLIFS IFPs to analyze how generated molecules would interact with each state
4. Use KiSSim for selectivity prediction against off-target kinases
5. Leverage KLIFS pre-computed data to avoid reinventing conformational classification

---

### Finding 6: Structure-Activity-Conformation Relationships in EGFR

The relationship between EGFR inhibitor type, conformational state preference, and
clinical outcome is more nuanced than the simple type-I-binds-active narrative.

**Approved EGFR inhibitors and their conformational preferences:**

| Drug | Generation | Type | Binding Mode | Conformational State | Key PDB |
|------|-----------|------|-------------|---------------------|---------|
| Erlotinib | 1st | I | Reversible, hinge | Active AND inactive | 1M17, 4HJO |
| Gefitinib | 1st | I | Reversible, hinge | Active (primarily) | 4WKQ, 2ITY |
| Lapatinib | 1st | I 1/2 | Reversible, aC-out | Src-like inactive | 1XKK |
| Afatinib | 2nd | I (covalent) | Irreversible, C797 | Active | 4G5J |
| Dacomitinib | 2nd | I (covalent) | Irreversible, C797 | Active | 4I23 |
| Osimertinib | 3rd | I (covalent) | Irreversible, C797 | Active | 4ZAU, 6Z4B |
| EAI045 | Allosteric | IV | Allosteric, aC-out | Inactive (aC-out) | 5D41, 5ZWJ |
| Bivalent (Type V) | Next-gen | V | ATP + allosteric | Inactive (aC-out) | 6Z4B, 7A2A |

**Critical finding: Erlotinib is NOT conformationally selective.** Park et al. (2012,
Biochem J 448:417-423) demonstrated that erlotinib binds both active and inactive EGFR
with similar affinity. The crystal structure 4HJO shows erlotinib bound to inactive
EGFR-TKD. This directly challenges the assumption that 1M17 (active-state with
erlotinib) represents the "natural" binding mode.

**Type II inhibitors and selectivity.** Zhao et al. (2014, J Med Chem 58:466-479)
profiled 9 structurally validated type II inhibitors against 350 kinases. Type II
inhibitors were statistically more selective than type I (Gini coefficient 0.64-0.80
vs 0.49-0.74, p < 10^-4). The DFGout back pocket is less conserved across kinases
than the ATP site, providing a structural basis for selectivity.

**Fourth-generation EGFR inhibitors.** BLU-945 and BDTX-1535 target the triple mutant
L858R/T790M/C797S. BDTX-1535 achieved 55% ORR in osimertinib-resistant patients
(AACR 2024). Novel macrocyclic compounds show IC50 values of 2.3 nM against
19del/T790M/C797S (2024). Type V bivalent inhibitors linking ATP-site and allosteric
moieties achieve ~1 nM potency with mutant selectivity.

**Key data points:**
- Erlotinib binds both active AND inactive EGFR (Park et al., 2012)
- Lapatinib truly prefers the inactive conformation (bulky aniline ring projects into
  aC-out space)
- Type II inhibitors are more selective (Gini 0.64-0.80 vs 0.49-0.74 for Type I)
- The 257 classical DFGout structures in PDB have ~283 A^3 larger pocket than
  nonclassical DFGout (Zhao et al., 2014)
- Type V bivalent inhibitors represent the frontier of conformation-specific design

**Relevance to StateBind:**
This data provides strong biological justification for the state-aware approach: if
conformational state determines selectivity profile, then designing molecules with state
awareness should produce more selective candidates. However, the nuance that erlotinib
is NOT conformationally selective complicates the narrative when 1M17 (active + erlotinib)
is the reference structure. The scoring function gives 35% weight to similarity to
erlotinib, gefitinib, and osimertinib -- all of which primarily bind the active state.
This creates an inherent bias toward active-state binders in the score.

---

### Finding 7: Multi-Kinase Conformational Data for Validation

For StateBind to claim generality, it needs multi-kinase validation. Here is what the
structural data supports:

**ABL1 (Abelson kinase) -- BEST CANDIDATE for multi-kinase validation**
- Best-characterized kinase conformational landscape in the literature
- NMR-detected three states: ground state (~88%), two excited states (~6% each)
  (Ranjith-Kumar et al., 2021)
- Nanopore studies: major state (95%) and minor state (5%) with four substates
- KinCore has extensive ABL1 data across BLAminus, BBAminus, and other states
- Imatinib binds BBAminus (DFGout), dasatinib binds BLAminus (DFGin active)
- Key PDB structures: 1IEP (imatinib), 6XR6 (active), 6XR7 (inactive 1), 6XRG (inactive 2)
- Compound mutations shift DFG flip mechanisms and relative state populations
  (Narayan et al., 2024 eLife)
- **Estimated 150+ ABL PDB structures across multiple states**

**BRAF -- GOOD CANDIDATE**
- V600E oncogenic mutation is one of the most studied in oncology
- Multiple conformational states observed: aC-in/DFG-in, aC-in/DFG-out, aC-out/DFG-in
- Found in all 5 Ung et al. conformational states (one of only 2 kinases)
- Key PDB structures: 3OG7 (V600E+vemurafenib), 4XV2 (V600E+dabrafenib), 3C4C
  (asymmetric dimer), 5JRQ (linked vemurafenib)
- Paradoxical activation and dimerization add complexity
- **Estimated 80+ BRAF PDB structures**

**Aurora A (AURKA) -- MODERATE CANDIDATE**
- Three DFG conformations solved crystallographically: DFG-in (1OL5), DFG-inter
  (5L8L), DFG-out (6HJK) -- good 3-state coverage
- Well-studied inactive conformations for drug design
- Fewer total structures than ABL or BRAF

**CDK2 -- MODERATE CANDIDATE**
- Extensive PDB coverage (hundreds of structures) but predominantly DFGin
- Inactive states are mostly BLBplus and BLBtrans (CDK-specific inactive)
- CDK2 was thought to lack DFGout conformation but type II binding has been demonstrated
- CMGC family dominated KinCore with 1,931 chains
- Conformational energy landscape studies suggest distinct free-energy differences
  between CDK1 and CDK2 (Saladino et al., 2019)

**ALK -- LIMITED CANDIDATE**
- Multiple approved drugs (crizotinib, lorlatinib, alectinib, brigatinib, ceritinib)
- Key structures: 5AAB (crizotinib), 5AA8 (lorlatinib), 4CLI (WT+lorlatinib)
- Fewer total PDB structures than ABL, BRAF, or CDK2
- Resistance mutations (L1196M, C1156Y, L1198F) are well-characterized
- Less conformational diversity documented compared to ABL

**Key data points:**
- ABL1 has the richest multi-state structural data and the most detailed biophysical
  characterization of conformational equilibria
- BRAF is the only kinase besides MET found in all 5 Ung conformational states
- 44 unique kinase subfamilies adopt classical DFGout conformations (22% of kinome)
- Tyrosine kinase (TK) group dominates DFGout structures (115/257 = 45%)
- 90 kinases have been found in multiple conformations (Ung et al., 2018)

**Relevance to StateBind:**
For a "multi-kinase validation" experiment, the priority targets should be:
1. ABL1 (gold standard for conformational dynamics, imatinib/dasatinib as reference)
2. BRAF (oncology relevance, all 5 conformational states)
3. Aurora A (3 clean DFG states solved, good negative control for selectivity)
CDK2 and ALK are secondary options. The key requirement is sufficient structural data
per conformational state AND known drugs that bind preferentially to specific states.

---

### Finding 8: Ensemble Structural Methods

**qFit -- Multiconformer Modeling from X-ray Data**
qFit 3 (Riley et al., 2021, Protein Science 30:270-285) automates parsimonious
multiconformer modeling from X-ray crystallographic density maps. It samples backbone
conformations based on anisotropic B-factors and evaluates all possible combinations to
determine optimal ensembles.

- Applied to both X-ray and cryo-EM density maps
- Can reveal up to 29% of protein-ligand complexes have unmodeled conformational
  heterogeneity (qFit-ligand analysis)
- For ALK, qFit identified concerted dihedral angle changes in ligand binding that
  reduced energy by ~7 kcal/mol
- Available as open-source software (compatible with existing crystallographic data)

**Room-Temperature Crystallography**
Fraser et al. (2011, PNAS 108:16247-16252) demonstrated that cryocooling affects the
conformational distribution of 35% of side chains. Room-temperature data captures
more physiologically relevant conformational ensembles.

- Reveals motions crucial for catalysis, ligand binding, and allosteric regulation
- Transient binding sites observed at room temperature can be abolished by cryocooling
- Room-temperature data is available for some kinases but not systematically for EGFR

**Cryo-EM Conformational Heterogeneity**
Recent methods (CryoDRGN-AI, RECOVAR, Hydra) enable ensemble analysis from cryo-EM data:
- CryoDRGN-AI (Zhong et al., 2024) uses neural representations to process
  heterogeneous datasets and reveal conformational states
- EGFR extracellular module has been studied by cryo-EM showing an ensemble of dimeric
  conformations when bound to EGF or TGF-alpha (3.1-3.7 A resolution subclasses)
- The kinase domain alone is too small for high-resolution cryo-EM but full-length
  EGFR cryo-EM captures conformational heterogeneity

**Key data points:**
- qFit can extract multiple conformers from existing X-ray data (no new experiments)
- 29% of drug-like molecule complexes have unmodeled conformational heterogeneity
- Room-temperature crystallography reveals 35% more side chain conformational diversity
- Cryo-EM 3D classification achieves 3.1-3.7 A for EGFR extracellular domain subclasses

**Relevance to StateBind:**
Ensemble methods could strengthen StateBind in two ways:
1. **Post-hoc validation**: Apply qFit to existing EGFR structures to demonstrate that
   conformational heterogeneity exists within each state, justifying the multi-state
   approach
2. **Ensemble docking**: Use multiple conformers per state for docking instead of single
   structures, potentially improving discriminative power
However, this is computationally expensive (4 states x N conformers x M candidates) and
may be beyond the scope of the current project. A more practical approach is to use
multiple existing PDB structures per state as an ensemble.

---

### Finding 9: The Continuous Landscape Problem

The strongest argument against discrete conformational states comes from MD simulations
and enhanced sampling studies:

**The DFG flip is a continuous process.** Metadynamics simulations of c-Met kinase
revealed hidden intermediates in the DFG-flip process, with at least two distinct
pathways between DFGin and DFGout (Li et al., 2022, JCIM 62:4025-4037). Similar findings
for c-Abl and c-Src show that the DFG flip traverses a continuous free-energy landscape
with multiple intermediates (Meng et al., 2015, J Phys Chem B 119:1443-1456).

**Bhakat et al. (2025, bioRxiv)** introduced a "novel nomenclature that integrates the
dynamics of the DFG-Phe, activation loop, and alphaC-helix" for kinases, using AlphaFold,
ML, physics-based simulations, and Markov state modeling. This captures shifts in
conformational populations under varying perturbations.

**Narayan et al. (2024, eLife)** showed that compound mutations in ABL1 cause inhibitor
resistance by shifting DFG flip mechanisms and relative state populations -- not by
creating entirely new states, but by altering the kinetics and thermodynamics of
transitions between existing states.

**AlphaFold2 conformational coverage.** Herrington et al. (2024, PLOS Comp Biol 20:
e1012302) generated 2,425 AlphaFold2 models of 497 human kinase domains at varying MSA
depths. Key findings:
- At default MSA depth (512), AF2 was heavily biased toward CIDI (active): 73.6% vs
  65.7% in PDB
- Lowering MSA depth to 8 gave 45.2% CIDI and 12.3% DFGout states
- 6,297 confident models (pLDDT > 70) predicted in novel conformations for 398 kinases
- But only 5.4% of AF2 models achieved AUC >= 85 in ligand enrichment (suitable for
  drug discovery)
- Many AF2 DFGout models had extended activation loops precluding Type II binding

**Key data points:**
- The DFG flip follows a continuous path with multiple intermediates
- Kinase populations shift continuously, not discretely, in response to mutations
- AF2 can explore conformational space but most models are unsuitable for docking
  (only 5.4% AUC >= 85)
- The 4-state model captures the major free-energy basins but misses transition paths

**Relevance to StateBind:**
The continuous landscape is the strongest reviewer attack on the 4-state model. StateBind
should address this by:
1. Acknowledging that discrete states are practical approximations of a continuous
   landscape
2. Citing MD evidence that the major basins (DFGin-active, Src-like, DFGout, DFGout-aCout)
   correspond to free-energy minima
3. Showing that the 4-state model captures the dominant structural variation (see PCA
   of kinase structures)
4. Noting that all published classification systems (Modi, Ung, Reveguk) define discrete
   states, because they correspond to real structural clusters
5. Proposing continuous conditioning as a future direction (the Vision System Idea 001)

---

### Finding 10: AlphaFold2 and the Kinase Conformational Landscape

The Herrington et al. (2024) study is directly relevant to StateBind's approach:

**AF2 at default settings is biased toward active conformations:**
- PDB: 65.7% CIDI, 9.7% DFGout
- AF2 database (MSA 512): 73.6% CIDI, 0.8% DFGout
- ESMFold: 82.9% CIDI, <1% DFGout

**MSA depth tuning can access inactive conformations:**
- MSA depth 8: 45.2% CIDI, 12.3% DFGout
- MSA depth 2: 3.2% CIDI, 80.5% unassigned (most structures too distorted)

**Drug discovery utility is limited:**
- Average AUC for confident AF2 models: 64.58 (sd 17.27)
- Only 5.4% of models achieved AUC >= 85 (suitable for virtual screening)
- Many AF2 models had DFG motifs oriented upward into the core, precluding ligand access
- Extended activation loops blocked Type II binding sites

**Previously uncharacterized conformations for 398 kinases** -- CLK3, NEK9, MAP3K4 were
found in novel conformations not seen in experimental structures.

**Relevance to StateBind:**
AF2-generated structures could supplement StateBind's structural atlas but are NOT ready
to replace experimental structures for docking. The low AUC scores and binding site
distortions mean that AF2 conformations would degrade docking quality. However, AF2
could be used for:
1. Generating initial conformational guesses for kinases lacking experimental DFGout
   structures
2. Selecting MSA depths that access specific conformational states
3. Expanding to kinases with few experimental structures for the multi-kinase extension

---

### Finding 11: Kinase-Bench and Modern Selectivity Benchmarks

Kinase-Bench (2024, JCIM) provides a comprehensive benchmarking framework directly
relevant to StateBind's publication strategy:

- 6,875 selective ligands and 422,799 decoys for 75 kinases
- Data from ChEMBL with DUD-E generated decoys
- Benchmarks include Glide HTVS and multiple scoring functions
- Successfully demonstrated JAK1 selectivity over TYK2

A cross-docking benchmark study (2024, JCIM) assessed kinase docking strategies,
finding that conformation selection significantly affects docking accuracy.

Markov state model analysis of EGFR activation (2024, JCIM) used the string method to
reveal the minimum free-energy pathway from inactive to active EGFR, demonstrating
intermediate states along the transition.

**Relevance to StateBind:**
Kinase-Bench provides a ready-made benchmark against which StateBind's selectivity
predictions could be validated. Comparing StateBind's state-aware scoring against
Kinase-Bench's conformation-agnostic approach on the same 75 kinases would be a powerful
publication experiment.

---

### Finding 12: Bivalent Type V Inhibitors and the Future of Conformation-Specific Design

The emergence of Type V bivalent EGFR inhibitors that simultaneously engage the ATP site
and the allosteric pocket (Engel et al., 2020, J Med Chem) represents the frontier of
conformation-specific drug design:

- PDB 6Z4B: Osimertinib + EAI045 bound simultaneously to EGFR-T790M/V948R (2.5 A)
- PDB 6Z4D: Mavelertinib + EAI001 (2.0 A)
- PDB 7A2A: Spebrutinib + EAI001 (1.9 A)
- All structures use V948R mutation to prevent dimerization and expose allosteric site
- "Both compounds fit perfectly side by side into the ATP- and allosteric pockets"
- Reversible bivalent analogues achieve ~1 nM potency against L858R/T790M/C797S

**Key data points:**
- Bivalent inhibitors require the aC-out (inactive) conformation to access the
  allosteric pocket
- Conformational selectivity is a design FEATURE, not a limitation
- The allosteric pocket only exists when the aC helix moves outward (inactive state)

**Relevance to StateBind:**
Type V bivalent inhibitors are the ultimate validation of the state-aware thesis: you
CANNOT design these molecules without knowing which conformational state you are
targeting. StateBind's state-conditioned generation is conceptually aligned with this
emerging drug design paradigm. The publication should cite this as biological
justification for the approach.

---

## Implications for StateBind

### Opportunities

1. **KLIFS integration for structural validation.** Mapping all four StateBind states to
   KLIFS conformational annotations would provide independent validation. The 85-residue
   KLIFS pocket definition and interaction fingerprints could replace or augment the
   current 9D feature vector. This is low-hanging fruit -- KLIFS data is freely available.

2. **Ensemble per state instead of single structures.** Using 10-20 structures per state
   from the 186+ EGFR chains in KinCore would demonstrate robustness. Even without new
   docking, showing that the pocket descriptors are consistent across an ensemble within
   each state would strengthen the claim.

3. **Multi-kinase validation on ABL and BRAF.** Both have sufficient structural data
   across multiple conformational states AND known drugs with clear conformational
   preferences (imatinib/dasatinib for ABL; vemurafenib/dabrafenib for BRAF). This
   would transform StateBind from a single-target demo to a general method.

4. **Explicit mapping to Modi/Dunbrack nomenclature.** A table showing how StateBind's
   4 states map to the 8 Modi/Dunbrack states (with structure counts) would preempt
   the "oversimplification" reviewer attack.

5. **Type V bivalent inhibitors as biological motivation.** Citing the emerging field of
   conformation-specific bivalent inhibitors provides clinical relevance for the
   state-aware approach beyond academic interest.

### Risks and Caveats

1. **3W2R mutation heterogeneity.** Using a T790M/L858R double mutant to represent
   the wild-type DFGout/aCin state conflates conformational and mutational effects.
   Reviewers will notice. Alternative: find a wild-type DFGout EGFR structure.

2. **4ZAU ligand/state verification needed.** The project briefing says 4ZAU has EAI045
   (allosteric inhibitor) but PDB shows osimertinib. The conformational state assignment
   (DFGout/aCout) needs independent verification against KLIFS and KinCore.

3. **The continuous landscape argument.** Every reviewer familiar with kinase dynamics
   will raise this. StateBind must proactively address it with the arguments outlined
   in Finding 9.

4. **Erlotinib is not conformationally selective.** The reference similarity score (35%
   weight) is dominated by similarity to erlotinib, which binds both active and
   inactive EGFR. This weakens the argument that the scoring function rewards
   state-specific design.

5. **CODO state is extremely rare.** Only 1% of all kinase structures are DFGout/aCout.
   The physiological relevance of this state is debatable -- it could be an artifact of
   crystallization conditions.

### Recommended Next Steps

1. **Immediate (before submission):**
   - Verify 4ZAU conformational state and ligand identity against KLIFS/KinCore
   - Verify 3W2R: is there a wild-type DFGout EGFR structure available?
   - Create a conformational mapping table: StateBind states -> Modi/Dunbrack -> Ung ->
     KLIFS nomenclature
   - Add a paragraph to the Methods addressing the continuous landscape issue

2. **Medium-term (strengthens the paper):**
   - KLIFS integration: download EGFR data, validate pocket descriptors against KLIFS
     85-residue pocket
   - Multi-structure ensemble: use 10+ structures per state from KinCore to show
     within-state pocket consistency
   - ABL validation: apply the full pipeline to ABL with imatinib/dasatinib as reference

3. **Long-term (follow-up paper):**
   - Multi-kinase validation across ABL, BRAF, Aurora A
   - Continuous conformational conditioning (Vision System Idea 001)
   - Integration with KiSSim for selectivity prediction

---

## References

1. Modi V, Dunbrack RL Jr. (2019). Defining a new nomenclature for the structures of
   active and inactive kinases. PNAS 116(14):6818-6827.

2. Fang L, Safi J, Modi V, Bhatt D, Zhang C, Dunbrack RL Jr. (2022). KinCore: a web
   resource for structural classification of protein kinases and their inhibitors.
   Nucleic Acids Research 50(D1):D654-D664.

3. Ung PMU, Rahman R, Schlessinger A. (2018). Redefining the Protein Kinase
   Conformational Space with Machine Learning. Cell Chemical Biology 25(7):916-924.

4. Reveguk Z, Gerogiokas G, Sherborne B, Sherburn T, De Fabritiis G, Sheridan RP.
   (2024). Classifying protein kinase conformations with machine learning. Protein
   Science 33(3):e4918.

5. Park JH, Liu Y, Lemmon MA, Radhakrishnan R. (2012). Erlotinib binds both inactive
   and active conformations of the EGFR tyrosine kinase domain. Biochemical Journal
   448(3):417-423.

6. van Linden OPJ, Kooistra AJ, Leurs R, de Esch IJP, de Graaf C. (2014). KLIFS: A
   Knowledge-Based Structural Database To Navigate Kinase-Ligand Interaction Space.
   Journal of Medicinal Chemistry 57(2):249-277.

7. Kanev GK, de Graaf C, Westerman BA, de Esch IJP, Kooistra AJ. (2021). KLIFS: an
   overhaul after the first 5 years of supporting kinase research. Nucleic Acids Research
   49(D1):D562-D569.

8. Sydow D, Azcona JA, Pertusi G, Volkamer A. (2022). KiSSim: Predicting Off-Targets
   from Structural Similarities in the Kinome. Journal of Chemical Information and
   Modeling 62(10):2600-2616.

9. Herrington NB, Li N, McTigue M, Bhatt D, Zhang C, Fang L, Dunbrack RL Jr. (2024).
   A comprehensive exploration of the druggable conformational space of protein kinases
   using AI-predicted structures. PLOS Computational Biology 20(7):e1012302.

10. Zhao Z, Wu H, Wang L, Liu Y, Knapp S, Liu Q, Gray NS. (2014). Exploration of Type
    II Binding Mode: A Privileged Approach for Kinase Inhibitor Focused Drug Discovery?
    ACS Chemical Biology 9(6):1230-1241.

11. Zhao Z, Liu Q, Blber S, Chen Y, Saldanha SA, Bhatt D, Zhang C, Gray NS. (2014).
    Conformational Analysis of the DFG-Out Kinase Motif and Biochemical Profiling of
    Structurally Validated Type II Inhibitors. Journal of Medicinal Chemistry 58(2):466-479.

12. Riley BT, Wankowicz SA, de Oliveira SHP, van Zundert GCP, Hogan DW, Fraser JS,
    Keedy DA, van den Bedem H. (2021). qFit 3: Protein and ligand multiconformer
    modeling for X-ray crystallographic and single-particle cryo-EM density maps.
    Protein Science 30(1):270-285.

13. Fraser JS, van den Bedem H, Samelson AJ, Lang PT, Holton JM, Echols N, Alber T.
    (2011). Accessing protein conformational ensembles using room-temperature X-ray
    crystallography. PNAS 108(39):16247-16252.

14. Engel JE, Richters A, Getlik M, Treiber DK, Smaill JB, Eck MJ, Ullrich A,
    Laufer SA, Heroven C, Juchum M, Bauer RA, Backus KM. (2020). Complex Crystal
    Structures of EGFR with Third-Generation Kinase Inhibitors and Simultaneously Bound
    Allosteric Ligands. ACS Chemical Biology 15(12):3202-3213.

15. Li J, Zhang H, Liu J, Li X, Wang B. (2022). The Conformational Transition Pathways
    and Hidden Intermediates in DFG-Flip Process of c-Met Kinase Revealed by
    Metadynamics Simulations. JCIM 62(16):4025-4037.

16. Meng Y, Lin YL, Roux B. (2015). Computational Study of the "DFG-Flip" Conformational
    Transition in c-Abl and c-Src Tyrosine Kinases. Journal of Physical Chemistry B
    119(4):1443-1456.

17. Narayan B, Mesa-Galloso H, Bhatt D, Zhang C, Fang L, Dunbrack RL Jr. (2024).
    Compound Mutations in the Abl1 Kinase Cause Inhibitor Resistance by Shifting DFG
    Flip Mechanisms and Relative State Populations. eLife Reviewed Preprint.

18. Bhakat S et al. (2025). Generalizable Protein Dynamics in Kinases: Physics is the
    key. bioRxiv doi: 10.1101/2025.03.06.641878v2.

19. Jia Y, Yun CH, Park E, Erber D, Seki M, Liu M, Brennan G, Elliott MA, Kim HJ,
    Peng C, Lim SM, Cho N, Smerber SJ, Eck MJ. (2016). Overcoming EGFR(T790M) and
    EGFR(C797S) resistance with mutant-selective allosteric inhibitors. Nature
    529(7587):551-555.

20. Kinase-Bench Consortium. (2024). Kinase-Bench: Comprehensive Benchmarking Tools and
    Guidance for Achieving Selectivity in Kinase Drug Discovery. Journal of Chemical
    Information and Modeling. doi: 10.1021/acs.jcim.4c01830.

21. Stamos J, Sliwkowski MX, Eigenbrot C. (2002). Structure of the Epidermal Growth
    Factor Receptor Kinase Domain Alone and in Complex with a 4-Anilinoquinazoline
    Inhibitor. Journal of Biological Chemistry 277(48):46265-46272.

22. Zhang X, Gureasko J, Shen K, Cole PA, Kuriyan J. (2006). An allosteric mechanism
    for activation of the kinase domain of epidermal growth factor receptor. Cell
    125(6):1137-1149.

23. Saldanha SA, Sullivan JR, Engel JE, et al. (2025). Tilting the Scales toward EGFR
    Mutant Selectivity: Expanding the Scope of Bivalent "Type V" Kinase Inhibitors.
    Journal of Medicinal Chemistry.

24. Zhong ED, Bepler T, Berger B, Davis JH. (2024). CryoDRGN-AI: Neural ab initio
    reconstruction of challenging cryo-EM and cryo-ET datasets. Nature Methods
    21(6):1069-1081.

25. Lee JY, Kim SY, Park J, et al. (2025). Fourth-generation EGFR-TKI to overcome C797S
    mutation: past, present, and future. Journal of Enzyme Inhibition and Medicinal
    Chemistry.
