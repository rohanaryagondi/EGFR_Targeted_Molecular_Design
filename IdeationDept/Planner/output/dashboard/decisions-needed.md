# Decisions Needed

Last updated: 2026-04-09T22:30:00Z

## Pending Decisions

No decisions pending from Phase 0. All gates resolved.

Future gates (Phase 1+) will be added here as phases are planned and executed.

## Decision Log

| # | Date | Decision | Gate | Outcome | Rationale |
|---|------|----------|------|---------|-----------|
| 1 | 2026-04-09 | 3-state model adopted | G0 (sub) | DFGin confirmed | 4ZAU=DFGin_aCin, 5D41=DFGin_aCout. No genuine EGFR DFGout structures exist. DFGout_aCout removed from codebase. |
| 2 | 2026-04-09 | Structural atlas verified | G0 | GO | 3iku removed (ParM, not EGFR). 3w2r promoted as DFGout_aCin representative with mutations ["T790M","L858R"]. 5D41 mutations corrected to ["L858R","T790M"]. All annotations match PDB records. |
| 3 | 2026-04-09 | MPNN scaffold split credible | G1 | GO | Scaffold R^2 = 0.5153 >= 0.35 threshold. Random R^2 was 0.69, degradation = 0.1863. MPNN remains in scoring function. |
