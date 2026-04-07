# Pending Workstreams — Agent Deployment Guide

**Last updated:** 2026-04-07
**Author:** Head AI (generation 4)

This document contains ready-to-paste prompts for launching the three pending
workstreams (WS11, WS12, WS13) as modular agents. It also documents parallelism
rules, dependency ordering, and post-launch verification steps.

---

## Parallelism Rules

```
WS11 (GNINA Docking)  ──┐
                         ├──  Can run in PARALLEL  ──► then merge both to ML
WS12 (Pareto Optim.)  ──┘
                                                        │
                                                        ▼
                                               WS13 (Retrospective Validation)
                                               Must start AFTER WS11 is merged
                                               (benefits from GNINA docking scores)
```

### Why this order?

| Rule | Reason |
|------|--------|
| **WS11 ∥ WS12** | Zero file overlap. WS11 creates `chemistry/docking.py` and modifies `ranking/scoring.py`. WS12 creates `ranking/pareto.py` and `evaluation/pareto_comparison.py`. The only shared modify target is `evaluation/figures.py` and `evaluation/comparison.py`, but they add independent functions (docking heatmaps vs Pareto projections) — trivial merge. |
| **WS13 after WS11** | WS13 re-runs the full pipeline under time-restricted data. If GNINA docking (WS11) is merged first, the retrospective validation automatically includes real docking scores, making the results far more compelling. WS13 also needs to retrain the MPNN on restricted data (GPU job). |
| **WS13 after WS12** | WS13 benefits from Pareto evaluation (WS12) to compare retrospective results. Not a hard dependency — WS13 can start while WS12 is finishing — but merging WS12 first is cleaner. |

### Conflict Zone

WS11 modifies `ranking/scoring.py` (adds GNINA as tier 0 in the docking cascade).
WS12 does NOT modify `ranking/scoring.py`. No scoring conflict.

WS11 and WS12 both modify `evaluation/figures.py` and `evaluation/comparison.py`,
but they add independent functions. Merge WS11 first, then WS12 (or vice versa) —
either order works with trivial conflict resolution.

---

## Pre-Launch Checklist

Before launching any agent, verify:

```bash
# 1. You're on the ML branch with clean state
cd ~/projects/statebind/repo
git checkout ML
git status  # should be clean or only have expected unstaged changes

# 2. Editable install is current (prevents cross-worktree contamination)
pip install -e ".[dev]"

# 3. Tests pass
pytest -v --tb=short -q  # expect 548 tests passing

# 4. For WS11: check if GNINA can be installed
module load miniconda
conda search gnina -c conda-forge  # or check if binary is available

# 5. For WS12: pymoo will be installed by the agent
pip install pymoo  # or let agent handle it
```

---

## Workstream 11: GNINA Physics-Informed Docking

### Launch Configuration

- **Parallelism:** Launch alongside WS12
- **Worktree:** `ws11-gnina` on branch `ws11/gnina`
- **Estimated effort:** 1-2 weeks
- **GPU needed:** Optional (GNINA is faster with GPU but works on CPU)
- **External deps:** GNINA binary, OpenBabel or Meeko for PDBQT conversion

### Agent Prompt

```
You are a modular AI agent working on the StateBind project. Your task is
Workstream 11: GNINA Physics-Informed Docking.

## Your Mission

Integrate GNINA (a CNN-scored molecular docking program built on AutoDock Vina)
as the top tier of the docking fallback chain in the StateBind pipeline. Every
candidate molecule must be dockable into each EGFR conformational state's binding
pocket, producing physics-based Vina scores, CNN scores, and 3D binding poses.

## Context

StateBind compares a static single-structure pipeline against a state-aware
4-state pipeline for EGFR molecular design. The null hypothesis was retained:
static pipeline wins on mean score. The docking component (20% of scoring
weight) currently uses a 3-tier cascade: MPNN → DockingProxy MLP → constant 0.5
stub. None of these tiers model the actual protein-ligand 3D interaction. Adding
GNINA gives the docking weight real physics-based signal and produces binding
poses for the first time.

## Essential Reading (read ALL before writing code)

1. `CLAUDE.md` — project rules, architecture, conventions
2. `CRITICAL.md` — scoring gotchas, fallback chain, module dependencies
3. `workstreams/11-gnina-docking.md` — your complete workstream brief
4. `workstreams/INTERFACES.md` — Contract 8 (GNINA Docking interface)
5. `reports/workstreams/ws11-report.md` — your progress report (update continuously)
6. `src/statebind/ranking/scoring.py` — the docking cascade you must extend (lines 28-69)
7. `src/statebind/structure/features.py` — curated PDB structures and pocket descriptors per state
8. `src/statebind/chemistry/docking_proxy.py` — existing proxy pattern to follow

## Step-by-Step Plan

### Step 1: Environment Setup
- Check if GNINA is available: `which gnina` or `gnina --version`
- If not installed, install via conda: `conda install -c conda-forge gnina`
  OR download the static binary from https://github.com/gnina/gnina/releases
- Check OpenBabel: `which obabel` or `obabel -V`
  If not installed: `conda install -c conda-forge openbabel`
- Verify RDKit is available (needed for 3D conformer generation):
  `python -c "from rdkit import Chem; print('OK')"`
  If not: `pip install rdkit`
- Update your progress report after this step.

### Step 2: Create Docking Config (`configs/docking.yaml`)
Create a config file with these parameters:
```yaml
gnina:
  binary_path: "gnina"           # or full path if not on PATH
  exhaustiveness: 8              # search thoroughness (8 = default)
  num_modes: 5                   # number of binding poses to generate
  cnn_model: "crossdock_default2018"  # best generalization
  box_padding: 5.0               # Angstroms beyond pocket centroid
  box_size: [25.0, 25.0, 25.0]  # default box dimensions
  timeout_per_molecule: 120      # seconds
  gpu: false                     # set true if GPU available
  seed: 42

