---
agent: Sr. Journal Reviewer -- Comp Bio
round: 2
date: 2026-04-09
type: review-assessment
scope: verification
---

# Round 2 Verification Report: Novelty, Selectivity Claims, and Structural Integrity

## Executive Summary

Three high-priority claims were subjected to deep verification through extensive web
research (40+ searches, 20+ page fetches across PDB, PubMed, KLIFS, bioRxiv, and
journal databases). Key findings: (1) The novelty claim -- that no published paper
conditions molecular generation on discrete conformational state labels -- is VERIFIED
with high confidence; the closest competitors (DynamicBind, DynamicFlow, Apo2Mol,
FLOWR, PLACER, CSDesign) all use fundamentally different mechanisms. (2) The Type II
Gini selectivity claim (0.76 vs 0.58) is PARTIALLY VERIFIED as directionally correct
but the exact values require careful attribution; the most likely source is Muller et
al. (2015, J. Med. Chem.), which reports individual values in this range but not
precisely these means. (3) The EGFR WT DFGout structure search uncovered a CRITICAL
codebase integrity issue: the project uses structures annotated as wild-type that are
actually mutants in PDB, and 4ZAU (used for DFGout/aCout) is likely in a DFGin active
conformation, not DFGout. This must be resolved before any publication.

---

## Task 1: FINAL Novelty Verification

### Claim
"No published paper explicitly conditions molecular generation on discrete
conformational state labels (DFG/aC classifications) and benchmarks retrospective
enrichment."

### Verdict: VERIFIED

After exhaustive searching across PubMed, bioRxiv, ChemRxiv, arXiv, Google Scholar,
and direct inspection of all competitor methods, I can confirm with high confidence
that **no published paper as of April 2026 conditions molecular generation on discrete
conformational state labels (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout)
and evaluates via retrospective enrichment.**

### Systematic Search Strategy

Searches conducted:
1. "conformational state conditioned molecular generation discrete DFG kinase drug design" (2020-2026)
2. "state-conditioned OR state-aware molecular generation kinase DFG conformation label VAE GAN diffusion" (2023-2025)
3. "discrete conformational state conditioning molecular generation drug design benchmark"
4. "conformation-aware OR conformation-conditioned molecular generation kinase inhibitor design benchmark enrichment"
5. bioRxiv/ChemRxiv searches for 2025-2026 preprints on kinase conformation conditioning
6. PubMed searches for conformational state conditioned molecular generation
7. Direct inspection of DynamicBind, DynamicFlow, Apo2Mol, FLOWR, PLACER, CSDesign papers

### Competitor Method Analysis

#### DynamicBind (Lu et al., 2024, Nature Communications)
- **Mechanism:** Deep equivariant generative model that predicts ligand-specific
  protein-ligand complex structures. Uses a diffusion process that simultaneously
  transforms apo protein structure and noisy ligand into holo complex.
- **Does NOT use discrete state labels.** DynamicBind handles conformational flexibility
  through learned continuous dynamics. It does not classify conformations into discrete
  states and does not condition generation on state labels.
- **Distinction from StateBind:** DynamicBind is a docking/pose prediction tool, not a
  molecular generator conditioned on conformational states.
- **Citation:** Lu, W. et al. "DynamicBind: predicting ligand-specific protein-ligand
  complex structure with a deep equivariant generative model." Nat. Commun. 15, 1071 (2024).

#### DynamicFlow (2025, ICLR 2025)
- **Mechanism:** SE(3)-equivariant full-atom flow model that simultaneously transforms
  apo pockets and noisy ligands into holo states and binding molecules. Uses a
  residue-level transformer for long-range dependencies plus atom-level GNN for local
  interactions.
- **Does NOT use discrete state labels.** DynamicFlow uses continuous apo-to-holo
  transitions, not discrete conformational state classification. It learns the
  transformation from apo to holo conformations.
- **Distinction from StateBind:** DynamicFlow integrates dynamics into SBDD but through
  continuous flow matching, not discrete state conditioning.
- **Citation:** "Integrating Protein Dynamics into Structure-Based Drug Design via
  Full-Atom Stochastic Flows." ICLR 2025. arXiv:2503.03989.

