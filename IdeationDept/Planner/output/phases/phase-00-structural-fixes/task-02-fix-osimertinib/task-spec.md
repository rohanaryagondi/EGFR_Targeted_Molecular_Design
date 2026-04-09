---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T02
task_name: "Fix Osimertinib Reference Leakage"
implementation_plan_ref: "P2: Fix Osimertinib Reference Leakage"
status: completed
created: 2026-04-09T18:00:00Z
estimated_effort: "15 minutes"
---

# Task: Fix Osimertinib Reference Leakage

## Objective

Remove osimertinib from the `_REFERENCE_BINDERS` list in `baselines/scoring.py`
to eliminate a temporal data leak. Osimertinib (approved 2015/2017) is used as a
"future drug" in retrospective evaluation, so including it in the reference set
used to compute similarity scores contaminates the baseline scoring.

## Context

The retrospective evaluation framework tests whether the pipeline can rediscover
drugs approved after a cutoff date. Osimertinib is one of those future drugs.
Including it in `_REFERENCE_BINDERS` means the scoring function already "knows"
about the drug it's supposed to predict, creating a circular evaluation.

The implementation plan flags this as a 15-minute fix with no dependencies.

## Prerequisites

- [ ] No prerequisites (independent task)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `src/statebind/baselines/scoring.py:55-70` | Current `_REFERENCE_BINDERS` definition |
| `CRITICAL.md` | Warning about modifying `_REFERENCE_BINDERS` (re-run pipeline) |
| `tests/test_baselines.py` | Tests that may reference the binder count |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `src/statebind/baselines/scoring.py` | 62-63 | Remove osimertinib SMILES entry from `_REFERENCE_BINDERS` |

## Implementation Steps

1. **Open `src/statebind/baselines/scoring.py`** and locate lines 57-64:
   ```python
   _REFERENCE_BINDERS = [
       # Erlotinib
       "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
       # Gefitinib
       "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
       # Osimertinib
       "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
   ]
   ```

2. **Remove lines 62-63** (the `# Osimertinib` comment and its SMILES string):
   ```python
   _REFERENCE_BINDERS = [
       # Erlotinib
       "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
       # Gefitinib
       "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
   ]
   ```

3. **Check tests** in `tests/test_baselines.py` for any assertions on the number
   of reference binders (e.g., `len(_REFERENCE_BINDERS) == 3`). If found, update
   to expect 2.

4. **Run tests:**
   ```bash
   pytest tests/test_baselines.py -v --tb=short
   ```

## Verification

- [ ] `_REFERENCE_BINDERS` contains exactly 2 entries (erlotinib, gefitinib)
- [ ] No remaining references to osimertinib in `_REFERENCE_BINDERS`
- [ ] `pytest tests/test_baselines.py -v` passes
- [ ] `pytest -v --tb=short` -- full test suite passes (646+)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion

## Agent Instructions

- This is a trivial, surgical edit. Do NOT change anything else in the file.
- The `CRITICAL.md` notes that modifying `_REFERENCE_BINDERS` requires re-running
  the full pipeline. This re-run will happen later (after all Phase 0 fixes).
  For now, just make the code change.
- Follow StateBind conventions: no other changes beyond the specified edit.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status.

## Notes and Gotchas

- **Do not re-run the pipeline** after this change alone. The pipeline will be
  re-run after all Phase 0 structural fixes are complete.
- **The trailing comma** after gefitinib's SMILES is fine (Python allows it).
- **`CRITICAL.md` warning:** "Do not modify `_REFERENCE_BINDERS` without
  re-running the full pipeline (`baselines/scoring.py:57-66`)." This is noted --
  the re-run will happen in a later task.
