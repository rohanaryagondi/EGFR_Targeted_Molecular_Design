---
type: phase-plan
phase: "Phase 1: Core Experiments"
implementation_plan_ref: "P6, P7, P8, P9, P10, P11, P12"
created: 2026-04-09T23:30:00Z
status: pending
---

# Phase Plan: Core Experiments

## Phase Overview

Phase 1 runs the project's definitive experiments: Ablation C (the thesis test),
compute-matched comparisons, scoring ablations, REINVENT 4 external baseline, and
ABL1 multi-kinase extension. The most critical item is Ablation C (P6) -- if an
unconditioned VAE achieves the same enrichment as the state-conditioned VAE, the
project's central claim is invalidated. Gate G2 (Cohen's d >= 0.5) determines
whether to proceed or pivot. ABL1 work (Waves 4-5) is conditional on G2 outcome.

This phase spans weeks 2-8 of the 18-week timeline and contains 3 go/no-go gates
(G2, G3, G4).

## Prerequisites

- [x] Phase 0 complete (9/9 tasks, G0 GO, G1 GO)
- [x] 3-state model adopted, VAE retrained (300 epochs, n_states=3)
- [x] MPNN scaffold R^2 = 0.5153 (>= 0.35 threshold)
- [x] Pre-registration committed (9e7cf96)
- [x] 669 tests passing, no regressions

## Task Summary

| Task ID | Task Name | Effort | Dependencies | Wave | Status |
|---------|-----------|--------|-------------|------|--------|
| P1-T01 | Ablation C Config + Data Prep | 0.5 day | None | 1A | pending |
| P1-T02 | VAE Quality Metrics (FCD/Recon/Novelty) | 2-3 days | None | 1A | pending |
| P1-T03 | Scoring Ablation + Fairness Script | 1-2 days | None | 1A | pending |
| P1-T04 | PMO Comparison Infrastructure | 1-2 days | None | 1B | pending |
| P1-T05 | ABL1 Schema + Data Curation Script | 2-3 days | None | 1B | pending |
| P1-T06 | REINVENT 4 Environment + GNINA Plugin | 3-5 days | None | 1B | pending |
| P1-T07 | Ablation C Training + Generation (GPU) | 2-3 days | P1-T01 | 2 | pending |
| P1-T08 | Scoring Ablation + PMO Execution | 2-3 days | P1-T03, P1-T04 | 2 | pending |
| P1-T09 | ABL1 Structures + Features | 2-3 days | P1-T05 | 2 | pending |
| P1-T10 | Ablation C Analysis + Gate G2 | 1-2 days | P1-T07, P1-T02 | 3 | pending |
| P1-T11 | REINVENT 4 EGFR Run + Gate G3 | 3-5 days | P1-T06 | 3 | pending |
| P1-T12 | ABL1 Model Training (VAE + MPNN) | 2-3 days | P1-T09, G2 GO | 4 | pending |
| P1-T13 | ABL1 Pipeline + Retrospective + Gate G4 | 2-3 days | P1-T12 | 5 | pending |

## Execution Order

```
Wave 1A: [T01] [T02] [T03]          -- 3 agents max
              |
Wave 1B: [T04] [T05] [T06]          -- 3 agents max
          |     |     |
Wave 2:  [T07] [T08] [T09]          -- 3 agents max
          |     |      |
Wave 3:  [T10]       [T11]          -- 2 agents
          | (Gate G2)  |
Wave 4:  [T12]         |            -- 1 agent (requires G2 GO)
          |             |
Wave 5:  [T13]          |           -- 1 agent
```

**Constraint:** Max 3 subagents running in parallel (token cost control).
SLURM jobs: up to 20 simultaneous, use priority queue (`-p priority -A prio_gerstein`).

## Operator Guide

### Option A: Phase Lead (Recommended)

1. Navigate to: `cd IdeationDept/Planner/output/phases/phase-01-core-experiments/`
2. Launch Claude Code: `claude`
3. Say: "You are a Phase Lead. Read phase-plan.md and all task-spec.md files
   in this directory. Execute the tasks in wave order, launching at most 3
   parallel tasks per wave using the Agent tool. After each batch of 3 completes,
   launch the next batch. Update progress.md after each task completes."
4. Monitor progress. The Phase Lead will report when all tasks are done.
5. **At Gate G2 checkpoint** (after P1-T10): Review Ablation C results.
   - If d >= 0.5: Tell the Phase Lead "G2 is GO, continue with Waves 4-5"
   - If d in [0.3, 0.5): Tell it "G2 is PIVOT, continue with ABL1 but note reframing"
   - If d < 0.3: Tell it "G2 is NO-GO, skip Waves 4-5"
6. After completion, return to the Planner AI and say "Review phase 1".

### Option B: Direct Execution

