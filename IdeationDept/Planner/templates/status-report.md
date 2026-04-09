---
type: status-report
date: <YYYY-MM-DDTHH:MM:SSZ>
phase: <current phase number and name>
author: <agent that wrote this, e.g., "Phase Lead" or task ID>
---

# Status Report: <date>

## Current Phase

<Phase number and name>

## Tasks Completed This Session

| Task ID | Task Name | Result | Notes |
|---------|-----------|--------|-------|
| <id> | <name> | PASS / PARTIAL / FAIL | <brief note> |

## Tasks In Progress

| Task ID | Task Name | Progress | Blockers |
|---------|-----------|----------|----------|
| <id> | <name> | <percentage or description> | <blocker or "None"> |

## Tasks Remaining

| Task ID | Task Name | Blocked By |
|---------|-----------|-----------|
| <id> | <name> | <dependency or "Ready"> |

## Blockers

<Any issues preventing progress. Be specific about what's blocked and why.>

1. <blocker description, affected task, suggested resolution>

## Gate Outcomes

<If any go/no-go gates were reached, report the metric and recommended outcome.
Final gate decisions are made by the human operator.>

| Gate | Metric | Value | Recommended Outcome |
|------|--------|-------|-------------------|
| <gate> | <metric> | <value> | GO / CONDITIONAL GO / NO-GO |

## Key Observations

<Anything unexpected or noteworthy discovered during execution. This helps the
planner orchestrator adapt future plans.>

- <observation 1>

## Next Steps

<What should happen next based on current progress.>

1. <next step>
