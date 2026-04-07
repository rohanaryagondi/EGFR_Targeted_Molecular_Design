# Human Operator Guide: Prompting AI Agents and Verifying Their Work

This document is for you, the human operator. It tells you exactly what to say to each
AI agent, what to expect back, and how to verify the output. No AI should read this file
as instructions -- it is your playbook for orchestrating them.

---

## 1. Overview

StateBind is a 12-module computational biology pipeline for EGFR-targeted molecular
design. It tests whether conformational state-aware design outperforms static
single-structure design. The codebase has 87 Python source files, 618 tests, and 3
trained neural networks (VAE, MPNN, ADMET) plus GNINA physics-based docking. 11 of 12
workstreams are complete (WS01-09, WS11-12), all models trained, and the null hypothesis
has been formally retained.

The pipeline has been upgraded from SMILES string heuristics to a research-grade system
with RDKit chemistry, trained ML models, and formal hypothesis testing.

You will use two types of AI agent:

- **Head AI** -- Reads the full project context. Coordinates across workstreams, resolves
  cross-cutting issues, and makes architectural decisions. There is one head AI.
- **Modular Agent** -- Reads only its assigned workstream file plus core docs. Executes
  one workstream in isolation. There are up to 9 modular agents running in parallel.

After every AI task completes, you run:
```bash
pytest -v --tb=short
```
This is non-negotiable. If tests fail, the work is not done. Send failures back to the
agent and require fixes before accepting the deliverable.

All 3 ML models are trained (2026-04-06 on Bouchet HPC). Section 4 retains the
training instructions for reference if retraining is needed.

Current test count: 618. Module count: 12 subpackages (including `chemistry/`).

**Testing policy:** Changes to scoring, ML, docking, or evaluation code require a
full SLURM GPU test run (618/618 pass, 0 skips). See `docs/ai-guide/testing-and-deps.md`
for the 3-tier testing policy. The canonical SLURM script is `scripts/run_tests_all.slurm`.

---

## 2. Head AI Setup

The head AI needs full project context. Point it to these files in this order:

1. `CLAUDE.md` -- Primary development reference (rules, architecture, conventions)
2. `GOALS.md` -- Success criteria and numeric targets
3. `TODO.md` -- Current roadmap, completed phases, planned work
4. `workstreams/README.md` -- Workstream index, dependency graph, conflict zones
5. `CRITICAL.md` -- Cross-cutting concerns and known issues

Use this prompt verbatim or adapt minimally:

> Read CLAUDE.md completely. This is your primary reference for all development decisions.
> Then read GOALS.md for project goals and success criteria, TODO.md for the current
> roadmap and task status, and workstreams/README.md for the workstream system. Read
> CRITICAL.md for cross-cutting concerns. Read reports/head-ai-log.md for your running
> log -- update it continuously after every major action (merge, decision, task
> assignment). You are the head developer coordinating workstreams across 12+ modules.
> When I ask about a workstream, read its brief in workstreams/ before answering. When
> current work is complete, check vision/ideas/ for proposed improvements and plan new
> workstreams from accepted ideas (see CLAUDE.md Section 18). Be detailed yet concise.

The head AI should NOT execute workstreams directly. Its job is to:
- Answer architectural questions ("Can WS04 run before WS02?")
- Resolve interface conflicts between workstreams
- Review modular agent output for correctness against INTERFACES.md
- Decide when integration tasks (TODO.md Section 6) are ready to start
- Merge completed modular agent worktrees into ML and push to GitHub
- **Review Visionary ideas and convert accepted ones into new workstreams**
- **Maintain its running log at `reports/head-ai-log.md`**

**The Head AI has no worktree.** It always operates directly on the `ML` branch and
pushes to `origin/ML`. See `CLAUDE.md` Section 16 for the full merge procedure.

---

## 3. Workstream Deployment Guide

For each workstream below: launch a fresh AI agent session **in its own worktree**, copy
the prompt, and let it execute. Each prompt tells the agent exactly which files to read
and what to build.

**Worktree naming:** Each agent's worktree MUST use the convention
`ws{NN}-{short-description}` on branch `ws{NN}/{short-description}`. See the table in
`CLAUDE.md` Section 11. Example: WS02 runs in worktree `ws02-scoring` on branch
`ws02/scoring`. Never use auto-generated worktree names.

**Documentation requirement:** Every agent MUST continuously update its progress report
at `reports/workstreams/ws{NN}-report.md` throughout its session. The report serves as
the handoff mechanism if context compacts or a new agent takes over. See `CLAUDE.md`
Section 17 for the full documentation system. Each agent prompt below includes the
documentation instruction -- do not remove it.

---

### WS01: Chemistry Foundation

**Prompt:**
> Read these files in order: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/01-chemistry-foundation.md,
> (3) workstreams/INTERFACES.md (Contract 1), (4) src/statebind/baselines/README.md,
> (5) src/statebind/baselines/CRITICAL.md,
> (6) reports/workstreams/ws01-report.md (your progress report -- update continuously).
> Create the src/statebind/chemistry/ package implementing Morgan fingerprints, molecular
> descriptors, SMILES validation, and SA scoring. Follow the interface contracts exactly.
> Update your progress report after every major step. Run all tests when done.

**Expected output:**
- New package: `src/statebind/chemistry/` with `__init__.py`, `fingerprints.py`,
  `descriptors.py`, `validation.py`, `sa_score.py`, `README.md`, `CRITICAL.md`
- New test file: `tests/test_chemistry.py` with 25+ tests
- No modifications to existing files outside `chemistry/`

**Verify:**
```bash
pytest -v --tb=short
# All tests pass. Total count >= 384 (359 existing + 25 new).
ruff check src/statebind/chemistry/
```

---