#### Apo2Mol (2024/2025, AAAI 2025)
- **Mechanism:** Full-atom hierarchical graph-based diffusion model that simultaneously
  generates 3D ligand molecules and holo pocket conformations from apo inputs. Uses
  SE(3)-equivariant attention layers within hierarchical message passing. Trained on
  24,000+ apo-holo structure pairs.
- **Does NOT use discrete state labels.** Apo2Mol conditions on 3D pocket structure
  (apo form), not on discrete conformational state labels. It is dynamics-aware through
  apo-holo pairs but does not classify kinase states.
- **Distinction from StateBind:** Apo2Mol handles protein flexibility through structural
  input (apo pocket), not categorical conditioning. It does not use DFG/aC labels.
- **Citation:** "Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion
  Models." AAAI 2025. arXiv:2511.14559.

#### FLOWR (Karami et al., 2025)
- **Mechanism:** Continuous and categorical flow matching with equivariant optimal
  transport for structure-based ligand generation. Achieves PoseBusters validity of
  0.92 and offers up to 70x inference speedup vs diffusion.
- **Does NOT use discrete state labels.** FLOWR conditions on 3D pocket structure
  directly, not on conformational state categories. It is structure-conditioned, not
  state-conditioned.
- **Distinction from StateBind:** FLOWR takes a pocket as input, not a state label.
  If given different pocket structures (e.g., DFGin vs DFGout), it would produce
  different molecules, but the conditioning is on geometry, not on discrete labels.
- **Citation:** Karami et al. "FLOWR -- Flow Matching for Structure-Aware De Novo,
  Interaction- and Fragment-Based Ligand Generation." arXiv:2504.10564 (2025).

#### PLACER (Anishchenko et al., 2024/2025, PNAS)
- **Mechanism:** Graph neural network that generates conformational ensembles of
  protein-small molecule systems using entirely atomic representation. Predicts
  protein side chain conformations and ligand placement from backbone + ligand
  composition.
- **Does NOT use discrete state labels.** PLACER generates structural ensembles
  stochastically; conformational diversity is sampled, not conditioned on labels.
- **Distinction from StateBind:** PLACER maps conformational landscapes by repeated
  stochastic sampling, not by conditioning on discrete state categories.
- **Citation:** Anishchenko, I. et al. "Modeling protein-small molecule conformational
  ensembles with PLACER." PNAS 121, e2427161122 (2025).

#### CSDesign (2025, bioRxiv/ICLR 2025)
- **Mechanism:** Designs protein SEQUENCES that prefer a target conformation over
  alternative conformations. Applied to MAP kinase ERK2 (active vs inactive).
- **Does NOT generate small molecules.** CSDesign is a protein design method, not a
  molecular generation method. It designs proteins, not drugs.
- **Distinction from StateBind:** Different task entirely. CSDesign conditions protein
  sequence design on conformation, but this is protein engineering, not drug design.
- **Citation:** "Conformation-specific Design: a New Benchmark and Algorithm with
  Application to Engineer a Constitutively Active Map Kinase." bioRxiv 2025.04.23.650138.

#### REINVENT 4 (Loeffler et al., 2024)
- **Mechanism:** RL-based molecular generation with customizable scoring components.
  Can dock against specific pockets using plugins.
- **Does NOT use discrete state labels.** REINVENT can be run on different pockets
  sequentially (pocket-specific optimization), but it does not condition generation
  on discrete conformational state labels in the way StateBind does (one-hot vector
  at every decoder timestep).
- **Distinction from StateBind:** Running REINVENT on 4 pockets is "pocket-specific
  optimization," not "state-conditioning." The paper must carefully distinguish these.

### Critical Framing Requirement

The novelty is VERIFIED but must be narrowly scoped. The correct claim is:

> "First systematic benchmark evaluating whether discrete conformational state-
> conditioning (using DFG/aC classifications) improves molecular generation for
> kinase drug design, assessed via retrospective enrichment."

The claim must NOT be:
- "First dynamics-aware molecular design" (DynamicBind, DynamicFlow predate this)
- "First conformation-conditioned generation" (FLOWR, Apo2Mol condition on structure)
- "First to consider protein flexibility" (many methods do this)

### Additional Search Results

- A comprehensive curated list of molecular generation papers (AspirinCode/papers-for-
  molecular-design-using-DL on GitHub) was checked. No entry conditions on discrete
  kinase conformational state labels.
