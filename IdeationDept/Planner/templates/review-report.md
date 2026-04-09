---
type: review-report
date: <YYYY-MM-DDTHH:MM:SSZ>
phase: <phase number and name reviewed>
reviewer: Reviewer AI
---

# Review Report: Phase <N> -- <Phase Name>

## Review Summary

<3-5 sentences: overall assessment of the phase. Did it accomplish its goals?
Are the changes correct and complete?>

## Task-by-Task Assessment

### Task <ID>: <Name>

- **Status:** PASS / PARTIAL / FAIL
- **Spec compliance:** Did the changes match the task-spec.md?
- **Findings:**
  - <finding 1: what was done well or what's wrong>
  - <finding 2>
- **Files inspected:**
  - `<path>:<lines>` -- <observation>
- **Suggested fixes** (if PARTIAL or FAIL):
  - <fix 1>

<Repeat for each task in the phase>

## Test Results

```
<paste pytest output summary here>
```

- **Total tests:** <number>
- **Passed:** <number>
- **Failed:** <number>
- **New tests added:** <number>
- **Tests removed:** <number> (should be 0 unless justified)
- **Baseline maintained:** YES / NO (646+ tests must pass)

## Implementation Plan Compliance

<Check each relevant work item from the implementation plan against what was
actually implemented.>

| Work Item | Criterion | Met? | Notes |
|-----------|-----------|------|-------|
| P0 | <criterion from impl plan> | YES / NO / PARTIAL | <notes> |

## Go/No-Go Gate Evaluation

<If this phase includes gates, evaluate them against the criteria.>

| Gate | Criterion | Measured Value | Outcome | Notes |
|------|-----------|---------------|---------|-------|
| G0 | Structural atlas verified | <value> | GO / NO-GO | <notes> |

**Gate decisions require human confirmation.** These findings are recommendations,
not final decisions.

## Issues Found

<List all issues, ordered by severity.>

| # | Severity | Description | File | Suggested Fix |
|---|----------|-------------|------|--------------|
| 1 | HIGH / MEDIUM / LOW | <description> | `<path>:<line>` | <fix> |

## Recommendations

<Overall recommendations for next steps.>

1. <recommendation 1>
2. <recommendation 2>

## Dashboard Updates

<Summary of updates made to dashboard files.>

- **current-status.md:** <what was updated>
- **action-items.md:** <items added, if any>
- **decisions-needed.md:** <decisions added, if any>
