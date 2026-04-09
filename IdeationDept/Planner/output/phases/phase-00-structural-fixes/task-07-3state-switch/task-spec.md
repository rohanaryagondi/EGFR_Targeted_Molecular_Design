---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T07
task_name: "Remove DFGout_aCout (3-State Switch)"
implementation_plan_ref: "P1: Fix Structural Annotations (3-state switch portion)"
status: pending
created: 2026-04-09T18:00:00Z
estimated_effort: "1-1.5 days"
conditional: true
condition: "Execute ONLY if P0-T01 determines 4ZAU is DFGin. If DFGout, SKIP this task."
---

# Task: Remove DFGout_aCout (3-State Switch)

## CONDITIONAL TASK

**Execute ONLY if P0-T01's output artifact
(`artifacts/verification/4zau_dfg_verification.json`) reports that 4ZAU is DFGin.**

If 4ZAU is DFGout, SKIP this task entirely. The project keeps 4 states with
mutant disclosure.

## Objective

Remove the `DFGout_aCout` conformational state from the entire codebase, switching
from a 4-state model (DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout) to a
3-state model (DFGin_aCin, DFGin_aCout, DFGout_aCin). This is required because
no genuine EGFR DFGout structures exist -- 4ZAU is actually DFGin.

## Context

If P0-T01 confirms 4ZAU is DFGin, the DFGout_aCout state has no valid structural
representative. Keeping it would mean generating molecules for a pocket geometry
that doesn't actually exist in EGFR. The 3-state model is scientifically more
honest and avoids generating compounds for a phantom pocket.

This is the largest single task in Phase 0, touching ~20 files. The changes are
mostly mechanical (find-and-remove), but the scope requires careful attention to
ensure nothing is missed.

## Prerequisites

- [ ] P0-T01 completed and confirms 4ZAU is DFGin
- [ ] P0-T06 completed (common annotation fixes applied first)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `artifacts/verification/4zau_dfg_verification.json` | Confirm DFGin classification |
| `src/statebind/processing/models.py` | ConformationalState enum definition |
| `src/statebind/processing/structures.py:200-226` | DFGout_aCout structures to remove |
| `src/statebind/structure/features.py:241-269` | DFGout_aCout features to remove |
| `src/statebind/generation/conditioning.py:115-135` | DFGout_aCout conditions to remove |
| `src/statebind/ml/vae.py:83-86` | VAEConfig.n_states default |
| `src/statebind/ml/vae_dataset.py:41-46` | DEFAULT_STATE_MAPPING |

## Files to Modify