receptors:
  # Map each conformational state to its representative PDB and pocket center.
  # These get populated by prepare_docking_receptors.py.
  # PDB IDs from structure/features.py curated data:
  #   DFGin_aCin:   1M17 (active, reference structure)
  #   DFGin_aCout:  2GS7 (inactive, αC-out)
  #   DFGout_aCin:  3IKA (DFG-out)
  #   DFGout_aCout: 4I22 (fully inactive)
  states:
    DFGin_aCin:
      pdb_id: "1m17"
      pdbqt_path: "data/processed/receptors/1m17_receptor.pdbqt"
      box_center: null  # computed by prep script
    DFGin_aCout:
      pdb_id: "2gs7"
      pdbqt_path: "data/processed/receptors/2gs7_receptor.pdbqt"
      box_center: null
    DFGout_aCin:
      pdb_id: "3ika"
      pdbqt_path: "data/processed/receptors/3ika_receptor.pdbqt"
      box_center: null
    DFGout_aCout:
      pdb_id: "4i22"
      pdbqt_path: "data/processed/receptors/4i22_receptor.pdbqt"
      box_center: null
```

### Step 3: Create Receptor Preparation Script (`scripts/prepare_docking_receptors.py`)
For each conformational state:
1. Download the PDB file (or use existing from `data/raw/structures/` if present)
2. Extract chain A (the kinase domain)
3. Remove water molecules and co-crystallized ligands
4. Add hydrogens using OpenBabel
5. Convert to PDBQT format using OpenBabel: `obabel -ipdb input.pdb -opdbqt -O output.pdbqt -h`
6. Compute the pocket centroid from the co-crystallized ligand position (or from
   the known binding site residues if no ligand). Key binding site residues for EGFR:
   L718, V726, A743, K745, E762, M766, L788, T790, Q791, L792, M793, P794, C797, L844, T854
7. Write the box center coordinates to the docking config
8. Output: one `{pdb_id}_receptor.pdbqt` file per state in `data/processed/receptors/`

If PDB files are not locally available, download from RCSB:
  `obabel -:"fetch 1m17" -opdb -O 1m17.pdb` or use urllib to download from
  `https://files.rcsb.org/download/{pdb_id}.pdb`

Note: The PDB structures are curated in `src/statebind/structure/features.py`
(function `_curated_features()`). Representative PDBs per state:
- DFGin_aCin (active): 1M17 — erlotinib-bound, pocket_volume=450 Å³
- DFGin_aCout (αC-out): 2GS7 — lapatinib-bound, pocket_volume=620 Å³
- DFGout_aCin (DFG-out): 3IKA — back pocket accessible, pocket_volume=780 Å³
- DFGout_aCout (fully inactive): 4I22 — largest pocket, pocket_volume=850 Å³

### Step 4: Create Docking Wrapper (`src/statebind/chemistry/docking.py`)
Implement the interface from INTERFACES.md Contract 8:
- `DockingResult` Pydantic model (smiles, receptor_state, vina_score, cnn_score,
  cnn_affinity, pose_pdb, n_poses, success, error)
- `is_gnina_available()` — check if GNINA binary is callable
- `dock_molecule(smiles, receptor_pdbqt, box_center, box_size, ...)` — dock one molecule:
  1. Convert SMILES → RDKit mol → 3D conformer (AllChem.EmbedMolecule + MMFF minimize)
  2. Write ligand to temporary SDF file
  3. Call GNINA via subprocess: `gnina --receptor {receptor} --ligand {ligand}
     --center_x {x} --center_y {y} --center_z {z}
     --size_x {sx} --size_y {sy} --size_z {sz}
     --exhaustiveness {e} --num_modes {n} --cnn {model} --out {output.sdf}`
  4. Parse GNINA output SDF for Vina score, CNN score, CNN affinity
  5. Return DockingResult. On failure, return success=False with error message.
- `dock_batch(smiles_list, receptor_pdbqt, box_center, ...)` — batch with
  optional multiprocessing (ProcessPoolExecutor)

Score parsing: GNINA writes scores as SDF properties. Parse with RDKit:
  `mol.GetProp('minimizedAffinity')` → Vina score (kcal/mol)
  `mol.GetProp('CNNscore')` → CNN score [0, 1]
  `mol.GetProp('CNNaffinity')` → predicted pKd

Follow the optional dependency pattern used everywhere in this project:
```python
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
```

### Step 5: Integrate into Scoring Cascade (`src/statebind/ranking/scoring.py`)
Add GNINA as tier 0 (highest priority) in the `_score_docking()` function at line 28.
The cascade becomes:
1. GNINA (if installed AND receptor files exist) → `_score_docking_gnina()`
2. MPNN (if trained model exists and torch available) — existing tier
3. DockingProxy MLP (WS04) — existing tier
4. Constant 0.5 stub — existing tier