- DiffMC-Gen (Yang, 2025, Advanced Science) uses multi-conditional diffusion but
  conditions on molecular properties, not protein conformational states.
- PharmaDiff (2025) conditions on 3D pharmacophores, not conformational states.
- MolSnapper (2024, JCIM) conditions on 3D pharmacophore constraints.
- None of these use discrete DFG/aC state labels for conditioning.

---

## Task 2: Type II Gini Selectivity Verification

### Claim
"Type II inhibitors have Gini coefficient 0.76 vs Type I 0.58, indicating better
selectivity."

### Verdict: PARTIALLY VERIFIED -- Directionally Correct, Exact Values Require
Careful Attribution

### Primary Source Identification

The most likely source for these specific values is **Muller et al. (2015)**, published
in J. Med. Chem. as "Conformational Analysis of the DFG-Out Kinase Motif and
Biochemical Profiling of Structurally Validated Type II Inhibitors" (doi:
10.1021/jm501603h, PMC4326797).

Key data from this paper:
- **Panel:** 350 recombinant human protein kinases (Reaction Biology Corp HotSpot)
- **Type II inhibitors profiled:** 13 structurally validated compounds
- **Type I inhibitors profiled:** 4 structurally validated compounds (from prior study)
- **Individual Type II Gini values ranged from 0.64 to 0.80** (e.g., imatinib = 0.76,
  sorafenib = 0.79)
- **Individual Type I Gini values ranged from 0.49 to 0.74** (e.g., sunitinib = 0.52,
  indirubin derivative E804 = 0.49)
- **Statistical significance confirmed:** Three independent tests:
  - Null hypothesis: p = 7.49 x 10^-5
  - Two-sample t-test: p = 1.56 x 10^-5
  - Alternative null: p = 8.08 x 10^-8
- The paper states "type II inhibitors are indeed more selective than type I inhibitors"
  with "statistical significance."

### Analysis of the 0.76 and 0.58 Values

The value 0.76 corresponds to the Gini coefficient of **imatinib specifically** (a
well-known Type II inhibitor), not the mean of all Type II inhibitors. The value 0.58
falls within the Type I range but does not correspond to any single compound in the
accessible data. These values may represent mean or median values from a specific
analysis, but I could not verify that they are published as "mean Gini for Type I"
and "mean Gini for Type II" in any single paper.

### Other Potential Sources Investigated

1. **Graczyk (2007), J. Med. Chem.:** Original Gini coefficient paper. Profiled 40
   inhibitors against 85 kinases. Did NOT distinguish Type I vs Type II.

2. **Davis et al. (2011), Nature Biotechnology:** Comprehensive profiling of 72
   inhibitors against 442 kinases. States "type II inhibitors are more selective than
   type I" with p < 10^-4, but I could not access the exact mean Gini values.

3. **Uitdehaag & Zaman (2012), Br. J. Pharmacol.:** Uses selectivity entropy, not
   Gini, as primary metric. Notes Type II/III are more selective but does not report
   Gini comparisons.

4. **Shen et al. (2019)**, Zhao et al. (2014), Elkins et al. (2016) -- searched but
   could not locate the specific 0.76/0.58 comparison in any of these papers.

### Recommendation

The directional claim (Type II more selective than Type I) is **robustly supported**
across multiple large-scale profiling studies with high statistical significance.
However, the specific values 0.76 and 0.58 should be:

1. Verified against the full Table 4 of Muller et al. (2015) to compute actual means
2. If they cannot be traced to a published mean, they should be reported as
   representative individual values with proper attribution, or the claim should be
   restated as "Type II inhibitors demonstrate statistically significantly higher
   Gini selectivity than Type I (p < 10^-4, Muller et al., 2015; Davis et al., 2011)"
3. The paper should avoid citing specific mean values that cannot be traced to a
   published table

### Key References for Gini Selectivity

- Graczyk, P.P. "Gini coefficient: a new way to express selectivity of kinase
  inhibitors against a family of kinases." J. Med. Chem. 50, 5773-5779 (2007).
- Davis, M.I. et al. "Comprehensive analysis of kinase inhibitor selectivity."
  Nat. Biotechnol. 29, 1046-1051 (2011).
