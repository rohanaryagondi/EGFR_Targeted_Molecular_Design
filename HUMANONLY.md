# Human Operator Guide: Prompting AI Agents and Verifying Their Work

This document is for you, the human operator. It tells you exactly what to say to each
AI agent, what to expect back, and how to verify the output. No AI should read this file
as instructions -- it is your playbook for orchestrating them.

---

## 1. Overview

StateBind is a 12-module computational biology pipeline for EGFR-targeted molecular
design. It tests whether conformational state-aware design outperforms static
single-structure design. The codebase has 72 Python source files, 359 tests, and 3
neural network architectures (VAE, MPNN, ADMET) that are written but not yet trained.

There are 9 independent workstreams that upgrade the pipeline from its current state
(SMILES string heuristics, a constant-0.5 docking stub, no statistical testing) to a
research-grade system (RDKit chemistry, trained ML models, formal hypothesis testing).

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

The ML models (VAE, MPNN, ADMET) have their architectures, configs, and training scripts
written. They are NOT trained. Training requires a GPU and happens on your HPC cluster,
not inside an AI coding session. Section 4 covers this.

Current test count: 359. Target after all workstreams: 500+.
Current module count: 12 subpackages. Target after WS01: 13 (adds `chemistry/`).

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
> roadmap and task status, and workstreams/README.md for the workstream system. Finally,
> read CRITICAL.md for cross-cutting concerns. You are the head developer coordinating
> 9 workstreams across 12 modules. When I ask about a workstream, read its brief in
> workstreams/ before answering. Be detailed yet concise.

The head AI should NOT execute workstreams directly. Its job is to:
- Answer architectural questions ("Can WS04 run before WS02?")
- Resolve interface conflicts between workstreams
- Review modular agent output for correctness against INTERFACES.md
- Decide when integration tasks (TODO.md Section 6) are ready to start
- Merge completed modular agent worktrees into ML and push to GitHub

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


### WS01: Chemistry Foundation

**Prompt:**
> Read these files in order: (1) CLAUDE.md, (2) workstreams/01-chemistry-foundation.md,
> (3) workstreams/INTERFACES.md (Contract 1), (4) src/statebind/baselines/README.md,
> (5) src/statebind/baselines/CRITICAL.md. Create the src/statebind/chemistry/ package
> implementing Morgan fingerprints, molecular descriptors, SMILES validation, and SA
> scoring. Follow the interface contracts exactly. Run all tests when done. Be detailed
> yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/02-scoring-integration.md,
> (3) workstreams/INTERFACES.md (Contract 1 and 7), (4) src/statebind/baselines/scoring.py,
> (5) src/statebind/ranking/scoring.py, (6) src/statebind/ranking/CRITICAL.md. Wire the
> chemistry module from WS01 into scoring. Upgrade n-gram similarity to Morgan fingerprints
> with fallback. Replace heuristic druglikeness with QED + Lipinski + SA score where RDKit
> is available. Run all tests. Be detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/03-statistical-testing.md,
> (3) workstreams/INTERFACES.md (Contract 3), (4) src/statebind/evaluation/README.md,
> (5) src/statebind/evaluation/CRITICAL.md. Create evaluation/statistics.py with
> Mann-Whitney U tests, bootstrap confidence intervals, and Cohen's d effect sizes.
> Create evaluation/sensitivity.py for scoring weight sensitivity analysis. Run all
> tests. Be detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/04-docking-proxy.md,
> (3) workstreams/INTERFACES.md (Contract 2), (4) src/statebind/baselines/scoring.py
> (lines 135-149 for the stub), (5) src/statebind/baselines/CRITICAL.md. Create a small
> MLP docking proxy trained on embedded SAR data from known EGFR inhibitors. The proxy
> must return varied scores, not constant 0.5. Wire it into the scoring function as a
> fallback between the MPNN and the stub. Run all tests. Be detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/05-visualization.md,
> (3) src/statebind/evaluation/README.md, (4) src/statebind/evaluation/CRITICAL.md.
> Create evaluation/plotting.py with matplotlib figures for score distributions, diversity
> comparisons, top-K composition charts, and state atlas heatmaps. All figures must be
> saveable to files without requiring a display. Run all tests. Be detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/06-ci-cd.md, (3) pyproject.toml. Create
> .github/workflows/ci.yml with a Python 3.10-3.12 test matrix running pytest and ruff
> check on every push and pull request. Add status badges to README.md. Be detailed yet
> concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/07-conditional-vae.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) src/statebind/generation/CRITICAL.md. Create the data preparation script for
> ChEMBL EGFR actives, and the VAE integration module that converts VAE output into
> StateConditionedCandidate objects compatible with the existing generation pipeline.
> Run all tests. Be detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/08-mpnn-affinity.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) src/statebind/ranking/CRITICAL.md, (6) workstreams/INTERFACES.md (Contract 4).
> Create the data preparation script for ChEMBL EGFR affinity data, the affinity
> predictor adapter that loads a trained MPNN checkpoint, and the cascading fallback in
> ranking/scoring.py: MPNN -> docking proxy -> constant 0.5 stub. Run all tests. Be
> detailed yet concise.

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
> Read: (1) CLAUDE.md, (2) workstreams/09-admet-predictor.md,
> (3) src/statebind/ml/README.md, (4) src/statebind/ml/CRITICAL.md,
> (5) workstreams/INTERFACES.md (Contract 6). Create the data preparation script for
> TDC ADMET benchmarks, the ADMET predictor adapter that loads a trained checkpoint, and
> the ADMET filter gate that flags or excludes candidates with hERG liability or CYP3A4
> inhibition. Run all tests. Be detailed yet concise.

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

The ML models are written but not trained. Training requires a GPU with CUDA. Do this
on your HPC cluster, not inside an AI coding session.

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
