---
agent: Senior Computational Chemist
round: 1
date: 2026-04-08
type: research-note
topic: Physics-based computational methods for strengthening StateBind validation and scoring
---

# Research Note: Physics-Based Validation and Scoring -- What StateBind Is Missing and What Can Be Added

## Summary

StateBind's scoring pipeline (GNINA docking + MPNN proxy + weighted sum) leaves
substantial physics on the table. Published benchmarks establish a clear accuracy
hierarchy: FEP (RMSE ~0.7--1.1 kcal/mol for RBFE) >> MM-GBSA (RMSE ~1.5--3.0
kcal/mol, highly variable) >> empirical docking (RMSE ~2--3 kcal/mol). GNINA's CNN
rescoring improves pose prediction (73% vs 58% Top1 over Vina) but not
thermodynamic accuracy. This note surveys six areas where physics-based methods
could strengthen StateBind's scientific credibility and publication case: (1) FEP
for rigorous computational validation, (2) MD-derived pocket ensembles, (3) water
thermodynamics as a state discriminator, (4) ensemble docking, (5) physics-ML hybrid
scoring, and (6) accuracy benchmarking of the current pipeline. I identify specific
open-source tools, estimate compute costs on Yale Bouchet H200 GPUs, and frame each
opportunity in terms of publication impact.

## Research Questions

1. Can FEP on StateBind's top 10--20 candidates serve as rigorous computational
   validation without wet-lab data? What accuracy, cost, and tooling are available?
2. What do published MD studies of EGFR conformational transitions reveal about
   timescales, sampling requirements, and feasibility of generating pocket ensembles?
3. How do water networks differ between EGFR conformational states, and can water
   thermodynamics serve as an independent state discriminator?
4. How much does ensemble docking (multiple structures per state) improve accuracy
   over single-structure docking, and what is the compute overhead?
5. What hybrid physics-ML scoring approaches exist that could replace or augment
   GNINA's scoring function with better thermodynamic grounding?
6. How does GNINA's scoring accuracy compare quantitatively to FEP and MM-GBSA
   on kinase systems?

## Methods

### Sources Consulted

- PubMed, Google Scholar, ChemRxiv, bioRxiv, arXiv for peer-reviewed literature
- OpenFE documentation and benchmark repository (openfree.energy)
- GNINA GitHub and published benchmarks (GNINA 1.0, GNINA 1.3)
- SSTMap documentation and GitHub repository
- AmberTools GIST documentation and tutorials
- OpenMM 8 documentation and benchmark data
- KLIFS kinase structural database
- NAMD GPU FEP documentation
- Schrodinger FEP+ published validation studies

### Search Strategy

Over 20 targeted web searches were conducted covering: FEP benchmarks on kinase
systems, EGFR MD simulations, GNINA accuracy, WaterMap/GIST kinase water analysis,
ensemble docking methods, ML force fields (MACE, ANI), semi-empirical QM scoring
(SQM2.20, GFN2-xTB), delta-ML approaches, SAMPL challenge results, AlphaFold2
multi-state kinase modeling, and OpenFE/pmx open-source FEP tooling. Specific papers
were fetched and analyzed for quantitative accuracy metrics.

## Findings

### Finding 1: The Accuracy Hierarchy Is Well Established -- GNINA Sits Near the Bottom

Published benchmarks across kinase systems demonstrate a consistent accuracy hierarchy
for binding affinity prediction:

| Method | Typical RMSE (kcal/mol) | Correlation (R^2) | Source |
|--------|------------------------|-------------------|--------|
| Relative FEP (RBFE) | 0.68--1.15 | 0.5--0.8 | OpenFE benchmark (Gapsys et al., 2025); KLK6 study |
| Absolute FEP (ABFE) | 1.0--2.0 | variable | FEP-SPell-ABFE, Felis toolkit benchmarks |
| SQM2.20 (semi-empirical QM) | ~1.5 equivalent | 0.69 (PL-REX) | Pecina et al., 2024, Nat Commun |
| MM-GBSA | 1.5--3.0 | 0.0--0.9 (system-dependent) | Hou et al., 2011; Genheden & Ryde, 2015 |
| Empirical docking (GNINA) | 2.0--3.0 | 0.3--0.5 | GNINA 1.0/1.3 benchmarks |
| Empirical docking (Vina) | 2.0--3.0+ | 0.2--0.4 | CASF-2016 benchmarks |

GNINA 1.0 achieves a docking pose success rate (Top1) of 73% in redocking (vs 58%
for Vina) and 37% in cross-docking (vs 27% for Vina) (McNutt et al., 2021). GNINA
1.3 improves virtual screening AUC to 0.78 median (vs 0.75 for GNINA 1.0) across 102
DUD-E targets (Sunseri & Koes, 2025). However, these are POSE prediction and RANKING
metrics -- they do NOT measure thermodynamic accuracy.

GNINA's scoring function does not account for: explicit water, protein flexibility,
entropy, long-range electrostatics, or solvation free energy. The CNN scoring function
was trained on PDBbind crystal complexes and inherits their biases. For a publication
claiming to identify superior drug candidates, this is a significant vulnerability.

**Key data points:**
- GNINA 1.3 virtual screening median AUC: 0.78 on DUD-E (Sunseri & Koes, 2025)
- GNINA 1.0 redocking Top1: 73% (McNutt et al., 2021)
- Cross-docking Top1: 37% (GNINA 1.0), 40% (GNINA 1.3)
- Average docking time: 23 seconds per complex in GNINA 1.3 CPU mode

