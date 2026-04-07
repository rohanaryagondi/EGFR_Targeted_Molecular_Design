# Limitations

A complete accounting of what StateBind does not do, cannot claim, and where the evidence is weakest. These limitations are not hidden — they appear in phase reports, the evaluation framework, and the README. This document collects them in one place.

---

## Scoring Limitations

### Docking uses an MPNN proxy, not physics-based scoring
The `docking_proxy` component uses a 3-tier cascade: a trained MPNN (RMSE=0.72, R^2=0.69, Pearson=0.83, 12.7M params, trained on 10,466 compounds), a DockingProxy MLP fallback, and a constant 0.5 stub as the final fallback. This means:
- The MPNN provides informative relative rankings but is still a learned proxy, not a physics simulation
- The scoring function now incorporates learned binding affinity estimates, but these are **not** equivalent to AutoDock Vina or GNINA outputs
- Claims about "binding affinity" should be qualified as "MPNN-predicted" not "physics-validated"

**Impact:** Substantially improved over the original constant stub, but physics-based docking (Vina, GNINA, or Smina) would still make the comparison more informative and biologically credible.

### SMILES n-gram similarity is a fallback only
Morgan/ECFP4 Tanimoto (from RDKit) is now the primary similarity metric (implemented in WS02). SMILES character 3-gram Tanimoto remains as a fallback when RDKit is unavailable. The primary metric captures circular atomic environments and is the cheminformatics standard.

### state_specificity creates built-in advantage
The state_specificity component (weight 0.15) rewards candidates unique to their target state. This is structurally zero for the static baseline, giving state-aware candidates an inherent scoring advantage on that axis. The diversity and novelty advantages are independent of this component, but the score delta is partially inflated.

---

## Chemistry Limitations

### SMILES-level modifications only
All molecular modifications are string-level operations (e.g., appending "C(F)(F)F" for a CF3 group). There is no:
- 3D pose generation or force-field energy minimization
- Reaction-based enumeration (real chemical transformations)
- Validation that modified SMILES correspond to physically realizable molecules

Note: Synthetic accessibility scoring (RDKit SA score) is now implemented in WS01 and filters unrealizable candidates. A VAE (9.5M params, SELFIES representation) generates valid molecules (999/1000 valid, 948 unique), supplementing SMILES-level modifications.

### ADMET profiling available but hERG filtering may be too aggressive
ADMET profiling was implemented in WS09 (hERG AUROC=0.7745, CYP3A4 AUROC=0.7323, 187K params, 27,698 molecules). However, the hERG toxicity classifier may be overly conservative, potentially filtering viable candidates. The AUROC of 0.7745 leaves meaningful false-positive rate for hERG liability.

### Covalent binder design is approximate
Acrylamide warhead addition (for C797-targeting) is a simple SMILES append, not a geometry-aware covalent docking workflow.

---

## Dataset Limitations

### Small benchmark scale
- 18 mutations (7 clinically key)
- 16 PDB structures across 4 states
- 9 reference inhibitors
- 461 state-aware candidates, 30 static candidates (491 total)

Statistical testing has been implemented (WS03): Mann-Whitney U (p<0.001), bootstrap CI, Cohen's d=1.36. The null hypothesis is formally retained (static has higher mean score).

### Single kinase family
Results are specific to EGFR. Other kinases with different conformational landscapes (e.g., ABL has a more prominent DFG-out population) may behave differently. Generalization is untested.

### Single-class context model
All 17 annotated mutations map to DFGin_aCin as their preferred state. The context-to-state prediction task is trivially solvable. Phase 4 ablations run but are uninformative.

### Literature-curated features, not computed
Structural features (DFG distances, pocket volumes, etc.) are taken from published analyses, not computed from PDB coordinates. This ensures correctness for the 16 curated structures but prevents scaling to new structures without manual curation.

---

## Modeling Limitations

### Literature-curated transitions
The Markov state-transition model is fitted to 16 literature-curated pathways, not MD simulation data. Transition probabilities reflect publication frequency, not thermodynamic populations. Commonly studied transitions (active ↔ Src-like) may be overrepresented.

### Learned MLP overfits
The learned world model (MLP on embeddings) overfits due to small training data (34 transitions). The Markov model is the correct choice at this data scale.

---

## Experimental Validation

### No experimental data
All results are computational. No IC50, no selectivity assays, no cell-based data, no animal models. The pipeline produces candidate molecules and computational metrics — not validated drug leads.

### No comparison to published tools
The pipeline is not benchmarked against established tools (REINVENT, DeepDock, DiffSBDD). The static baseline is a simple analog enumeration, not a state-of-the-art generative model.

---

## What Would Resolve These Limitations

| Limitation | Resolution | Status |
|-----------|-----------|--------|
| Docking stub | MPNN proxy trained (RMSE=0.72) in 3-tier cascade (WS08) | **[RESOLVED]** — physics-based docking still needed |
| SMILES similarity | Morgan/ECFP4 Tanimoto is primary metric (WS02) | **[RESOLVED]** |
| Synthetic accessibility | RDKit SA score integrated (WS01) | **[RESOLVED]** |
| ADMET profiling | hERG + CYP3A4 classifiers trained (WS09) | **[RESOLVED]** — hERG may be too aggressive |
| Statistical testing | Mann-Whitney U, bootstrap CI, Cohen's d (WS03) | **[RESOLVED]** |
| No CI/CD | GitHub Actions pytest workflow (WS06) | **[RESOLVED]** |
| Small benchmark | Automate PDB/COSMIC data acquisition | Remaining |
| Single kinase | Extend to ABL, ALK, BRAF | Remaining |
| MD transitions | Use existing EGFR MD trajectory data | Remaining |
