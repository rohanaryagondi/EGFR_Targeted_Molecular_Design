# WS04: Docking Proxy -- Progress Report

## Status

- **State:** Not started
- **Last updated:** 2026-03-28T18:00:00+00:00
- **Session count:** 0
- **Test count added:** 0
- **Files created:** 0
- **Files modified:** 0

## Objective

Create a lightweight MLP docking proxy trained on embedded SAR data from known EGFR
inhibitors. The proxy replaces the constant-0.5 docking stub with a function that
returns varied, chemically meaningful scores. It sits in the cascading fallback chain:
MPNN (WS08) -> Docking Proxy (this WS) -> constant 0.5 stub.

---

## Progress Log

_No sessions yet._

---

## Current State

**What is done:** Nothing.

**What is NOT done yet:**
- Create `src/statebind/chemistry/docking_proxy.py` (MLP model + inference)
- Create `src/statebind/chemistry/docking_data.py` (embedded training data)
- Modify `src/statebind/ranking/scoring.py` (fallback chain)
- Write 15+ tests
- Verify proxy returns varied scores for different inputs

**Blockers:** None. WS02 is merged; this workstream can begin.

---

## Next Steps

1. Read workstream brief: `workstreams/04-docking-proxy.md`
2. Read current scoring stub: `src/statebind/baselines/scoring.py:135-149`
3. Read INTERFACES.md Contract 2
4. Implement docking proxy MLP
5. Wire into scoring fallback chain
6. Write tests, verify all pass

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md`
2. Read `workstreams/04-docking-proxy.md`
3. Read this file
4. Pick up from "Next Steps" above

**DO NOT:**
- Modify `baselines/scoring.py` reference binders (lines 59-66)
- Change `DEFAULT_WEIGHTS` in `ranking/scoring.py`
- Run in parallel with WS08 (both touch `ranking/scoring.py`)
