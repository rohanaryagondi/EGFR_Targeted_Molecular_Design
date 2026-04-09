---
type: phase-plan
phase: <phase number and name, e.g., "Phase 0: Structural & Methodological Fixes">
implementation_plan_ref: <work items covered, e.g., "P0, P1, P2, P3, P4, P5">
created: <YYYY-MM-DDTHH:MM:SSZ>
status: pending
---

# Phase Plan: <phase name>

## Phase Overview

<3-5 sentences: what this phase accomplishes, why it's the current priority,
and what must be true before the next phase can be planned.>

## Prerequisites

<What must be completed before this phase starts. Reference prior phases,
gate outcomes, or external requirements.>

- [ ] <prerequisite 1>
- [ ] <prerequisite 2>

## Task Summary

| Task ID | Task Name | Effort | Dependencies | Wave | Status |
|---------|-----------|--------|-------------|------|--------|
| P0-T01 | <name> | <est.> | None | 1 | pending |
| P0-T02 | <name> | <est.> | None | 1 | pending |
| P0-T03 | <name> | <est.> | P0-T01 | 2 | pending |

## Execution Order

<Visual dependency diagram showing which tasks can run in parallel (same wave)
and which must be sequential.>

```
Wave 1: [T01, T02]  -- independent, run in parallel
         │
Wave 2: [T03]       -- depends on T01
         │
Wave 3: [T04, T05]  -- depend on T03, independent of each other
```

## Operator Guide

<Step-by-step instructions for the human operator. This should be followable
by someone who hasn't read the implementation plan.>

### Option A: Phase Lead (Recommended for 3+ Parallel Tasks)

1. Navigate to: `cd IdeationDept/Planner/output/phases/phase-NN-<name>/`
2. Launch Claude Code: `claude`
3. Say: "You are a Phase Lead. Read phase-plan.md and all task-spec.md files
   in this directory. Execute the tasks in wave order, launching parallel
   tasks simultaneously using the Agent tool. Update progress.md after each
   task completes."
4. Monitor progress. The Phase Lead will report when all tasks are done.
5. After completion, return to the Planner AI and say "Review phase N".

### Option B: Direct Execution (For < 3 Tasks or Manual Control)

1. **Wave 1:**
   - Task P0-T01: `cd <repo-root> && claude` then say "<task instruction>"
   - Task P0-T02: (can run in a separate terminal simultaneously)
2. **Wave 2** (after Wave 1 completes):
   - Task P0-T03: `cd <repo-root> && claude` then say "<task instruction>"
3. After all tasks complete, return to the Planner AI and say "Review phase N".

## Phase Lead Instructions

<Only include this section if the phase has 3+ parallel tasks. These instructions
are for the Phase Lead agent, not the human operator.>

You are the Phase Lead for <phase name>. Your job is to execute all tasks in
this phase in the correct order.

1. Read this phase-plan.md and all task-spec.md files in this directory
2. Execute tasks by wave:
   - **Wave 1**: Launch tasks <list> in parallel using multiple Agent tool calls
     in a single message
   - **Wave 2**: After Wave 1 completes, launch tasks <list>
   - Continue until all waves complete
3. For each task agent, provide:
   - The full contents of the task's task-spec.md
   - The StateBind project rules from CLAUDE.md
   - Instructions to update progress.md upon completion
4. After each task completes, verify success by reading the agent's output
5. Update `../../logs/progress.md` with task completion status
6. Report a summary when all tasks are done

## Reviewer Checklist

<What the reviewer should verify after this phase completes.>

- [ ] <check 1, e.g., "All PDB annotations match actual PDB records">
- [ ] <check 2, e.g., "All 646+ existing tests still pass">
- [ ] <check 3, e.g., "New tests added for new functions">

## Go/No-Go Gates in This Phase

<List any gates from the implementation plan that fall within this phase.
Include the criteria and what happens for each outcome.>

| Gate | Criterion | GO | CONDITIONAL GO | NO-GO |
|------|-----------|-----|----------------|-------|
| G0 | <criterion> | <action> | <action> | <action> |

## Success Criteria

<How to know this phase is truly done. All of these must be true.>

- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>