### WS02: Scoring Integration

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/02-scoring-integration.md,
> (3) workstreams/INTERFACES.md (Contract 1 and 7), (4) src/statebind/baselines/scoring.py,
> (5) src/statebind/ranking/scoring.py, (6) src/statebind/ranking/CRITICAL.md,
> (7) reports/workstreams/ws02-report.md (your progress report -- update continuously).
> Wire the chemistry module from WS01 into scoring. Upgrade n-gram similarity to Morgan
> fingerprints with fallback. Replace heuristic druglikeness with QED + Lipinski + SA
> score where RDKit is available. Update your progress report after every major step.
> Run all tests.

**Expected output:**
- Modified: `src/statebind/baselines/scoring.py` (Morgan fingerprint integration)
- Modified: `src/statebind/ranking/scoring.py` (upgraded similarity and druglikeness)
- New or expanded: `tests/test_scoring_integration.py`
- Fallback paths preserved: if RDKit is missing, old heuristics still work

**Verify:**
```bash
pytest -v --tb=short
# All tests pass. Scoring with RDKit installed gives different (better) results.
# Scoring without RDKit falls back to n-gram heuristics.
python -c "from statebind.ranking.scoring import score_candidate; print('OK')"
```

**Prerequisite:** WS01 must be complete and merged.

---

### WS03: Statistical Testing

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/03-statistical-testing.md,
> (3) workstreams/INTERFACES.md (Contract 3), (4) src/statebind/evaluation/README.md,
> (5) src/statebind/evaluation/CRITICAL.md,
> (6) reports/workstreams/ws03-report.md (your progress report -- update continuously).
> Create evaluation/statistics.py with Mann-Whitney U tests, bootstrap confidence
> intervals, and Cohen's d effect sizes. Create evaluation/sensitivity.py for scoring
> weight sensitivity analysis. Update your progress report after every major step.
> Run all tests.

**Expected output:**
- New: `src/statebind/evaluation/statistics.py`
- New: `src/statebind/evaluation/sensitivity.py`
- New: `tests/test_statistics.py` with 25+ tests
- Updated: `src/statebind/evaluation/__init__.py` (exports new functions)

**Verify:**
```bash
pytest -v --tb=short
# All tests pass. Total count >= 384.
python -c "from statebind.evaluation.statistics import mann_whitney_comparison; print('OK')"
```

**Prerequisite:** None. Can run in parallel with WS01.

---

### WS04: Docking Proxy

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/04-docking-proxy.md,
> (3) workstreams/INTERFACES.md (Contract 2), (4) src/statebind/baselines/scoring.py
> (lines 135-149 for the stub), (5) src/statebind/baselines/CRITICAL.md,
> (6) reports/workstreams/ws04-report.md (your progress report -- update continuously).
> Create a small MLP docking proxy trained on embedded SAR data from known EGFR
> inhibitors. The proxy must return varied scores, not constant 0.5. Wire it into the
> scoring function as a fallback between the MPNN and the stub. Update your progress
> report after every major step. Run all tests.

**Expected output:**
- New: `src/statebind/chemistry/docking_proxy.py` (MLP model + inference)
- New: `src/statebind/chemistry/docking_data.py` (embedded training data)
- New or expanded tests: 15+ tests for the proxy
- Modified: `src/statebind/ranking/scoring.py` (fallback chain updated)

**Verify:**
```bash
pytest -v --tb=short
# Proxy returns varied scores:
python -c "
from statebind.chemistry.docking_proxy import predict_docking_score
scores = [predict_docking_score(s) for s in ['CCO', 'c1ccccc1', 'CC(=O)Oc1ccccc1C(=O)O']]
assert len(set([round(s, 2) for s in scores])) > 1, 'Scores should vary'
print('Scores vary:', scores)
"
```

**Prerequisite:** WS01 complete. Must run AFTER WS02 in the scoring chain.

---

### WS05: Visualization

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/05-visualization.md,
> (3) src/statebind/evaluation/README.md, (4) src/statebind/evaluation/CRITICAL.md,
> (5) reports/workstreams/ws05-report.md (your progress report -- update continuously).
> Create evaluation/plotting.py with matplotlib figures for score distributions, diversity
> comparisons, top-K composition charts, and state atlas heatmaps. All figures must be
> saveable to files without requiring a display. Update your progress report after every
> major step. Run all tests.

**Expected output:**
- New: `src/statebind/evaluation/plotting.py`
- New: `tests/test_plotting.py` with 12+ tests
- All plots use `matplotlib.use('Agg')` for headless rendering

**Verify:**
```bash
pytest -v --tb=short
python -c "from statebind.evaluation.plotting import plot_score_distributions; print('OK')"
```

**Prerequisite:** WS03 must be complete (uses confidence intervals for error bars).

---

### WS06: CI/CD

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/06-ci-cd.md, (3) pyproject.toml,
> (4) reports/workstreams/ws06-report.md (your progress report -- update continuously).
> Create .github/workflows/ci.yml with a Python 3.10-3.12 test matrix running pytest
> and ruff check on every push and pull request. Add status badges to README.md. Update
> your progress report after every major step.

**Expected output:**
- New: `.github/workflows/ci.yml`
- Modified: `README.md` (status badges added at top)
- Workflow runs pytest and ruff on Python 3.10, 3.11, 3.12

**Verify:**
```bash
# Local syntax check:
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
# Then push to GitHub and check the Actions tab for green checks.
```

**Prerequisite:** None. Can run in parallel with anything.

---

### WS07: Conditional VAE

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/07-conditional-vae.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) src/statebind/generation/CRITICAL.md,
> (6) reports/workstreams/ws07-report.md (your progress report -- update continuously).
> Create the data preparation script for ChEMBL EGFR actives, and the VAE integration
> module that converts VAE output into StateConditionedCandidate objects compatible
> with the existing generation pipeline. Update your progress report after every major
> step. Run all tests.

