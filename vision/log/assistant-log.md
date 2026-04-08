# Assistant AI -- Running Log

## Status

- **Last session:** Session 2 (2026-04-07)
- **Briefings written:** 5 / 5
- **Last updated:** 2026-04-07T20:00:00+00:00

---

## Sessions

### Session 2 -- 2026-04-07

Second briefing session. All 5 briefings updated to reflect 3 new workstreams (WS11, WS12, WS13), test count increase (548 -> 646), and retrospective validation results.

#### Files Read

Core documentation:
- CLAUDE.md (updated: 91 source files, 22 test files, 646 tests, 12 configs, 49 scripts)
- GOALS.md (updated: all targets met, retrospective EF@10 results, 12/12 workstreams)
- TODO.md (last updated 2026-04-05, reflects WS11-13 completion)
- CRITICAL.md (updated: 4-tier docking cascade, GNINA v1.1 details, retrospective pre-cutoff models)

Workstream system:
- workstreams/README.md (12 workstreams, test count progression to 646)
- workstreams/INTERFACES.md (10 contracts, added WS11/12/13 interfaces)

All 12 workstream reports:
- reports/workstreams/ws01-report.md (Chemistry Foundation -- complete, unchanged)
- reports/workstreams/ws02-report.md (Scoring Integration -- complete, unchanged)
- reports/workstreams/ws03-report.md (Statistical Testing -- complete, unchanged)
- reports/workstreams/ws04-report.md (Docking Proxy -- complete, unchanged)
- reports/workstreams/ws05-report.md (Visualization -- complete, unchanged)
- reports/workstreams/ws06-report.md (CI/CD -- complete, unchanged)
- reports/workstreams/ws07-report.md (Conditional VAE -- complete, updated with VAE v3 SELFIES results)
- reports/workstreams/ws08-report.md (MPNN Affinity -- complete, updated with training results)
- reports/workstreams/ws09-report.md (ADMET Predictor -- complete, updated with training results)
- reports/workstreams/ws11-report.md (GNINA Docking -- NEW, complete)
- reports/workstreams/ws12-report.md (Pareto Optimization -- NEW, complete)
- reports/workstreams/ws13-report.md (Retrospective Validation -- NEW, complete)
- reports/head-ai-log.md (updated through 2026-04-08, generation 6)

Key source files:
- src/statebind/ranking/scoring.py (4-tier docking cascade: GNINA -> MPNN -> proxy -> stub)
- src/statebind/baselines/scoring.py (component scorers, 3 reference binders, unchanged)
- src/statebind/ml/__init__.py (HAS_TORCH flags, Pydantic config exports, unchanged)
- src/statebind/evaluation/comparison.py (ComparativeResult now includes pareto + retrospective fields)
- pyproject.toml (6 dependency groups, unchanged)

Admin system:
- admin/suggestions.md (24 suggestions: 18 implemented, 4 wont-fix, 2 P0 awaiting triage)
- admin/log/admin-log.md (2 sessions: 2026-03-30 and 2026-04-05)

Vision system:
- vision/briefings/INSTRUCTIONS.md (unchanged)
- vision/ideas/ -- 12 ideas (001-012): 3 accepted (005->WS11, 008->WS12, 009->WS13), 9 deferred
- vision/log/assistant-log.md (this file, Session 1 from 2026-03-30)

#### Briefings Updated

All 5 briefings updated with "Changes since last briefing" sections:

- `project-overview.md` -- Updated Current Position with retrospective validation narrative, 12 workstreams, 646 tests, GNINA tier 0 docking, Pareto optimization. The project story is now nuanced: null hypothesis retained on mean score, but state-aware has 10x enrichment for future drugs.
- `current-progress.md` -- Added WS11/12/13 to workstream table, updated all codebase metrics (91 files, 22 test files, 646 tests, 12 configs, 49 scripts), updated docking cascade to 4-tier, added pre-cutoff model info, updated merge history.
- `remaining-goals.md` -- Marked 3 gaps as addressed (physics docking, Pareto, retrospective validation). Added "What Retrospective Validation Revealed" section with EF@10 results. Updated honest assessment. Remaining gaps reduced from 10 to 7.
- `architecture.md` -- Updated docking cascade to 4-tier with GNINA. Added new modules (docking.py, pareto.py, pareto_comparison.py, docking_analysis.py, retrospective.py). Updated config table to 12 YAMLs. Updated ComparativeResult fields.
- `known-limitations.md` -- Rewrote 3 limitations (docking, weighted sum, external validation) to reflect WS11/12/13. Added 2 new limitations (GNINA runtime cost, retrospective sample size). Updated peer reviewer and practitioner sections.

