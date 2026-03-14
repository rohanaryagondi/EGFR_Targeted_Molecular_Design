# Phase Plan

Each phase has a defined objective, inputs, outputs, scripts, metrics, and a pass/fail condition. A phase ships only when the pass condition is met.

---

## Phase 0: Scaffold ✅

**Objective:** Establish repository structure, documentation, development environment, and CI basics so that all subsequent phases start from a clean foundation.

| Aspect | Detail |
|--------|--------|
| **Inputs** | Project requirements, technology choices |
| **Outputs** | Installable package, passing tests, documentation framework |
| **Scripts** | N/A |
| **Metrics** | All tests pass, `statebind --help` works, `pip install -e .` succeeds |
| **Pass condition** | 22/22 tests pass. Package installs cleanly. CLI responds. Docs exist. Pushed to GitHub. |
| **Fail condition** | Any test fails, or package doesn't install. |

**Status:** ✅ Complete (2026-03-14). 22 tests passing, pushed to GitHub.

---

## Phase 1: Context & Data

**Objective:** Build a curated, queryable atlas of EGFR kinase domain mutations with resistance mechanism annotations. This is the "input" to the entire pipeline — if the mutation data is wrong or incomplete, everything downstream is compromised.

| Aspect | Detail |
|--------|--------|
| **Inputs** | COSMIC mutation data (public), ClinVar variants, published review papers on EGFR resistance (Yun et al. 2008, Jänne et al. 2015, Thress et al. 2015) |
| **Outputs** | `MutationAtlas` — a structured JSON file containing 15–30 curated mutations with: residue position, WT/mutant AA, resistance generation (1st/2nd/3rd), mechanism category (gatekeeper, covalent site, hinge, hydrophobic spine), known drug associations, documented conformational effect |
| **Scripts** | `scripts/run_context.py --config configs/context.yaml` |
| **Artifacts** | `artifacts/context/mutation_atlas.json`, `artifacts/context/mutation_summary.csv` |
| **Metrics** | (1) Number of curated mutations (target: 15–30). (2) Fraction with documented conformational effect (target: >50%). (3) Schema validation passes (all records conform to Pydantic model). |
| **Pass condition** | ≥15 mutations curated. Schema validation passes on all records. At least T790M, L858R, and C797S are present with complete annotations. Unit tests pass. |
| **Fail condition** | Fewer than 10 mutations, or any of the three key mutations (T790M, L858R, C797S) missing or incompletely annotated. |

**Key decisions to make:**
- What counts as "resistance" (clinical vs. in vitro)?
- How to handle compound mutations (e.g., T790M+C797S)?
- Whether to include activating mutations (L858R) alongside resistance mutations

---

## Phase 2: Structure Atlas

**Objective:** Download EGFR kinase domain structures from PDB, classify each by conformational state (DFG × αC-helix), extract binding pocket geometries, and select representative structures per state.

| Aspect | Detail |
|--------|--------|
| **Inputs** | PDB query for EGFR kinase domain structures, mutation atlas (for mutation-structure mapping) |
| **Outputs** | `StateAtlas` — classified structures with state labels; pocket geometries per state; representative structures |
| **Scripts** | `scripts/run_structure.py --config configs/structure.yaml` |
| **Artifacts** | `artifacts/structure/state_atlas.json`, `artifacts/structure/pockets/<state>/*.json`, `artifacts/structure/representatives.json` |
| **Metrics** | (1) Number of structures classified (target: 30–80). (2) Number of states with ≥3 structures (target: ≥3 of 4 states). (3) Classification agreement with KLIFS database (if available) on a spot-check of 10 structures. (4) Pocket volume variance within a state (should be < variance between states). |
| **Pass condition** | ≥30 structures classified. ≥3 states populated with ≥3 structures each. Representative structure selected per populated state. Pocket extraction runs without error. |
| **Fail condition** | Fewer than 20 structures classified, or fewer than 2 states populated. |

**Key decisions to make:**
- Geometric thresholds for DFG classification (Asp–Phe Cα distance cutoff)
- αC-helix classification method (RMSD to reference vs. Lys-Glu salt bridge distance)
- Pocket extraction radius and method (geometric vs. fpocket vs. custom)
- How to handle structures with missing residues in the DFG or αC-helix region

---

## Phase 3: Dynamics & State Prediction

**Objective:** Given a mutation context, predict which conformational states are most relevant for molecular design. Start with a lookup table baseline; extend to a classifier if data supports it.

| Aspect | Detail |
|--------|--------|
| **Inputs** | Mutation atlas (Phase 1), state atlas (Phase 2), literature on mutation-state associations |
| **Outputs** | State relevance predictions: for each mutation, a probability distribution over the 4 canonical states |
| **Scripts** | `scripts/run_dynamics.py --config configs/dynamics.yaml` |
| **Artifacts** | `artifacts/dynamics/state_predictions.json`, `artifacts/dynamics/state_relevance_matrix.csv` |
| **Metrics** | (1) Coverage: fraction of atlas mutations with a non-uniform state prediction (target: >60%). (2) Agreement with literature: for T790M, L858R, C797S, does the predicted top state match published structural data? (3) If ML model: leave-one-out accuracy on the curated dataset. |
| **Pass condition** | Lookup table baseline covers ≥3 key mutations with literature-supported predictions. State predictions are non-trivial (not all uniform). Output schema is valid. |
| **Fail condition** | Lookup table is empty or covers <3 mutations. No basis for any state prediction. |