Score normalization for GNINA: `sigmoid(-vina_score / 3)`.
This maps Vina kcal/mol (more negative = better binding) to [0, 1]:
- Vina = -10 kcal/mol → sigmoid(10/3) ≈ 0.96 (excellent binder)
- Vina = -7 kcal/mol → sigmoid(7/3) ≈ 0.91 (good binder)
- Vina = -4 kcal/mol → sigmoid(4/3) ≈ 0.79 (moderate)
- Vina = 0 kcal/mol → sigmoid(0) = 0.50 (no binding)

Also update `_get_scoring_method()` to report "GNINA(Vina+CNN)" when active.

IMPORTANT: The function signature of `_score_docking()` already accepts
`(smiles, pdb_id)` and returns `(score, is_stub, method_string)`. You must
match this return signature. Add `target_state` as an optional parameter or
resolve the state from pdb_id using the docking config.

### Step 6: Create State-Specific Docking Analysis (`src/statebind/evaluation/docking_analysis.py`)
For each candidate:
1. Dock into all 4 state pockets
2. Record the score matrix: candidates × states
3. Compute state selectivity: `selectivity = best_state_score - second_best_state_score`
4. Report: does each candidate bind best to its intended state?
5. Output a DockingAnalysis dataclass with the score matrix and selectivity stats.

### Step 7: Add Docking Visualizations (`src/statebind/evaluation/figures.py`)
Add a function `docking_heatmap()` that:
- Takes the candidate × state score matrix from docking analysis
- Produces a matplotlib heatmap (candidates on y-axis, states on x-axis)
- Color-coded by docking score (darker = better binding)
- Save to `artifacts/ranking/figures/docking_heatmap.png`
Do NOT modify existing figure functions — add new ones.

### Step 8: Write Tests (`tests/test_docking.py`)
Write 20+ tests following the plan in the workstream brief:
- GNINA availability tests (should pass even when GNINA is not installed)
- Receptor preparation tests
- Docking wrapper tests (mark with `@pytest.mark.skipif(not is_gnina_available(), ...)`
  so they skip gracefully on CI/machines without GNINA)
- Score normalization tests
- Fallback chain tests (mock GNINA as unavailable, verify cascade degrades)
- DockingResult Pydantic serialization tests

CRITICAL: All 548 existing tests must continue to pass. Run `pytest -v --tb=short`
after your changes to verify.

### Step 9: Update Documentation
- Update `reports/workstreams/ws11-report.md` with final status
- Add any non-obvious facts discovered to `CRITICAL.md`
- Add the GNINA cascade info to `src/statebind/ranking/CRITICAL.md` if it exists

