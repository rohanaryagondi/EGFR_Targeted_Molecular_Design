# Technical Deep Dive

Module-by-module explanation of StateBind's design decisions, tradeoffs, and failure cases.

---

## 1. Data Layer (`data/`, `processing/`)

### Design
- **Source registry** maps every data source to a URL, license, version, and quality tier
- **Manifests** track what was downloaded, when, and what checksum
- **Processing pipeline** transforms raw records into typed Pydantic models (MutationRecord, StructureRecord, LigandRecord) with provenance fields

### Decision: Literature-curated data instead of automated downloads
We hardcoded curated mutation and structure records rather than building a PDB/COSMIC download pipeline. This trades scalability for correctness — every record has been verified against published structural studies.

**Tradeoff:** The dataset is small (18 mutations, 16 structures, 9 ligands). Automating data acquisition would increase scale but introduce noise from misannotated or irrelevant entries.

### Failure case
If a mutation's preferred conformational state is not represented in PDB structures, the context model defaults to DFGin_aCin (active state). This happened for all 17 mutations in Phase 4, producing a single-class dataset. The limitation is documented, not hidden.

---

## 2. Static Baseline (`baselines/`)

### Design
Single-structure pipeline: 1M17 → pocket definition → candidate library → property filtering → scoring → ranking.

Scoring uses three components:
- reference_similarity (Tanimoto to erlotinib/gefitinib/osimertinib)
- druglikeness (MW, HBA, HBD, ring count)
- docking_proxy (3-tier cascade: MPNN → DockingProxy MLP → stub)

### Decision: Build the baseline before the state-aware pipeline
This follows the baseline-first principle from the project charter. The baseline defines the floor that state-aware design must beat. Building it first prevents unconscious tuning of the evaluation to favor the state-aware approach.

### Decision: SMILES n-gram Tanimoto instead of ECFP4
We use character 3-grams as a fingerprint proxy because RDKit is an optional dependency. This is a known approximation — ECFP4 would be more accurate. The `_tanimoto_ngram` function is isolated and swappable.

**Tradeoff:** Lower discriminative power for similarity scoring. Some structurally different molecules may appear similar by n-grams, and vice versa.

---

## 3. Structural State Atlas (`structure/`)

### Design
Each EGFR structure is classified into one of four canonical states based on a 9-dimensional feature vector:
1. DFG Asp-Phe distance
2. DFG Phe position
3. αC-helix salt bridge
4. αC-helix rotation
5. P-loop displacement
6. Hinge angle
7. Activation loop RMSD
8. Gatekeeper sidechain
9. Pocket volume

K-means clustering (k=4) assigns states. Silhouette score validates cluster quality.

### Decision: Literature-curated features instead of coordinate extraction
Computing structural features from PDB coordinates requires BioPython/MDAnalysis and coordinate parsing. We instead curate feature values from published structural analyses. This ensures correctness but limits scalability.

**Tradeoff:** Cannot add new PDB structures without manual curation. An automated feature extraction module would enable dynamic atlas updates.

### Failure case
If cluster quality is poor (silhouette < 0.3), the classification is unreliable. Current silhouette scores are acceptable because the four EGFR states are well-separated in structural feature space.

---

## 4. Context Model (`context/`)

### Design
Maps mutation context (29 mutation features + 4 pathway proxy features) to conformational state relevance. Three model tiers:
1. **Nearest centroid** — baseline, no training
2. **Logistic regression** — L2 regularized, SGD
3. **MLP** — 2-layer, ReLU, Xavier init

### Decision: Include pathway features as proxies
Mutations affect downstream signaling pathways (MAPK, PI3K, STAT3, Src). These 4 binary features serve as proxies for pathway context that may influence conformational preference.

### Critical finding: Single-class dataset
All 17 mutations map to DFGin_aCin as their preferred state (from literature annotations). This makes the classification task trivially solvable — every model achieves 100% accuracy. The ablation suite runs but is uninformative.

**This is not a bug.** EGFR mutations in the literature do predominantly favor the active state. A multi-class dataset would require mutations from other kinase families or engineered variants.

### What would make it meaningful
Adding mutations from ABL (which has well-characterized DFG-out preferences) or incorporating MD simulation data that reveals mutation-specific state populations.

---

## 5. World Model / Dynamics (`dynamics/`)

### Design
- **State sequences:** 16 literature-curated sequences encoding EGFR conformational pathways (activation, inactivation, drug-induced, mutation-biased, equilibrium)
- **Transition matrix:** Laplace-smoothed MLE from 34 pairwise transitions
- **Embeddings:** 4-D contrastive embedding where distance ∝ −log(transition probability)
- **Learned model:** MLP on embeddings for next-state prediction