**Expected output:**
- New: `scripts/prepare_vae_data.py` (ChEMBL EGFR data download and processing)
- New or modified: generation integration code for VAE-sampled candidates
- New: 15+ tests for data prep and integration
- The VAE architecture itself already exists in `src/statebind/ml/vae.py`

**Verify:**
```bash
pytest -v --tb=short
# Data prep script should be runnable (may need network access for ChEMBL):
python scripts/prepare_vae_data.py --help
```

**Prerequisite:** None for code. Training happens separately on HPC (Section 4).

---

### WS08: MPNN Affinity

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/08-mpnn-affinity.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) src/statebind/ranking/CRITICAL.md, (6) workstreams/INTERFACES.md (Contract 4),
> (7) reports/workstreams/ws08-report.md (your progress report -- update continuously).
> Create the data preparation script for ChEMBL EGFR affinity data, the affinity
> predictor adapter that loads a trained MPNN checkpoint, and the cascading fallback in
> ranking/scoring.py: MPNN -> docking proxy -> constant 0.5 stub. Update your progress
> report after every major step. Run all tests.

**Expected output:**
- New: `scripts/prepare_mpnn_data.py`
- New: `src/statebind/ml/affinity_predictor.py` (adapter wrapping the MPNN)
- Modified: `src/statebind/ranking/scoring.py` (cascading fallback chain)
- New: 20+ tests for the adapter and fallback logic

**Verify:**
```bash
pytest -v --tb=short
# Without a trained checkpoint, scoring should fall back gracefully:
python -c "
from statebind.ranking.scoring import score_candidate
# Should not crash, should use fallback
print('Fallback works')
"
```

**Prerequisite:** WS01 complete. Must run AFTER WS04 in the scoring chain.
Training happens separately on HPC (Section 4).

---

### WS09: ADMET Predictor

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/09-admet-predictor.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) workstreams/INTERFACES.md (Contract 6),
> (6) reports/workstreams/ws09-report.md (your progress report -- update continuously).
> Create the data preparation script for TDC ADMET benchmarks, the ADMET predictor
> adapter that loads a trained checkpoint, and the ADMET filter gate that flags or
> excludes candidates with hERG liability or CYP3A4 inhibition. Update your progress
> report after every major step. Run all tests.

**Expected output:**
- New: `scripts/prepare_admet_data.py`
- New: `src/statebind/ml/admet_predictor.py` (adapter wrapping ADMET model)
- New: `src/statebind/generation/admet_filter.py` (pass/fail gate)
- New: 25+ tests for the adapter and filter

**Verify:**
```bash
pytest -v --tb=short
# Filter should work in fallback mode without a checkpoint:
python -c "
from statebind.generation.admet_filter import admet_filter_candidates
print('ADMET filter importable')
"
```

**Prerequisite:** WS01 complete. Does NOT modify `ranking/scoring.py`, so it can run
in parallel with WS02/WS04/WS08.
Training happens separately on HPC (Section 4).

---

### WS11: GNINA Physics-Informed Docking

**Origin:** Vision Idea 005 (accepted 2026-04-07).

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/11-gnina-docking.md,
> (3) src/statebind/chemistry/README.md, (4) src/statebind/ranking/CRITICAL.md,
> (5) src/statebind/structure/README.md,
> (6) reports/workstreams/ws11-report.md (your progress report -- update continuously).
> Integrate GNINA as the top tier of the docking fallback chain. Create a Python wrapper
> around GNINA CLI, prepare receptor PDBQT files for each conformational state, and add
> state-specific docking analysis. Wire GNINA into ranking/scoring.py as tier 0 in the
> cascade. Update your progress report after every major step. Run all tests.

**Expected output:**
- New: `src/statebind/chemistry/docking.py` (GNINA wrapper, DockingResult model)
- New: `scripts/prepare_docking_receptors.py` (receptor PDBQT + box config per state)
- New: `src/statebind/evaluation/docking_analysis.py` (state-specific analysis)
- New: `configs/docking.yaml` (GNINA parameters)
- Modified: `src/statebind/ranking/scoring.py` (GNINA tier 0 in cascade)
- New: `tests/test_docking.py` with 20+ tests

**Verify:**
```bash
pytest -v --tb=short
# GNINA-dependent tests auto-skip if GNINA not installed:
pytest tests/test_docking.py -v
# If GNINA is installed, verify known binder docking:
python -c "
from statebind.chemistry.docking import is_gnina_available
print('GNINA available:', is_gnina_available())
"
```

**Prerequisite:** All WS01-WS09 complete. GNINA must be installed on the cluster.

---

### WS12: Pareto Multi-Objective Optimization

**Origin:** Vision Idea 008 (accepted 2026-04-07).

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/12-pareto-optimization.md,
> (3) src/statebind/evaluation/README.md, (4) src/statebind/evaluation/CRITICAL.md,
> (5) src/statebind/ranking/README.md,
> (6) reports/workstreams/ws12-report.md (your progress report -- update continuously).
> Add Pareto front analysis and hypervolume comparison to the evaluation pipeline.
> Compute Pareto fronts for both pipelines, compare via hypervolume indicator, and
> produce 2D projection and parallel coordinates visualizations. This complements (does
> NOT replace) the existing weighted-sum comparison. Update your progress report after
> every major step. Run all tests.

**Expected output:**
- New: `src/statebind/ranking/pareto.py` (Pareto front, hypervolume)
- New: `src/statebind/evaluation/pareto_comparison.py` (pipeline comparison)
- Modified: `src/statebind/evaluation/figures.py` (Pareto plots)
- Modified: `src/statebind/evaluation/comparison.py` (Pareto section in results)
- New: `tests/test_pareto.py` with 20+ tests

**Verify:**
```bash
pytest -v --tb=short
python -c "
from statebind.ranking.pareto import compute_pareto_front
import numpy as np
scores = np.random.rand(20, 4)
result = compute_pareto_front(scores, ['sim', 'drug', 'dock', 'state'])
print(f'Front size: {len(result.front_indices)} / {scores.shape[0]}')
"
```

