# Planner AI -- Department Rules

These rules apply to ALL agents in the Planner system (planner orchestrator,
phase leads, task agents, and reviewers). The planner orchestrator embeds
these rules into every subagent prompt.

---

## Mission

Transform the ReviewCohort's implementation plan into atomic, executable task
specifications for Claude Code agents. Work incrementally -- one phase at a time --
so planning adapts to empirical results and gate outcomes.

The Planner does NOT execute code. It produces **plans and task specifications**.
Separate Claude Code agents execute the tasks.

---

## Non-Negotiable Rules

### 1. NO CODE CHANGES -- DOCUMENTS ONLY

**The planner orchestrator and reviewer agents MUST NEVER modify the codebase.**

This means: no editing files in `src/`, `tests/`, `scripts/`, `configs/`, `data/`,
`artifacts/`, or any directory outside `IdeationDept/Planner/output/`. No running
`python`, `pytest`, `pip install`, or any command that modifies project state. No
creating scripts, no running computations, no git commits of code changes.

The planner's ONLY output is markdown documents (task specs, phase plans, dashboard
files) written to `IdeationDept/Planner/output/`.

Reading project files for context is allowed. Writing to them is not. Even if
instructed to "implement", "execute", or "do the work" -- the planner writes
documents describing the work. Separate Claude Code agents do the actual execution.

**Task agents** (spawned from task specs by the human operator or a Phase Lead)
DO modify the codebase -- that is their purpose. But task agents are separate
Claude Code sessions, not part of the Planner system.

### 2. Read-Only Access to Project Files

Planner and reviewer agents may READ project files for context:
- `src/statebind/` -- to understand current implementations
- `configs/` -- to understand parameters
- `artifacts/` -- to understand pipeline outputs
- `tests/` -- to understand test coverage
- `CLAUDE.md`, `CRITICAL.md` -- for project rules
- `IdeationDept/ReviewCohort/output/` -- for the review panel's findings
- `reports/` -- for workstream results

But never WRITE to any of these locations.

### 3. Write Access

All Planner system output goes to `IdeationDept/Planner/output/` and its
subdirectories only. The directory structure:

```
output/
├── phases/phase-NN-<name>/         # Phase plans + task specs
│   ├── phase-plan.md               # Phase overview + operator guide
│   └── task-NN-<name>/task-spec.md # Individual task specifications
├── logs/progress.md                # Master progress tracker
├── reviews/phase-NN/               # Reviewer output per phase
└── dashboard/                      # Human-facing status files
    ├── current-status.md
    ├── action-items.md
    └── decisions-needed.md
```

### 4. Source of Truth

The file `context/implementation-plan.md` is the authoritative source for what
needs to be built. All task specs must trace back to specific work items (P0-P21)
in that document.

### 5. Incremental Planning

The planner creates ONE phase at a time. It reads the current project state
(progress.md, actual codebase, test results, reviewer reports) before planning
the next phase. This ensures planning adapts to:
- Gate outcomes (G0-G5)
- Actual performance metrics (R^2, Cohen's d, etc.)
- Unexpected blockers or faster-than-expected progress

### 6. Task Specification Standards

Every task spec must contain ALL information a Claude Code agent needs to execute
independently:
- Exact file paths and line numbers
- What to change and why
- Prerequisites (what must exist before this task runs)
- Verification steps (how to confirm the task succeeded)
- Gotchas and edge cases

A task agent should never need to "figure out" what to do. The thinking happens
during planning; execution is mechanical.

### 7. Task Granularity

- A task should be completable in a single Claude Code session
- A task should touch a bounded set of files (ideally <10)
- A task should have a clear verification step (run tests, check output, etc.)
- A task should not require human judgment mid-execution
- If a task is too large, split it. If it's too small, merge with related work.

### 8. Document Conventions

All documents use YAML frontmatter:
```yaml
---
type: <phase-plan | task-spec | status-report | review-report>
created: <ISO date>
---
```

- Timestamps: Always UTC ISO format
- Task IDs: `P<phase>-T<number>` (e.g., `P0-T01`)
- File references: Use paths relative to the repo root
- Scores and metrics: Round to 4 decimal places

### 9. StateBind Project Rules

All agents in the Planner system must respect the StateBind project rules from
the root `CLAUDE.md` and `CRITICAL.md`. Key rules:
- Typed Python with `from __future__ import annotations`
- Pydantic v2 models for cross-module data
- Config-driven (YAML in `configs/`)
- No hard-coded paths (use `DataPaths`)
- Tests required for every new function (646+ must pass)
- Artifacts on disk (JSON with `generated_at` and `notes`)
- Optional deps (RDKit, scipy, torch) always have fallback paths
