---
type: phase-plan
phase: "Phase 0: Structural & Methodological Fixes"
implementation_plan_ref: "P0, P1, P2, P3, P4, P5"
created: 2026-04-09T18:00:00Z
status: completed
---

# Phase Plan: Structural & Methodological Fixes

## Phase Overview

Phase 0 fixes six publication-blocking issues that must be resolved before any
experiments (Phase 1+) can begin. These are: structural annotation errors in the
conformational atlas (3iku is not EGFR, 3W2R/5D41 have wrong mutation fields,
4ZAU's DFG classification is suspect), a temporal data leak (osimertinib in
reference binders), MPNN evaluation using random instead of scaffold split,
missing confidence intervals, vacuous SELFIES validity metrics, and the need
for a pre-registration document before ablation experiments.

The implementation plan states: "Nothing else starts until Phase 0 is complete."
This phase includes gates G0 (structural atlas verified) and G1 (MPNN scaffold
R^2 >= 0.35).

## Prerequisites

- [ ] Implementation plan read and approved (`context/implementation-plan.md`)
- [ ] No prior phases to complete (this is the first phase)

## Task Summary

| Task ID | Task Name | Effort | Dependencies | Wave | Conditional? | Status |
|---------|-----------|--------|-------------|------|-------------|--------|
| P0-T01 | Verify 4ZAU DFG Conformation | 2h | None | 1 | No | completed |
| P0-T02 | Fix Osimertinib Reference Leakage | 15min | None | 1 | No | completed |
| P0-T03 | MPNN Scaffold + Temporal Split (Code) | 2-3d | None | 1 | No | completed |
| P0-T04 | Bootstrap CIs + BEDROC | 0.5-1d | None | 1 | No | completed |
| P0-T05 | MPNN Scaffold Split Evaluation (GPU) | 2-4h | T03 | 2 | No | completed |
| P0-T06 | Fix Structural Annotations (Common) | 4-8h | T01 | 2 | No | completed |
| P0-T07 | Remove DFGout_aCout (3-State Switch) | 1-1.5d | T01=DFGin, T06 | 3 | Executed (DFGin confirmed) | completed |
| P0-T08 | VAE Retrain (3-State) | 30min GPU | T07 | 4 | Executed (3-state) | completed |
| P0-T09 | Pre-Registration Document | 2-4h | All prior settled | 4 | No | completed |

## Execution Order

```
Wave 1: [T01, T02, T03, T04]  -- all independent, run in parallel
         │          │
Wave 2: [T06]      [T05]      -- T06 depends on T01; T05 depends on T03
         │
Wave 3: [T07]                 -- CONDITIONAL: only if T01 confirms DFGin
         │                       depends on T06
Wave 4: [T08]  [T09]          -- T08 CONDITIONAL: only if T07 ran
                                  T09 depends on all prior being settled
```

### Branching Logic (4-State vs 3-State)

P0-T01 determines whether 4ZAU is DFGin or DFGout:

- **DFGin confirmed (expected, ~60%):** Execute T07 (remove DFGout_aCout) and T08
  (VAE retrain). This is the 3-state path.
- **DFGout confirmed (~40%):** SKIP T07 and T08. Keep 4 states with mutant
  disclosure. T06's common annotation fixes still apply.

The Phase Lead reads T01's output artifact (`artifacts/verification/4zau_dfg_verification.json`)
to make this dispatch decision.

## Operator Guide

### Option A: Phase Lead (Recommended)

Wave 1 has 4 parallel tasks, so a Phase Lead is recommended.

1. Navigate to the repo root: `cd /home/rag88/projects/statebind/repo`
2. Launch Claude Code: `claude`
3. Say:

   > You are a Phase Lead for Phase 0: Structural & Methodological Fixes.
   > Read `IdeationDept/Planner/output/phases/phase-00-structural-fixes/phase-plan.md`
   > and all task-spec.md files in subdirectories. Execute the tasks in wave order,
   > launching Wave 1 tasks (T01, T02, T03, T04) simultaneously using the Agent tool.
   > After Wave 1, read T01's output and launch Wave 2 tasks. Handle the 3-state vs
   > 4-state branching based on T01 results. Update
   > `IdeationDept/Planner/output/logs/progress.md` after each task completes.

4. Monitor progress. The Phase Lead will report when all tasks are done.
5. After completion, return to the Planner AI and say "Review phase 0".

### Option B: Direct Execution (Manual Control)

1. **Wave 1** (run in 4 separate terminals):
   - T01: `cd /home/rag88/projects/statebind/repo && claude` then say:
     "Execute task P0-T01: Read `IdeationDept/Planner/output/phases/phase-00-structural-fixes/task-01-verify-4zau/task-spec.md` and follow the instructions."
   - T02: Same pattern with task-02-fix-osimertinib
   - T03: Same pattern with task-03-scaffold-split
   - T04: Same pattern with task-04-bootstrap-bedroc
