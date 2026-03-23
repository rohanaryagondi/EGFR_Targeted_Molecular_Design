# Development Workstreams

Independent improvement tasks designed for parallel AI development. Each workstream is self-contained: an AI agent given only the workstream file, `CLAUDE.md`, and the relevant module READMEs can execute the work autonomously.

## Workstream Index

| # | Name | Status | Effort | Impact | Dependencies |
|---|------|--------|--------|--------|-------------|
| 01 | [Chemistry Foundation](01-chemistry-foundation.md) | **Complete** | Moderate | High | None |
| 02 | [Scoring Integration](02-scoring-integration.md) | Not started | Low | High | 01 |
| 03 | [Statistical Testing](03-statistical-testing.md) | **Complete** | Low | High | None |
| 04 | [Docking Proxy](04-docking-proxy.md) | Not started | Moderate | Critical | 01 |
| 05 | [Visualization](05-visualization.md) | Not started | Low | Moderate | 03 |
| 06 | [CI/CD](06-ci-cd.md) | **Complete** | Low | Moderate | None |
| 07 | [Conditional VAE](07-conditional-vae.md) | **Complete** (data prep + integration) | High | High | None (01 helpful) |
| 08 | [MPNN Affinity](08-mpnn-affinity.md) | Not started | High | Critical | 01 |
| 09 | [ADMET Predictor](09-admet-predictor.md) | Not started | High | High | 01 |

## Dependency Graph

```
01-chemistry-foundation ──► (independent, start immediately)
02-scoring-integration  ──► depends on 01
03-statistical-testing  ──► (independent, start immediately)
04-docking-proxy        ──► depends on 01
05-visualization        ──► depends on 03
06-ci-cd                ──► (independent, start immediately)
07-conditional-vae      ──► (independent, 01 helpful but not required)
08-mpnn-affinity        ──► depends on 01
09-admet-predictor      ──► depends on 01
```

## Parallel Groups

**Group A** (start immediately, no dependencies):
- Workstream 01: Chemistry Foundation
- Workstream 03: Statistical Testing
- Workstream 06: CI/CD
- Workstream 07: Conditional VAE

**Group B** (after Workstream 01 completes):
- Workstream 02: Scoring Integration
- Workstream 04: Docking Proxy
- Workstream 08: MPNN Affinity
- Workstream 09: ADMET Predictor

**Group C** (after Workstream 03 completes):
- Workstream 05: Visualization

## Conflict Zones

Workstreams 02, 04, and 08 all modify `ranking/scoring.py`. They should NOT run in parallel. Recommended execution order: 02 -> 04 -> 08, so each fallback layer builds on the previous.

Workstream 09 modifies the filtering pipeline (`generation/` module) but does not conflict with scoring workstreams.

## Interface Contracts

See [INTERFACES.md](INTERFACES.md) for the exact function signatures and return types that workstreams must conform to. This is the contract that prevents workstreams from breaking each other.

## Worktree Naming Convention

Each modular agent runs in an isolated git worktree. Names must be descriptive —
never use auto-generated names. The Head AI has **no worktree**; it works directly
on the `ML` branch.

| WS | Worktree Name | Branch | Description |
|----|---------------|--------|-------------|
| 01 | `ws01-chemistry` | `ws01/chemistry` | Chemistry Foundation |
| 02 | `ws02-scoring` | `ws02/scoring` | Scoring Integration |
| 03 | `ws03-stats` | `ws03/stats` | Statistical Testing |
| 04 | `ws04-docking` | `ws04/docking` | Docking Proxy |
| 05 | `ws05-viz` | `ws05/viz` | Visualization |
| 06 | `ws06-cicd` | `ws06/cicd` | CI/CD |
| 07 | `ws07-vae` | `ws07/vae` | Conditional VAE |
| 08 | `ws08-mpnn` | `ws08/mpnn` | MPNN Affinity |
| 09 | `ws09-admet` | `ws09/admet` | ADMET Predictor |

All worktrees live under `.claude/worktrees/`. After a workstream completes, the Head
AI merges the worktree branch into `ML` (see `CLAUDE.md` Section 16).

## How to Use a Workstream File

Each workstream file contains:
1. **Goal** — what to achieve and why
2. **Files to create** — new files with their purpose
3. **Files to modify** — existing files and what changes
4. **Interface contracts** — function signatures and return types
5. **Existing code to reuse** — file paths and line numbers
6. **What NOT to touch** — files off-limits for this workstream
7. **Testing requirements** — what tests to write and how to verify
8. **Definition of done** — checklist for completion

Before starting any workstream, read:
1. `CLAUDE.md` (project rules)
2. The workstream file
3. The relevant `src/statebind/*/README.md` files
4. `workstreams/INTERFACES.md` (if the workstream produces or consumes interfaces)