**Relevance to StateBind:** StateBind uses GNINA v1.1 as Tier 0 scoring, normalized
via sigmoid(-vina_score/3). This maps a physically meaningless scale to [0,1]. The
delta between known binders (-7.32 kcal/mol) and non-binders (-4.16 kcal/mol) is only
3.16 kcal/mol -- well within the noise floor of empirical docking. FEP on even a
subset of candidates would provide substantially more rigorous differentiation.

---

### Finding 2: Open-Source FEP Is Now Production-Ready for Kinase Systems

The OpenFE consortium (15 pharmaceutical companies) published the largest collaborative
FEP benchmark to date in 2025. Key results:

**Public dataset (59 targets, 876 ligands, >7,000 calculations):**
- Weighted RMSE: 1.73 kcal/mol [1.53, 1.96 CI]
- 10 of 59 systems achieved sub-kcal/mol accuracy
- These are "out-of-the-box" results with default settings

**Private dataset (37 targets, 864 ligands, real pharma campaigns):**
- Weighted RMSE: 2.44 kcal/mol [1.94, 3.06 CI]
- 2 of 37 systems sub-kcal/mol
- Reflects real-world complexity (scaffold changes, charge modifications)

For comparison, Schrodinger's FEP+ achieves RMSE < 1 kcal/mol on well-behaved kinase
systems, with prospective validation showing 78% of predicted tight binders confirmed
and 69% of predictions within 1 log unit (Wang et al., 2015; Schrodinger case studies).

On the specific KLK6 kinase benchmark, RBFE achieved MUE = 0.53 kcal/mol and
RMSE = 0.68 kcal/mol, substantially outperforming MM-GBSA on the same system
(Menke et al., 2023).

**Open-source tools now available:**
- **OpenFE** (MIT license): Full RBFE/ABFE workflow, OpenMM-based, Python API
- **pmx** (LGPL v3): GROMACS-based alchemical FEP, tutorials for kinase systems (JNK1)
- **FEP-SPell-ABFE** (MIT license): Automated ABFE workflow, RMSE = 0.27 kcal/mol on
  benchmarks (after protein reorganization correction)
- **BAT.py**: Automated ABFE/RBFE with AMBER and OpenMM
- **PyAutoFEP**: GROMACS RBFE with enhanced sampling integration

**Compute costs:**
- OpenFE v1.7: ~3 hours wall time per pairwise RBFE transformation on a single GPU
  (down from ~6 hours in v1.0, using dodecahedral box and optimized replica exchange)
- For 20 candidates in a perturbation network: approximately 40--60 transformations
  needed, or 120--180 GPU-hours total on H200
- This is entirely feasible on Bouchet: 1 H200 node (8 GPUs) could complete the
  entire campaign in under 24 hours

**Key data points:**
- OpenFE public benchmark RMSE: 1.73 kcal/mol (Gapsys et al., 2025)
- FEP+ kinase RMSE: < 1.0 kcal/mol on well-behaved systems (Wang et al., 2015)
- OpenFE v1.7 wall time per transformation: ~3 hours/GPU
- 20-compound RBFE campaign: ~120--180 GPU-hours

**Relevance to StateBind:** Running OpenFE RBFE on StateBind's top 20 candidates per
conformational state would provide the most rigorous computational validation possible
without wet-lab data. This directly addresses the #1 reviewer concern ("where is the
experimental validation?") by replacing it with gold-standard computational validation.
FEP results could demonstrate that top-ranked state-aware candidates genuinely bind
more tightly than static candidates -- or reveal that the scoring function is misleading.

---

### Finding 3: EGFR Conformational Transitions Are Well-Studied by MD but Require Enhanced Sampling

Multiple groups have simulated EGFR kinase dynamics. The literature establishes:

**Timescales for EGFR conformational transitions:**
- DFG flip: microseconds to milliseconds (Sutto & Gervasio, 2013)
- aC helix rotation: hundreds of nanoseconds to microseconds
- A-loop unfolding: hundreds of nanoseconds
- Standard 100 ns MD cannot sample these transitions

**Key EGFR MD studies:**

(a) Sutto & Gervasio (2013, PNAS): Used parallel tempering + metadynamics on EGFR
kinase domain. Found that L858R populates the active state with a 2--4 kcal/mol
thermodynamic penalty vs inactive. T790M lowers active-state free energy by ~5
kcal/mol. DFG flip barrier: ~2 kcal/mol for T790M-L858R double mutant.

(b) Yang et al. (2014, JCTC): Combined multiple 100 ns MD simulations with Bayesian
clustering to map conformational transition pathways. Found that partial unfolding
of the aC helix accompanies the transition between active and inactive forms and
facilitates DFG-flip. Disruption of the Lys745-Glu762 salt bridge is critical.

(c) Sato et al. (2021, npj Precision Oncology): Microsecond-timescale MD of EGFR minor
mutations predicts structural flexibility of the kinase core that reflects inhibitor
sensitivity. Direct evidence that microsecond MD captures pharmacologically relevant
dynamics.

(d) Zhang et al. (2024, JCIM): String method + Markov state model analysis of EGFR
dimer activation. Found that A-loop unfolding precedes C-helix rearrangement during
kinase activation.

**Enhanced sampling tools for Bouchet:**
- OpenMM 8 with metadynamics (native + PLUMED integration)
- PySAGES for advanced enhanced sampling on GPU
- Gaussian accelerated MD (GaMD) in OpenMM

**Performance on H200 GPUs:**
- OpenMM achieves >500 ns/day on H200 for ~44K atom systems (T4 lysozyme benchmark)
- EGFR kinase domain in explicit solvent: ~60--80K atoms, estimate ~200--300 ns/day
- 1 microsecond simulation: ~3--5 days wall time per replica on a single H200 GPU
- With 4 replicas per state x 4 states = 16 replicas: ~2 weeks on 2 H200 nodes