2. **Wave 2** (after Wave 1 completes):
   - T05: task-05-mpnn-evaluation (requires T03 done)
   - T06: task-06-fix-annotations (requires T01 done)
3. **Wave 3** (only if T01 confirmed DFGin):
   - T07: task-07-3state-switch (requires T06 done)
4. **Wave 4** (after Wave 3 or after skipping T07):
   - T08: task-08-vae-retrain (only if T07 ran)
   - T09: task-09-preregistration
5. After all tasks complete, return to the Planner AI and say "Review phase 0".

## Phase Lead Instructions

You are the Phase Lead for Phase 0: Structural & Methodological Fixes. Your job
is to execute all 9 tasks (7 unconditional, 2 conditional) in the correct order.

1. Read this phase-plan.md and all task-spec.md files in subdirectories
2. Execute tasks by wave:
   - **Wave 1**: Launch T01, T02, T03, T04 in parallel using 4 Agent tool calls
     in a single message. Each agent gets the full task-spec.md contents plus
     StateBind project rules.
   - **Wave 2**: After Wave 1 completes:
     - Read T01's output artifact (`artifacts/verification/4zau_dfg_verification.json`)
       to determine DFGin vs DFGout
     - Launch T05 (depends on T03) and T06 (depends on T01) in parallel
   - **Wave 3**: If T01 confirmed DFGin, launch T07 (depends on T06)
     If T01 confirmed DFGout, SKIP T07 and T08 — proceed directly to T09
   - **Wave 4**: If T07 ran, launch T08 (VAE retrain). Then launch T09.
     If T07 was skipped, launch T09 directly.
3. For each task agent, provide:
   - The full contents of the task's task-spec.md
   - The instruction to follow StateBind conventions (typed Python, Pydantic v2,
     config-driven, no hard-coded paths, tests required)
   - Instructions to update `IdeationDept/Planner/output/logs/progress.md`
     upon completion
4. After each task completes, verify success by reading the agent's output
5. Update `../../logs/progress.md` with task completion status
6. Report a summary when all tasks are done, including:
   - 4ZAU conformation result (DFGin/DFGout) and 3-state vs 4-state decision
   - MPNN scaffold R^2 value and G1 gate outcome
   - Number of tests passing
   - Any issues encountered

## Reviewer Checklist

### Structural/Scientific

- [ ] 4ZAU DFG measurements verified against published literature
      (Yun et al., PNAS 2008; Park et al., JACS 2015)
- [ ] 3iku replacement is scientifically correct (new PDB is EGFR DFGout_aCin)
- [ ] 3W2R mutation annotations `["T790M", "L858R"]` match PDB records
- [ ] 5D41 mutation annotations `["L858R", "T790M"]` match PDB records
- [ ] If 3-state: DFGout_aCout removal is thorough across all files
- [ ] ConformationalState enum consistent with all downstream consumers

### Methodological/Code

- [ ] scaffold_split groups by Bemis-Murcko generic scaffold correctly
- [ ] temporal_split uses activity year correctly
- [ ] Backward compatibility preserved (split_type="random" produces same results)
- [ ] BCa bootstrap correctly implements jackknife acceleration + bias correction
- [ ] BEDROC uses alpha=20 parameter and handles edge cases
- [ ] Pre-registration document contains all required elements

### Test Verification

- [ ] All pre-existing tests still pass (646+ baseline)
- [ ] New tests added for scaffold_split, temporal_split, BCa bootstrap, BEDROC
- [ ] No tests removed or skipped without justification

### Gate Evaluation

- [ ] G0: All PDB annotations verified against PDB records — report outcome
- [ ] G1: MPNN scaffold-split R^2 measured — report value against thresholds:
  - >= 0.35: GO
  - [0.20, 0.35): CONDITIONAL GO (reframe MPNN as supplementary)
  - < 0.20: NO-GO (drop MPNN from scoring)

## Go/No-Go Gates in This Phase

| Gate | Criterion | GO | CONDITIONAL GO | NO-GO |
|------|-----------|-----|----------------|-------|
| G0 (week 1) | Structural atlas verified | All annotations match PDB | -- | Classification scheme invalid (<5%) |
| G1 (week 2) | MPNN scaffold R^2 | >= 0.35 | [0.20, 0.35): "supplementary signal" | < 0.20: drop MPNN (~10%) |

## Success Criteria

- [x] All PDB annotations verified and corrected
- [x] 3-state model adopted (4ZAU=DFGin_aCin, 5D41=DFGin_aCout, DFGout_aCout removed)
- [x] Osimertinib removed from reference binders
- [x] Scaffold + temporal split implemented with tests (7 new tests)
- [x] MPNN R^2 evaluated with scaffold split (G1 GO: R^2 = 0.5153)
- [x] BCa bootstrap + BEDROC implemented with tests (19 new tests)
- [x] Pre-registration document committed (commit 9e7cf96)
- [x] 669 tests pass (was 646; 23 new tests added, 0 failures)
- [x] Progress tracker updated for all tasks
