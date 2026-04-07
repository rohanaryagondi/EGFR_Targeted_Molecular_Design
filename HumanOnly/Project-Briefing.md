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
- **Vision System:** 12 strategic improvement ideas proposed by Visionary AI (not yet reviewed by Head AI)
- **Admin AI:** First audit complete, 12 suggestions triaged (10 implemented, 1 deferred, 1 wont-fix)
- **Documentation:** Comprehensive refresh completed 2026-04-07 (20 files updated)

---

## What's Pending (Stretch Goals Only)

All core work is complete. Remaining items are stretch goals:

### 1. Vision Idea Review

12 ideas proposed by Visionary AI, not yet reviewed. Run Head AI with:
> Read all idea files in `vision/ideas/` that have `Status: proposed`. For each idea, decide whether to accept or defer.

Ideas span: continuous conditioning, 3D pocket diffusion, kinome selectivity, ensemble uncertainty, GNINA docking, learned similarity, retrosynthetic feasibility, Pareto optimization, time-split validation, self-supervised pretraining, water thermodynamics, RL molecular optimization.

### 2. Real Docking Validation

MPNN provides learned affinity predictions but is not physics-based docking. AutoDock Vina or GNINA would provide pose-level validation.

### 3. Active Learning Loop

VAE generates → MPNN scores → top candidates retrain MPNN → updated scores guide next VAE round.

### 4. Multi-Target Expansion

Replicate for ABL, ALK, BRAF to test generalizability beyond EGFR.

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