### Decision: Literature curation instead of MD trajectories
MD simulations of EGFR state transitions are computationally expensive (microseconds of simulation time) and not publicly available in standardized form. Literature-curated sequences capture established pathways (e.g., active→Src-like via αC-helix rotation) without requiring simulation infrastructure.

**Tradeoff:** The transition matrix reflects literature consensus, not thermodynamic reality. Transition probabilities are relative frequencies, not Boltzmann-weighted populations.

### Key result
- Markov model best on test set (LL=−1.31 vs uniform −1.39)
- Learned MLP overfits (LL=−2.25) due to small dataset
- Stationary distribution: DFGin_aCin 36.5%, DFGin_aCout 26.7%, DFGout_aCin 18.5%, DFGout_aCout 18.3%
- Embedding distance-transition correlation: −0.912

### Failure case
The learned MLP overfits because 34 transitions are too few for a neural model. The Markov model is the correct choice at this data scale. The overfitting is documented and the MLP is retained for future use with larger datasets.

---

## 6. State-Conditioned Generation (`generation/`)

### Design
Each conformational state gets a `PocketCondition` that maps pocket geometry to generation strategies:
- **DFGin_aCin:** hinge optimization, gatekeeper avoidance, covalent warhead
- **DFGin_aCout:** volume filling, hinge optimization
- **DFGout_aCin:** back-pocket extension, volume filling
- **DFGout_aCout:** back-pocket extension, P-loop interaction

Strategies apply SMILES-level transformations to reference compounds. Filtering uses type-I rules (MW 200-600) for DFGin states and type-II rules (MW 250-800) for DFGout states.

### Decision: SMILES-level modifications instead of 3D-aware generation
Generative models like REINVENT or 3D-SBDD require either pretrained models or docking infrastructure. SMILES modifications are crude but transparent — every transformation has a stated pharmacological rationale.

**Tradeoff:** No guarantee that modified SMILES correspond to synthetically accessible or geometrically valid molecules. The modifications encode known medicinal chemistry patterns (e.g., acrylamide warheads for covalent inhibitors) but not 3D binding pose complementarity.

### What it does well
Produces genuinely different candidate sets per state. Back-pocket extensions appear only for DFG-out states. P-loop binders appear only for the fully inactive DFGout_aCout state. This is a structural result, not an artifact.

---

## 7. Ranking & Evaluation (`ranking/`, `evaluation/`)

### Design
Unified scoring applies the same 4-component function to both pipelines. The merge deduplicates by SMILES, keeping the higher-scoring version. Comparison metrics: overlap (Jaccard), diversity, score distributions, top-K composition, rank shifts, and novelty analysis.

### Decision: Include state_specificity in unified scoring
This component rewards candidates unique to their target state (1.0 if unique, 0.5 if in 2 states, 0.0 if in all 4). It is structurally zero for the static baseline.

**Why include it:** State specificity is a genuine design desideratum. A molecule designed for the DFG-out back pocket should ideally not also fit the compact DFGin pocket — that would suggest it's not actually exploiting the back pocket.

**Why it's controversial:** It gives state-aware candidates an inherent advantage. All interpretations in the report account for this. The evaluation framework document specifies that results should be reported with and without this component.

### Decision: ASCII figures instead of matplotlib
Text-based figures can be embedded directly in markdown and rendered on GitHub without image hosting. They are also deterministic (no rendering differences across platforms). matplotlib integration is noted as a future upgrade.

---

## 8. Cross-Cutting Design Decisions

### Typed throughout
Every function has type annotations. Every data structure is a Pydantic model or typed dataclass. This catches errors at the schema boundary, not deep inside computation.

### No hard-coded paths
All paths flow from config files or function arguments. The `DataPaths` utility centralizes path construction. Artifacts go under `artifacts/`, reports under `reports/`.

### Tests before code (in spirit)
Test files are written alongside modules. The test suite validates schemas, pipeline outputs, metric ranges, and figure generation — not just "does it run." 548 tests at fast execution means the suite runs on every save.

### Git hygiene
One commit per phase. Each commit message states what the phase accomplished. No squashing, no rewriting history.

---

## 9. What Would Make This Production-Ready

| Gap | Fix | Effort |
|-----|-----|--------|
| Physics-based docking | Replace MPNN proxy with AutoDock Vina/GNINA | Medium |
| SMILES fingerprints | Add RDKit ECFP4/Morgan | Low |
| Synthetic accessibility | Add SA score from RDKit | Low |
| Larger benchmark | Automate PDB/COSMIC data acquisition | High |
| MD-derived transitions | Run EGFR simulations or use existing trajectories | High |
| 3D-aware generation | Integrate REINVENT or DiffSBDD | High |
| Statistical testing | Add Mann-Whitney U / bootstrap CI | Low |
| CI/CD | GitHub Actions for pytest + ruff | Low |
