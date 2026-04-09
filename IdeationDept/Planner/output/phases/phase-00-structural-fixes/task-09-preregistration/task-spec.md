---
phase: "Phase 0: Structural & Methodological Fixes"
task_id: P0-T09
task_name: "Pre-Registration Document"
implementation_plan_ref: "P5: Pre-Registration Document"
status: completed
created: 2026-04-09T18:00:00Z
estimated_effort: "2-4 hours"
---

# Task: Pre-Registration Document

## Objective

Write a pre-registration document specifying the Ablation C hypothesis, success
thresholds, and analysis plan. This document must be committed to git with a
timestamp BEFORE any ablation experiments begin (Phase 1). Pre-registration
prevents post-hoc threshold adjustment and demonstrates scientific rigor.

## Context

The implementation plan requires: "Timestamped git commit before any ablation
experiments." The pre-registration specifies exactly what will be tested (Ablation
C: conditioned vs unconditioned VAE), what metrics will be used (EF@10, BEDROC,
Cohen's d), and what thresholds determine success. This is standard practice in
rigorous computational research and will strengthen the paper's methodology section.

## Prerequisites

- [ ] P0-T01 completed (state model decided: 3-state or 4-state)
- [ ] P0-T03 completed (split type decided: scaffold split implemented)
- [ ] P0-T04 completed (statistical methods decided: BCa bootstrap + BEDROC)
- [ ] P0-T06 completed (structural annotations fixed)
- [ ] P0-T07 completed or skipped (3-state vs 4-state path settled)

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `IdeationDept/Planner/context/implementation-plan.md:200-227` | Ablation C specification |
| `artifacts/verification/4zau_dfg_verification.json` | State model decision |
| `artifacts/evaluation/mpnn_scaffold_metrics.json` | MPNN R^2 with scaffold split (if T05 is done) |
| `src/statebind/evaluation/statistics.py` | Available statistical methods |
| `src/statebind/evaluation/retrospective.py` | Enrichment + BEDROC methods |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| `docs/pre-registration.md` | NEW | Pre-registration document |

## Implementation Steps

1. **Write `docs/pre-registration.md`** with the following content:

   ```markdown
   # StateBind Pre-Registration: Ablation C

   ## Date
   <UTC ISO timestamp of document creation>

   ## Authors
   <from the project -- check pyproject.toml or existing docs>

   ## Hypothesis
   State-conditioned VAE (using discrete conformational state labels) produces
   higher retrospective enrichment than an unconditioned VAE with identical
   architecture and training procedure.

   Formally: EF@10(conditioned) > EF@10(unconditioned) with Cohen's d >= 0.5.

   ## State Model
   <3-state or 4-state, based on P0-T01 result>
   States: <list the states>

   ## Experimental Design

   ### Conditioned VAE
   - Architecture: SELFIES VAE with state-conditioning (one-hot state vector
     concatenated with latent code)
   - n_states: <3 or 4>
   - Training data: ChEMBL EGFR compounds, labeled by conformational state
   - Hyperparameters: as specified in configs/vae.yaml

   ### Unconditioned VAE (Ablation C)
   - Architecture: IDENTICAL to conditioned VAE
   - n_states: 1 (all molecules assigned to state 0, constant one-hot [1.0])
   - This is mathematically equivalent to no conditioning (constant input adds
     no information) while preserving the same architecture and parameter count
   - Training data: same dataset, same preprocessing
   - Hyperparameters: same as conditioned (epochs, learning rate, batch size)

   ### Evaluation Protocol
   - Generate the same total number of candidate molecules per condition
   - Score all candidates with the SAME unified scoring function (ranking/scoring.py)
   - Compute:
     - EF@10 (enrichment factor at top 10)
     - BEDROC(alpha=20) (Boltzmann-enhanced early enrichment)
     - Mean composite score
   - All metrics computed with 10,000-fold BCa bootstrap confidence intervals
   - Run across 3+ random seeds
   - Compute Cohen's d between conditioned and unconditioned distributions

   ## Success Thresholds (Pre-Registered)

   | Metric | STRONG GO | GO | PIVOT | NO-GO |
   |--------|-----------|-----|-------|-------|
   | Cohen's d | >= 0.8 | [0.5, 0.8) | [0.3, 0.5) | < 0.3 |

   - d >= 0.8: Strong effect. Paper's thesis robustly supported.
   - d in [0.5, 0.8): Moderate effect. Publishable with tempered claims.
   - d in [0.3, 0.5): Weak effect. Pivot to "diversity + multi-pocket docking"
     framing rather than "state conditioning drives enrichment."
   - d < 0.3: State conditioning provides no meaningful benefit. Pivot to
     negative result or benchmark-only contribution.

   ## Covariates
   - Pool size (number of generated candidates per condition)
   - Chemical diversity (number of unique Murcko scaffolds, or #Circles if available)
   - FCD (Frechet ChemNet Distance to training set)
   - MPNN scoring component R^2 (scaffold split): <value from P0-T05 if available>

   ## Analysis Plan
   - Primary comparison: Mann-Whitney U test on EF@10 distributions
   - Effect size: Cohen's d with pooled standard deviation
   - Confidence intervals: BCa bootstrap (10,000 resamples)
   - Visualization: Box plot of per-seed EF@10 for both conditions
   - Robustness checks: BEDROC comparison, scoring component ablation

   ## Data Availability
   - All code: GitHub repository (to be made public upon submission)
   - Training data: ChEMBL (public)
   - Generated candidates: will be deposited with manuscript

   ## Commitment
   This document was committed to the git repository before any Ablation C
   experiments were run. The commit hash serves as a timestamp. Results will
   be reported regardless of outcome (positive or negative).
   ```

2. **Customize the document** with actual values:
   - Fill in the state model (3 or 4) from T01 result
   - Fill in MPNN R^2 from T05 result (if available; otherwise note "pending")
   - Fill in authors from `pyproject.toml`
   - Fill in exact date

3. **Commit to git:**
   ```bash
   git add docs/pre-registration.md
   git commit -m "pre-registration: Ablation C hypothesis and analysis plan

   Pre-registered before any ablation experiments.
   State model: <3 or 4>-state (based on 4ZAU verification).
   Primary threshold: Cohen's d >= 0.5 for GO decision.

   This commit timestamp serves as proof of pre-registration."
   ```

## Verification

- [ ] `docs/pre-registration.md` exists with complete content
- [ ] All placeholder values filled in with actual data
- [ ] Git commit created with descriptive message
- [ ] Commit hash recorded
- [ ] No ablation experiments have been run yet (this is the whole point)
- [ ] Update `IdeationDept/Planner/output/logs/progress.md` with task completion
      and commit hash

## Agent Instructions

- This is a **document-writing task**. The only code interaction is the git commit.
- Follow StateBind conventions: UTC ISO timestamps.
- The document should be written in clear, formal scientific language.
- Do NOT modify any source code, tests, or configs.
- The git commit is important -- it provides a tamper-evident timestamp proving
  the hypotheses were registered before experiments.
- After completing all steps, update `IdeationDept/Planner/output/logs/progress.md`
  with this task's completion status and the git commit hash.

## Notes and Gotchas

- **Timing is critical:** This document MUST be committed before ANY Ablation C
  code runs. If someone accidentally starts Phase 1 before this commit, the
  pre-registration loses its value.
- **The document should be honest about what we know:** If MPNN R^2 from T05 is
  available, include it. If the pipeline has been re-run with corrected annotations,
  include the updated EF@10 values. Pre-registration registers the hypothesis and
  thresholds, not the baseline numbers.
- **Keep the thresholds from the implementation plan** (Cohen's d >= 0.5 for GO).
  Do not adjust these based on Phase 0 results -- that would defeat the purpose.
