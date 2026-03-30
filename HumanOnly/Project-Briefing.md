# Project Briefing

Last updated: 2026-03-30

---

## Status at a Glance

All code is written. All 9 workstreams are complete. 548 tests pass. The pipeline runs end-to-end with stub/proxy scoring. **The critical path is now GPU training of 3 ML models**, followed by a full pipeline re-run with real scores and statistical hypothesis testing.

---

## What's Done

- **Core pipeline (Phases 1-7):** Static baseline (30 candidates) and state-aware pipeline (79 candidates) both built and scored by the same unified function
- **9 workstreams complete:** Chemistry foundation, scoring integration, statistical testing, docking proxy, visualization, CI/CD, conditional VAE, MPNN affinity, ADMET predictor
- **ML integration code:** All 3 adapters written (VAE -> generation, MPNN -> ranking, ADMET -> evaluation). Cascading docking fallback assembled: MPNN -> DockingProxy MLP -> stub
- **Training data prepared:** ChEMBL EGFR (1,678 compounds), TDC ADMET benchmarks, VAE SMILES training set
- **548 tests across 19 files**, all passing
- **Vision System:** 12 strategic improvement ideas proposed by Visionary AI (not yet reviewed by Head AI)
- **Admin AI:** First audit complete, 12 suggestions triaged (10 implemented, 1 deferred, 1 wont-fix)
- **Documentation:** All files updated to reflect post-workstream reality

---

## What's Pending

### 1. ML Model Training (Critical Path)

Three models need GPU training. All code, configs, and data are ready.

```bash
# On your HPC cluster:
git checkout ML
pip install -e ".[ml]"

python scripts/train_vae.py --config configs/vae.yaml      # 2-4 hours
python scripts/train_mpnn.py --config configs/mpnn.yaml     # 1-2 hours
python scripts/train_admet.py --config configs/admet.yaml   # 2-3 hours
```

**Success criteria:**
- VAE: validity >= 50%, uniqueness >= 80%, reconstruction loss < 2.0
- MPNN: RMSE < 1.0 pIC50, R-squared > 0.5, Pearson r > 0.7
- ADMET: hERG AUROC > 0.75, CYP3A4 AUROC > 0.70

After training, copy checkpoints back (do NOT git commit .pt files):
```bash
rsync -av artifacts/models/ /path/to/local/repo/artifacts/models/
```

### 2. Ruff Violations (~40 files)

CI/CD pipeline (GitHub Actions) will fail until fixed. Mostly auto-fixable:
```bash
ruff check --fix src/
ruff check src/          # Check for remaining manual fixes
```

Violations: F401 (unused imports), I001 (import sorting), E501 (line length), F541 (f-strings), N815 (naming).

### 3. Full Pipeline Re-Run

After models are trained:
```bash
python scripts/rerank_candidates.py                      # Re-score with real MPNN
python scripts/compare_baseline_vs_state_aware.py        # Head-to-head comparison
python scripts/report_comparative_results.py             # Generate reports
```

This is where the null hypothesis gets tested. If p < 0.05 on Mann-Whitney U for score distributions, the state-aware advantage is statistically significant.

### 4. Vision Idea Review

12 ideas proposed by Visionary AI, not yet reviewed. Run Head AI with:
> Read all idea files in `vision/ideas/` that have `Status: proposed`. For each idea, decide whether to accept or defer.

Ideas span: continuous conditioning, 3D pocket diffusion, kinome selectivity, ensemble uncertainty, GNINA docking, learned similarity, retrosynthetic feasibility, Pareto optimization, time-split validation, self-supervised pretraining, water thermodynamics, RL molecular optimization.

---

## Recommended Order of Operations

```
1. Fix ruff violations          (30 min, unblocks CI)
2. Train ML models on HPC       (6-9 hours GPU time, can run overnight)
3. Re-run pipeline with models  (30 min)
4. Review statistical results   (is p < 0.05?)
5. Review Vision ideas          (use Head AI)
6. Create new workstreams       (from accepted ideas)
```

Steps 1 and 2 can happen in parallel. Step 3 requires step 2. Steps 4-6 are sequential.

---

## Null Hypothesis Status

**Not rejected.** The state-aware pipeline shows +0.020 mean score and +0.035 diversity advantage, but without real docking scores (20% of the scoring function is a stub) and without formal statistical testing, these differences lack significance. Training the MPNN is what unlocks a real test.