- Muller, S. et al. "Conformational Analysis of the DFG-Out Kinase Motif and
  Biochemical Profiling of Structurally Validated Type II Inhibitors." J. Med. Chem.
  58, 1610-1629 (2015).
- Uitdehaag, J.C.M. & Zaman, G.J.R. "A guide to picking the most selective kinase
  inhibitor tool compounds for pharmacological validation of drug targets." Br. J.
  Pharmacol. 166, 858-876 (2012).
- Muller, S., Chaikuad, A., Gray, N.S. & Knapp, S. "The ins and outs of selective
  kinase inhibitor development." Nat. Chem. Biol. 11, 818-821 (2015).

---

## Task 3: EGFR WT DFGout Structure Search

### Claim
StateBind uses 3W2R for DFGout/aCin and 4ZAU for DFGout/aCout. The question is
whether wild-type EGFR DFGout structures exist.

### Verdict: CRITICAL STRUCTURAL DATA INTEGRITY ISSUE DISCOVERED

This verification task uncovered a problem far more serious than the original question.
The StateBind codebase contains multiple structural annotation errors that undermine
the conformational state atlas and must be corrected before publication.

### Finding 3A: 3W2R Is a T790M/L858R Double Mutant, Not Wild-Type

**PDB 3W2R** is titled "EGFR Kinase domain T790M/L858R mutant with compound 4"
(deposited 2012-12-03, 2.05 A resolution, Sogabe et al.).

The codebase at `src/statebind/processing/structures.py:188-199` lists:
```python
StructureRecord(
    pdb_id="3w2r",
    mutations_present=[],  # <-- INCORRECT: should be ["T790M", "L858R"]
    notes="DFG-out with type-II inhibitor.",
)
```

This confirms the Round 1 concern: **3W2R is a double mutant structure being used
as if it were wild-type.** The T790M gatekeeper mutation alters the binding pocket
volume and hydrophobic character. The L858R mutation stabilizes the active conformation
and is clinically associated with drug sensitivity. Using this structure to represent
the wild-type DFGout/aCin state conflates mutational and conformational effects.

### Finding 3B: 4ZAU Is Likely DFGin/Active, Not DFGout/aCout

**PDB 4ZAU** is titled "AZD9291 complex with wild type EGFR" (deposited 2015-04-14,
2.80 A resolution, Squire/Yosaatmadja et al.). Published in Yosaatmadja et al., J.
Struct. Biol. 192, 539-544 (2015).

This IS wild-type EGFR (Mutation(s): No). However, there is strong evidence that
4ZAU is in the active DFGin conformation, NOT DFGout/aCout:

1. **Osimertinib is a Type I covalent inhibitor** (third-generation TKI), not a Type II
   inhibitor. Type I inhibitors bind the DFGin active conformation.
2. **Literature describes 4ZAU as binding at the "active site"** -- multiple papers
   reference "osimertinib binding into the active site of EGFR (pdb 4ZAU)."
3. **WT EGFR kinase domains crystallize in the active conformation** due to asymmetric
   dimer crystal packing, as noted in the literature on EGFR crystal structures.
4. **The DFG motif in osimertinib-bound structures** shows interaction with Asp855 and
   Phe856 consistent with DFGin conformation.

The codebase at `src/statebind/processing/structures.py:202-214` classifies 4ZAU as:
```python
StructureRecord(
    pdb_id="4zau",
    state=ConformationalState.DFGOUT_ACOUT,  # <-- LIKELY INCORRECT
    mutations_present=[],  # Correct: 4ZAU is wild-type
    notes="WT EGFR classical inactive. Both DFG-out and aC-helix-out.",
)
```

If 4ZAU is actually in DFGin conformation, this is a fundamental error in the
conformational state atlas -- the representative structure for DFGout/aCout is not
actually in that conformation.

**Important caveat:** I could not access KLIFS annotations directly to confirm
the DFG classification. The codebase notes `provenance: ["pdb", "klifs"]` for this
entry, suggesting it may have been classified by KLIFS as DFGout. This requires
independent verification by inspecting the actual 3D coordinates (DFG-Asp/Phe distances,
aC-helix salt bridge distances). However, the circumstantial evidence -- Type I
inhibitor bound, active site binding, WT crystallization preference -- strongly
suggests misclassification.

### Finding 3C: 5D41 Is a L858R/T790M Mutant, Not Wild-Type

