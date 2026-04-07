# Project Log

Timestamped history of major project events. Newest first.

---

## 2026-04-07 (night)

**WS11 + WS12 merged, sklearn fix, 618 tests passing**

Head AI Generation 5 reviewed and merged two workstreams:

- **WS11 (GNINA Docking):** Physics-based docking as tier 0 in scoring cascade. GNINA v1.1 wrapper, receptor preparation for all 4 states, GPU guard, 33 new tests. Validation: binders -7.32 vs non-binders -4.16 kcal/mol. Agent had not committed — Head AI committed and merged.
- **WS12 (Pareto Optimization):** Weight-free hypervolume comparison alongside weighted-sum scoring. Pareto front plots (2D projections + parallel coordinates), 36 new tests. Agent committed properly.

**sklearn import fix:** `structure/clustering.py` used unconditional sklearn import, violating the project's optional dependency pattern. Wrapped in try/except with HAS_SKLEARN guard. Tests updated to skip gracefully. Also fixed torch_geometric skip in ADMET tests.

**Testing policy established:** Three tiers documented in `docs/ai-guide/testing-and-deps.md`. Changes to scoring/ML/docking/evaluation require SLURM GPU test (scripts/run_tests_all.slurm). Gold standard: 618 passed, 0 skipped, 0 failures (verified on SLURM job 7587145, L40S GPU, 65 min).

**Test count:** 548 → 618 (+33 docking, +36 Pareto, +1 import test).

---

## 2026-04-07 (evening)

**Vision idea review: 3 accepted, 9 deferred**
Head AI Generation 4 reviewed all 12 Visionary ideas. Decision framework: accept ideas that address root causes of the null result (scoring quality, evaluation methodology, validation) with medium effort. Defer architecture changes, Epic-scope ideas, and premature optimizations.

Accepted:
- **005: GNINA Docking** → WS11: Real physics-based docking for 20% of scoring weight
- **008: Pareto Optimization** → WS12: Weight-free hypervolume comparison
- **009: Retrospective Time-Split Validation** → WS13: Predict future drugs from historical data

Key deferrals: 001 (continuous conditioning -- null result not caused by discretization), 006 (learned similarity -- risk of appearing to p-hack), 002 (3D diffusion -- Epic scope).

**3 workstream briefs created**
Full briefs with interface contracts, testing requirements, and definitions of done:
- `workstreams/11-gnina-docking.md`
- `workstreams/12-pareto-optimization.md`
- `workstreams/13-retrospective-validation.md`

**All project documentation updated**
- 12 idea files: status changed to accepted (3) or deferred (9)
- `reports/head-ai-log.md`: vision review log, decisions, task assignments, next steps
- `workstreams/README.md`: new WS11-13, Group D parallel group, conflict zones
- `HumanOnly/AI-Operations-Manual.md`: WS11-13 deployment prompts, Wave 8 order of operations
- `HumanOnly/Project-Briefing.md`: pending section rewritten with accepted/deferred split
- `HumanOnly/Project-Log.md`: this entry
- 3 report templates: `reports/workstreams/ws{11,12,13}-report.md`

---

## 2026-04-07

**Comprehensive documentation refresh**
All 25 documentation files updated to reflect final milestone state. 20 files in main repo + 5 HumanOnly files. All numbers now reflect: VAE v3 99.9% valid, MPNN cascade active, ADMET informational, 548 tests, null hypothesis retained, 431 novel candidates. Committed and pushed to origin ML.

---

## 2026-04-06

**VAE v3 (SELFIES) trained -- 99.9% valid generation**
After two failed SMILES-based attempts (v1: 0% valid due to teacher forcing bug; v2: 0% valid due to prior-posterior mismatch), switched to SELFIES representation which guarantees validity by construction. Trained 300 epochs on H200 (31 min). Generation: 999/1000 valid, 948 unique. Mean MW=341, 79.5% drug-like.

**Full comparison re-run with VAE candidates**
State-aware: 461 candidates (395 VAE + 36 template + 30 shared). Static: 30. Mann-Whitney U: p<0.001, d=1.36 (large, static favored). Max score: state-aware=0.7794 vs static=0.7288. Diversity: 0.9056 vs 0.5684. 431 novel candidates. Weight sensitivity: 44%/56%. Null hypothesis formally retained.

**Comparison script bug fixed**
Null hypothesis display always showed "NOT REJECTED" because `getattr(t, "significant", False)` always returned False (`StatisticalTest` dataclass has no `significant` field). Fixed to check `t.p_value < 0.05` AND `result.scores.delta_mean > 0`.

**All ruff violations fixed (121→0)**
CI lint now passes clean. Config updated to ignore N803/N806/N815 (scientific convention) and E402 (lazy imports).

**Git push to origin ML**
All commits pushed via SSH after adding ed25519 key. Fixed SSH config permissions (chmod 600) and added GitHub host key.

---

## 2026-04-05

**MPNN trained -- all targets exceeded**
RMSE=0.7182 (<1.0), R²=0.6863 (>0.5), Pearson=0.8323 (>0.7). 12.7M params, 10,466 compounds, best epoch 83/150. Trained in 217s on H200. Integrated into scoring cascade and verified (osimertinib=0.75, ethanol=0.34).

**ADMET trained -- classification targets met**
hERG AUROC=0.7745 (>0.75), CYP3A4 AUROC=0.7323 (>0.70). 187K params, 27,698 molecules, best epoch 40/150. Trained in 197s on L40S. Key finding: hard ADMET filtering eliminates ALL kinase inhibitor candidates (100% hERG failure). ADMET used as informational annotation, not pre-ranking gate.