**Key data points:**
- DFG flip free energy barrier: ~2--5 kcal/mol depending on mutation (Sutto & Gervasio, 2013)
- Microsecond MD captures pharmacologically relevant dynamics (Sato et al., 2021)
- OpenMM on H200: ~200--300 ns/day for EGFR-sized systems (estimated)
- Pocket ensemble generation: ~2 weeks on 2 H200 nodes for all 4 states

**Relevance to StateBind:** StateBind uses 1 crystal structure per conformational
state. This is a snapshot, not the ensemble. Running 1+ microsecond enhanced sampling
MD per state would: (a) generate pocket conformational ensembles for ensemble docking,
(b) provide free energy differences between states that could replace the ad hoc
geometric decay function, (c) reveal whether the 4 discrete states are truly distinct
or part of a continuum, and (d) provide publishable MD-derived evidence for the
state-aware hypothesis.

---

### Finding 4: Water Thermodynamics Differentiates Conformational States -- A Key Missing Discriminator

Water thermodynamics is arguably the most important physics missing from StateBind's
scoring. The literature demonstrates:

**WaterMap on SRC kinase (Robinson et al., 2014):**
- Identified 36 hydration sites in the ATP pocket, 21 with positive free energy
  (unfavorable, ΔG > 1.0 kcal/mol)
- Water displacement energetics in the selectivity pocket: ΔG = 2.6--6.6 kcal/mol
  per displaced water
- MM-GBSA (R^2 = 0.68) outperformed WaterMap (R^2 = 0.55) for quantitative potency
  ranking, but WaterMap provided qualitative physical insight

**General kinase water networks:**
- The DFG-out allosteric pocket is hydrophobic; water displacement is a major
  thermodynamic driving force for type II inhibitor binding
- The ATP pocket contains 2--3 conserved water molecules mediating hinge interactions
- Different conformational states have different water networks -- this is directly
  relevant to state-aware design
- Extended inhibitor structures accessing deeper lipophilic pockets gain potency
  primarily through water displacement

**AutoDock-GIST (Uehara & Tanaka, 2016):**
- Incorporated GIST water thermodynamics into AutoDock4 scoring
- Improved both scoring accuracy and docking success rate on Factor Xa
- R^2 improved from ~0.3 to 0.41--0.50 with water correction
- Demonstrates that water terms can be added to existing docking scores

**Open-source tools:**
- **SSTMap** (open-source): Computes GIST and HSA water thermodynamics from MD
  trajectories. Supports OpenMM, GROMACS, Amber, NAMD output.
- **GIST in cpptraj** (AmberTools, free): Grid-based solvation analysis. MPI-parallel
  version available (v6.22.0+). Tutorial for Factor Xa available.
- **3D-RISM in AmberTools**: Analytical solvation theory, faster than MD-based GIST
  but less accurate for complex pockets.

**Compute cost for GIST analysis:**
- Requires short (5--10 ns) MD simulations with restrained protein backbone
- For 4 EGFR states: 4 x 10 ns = 40 ns total, ~1 day on a single H200 GPU
- GIST post-processing: minutes to hours per system
- Total compute: < 2 GPU-days for complete water thermodynamic maps of all 4 states

**Key data points:**
- Water displacement free energy in kinase selectivity pocket: 2.6--6.6 kcal/mol
  per water (Robinson et al., 2014)
- 21 of 36 ATP pocket hydration sites are thermodynamically unfavorable (SRC kinase)
- GIST water correction improves docking R^2 from ~0.3 to 0.41--0.50
- Compute cost for all 4 states: < 2 GPU-days

**Relevance to StateBind:** Water thermodynamic maps would provide the strongest
physics-based evidence that the 4 conformational states present genuinely different
binding environments. If water networks differ substantially between DFGin/aCin and
DFGout/aCout, this validates the entire state-aware hypothesis on thermodynamic
grounds. Additionally, a GIST-derived water displacement score could replace or
supplement the current solvation-blind scoring. This analysis is cheap, fast, and
would produce a publication-worthy figure showing differential water thermodynamics
across EGFR states. It also builds on -- and significantly extends -- the deferred
Vision System idea 011 (Water Thermodynamics) by connecting water analysis directly
to the state discrimination hypothesis.

---

### Finding 5: Ensemble Docking Improves Accuracy Over Single-Structure Docking

StateBind uses 1 crystal structure per conformational state. Published evidence shows
that ensemble docking with multiple structures consistently outperforms single-structure
approaches:

**Kinase-specific ensemble docking results:**

(a) Rueda et al. (2014, JCIM): Ensemble docking protocol for ALK, CDK2, and VEGFR2
kinases. Ensembles of 2--3 structures outperformed any single structure for virtual
screening. Naive Bayesian classification of ensemble docking scores improved
enrichment factors.

(b) Clyde et al. (2022, JCIM): Ensemble docking + ML classifiers (logistic regression,
gradient boosting). ML-enhanced ensemble docking improved AUC by ~0.15 over naive
Bayesian consensus and single-structure docking. Performance did NOT decrease with
more ensemble members.

(c) Vijayan et al. (2024, Scientific Reports): AlphaFold2 multi-state modeling for
kinase ensemble docking. MSM-TT models achieved average RMSD of 2.15 A vs 2.74 A
for standard AF2. Ensemble virtual screening EF1% of 8.2 vs 6.6 for single AF2
model across 25 kinases.

**Quantitative improvements:**
- Single structure mean ROC area: 0.81 +/- 0.11 (DUD-E)
- 5-member ensemble mean ROC area: 0.84 +/- 0.09 (same benchmark)
- Ensembles of 3 receptors: ~40% of known actives outrank all decoys
- More diverse hit scaffolds identified with ensembles

