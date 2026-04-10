---
phase: "Phase 1: Core Experiments"
task_id: P1-T08
task_name: "Scoring Ablation + PMO Execution"
implementation_plan_ref: "P7, P10, P11"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: Scoring Ablation + PMO Execution

## Objective

Execute the scoring ablation battery (P10 + P11) and the PMO comparison (P7)
using the infrastructure created in P1-T03 and P1-T04. This produces the
quantitative results showing which scoring component drives enrichment and
whether enrichment holds under equal compute budgets.

## Context

The scoring ablation answers: "Which component drives enrichment?" If GNINA
(physics-based) drives it, the result is robust. If MPNN (learned) drives it,
data leakage concerns increase. If state_specificity drives it, the result is
circular. The PMO comparison answers: "Does state-aware still win under equal
oracle budgets?"

## Prerequisites

- [x] P1-T03 completed (scoring ablation script)
- [x] P1-T04 completed (PMO comparison script)
- [x] Existing scored candidates in `artifacts/ranking/`
- [x] GNINA available for PMO docking

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `scripts/run_scoring_ablation.py` | Script from P1-T03 |
| `scripts/run_pmo_comparison.py` | Script from P1-T04 |
| `artifacts/ranking/` | Existing scored candidates |
| `configs/docking.yaml` | Docking settings for PMO |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| No source code changes | -- | This is an execution task |

## Implementation Steps

1. **Run scoring ablation**:

   ```bash
   python scripts/run_scoring_ablation.py \
       --input artifacts/ranking/ \
       --output artifacts/evaluation/scoring_ablation.json
   ```

   This produces EF@10 with BCa CIs for:
   - Baseline (all 4 components at default weights)
   - Ablation: reference_similarity = 0
   - Ablation: druglikeness = 0
   - Ablation: docking_proxy = 0
   - Ablation: state_specificity = 0 (this is P11: 3-component fairness check)

2. **Interpret scoring ablation results**:

   Key questions to answer:
   - Which ablation causes the largest EF@10 drop? That component drives enrichment.
   - Does enrichment survive when state_specificity = 0? If yes, the advantage comes
     from multi-pocket docking diversity, not the state label itself.
   - Do 95% CIs overlap between baseline and any ablation?

3. **Run PMO comparison** (requires SLURM for GNINA docking):

   Create a SLURM script for the PMO run:
   ```bash
   #!/bin/bash
   #SBATCH --job-name=pmo_comparison
   #SBATCH -p priority
   #SBATCH -A prio_gerstein
   #SBATCH --cpus-per-task=16
   #SBATCH --mem=32G
   #SBATCH -t 12:00:00

   python scripts/run_pmo_comparison.py \
       --budget 500 \
       --output artifacts/evaluation/pmo_comparison.json
   ```

   Submit: `sbatch scripts/slurm_pmo.sh`

4. **Collect and verify results**:

   - Scoring ablation JSON at `artifacts/evaluation/scoring_ablation.json`
   - PMO comparison JSON at `artifacts/evaluation/pmo_comparison.json`
   - Print summary tables for both

## Verification

- [ ] Scoring ablation produces 5 results (1 baseline + 4 ablations)
- [ ] All enrichment values have BCa CIs (lower, upper)
- [ ] PMO comparison uses exactly 500 oracle calls per pipeline
- [ ] Both JSON artifacts have `generated_at` timestamps
- [ ] Results are scientifically coherent (no obvious errors)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- The scoring ablation does NOT require GNINA -- it re-ranks existing scores.
  Run it directly (no SLURM needed).
- The PMO comparison DOES require GNINA docking -- submit via SLURM on priority queue.
- If the scoring ablation script from P1-T03 doesn't handle the input format
  correctly, fix it and document changes.
- Report results clearly: which component matters most, does enrichment survive
  without state_specificity.

## Notes and Gotchas

- **PMO docking is expensive**: 500 oracle calls x 2 pipelines = 1000 GNINA
  dockings x ~30s each = ~8 hours of CPU time. Use multi-core (16 CPUs) to
  parallelize with ProcessPoolExecutor.
- **State-aware PMO uses 3 receptors**: The 500 oracle calls are distributed
  across the 3 state-specific receptors. Each molecule is docked against the
  receptor for its target state.
- **Pre-filter scoring** should NOT use GNINA (that would consume oracle budget).
  Use cheap descriptors only: Tanimoto, druglikeness, property filters.