## Files You MUST NOT Touch
- `src/statebind/ml/` — ML model code is finalized
- `src/statebind/baselines/scoring.py` — baseline scoring is separate
- `src/statebind/context/` — orthogonal
- `src/statebind/dynamics/` — orthogonal
- Any existing test files (don't modify, only add new ones)
- `HumanOnly/` — off-limits

## Non-Negotiable Rules
1. All functions must have type annotations. Use `from __future__ import annotations`.
2. Cross-module data structures must be Pydantic BaseModel subclasses.
3. No hard-coded paths — use DataPaths or config-driven paths.
4. GNINA must degrade gracefully when not installed (fallback to next tier).
5. Tests required for every new function.
6. Update your progress report (`reports/workstreams/ws11-report.md`) after every
   major step. This is non-negotiable (CLAUDE.md Rule 10).
7. Commit your work with descriptive messages. Push to the ws11/gnina branch.

## Definition of Done
- [ ] GNINA wrapper docks molecules and returns structured DockingResult
- [ ] Receptor PDBQT + box config prepared for each of 4 conformational states
- [ ] GNINA integrated as tier 0 in scoring cascade with graceful fallback
- [ ] State-specific docking analysis produces candidate × state score matrix
- [ ] Docking heatmap visualization added to figures.py
- [ ] Docking config at configs/docking.yaml
- [ ] 20+ new tests, all passing
- [ ] All 548 existing tests still pass
- [ ] Known binders (erlotinib, gefitinib, osimertinib) dock with reasonable scores
- [ ] Progress report updated with final status
```

### Post-Launch Verification

After the agent reports done:
```bash
cd .claude/worktrees/ws11-gnina
git status                         # check for uncommitted changes
git log --oneline -5               # verify commits
pip install -e ".[dev]" && cd ~/projects/statebind/repo && pip install -e ".[dev]"
pytest -v --tb=short               # all 548+ tests pass
pytest tests/test_docking.py -v    # new tests pass specifically
```

---

## Workstream 12: Pareto Multi-Objective Optimization

### Launch Configuration

- **Parallelism:** Launch alongside WS11
- **Worktree:** `ws12-pareto` on branch `ws12/pareto`
- **Estimated effort:** 3-5 days
- **GPU needed:** No
- **External deps:** pymoo (`pip install pymoo`)

### Agent Prompt

```
You are a modular AI agent working on the StateBind project. Your task is
Workstream 12: Pareto Multi-Objective Optimization.

## Your Mission

Add Pareto front analysis and hypervolume-based comparison to the evaluation
pipeline. Instead of relying solely on the weighted-sum composite score (with
arbitrary human-chosen weights of 0.35/0.30/0.20/0.15), compute the Pareto
front for each pipeline and compare them using the hypervolume indicator — a
weight-free metric that measures which pipeline is better across ALL possible
weight combinations.

## Context

StateBind compares a static single-structure pipeline against a state-aware
4-state pipeline for EGFR molecular design. The null hypothesis was retained:
static mean=0.5437 vs state-aware=0.4378. But weight sensitivity analysis shows
state-aware wins under 44% of random weight configurations. The "winner" depends
on weight choice, not scientific reality. Pareto analysis eliminates this problem.

The 4 scoring objectives are: reference_similarity (0.35), druglikeness (0.30),
docking_proxy (0.20), state_specificity (0.15). Each candidate has all 4
component scores stored in the comparison artifact.

IMPORTANT: Pareto analysis is ADDITIVE — it complements the weighted-sum
comparison, it does NOT replace it. Keep all existing comparison logic intact.

## Essential Reading (read ALL before writing code)

1. `CLAUDE.md` — project rules, architecture, conventions
2. `CRITICAL.md` — scoring system, module dependencies
3. `workstreams/12-pareto-optimization.md` — your complete workstream brief
4. `workstreams/INTERFACES.md` — Contract 9 (Pareto Optimization interface)
5. `reports/workstreams/ws12-report.md` — your progress report (update continuously)
6. `src/statebind/evaluation/comparison.py` — ComparativeResult dataclass you'll extend
7. `src/statebind/evaluation/figures.py` — plotting patterns to follow
8. `src/statebind/evaluation/sensitivity.py` — weight sensitivity patterns
9. `src/statebind/ranking/models.py` — UnifiedScoreComponent, UnifiedScoredCandidate
10. `artifacts/ranking/comparison.json` — the actual scored data

## Step-by-Step Plan

### Step 1: Install pymoo
```bash
pip install pymoo
```
Verify: `python -c "from pymoo.indicators.hv import HV; print('pymoo OK')"`

If pymoo is not installable, implement Pareto front computation from scratch
using numpy (non-dominated sorting is straightforward). Hypervolume is harder —
use the inclusion-exclusion algorithm for ≤4 objectives.

### Step 2: Create Pareto Front Module (`src/statebind/ranking/pareto.py`)
Implement the interface from INTERFACES.md Contract 9:

```python
@dataclass
class ParetoResult:
    front_indices: list[int]        # Indices of non-dominated candidates
    front_scores: np.ndarray        # Shape (n_front, n_objectives)
    hypervolume: float              # Volume dominated by the front
    crowding_distances: list[float] # Per-front-member crowding distance
    n_candidates: int
    n_objectives: int
    objective_names: list[str]

def compute_pareto_front(
    scores: np.ndarray,                      # (n_candidates, n_objectives)
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
    maximize: bool = True,
) -> ParetoResult:
```

Key implementation details:
- **Non-dominated sorting:** Candidate A dominates B if A is ≥ B on all objectives
  and strictly > on at least one (when maximize=True). The Pareto front is the
  set of non-dominated candidates.
- **Hypervolume:** Use `pymoo.indicators.hv.HV` if available. The reference point
  should default to the worst observed value per objective minus a small epsilon.
  For our project, scores are in [0, 1], so reference_point = [0, 0, 0, 0] is a
  natural choice for absolute hypervolume.
- **Crowding distance:** For diversity measurement along the front. Use standard
  NSGA-II crowding distance.
- Follow the optional dependency pattern:
  ```python
  try:
      from pymoo.indicators.hv import HV
      HAS_PYMOO = True
  except ImportError:
      HAS_PYMOO = False
  ```
  If pymoo is not available, compute Pareto front with numpy (skip hypervolume
  or use a simple bounding-box approximation).

### Step 3: Create Pareto Comparison Module (`src/statebind/evaluation/pareto_comparison.py`)
```python
@dataclass
class ParetoComparison:
    static_result: ParetoResult
    state_aware_result: ParetoResult
    hypervolume_ratio: float         # state_aware_hv / static_hv (>1 = state wins)
    dominance_fraction: float        # fraction of static front dominated by state-aware front
    per_objective_winner: dict[str, str]  # best extreme per objective
    reference_point: list[float]

def compare_pareto_fronts(
    static_scores: np.ndarray,
    state_aware_scores: np.ndarray,
    objective_names: list[str] | None = None,
    reference_point: list[float] | None = None,
) -> ParetoComparison:
```

The comparison must compute:
1. **Hypervolume ratio:** `state_aware_hv / static_hv`. >1 means state-aware is
   better across all weight combinations. This is the headline number.
2. **Dominance fraction:** For each point on the static Pareto front, check if
   any point on the state-aware front dominates it. Report the fraction dominated.
3. **Per-objective winner:** Which pipeline has the best extreme value on each
   individual objective.

To extract per-component scores from the comparison artifact, read
`artifacts/ranking/comparison.json`. The `scores` section contains per-pipeline
statistics. To get individual candidate scores, you need to read from the
pipeline's scored candidates. Check `ranking/models.py:UnifiedScoredCandidate`
for the data structure — each candidate has a `components` list of
`UnifiedScoreComponent` objects with `name`, `raw_score`, `weight`, and
`weighted_score` fields.

If individual candidate component scores are not directly in comparison.json,
you will need to re-score candidates or load from the ranking artifacts. Check:
- `artifacts/ranking/static_ranked.json`
- `artifacts/ranking/state_aware_ranked.json`
- Or re-run scoring on the merged candidates.

### Step 4: Add Pareto Visualizations (`src/statebind/evaluation/figures.py`)
Add these functions (do NOT modify existing ones):

1. `plot_pareto_projections(comparison: ParetoComparison, save_dir: Path) -> list[Path]`
   - For all C(4,2) = 6 pairs of objectives, create a 2D scatter plot
   - Static candidates in blue, state-aware in red
   - Pareto front points highlighted (larger markers, connected by lines)
   - Axes labeled with objective names
   - Save as `pareto_{obj1}_vs_{obj2}.png`

2. `plot_parallel_coordinates(comparison: ParetoComparison, save_path: Path) -> Path`
   - All 4 objectives on parallel vertical axes
   - Each candidate is a polyline connecting its scores across objectives
   - Static in blue, state-aware in red, Pareto front in bold
   - Include hypervolume ratio annotation

Use matplotlib with `plt.switch_backend('Agg')` for headless operation.

### Step 5: Integrate into ComparativeResult (`src/statebind/evaluation/comparison.py`)
Add an optional `pareto` field to the `ComparativeResult` dataclass:
```python
@dataclass
class ComparativeResult:
    ...  # existing fields
    pareto: object = field(default=None)  # ParetoComparison when available
```

Modify `run_full_comparison()` to optionally compute Pareto analysis when pymoo
is available and component scores are accessible. This should be a best-effort
addition — if it fails, the rest of the comparison should work normally.

### Step 6: Add Pareto Section to Comparison Report
Modify `scripts/report_comparative_results.py` (if it exists) or create a
function that prints Pareto results as part of the comparison report:
- Hypervolume: static = X, state-aware = Y, ratio = Y/X
- Pareto front sizes: static = N points, state-aware = M points
- Dominance fraction: X% of static front dominated by state-aware
- Per-objective winners table

### Step 7: Write Tests (`tests/test_pareto.py`)
Write 20+ tests following the plan in the workstream brief:

**Pareto front computation (5+ tests):**
- Single dominating candidate → front = [that candidate]
- All non-dominated → all on front
- Known 2D example with expected front indices
- 4-objective case (project's actual setup)
- Empty input → empty result

**Hypervolume (4+ tests):**
- Monotone: adding a non-dominated point never decreases hypervolume
- Single point: hypervolume = product of (point - ref) per dimension
- Known 2D analytical value
- Different reference points → different hypervolumes

**Comparison (4+ tests):**
- Swapping pipelines inverts the ratio
- Dominance fraction in [0, 1]
- Per-objective winner correctly identified
- Run on real comparison.json without crash

**Visualization (3+ tests):**
- 6 PNG files created for C(4,2) objective pairs
- 1 parallel coordinates PNG created
- Works with Agg backend (headless)

**Integration (3+ tests):**
- ParetoResult serializes to dict/JSON
- ParetoComparison serializes to dict/JSON
- Graceful fallback when pymoo not installed

CRITICAL: All 548 existing tests must continue to pass.

### Step 8: Update Documentation
- Update `reports/workstreams/ws12-report.md` with final status
- Add any non-obvious facts to `CRITICAL.md`

## Understanding the Score Data

The 4 objectives for each candidate:
1. `reference_similarity` — Morgan/ECFP4 Tanimoto to erlotinib/gefitinib/osimertinib [0,1]
2. `druglikeness` — RDKit QED + Lipinski + SA score composite [0,1]
3. `docking_proxy` — MPNN pIC50 prediction, sigmoid-normalized [0,1]
4. `state_specificity` — geometric decay based on state uniqueness [0,1]
   (always 0 for static baseline candidates)

All 4 are "higher is better" — maximize=True for Pareto computation.

Note on state_specificity: Static candidates always score 0 on this objective.
This is by design (only state-aware candidates get credit for state-specific
generation). In Pareto analysis, this means static candidates can never dominate
state-aware candidates on ALL objectives — they will always lose on
state_specificity. Discuss this in your report.

## Files You MUST NOT Touch
- `src/statebind/ranking/scoring.py` — scoring function unchanged
- `src/statebind/ml/` — ML models unchanged
- `src/statebind/generation/` — generation unchanged
- `src/statebind/baselines/` — baseline pipeline unchanged
- Any existing test files (don't modify, only add new ones)
- `HumanOnly/` — off-limits

## Non-Negotiable Rules
1. Type annotations on all functions. `from __future__ import annotations`.
2. Use dataclass for ParetoResult/ParetoComparison (internal to evaluation).
3. pymoo is optional — degrade gracefully if not installed.
4. Do NOT replace weighted-sum comparison — Pareto is additive.
5. Tests required for every new function.
6. Update `reports/workstreams/ws12-report.md` after every major step.
7. Commit your work. Push to ws12/pareto branch.
8. All scores are [0,1], higher is better. Use maximize=True.

## Definition of Done
- [ ] `ranking/pareto.py` computes Pareto fronts and hypervolume
- [ ] `evaluation/pareto_comparison.py` compares pipeline Pareto fronts
- [ ] Hypervolume ratio reported alongside weighted-sum comparison
- [ ] 2D Pareto projection plots for all 6 objective pairs
- [ ] Parallel coordinates plot for 4-objective view
- [ ] 20+ new tests, all passing
- [ ] All 548 existing tests still pass
- [ ] ComparativeResult optionally includes Pareto section
- [ ] Progress report updated
```

### Post-Launch Verification

After the agent reports done:
```bash
cd .claude/worktrees/ws12-pareto
git status
git log --oneline -5
cd ~/projects/statebind/repo && pip install -e ".[dev]"
pytest -v --tb=short
pytest tests/test_pareto.py -v
```

---

## Workstream 13: Retrospective Time-Split Validation

### Launch Configuration

- **Parallelism:** Launch AFTER WS11 and WS12 are merged (or at least WS11)
- **Worktree:** `ws13-retro` on branch `ws13/retro`
- **Estimated effort:** 1-2 weeks
- **GPU needed:** Yes (MPNN retraining on restricted data — 2 SLURM jobs)
- **External deps:** ChEMBL API access, RDKit

### Agent Prompt

```
You are a modular AI agent working on the StateBind project. Your task is
Workstream 13: Retrospective Time-Split Validation.

## Your Mission

Validate the StateBind pipeline retrospectively using a time-split strategy:
train models on EGFR data available before a cutoff date (2010 and 2015), then
test whether the pipeline identifies molecules resembling drugs that were later
approved or advanced to clinical trials. This is the strongest validation
strategy available to a purely computational project.

## Context

StateBind compares static vs state-aware molecular design for EGFR. The null
hypothesis was retained (static wins on mean score). The pipeline needs external
validation beyond self-benchmarking. Retrospective validation tests real
predictive power: if the state-aware pipeline can identify osimertinib-like
molecules (approved 2015) using only pre-2015 data, that demonstrates genuine
predictive value regardless of the mean score comparison.

Key EGFR drug timeline:
- Erlotinib: approved 2004 (1st gen, type I, DFGin_aCin)
- Gefitinib: approved 2003 (1st gen, type I, DFGin_aCin)
- Afatinib: approved 2013 (2nd gen, irreversible, DFGin_aCin)
- Osimertinib: approved 2015 (3rd gen, T790M-targeting, covalent C797)
- Dacomitinib: approved 2018 (2nd gen, pan-HER)
- Lazertinib: approved 2021 (3rd gen)
- Mobocertinib: approved 2021 (targets EGFR exon 20 insertions)

## Essential Reading (read ALL before writing code)

1. `CLAUDE.md` — project rules, architecture, conventions
2. `CRITICAL.md` — scoring system, ML infrastructure, data details
3. `workstreams/13-retrospective-validation.md` — your complete workstream brief
4. `workstreams/INTERFACES.md` — Contract 10 (Retrospective Validation interface)
5. `reports/workstreams/ws13-report.md` — your progress report (update continuously)
6. `scripts/prepare_mpnn_data.py` — existing ChEMBL data prep (pagination patterns)
7. `scripts/prepare_vae_data.py` — existing VAE data prep
8. `scripts/train_mpnn.py` — MPNN training script
9. `src/statebind/evaluation/comparison.py` — ComparativeResult you'll extend
10. `src/statebind/chemistry/fingerprints.py` — Morgan similarity functions
11. `src/statebind/baselines/scoring.py` — reference binder list at lines 59-66

## Step-by-Step Plan

### Step 1: Create Time-Split Dataset Builder (`scripts/build_timesplit_datasets.py`)

Query ChEMBL for ALL EGFR bioactivity data with publication dates:
- Target: CHEMBL203 (EGFR)
- Assay types: IC50, Ki (same as prepare_mpnn_data.py)
- Additional field needed: `document_year` or `first_publication` from ChEMBL API
- The ChEMBL REST API provides `document_year` in the activities endpoint

For each cutoff year (2010, 2015):
1. Split compounds: train = published ≤ cutoff year, validation = published > cutoff year
2. Identify "future drugs" — approved EGFR inhibitors not in training set
3. Canonicalize all SMILES via RDKit, deduplicate
4. Verify NO data leakage: assert no validation compound appears in training set
5. Output: `data/processed/timesplit_{cutoff}_train.json` and
   `data/processed/timesplit_{cutoff}_validation.json`

Future drug SMILES (hardcode these — they are canonical reference compounds):
```python
FUTURE_DRUGS = {
    "erlotinib": {
        "smiles": "C=Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1",
        "approved": 2004, "generation": 1, "type": "reversible_type_I"
    },
    "gefitinib": {
        "smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        "approved": 2003, "generation": 1, "type": "reversible_type_I"
    },
    "afatinib": {
        "smiles": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
        "approved": 2013, "generation": 2, "type": "irreversible"
    },
    "osimertinib": {
        "smiles": "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
        "approved": 2015, "generation": 3, "type": "covalent_C797"
    },
    "dacomitinib": {
        "smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1NC(=O)/C=C/CN1CCCCC1",
        "approved": 2018, "generation": 2, "type": "irreversible_pan_HER"
    },
    "lazertinib": {
        "smiles": "CNC(=O)c1cc(Oc2ccc(NC(=O)/C=C/CN(C)C)cc2)ccn1",
        "approved": 2021, "generation": 3, "type": "covalent_C797"
    },
}
```
IMPORTANT: Verify these SMILES are correct by canonicalizing with RDKit. If any
are incorrect, look up the correct canonical SMILES from ChEMBL.

For the 2010 cutoff: erlotinib and gefitinib are in training. Afatinib,
osimertinib, dacomitinib, lazertinib are held out as future drugs.

For the 2015 cutoff: erlotinib, gefitinib, afatinib, osimertinib are in
training. Dacomitinib, lazertinib are held out.

### Step 2: Create Retrospective Config (`configs/retrospective.yaml`)
```yaml
retrospective:
  cutoffs: [2010, 2015]
  enrichment_k_values: [10, 50, 100]
  similarity_threshold: 0.4        # Tanimoto threshold for "hit"
  reference_binders:
    pre_2010: ["erlotinib", "gefitinib"]
    pre_2015: ["erlotinib", "gefitinib", "afatinib", "osimertinib"]
  restrict_structures: false        # if true, also restrict PDB structures by year
  restrict_vae_training: true       # retrain VAE on pre-cutoff SMILES
  restrict_mpnn_training: true      # retrain MPNN on pre-cutoff data
```

### Step 3: Create Retrospective Metrics Module (`src/statebind/evaluation/retrospective.py`)

Implement the interface from INTERFACES.md Contract 10:

```python
@dataclass
class TimeSplitDataset:
    cutoff_year: int
    train_smiles: list[str]
    train_pIC50: list[float]
    n_train: int
    held_out_drugs: list[dict]
    n_held_out: int

@dataclass
class RetrospectiveResult:
    cutoff_year: int
    pipeline: str                    # "static" or "state_aware"
    enrichment_factor_10: float
    enrichment_factor_50: float
    max_similarity_to_future: float
    mean_similarity_to_future: float
    n_candidates: int
    n_future_drugs: int
    future_drug_ranks: dict[str, int | None]
    novelty_vs_training: float

def compute_enrichment_factor(
    candidate_similarities: list[float],
    threshold: float = 0.4,
    top_k: int = 10,
) -> float:
    """EF = (hits_in_top_k / top_k) / (total_hits / total_candidates)"""
```

Enrichment factor measures whether future drugs are enriched among top-ranked
candidates. Sort candidates by their composite score. Count how many of the
top-K candidates have Tanimoto similarity ≥ threshold to any future drug.
EF = (hits_in_top_k / top_k) / (total_hits / total_candidates).

Similarity to future drugs: for each candidate, compute Morgan/ECFP4 Tanimoto
similarity to each held-out future drug. Use `chemistry/fingerprints.py`
functions.

Novelty: fraction of generated candidates whose SMILES are NOT in the
pre-cutoff training set (exact match after canonicalization).

### Step 4: Create Retrospective Pipeline Script (`scripts/run_retrospective_validation.py`)

This is the orchestration script. For each cutoff year:

1. Load the time-split dataset
2. Restrict the reference binder list (remove post-cutoff drugs from
   `baselines/scoring.py` reference set). Do this by passing a custom reference
   list to the scoring functions, NOT by modifying the source code.
3. Retrain MPNN on pre-cutoff data:
   - Write a SLURM script: `scripts/slurm/retrain_mpnn_{cutoff}.slurm`
   - Use `scripts/train_mpnn.py` with `--data` pointing to the time-split train file
   - Save checkpoint to `artifacts/models/mpnn/best_model_pre{cutoff}.pt`
4. Optionally retrain VAE on pre-cutoff SMILES (lower priority — the VAE
   generates molecules, it doesn't score them)
5. Run the full pipeline:
   a. Generate candidates (static + state-aware)
   b. Score with the restricted MPNN
   c. Rank and merge
   d. Run comparison
6. Compute retrospective metrics against held-out future drugs
7. Save results to `artifacts/evaluation/retrospective_{cutoff}.json`

IMPORTANT: This script coordinates GPU-dependent steps (MPNN retraining) with
CPU steps (evaluation). Design it so that:
- The SLURM job for MPNN retraining can be submitted separately
- The evaluation step checks for the checkpoint and uses it if available
- If no restricted checkpoint exists, fall back to the full-data MPNN

### Step 5: Create SLURM Templates for Restricted Retraining

Create `scripts/slurm/retrain_mpnn_2010.slurm` and `retrain_mpnn_2015.slurm`:
```bash
#!/bin/bash
#SBATCH --job-name=mpnn_retro_2010
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH -p gpu_devel
#SBATCH -A pi_mg269
#SBATCH --gpus=h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00

module load miniconda
eval "$(conda shell.bash hook)"
conda activate statebind  # or whatever env has torch

cd $HOME/projects/statebind/repo
mkdir -p logs artifacts/models/mpnn

python scripts/train_mpnn.py \
    --config configs/mpnn.yaml \
    --data data/processed/timesplit_2010_train.json \
    --output artifacts/models/mpnn/best_model_pre2010.pt
```

### Step 6: Integrate into ComparativeResult
Add an optional `retrospective` field to `ComparativeResult` in
`evaluation/comparison.py`:
```python
retrospective: object = field(default=None)  # RetrospectiveComparison
```

### Step 7: Add Retrospective Visualizations (`src/statebind/evaluation/figures.py`)
Add functions (do NOT modify existing ones):
1. `plot_enrichment_by_cutoff()` — bar chart: EF@10 and EF@50 for each
   pipeline at each cutoff
2. `plot_similarity_to_future_drugs()` — violin or box plot: distribution of
   max similarity to future drugs, static vs state-aware

### Step 8: Write Tests (`tests/test_retrospective.py`)
Write 15+ tests following the workstream brief:

**Time-split integrity (4+ tests):**
- No future leakage at 2010 cutoff
- No future leakage at 2015 cutoff
- Future drugs excluded from training
- Reference binders properly restricted

**Enrichment computation (4+ tests):**
- Perfect enrichment (all hits in top-K) → max EF
- Random ordering → EF ≈ 1.0
- Zero hits → EF = 0.0
- K larger than N → handles gracefully

**Similarity and novelty (3+ tests):**
- Known analog scores high against known drug
- Novelty fraction in [0, 1]
- Future drug ranking is correct sorted position

**Integration (3+ tests):**
- RetrospectiveResult serializes to JSON
- Comparison summary is non-empty
- TimeSplitDataset has valid fields

CRITICAL: All existing tests (548+) must continue to pass.

### Step 9: Update Documentation
- Update `reports/workstreams/ws13-report.md` continuously
- Add data leakage verification facts to `CRITICAL.md`

## Scientific Honesty Requirements

This is the most important rule for this workstream:
- Do NOT design the validation to favor a particular outcome
- Report results as found, whether positive or negative
- If state-aware pipeline FAILS to identify future drugs, that is a valid
  and valuable finding — report it clearly
- Never adjust thresholds or metrics after seeing results to change the outcome
- A well-characterized negative result is more valuable than a cherry-picked
  positive one

## Files You MUST NOT Touch
- `src/statebind/ranking/scoring.py` — scoring function unchanged
- `src/statebind/ml/mpnn.py` — model architecture unchanged (only retrain)
- `src/statebind/ml/vae.py` — model architecture unchanged
- `src/statebind/structure/` — structure module unchanged
- Any existing test files
- `HumanOnly/` — off-limits

## Non-Negotiable Rules
1. Type annotations. `from __future__ import annotations`.
2. No hard-coded paths — use DataPaths or config-driven paths.
3. NO DATA LEAKAGE. This is the #1 failure mode. Triple-check that no
   post-cutoff compounds appear in pre-cutoff training data.
4. Tests required for every new function.
5. Update `reports/workstreams/ws13-report.md` after every major step.
6. Commit your work. Push to ws13/retro branch.
7. SLURM jobs use `-A pi_mg269` and appropriate GPU partitions.

## Definition of Done
- [ ] Time-split datasets created for 2010 and 2015 cutoffs
- [ ] No data leakage verified by tests
- [ ] MPNN retraining SLURM scripts created for both cutoffs
- [ ] Retrospective metrics module computes enrichment, similarity, novelty
- [ ] Pipeline execution script runs full comparison under time restriction
- [ ] Results reported for both pipelines at both cutoffs
- [ ] 15+ new tests, all passing
- [ ] All existing tests still pass
- [ ] Progress report updated
- [ ] Results reported honestly regardless of direction
```

### Post-Launch Verification

After the agent reports done:
```bash
cd .claude/worktrees/ws13-retro
git status
git log --oneline -5
cd ~/projects/statebind/repo && pip install -e ".[dev]"
pytest -v --tb=short
pytest tests/test_retrospective.py -v
# Also verify no data leakage:
python -c "
import json
train = json.load(open('data/processed/timesplit_2010_train.json'))
val = json.load(open('data/processed/timesplit_2010_validation.json'))
train_set = set(s['smiles'] for s in train['compounds'])
val_set = set(s['smiles'] for s in val['compounds'])
overlap = train_set & val_set
print(f'Leakage: {len(overlap)} compounds')
assert len(overlap) == 0, 'DATA LEAKAGE DETECTED'
"
```

---

## Merge Procedure (Head AI)

After agents complete, the Head AI merges in this order:

### Round 1: WS11 and WS12 (parallel workstreams)

```bash
# Merge WS11 first (touches ranking/scoring.py)
cd ~/projects/statebind/repo
git checkout ML
pip install -e ".[dev]"
pytest -v --tb=short                          # baseline: 548 pass

git merge ws11/gnina --no-ff -m "Merge WS11: GNINA physics-informed docking"
pip install -e ".[dev]"
pytest -v --tb=short                          # expect 568+ pass

# Then merge WS12
git merge ws12/pareto --no-ff -m "Merge WS12: Pareto multi-objective optimization"
pip install -e ".[dev]"
pytest -v --tb=short                          # expect 588+ pass

# If merge conflicts in evaluation/figures.py or evaluation/comparison.py:
# Both add independent functions. Keep both sets of additions.

git push origin ML
```

### Round 2: WS13 (after Round 1)

```bash
git merge ws13/retro --no-ff -m "Merge WS13: Retrospective time-split validation"
pip install -e ".[dev]"
pytest -v --tb=short                          # expect 603+ pass
git push origin ML
```

### Post-Merge

1. Update `reports/head-ai-log.md` with merge results
2. Update `TODO.md` to mark stretch goals as complete
3. Re-run full comparison with GNINA docking + Pareto evaluation
4. Run Assistant AI to refresh vision briefings

---

## Summary Table

| WS | Name | Launch | Parallel With | GPU | Deps to Install | Est. New Tests |
|----|------|--------|--------------|-----|-----------------|----------------|
| 11 | GNINA Docking | Now | WS12 | Optional | gnina, openbabel | 20+ |
| 12 | Pareto Optimization | Now | WS11 | No | pymoo | 20+ |
| 13 | Retrospective Validation | After WS11+WS12 merge | None | Yes (MPNN retrain) | None new | 15+ |