**Sources of ensemble structures for StateBind:**
1. KLIFS database: EGFR has 100+ crystal structures across conformational states
   (107 BLAminus chains, 79 BLBplus chains per Modi & Bhatt, 2019)
2. AlphaFold2 multi-state modeling (Vijayan et al., 2024)
3. MD-derived ensembles from enhanced sampling (see Finding 3)

**Compute cost:**
- If 5 structures per state: 4 states x 5 structures = 20 docking runs per candidate
- GNINA on GPU: ~23 seconds per complex (GNINA 1.3)
- 461 candidates x 20 structures = 9,220 dockings = ~59 GPU-hours
- Entirely feasible on Bouchet

**Key data points:**
- AUC improvement from ensemble: 0.81 -> 0.84 (3.7% relative improvement)
- EF1% improvement with AF2 MSM: 6.6 -> 8.2 (24% relative improvement)
- RMSD improvement with AF2 MSM: 2.74 A -> 2.15 A
- Compute cost for full ensemble docking: ~59 GPU-hours

**Relevance to StateBind:** Moving from 1 to 5 structures per state would: (a) capture
pocket flexibility within each state, (b) reduce the chance that a single crystal
artifact dominates the score, (c) produce more robust rankings, and (d) address the
reviewer critique about "4 static crystal structures." The compute cost is modest
(~3 days on a single GPU) and the structural data already exists in KLIFS.

---

### Finding 6: FEP on Top Candidates Would Be the Strongest Possible Computational Validation

Without wet-lab data, FEP represents the highest tier of computational evidence.
Published prospective success rates:

**Schrodinger FEP+ prospective results:**
- 78% of predicted tight binders (< 100 nM) confirmed as true positives
- 92% of predicted weak binders (> 100 nM) confirmed as true negatives
- 69% of prospective predictions within 1 log unit of experiment
- Only 6% with > 2 log unit error
- Kinase selectivity optimization: selectivity window improved from 40% to 90% of
  kinases with > 100x selectivity (Schrodinger case studies)

**FEP accuracy on kinase systems specifically:**
- Abl kinase RBFE with Amber99sb*-ILDN: RMSE = 0.91 kcal/mol (Aldeghi et al., 2019)
- Abl kinase RBFE with CHARMM22*: RMSE = 1.03 kcal/mol
- Abl kinase with Rosetta REF15: RMSE = 0.72 kcal/mol (best for mutations)
- KLK6 kinase RBFE: MUE = 0.53, RMSE = 0.68 kcal/mol (Menke et al., 2023)
- TYK2 benchmark (OpenFE standard): consistently sub-kcal/mol

**ABFE for virtual screening hits:**
- FEP-SPell-ABFE: RMSE = 0.27 kcal/mol after protein reorganization correction
  (but this was on a specific well-behaved benchmark)
- Felis toolkit: ABFE performance comparable to RBFE across 43 targets, 859 ligands
- Kinase-specific ABFE (TYK2, P38, JNK1, CDK2): optimized protocols reduce RMSE
  by up to 0.23 kcal/mol vs unoptimized

**A specific FEP validation protocol for StateBind:**
1. Select top 20 candidates from state-aware pipeline + top 10 from static baseline
2. Run RBFE within each chemical series using OpenFE (MIT license)
3. Run ABFE for cross-series comparison using FEP-SPell-ABFE
4. Compare FEP-derived rankings to GNINA-derived rankings
5. Compute correlation between FEP binding free energy and unified score

**Estimated compute:**
- RBFE: ~3 hours per transformation x 60 transformations = 180 GPU-hours
- ABFE: ~20--40 hours per compound x 30 compounds = 600--1200 GPU-hours
- TOTAL: ~800--1400 GPU-hours = 4--7 days on a single 8-GPU H200 node
- With Bouchet priority queue and 2 nodes: 2--4 days

**Key data points:**
- FEP prospective success rate: 78% true positive, 92% true negative
- Kinase RBFE RMSE: 0.68--1.03 kcal/mol
- Total compute for StateBind FEP validation: ~800--1400 GPU-hours
- Wall time on 2 H200 nodes: ~2--4 days

**Relevance to StateBind:** An FEP validation study would be the strongest possible
response to the #1 reviewer concern. If FEP confirms that top state-aware candidates
have genuinely lower binding free energies than static candidates, this provides
physics-grounded evidence for the 10x enrichment result. If FEP disagrees with GNINA
rankings, that is also valuable -- it reveals scoring function limitations and
motivates improvement. Either outcome is publishable.

---

### Finding 7: SQM2.20 -- DFT-Quality Scoring in Minutes, Not Hours

A semi-empirical quantum mechanical scoring function (SQM2.20) achieves correlation
with experiment rivaling DFT while running in ~20 minutes per complex (Pecina et al.,
2024, Nature Communications):

- Average R^2 = 0.69 across 10 diverse protein targets (PL-REX benchmark)
- Per-target R^2 range: 0.56 (JAK1) to 0.81
- 4 orders of magnitude faster than DFT
- Substantially outperforms conventional scoring (GlideSP, Vina, PLANTS: R^2 ~ 0.40)
- Uses MOPAC with MOZYME linear-scaling algorithm for systems with thousands of atoms

**Comparison to StateBind's methods:**
- SQM2.20 R^2 = 0.69 vs MPNN R^2 = 0.69 (coincidentally identical)
- But SQM2.20 is physics-based, not learned, so it generalizes to novel chemotypes
- 20 minutes per complex is expensive for 461 candidates x 4 states (~2,564 hours)
  but feasible for top 50 candidates (~67 hours)

**Key data point:** SQM2.20 could serve as a bridge between fast docking and slow FEP,
providing physics-based rescoring of top candidates with minimal setup.

