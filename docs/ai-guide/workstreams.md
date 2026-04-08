# Workstream System

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Overview

Workstreams are independent improvement tasks designed for parallel AI development.
Each workstream file in `workstreams/` is self-contained: an AI agent given only
the workstream file, `CLAUDE.md`, and the relevant module READMEs can execute the
work autonomously.

## Workstream Index

| # | Name | Effort | Impact | Dependencies | Status |
|---|------|--------|--------|-------------|--------|
| 01 | Chemistry Foundation | Moderate | High | None | **Complete** |
| 02 | Scoring Integration | Low | High | 01 | **Complete** |
| 03 | Statistical Testing | Low | High | None | **Complete** |
| 04 | Docking Proxy | Moderate | Critical | 01 | **Complete** |
| 05 | Visualization | Low | Moderate | 03 | **Complete** |
| 06 | CI/CD | Low | Moderate | None | **Complete** |
| 07 | Conditional VAE | High | High | None (01 helpful) | **Complete** |
| 08 | MPNN Affinity | High | Critical | 01 | **Complete** |
| 09 | ADMET Predictor | High | High | 01 | **Complete** |
| 11 | GNINA Docking | Moderate | High | 01, structure atlas | **Complete** |
| 12 | Pareto Optimization | Low | High | None | **Complete** |
| 13 | Retrospective Validation | Moderate | Critical | MPNN, full pipeline | **Complete** |

## Four Parallel Groups

**Group A** -- Start immediately (no dependencies):
- WS01: Chemistry Foundation, WS03: Statistical Testing, WS06: CI/CD, WS07: Conditional VAE

**Group B** -- After WS01 completes:
- WS02: Scoring Integration, WS04: Docking Proxy, WS08: MPNN Affinity, WS09: ADMET Predictor

**Group C** -- After WS03 completes:
- WS05: Visualization

**Group D** -- After full pipeline run, all models trained:
- WS11: GNINA Docking (parallel with WS12), WS12: Pareto Optimization (parallel with WS11)
- WS13: Retrospective Validation (after WS11/WS12)

## Conflict Zones

**Scoring chain (WS02 -> WS04 -> WS08):** All modify `ranking/scoring.py`. Must NOT
run in parallel. Each builds a fallback layer on the previous.

**WS11 modifies `ranking/scoring.py`** (adds GNINA as tier 0). It merged BEFORE WS12.
WS12 does NOT touch `ranking/scoring.py`.

WS09 modifies the filtering pipeline (`generation/`) and does not conflict with scoring.

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
| 11 | `ws11-gnina` | `ws11/gnina` |
| 12 | `ws12-pareto` | `ws12/pareto` |
| 13 | `ws13-retro` | `ws13/retro` |

For non-workstream tasks, use `task-{short-description}` (e.g., `task-docs-update`).

**Head AI has no worktree.** The Head AI always operates directly on the `ML` branch
in the main repository. Only modular agents use worktrees.

## How to Deploy an Agent on a Workstream

Give the agent these files (in order of priority):
1. `CLAUDE.md` -- project rules and architecture
2. `workstreams/{NN}-{name}.md` -- the specific workstream brief
3. `src/statebind/{module}/README.md` -- relevant module documentation
4. `workstreams/INTERFACES.md` -- interface contracts the workstream must honor
