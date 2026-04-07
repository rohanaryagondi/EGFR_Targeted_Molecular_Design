# WS13: Retrospective Time-Split Validation -- Progress Report

## Status

- **State:** Not started
- **Last updated:** 2026-04-07T16:00:00+00:00
- **Session count:** 0
- **Test count added:** 0
- **Files created:** 0
- **Files modified:** 0

## Objective

Validate the pipeline retrospectively by training on pre-cutoff data (2010, 2015) and
testing whether it identifies molecules resembling drugs approved after the cutoff. This
is the strongest validation strategy available without wet lab work. See
`workstreams/13-retrospective-validation.md` for the full brief.

---

## Progress Log

(No sessions yet.)

---

## Current State

**What is done:**
- Workstream brief created (`workstreams/13-retrospective-validation.md`)

**What is NOT done yet:**
- Time-split dataset creation from ChEMBL
- Retrospective pipeline execution script
- MPNN retraining on restricted data
- Retrospective metrics module (`evaluation/retrospective.py`)
- Config file (`configs/retrospective.yaml`)
- Tests

---

## Next Steps

1. Query ChEMBL for all EGFR compounds with publication dates
2. Build time-split datasets for 2010 and 2015 cutoffs
3. Identify held-out "future drugs" (osimertinib, afatinib, lazertinib, etc.)
4. Create `scripts/run_retrospective_validation.py` pipeline wrapper
5. Retrain MPNN on pre-cutoff data (2 SLURM jobs)
6. Compute retrospective metrics and compare pipelines
7. Write tests, verify no data leakage

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md` (project rules)
2. Read `workstreams/13-retrospective-validation.md` (workstream brief)
3. Read THIS file (you are here)
4. Pick up from "Next Steps" above

**DO NOT:**
- Modify model architectures (only retrain with different data)
- Change scoring weights (same weights for fair comparison)
- Cherry-pick results (report all findings honestly)
- Delete or weaken any existing tests