**Relevance to StateBind:** SQM2.20 rescoring of the top 50 state-aware candidates
would add a physics-based validation layer without the complexity of full FEP.
At ~3 days of CPU time (parallelizable), this is a low-cost, high-impact addition.

---

### Finding 8: Machine-Learned Force Fields Are Not Yet Ready for Binding Free Energy

MACE-OFF23 and ANI-2x represent the state of the art in ML force fields for organic
molecules, but they have significant limitations for protein-ligand binding:

**MACE-OFF23 (Kovacs et al., 2024, JACS):**
- Trained on high-level QM data for organic molecules
- Accurate dihedral scans, crystal properties, liquid properties
- Can simulate small proteins in explicit water (crambin, 18K atoms)
- Better accuracy than ANI-2x on COMP6 benchmark
- Limitation: trained on organic molecules only; no ions, no metals, no cofactors

**ANI-2x (OpenMM 8 integration):**
- 56 ns/day with NNPOps on RTX 4080 for CDK8 system (134K atoms)
- 105 ns/day with single model (no ensemble)
- Supports only 7 elements (H, C, N, O, F, S, Cl)
- Cannot handle charged molecules
- 5.7x speedup from NNPOps GPU optimization

**Limitations for binding free energy:**
- Neither MACE-OFF nor ANI-2x cover the full periodic table needed for drug molecules
  (many kinase inhibitors contain fluorine, chlorine, bromine, sulfur)
- Protein-ligand binding energy is not a primary training target
- Long-range electrostatics not well captured by short-range ML potentials
- No published binding free energy benchmarks on kinase systems

**GFN2-xTB as alternative:**
- Semi-empirical QM, not ML, but very fast
- Mean error ~3 kcal/mol for large complexes vs experiment
- Kendall's tau = 0.63 for conformer ranking (Kong et al., 2025)
- Combined with CREST for conformational sampling
- Used in de novo design workflows (RSC Advances, 2024)

**Key data points:**
- ANI-2x on CDK8: 56--105 ns/day (GPU, OpenMM 8)
- MACE-OFF accuracy: better than ANI-2x on drug-like organic molecules
- GFN2-xTB binding free energy error: ~3 kcal/mol
- Neither ML potential is production-ready for kinase binding FE

**Relevance to StateBind:** ML force fields are not yet a replacement for classical
force fields or FEP for binding affinity. However, MACE-OFF could be used for
ligand strain energy calculation (intramolecular term only), and ANI-2x in OpenMM 8
could accelerate conformational sampling. These are incremental additions, not
transformative. GFN2-xTB is more immediately useful as a fast QM filter for
geometry optimization and strain energy assessment.

---

### Finding 9: Delta-ML Approaches Bridge the Physics-ML Gap

The delta-ML paradigm uses machine learning to correct physics-based scores, combining
the generalizability of physics with the accuracy of ML:

**Published delta-ML results:**
- Boyles et al. (2022, JCIM): Delta-ML corrections to Vina scoring using XGBoost.
  Used Lin_F9 as physics baseline + ML correction. Improved scoring, ranking, AND
  screening simultaneously -- addressing the known failure mode where ML scoring
  functions improve scoring power but hurt docking/screening power.
- Hybrid MM-GBSA + ML (GXLE): ML trained on MM-GBSA energy decomposition terms.
  Outperforms MM-GBSA without entropy correction.
- "Narrowing the gap between ML and FEP" (Comm Chem, 2025): ML model (AEV-PLIG)
  benchmarked against FEP calculations. Augmented training data from FEP results
  improved ML model accuracy to approach FEP-level performance.

**The key insight:** Rather than replacing physics with ML or ML with physics, the
delta-ML approach:
1. Starts with a physics score (Vina, MM-GBSA, or GNINA)
2. Computes ML correction: Delta = ML(features) - physics_score
3. Final score = physics_score + Delta
4. The ML only needs to learn the RESIDUAL, which is smaller and more learnable

**Relevance to StateBind:** StateBind already has both physics (GNINA) and ML (MPNN)
scores. A delta-ML approach that learns the correction from GNINA to FEP (using FEP
results as training targets for the top candidates) could extend physics-quality
predictions to the entire candidate set without running FEP on every molecule.

---

### Finding 10: AlphaFold2 Multi-State Modeling Enables Ensemble Generation Without MD

Recent work demonstrates that AlphaFold2 can generate multiple conformational states
of kinases without running MD (Vijayan et al., 2024):

- Multi-state modeling (MSM) with state-specific templates produces accurate
  conformational ensembles
- 25 kinases benchmarked on DUD-E
- Cross-docking RMSD: MSM-TT 2.15 A vs standard AF2 2.74 A vs AF3 3.68 A
- AUC: 0.639--0.664 (approaching crystal structure performance at 0.664)
- AF2RAVE-Glide: Combines AF2 with enhanced sampling MD + induced fit docking for
  metastable kinase conformations

**AlphaFold2 subsampled conformational distributions (Del Alamo et al., 2024):**
- Subsampling MSAs enables direct prediction of relative state populations
- >80% accuracy for predicting changes in conformational populations
- Applicable to kinases across the kinome

**Relevance to StateBind:** AF2 multi-state modeling could generate 5--10 structures
per EGFR conformational state without any MD simulation. This provides immediate
ensemble docking capability. Combined with MD validation of the AF2-generated
ensembles, this is a fast path to addressing the "4 static structures" limitation.

---

### Finding 11: SAMPL Challenges Reveal the State of the Art for Blind Binding Prediction

The SAMPL9 host-guest challenge (2024) provides a reality check on blind prediction
accuracy:

