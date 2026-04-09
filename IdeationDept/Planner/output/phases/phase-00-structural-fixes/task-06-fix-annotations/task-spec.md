---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T06
task_name: "Fix Structural Annotations (Common)"
implementation_plan_ref: "P1: Fix Structural Annotations (common fixes for both 3-state and 4-state paths)"
status: pending
created: 2026-04-09T18:00:00Z
estimated_effort: "4-8 hours"
---

# Task: Fix Structural Annotations (Common)

## Objective

Fix three structural annotation errors that exist regardless of whether the
project uses 3 or 4 conformational states: (1) 3iku is not EGFR, (2) 3W2R is
mislabeled as wild-type, (3) 5D41 is mislabeled as wild-type. These are factual
errors that must be corrected for scientific integrity.

## Context

The ReviewCohort verified through PDB searches that:
- **3iku** is ParM (an E. coli protein), NOT EGFR. It should not be in the EGFR
  structural atlas at all. The docking config already works around this (uses 3w2r
  instead), but the atlas code still references 3iku.
- **3W2R** is a T790M/L858R double mutant, NOT wild-type. The `mutations_present`
  field is incorrectly `[]`.
- **5D41** is a L858R/T790M double mutant, NOT wild-type. Same issue.

These fixes are needed on BOTH the 3-state and 4-state paths. They are separated
from the 3-state switch (P0-T07) so they can proceed immediately after P0-T01
regardless of its outcome.

## Prerequisites

- [ ] P0-T01 completed (4ZAU conformation determined -- needed to know if 3iku
      replacement is into a state that will be removed in T07, but the common
      fixes are valid either way)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/processing/structures.py:130-230` | Full structural atlas definition |
| `src/statebind/structure/features.py:180-270` | Feature definitions for each PDB |
| `src/statebind/generation/conditioning.py:70-140` | Pocket conditions for each state |
| `configs/docking.yaml` | Docking config (already uses 3w2r, has 3iku comment) |
| `tests/test_structure.py:130-170` | Tests referencing 3iku |
| `tests/test_processing.py` | Tests for structure processing |
| `tests/test_generation.py` | Tests for generation conditioning |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/processing/structures.py` | 175-187 | Replace 3iku with a valid EGFR DFGout_aCin PDB |
| `src/statebind/processing/structures.py` | 196 | Fix 3W2R mutations `[]` -> `["T790M", "L858R"]` |
| `src/statebind/processing/structures.py` | 223 | Fix 5D41 mutations `[]` -> `["L858R", "T790M"]` |
| `src/statebind/structure/features.py` | 212-225 | Replace 3iku feature entry with new PDB |
| `src/statebind/generation/conditioning.py` | 96 | Replace representative_pdb="3iku" |
| `tests/test_structure.py` | 146, 158, 163 | Update 3iku references to new PDB |

## Implementation Steps

