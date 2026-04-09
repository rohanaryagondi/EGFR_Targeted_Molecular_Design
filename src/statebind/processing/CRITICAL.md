# Critical Information -- Processing

- ALL curated data is embedded as Python literals in source code, not loaded from external files -- `context.py:24-37` returns hard-coded `MutationRecord` list.
- Dataset sizes: 18 mutations (17 resistance + 1 activating pair), 16 structures, 9 ligands.
- `ConformationalState` enum at `models.py:52-56` is the CANONICAL state definition used by every downstream module. 4 values: DFGin_aCin, DFGin_aCout, DFGout_aCin, unclassified. (DFGout_aCout removed: no genuine EGFR DFGout/aCout structures exist.)
- `ResistanceGeneration` enum at `models.py:18-24` has 6 values: FIRST through FOURTH, ACTIVATING, UNKNOWN.
- `MechanismCategory` enum at `models.py:27-39` has 12 values covering all known EGFR resistance mechanisms.
- `ConformationalEffect` enum at `models.py:42-49` has 7 values describing how mutations affect conformational equilibrium.
- `Provenance` model at `models.py:70-76` is attached to every processed entity for traceability.
- Every mutation record includes PMIDs in `references` field -- `context.py:52`. This is the provenance chain.
- The `__init__.py` exports 6 builder functions: `build_context_dataset`, `build_structure_dataset`, `build_ligand_dataset`, `build_mapping_tables`, `assemble_benchmark`, `validate_dataset`.
- Downstream modules (`structure/`, `context/`, `generation/`) import enums and models from `processing/models.py` -- changing enum values breaks everything.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