### Source files

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/processing/structures.py` | 201-226 | Remove DFGout_aCout section (4ZAU + 5D41 StructureRecords) |
| `src/statebind/structure/features.py` | ~229-256* | Remove DFGout_aCout feature entries (4zau + 5d41) |
| `src/statebind/generation/conditioning.py` | 115-135 | Remove DFGout_aCout PocketCondition block |
| `src/statebind/ml/vae.py` | 84 | Change `default=4` to `default=3` |
| `src/statebind/ml/vae_dataset.py` | 45 | Remove `"DFGout_aCout": 3` from DEFAULT_STATE_MAPPING |
| `src/statebind/evaluation/docking_analysis.py` | 26 | Remove "DFGout_aCout" from `_STATES` list |

*Note: features.py line numbers will have shifted after T06 removed the 3iku entry.
Read the file fresh to find current line numbers.

### Config files

| File | Lines | Change Description |
|------|-------|-------------------|
| `configs/vae.yaml` | 21 | `n_states: 4` -> `n_states: 3` |
| `configs/vae_pre2010.yaml` | 12 | `n_states: 4` -> `n_states: 3` |
| `configs/vae_pre2015.yaml` | 12 | `n_states: 4` -> `n_states: 3` |
| `configs/docking.yaml` | 30 | Remove `DFGout_aCout: 4zau` line |

### Test files (9 files, 12 occurrences)

| File | Line(s) | Change Description |
|------|---------|-------------------|
| `tests/test_context.py` | 299 | Remove DFGout_aCout from test data dict |
| `tests/test_docking.py` | 296 | Remove from expected states set |
| `tests/test_docking.py` | 404 | Remove from test data dict |
| `tests/test_dynamics.py` | 191 | Remove from test data dict |
| `tests/test_dynamics.py` | 214 | Remove from test data dict |
| `tests/test_generation.py` | 128 | Remove DFGout_aCout condition access |
| `tests/test_generation.py` | 179 | Remove DFGout_aCout library reference |
| `tests/test_ranking.py` | 166 | Remove from test data dict |
| `tests/test_structure.py` | 271 | Remove DFGout_aCout comparison access |
| `tests/test_vae_integration.py` | 69 | Change state from "DFGout_aCout" to valid state |
| `tests/test_vae_integration.py` | 268 | Change `n_states=4` to `n_states=3` |
| `tests/test_vae_integration.py` | 298 | Change `n_states=4` to `n_states=3` |

## Implementation Steps

1. **Read T01 artifact** to confirm DFGin classification:
   ```bash
   cat artifacts/verification/4zau_dfg_verification.json
   ```
   If `classification.dfg_state` is NOT "DFGin", STOP and report that T07 is skipped.

2. **Remove DFGout_aCout StructureRecords** from `processing/structures.py`:
   - Delete the `# -- DFGout_aCout` section header and both records (4zau, 5d41)
   - These are at lines 201-226 (but may have shifted after T06's changes)
   - Read the file fresh to find exact current locations

3. **Remove DFGout_aCout features** from `structure/features.py`:
   - Delete the `# -- DFGout_aCout` section header and both entries (4zau, 5d41)
   - Note: line numbers have shifted after T06 removed 3iku

4. **Remove DFGout_aCout PocketCondition** from `generation/conditioning.py`:
   - Delete the `ConformationalState.DFGOUT_ACOUT.value: PocketCondition(...)` block
   - Note: line numbers are at 115-135 (may shift after T06's changes)

5. **Update VAE config defaults:**
   - `ml/vae.py:84`: Change `default=4` to `default=3`
   - `ml/vae_dataset.py:45`: Remove `"DFGout_aCout": 3` entry. Renumber remaining
     states: DFGin_aCin=0, DFGin_aCout=1, DFGout_aCin=2.

6. **Update evaluation code:**
   - `evaluation/docking_analysis.py:26`: Remove "DFGout_aCout" from `_STATES` list

7. **Search for other DFGout_aCout references** in source code:
   ```bash
   grep -rn "DFGout_aCout" src/
   grep -rn "DFGOUT_ACOUT" src/
   ```
   Fix any remaining references. Potential locations:
   - `processing/models.py`: The `ConformationalState` enum may have a
     `DFGOUT_ACOUT` variant. Remove it or keep with a deprecation comment.
   - `chemistry/docking.py`: May reference DFGout_aCout in docking state mapping
   - `dynamics/sequences.py`: May have a state alias
   - `structure/clustering.py`: May have state description
   - `context/features.py`: May reference in feature mapping

8. **Update all 3 VAE config files:**
   - `configs/vae.yaml:21`: `n_states: 3`
   - `configs/vae_pre2010.yaml:12`: `n_states: 3`
   - `configs/vae_pre2015.yaml:12`: `n_states: 3`

9. **Update docking config:**
   - `configs/docking.yaml:30`: Remove the `DFGout_aCout: 4zau` entry

10. **Update all test files** (see table above):
    For each file, read the current code around the listed line, understand the
    test's intent, and make the minimal change to remove DFGout_aCout while
    keeping the test valid.

    Common patterns:
    - Dicts with `"DFGout_aCout": <value>`: Remove the key-value pair
    - Sets with `"DFGout_aCout"`: Remove the element
    - Code accessing `conditions["DFGout_aCout"]`: Remove the access and any
      assertions about it
    - `n_states=4`: Change to `n_states=3`

11. **Final sweep:**
    ```bash
    grep -rn "DFGout_aCout\|DFGOUT_ACOUT\|n_states.*4\|n_states=4" src/ tests/ configs/
    ```
    Anything remaining should either be historical comments (acceptable) or
    missed references (fix them).

12. **Run full test suite:**
    ```bash
    pytest -v --tb=short
    ```
    All 646+ tests must pass. Some tests may need minor adjustments beyond
    what's listed if they construct objects with n_states=4 or reference
    DFGout_aCout indirectly.

## Verification

- [ ] `grep -rn "DFGout_aCout" src/ tests/ configs/` returns no active code
      (only comments/historical references if any)
- [ ] `grep -rn "DFGOUT_ACOUT" src/` returns no active code
- [ ] All VAE configs have `n_states: 3`
- [ ] `vae.py` default is `n_states: int = Field(default=3, ...)`
- [ ] `DEFAULT_STATE_MAPPING` has exactly 3 entries (indices 0, 1, 2)
- [ ] Docking config has no DFGout_aCout entry
- [ ] `pytest -v --tb=short` -- full test suite passes (646+)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- This is the largest task in Phase 0. Be methodical: work through files in the
  order listed, checking each change compiles before moving to the next.
- **Read each file fresh** before editing. T06 may have shifted line numbers.
- Follow StateBind conventions: typed Python, Pydantic v2 models.
- **The ConformationalState enum** in `processing/models.py` should have the
  `DFGOUT_ACOUT` variant removed. Check all enum value references first.
- **Do not change scoring weights or scoring logic.** The `state_specificity`
  scoring component should still work with 3 states.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **Enum removal cascade:** Removing `DFGOUT_ACOUT` from the enum may cause
  `AttributeError` in code that references `ConformationalState.DFGOUT_ACOUT`.
  Search exhaustively before removing.
- **DEFAULT_STATE_MAPPING renumbering:** After removing DFGout_aCout (index 3),
  the remaining states should map to indices 0, 1, 2. This is critical because
  the VAE uses these indices for one-hot encoding. **Existing VAE checkpoints
  will be incompatible** after this change -- that's why T08 (VAE retrain) exists.
- **Test data dicts:** Some tests construct dicts with all 4 states as test data.
  Removing the DFGout_aCout entry should be safe if the test logic doesn't depend
  on exactly 4 states. Read each test carefully.
- **features.py line shifts:** T06 removed the 3iku entry (~13 lines). The
  DFGout_aCout entries will have shifted upward. Always read the file fresh.