**Prerequisite:** None for code. Uses existing scored data in `artifacts/ranking/comparison.json`.

---

### WS13: Retrospective Time-Split Validation

**Origin:** Vision Idea 009 (accepted 2026-04-07).

**Prompt:**
> Read: (1) CLAUDE.md (especially Rules 10 and Section 17),
> (2) workstreams/13-retrospective-validation.md,
> (3) src/statebind/evaluation/README.md,
> (4) scripts/prepare_mpnn_data.py (for ChEMBL data patterns),
> (5) scripts/compare_baseline_vs_state_aware.py (for pipeline execution patterns),
> (6) reports/workstreams/ws13-report.md (your progress report -- update continuously).
> Build a retrospective validation framework: create time-split datasets from ChEMBL
> (2010 and 2015 cutoffs), retrain MPNN on pre-cutoff data, run both pipelines under
> time restriction, and evaluate whether generated candidates resemble drugs approved
> after the cutoff. Scientific honesty is paramount -- report results as found. Update
> your progress report after every major step. Run all tests.

**Expected output:**
- New: `scripts/build_timesplit_datasets.py` (ChEMBL time-split data curation)
- New: `scripts/run_retrospective_validation.py` (full pipeline under time restriction)
- New: `src/statebind/evaluation/retrospective.py` (enrichment, similarity metrics)
- New: `configs/retrospective.yaml` (cutoff dates, future drug SMILES)
- New: `tests/test_retrospective.py` with 15+ tests

**Verify:**
```bash
pytest -v --tb=short
# Verify no data leakage:
python -c "
from statebind.evaluation.retrospective import compute_enrichment_factor
ef = compute_enrichment_factor([0.8, 0.6, 0.3, 0.1], threshold=0.5, top_k=2)
print(f'Enrichment factor: {ef:.2f}')
"
```

**Prerequisite:** Trained MPNN (for retraining on restricted data). Full pipeline must run
end-to-end. Requires ChEMBL API access for time-split data curation.

---

## 3.5. Merging Completed Worktrees (Head AI Procedure)

When modular agents finish their workstreams, use the Head AI to merge and push.
The Head AI always works on the ML branch directly — no worktree of its own.

### Before You Ask the Head AI to Merge

1. Verify the agent's work: `cd .claude/worktrees/ws{NN}-{name} && pytest -v --tb=short`
2. Check the "Definition of Done" in the workstream brief is fully satisfied
3. Review `git diff --stat ML...ws{NN}/{description}` to confirm no out-of-scope files

### Prompt for the Head AI (Merge & Push)

> The following worktrees are ready to merge: ws{NN}-{name}, ws{NN}-{name}, ...
> Check `.claude/worktrees/` for the branches. Verify no file conflicts exist.
> Ask me before merging each one, then merge into ML and push to origin/ML.

For ML work done on an HPC cluster (no local worktree), tell the Head AI:

> The work for WS{NN} was done on the HPC cluster. The worktree/branch is at {path}.
> Ask me if ready, then merge into ML and push.

### Key Rules

- Head AI asks for your confirmation before merging each worktree — do not skip this
- Scoring chain (WS02 → WS04 → WS08) must merge strictly in order
- Tests must pass before and after each merge
- See `CLAUDE.md` Section 16 for the full procedure

---

## 4. HPC Training Instructions

All 3 ML models have been trained (2026-04-06). These instructions are retained for
reference if retraining is needed. Training requires a GPU with CUDA on your HPC cluster.

### Setup

```bash
git clone https://github.com/rohanaryagondi/EGFR_Targeted_Molecular_Design.git
cd EGFR_Targeted_Molecular_Design
git checkout ML
pip install -e ".[ml]"
```

The `[ml]` extra installs `torch`, `torch_geometric`, and `rdkit`. Verify:
```bash
python -c "import torch; print(torch.cuda.is_available())"
# Should print True on a GPU node.
```

### Conditional SMILES VAE

```bash
python scripts/train_vae.py --config configs/vae.yaml
```

- **Time:** 2-4 hours on a single GPU
- **Config:** `configs/vae.yaml` -- 200 epochs, batch 128, latent_dim 64, KL annealing over 20 epochs
- **Output:** `artifacts/models/vae/best_model.pt`, `artifacts/models/vae/vocabulary.json`
- **Monitor:** `artifacts/logs/vae/training_log.csv`
- **Success criteria:** val_loss decreasing, final reconstruction loss < 2.0, validity >= 50%, uniqueness >= 80%
- **Troubleshooting:**
  - KL collapse (posterior equals prior, all samples identical): reduce `kl_weight` in config from 0.01 to 0.005, or increase `warmup_epochs` from 20 to 40
  - Overfitting (train loss drops, val loss rises): increase `dropout` from 0.1 to 0.2
  - Low validity: increase `max_len` from 128 to 150, or reduce `temperature` from 0.8 to 0.7 during generation

### Affinity MPNN

```bash
python scripts/train_mpnn.py --config configs/mpnn.yaml
```

- **Time:** 1-2 hours on a single GPU
- **Config:** `configs/mpnn.yaml` -- 150 epochs, batch 64, 3 message-passing layers, mean+max readout
- **Output:** `artifacts/models/mpnn/best_model.pt`
- **Monitor:** `artifacts/logs/mpnn/training_log.csv`
- **Success criteria:** test RMSE < 1.0 pIC50, R-squared > 0.5, Pearson r > 0.7
- **Troubleshooting:**
  - Overfitting: increase `dropout` from 0.1 to 0.2, or reduce `hidden_dim` from 128 to 64
  - Underfitting: increase `n_message_passing_layers` from 3 to 4, or increase `hidden_dim` to 256
  - Unstable training: reduce `learning_rate` from 0.001 to 0.0005