#### Notable Observations

1. **Retrospective validation is the project's strongest result.** State-aware EF@10 = 4.95/7.72 vs static 0.47/0.79. This 10x enrichment factor fundamentally changes the project narrative. The null hypothesis was retained on mean score, but the state-aware pipeline is dramatically better at identifying future approved drugs.

2. **Three Visionary ideas were implemented.** Ideas 005 (GNINA), 008 (Pareto), 009 (Retrospective) all became workstreams and were completed. The Vision System's idea pipeline is working.

3. **9 Visionary ideas remain deferred.** Updated briefings should help the Visionary prioritize which to propose next. The strongest remaining candidates appear to be: 003 (Kinome selectivity), 004 (Uncertainty quantification), 006 (Learned similarity).

4. **Admin AI has completed 2 audit sessions.** 24 suggestions total, 18 implemented. Two P0 suggestions (S013, S014) await triage. Root-level documentation is mostly accurate; module-level CRITICAL.md files are the main remaining gap.

5. **GNINA requires GPU.** The scoring cascade behavior differs between login nodes (MPNN tier 1) and GPU compute nodes (GNINA tier 0). This means test results and scoring results depend on the execution environment.

6. **Pre-cutoff MPNN models performed surprisingly well.** The pre-2010 model (only 2,974 training compounds) achieved R^2=0.717 and Pearson=0.854 -- better than the full model (R^2=0.6863, Pearson=0.8323) on 10,466 compounds. This suggests the pre-2010 data may be higher quality (more carefully curated early literature).

7. **The project has a complete, tested, and validated pipeline.** 12/12 workstreams, 646 tests, 3 trained ML models + 4 pre-cutoff models, physics-based docking, Pareto analysis, retrospective validation. The infrastructure gap from Session 1 (everything waiting on GPU training) is fully resolved.

8. **The null hypothesis nuance matters for briefings.** The static baseline wins on mean score (0.5437 vs 0.4378), but the state-aware pipeline wins on diversity (0.9056 vs 0.5684), max score (0.7794 vs 0.7288), candidate volume (461 vs 30), novelty (431 new molecules), and retrospective enrichment (10x). The briefings must convey both sides honestly.

#### Changes Since Last Session

| Metric | Session 1 (2026-03-30) | Session 2 (2026-04-07) | Delta |
|--------|----------------------|----------------------|-------|
| Workstreams | 9/9 | 12/12 | +3 (WS11, WS12, WS13) |
| Tests | 548 | 646 | +98 |
| Python source files | 84 | 91 | +7 |
| Test files | 19 | 22 | +3 |
| YAML configs | 6 | 12 | +6 |
| Pipeline scripts | 37+ | 49 | +12 |
| Docking cascade | 3-tier | 4-tier | +GNINA |
| Visionary ideas | 0 | 12 (3 accepted) | +12 |
| Admin suggestions | 0 | 24 (18 implemented) | +24 |
| Pre-cutoff models | 0 | 4 (2 MPNN + 2 VAE) | +4 |

---

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
- reports/workstreams/ws01-report.md (Chemistry Foundation -- complete)
- reports/workstreams/ws02-report.md (Scoring Integration -- complete)
- reports/workstreams/ws03-report.md (Statistical Testing -- complete)
- reports/workstreams/ws04-report.md (Docking Proxy -- complete)
- reports/workstreams/ws05-report.md (Visualization -- complete)
- reports/workstreams/ws06-report.md (CI/CD -- complete)
- reports/workstreams/ws07-report.md (Conditional VAE -- complete)
- reports/workstreams/ws08-report.md (MPNN Affinity -- complete)
- reports/workstreams/ws09-report.md (ADMET Predictor -- complete)
- reports/head-ai-log.md (Head AI merge log and decisions)

