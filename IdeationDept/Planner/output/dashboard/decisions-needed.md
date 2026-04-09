# Decisions Needed

Last updated: 2026-04-09T18:00:00Z

## Pending Decisions

### 1. 3-State vs 4-State Model (Gate G0 sub-decision)

**Status:** Awaiting P0-T01 (4ZAU DFG verification)
**Expected:** Week 1
**Impact:** Determines whether T07 and T08 execute

| 4ZAU Result | Model | Action |
|-------------|-------|--------|
| DFGin (expected, ~60%) | 3-state | Execute T07 (remove DFGout_aCout) + T08 (VAE retrain) |
| DFGout (~40%) | 4-state | Skip T07 + T08; keep 4 states with mutant disclosure |

This is handled automatically by the Phase Lead but should be confirmed by the operator.

### 2. Gate G0: Structural Atlas Verification

**Status:** Awaiting T01, T06, and possibly T07
**Expected:** Week 1
**Impact:** Phase 1 is blocked until G0 passes

| Outcome | Probability | Action |
|---------|------------|--------|
| PASS: All annotations match PDB | ~95% | Proceed to Phase 1 |
| FAIL: Classification scheme invalid | <5% | Stop and rethink project thesis |

### 3. Gate G1: MPNN Scaffold Split R^2

**Status:** Awaiting T03 (code) + T05 (GPU evaluation)
**Expected:** Week 2
**Impact:** Determines MPNN role in scoring function

| R^2 | Outcome | Action |
|-----|---------|--------|
| >= 0.35 | GO | MPNN stays in scoring |
| [0.20, 0.35) | CONDITIONAL GO | Reframe as supplementary signal |
| < 0.20 | NO-GO (~10%) | Drop MPNN from scoring |

CONDITIONAL GO and NO-GO require scoring weight changes -- deferred to Phase 1 planning.

## Decision Log

| # | Date | Decision | Gate | Outcome | Rationale |
|---|------|----------|------|---------|-----------|
| -- | -- | No decisions recorded yet | -- | -- | -- |