### Multi-task ADMET

```bash
python scripts/train_admet.py --config configs/admet.yaml
```

- **Time:** 2-3 hours on a single GPU
- **Config:** `configs/admet.yaml` -- 150 epochs, batch 64, GIN backbone, 6 tasks with weighted loss
- **Output:** `artifacts/models/admet/best_model.pt`
- **Monitor:** `artifacts/logs/admet/training_log.csv`
- **Success criteria:** hERG AUROC > 0.75, CYP3A4 AUROC > 0.70, Spearman > 0.5 on >= 4/6 endpoints
- **Troubleshooting:**
  - Poor multi-task balance (one task dominates): adjust `task_weights` in config -- the hERG weight is already set to 1.5 for safety priority; try reducing it to 1.2 if other tasks suffer
  - Low classification AUROC: ensure class balance in data; consider upsampling minority class
  - Regression tasks underperforming: normalize target values per-task if not already done

### After Training

Copy checkpoints back to the repo:
```bash
# From HPC, scp or rsync the artifacts directory back to your local repo:
rsync -av artifacts/models/ /path/to/local/repo/artifacts/models/
rsync -av artifacts/logs/ /path/to/local/repo/artifacts/logs/
```

Do NOT commit checkpoint files (`.pt`) to git. They are large binaries. The `.gitignore`
should already exclude them. If it does not, add `artifacts/models/**/*.pt` to `.gitignore`.

---

## 5. Verification Checklist

### After Each Workstream

- [ ] `pytest -v --tb=short` -- all tests pass
- [ ] Test count >= previous count (never decreases)
- [ ] `ruff check src/` -- no lint errors
- [ ] New test file exists with meaningful, descriptive test names
- [ ] Check the workstream's "Definition of Done" section in its brief file
- [ ] No files outside the workstream's scope were modified (check `git diff --stat`)
- [ ] All new functions have type annotations
- [ ] All new data structures crossing module boundaries use Pydantic BaseModel
- [ ] No hard-coded paths or thresholds in source code

### After ML Training

- [ ] Checkpoint exists: `artifacts/models/{model}/best_model.pt`
- [ ] Training log CSV exists: `artifacts/logs/{model}/training_log.csv`
- [ ] Training log shows decreasing loss trend (not flat, not diverging)
- [ ] Evaluation metrics meet targets from GOALS.md:
  - VAE: reconstruction > 80%, validity >= 50%, uniqueness >= 80%
  - MPNN: RMSE < 1.0, R-squared > 0.5, Pearson r > 0.7
  - ADMET: hERG AUROC > 0.75, CYP3A4 AUROC > 0.70
- [ ] Model card JSON saved with architecture, hyperparameters, and metrics metadata

### After Full Integration

- [ ] All 9 workstreams complete and verified
- [ ] All 3 models trained with metrics meeting targets
- [ ] `scripts/compare_baseline_vs_state_aware.py` runs end-to-end without errors
- [ ] Statistical test produces a p-value (regardless of result)
- [ ] Reports in `reports/` regenerated with new results
- [ ] README.md updated with current metrics and status

---

## 6. Troubleshooting AI Agents

These are the five most common failure modes when an AI agent executes a workstream,
and exactly how to intervene.

**1. "Can't find a function" or "Module not found"**
The agent is guessing at imports. Point it to the exact file path and line number. Every
module has a README.md and most have a CRITICAL.md. Tell the agent:
> Read src/statebind/{module}/README.md for the API. The function you need is in
> {file}. Read that file before writing any code that depends on it.

**2. "Broke existing tests"**
The agent modified a public interface or changed behavior. Tell the agent:
> Run `pytest -v --tb=short`. You have test failures. Fix ALL failures before continuing.
> Do not skip, delete, or weaken any existing test. The 359 existing tests must all pass.

**3. "Circular import" or "ImportError during collection"**
The agent added an import that violates the dependency graph. Tell the agent:
> See the dependency graph in CLAUDE.md Section "Architecture". Module X cannot import
> from module Y because Y depends on X. Move the shared code to a lower-level module
> (data/ or utils/) or use late imports inside functions.

**4. "Changed a public function signature"**
The agent broke an interface contract. Tell the agent:
> Restore the original function signature. Read workstreams/INTERFACES.md for the exact
> contract. Your code must conform to the interface, not the other way around. Add new
> parameters as keyword-only with defaults if you must extend the API.

**5. "Code doesn't match the spec"**
The agent produced something that works but does not match the workstream brief. Compare
its output against the "Definition of Done" checklist in the workstream file. Tell the
agent:
> Read the "Definition of Done" section in workstreams/{N}-{name}.md. Items {X, Y, Z}
> are not satisfied. Complete them before marking this workstream as done.

---

## 7. Order of Operations

### Recommended Deployment Schedule

**Wave 1 -- No dependencies (deploy in parallel):**
- WS01: Chemistry Foundation
- WS03: Statistical Testing
- WS06: CI/CD
- WS07: Conditional VAE (data preparation portion only)

**Wave 2 -- After WS01 completes:**
- WS02: Scoring Integration (first in the scoring chain)

**Wave 3 -- After WS02 completes:**
- WS04: Docking Proxy (second in the scoring chain)

**Wave 4 -- After WS03 completes:**
- WS05: Visualization

**Wave 5 -- After WS01 + data prep scripts ready:**
- WS08: MPNN Affinity (third in the scoring chain, after WS04)
- WS09: ADMET Predictor (parallel with scoring chain, no conflict)

**Wave 6 -- After WS04 completes:**
- Integrate WS08 scoring changes into ranking/scoring.py

**Wave 7 -- After all workstreams complete + models trained:**
- Re-run full pipeline end-to-end
- Run statistical tests
- Regenerate reports