**Key decisions to make:**
- Whether an ML model is warranted (depends on how many mutation-state pairs we can curate)
- How to handle mutations with no documented conformational effect (uniform prior? exclude?)
- Whether to weight states by structure count in the atlas

---

## Phase 4: Molecular Generation

**Objective:** Generate candidate small molecules for EGFR pockets. Run two parallel tracks: state-aware (pocket from predicted top state) and baseline (pocket from static single structure). Compare generation outputs.

| Aspect | Detail |
|--------|--------|
| **Inputs** | Pocket geometries (Phase 2), state predictions (Phase 3) |
| **Outputs** | Two sets of candidate molecules (SMILES + metadata): state-aware and baseline |
| **Scripts** | `scripts/run_generation.py --config configs/generation.yaml` |
| **Artifacts** | `artifacts/generation/candidates_stateaware.csv`, `artifacts/generation/candidates_baseline.csv` |
| **Metrics** | (1) Number of valid candidates generated per track (target: 100–500). (2) Chemical validity rate (fraction passing RDKit sanitization, target: >90%). (3) Uniqueness rate (fraction of unique SMILES, target: >80%). (4) Diversity: mean pairwise Tanimoto distance (target: >0.5). (5) Drug-likeness: fraction passing Lipinski rule of 5 (target: >70%). |
| **Pass condition** | Both tracks produce ≥50 valid, unique candidates. Validity >80%. Both tracks use the same generation method (only the pocket differs). |
| **Fail condition** | Either track produces <20 valid candidates, or validity <50%. |

**Key decisions to make:**
- Generation method: fragment enumeration, SMILES sampling from pretrained model, or pharmacophore-based
- Pocket representation for conditioning: 3D coordinates, pharmacophore features, or descriptor vector
- Number of candidates to generate (enough for statistical comparison)
- Whether to apply chemical filters before or after generation

---

## Phase 5: Ranking & Benchmarking

**Objective:** Score all candidates against all state pockets, compare state-aware vs. baseline track, report statistical results.

| Aspect | Detail |
|--------|--------|
| **Inputs** | Candidate molecules (both tracks, Phase 4), pocket geometries (all states, Phase 2), state predictions (Phase 3) |
| **Outputs** | Scored candidate lists, statistical comparison, final report |
| **Scripts** | `scripts/run_ranking.py --config configs/ranking.yaml` |
| **Artifacts** | `artifacts/ranking/comparison_results.json`, `artifacts/ranking/scores_stateaware.csv`, `artifacts/ranking/scores_baseline.csv` |
| **Metrics** | (1) **Primary:** Mean docking score of top-10 candidates, state-aware vs. baseline (lower is better for Vina-like scores). (2) **Secondary:** Cross-state selectivity — do state-aware candidates score well on the intended state and worse on others? (3) **Tertiary:** Score distribution overlap (KL divergence or Wasserstein distance between state-aware and baseline score distributions). (4) Statistical test: Mann-Whitney U or paired Wilcoxon on matched-pocket scores, with Bonferroni correction. |
| **Pass condition** | Both tracks scored. Statistical comparison reported with effect size and p-value. Result is interpretable regardless of direction (state-aware may or may not "win"). |
| **Fail condition** | Scoring fails on >20% of candidates. No statistical comparison produced. |

**Key decisions to make:**
- Docking tool: Vina, smina, or GNINA (tradeoff: speed vs. accuracy vs. availability)
- Whether to use rescoring (dock with one tool, rescore with another)
- How many top-N candidates to compare (top-10? top-50?)
- How to handle docking failures (exclude? penalize?)

---

## Phase 6: Integration & Demo

**Objective:** Wire the full pipeline end-to-end, create demo artifacts, write the final report, polish the repository for public viewing.

| Aspect | Detail |
|--------|--------|
| **Inputs** | All modules, all artifacts from Phases 1–5 |
| **Outputs** | End-to-end runnable pipeline, demo notebook, final report, polished README |
| **Scripts** | `scripts/run_pipeline.py --config configs/pipeline.yaml` |
| **Artifacts** | `reports/final_report.md`, `reports/figures/`, demo notebook |
| **Metrics** | (1) Pipeline runs end-to-end from `statebind run --config configs/pipeline.yaml` without manual intervention. (2) Report contains: thesis, methods, results, figures, limitations. (3) README hero image exists. |
| **Pass condition** | Full pipeline runs. Report exists with at least one comparison figure. Repository is clean (no dead code, no broken imports, all tests pass). |
| **Fail condition** | Pipeline crashes mid-run. No report produced. |