**VAE v1 and v2 attempted (both 0% valid)**
v1 (2.6M params): 0% valid SMILES. Teacher forcing issue. v2 (9.5M params, improved config): still 0% valid at all temperatures. Root cause identified: prior-posterior mismatch + character-level SMILES fragility.

---

## 2026-03-30

**Documentation overhaul (Admin AI triage)**
Head AI Generation 2 triaged 12 Admin AI suggestions. Fixed all P0s (missing chemistry/ module in docs, 18 broken file:line references, massively stale GOALS.md success table) and all P1s (stale test counts, wrong module file counts, stale module READMEs, broken interface contracts). Deferred S010 (ruff violations, ~40 files). Wont-fixed S012 (__init__.py exports). Updated 13 files across the project. Test count standardized to 548 everywhere.

**Admin AI first audit**
Admin AI audited 28 project files and produced 12 structured suggestions (3 P0, 6 P1, 2 P2, 1 P3). Primary finding: all documentation still reflected pre-workstream state despite all 9 workstreams being complete. This was the #1 quality issue.

---

## 2026-03-28

**All 9 workstreams complete**
WS08 (MPNN Affinity) merged as the final workstream. The full scoring cascade is now assembled: MPNN -> DockingProxy MLP -> constant 0.5 stub. All integration adapters written. Test count reached 548 (up from 359 pre-workstream). All workstreams merged to ML branch without conflicts.

**WS04 and WS08 merged (scoring chain)**
WS04 (Docking Proxy MLP) and WS08 (MPNN Affinity) merged sequentially — both modify `ranking/scoring.py`. The 3-tier cascading fallback chain is complete. Models still need GPU training.

**WS02, WS05, WS09 batch-merged**
Three workstreams merged as a batch (no file conflicts between them):
- WS02: Scoring Integration — Morgan fingerprints replace n-gram Tanimoto, QED/Lipinski replace heuristic druglikeness
- WS05: Visualization — matplotlib score distributions, radar plots, comparison figures
- WS09: ADMET Predictor — multi-task ADMET adapter, safety filter gate, TDC data prep

**Vision System created**
Three-role strategic planning layer established: Assistant AI (writes briefings), Visionary AI (proposes ideas), Head AI (triages). Folder structure: `vision/briefings/`, `vision/ideas/`, `vision/log/`.

**Admin AI system created**
Infrastructure quality monitoring role added. Writes structured suggestions to `admin/suggestions.md`. Head AI triages and implements.

**AI Employee Directory established**
Full organizational chart with 5 AI roles documented: Head AI, Modular Agents, Assistant AI, Visionary AI, Admin AI. Information flow, dependencies, and reporting structure codified.

**Documentation system formalized**
Rule 10 (continuous documentation) applied universally. Every AI agent must maintain a running progress report. Report template created at `reports/workstreams/TEMPLATE.md`.

---

## 2026-03-23

**Wave 1 workstreams merged**
Four independent workstreams merged simultaneously:
- WS01: Chemistry Foundation — RDKit fingerprints, descriptors, SMILES validation, SA scoring (new `chemistry/` package)
- WS03: Statistical Testing — Mann-Whitney U, bootstrap confidence intervals, Cohen's d, weight sensitivity analysis
- WS06: CI/CD — GitHub Actions workflow for Python 3.10-3.12 test matrix + ruff linting
- WS07: Conditional VAE — data preparation pipeline, ChEMBL EGFR data, VAE generation integration

Test count jumped from 359 to ~498. Worktree naming convention and Head AI merge procedure documented.

---

## 2026-03-21

**ML infrastructure built**
Three neural network architectures written (code-complete, not trained):
- Conditional SMILES VAE (GRU encoder/decoder, state conditioning, KL annealing)
- Affinity MPNN (NNConv message passing, graph-level readout)
- Multi-task ADMET (GIN backbone, 6 endpoint heads)

Training scripts, configs, and data prep pipelines created. All require GPU.

**Full documentation overhaul for multi-agent development**
CLAUDE.md expanded to comprehensive AI development guide. Workstream system designed (9 independent tasks). HUMANONLY.md created as human operator playbook. TODO.md rewritten with detailed roadmap.

---

## 2026-03-20

**Phase 7: Unified ranking and evaluation**
Both pipelines (static and state-aware) scored by the same unified function. Head-to-head comparison completed. Key result: state-aware produces 49 novel candidates inaccessible to static pipeline, with higher diversity (+0.035) and competitive scores (+0.020). Verdict: real but moderate advantage; docking stub limits conclusions.

**Full project audit**
Removed unsupported claims, added weight validation, documented all limitations. README rewritten. Documentation suite created (PROJECT_CHARTER, ARCHITECTURE, EVALUATION, RESULTS_SUMMARY, LIMITATIONS, etc.).

---

## 2026-03-14

**Core pipeline built (Phases 0-6)**
The entire computational pipeline assembled in a single day:

- **Phase 0:** Project scaffold, scientific framing, benchmark specification, project charter
- **Phase 1:** Data infrastructure (registry, manifests, validation) + processed benchmark datasets (18 mutations, 16 PDB structures, 9 ligands)
- **Phase 2:** Static baseline pipeline — single structure (1M17), one pocket, halogen/methyl analog generation, 30 candidates
- **Phase 3:** Structural state atlas — 4 EGFR conformational states classified via 9D feature vectors from 16 PDB structures
- **Phase 4:** Context-to-state prediction — mutation features mapped to conformational states (29 mutation + 4 pathway features)
- **Phase 5:** World model — Markov state transitions, contrastive embeddings, stationary distribution
- **Phase 6:** State-conditioned generation — 79 candidates across 4 states using 7 strategies (hinge optimization, back-pocket extension, gatekeeper avoidance, volume filling, covalent warhead, P-loop interaction, analog generation)

359 tests written across 14 test files, all passing.