- Best RMSE for WP6 macrocycle: 1.70 kcal/mol (docking-based)
- Best RMSE for cyclodextrin: 1.86 kcal/mol (ATM alchemical method)
- ML methods: RMSE 2.04 kcal/mol on WP6 (descriptors-based)
- SAMPL8: AMOEBA polarizable FEP achieved RMSE < 1 kcal/mol on cavitand

These are HOST-GUEST systems (simpler than protein-ligand). For protein-ligand
binding, current blind prediction accuracy is WORSE. This underscores that no single
method achieves chemical accuracy, and multi-method validation is essential.

**Key data point:** Best blind prediction RMSE on host-guest: ~1.0--1.7 kcal/mol.
Protein-ligand will be worse.

**Relevance to StateBind:** Citing SAMPL results contextualizes StateBind's scoring
accuracy expectations. Reviewers should not expect FEP-level accuracy from docking.
The publication should explicitly acknowledge the accuracy hierarchy and use FEP as
a validation tier, not as the primary scoring method.

---

### Finding 12: GPU-Accelerated FEP in NAMD and GROMACS Makes Large-Scale FEP Feasible

GPU acceleration has transformed FEP from a specialty calculation to a routine tool:

**NAMD 3.0 GPU FEP:**
- 4--12x speedup over CPU with traditional GPU code
- Up to 30x speedup with single-GPU optimized code path
- Tested on 98K atom systems in explicit solvent

**GROMACS GPU FEP (2025):**
- Acceleration of FEP calculations on GPUs reported in ACS Omega (2025)
- GROMACS is the backend for pmx FEP workflows

**OpenMM 8 for FEP:**
- Backend for OpenFE
- ML potential support (ANI-2x at 56--105 ns/day)
- Metadynamics, simulated tempering, replica exchange built in
- Python API for custom workflows

**Compute scaling for StateBind FEP campaign:**

| Scenario | Compounds | Method | GPU-Hours | Wall Time (2x H200 nodes) |
|----------|-----------|--------|-----------|--------------------------|
| RBFE top-20 state-aware | 20 | OpenFE RBFE | ~180 | ~12 hours |
| ABFE top-20 + top-10 static | 30 | FEP-SPell-ABFE | ~600--1200 | 2--4 days |
| Full validation (RBFE+ABFE) | 30 | Combined | ~800--1400 | 2--4 days |
| Per-state FEP (4 states x 20) | 80 | RBFE | ~720 | ~2 days |

**Key data point:** A full FEP validation campaign for StateBind is feasible in under
1 week on 2 H200 nodes -- well within Bouchet capacity.

**Relevance to StateBind:** The compute barrier for FEP has fallen dramatically. What
was once a months-long effort is now a days-long campaign. This makes FEP validation
not just possible but practically obligatory for a competitive publication.

---

### Finding 13: The Physics Case for Water State-Discrimination Is Strongest for DFG-out

Published structural and thermodynamic data strongly supports using water analysis
to differentiate EGFR conformational states:

**DFG-out allosteric pocket:**
- Created when DFG flips out; large hydrophobic extension of the ATP pocket
- Type II inhibitors gain potency primarily through water displacement in this pocket
- Water displacement energetics: 2.6--6.6 kcal/mol per displaced water
- This pocket does NOT exist in DFGin states

**ATP hinge region:**
- 2--3 conserved waters mediate hinge interactions across all states
- These waters are less state-dependent but critical for all inhibitor types

**aC-out pocket:**
- aC helix rotation creates a distinct pocket geometry
- Water networks rearrange when aC moves out
- A water-mediated allosteric network links C-helix to the active site (Aurora kinase
  analog; Cyphers et al., 2017)

**Prediction:** GIST analysis of the 4 EGFR states would show:
- DFGin/aCin: smallest pocket, fewest displaceable waters, most conserved network
- DFGout/aCout: largest pocket, most displaceable high-energy waters
- DFGin/aCout and DFGout/aCin: intermediate water network complexity
- This gradient would mirror StateBind's pocket volume gradient (450--850 cubic A)

**Relevance to StateBind:** Water thermodynamic analysis would be the cheapest and
most informative single experiment to validate the state-aware hypothesis. It would
produce direct physical evidence that different conformational states present
different thermodynamic binding environments.

---

### Finding 14: The Scoring Gap Between GNINA and FEP Is Quantifiable

By combining data across findings, the scoring accuracy gap can be precisely stated:

| StateBind Current | Estimated RMSE | Source |
|-------------------|---------------|--------|
| GNINA v1.1 Vina score | ~2.5--3.0 kcal/mol | Empirical docking literature |
| GNINA CNN affinity | ~2.0--2.5 kcal/mol | PDBbind trained CNN |
| MPNN pIC50 proxy | RMSE = 0.72 pIC50 (~1.0 kcal/mol equiv.) | StateBind trained |
| Normalized unified score | No physical meaning | Sigmoid transformation |

| Potential Additions | Estimated RMSE | Feasibility |
|--------------------|---------------|-------------|
| SQM2.20 rescoring | R^2 = 0.69 (PL-REX) | 3 CPU-days for top 50 |
| GIST water correction | +0.1--0.2 R^2 improvement | 2 GPU-days for all 4 states |
| Ensemble docking (5 struct.) | ~3--24% improvement in EF/AUC | 3 GPU-days |
| OpenFE RBFE | RMSE ~0.7--1.7 kcal/mol | 1--4 GPU-days for top 30 |
| Full ABFE | RMSE ~1.0--2.0 kcal/mol | 4--7 GPU-days for top 30 |

The gap between GNINA (~2.5 kcal/mol RMSE) and FEP (~1.0 kcal/mol) is ~1.5 kcal/mol --
this is the difference between noise and signal for lead optimization.

---

### Finding 15: The Publication Impact of Each Method Differs Substantially

