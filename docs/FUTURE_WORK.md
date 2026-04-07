# Future Work

Concrete next steps for StateBind, organized by priority and effort.

---

## High Priority (Would Substantially Strengthen Claims)

### 1. [DONE] Replace docking stub with learned proxy
**Status:** MPNN trained (RMSE=0.72, R^2=0.69, Pearson=0.83, 12.7M params, 10,466 compounds) and active in 3-tier cascade (WS08). DockingProxy MLP and constant fallback remain as backup tiers.

**Remaining:** Replace MPNN proxy with physics-based docking (AutoDock Vina, GNINA, or Smina) for true binding affinity prediction. This is still the single largest gap for biological validity.

### 2. [DONE] Add ECFP4/Morgan fingerprint similarity
**Status:** Implemented in WS02 (Morgan/ECFP4 Tanimoto). Now the primary similarity metric in the scoring function; SMILES n-gram is fallback only.

### 3. [DONE] Add statistical testing
**Status:** Implemented in WS03 (Mann-Whitney U, bootstrap CI, Cohen's d). 548 tests across 12 subpackages. Null hypothesis formally retained (p<0.001, d=1.36, static mean > state-aware mean).

---

## Medium Priority (Would Improve Quality)

### 4. [DONE] Synthetic accessibility scoring
**Status:** Implemented in WS01 (RDKit SA score, Ertl & Schuffenhauer, 2009). Integrated into candidate filtering pipeline.

### 5. Automated PDB structure acquisition
**Why:** Current dataset is manually curated (16 structures). Automated acquisition would enable larger benchmarks.

**How:** Use the PDB REST API to query EGFR kinase domain structures. Compute structural features from coordinates using BioPython.

**Effort:** High (1 week). Requires coordinate parsing and feature extraction code.

### 6. [DONE] CI/CD with GitHub Actions
**Status:** Implemented in WS06 (`.github/workflows/test.yml`). Automated pytest on push/PR.

### 7. Expand to additional kinase families
**Why:** EGFR may not be representative. ABL has well-characterized DFG-out preferences. ALK and BRAF have distinct conformational landscapes.

**How:** Replicate the data curation and pipeline for each new target. Evaluate whether the state-aware advantage generalizes.

**Effort:** High per target (3-5 days each).

---

## Lower Priority (Nice to Have)

### 8. MD-derived transition matrices
Replace literature-curated sequences with transition counts from existing EGFR MD trajectories (e.g., from D.E. Shaw Research published datasets).

### 9. 3D-aware molecular generation
Integrate REINVENT, DiffSBDD, or Pocket2Mol for structure-based generation instead of SMILES-level modifications.

### 10. [DONE] ADMET profiling
**Status:** Implemented in WS09 (hERG AUROC=0.7745, CYP3A4=0.7323, 187K params, 27,698 molecules). Caveat: hERG filtering may be too aggressive at current threshold.

### 11. Cross-state selectivity metric
Score each candidate against all 4 state pockets (requires docking). Compute selectivity as score variance across states. State-aware candidates should be more selective for their intended state.

### 12. Interactive visualization
Build a Streamlit or Panel dashboard showing the comparison results, with interactive filtering by state, strategy, and score range.

---

## Implementation Order

Items 1-5 are complete. Remaining priorities:

1. ~~**ECFP4 fingerprints**~~ [DONE]
2. ~~**Statistical testing**~~ [DONE]
3. ~~**Docking proxy (MPNN)**~~ [DONE] — physics-based docking (Vina/GNINA) remains
4. ~~**SA scoring**~~ [DONE]
5. ~~**CI/CD**~~ [DONE]
6. **Additional kinases** (1 week+) — generalization evidence
7. **Physics-based docking** (Vina/GNINA) — replaces learned proxy with true binding affinity
8. **MD-derived transition matrices** — replaces literature-curated Markov model
9. **FEP+ validation** — free energy perturbation for top candidates