**Wave 8 -- Vision Phase (after pipeline run + null hypothesis retained):**
- WS11: GNINA Docking + WS12: Pareto Optimization (deploy in parallel)
- WS13: Retrospective Validation (after WS11/WS12 underway)
- Merge order: WS11 -> WS12 -> WS13 (WS11 modifies scoring.py; WS12/WS13 modify comparison.py)

### Agent Scope Rules

**Head AI:** Give it CLAUDE.md + GOALS.md + TODO.md + workstreams/README.md + CRITICAL.md.
It coordinates and reviews. It does not execute workstreams.

**Modular Agent:** Give it ONLY its workstream brief + CLAUDE.md + the relevant module
READMEs and CRITICAL.md files listed in its prompt. It executes one workstream in
isolation.

**Key rule:** Modular agents must NOT modify files outside their workstream's defined
scope. If an agent needs to change a file owned by another workstream, it should flag
the need and stop. You then coordinate the change through the head AI or handle it
manually.

The scoring chain (WS02 -> WS04 -> WS08) is the critical path. Each agent in this chain
modifies `ranking/scoring.py`. Run them strictly sequentially. Merge each one's changes
and verify tests before starting the next.

ML training (Section 4) runs on HPC in parallel with all workstreams. The training
scripts and model code already exist. Workstreams WS07, WS08, and WS09 create the
integration adapters that will wire trained checkpoints into the pipeline, but the
training itself is independent.

---

## 8. Vision System

The Vision System is a strategic planning layer that sits above the workstream system.
It generates bold ideas for project improvement through a structured three-role workflow.

### 8.1 Overview

Three AI roles work together:

1. **Assistant AI** -- Reads the full project, writes concise briefings into `vision/briefings/`
2. **Visionary AI** -- Reads ONLY `vision/` files, writes improvement ideas into `vision/ideas/`
3. **Head AI** -- Reviews ideas, converts accepted ones into new workstreams

The workflow is always: **Assistant first, then Visionary, then Head AI reviews.**

All three maintain running documentation:
- Assistant: `vision/log/assistant-log.md`
- Visionary: `vision/log/visionary-log.md`
- Head AI: `reports/head-ai-log.md`

### 8.2 When to Run the Vision System

Run the Vision System at these milestones:

- **After all Group A workstreams complete** (WS01/03/06/07) -- initial vision
- **After all 9 workstreams complete** -- post-workstream vision
- **After ML models are trained** -- post-training vision
- **After full integration and final comparison** -- publication-readiness vision
- **Any time the project feels stuck** -- strategic reset

Always run the Assistant AI first to refresh briefings, then the Visionary.

### 8.3 Assistant AI Prompt

Launch in any session (no worktree needed -- the Assistant only writes to `vision/`).

**Prompt:**
> Read `vision/briefings/INSTRUCTIONS.md` completely -- this is your playbook. It lists
> every file you must read and every briefing you must produce. Read ALL files listed
> in the instructions (CLAUDE.md, GOALS.md, TODO.md, CRITICAL.md, all 9 workstream
> reports in reports/workstreams/, reports/head-ai-log.md, workstreams/README.md,
> workstreams/INTERFACES.md, pyproject.toml, and the key source files listed). Then
> write or update all 5 briefing files in vision/briefings/. Be honest about
> limitations -- the Visionary needs truth, not optimism. Quantify everything.
> Include opportunity signals after every limitation. Update vision/log/assistant-log.md
> continuously as you work.

**Expected output:**
- 5 briefing files in `vision/briefings/` (created or updated):
  `project-overview.md`, `current-progress.md`, `remaining-goals.md`,
  `architecture.md`, `known-limitations.md`
- Updated `vision/log/assistant-log.md`

**Verify:**
```bash
ls vision/briefings/*.md  # Should show 6 files (INSTRUCTIONS + 5 briefings)
# Each briefing should have "Last updated:" at the top with today's date
```

### 8.4 Visionary AI Prompt

Launch in a fresh session (no worktree needed).

**Prompt:**
> You are the Visionary AI for the StateBind project. Read ONLY files inside the
> `vision/` directory -- you never read source code or any file outside this folder.
> Start by reading `vision/ideas/README.md` for your rules and the idea template.
> Then read all 5 briefings in `vision/briefings/`. Then read any existing idea files
> in `vision/ideas/` to avoid repetition. Finally, read `vision/log/visionary-log.md`
> for your running log. Generate 5-15 bold improvement ideas and write each as a
> numbered file in `vision/ideas/` following the template in the README. Think like a
> PI, a drug discovery veteran, and an ML researcher simultaneously. Be ambitious --
> if an idea feels too bold, it's probably the right size. Update
> `vision/log/visionary-log.md` continuously as you work.

**Expected output:**
- 5-15 new idea files in `vision/ideas/` (e.g., `001-ensemble-docking.md`)
- Updated `vision/log/visionary-log.md`

**Verify:**
```bash
ls vision/ideas/*.md      # Should show README.md + numbered idea files
# Each idea should have Status: proposed, a filled-in template, and an
# implementation sketch section
```

**Important:** The Visionary AI should NOT be told to read CLAUDE.md, source code, or
any file outside `vision/`. Its entire context comes from the Assistant's briefings.
This constraint forces the Visionary to think at the strategic level.

### 8.5 Head AI: Processing Visionary Ideas

After the Visionary completes a session, tell the Head AI:

**Prompt:**
> Read all idea files in `vision/ideas/` that have `Status: proposed`. For each idea,
> decide whether to accept or defer. For accepted ideas, create a workstream brief in
> `workstreams/`, add a deployment prompt to `HumanOnly/AI-Operations-Manual.md`, and update
> `workstreams/README.md`. Update the idea file's Status field to `accepted` or
> `deferred`. Document every decision with rationale in `reports/head-ai-log.md`.
> Follow the workstream creation patterns in existing briefs (e.g.,
> `workstreams/01-chemistry-foundation.md`).