| Method | Effort | Impact | Venue Relevance |
|--------|--------|--------|-----------------|
| GIST water thermodynamics | Low (2 GPU-days) | High (state-discrimination evidence) | JCIM, Nature Comp Sci |
| Ensemble docking (KLIFS + AF2) | Low-Medium (3 GPU-days) | Medium (robustness improvement) | JCIM, Bioinformatics |
| SQM2.20 rescoring of top 50 | Low (3 CPU-days) | Medium (physics validation layer) | JCIM |
| OpenFE RBFE on top 20 | Medium (1--4 GPU-days) | Very High (gold-standard validation) | Nature Comp Sci, PNAS |
| Enhanced sampling MD (4 states) | High (2--4 weeks) | Very High (conformational landscape) | PNAS, Nature Comp Sci |
| Full ABFE validation | High (4--7 GPU-days) | Very High (thermodynamic validation) | Nature Comp Sci |
| Delta-ML (GNINA -> FEP correction) | Medium (requires FEP training data) | High (methodological novelty) | NeurIPS, ICML |
| ML force field (MACE/ANI) | Low payoff currently | Low (not production-ready) | Premature |

## Implications for StateBind

### Opportunities

1. **FEP validation is the single highest-impact addition.** Running OpenFE RBFE on
   the top 20 state-aware + 10 static candidates would provide the most rigorous
   computational validation possible. Cost: ~800--1400 GPU-hours (2--4 days on 2
   H200 nodes). This directly addresses reviewer concern #1.

2. **GIST water thermodynamics is the cheapest high-impact experiment.** A 2-GPU-day
   analysis would produce publication-quality evidence that conformational states
   present different thermodynamic environments. This validates the fundamental thesis.

3. **Ensemble docking from KLIFS structures is low-hanging fruit.** EGFR has 100+
   crystal structures in KLIFS. Selecting 5 per state for ensemble docking improves
   robustness with ~3 GPU-days of compute.

4. **SQM2.20 rescoring provides a fast physics checkpoint.** At ~20 min per complex,
   rescoring the top 50 candidates adds a physics-based validation layer without
   FEP complexity.

5. **Enhanced sampling MD generates the richest data but requires the most effort.**
   Microsecond-scale metadynamics of all 4 EGFR states would produce conformational
   free energy landscapes, pocket ensembles, AND water thermodynamic maps. This is
   the most comprehensive approach but requires 2--4 weeks of GPU time.

6. **Delta-ML is a novel methodological contribution.** Training an ML correction from
   GNINA to FEP, then applying it to all candidates, could be the basis of a separate
   methods paper targeting NeurIPS or ICML.

### Risks and Caveats

1. **FEP can fail on challenging transformations.** Charge changes, scaffold hops, and
   flexible binding sites are FEP failure modes. StateBind's VAE-generated candidates
   may include such challenging cases. The OpenFE benchmark showed RMSE of 2.44 kcal/mol
   on real pharma datasets -- not always better than docking.

2. **Water thermodynamics depends on accurate structures.** GIST analysis of crystal
   structures with unresolved waters or crystal contacts may be misleading. MD
   equilibration before GIST is recommended.

3. **Ensemble docking may not improve ranking within states.** It improves cross-state
   comparison and hit diversity, but within a single congeneric series the benefit is
   smaller.

4. **ML force fields are not ready.** MACE-OFF and ANI-2x cannot handle the full
   chemical diversity of kinase inhibitors. Do not invest significant effort here.

5. **Compute cost is real but manageable.** The full physics validation stack (GIST +
   ensemble docking + FEP) would require ~1--2 weeks of dedicated GPU time. This must
   be weighed against competing compute demands on Bouchet.

6. **Score normalization remains a fundamental problem.** Physics-based methods produce
   free energies (kcal/mol). The current pipeline normalizes to [0,1] via sigmoids.
   Any physics upgrade requires rethinking the scoring aggregation.

### Recommended Next Steps

**Tier 1 (do immediately, < 1 week total):**
1. GIST water thermodynamic analysis of all 4 EGFR states (~2 GPU-days)
2. Ensemble docking with 5 KLIFS structures per state (~3 GPU-days)

**Tier 2 (do next, 1--2 weeks):**
3. OpenFE RBFE on top 20 state-aware + top 10 static candidates (~2--4 days)
4. SQM2.20 rescoring of top 50 candidates (~3 CPU-days, parallelizable)

**Tier 3 (if pursuing Nature Comp Sci or similar):**
5. Enhanced sampling MD of all 4 EGFR states (~2--4 weeks)
6. ABFE for cross-series thermodynamic comparison (~4--7 GPU-days)
7. Delta-ML correction from GNINA to FEP (~1 week development)

## References

1. McNutt AT, Francoeur P, Aggarwal R, et al. GNINA 1.0: molecular docking with
   deep learning. J Cheminform. 2021;13:43. doi:10.1186/s13321-021-00522-2

2. Sunseri J, Koes DR. GNINA 1.3: the next increment in molecular docking with deep
   learning. J Cheminform. 2025;17:19. doi:10.1186/s13321-025-00973-x

3. Gapsys V, et al. Large-scale collaborative assessment of binding free energy
   calculations for drug discovery using OpenFE. ChemRxiv. 2025.
   doi:10.26434/chemrxiv-2025-7sthd

4. Wang L, Wu Y, Deng Y, et al. Accurate and reliable prediction of relative ligand
   binding potency in prospective drug discovery by way of a modern free-energy
   calculation protocol and force field. J Am Chem Soc. 2015;137(7):2695-2703.

5. Menke J, et al. Assessing the performance of docking, FEP, and MM/GBSA methods on
   a series of KLK6 inhibitors. J Comput Aided Mol Des. 2023;37:515-530.
   doi:10.1007/s10822-023-00515-3

