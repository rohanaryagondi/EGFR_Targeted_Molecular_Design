# Project Briefing

Last updated: 2026-04-08

---

## Status at a Glance

**Project is complete.** All 12 workstreams finished and merged, all 3 ML models trained, 646 tests pass (640 on login node + 6 GPU-only), ruff clean, full comparison run, null hypothesis formally retained, retrospective validation confirms 10x enrichment. Pushed to GitHub ML branch.

---

## What's Done

- **Core pipeline (Phases 1-7):** Static baseline (30 candidates) and state-aware pipeline (461 candidates: 395 VAE + 36 template + 30 shared) both scored by the same unified function
- **All 12 workstreams complete:**
  - WS01-09: Chemistry foundation, scoring integration, statistical testing, docking proxy, visualization, CI/CD, conditional VAE, MPNN affinity, ADMET predictor
  - WS11: GNINA physics-based docking (tier 0 in 4-tier scoring cascade, 33 tests)
  - WS12: Pareto multi-objective optimization (weight-free hypervolume comparison, 36 tests)
  - WS13: Retrospective time-split validation (predict post-2015 drugs from pre-2015 data, 28 tests)
- **All 3 ML models trained:**
  - MPNN: RMSE=0.7182, R²=0.6863, Pearson=0.8323 (12.7M params, 10,466 compounds)
  - ADMET: hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 (187K params, 27,698 molecules)
  - VAE v3 (SELFIES): 99.9% valid, 94.8% unique (9.5M params, 300 epochs)
- **4-tier docking cascade:** GNINA → MPNN → DockingProxy MLP → constant 0.5 stub. GNINA provides real physics-based Vina + CNN scores with GPU guard.
- **Full comparison run:** State-aware mean=0.4378 vs static=0.5437. Mann-Whitney U: p<0.001, d=1.36 (static favored). **Null hypothesis formally retained.** 431 novel candidates, diversity 0.9056 vs 0.5684
- **Retrospective validation:** State-aware EF@10 = 4.95 (pre-2010) and 7.72 (pre-2015) vs static 0.47/0.79 — 10x enrichment over static baseline. Models retrained on time-split data with verified no-leakage.
- **Pareto analysis:** Weight-free hypervolume comparison alongside weighted-sum scoring. Pareto front plots (2D projections + parallel coordinates).
- **646 tests across 22 files**, all passing (640 on login node + 6 GPU-skipped). Ruff clean.
- **Vision System:** 12 ideas proposed, 3 accepted and completed (005 GNINA, 008 Pareto, 009 Time-Split), 9 deferred
- **Admin AI:** Two audits complete, 24 suggestions triaged (all resolved)
- **Documentation:** Comprehensive audit completed 2026-04-08 (all stale references fixed)

---

## What's Remaining

### Deferred Vision Ideas (9 total, revisit post-paper)

001 (continuous conditioning), 002 (3D diffusion), 003 (kinome selectivity), 004 (ensemble uncertainty), 006 (learned similarity), 007 (retrosynthesis), 010 (pre-training), 011 (water thermodynamics), 012 (RL optimization). Full rationale in `reports/head-ai-log.md`.

### Stretch Goals

- Active learning loop (VAE → MPNN → retrain cycle)
- Multi-target expansion (ABL, ALK, BRAF)

---

## Null Hypothesis Status

**Formally retained (2026-04-06).** Two comparisons run:

**Comparison 1 (templates only):** State-aware mean=0.5699 vs static=0.5437 (delta=+0.026). Mann-Whitney U: p=0.5349. Not significant.

**Comparison 2 (templates + VAE, definitive):**

| Metric | State-Aware | Static | Delta |
|--------|:-----------:|:------:|:-----:|
| Candidates | 461 | 30 | +431 |
| Mean composite score | 0.4378 | 0.5437 | -0.1059 |
| Max composite score | 0.7794 | 0.7288 | +0.0506 |
| Diversity | 0.9056 | 0.5684 | +0.3372 |
| Mann-Whitney U p | <0.001 | -- | -- |
| Cohen's d | 1.36 (static favored) | -- | -- |
| Novel candidates | 431 | 0 | +431 |
| Weight sensitivity | 44% state wins | 56% static wins | -- |

**Interpretation:** State-aware dramatically expands chemical space (431 novel, 0.91 diversity) and achieves a higher max score (0.78 vs 0.73). But the mean score is significantly lower because VAE candidates have low reference similarity (35% of score weight). The scoring function inherently penalizes genuinely novel molecules. Neither pipeline dominates across weight configurations (44/56 split).