Key source files:
- src/statebind/ranking/scoring.py (unified scoring, DEFAULT_WEIGHTS, cascading fallback)
- src/statebind/baselines/scoring.py (component scorers, reference binders, docking stub)
- src/statebind/ml/__init__.py (HAS_TORCH flags, Pydantic config exports)
- src/statebind/evaluation/comparison.py (head-to-head comparison framework)
- pyproject.toml (package definition, 6 dependency groups)

Admin system:
- admin/suggestions.md (empty template -- Admin AI never run)
- admin/log/admin-log.md (empty template -- Admin AI never run)

Vision system:
- vision/briefings/INSTRUCTIONS.md (this role's playbook)
- vision/ideas/README.md (Visionary AI rules and template)
- vision/log/assistant-log.md (this file -- was empty template)
- No existing briefing files
- No existing idea files

#### Briefings Created

- `project-overview.md` -- Created. Scientific thesis, 4 conformational states, 2 pipelines, unified scoring, positioning as computational hypothesis generation.
- `current-progress.md` -- Created. All 9 WS complete, 540 tests, 86 source files, 13 subpackages. ML models untrained. Scoring: Morgan/QED active, proxy MLP active, MPNN adapter ready. Training data on disk.
- `remaining-goals.md` -- Created. Gap analysis: 5 met, 2 partial, 11 not met. All unmet goals depend on ML training. 10 gaps that current plans do NOT address (physics docking, validation, selectivity, retrosynthesis, continuous conformations, pre-training, multi-objective, ADMET in scoring, uncertainty, active learning).
- `architecture.md` -- Created. 13 subpackages, acyclic dependency graph, scoring deep dive with 4 components and 3-tier fallback, ML model architecture summaries, config system, artifact-based communication.
- `known-limitations.md` -- Created. 15 limitations organized into 6 categories (scoring, scientific, ML, pipeline, peer review, practitioner). Each with opportunity signal.

#### Notable Observations

1. **The project is at a single bottleneck.** Everything waits on GPU training of 3 ML models. The entire infrastructure is ready -- adapters, fallbacks, statistical tests, visualization -- but produces meaningless results until the models are trained.

2. **The docking proxy MLP is trained on 34 molecules.** 9 binders + 25 decoys. It achieves AUROC >0.7 on this set, but this is almost certainly overfitting. Any novel candidate structurally different from the training set will get an unreliable score.

3. **The mutation-to-state mapping is uninformative.** All 17 mutations map to DFGin/aCin. This is a dataset limitation, not a code limitation -- the context module works correctly but has no discriminative signal in the current data.

4. **The state_specificity component (15%) is the ONLY axis for state-aware advantage.** This is by design (fair comparison), but it means the effect size is inherently small. If the Visionary proposes ideas that amplify the state-aware signal, they should consider whether the 15% weight is sufficient.

5. **No ideas have been proposed yet.** This is the first Vision System session. The ideas directory is empty. The Visionary has a clean slate.

6. **Admin AI has never been run.** Documentation may have stale references (e.g., CLAUDE.md still says 359 tests in some sections).

#### Changes Since Last Session

N/A -- this is the first session.

---

## Current State

**What is done:** All 5 briefing files updated for Session 2. This log updated with Session 2 entry.

**Next steps:**
1. Visionary AI should be re-launched to read updated briefings and propose new ideas (9 deferred ideas exist; updated briefings provide fresh context)
2. On next Assistant AI session: re-read all source files, check for changes since 2026-04-07
3. Pay particular attention to whether a full comparison re-run with GNINA+Pareto+Retrospective all merged has been executed
4. Check if Admin AI P0 suggestions S013/S014 have been triaged
5. Check if any new workstreams have been created from deferred Visionary ideas

---

## Context Recovery

If your context compacts:
1. Re-read this log
2. Re-read `vision/briefings/INSTRUCTIONS.md`
3. Check which briefing files exist and their "Last updated" timestamps
4. Resume from "Next steps" above
