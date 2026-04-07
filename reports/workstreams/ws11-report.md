# WS11: GNINA Physics-Informed Docking -- Progress Report

## Status

- **State:** Not started
- **Last updated:** 2026-04-07T16:00:00+00:00
- **Session count:** 0
- **Test count added:** 0
- **Files created:** 0
- **Files modified:** 0

## Objective

Integrate GNINA as the top tier of the docking fallback chain, providing physics-based
binding scores and 3D binding poses for all candidates docked into each conformational
state's pocket. This activates 20% of scoring weight with real protein-ligand structural
modeling. See `workstreams/11-gnina-docking.md` for the full brief.

---

## Progress Log

(No sessions yet.)

---

## Current State

**What is done:**
- Workstream brief created (`workstreams/11-gnina-docking.md`)

**What is NOT done yet:**
- GNINA installation and verification
- Receptor preparation for each conformational state
- Docking wrapper (`chemistry/docking.py`)
- Scoring cascade integration (tier 0)
- State-specific docking analysis
- Docking config (`configs/docking.yaml`)
- Tests

---

## Next Steps

1. Verify GNINA availability on Bouchet cluster (`conda install -c conda-forge gnina`)
2. Prepare receptor PDBQT files for each conformational state
3. Implement docking wrapper in `chemistry/docking.py`
4. Integrate into scoring cascade in `ranking/scoring.py`
5. Build state-specific docking analysis in `evaluation/docking_analysis.py`
6. Write tests, verify known binder docking

---

## Handoff Notes

**To resume this workstream:**
1. Read `CLAUDE.md` (project rules)
2. Read `workstreams/11-gnina-docking.md` (workstream brief)
3. Read THIS file (you are here)
4. Pick up from "Next Steps" above

**DO NOT:**
- Modify `src/statebind/ml/` (model code is finalized)
- Modify `src/statebind/baselines/scoring.py` (baseline scoring is separate)
- Delete or weaken any existing tests
