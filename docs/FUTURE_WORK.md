# Future Work

Concrete next steps for StateBind, organized by priority and effort.

---

## High Priority (Would Substantially Strengthen Claims)

### 1. Replace docking stub with AutoDock Vina
**Why:** The docking proxy is the single largest gap. Replacing it would enable actual binding affinity comparison between pipelines.

**How:** Call Vina via subprocess for each candidate × each state pocket. Parse the affinity output. Replace `docking_proxy` in the unified scoring function.

**Effort:** Medium (2-3 days). Requires Vina installation and receptor PDBQT preparation for 4 structures.

**Impact:** Transforms the comparison from "chemical space exploration" to "predicted binding quality."

### 2. Add ECFP4/Morgan fingerprint similarity
**Why:** SMILES 3-gram Tanimoto is a crude proxy. ECFP4 captures circular atomic environments and is the standard in cheminformatics.

**How:** Make RDKit a required dependency. Replace `_tanimoto_ngram()` with `DataStructs.TanimotoSimilarity(AllChem.GetMorganFingerprintAsBitVect(...))`.

**Effort:** Low (1 day). The function is already isolated and swappable.

**Impact:** More accurate similarity scoring. Better diversity measurement. More credible reference_similarity component.

### 3. Add statistical testing
**Why:** The comparison reports means and deltas but no confidence intervals or significance tests. With 30 vs 79 candidates, formal testing would clarify whether differences are meaningful.

**How:** Add scipy as a dependency. Compute Mann-Whitney U for score distributions. Add bootstrap confidence intervals for diversity and mean score deltas.

**Effort:** Low (1 day).

**Impact:** Quantifies uncertainty. Enables "significant" vs "not significant" verdict.

---

## Medium Priority (Would Improve Quality)

### 4. Synthetic accessibility scoring
**Why:** Some generated SMILES may correspond to molecules that are impossible to synthesize.

**How:** Add RDKit SA score (Ertl & Schuffenhauer, 2009). Filter candidates with SA > 6.0.

**Effort:** Low (1 day).

### 5. Automated PDB structure acquisition
**Why:** Current dataset is manually curated (16 structures). Automated acquisition would enable larger benchmarks.

**How:** Use the PDB REST API to query EGFR kinase domain structures. Compute structural features from coordinates using BioPython.

**Effort:** High (1 week). Requires coordinate parsing and feature extraction code.

### 6. CI/CD with GitHub Actions
**Why:** Tests currently run locally only. A push could break tests without immediate feedback.

**How:** Add `.github/workflows/test.yml` running `pytest` on push/PR.

**Effort:** Low (1 hour).

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

### 10. ADMET profiling
Add absorption, distribution, metabolism, excretion, and toxicity predictions using open-source tools (ADMETlab, pkCSM).

### 11. Cross-state selectivity metric
Score each candidate against all 4 state pockets (requires docking). Compute selectivity as score variance across states. State-aware candidates should be more selective for their intended state.

### 12. Interactive visualization
Build a Streamlit or Panel dashboard showing the comparison results, with interactive filtering by state, strategy, and score range.

---

## Implementation Order

For maximum impact with minimum effort:

1. **ECFP4 fingerprints** (1 day) — immediately improves similarity scoring
2. **Statistical testing** (1 day) — adds rigor to the comparison
3. **AutoDock Vina** (2-3 days) — transforms the evaluation
4. **SA scoring** (1 day) — filters unrealizable candidates
5. **CI/CD** (1 hour) — basic engineering hygiene
6. **Additional kinases** (1 week+) — generalization evidence
