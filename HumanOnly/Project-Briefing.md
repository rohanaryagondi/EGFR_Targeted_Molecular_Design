# Project Briefing

Last updated: 2026-04-07

---

## Status at a Glance

**Project is feature-complete.** All code written, all 9 workstreams complete, all 3 ML models trained, 548 tests pass, ruff clean, full comparison run, null hypothesis formally retained. Pushed to GitHub ML branch.

---

## What's Done

- **Core pipeline (Phases 1-7):** Static baseline (30 candidates) and state-aware pipeline (461 candidates: 395 VAE + 36 template + 30 shared) both scored by the same unified function
- **9 workstreams complete:** Chemistry foundation, scoring integration, statistical testing, docking proxy, visualization, CI/CD, conditional VAE, MPNN affinity, ADMET predictor
- **All 3 ML models trained:**
  - MPNN: RMSE=0.7182, R²=0.6863, Pearson=0.8323 (12.7M params, 10,466 compounds)
  - ADMET: hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 (187K params, 27,698 molecules)
  - VAE v3 (SELFIES): 99.9% valid, 94.8% unique (9.5M params, 300 epochs)
- **MPNN scoring cascade active:** MPNN → DockingProxy MLP → constant 0.5 stub. Verified: osimertinib=0.75, ethanol=0.34
- **Full comparison run:** State-aware mean=0.4378 vs static=0.5437. Mann-Whitney U: p<0.001, d=1.36 (static favored). **Null hypothesis formally retained.** 431 novel candidates, diversity 0.9056 vs 0.5684
- **548 tests across 19 files**, all passing. Ruff clean (121→0)
- **Vision System:** 12 ideas proposed, **3 accepted** (005 GNINA, 008 Pareto, 009 Time-Split), 9 deferred
- **Admin AI:** Two audits complete, 24 suggestions triaged (all resolved)
- **Documentation:** Comprehensive refresh completed 2026-04-07 (20 files updated)

---

## What's Pending

### Vision Phase: 3 Accepted Workstreams

| WS | Idea | Priority | Why |
|----|------|----------|-----|
| **11** | GNINA Physics-Informed Docking | Start first | Real docking scores + binding poses for 20% of scoring weight |
| **12** | Pareto Multi-Objective Optimization | Parallel with WS11 | Weight-free hypervolume comparison eliminates arbitrary weight problem |
| **13** | Retrospective Time-Split Validation | After WS11/WS12 | Predict future drugs from historical data -- strongest computational validation |

Deploy WS11 + WS12 in parallel, WS13 after they're underway. See AI-Operations-Manual.md Sections 3 and 7 (Wave 8).

### Deferred Ideas (9 total, revisit post-paper)

001 (continuous conditioning), 002 (3D diffusion), 003 (kinome selectivity), 004 (ensemble uncertainty), 006 (learned similarity), 007 (retrosynthesis), 010 (pre-training), 011 (water thermodynamics), 012 (RL optimization). Full rationale in `reports/head-ai-log.md`.

### Remaining Stretch Goals

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