**PDB 5D41** is titled "EGFR kinase domain in complex with mutant selective allosteric
inhibitor" (2.31 A resolution). This structure contains the **L858R/T790M double
mutation** and is bound to both an allosteric inhibitor (57N) and ANP.

The codebase at `src/statebind/processing/structures.py:215-226` lists:
```python
StructureRecord(
    pdb_id="5d41",
    mutations_present=[],  # <-- INCORRECT: should be ["L858R", "T790M"]
    notes="Inactive EGFR conformation.",
)
```

### Finding 3D: 3IKU Is Not an EGFR Structure At All

The codebase uses PDB ID "3iku" as representative for DFGout/aCin state
(`src/statebind/structure/features.py:212`, `processing/structures.py:176`). However:

- **PDB 3IKU** is "Structural model of ParM filament in closed state from cryo-EM"
  -- a bacterial plasmid segregation protein from E. coli, NOT EGFR. 18 A resolution.
- **PDB 3IKA** is "Crystal Structure of EGFR 696-1022 T790M Mutant Covalently Binding
  to WZ4002" -- this is the likely intended structure, but it is a **T790M mutant**,
  not wild-type.

The codebase lists 3iku with `mutations_present=[]` and notes "WT EGFR with DFG-out
and aC-helix in." If the actual PDB ID used in docking is the related 3IKA, then:
1. The PDB ID is recorded incorrectly (3iku vs 3IKA)
2. The mutation status is incorrect (T790M, not wild-type)
3. This is a second instance of using mutant structures as wild-type representatives

### Finding 3E: No Wild-Type EGFR DFGout Structure Exists in PDB

After exhaustive searching of PDB, literature, and KLIFS references:

**Known EGFR DFGout structures (all mutant):**

| PDB ID | Mutations | DFG State | aC State | Resolution | Notes |
|--------|-----------|-----------|----------|------------|-------|
| 3W2R | T790M, L858R | DFGout | aCin | 2.05 A | Pyrimidine inhibitor |
| 3W2O | T790M, L858R | DFGout* | aCin* | ~2.0 A | TAK-285 |
| 3W2Q | T790M, L858R | DFGout* | aCin* | ~2.0 A | HKI-272 |
| 3IKA | T790M | DFGout** | Mixed** | 2.90 A | WZ4002 (Chain B) |
| 5HG5 | L858R, T790M, V948R | DFGout | ~aCin | ~2.0 A | PF-06459988 series |
| 5HG7 | L858R, T790M, V948R | DFGout | ~aCin | 1.85 A | PF-06459988 |
| 5HG8 | L858R, T790M, V948R | DFGout | ~aCin | ~2.0 A | PF-06459988 series |
| 5HG9 | L858R, T790M, V948R | DFGout | ~aCin | 2.15 A | PF-06459988 series |

*Conformation inferred from related structures in the same publication.
**3IKA contains an asymmetric dimer; Chain A is active (DFGin), Chain B is inactive.

**Known wild-type EGFR structures (all DFGin):**

| PDB ID | DFG State | aC State | Ligand | Notes |
|--------|-----------|----------|--------|-------|
| 1M17 | DFGin | aCin | Erlotinib | Active, used as StateBind baseline |
| 3VJO | DFGin | aCin | AMPPNP | Active, wild-type |
| 4I23 | DFGin | aCin | Dacomitinib | Active, wild-type |
| 4WKQ | DFGin | aCin | Gefitinib | Active, wild-type |
| 2GS6 | DFGin | aCin | ATP analog | Active, wild-type |
| 2GS7 | DFGin | aCout | AMPPNP | Src-like inactive, wild-type |
| 2ITY | DFGin | aCin | Iressa | Active, wild-type |
| 4ZAU | DFGin* | aCin* | Osimertinib | Wild-type, likely active |

*4ZAU classification needs verification by direct 3D inspection but evidence
strongly suggests DFGin/active.

**No experimentally solved wild-type EGFR crystal structure with confirmed DFGout
conformation was identified in PDB or literature.**

### Finding 3F: AlphaFold2 DFGout EGFR Predictions Are Limited

AlphaFold2 predictions for EGFR are heavily skewed toward DFGin conformations. While
significant DFGout population is observed in MD simulations of wild-type EGFR (the
transition pathway has been characterized by Shan et al., 2013), AF2 preferentially
generates DFGin structures. DFGmodel (Ung & Schlessinger, 2015) can generate DFGout
homology models for kinases but did not include EGFR in their published case studies.

