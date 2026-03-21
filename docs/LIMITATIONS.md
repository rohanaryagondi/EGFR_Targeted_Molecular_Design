# Limitations

A complete accounting of what StateBind does not do, cannot claim, and where the evidence is weakest. These limitations are not hidden — they appear in phase reports, the evaluation framework, and the README. This document collects them in one place.

---

## Scoring Limitations

### Docking is a stub
The `docking_proxy` component returns a constant 0.5 for every candidate. This means:
- The comparison **cannot distinguish candidates that actually bind** from those that don't
- The scoring function measures chemical similarity and drug-likeness, not predicted binding affinity
- Any claim about "better binding" or "higher affinity" is unsupported

**Impact:** The single largest gap in the evaluation. Integrating AutoDock Vina, GNINA, or Smina would make the comparison substantially more informative.

### SMILES n-gram similarity is crude
Character 3-gram Tanimoto similarity does not capture molecular topology. Two molecules with similar SMILES strings may have very different 3D shapes, and vice versa. ECFP4/Morgan fingerprints (from RDKit) would provide more accurate similarity measurement.

### state_specificity creates built-in advantage
The state_specificity component (weight 0.15) rewards candidates unique to their target state. This is structurally zero for the static baseline, giving state-aware candidates an inherent scoring advantage on that axis. The diversity and novelty advantages are independent of this component, but the score delta is partially inflated.

---

## Chemistry Limitations

### SMILES-level modifications only
All molecular modifications are string-level operations (e.g., appending "C(F)(F)F" for a CF3 group). There is no:
- 3D pose generation or force-field energy minimization
- Synthetic accessibility scoring (SA score, ASKCOS)
- Reaction-based enumeration (real chemical transformations)
- Validation that modified SMILES correspond to physically realizable molecules

### No ADMET profiling
No absorption, distribution, metabolism, excretion, or toxicity predictions beyond crude MW/HBA/HBD filters.

### Covalent binder design is approximate
Acrylamide warhead addition (for C797-targeting) is a simple SMILES append, not a geometry-aware covalent docking workflow.

---

## Dataset Limitations

### Small benchmark scale
- 18 mutations (7 clinically key)
- 16 PDB structures across 4 states
- 9 reference inhibitors
- ~80 total candidates

This is insufficient for formal statistical testing. No confidence intervals, bootstrap tests, or power analysis.

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

| Limitation | Resolution | Effort |
|-----------|-----------|--------|
| Docking stub | Integrate AutoDock Vina via subprocess | Medium |
| SMILES similarity | Add RDKit ECFP4/Morgan fingerprints | Low |
| Synthetic accessibility | Add RDKit SA score | Low |
| Small benchmark | Automate PDB/COSMIC data acquisition | High |
| Single kinase | Extend to ABL, ALK, BRAF | High |
| MD transitions | Use existing EGFR MD trajectory data | High |
| Statistical testing | Add scipy Mann-Whitney U, bootstrap CI | Low |
| No CI/CD | Add GitHub Actions pytest workflow | Low |
