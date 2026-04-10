# Decisions Needed

Last updated: 2026-04-09T22:30:00Z

## Pending Decisions

| # | Gate | Expected | Criterion | Action Needed |
|---|------|----------|-----------|---------------|
| 1 | G2 | week 4-5 | Ablation C Cohen's d >= 0.5 | After P1-T10: decide GO/PIVOT/NO-GO for ABL1 (Waves 4-5) |
| 2 | G3 | week 7 | REINVENT 4 produces 100+ valid docked molecules | After P1-T11: decide GO/CONDITIONAL/NO-GO |
| 3 | G4 | week 8 | ABL1 EF@10 > 1.0 for state-aware | After P1-T13: decide GO/CONDITIONAL/NO-GO |

## Decision Log

| # | Date | Decision | Gate | Outcome | Rationale |
|---|------|----------|------|---------|-----------|
| 1 | 2026-04-09 | 3-state model adopted | G0 (sub) | DFGin confirmed | 4ZAU=DFGin_aCin, 5D41=DFGin_aCout. No genuine EGFR DFGout structures exist. DFGout_aCout removed from codebase. |
| 2 | 2026-04-09 | Structural atlas verified | G0 | GO | 3iku removed (ParM, not EGFR). 3w2r promoted as DFGout_aCin representative with mutations ["T790M","L858R"]. 5D41 mutations corrected to ["L858R","T790M"]. All annotations match PDB records. |
| 3 | 2026-04-09 | MPNN scaffold split credible | G1 | GO | Scaffold R^2 = 0.5153 >= 0.35 threshold. Random R^2 was 0.69, degradation = 0.1863. MPNN remains in scoring function. |
