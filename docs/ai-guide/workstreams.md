# Workstream System

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Overview

Workstreams are independent improvement tasks designed for parallel AI development.
Each workstream file in `workstreams/` is self-contained: an AI agent given only
the workstream file, `CLAUDE.md`, and the relevant module READMEs can execute the
work autonomously.

## Workstream Index

| # | Name | Effort | Impact | Dependencies |
|---|------|--------|--------|-------------|
| 01 | Chemistry Foundation | Moderate | High | None |
| 02 | Scoring Integration | Low | High | 01 |
| 03 | Statistical Testing | Low | High | None |
| 04 | Docking Proxy | Moderate | Critical | 01 |
| 05 | Visualization | Low | Moderate | 03 |
| 06 | CI/CD | Low | Moderate | None |
| 07 | Conditional VAE | High | High | None (01 helpful) |
| 08 | MPNN Affinity | High | Critical | 01 |
| 09 | ADMET Predictor | High | High | 01 |

## Three Parallel Groups

**Group A** -- Start immediately (no dependencies):
- WS01: Chemistry Foundation, WS03: Statistical Testing, WS06: CI/CD, WS07: Conditional VAE

**Group B** -- After WS01 completes:
- WS02: Scoring Integration, WS04: Docking Proxy, WS08: MPNN Affinity, WS09: ADMET Predictor

**Group C** -- After WS03 completes:
- WS05: Visualization

## Conflict Zone: WS02 -> WS04 -> WS08

Workstreams 02, 04, and 08 ALL modify `ranking/scoring.py`. They must NOT run in
parallel. Execute in order: WS02 -> WS04 -> WS08. Each builds a fallback layer on
top of the previous. WS09 modifies the filtering pipeline (`generation/`) and does
not conflict.

## Worktree Naming Convention

Each modular agent runs in its own isolated git worktree.

**Format:** `ws{NN}-{short-description}`
**Branch:** `ws{NN}/{short-description}`
**Location:** `.claude/worktrees/ws{NN}-{short-description}`

| WS | Worktree Name | Branch |
|----|---------------|--------|
| 01 | `ws01-chemistry` | `ws01/chemistry` |
| 02 | `ws02-scoring` | `ws02/scoring` |
| 03 | `ws03-stats` | `ws03/stats` |
| 04 | `ws04-docking` | `ws04/docking` |
| 05 | `ws05-viz` | `ws05/viz` |
| 06 | `ws06-cicd` | `ws06/cicd` |
| 07 | `ws07-vae` | `ws07/vae` |
| 08 | `ws08-mpnn` | `ws08/mpnn` |
| 09 | `ws09-admet` | `ws09/admet` |

For non-workstream tasks, use `task-{short-description}` (e.g., `task-docs-update`).

**Head AI has no worktree.** The Head AI always operates directly on the `ML` branch
in the main repository. Only modular agents use worktrees.

## How to Deploy an Agent on a Workstream

Give the agent these files (in order of priority):
1. `CLAUDE.md` -- project rules and architecture
2. `workstreams/{NN}-{name}.md` -- the specific workstream brief
3. `src/statebind/{module}/README.md` -- relevant module documentation
4. `workstreams/INTERFACES.md` -- interface contracts the workstream must honor