1. **Wave 1A** (3 tasks in parallel):
   - T01: `cd <repo-root> && claude` then say "Execute task P1-T01 from IdeationDept/Planner/output/phases/phase-01-core-experiments/task-01-ablation-c-config/task-spec.md"
   - T02: Same pattern with task-02
   - T03: Same pattern with task-03
2. **Wave 1B** (after 1A completes, 3 tasks):
   - T04, T05, T06 in parallel
3. **Wave 2** (after 1B completes, 3 tasks):
   - T07, T08, T09 in parallel
4. **Wave 3** (2 tasks):
   - T10, T11 in parallel
5. **Gate G2 decision** after T10 completes
6. **Wave 4** (1 task, if G2 GO): T12
7. **Wave 5** (1 task): T13

## Phase Lead Instructions

You are the Phase Lead for Phase 1: Core Experiments. Your job is to execute all
tasks in this phase in the correct order, respecting the 3-agent parallel limit.

1. Read this phase-plan.md and all task-spec.md files in this directory
2. Execute tasks by wave, launching at most 3 Agent tool calls per message:
   - **Wave 1A**: Launch P1-T01, P1-T02, P1-T03 in parallel (3 agents)
   - **Wave 1B** (after 1A completes): Launch P1-T04, P1-T05, P1-T06 (3 agents)
   - **Wave 2** (after 1B completes): Launch P1-T07, P1-T08, P1-T09 (3 agents)
   - **Wave 3** (after Wave 2 completes): Launch P1-T10, P1-T11 (2 agents)
   - **Gate G2 checkpoint**: After P1-T10 completes, report G2 outcome to operator.
     Wait for operator decision before proceeding.
   - **Wave 4** (if G2 GO/PIVOT): Launch P1-T12 (1 agent)
   - **Wave 5** (after Wave 4): Launch P1-T13 (1 agent)
3. For each task agent, provide:
   - The full contents of the task's task-spec.md
   - Instructions to update `../../logs/progress.md` upon completion
4. After each task completes, verify success by reading the agent's output
5. Update `../../logs/progress.md` with task completion status
6. Report a summary when all tasks are done (or when paused at G2)

**SLURM jobs**: Task agents may submit up to 20 simultaneous SLURM jobs using
the priority queue: `-p priority -A prio_gerstein`.

## Reviewer Checklist

- [ ] Ablation C uses identical architecture, hyperparameters, and epochs as conditioned VAE
- [ ] Unconditioned VAE uses n_states=1 (constant one-hot [1.0], no information)
- [ ] Cohen's d computed correctly with pooled standard deviation across 3+ seeds
- [ ] BCa bootstrap uses 10,000 iterations with bias correction
- [ ] PMO comparison uses strictly equal oracle budgets (N=500)
- [ ] Scoring ablation covers all 4 components independently
- [ ] 3-component fairness check shows enrichment without state_specificity
- [ ] FCD scores reported for both conditioned and unconditioned VAEs
- [ ] REINVENT 4 uses same unified scoring function as StateBind pipelines
- [ ] ABL1 structure annotations verified against PDB records (not just metadata)
- [ ] ABL1 MPNN uses scaffold split from day 1
- [ ] All new functions have tests; 669+ tests pass with no regressions
- [ ] Artifacts written as JSON with generated_at and notes fields
- [ ] No code changes outside src/, tests/, scripts/, configs/ (no doc/report drift)

## Go/No-Go Gates in This Phase

| Gate | Criterion | GO | CONDITIONAL GO / PIVOT | NO-GO |
|------|-----------|-----|------------------------|-------|
| G2 (week 4-5) | Ablation C Cohen's d | >= 0.5 (ideally >= 0.8): thesis robustly supported | [0.3, 0.5): reframe as "diversity + multi-pocket docking" benefit | < 0.3: thesis not supported; pivot to negative result (~20%) |
| G3 (week 7) | REINVENT 4 integration | 100+ valid docked molecules with GNINA | Slow but functional (>10 min/mol): reduce N | Fails after 2 weeks: fall back to Vina scoring (~15%) |
| G4 (week 8) | ABL1 enrichment | EF@10 > 1.0 for state-aware | Positive direction, wide CIs: report honestly | < 1.0: investigate; try BRAF instead (~25%) |

## Success Criteria

- [ ] Ablation C complete with Cohen's d and G2 decision recorded
- [ ] PMO comparison shows enrichment under equal oracle budgets
- [ ] Scoring ablation identifies which component drives enrichment
- [ ] 3-component check shows enrichment persists without state_specificity
- [ ] FCD, reconstruction accuracy, novelty, and diversity reported for VAE
- [ ] REINVENT 4 baseline complete with enrichment comparison
- [ ] ABL1 pipeline complete with retrospective enrichment and G4 decision (if G2 GO)
- [ ] All gates (G2, G3, G4) decided and recorded in decisions-needed.md
- [ ] progress.md updated with all 13 task completions
