---
phase: <phase number and name, e.g., "Phase 0: Structural & Methodological Fixes">
task_id: <e.g., P0-T01>
task_name: <descriptive name>
implementation_plan_ref: <which work item(s) this implements, e.g., "P0: Verify 4ZAU DFG Conformation">
status: pending
created: <YYYY-MM-DDTHH:MM:SSZ>
estimated_effort: <hours or days>
---

# Task: <task_name>

## Objective

<1-3 sentences: what this task accomplishes and why it matters. Reference the
implementation plan item.>

## Context

<Why this matters in the bigger picture. What happens if this task isn't done or
is done incorrectly. Reference the implementation plan's rationale.>

## Prerequisites

<What must be completed before this task can start. Reference specific task IDs
if applicable.>

- [ ] <prerequisite 1, e.g., "P0-T01 completed (4ZAU conformation determined)">
- [ ] <prerequisite 2>

## Files to Read (Context)

<Files the executing agent should read to understand the surrounding code and
conventions. Include paths relative to repo root.>

| File | Why Read It |
|------|------------|
| `<path>` | <reason> |

## Files to Modify

<Exact files, line numbers, and what to change. Line numbers should be verified
at planning time by the planner orchestrator.>

| File | Lines | Change Description |
|------|-------|-------------------|
| `<path>` | <line range> | <what to change> |

## Implementation Steps

<Numbered, specific steps. Each step should be unambiguous enough that the
executing agent doesn't need to make judgment calls.>

1. <step 1>
2. <step 2>
3. ...

## Verification

<How to confirm the task succeeded. Be specific about commands to run, output
to check, and what "success" looks like.>

- [ ] <verification step 1, e.g., "Run `pytest tests/test_structure.py -v` -- all tests pass">
- [ ] <verification step 2, e.g., "Run `pytest -v --tb=short` -- 646+ tests pass, no regressions">
- [ ] <verification step 3>

## Agent Instructions

<Specific instructions for the Claude Code agent executing this task. Include
any StateBind conventions that are particularly relevant.>

- Follow StateBind conventions: typed Python, Pydantic v2, config-driven
- <additional instruction>
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status

## Notes and Gotchas

<Anything non-obvious that could trip up the executing agent. Edge cases,
known issues, things that look wrong but are intentional, etc.>

- <gotcha 1>
- <gotcha 2>
