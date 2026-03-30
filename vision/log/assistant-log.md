# Assistant AI -- Running Log

## Status

- **Last session:** Session 1 (2026-03-30)
- **Briefings written:** 5 / 5
- **Last updated:** 2026-03-30T00:00:00+00:00

---

## Sessions

### Session 1 -- 2026-03-30

First briefing session. All 5 briefings created from scratch. No prior briefings existed.

#### Files Read

Core documentation:
- CLAUDE.md (full project reference, ~700 lines)
- GOALS.md (success criteria and numeric targets)
- TODO.md (development roadmap, last updated 2026-03-28)
- CRITICAL.md (cross-cutting concerns and known issues)

Workstream system:
- workstreams/README.md (workstream index and status table)
- workstreams/INTERFACES.md (7 interface contracts)

All 9 workstream reports:
- reports/workstreams/ws01-report.md (Chemistry Foundation — complete)
- reports/workstreams/ws02-report.md (Scoring Integration — complete)
- reports/workstreams/ws03-report.md (Statistical Testing — complete)
- reports/workstreams/ws04-report.md (Docking Proxy — complete)
- reports/workstreams/ws05-report.md (Visualization — complete)
- reports/workstreams/ws06-report.md (CI/CD — complete)
- reports/workstreams/ws07-report.md (Conditional VAE — complete)
- reports/workstreams/ws08-report.md (MPNN Affinity — complete)
- reports/workstreams/ws09-report.md (ADMET Predictor — complete)
- reports/head-ai-log.md (Head AI merge log and decisions)

Key source files:
- src/statebind/ranking/scoring.py (unified scoring, DEFAULT_WEIGHTS, cascading fallback)
- src/statebind/baselines/scoring.py (component scorers, reference binders, docking stub)
- src/statebind/ml/__init__.py (HAS_TORCH flags, Pydantic config exports)
- src/statebind/evaluation/comparison.py (head-to-head comparison framework)
- pyproject.toml (package definition, 6 dependency groups)

Admin system:
- admin/suggestions.md (empty template — Admin AI never run)
- admin/log/admin-log.md (empty template — Admin AI never run)

Vision system:
- vision/briefings/INSTRUCTIONS.md (this role's playbook)
- vision/ideas/README.md (Visionary AI rules and template)
- vision/log/assistant-log.md (this file — was empty template)
- No existing briefing files
- No existing idea files

#### Briefings Created

- `project-overview.md` — Created. Scientific thesis, 4 conformational states, 2 pipelines, unified scoring, positioning as computational hypothesis generation.
- `current-progress.md` — Created. All 9 WS complete, 540 tests, 86 source files, 13 subpackages. ML models untrained. Scoring: Morgan/QED active, proxy MLP active, MPNN adapter ready. Training data on disk.
- `remaining-goals.md` — Created. Gap analysis: 5 met, 2 partial, 11 not met. All unmet goals depend on ML training. 10 gaps that current plans do NOT address (physics docking, validation, selectivity, retrosynthesis, continuous conformations, pre-training, multi-objective, ADMET in scoring, uncertainty, active learning).
- `architecture.md` — Created. 13 subpackages, acyclic dependency graph, scoring deep dive with 4 components and 3-tier fallback, ML model architecture summaries, config system, artifact-based communication.
- `known-limitations.md` — Created. 15 limitations organized into 6 categories (scoring, scientific, ML, pipeline, peer review, practitioner). Each with opportunity signal.

#### Notable Observations

1. **The project is at a single bottleneck.** Everything waits on GPU training of 3 ML models. The entire infrastructure is ready — adapters, fallbacks, statistical tests, visualization — but produces meaningless results until the models are trained.

2. **The docking proxy MLP is trained on 34 molecules.** 9 binders + 25 decoys. It achieves AUROC >0.7 on this set, but this is almost certainly overfitting. Any novel candidate structurally different from the training set will get an unreliable score.

3. **The mutation-to-state mapping is uninformative.** All 17 mutations map to DFGin/aCin. This is a dataset limitation, not a code limitation — the context module works correctly but has no discriminative signal in the current data.

4. **The state_specificity component (15%) is the ONLY axis for state-aware advantage.** This is by design (fair comparison), but it means the effect size is inherently small. If the Visionary proposes ideas that amplify the state-aware signal, they should consider whether the 15% weight is sufficient.

5. **No ideas have been proposed yet.** This is the first Vision System session. The ideas directory is empty. The Visionary has a clean slate.

6. **Admin AI has never been run.** Documentation may have stale references (e.g., CLAUDE.md still says 359 tests in some sections).

#### Changes Since Last Session

N/A — this is the first session.

---

## Current State

**What is done:** All 5 briefing files created and written to vision/briefings/. This log updated.

**Next steps:**
1. Visionary AI should be launched to read briefings and propose ideas
2. On next Assistant AI session: re-read all source files, check for changes since 2026-03-30, update briefings with "Changes since last briefing" sections
3. Pay particular attention to whether ML models have been trained (check for checkpoint files)
4. Update test count if it has changed

---

## Context Recovery

If your context compacts:
1. Re-read this log
2. Re-read `vision/briefings/INSTRUCTIONS.md`
3. Check which briefing files exist and their "Last updated" timestamps
4. Resume from "Next steps" above