### Impact Assessment and Recommendations

**Severity: PUBLICATION-BLOCKING**

The structural annotation errors are not minor metadata issues. They affect:

1. **The conformational state atlas itself** -- If 3 of 4 DFGout structures used are
   actually mutants (3W2R, 3IKA/3iku, 5D41), then the DFGout pocket descriptors
   (volume, shape, back-pocket accessibility) reflect mutant pockets, not wild-type.
2. **The docking validation** -- GNINA docking was performed against PDBQT files
   prepared from these structures. Docking against mutant receptors to evaluate
   wild-type state-specific design is methodologically unsound.
3. **The conformational state conditioning** -- If 4ZAU is actually DFGin (not
   DFGout/aCout), then the state labels used for VAE training may be incorrect for
   molecules assigned to the "DFGout/aCout" state.
4. **The entire DFGout narrative** -- The claim that the pipeline designs molecules
   for DFGout states is undermined if the DFGout representatives are mutant structures.

**Required Actions:**

1. **Immediate verification:** Inspect the 3D coordinates of 4ZAU, 3W2R, 3iku/3IKA,
   and 5D41 to confirm DFG conformations using established geometric criteria
   (DFG-Asp/Phe distance, aC-helix K745-E762 salt bridge distance).
2. **Correct PDB IDs:** If "3iku" was meant to be "3IKA," fix the ID and add T790M
   to mutations_present.
3. **Correct mutation annotations:** Add mutations to 3W2R (T790M, L858R), 5D41
   (L858R, T790M), and 3IKA if used (T790M).
4. **Verify 4ZAU classification:** If confirmed as DFGin, remove from DFGout/aCout
   and either find a genuine DFGout/aCout structure or acknowledge this state has
   no experimental WT structure.
5. **Disclose in the paper:** If mutant structures must be used (because no WT DFGout
   exists), this must be explicitly disclosed as a limitation with analysis of how
   the mutations affect pocket geometry.
6. **Consider DFGmodel homology models:** If no WT DFGout exists experimentally,
   generating a homology model using DFGmodel (Ung & Schlessinger, 2015) and
   disclosing this is more defensible than silently using mutant structures as
   wild-type.

---

## Updated Recommendations

### Changes to Publication Plan Based on Verification Findings

#### 1. Novelty Claim: Narrowly Scope but Publish with Confidence

The novelty is verified. The paper should claim:

> "We present the first systematic benchmark evaluating whether discrete
> conformational state-conditioning -- using DFG/aC kinase classifications as
> generation labels -- improves molecular design, assessed via retrospective
> enrichment."

This is defensible against all current competitors. However, the competitive
landscape is moving fast: DynamicFlow (ICLR 2025), Apo2Mol (AAAI 2025), and
FLOWR (2025) all handle flexibility differently. Time-to-publication is critical.

#### 2. Selectivity Claim: Restate with Proper Attribution

Replace "Type II Gini 0.76 vs Type I 0.58" with:

> "Large-scale kinase profiling consistently demonstrates that Type II inhibitors
> are more selective than Type I inhibitors (p < 10^-4, Davis et al., 2011; Muller
> et al., 2015), with Gini coefficients typically ranging 0.64-0.80 for Type II
> vs 0.49-0.74 for Type I (Muller et al., 2015, Table 4)."

This is more accurate and citable.

#### 3. Structural Atlas: Fix Before ANY New Experiments

The structural data integrity issue is the most critical finding of this
verification round. No new experiments (multi-kinase extension, ablation studies,
REINVENT comparison) should proceed until the conformational state atlas is
verified and corrected. The impact cascades through:
- Docking validation scores
- VAE state conditioning labels
- Pocket descriptors (volume, shape features)
- The conformational selection narrative

This should be elevated to **Tier 0, Item 0** in the implementation plan, ahead
of even the osimertinib leakage fix.

#### 4. Timeline Impact

If structural atlas corrections require re-running docking or re-training the VAE
with corrected state labels, this could add 2-4 weeks to the timeline. This must
be assessed immediately.

---

## References

