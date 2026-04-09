# Planner AI

The Planner AI transforms the ReviewCohort's implementation plan into atomic,
executable task specifications for Claude Code agents. It works incrementally --
one phase at a time -- so it can adapt to empirical results and gate outcomes.

## Quick Start

```bash
cd IdeationDept/Planner/agents/planner && claude
```

Then say: **"Plan out the next phase"**

The Planner will read the implementation plan, check current progress, and produce
a phase directory with task specs and an operator guide.

## How It Works

```
You say "Plan out the next phase"
        │
        ▼
Planner reads implementation plan + current progress
        │
        ▼
Planner produces:
  output/phases/phase-NN-<name>/
    ├── phase-plan.md          ← read this: your operator guide
    └── task-NN-<name>/
        └── task-spec.md       ← one per task, self-contained
        │
        ▼
You execute tasks (following the operator guide in phase-plan.md)
        │
        ▼
You say "Review phase N"
        │
        ▼
Reviewer checks the work, updates dashboard
        │
        ▼
You check dashboard, make gate decisions
        │
        ▼
You say "Plan out the next phase" (repeat)
```

## Directory Structure

```
Planner/
├── CLAUDE.md                    # Department rules (all agents follow these)
├── README.md                    # This file
├── agents/
│   ├── planner/CLAUDE.md        # Planner orchestrator (you interact with this)
│   └── reviewer/CLAUDE.md       # Reviewer agent template
├── context/
│   └── implementation-plan.md   # Copy of ReviewCohort's final plan (source of truth)
├── templates/
│   ├── task-spec.md             # Template: individual task specification
│   ├── phase-plan.md            # Template: phase-level overview + operator guide
│   ├── status-report.md         # Template: progress updates from task agents
│   └── review-report.md         # Template: reviewer output
└── output/                      # Everything the Planner produces
    ├── phases/                  # Phase plans (created on demand)
    │   └── phase-NN-<name>/
    │       ├── phase-plan.md
    │       └── task-NN-<name>/
    │           └── task-spec.md
    ├── logs/
    │   └── progress.md          # Master progress tracker
    ├── reviews/
    │   └── phase-NN/            # Reviews per phase
    └── dashboard/               # Human-facing status
        ├── current-status.md    # What's happening now
        ├── action-items.md      # What needs your attention
        └── decisions-needed.md  # Gate outcomes requiring your input
```

## Checking Progress

Look at the dashboard files:

```bash
cat IdeationDept/Planner/output/dashboard/current-status.md
cat IdeationDept/Planner/output/dashboard/action-items.md
cat IdeationDept/Planner/output/dashboard/decisions-needed.md
```

Or ask the Planner: **"What's the status?"**

## Triggering a Review

After completing a phase of work:

```bash
cd IdeationDept/Planner/agents/planner && claude
```

Then say: **"Review phase N"** (where N is the phase number)

The Planner will launch a reviewer agent to inspect the completed work against
the task specs, run tests, and evaluate any go/no-go gates.

## Execution Lifecycle

```
Phase 0 planned → Phase 0 executed → Phase 0 reviewed → Gate G0/G1 decided
                                                               │
Phase 1 planned ◄──────────────────────────────────────────────┘
(incorporates gate outcomes, actual metrics, etc.)
      │
      ▼
Phase 1 executed → Phase 1 reviewed → Gate G2/G3 decided → ...
```

## Source of Truth

The file `context/implementation-plan.md` is the authoritative plan. It contains
21 work items (P0-P21) across 4 phases, 5 go/no-go gates, and an 18-week timeline
targeting JCIM submission. The Planner decomposes this into executable tasks but
does not second-guess it.
