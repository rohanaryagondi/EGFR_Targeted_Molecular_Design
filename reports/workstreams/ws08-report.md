# WS08: MPNN Affinity -- Progress Report

## Status

- **State:** Not started
- **Last updated:** 2026-03-28T18:00:00+00:00
- **Session count:** 0
- **Test count added:** 0
- **Files created:** 0
- **Files modified:** 0

## Objective

Create the MPNN data preparation pipeline (ChEMBL EGFR affinity data), the affinity
predictor adapter that loads a trained MPNN checkpoint, and the cascading fallback in
`ranking/scoring.py`: MPNN -> docking proxy (WS04) -> constant 0.5 stub. The MPNN
architecture already exists in `ml/mpnn.py`; this workstream creates integration code.

---

## Progress Log

_No sessions yet._

---

## Current State

**What is done:** Nothing.

**What is NOT done yet:**
- Create `scripts/prepare_mpnn_data.py`
- Create `src/statebind/ml/affinity_predictor.py` (adapter wrapping MPNN)
- Modify `src/statebind/ranking/scoring.py` (cascading fallback chain)
- Write 20+ tests for adapter and fallback logic
- Verify graceful fallback without trained checkpoint

**Blockers:** WS04 must be merged first (both modify `ranking/scoring.py`).

---

## Next Steps

1. Read workstream brief: `workstreams/08-mpnn-affinity.md`
2. Read INTERFACES.md Contract 4
3. Read current `ranking/scoring.py` (after WS04's changes)
4. Implement affinity predictor adapter
5. Wire cascading fallback: MPNN -> docking proxy -> stub
6. Create data preparation script
7. Write tests, verify all pass

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md`
2. Read `workstreams/08-mpnn-affinity.md`
3. Read this file
4. Pick up from "Next Steps" above

**DO NOT:**
- Run in parallel with WS04 (both touch `ranking/scoring.py`)
- Change `DEFAULT_WEIGHTS` without updating `SCORING_METHOD`
- Remove the docking proxy fallback (WS04's contribution)