**Expected output:**
- Idea status fields updated (`accepted` or `deferred`)
- New workstream briefs for accepted ideas
- Updated `HumanOnly/AI-Operations-Manual.md` with new deployment prompts
- Updated `workstreams/README.md` with new entries
- Updated `reports/head-ai-log.md` with decision rationale

### 8.6 Running Documentation Requirement

All AI roles must maintain their running logs continuously -- this is non-negotiable
(CLAUDE.md Rule 10). The logs serve as context recovery when chat compacts and as
handoff documents for replacement agents.

| Role | Log File | Update Frequency |
|------|----------|-----------------|
| Assistant AI | `vision/log/assistant-log.md` | After each briefing written |
| Visionary AI | `vision/log/visionary-log.md` | After every 2-3 ideas |
| Head AI | `reports/head-ai-log.md` | After every merge, decision, or task assignment |
| Admin AI | `admin/log/admin-log.md` | After every batch of suggestions |

---

## 9. Admin AI

The Admin AI monitors infrastructure quality -- documentation accuracy, scaffolding
completeness, config consistency, and stale content. It does NOT execute workstreams
or make architectural decisions. It audits and suggests.

### 9.1 When to Run

- Before handing off to a new Head AI (knowledge transfer audit)
- After merging a batch of workstreams
- After major documentation changes
- When a new agent reports confusion from stale docs
- Periodically as a health check

### 9.2 Admin AI Prompt

Launch in any session (no worktree needed -- the Admin AI only writes to `admin/`).

**Prompt:**
> Read `admin/INSTRUCTIONS.md` completely -- this is your audit playbook. It lists every
> file you must read and every check you must perform. Read ALL files listed in the
> instructions (CLAUDE.md, CRITICAL.md, GOALS.md, TODO.md, pyproject.toml, all
> `__init__.py` files in src/statebind/, all module READMEs, all config files, CI
> workflow, reports, workstreams/README.md). Then systematically audit the project's
> infrastructure: documentation accuracy, scaffolding completeness, config consistency,
> cross-reference integrity, and stale content. Write structured suggestions to
> `admin/suggestions.md` following the template in that file. Prioritize P0 items
> (things that are broken or actively misleading) above all else. Update
> `admin/log/admin-log.md` continuously as you work. Focus on infrastructure health,
> not scientific or architectural decisions.

**Expected output:**
- Updated `admin/suggestions.md` with structured suggestions (ID, priority, category)
- Updated `admin/log/admin-log.md` with audit session details

**Verify:**
```bash
cat admin/suggestions.md | head -30
# Should show suggestions with IDs (S001, S002...), priorities, and categories
# Each suggestion should have a specific file:line reference
```

### 9.3 Processing Admin AI Suggestions (Head AI)

After the Admin AI session, tell the Head AI:

**Prompt:**
> Read `admin/suggestions.md`. For each suggestion with Status: suggested, decide
> whether to accept and implement, or mark as wont-fix. For P0 items (broken/wrong),
> fix immediately. For P1 items (stale/misleading), fix or schedule. For P2/P3, use
> your judgment. Update each suggestion's status field and add notes. Log your
> decisions in `reports/head-ai-log.md`.

**Expected output:**
- Suggestion status fields updated (`accepted`, `implemented`, or `wont-fix`)
- Fixes applied directly to ML branch for small items
- Updated `reports/head-ai-log.md` with decision rationale

---

## 10. AI Employee Directory

Complete reference for every AI role in the StateBind development system. This directory
is the authoritative source for understanding who does what, who reports to whom, and
where to find each role's documentation and prompts.

### 10.1 Organizational Chart

```
                    +-----------------------+
                    |    Human Operator     |
                    |    (You)              |
                    +---+-------+-------+---+
                        |       |       |
           +------------+   +---+---+   +------------+
           |                |       |                |
  +--------v--------+  +---v---+  +v-----------+  +-v-----------+
  |    Head AI       |  | Admin |  | Assistant  |  | Modular     |
  |  (Coordinator)   |  |  AI   |  |    AI      |  | Agents      |
  |                  |  |(Audit)|  | (Briefing  |  | (WS01-WS09) |
  +--+----------+----+  +---+---+  |  Writer)   |  +-------------+
     |          |            |     +------+------+
     |          |            |            |
     |     Merges completed  |     +------v------+
     |     agent worktrees   |     | Visionary   |
     |     into ML branch    |     |    AI       |
     |                       |     | (Ideas)     |
     |   Reviews suggestions |     +-------------+
     |   from Admin AI       |
     |                       |
     |   Reviews ideas       |
     |   from Visionary AI   |
     |                       |
     +--- Creates new        |
          workstream briefs   |
          for Modular Agents  |
```

### 10.2 Role Details

#### Head AI -- Coordinator & Decision Maker

