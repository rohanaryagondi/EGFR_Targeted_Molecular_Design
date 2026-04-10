---
phase: "Phase 1: Core Experiments"
task_id: P1-T09
task_name: "ABL1 Structures + Features"
implementation_plan_ref: "P12: Multi-Kinase Extension -- ABL1 (steps 3-4)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: ABL1 Structures + Features

## Objective

Curate ABL1 PDB structures across conformational states, add ABL1-specific
pocket features and conditioning vectors, and create ABL1 docking configuration.
This builds the structural foundation for ABL1 pipeline execution.

## Context

ABL1 has genuine DFGout structures (unlike EGFR), making it a stronger test of
the state-conditioning hypothesis. The canonical DFGout structure is 1IEP
(imatinib-bound). The lesson from EGFR Phase 0 is that every structural
annotation must be verified against the actual PDB record.

## Prerequisites

- [x] P1-T05 completed (target_gene field added, ABL1 data curated)
- [x] ABL1 ChEMBL data at `data/processed/abl1_affinity.json`

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/structure/features.py` | How EGFR features are defined -- template for ABL1 |
| `src/statebind/generation/conditioning.py` | How pocket conditions map to generation strategies |
| `configs/docking.yaml` | Current EGFR docking config -- template for ABL1 |
| `src/statebind/processing/structures.py` | EGFR structure curation pattern |
| `scripts/curate_abl1_structures.py` | ABL1 structure curation from P1-T05 |
| `data/processed/structures/abl1_structures.json` | ABL1 structures from P1-T05 |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/structure/features.py` | append | Add ABL1 PDB features to curated features dict |
| `src/statebind/generation/conditioning.py` | append | Add ABL1 pocket conditions |
| NEW: `configs/docking_abl1.yaml` | -- | ABL1-specific docking config with state->receptor mapping |
| `src/statebind/structure/atlas.py` | ~50 | Add target_gene parameter to build_state_atlas() |
| NEW: `tests/test_abl1_features.py` | -- | Tests for ABL1 feature values and conditioning |

## Implementation Steps

1. **Verify ABL1 PDB structures** from P1-T05 output:

   For each ABL1 structure, verify against PDB:
   - **1IEP** (imatinib): Should be DFGout. Check DFG-Asp381/Phe382 distance.
     Organism: Homo sapiens. Mutations: none (WT construct).
   - **2GQG** (dasatinib): Should be DFGin. Check DFG distances.
     Organism: Homo sapiens. Mutations: verify carefully.
   - **3PYY** (nilotinib): Should be DFGout. Verify.
   - Cross-reference all with KLIFS for DFG/aC classification.

   **CRITICAL**: Do NOT trust metadata alone. Download PDB headers and verify.
   The EGFR experience showed 3iku was ParM (not EGFR) and 4ZAU was mislabeled.

2. **Add ABL1 features to `structure/features.py`**:

   Add ABL1-specific entries to the curated features dictionary. Each entry maps
   a PDB ID to (StructuralFeatures, PocketDescriptor). For ABL1:

   - StructuralFeatures: dfg_distance, ac_rotation, p_loop_displacement,
     back_pocket_depth, activation_loop_rmsd, hinge_angle, gatekeeper_distance,
     k_e_salt_bridge, overall_compactness
   - PocketDescriptor: volume, hydrophobic_fraction, hba_count, hbd_count,
     aromatic_fraction, flexibility_score, solvent_exposure

   These should be derived from literature values or computed from PDB coordinates
   using BioPython if available. Document the source of each value.

3. **Add ABL1 pocket conditions to `conditioning.py`**:

   Add ABL1-specific `PocketCondition` entries. The strategies may differ from EGFR:
   - ABL1 DFGin: HINGE_OPTIMIZED (type-I inhibitors)
   - ABL1 DFGout: BACK_POCKET_EXTENSION (type-II inhibitors, larger DFGout pocket)
   - ABL1 aC-out: may not exist; check KLIFS

   Use the `select_strategies_for_pocket()` function pattern -- it's already
   generic and should work for ABL1 pocket descriptors.

4. **Create `configs/docking_abl1.yaml`**:

   ```yaml
   # ABL1 docking configuration
   gnina_path: "gnina"
   exhaustiveness: 8
   num_modes: 5
   cnn_scoring: "rescore"
   receptor_output_dir: "data/processed/docking/receptors/abl1/"
   box_padding: 5.0
   box_size: [25, 25, 25]
   scoring:
     vina_scale: 3.0

   representatives:
     DFGin_aCin: "2gqg"     # dasatinib-bound, DFGin
     DFGout_aCin: "1iep"    # imatinib-bound, DFGout
     # Add DFGin_aCout if a suitable structure exists
   ```

5. **Add target_gene to `atlas.py`**:

   Modify `build_state_atlas()` to accept an optional `target_gene` parameter:
   ```python
   def build_state_atlas(target_gene: str = "EGFR", ...) -> StateAtlas:
   ```
   When target_gene != "EGFR", load the appropriate structures and features.
   Keep backward compatibility: default is "EGFR".

6. **Write tests** (`tests/test_abl1_features.py`):

   - Test ABL1 feature values are present in curated features dict
   - Test ABL1 pocket conditions are defined for each ABL1 state
   - Test `build_state_atlas(target_gene="ABL1")` produces a valid atlas
   - Test docking config for ABL1 has correct representative PDBs

## Verification

- [ ] ABL1 PDB annotations verified against actual PDB records
- [ ] ABL1 features added to features.py with documented sources
- [ ] ABL1 pocket conditions added to conditioning.py
- [ ] `configs/docking_abl1.yaml` has correct state->receptor mapping
- [ ] `build_state_atlas(target_gene="ABL1")` returns valid atlas
- [ ] `pytest tests/test_abl1_features.py -v` -- all tests pass
- [ ] `pytest -v --tb=short` -- 669+ tests pass, no regressions
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- **Verify every annotation**. The EGFR Phase 0 lesson: 3iku was ParM (not EGFR),
  4ZAU was mislabeled as DFGout. Download PDB headers. Check organism. Check
  mutations. Cross-reference with KLIFS.
- Features should be curated from literature or computed from coordinates. Do NOT
  invent plausible-looking numbers.
- ABL1 has a genuine DFGout state (unlike EGFR). This is a key advantage for
  the multi-kinase analysis.
- Keep the code generic where possible -- a future third kinase (BRAF) should
  follow the same pattern.

## Notes and Gotchas

- **ABL1 T315I gatekeeper mutation**: Many ABL1 structures carry this resistance
  mutation. Document which structures are WT vs T315I.
- **ABL1 may have 3 or 4 conformational states**: Unlike EGFR (which was reduced
  to 3 states), ABL1 may genuinely have DFGout_aCout structures. Verify before
  committing to a state count.
- **Receptor preparation**: Each ABL1 PDB structure needs to be prepared for
  GNINA docking (remove water, add hydrogens, etc.). This can be done with
  `scripts/prepare_docking_receptors.py` adapted for ABL1.
- **features.py uses a flat dict**: The `_curated_features()` function returns
  a dict keyed by PDB ID. ABL1 PDB IDs won't conflict with EGFR PDB IDs,
  so they can coexist in the same dict.