1. Lu, W. et al. "DynamicBind: predicting ligand-specific protein-ligand complex
   structure with a deep equivariant generative model." Nat. Commun. 15, 1071 (2024).

2. "Integrating Protein Dynamics into Structure-Based Drug Design via Full-Atom
   Stochastic Flows." ICLR 2025. arXiv:2503.03989.

3. "Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion Models."
   AAAI 2025. arXiv:2511.14559.

4. Karami et al. "FLOWR -- Flow Matching for Structure-Aware De Novo, Interaction-
   and Fragment-Based Ligand Generation." arXiv:2504.10564 (2025).

5. Anishchenko, I. et al. "Modeling protein-small molecule conformational ensembles
   with PLACER." PNAS 121, e2427161122 (2025).

6. "Conformation-specific Design: a New Benchmark and Algorithm with Application to
   Engineer a Constitutively Active Map Kinase." bioRxiv 2025.04.23.650138.

7. Graczyk, P.P. "Gini coefficient: a new way to express selectivity of kinase
   inhibitors against a family of kinases." J. Med. Chem. 50, 5773-5779 (2007).

8. Davis, M.I. et al. "Comprehensive analysis of kinase inhibitor selectivity."
   Nat. Biotechnol. 29, 1046-1051 (2011).

9. Muller, S. et al. "Conformational Analysis of the DFG-Out Kinase Motif and
   Biochemical Profiling of Structurally Validated Type II Inhibitors." J. Med. Chem.
   58, 1610-1629 (2015). PMC4326797.

10. Uitdehaag, J.C.M. & Zaman, G.J.R. "A guide to picking the most selective kinase
    inhibitor tool compounds." Br. J. Pharmacol. 166, 858-876 (2012).

11. Muller, S., Chaikuad, A., Gray, N.S. & Knapp, S. "The ins and outs of selective
    kinase inhibitor development." Nat. Chem. Biol. 11, 818-821 (2015).

12. Sogabe, S. et al. "Structure-Based Approach for the Discovery of Pyrrolo[3,2-d]-
    pyrimidine-Based EGFR T790M/L858R Mutant Inhibitors." J. Med. Chem. 56, 7924-7940
    (2013). PDB: 3W2R.

13. Yosaatmadja, Y. et al. "Binding mode of the breakthrough inhibitor AZD9291 to
    epidermal growth factor receptor revealed." J. Struct. Biol. 192, 539-544 (2015).
    PDB: 4ZAU.

14. Cheng, H. et al. "Discovery of PF-06459988, a Potent, WT Sparing, Irreversible
    Inhibitor of T790M-Containing EGFR Mutants." J. Med. Chem. 59, 2005-2024 (2016).
    PDBs: 5HG5, 5HG7, 5HG8, 5HG9.

15. Yun, C.H. et al. "The T790M mutation in EGFR kinase causes drug resistance by
    increasing the affinity for ATP." PNAS 105, 2070-2075 (2008). PDB: 3IKA.

16. Ung, P.M.U. & Schlessinger, A. "DFGmodel: Predicting Protein Kinase Structures
    in Inactive States for Structure-Based Discovery of Type-II Inhibitors." ACS Chem.
    Biol. 10, 269-278 (2015).

17. Modi, V. & Bhatt, R. "Pockets as structural descriptors of EGFR kinase
    conformations." PLOS ONE 12, e0189147 (2017).

18. Ung, P.M.U. et al. "Redefining the Protein Kinase Conformational Space with
    Machine Learning." Cell Chem. Biol. 25, 916-924 (2018).

19. Sutto, L. & Gervasio, F.L. "Effects of oncogenic mutations on the conformational
    free-energy landscape of EGFR kinase." PNAS 110, 10616-10621 (2013).

20. Shan, Y. et al. "Transitions to catalytically inactive conformations in EGFR
    kinase." PNAS 110, 7270-7275 (2013).

21. Kooistra, A.J. et al. "KLIFS: an overhaul after the first 5 years of supporting
    kinase research." Nucleic Acids Res. 49, D562-D569 (2021).

22. Brogi, S. et al. "Structural Insight and Development of EGFR Tyrosine Kinase
    Inhibitors." Molecules 27, 819 (2022).

23. Sato, T. et al. "Structure-based classification predicts drug response in EGFR-
    mutant NSCLC." Nature 598, 122-127 (2021).