1. **Choose a replacement for 3iku** in the DFGout_aCin state:

   The docking config already uses **3w2r** as the DFGout_aCin representative
   (`configs/docking.yaml:29`). Since 3w2r is already in the atlas (line 188-199),
   the simplest fix is:
   - **Remove the 3iku StructureRecord entirely** from the atlas (lines 175-187)
   - **Promote 3w2r to representative** by setting `is_representative=True` on the
     3w2r record (it currently lacks this flag)
   - This avoids introducing a new PDB that hasn't been verified

   Alternatively, if 3w2r should not be representative (it's a mutant), research
   a genuine WT EGFR DFGout_aCin structure. However, the ReviewCohort found that
   "No WT EGFR DFGout exists" -- all DFGout structures carry T790M and/or L858R.
   So 3w2r (T790M/L858R) is the best available, and its mutations should be
   disclosed.

2. **Remove 3iku StructureRecord** from `structures.py`:

   Delete lines 175-187 (the full 3iku StructureRecord). Keep the
   `# -- DFGout_aCin` section header comment.

3. **Update 3w2r record** at lines 188-199:

   Add `is_representative=True` to the 3w2r StructureRecord. Also fix its
   mutations field:
   ```python
   StructureRecord(
       pdb_id="3w2r",
       resolution=2.35,
       chain="A",
       state=ConformationalState.DFGOUT_ACIN,
       ligand_id="W2R",
       ligand_bound=True,
       is_apo=False,
       mutations_present=["T790M", "L858R"],  # Fixed: was []
       is_representative=True,  # Added: promoted from 3iku
       notes="T790M/L858R EGFR with DFG-out and aC-helix in. Type-II inhibitor bound. "
             "Note: no WT EGFR DFGout structures exist in PDB.",
       provenance=Provenance(sources=["pdb", "klifs"], processing_date="2026-03-14"),
   ),
   ```

4. **Fix 5D41 mutations** at line 223:

   Change `mutations_present=[]` to `mutations_present=["L858R", "T790M"]`.
   Update the notes to mention the mutations:
   ```python
   mutations_present=["L858R", "T790M"],
   notes="L858R/T790M EGFR inactive conformation.",
   ```

5. **Fix 4ZAU mutations** at line 210 (while we're fixing annotations):

   4ZAU also has `mutations_present=[]`, but the ReviewCohort notes 4ZAU may
   have mutations too. Check the PDB record. If 4ZAU is WT, leave as-is. If
   mutant, fix accordingly. (P0-T01's verification script should check this.)

   **If uncertain:** Leave 4ZAU mutations as-is for now. T07 will either remove
   4ZAU entirely (3-state path) or it will be fixed during T07's detailed work
   (4-state path).

6. **Replace 3iku features** in `features.py`:

   At lines 212-225, replace the `"3iku"` key with `"3w2r"` (since 3w2r is now
   the representative). The feature values for 3w2r already exist at lines 226-239
   in the same file. So:
   - **Delete the 3iku entry** (lines 212-225)
   - The 3w2r entry already exists, so no new features need to be added
   - Verify that the DFGout_aCin section still has complete coverage

7. **Update conditioning** in `conditioning.py`:

   At line 96, change `representative_pdb="3iku"` to `representative_pdb="3w2r"`.
   The pocket descriptor values in lines 97-104 should be checked against the
   3w2r features in features.py for consistency.

8. **Update tests** in `test_structure.py`:

   - Line 146: `extract_features("3iku")` -> `extract_features("3w2r")`
   - Line 158: Same change
   - Line 163: Same change
   - Search for any other "3iku" references in the test file

9. **Search for other 3iku references** across the entire codebase:
   ```bash
   grep -r "3iku" src/ tests/ configs/
   ```
   Fix any remaining references. The `configs/docking.yaml:24-25` has a comment
   about 3iku -- update it to note that 3iku has been removed from the atlas.

10. **Run tests:**
    ```bash
    pytest tests/test_structure.py tests/test_processing.py tests/test_generation.py -v --tb=short
    pytest -v --tb=short  # full suite
    ```

## Verification

- [ ] No remaining references to "3iku" in `src/` (except possibly historical comments)
- [ ] 3w2r has `is_representative=True` and `mutations_present=["T790M", "L858R"]`
- [ ] 5D41 has `mutations_present=["L858R", "T790M"]`
- [ ] `conditioning.py` uses `representative_pdb="3w2r"` for DFGout_aCin
- [ ] `features.py` has no "3iku" entry; 3w2r features are intact
- [ ] `grep -r "3iku" src/ tests/ configs/` returns no active code references
- [ ] `pytest tests/test_structure.py tests/test_processing.py tests/test_generation.py -v` passes
- [ ] `pytest -v --tb=short` -- full test suite passes (646+)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- Follow StateBind conventions: typed Python, Pydantic v2 models.
- **Do not remove the DFGout_aCout state** in this task. That is P0-T07's job
  (conditional on T01 result). This task only fixes factual errors.
- When removing the 3iku record, be careful not to break the list structure
  (trailing commas, section comments).
- The 3w2r features in `features.py` already exist at lines 226-239. Do not
  duplicate them.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **3w2r is also a mutant** (T790M/L858R). This is scientifically correct to
  disclose but doesn't invalidate its use as a DFGout_aCin representative. The
  key point is that no WT EGFR DFGout structures exist. The paper will disclose
  this in the Methods section.
- **The `is_representative` flag** is used by other code to select default
  structures for each state. Make sure only one structure per state has this flag.
  Currently 3iku has it for DFGout_aCin; after removal, 3w2r should get it.
- **Features.py line numbers:** After removing the 3iku entry (13 lines), all
  subsequent line numbers in features.py will shift up by ~13 lines. This affects
  T07's line references for DFGout_aCout features.
- **The docking.yaml comment** at lines 24-25 says "3iku is not EGFR; 3w2r used
  instead." After this fix, update it to say "3iku was removed from atlas
  (was ParM, not EGFR). 3w2r is the DFGout_aCin representative."
