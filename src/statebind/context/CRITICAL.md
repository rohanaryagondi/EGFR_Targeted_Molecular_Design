# Critical Information -- Context

- SINGLE-CLASS DATASET: all 17 resistance mutations map to `DFGin_aCin` (`preferred_states` in `processing/context.py`). Model evaluation is uninformative -- 100% accuracy is trivially achievable.
- 33 features total: 29 mutation features + 4 pathway features -- extracted in `features.py`.
- Mutation features include: position (normalized), wild-type/mutant AA properties (hydrophobicity, MW, volume, charge), mechanism one-hot, resistance generation one-hot -- `features.py:26-55`.
- Three model tiers exist but all predict the same class due to single-class data: mutation-only, combined, and embedding models.
- EGFR kinase domain boundaries at `features.py:58-59`: residues 696-1022. Position normalization uses these bounds.
- Amino acid property tables (hydrophobicity, MW, volume, charge) are at `features.py:26-55`. Missing amino acids return 0.0.
- `evaluation.py:1-9` computes accuracy, precision/recall/F1, confusion matrix, calibration, and cross-entropy loss -- all meaningless with single-class data.
- The module imports from `processing.models` for `ConformationalState`, `MechanismCategory`, `MutationRecord`, `ResistanceGeneration` -- `features.py:15-20`.
- Adding multi-class mutations (e.g., DFGout-preferring mutations) would make context prediction meaningful.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
