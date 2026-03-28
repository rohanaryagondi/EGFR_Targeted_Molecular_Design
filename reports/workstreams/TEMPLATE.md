# WS{NN}: {Name} -- Progress Report

<!--
  INSTRUCTIONS FOR AI AGENTS:

  This is your living document. Update it continuously as you work -- after every
  major step, not just at the end. If your context window compacts or you are
  replaced by another agent, this file is the primary handoff mechanism.

  Rules:
  1. Update AFTER each meaningful action (file created, test written, decision made).
  2. Newest log entries go at the TOP of the Progress Log section.
  3. Keep the "Current State" and "Next Steps" sections always accurate.
  4. Write for a stranger: assume the reader has CLAUDE.md but no other context.
  5. Include file:line references so the next agent can navigate instantly.
  6. Never delete log entries -- only append.
  7. If you hit a blocker, document it in "Current State" before stopping.
-->

## Status

- **State:** Not started | In progress | Complete
- **Last updated:** {UTC ISO timestamp}
- **Session count:** {n}
- **Test count added:** {number}
- **Files created:** {number}
- **Files modified:** {number}

## Objective

{One-paragraph summary of what this workstream achieves and why it matters to the
StateBind pipeline. Reference the workstream brief for full details.}

---

## Progress Log

<!-- Newest entries first. Each session gets its own heading. -->

### Session {n} -- {YYYY-MM-DD}

#### Completed
- {What was done, with file paths and line numbers}
- Example: Created `src/statebind/chemistry/fingerprints.py` (Morgan fingerprint wrapper, 145 lines)

#### Decisions Made
- {Why you chose approach X over Y, with rationale}
- Example: Used radius=2 for Morgan fingerprints (standard ECFP4, matches literature)

#### Issues Encountered
- {Problems hit, root cause, and resolution}
- Example: `torch_geometric` NNConv requires edge_attr -- added edge feature projection at `ml/mpnn.py:87`

#### Tests Written
- {Test file, count, what's covered}
- Example: `tests/test_chemistry.py` -- 12 tests covering fingerprint generation, similarity, edge cases

---

## Current State

<!-- Always keep this section up to date. This is what a replacement agent reads first. -->

**What is done:**
- {Bulleted list of completed deliverables}

**What is in progress:**
- {Current task, how far along, what remains}

**What is NOT done yet:**
- {Remaining tasks from the workstream brief}

**Blockers (if any):**
- {Anything preventing progress}

---

## Next Steps

<!-- Ordered list of what to do next. A replacement agent starts here. -->

1. {Next immediate action}
2. {Following action}
3. {Final action before Definition of Done}

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `path/to/file.py` | {Brief description} | {n} |

## Files Modified

| File | What Changed | Lines Changed |
|------|-------------|---------------|
| `path/to/file.py` | {Brief description} | +{n}/-{n} |

## Tests

| Test File | Tests Added | What's Covered |
|-----------|-------------|----------------|
| `tests/test_foo.py` | {n} | {Brief description} |

---

## Architecture Decisions

<!-- Non-obvious choices that future agents or reviewers need to understand. -->

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| {What you chose} | {What you rejected} | {Why} |

---

## Handoff Notes

<!--
  If your context compacts or you are replaced, the next agent reads this section
  to get oriented. Keep it brutally specific.
-->

**To resume this workstream:**
1. Read `CLAUDE.md` (project rules)
2. Read `workstreams/{NN}-{name}.md` (workstream brief)
3. Read THIS file (you are here)
4. Pick up from "Next Steps" above

**Critical context not in the code:**
- {Anything the next agent needs to know that isn't obvious from reading source files}

**DO NOT:**
- {Things the next agent should avoid -- e.g., "Do not modify ranking/scoring.py, that's WS02's job"}