6. Sutto L, Gervasio FL. Effects of oncogenic mutations on the conformational
   free-energy landscape of EGFR kinase. Proc Natl Acad Sci USA. 2013;110(26):
   10616-10621. doi:10.1073/pnas.1221953110

7. Yang Z, et al. Conformational transition pathways of epidermal growth factor
   receptor kinase domain from multiple molecular dynamics simulations and Bayesian
   clustering. J Chem Theory Comput. 2014;10(8):3448-3461. doi:10.1021/ct500162b

8. Sato T, et al. Microsecond-timescale MD simulation of EGFR minor mutation predicts
   the structural flexibility of EGFR kinase core that reflects EGFR inhibitor
   sensitivity. npj Precis Oncol. 2021;5:32. doi:10.1038/s41698-021-00170-7

9. Zhang Y, et al. Computational analysis of activation of dimerized epidermal growth
   factor receptor kinase using the string method and Markov state model. J Chem Inf
   Model. 2024;64(6):2124-2137. doi:10.1021/acs.jcim.4c00172

10. Robinson DD, et al. Application of MM-GB/SA and WaterMap to SRC kinase inhibitor
    potency prediction. J Comput Aided Mol Des. 2014. doi:10.1007/s10822-014-9735-9

11. Haider K, Cruz A, Ramsey S, et al. Solvation Structure and Thermodynamic Mapping
    (SSTMap): An open-source, flexible package for the analysis of water in molecular
    dynamics trajectories. J Chem Theory Comput. 2018;14(1):418-425.

12. Ramsey S, et al. Solvation thermodynamic mapping of molecular surfaces in
    AmberTools: GIST. J Comput Chem. 2016;37(21):2029-2037.

13. Uehara S, Tanaka S. AutoDock-GIST: Incorporating thermodynamics of active-site
    water into scoring function for accurate protein-ligand docking. Molecules. 2016;
    21(11):1604.

14. Pecina A, Fanfrlik J, et al. SQM2.20: Semiempirical quantum-mechanical scoring
    function yields DFT-quality protein-ligand binding affinity predictions in
    minutes. Nat Commun. 2024;15:1127. doi:10.1038/s41467-024-45431-8

15. Kovacs DP, et al. MACE-OFF: Short-range transferable machine learning force fields
    for organic molecules. J Am Chem Soc. 2024. doi:10.1021/jacs.4c07099

16. Eastman P, et al. OpenMM 8: Molecular dynamics simulation with machine learning
    potentials. J Phys Chem B. 2024;128:109-118.

17. Boyles F, et al. Delta machine learning to improve scoring-ranking-screening
    performances of protein-ligand scoring functions. J Chem Inf Model. 2022;62(12):
    2965-2978. doi:10.1021/acs.jcim.2c00485

18. Vijayan RK, et al. Improving docking and virtual screening performance using
    AlphaFold2 multi-state modeling for kinases. Sci Rep. 2024;14:24654.
    doi:10.1038/s41598-024-75400-6

19. Rueda M, et al. Assessing an ensemble docking-based virtual screening strategy
    for kinase targets by considering protein flexibility. J Chem Inf Model. 2014;
    54(10):2826-2836. doi:10.1021/ci500414b

20. Clyde A, et al. Improving structure-based virtual screening with ensemble docking
    and machine learning. J Chem Inf Model. 2022;62(3):578-590.
    doi:10.1021/acs.jcim.1c00511

21. Aldeghi M, Heifetz A, Bodkin MJ, et al. Predicting kinase inhibitor resistance:
    physics-based and data-driven approaches. ACS Cent Sci. 2019;5(8):1468-1474.
    doi:10.1021/acscentsci.9b00590

22. Chen C, et al. Boosting free-energy perturbation calculations with GPU-accelerated
    NAMD. J Chem Inf Model. 2020;60(11):5301-5307. doi:10.1021/acs.jcim.0c00745

23. Hou T, et al. Assessing the performance of the MM/PBSA and MM/GBSA methods. 1.
    The accuracy of binding free energy calculations based on molecular dynamics
    simulations. J Chem Inf Model. 2011;51(1):69-82. doi:10.1021/ci100275a

24. Genheden S, Ryde U. The MM/PBSA and MM/GBSA methods to estimate ligand-binding
    affinities. Expert Opin Drug Discov. 2015;10(5):449-461.

25. Del Alamo D, et al. High-throughput prediction of protein conformational
    distributions with subsampled AlphaFold2. Nat Commun. 2024;15:2464.
    doi:10.1038/s41467-024-46715-9

26. Modi V, Bhatt VS. Defining a new nomenclature for the structures of active and
    inactive kinases. Proc Natl Acad Sci USA. 2019;116(14):6818-6827.
    doi:10.1073/pnas.1814279116

27. Cyphers S, et al. A water-mediated allosteric network governs activation of
    Aurora kinase A. Nat Chem Biol. 2017;13:402-408. doi:10.1038/nchembio.2296

28. FEP-SPell-ABFE. An open-source automated alchemical absolute binding free energy
    calculation workflow. J Chem Inf Model. 2025. doi:10.1021/acs.jcim.4c01986

29. Bannwarth C, Ehlert S, Grimme S. GFN2-xTB -- an accurate and broadly parametrized
    self-consistent tight-binding quantum chemical method. J Chem Theory Comput.
    2019;15(3):1652-1671. doi:10.1021/acs.jctc.8b01176

30. OpenFE documentation. Welcome to OpenFE's documentation! https://docs.openfree.energy/

31. Mey ASJS, et al. The maximal and current accuracy of rigorous protein-ligand
    binding free energy calculations. Commun Chem. 2023;6:242.
    doi:10.1038/s42004-023-01019-9