| Attribute | Value |
|-----------|-------|
| **Branch** | ML (always, no worktree) |
| **Reads** | CLAUDE.md, GOALS.md, TODO.md, CRITICAL.md, workstreams/README.md, reports/head-ai-log.md, vision/ideas/*.md, admin/suggestions.md |
| **Writes** | reports/head-ai-log.md, workstreams/ (new briefs), HumanOnly/AI-Operations-Manual.md (new prompts), CLAUDE.md (architecture changes), CRITICAL.md (new gotchas), idea status fields, suggestion status fields |
| **Reports to** | Human Operator |
| **Receives from** | Modular Agents (completed worktrees), Visionary AI (ideas), Admin AI (suggestions) |
| **Documentation** | `reports/head-ai-log.md` |
| **Prompt location** | HumanOnly/AI-Operations-Manual.md Section 2 |

**Key responsibilities:**
- Merge completed worktrees into ML and push to `origin/ML`
- Triage Visionary ideas (accept/defer) and create workstream briefs
- Triage Admin suggestions (implement/schedule/wont-fix)
- Resolve cross-workstream conflicts
- Make architectural decisions with rationale
- Maintain running log continuously

---

#### Modular Agent -- Workstream Executor

| Attribute | Value |
|-----------|-------|
| **Branch** | `ws{NN}/{description}` in isolated worktree at `.claude/worktrees/ws{NN}-{description}` |
| **Reads** | CLAUDE.md, workstreams/{NN}-*.md, relevant module README.md/CRITICAL.md, INTERFACES.md, its own report |
| **Writes** | Source code in its scope, tests, reports/workstreams/ws{NN}-report.md |
| **Reports to** | Head AI (via completed worktree + report) |
| **Receives from** | Human Operator (prompt with worktree name) |
| **Documentation** | `reports/workstreams/ws{NN}-report.md` |
| **Prompt location** | HumanOnly/AI-Operations-Manual.md Section 3 (one prompt per workstream) |

**Key responsibilities:**
- Execute one workstream in isolation
- Follow interface contracts from INTERFACES.md
- Write tests for all new code (test count must not decrease)
- Continuously update progress report
- Stay within scope (never modify files listed in "Files NOT to Touch")

---

#### Assistant AI -- Briefing Writer

| Attribute | Value |
|-----------|-------|
| **Branch** | Any (no worktree needed, writes only to `vision/`) |
| **Reads** | Everything: CLAUDE.md, GOALS.md, TODO.md, CRITICAL.md, all reports, key source files, workstreams/README.md, INTERFACES.md, pyproject.toml, admin/ directory |
| **Writes** | `vision/briefings/*.md` (5 briefing files), `vision/log/assistant-log.md` |
| **Reports to** | Human Operator |
| **Receives from** | The entire codebase (read-only) |
| **Documentation** | `vision/log/assistant-log.md` |
| **Prompt location** | HumanOnly/AI-Operations-Manual.md Section 8.3 |
| **Playbook** | `vision/briefings/INSTRUCTIONS.md` |

**Key responsibilities:**
- Translate full project state into digestible briefings for Visionary AI
- Produce 5 briefing files: project-overview, current-progress, remaining-goals, architecture, known-limitations
- Be honest and quantitative (no optimism bias)
- Refresh briefings before every Visionary session
- Include "opportunity signals" after every limitation

---

#### Visionary AI -- Strategic Thinker

| Attribute | Value |
|-----------|-------|
| **Branch** | Any (no worktree needed, writes only to `vision/`) |
| **Reads** | ONLY files inside `vision/` (briefings, own ideas, own log) -- NEVER source code |
| **Writes** | `vision/ideas/{NNN}-*.md` (idea files), `vision/log/visionary-log.md` |
| **Reports to** | Head AI (via ideas) |
| **Receives from** | Assistant AI (via briefings in `vision/briefings/`) |
| **Documentation** | `vision/log/visionary-log.md` |
| **Prompt location** | HumanOnly/AI-Operations-Manual.md Section 8.4 |
| **Playbook** | `vision/ideas/README.md` |

**Key responsibilities:**
- Propose 5-15 bold improvement ideas per session
- Think simultaneously as PI, drug discovery veteran, and ML researcher
- Never read source code or implement anything
- Reference briefings to ground ideas in project reality
- Categorize ideas: Scientific Rigor, Pipeline Gaps, ML Improvements, Validation, Novel Approaches, Infrastructure

---

#### Admin AI -- Infrastructure Monitor

| Attribute | Value |
|-----------|-------|
| **Branch** | Any (no worktree needed, writes only to `admin/`) |
| **Reads** | CLAUDE.md, CRITICAL.md, GOALS.md, TODO.md, all `__init__.py`, all module READMEs, configs/, reports/, pyproject.toml, test structure, .gitignore, CI workflow |
| **Writes** | `admin/suggestions.md`, `admin/log/admin-log.md` |
| **Reports to** | Head AI (via suggestions) |
| **Receives from** | The infrastructure layer of the codebase (read-only) |
| **Documentation** | `admin/log/admin-log.md` |
| **Prompt location** | HumanOnly/AI-Operations-Manual.md Section 9.2 |
| **Playbook** | `admin/INSTRUCTIONS.md` |

**Key responsibilities:**
- Audit documentation accuracy, scaffolding completeness, config consistency
- Write structured suggestions with priority (P0-P3) and category
- Never implement changes -- only observe and suggest
- Focus on infrastructure quality, not scientific or architectural decisions

---

### 10.3 Information Flow

```
Full Codebase ----(reads)----> Assistant AI ----(briefings)----> Visionary AI
                                                                      |
                                                                (ideas, proposed)
                                                                      |
                                                                      v
Full Codebase ----(reads)----> Head AI <-------(suggestions)---- Admin AI
                                  |
                            (accepts ideas,
                             creates workstreams,
                             implements suggestions)
                                  |
                                  v
                            Modular Agents
                            (execute workstreams
                             in isolated worktrees)
                                  |
                            (completed worktrees
                             with code + tests)
                                  |
                                  v
                            Head AI merges
                            to ML branch
```

### 10.4 Dependencies Between Roles

| Producer | Consumer | What Flows | Where It Lives |
|----------|----------|------------|----------------|
| Assistant AI | Visionary AI | 5 briefing files | `vision/briefings/*.md` |
| Visionary AI | Head AI | Numbered idea files | `vision/ideas/{NNN}-*.md` |
| Admin AI | Head AI | Structured suggestions | `admin/suggestions.md` |
| Head AI | Modular Agents | Workstream brief files | `workstreams/{NN}-*.md` |
| Head AI | Human Operator | Agent prompts | `HumanOnly/AI-Operations-Manual.md` Sections 3, 8, 9 |
| Modular Agents | Head AI | Completed worktrees | `.claude/worktrees/ws{NN}-*` |
| All roles | Future selves | Running documentation | See log file per role above |
