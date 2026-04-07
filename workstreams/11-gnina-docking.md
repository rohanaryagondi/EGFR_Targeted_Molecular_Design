# Workstream 11: GNINA Physics-Informed Docking

## Goal

Integrate GNINA (CNN-scored molecular docking built on AutoDock Vina) as the top tier of the docking fallback chain. Every candidate is docked into each conformational state's binding pocket, producing physics-based scores and 3D binding poses. This activates the 20% docking component of scoring weight with real protein-ligand structural modeling, replacing the proxy MLP trained on 34 molecules.

## Why This Matters

- The docking_proxy component (20% of unified score) is currently served by a 3-tier cascade: MPNN -> MLP proxy (34 molecules) -> constant 0.5. None of these tiers model the protein-ligand 3D interaction.
- GNINA provides Vina scores (physics-based) and CNN scores (learned from PDBbind), plus binding poses.
- State-specific docking directly measures whether candidates bind better to their intended state pocket -- the core test of the state-aware hypothesis.
- Binding poses enable downstream visual and interaction fingerprint analysis.
- The null hypothesis was retained under the current scoring; real docking could change the comparison outcome.

## Prerequisites

- **GNINA** installed (conda-forge or compiled binary). Test: `gnina --version`.
- **OpenBabel** or **Meeko** for PDBQT format conversion.
- **RDKit** for 3D conformer generation from SMILES (already a project dependency).
- **PDB structures** for each conformational state (existing in `data/raw/structures/`).
- Structure module artifacts (state atlas with representative structures per state).

## Origin

Vision Idea 005 (GNINA Integration for Physics-Informed Docking). Accepted 2026-04-07.

## Files to Create

| File | Purpose |
|------|---------|
| `src/statebind/chemistry/docking.py` | Python wrapper around GNINA CLI. Input: SMILES + receptor PDBQT + box config. Output: `DockingResult` with pose, Vina score, CNN score. Supports batch docking. |
| `scripts/prepare_docking_receptors.py` | For each conformational state, prepare receptor PDBQT: extract binding site, add hydrogens, define docking box centered on pocket centroid. Output: one receptor + box config per state. |
| `configs/docking.yaml` | GNINA binary path, exhaustiveness, num_poses, CNN model, box padding, timeout_per_molecule, GPU acceleration toggle. |
| `evaluation/docking_analysis.py` | State-specific docking analysis: dock each candidate into all 4 pockets, compute state selectivity from docking scores, interaction fingerprints if poses available. |
| `tests/test_docking.py` | 20+ tests for wrapper, receptor prep, fallback, integration. |

## Files to Modify

| File | Change |
|------|--------|
| `src/statebind/ranking/scoring.py` | Add GNINA as tier 0 in the docking fallback chain: GNINA -> MPNN -> proxy MLP -> stub. Add `_score_docking_gnina()` function. Score normalization: `sigmoid(-vina_score / 3)` maps kcal/mol to [0, 1]. |
| `src/statebind/evaluation/figures.py` | Add docking score heatmap (candidate x state) and optionally binding pose thumbnails. |
| `src/statebind/evaluation/comparison.py` | Add optional docking analysis section to `ComparativeResult` when GNINA results are available. |

## Interface Contracts

### Primary Interface

```python
from pydantic import BaseModel

class DockingResult(BaseModel):
    smiles: str
    receptor_state: str          # e.g., "DFGin_aCin"
    vina_score: float            # kcal/mol (more negative = better)
    cnn_score: float             # [0, 1] from GNINA CNN
    cnn_affinity: float          # predicted pKd from CNN
    pose_pdb: str | None = None  # PDB block of best pose (optional)
    n_poses: int = 0
    success: bool = True
    error: str | None = None

def dock_molecule(
    smiles: str,
    receptor_pdbqt: str | Path,
    box_center: tuple[float, float, float],
    box_size: tuple[float, float, float] = (25.0, 25.0, 25.0),
    exhaustiveness: int = 8,
    num_modes: int = 5,
    timeout: int = 120,
) -> DockingResult:
    """Dock a single molecule into a receptor pocket using GNINA.

    Returns DockingResult with success=False and error message on failure.
    Falls back gracefully if GNINA is not installed.
    """

def dock_batch(
    smiles_list: list[str],
    receptor_pdbqt: str | Path,
    box_center: tuple[float, float, float],
    box_size: tuple[float, float, float] = (25.0, 25.0, 25.0),
    n_workers: int = 4,
) -> list[DockingResult]:
    """Batch docking with optional parallelization."""

def is_gnina_available() -> bool:
    """Check if GNINA binary is installed and callable."""
```

### Scoring Integration

```python
# In ranking/scoring.py, the docking fallback chain becomes:
# 1. GNINA (if installed and receptor files exist) -> physics + CNN score
# 2. MPNN (if trained model exists) -> learned affinity
# 3. DockingProxy MLP (trained on 34 molecules) -> proxy
# 4. Constant 0.5 stub

def _score_docking_gnina(smiles: str, target_state: str) -> float | None:
    """Attempt GNINA docking. Returns normalized score in [0, 1] or None if unavailable."""
```

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| Scoring cascade | `ranking/scoring.py:_get_scoring_method()` | Add GNINA as highest-priority tier |
| MPNN affinity | `ml/affinity_predictor.py` | Existing tier 2 in cascade |
| Proxy MLP | `chemistry/docking_proxy.py` | Existing tier 3 in cascade |
| State atlas | `structure/atlas.py` | Get representative PDB per state |
| RDKit conformers | `chemistry/descriptors.py` | 3D conformer generation patterns |
| Score normalization | `ranking/scoring.py:score_unified()` | Existing [0, 1] normalization approach |

## Files NOT to Touch

- `src/statebind/ml/` -- ML model code is finalized
- `src/statebind/baselines/scoring.py` -- baseline scoring is separate
- `src/statebind/context/` -- context module is orthogonal
- `src/statebind/dynamics/` -- dynamics module is orthogonal
- Any existing test files (except adding new test imports if needed)

## Testing Requirements

### `tests/test_docking.py` -- ~20 tests

**1. GNINA availability tests:**
- `test_is_gnina_available()` -- returns bool without crashing
- `test_dock_without_gnina()` -- returns DockingResult with success=False when GNINA missing

**2. Receptor preparation tests:**
- `test_prepare_receptor_creates_pdbqt()` -- output file exists
- `test_box_config_valid()` -- box center within PDB bounds, box size > 0
- `test_all_states_have_receptors()` -- one receptor per populated state

**3. Docking wrapper tests (skip if GNINA not installed):**
- `test_dock_known_binder()` -- erlotinib into 1M17 returns Vina score < 0
- `test_dock_invalid_smiles()` -- returns success=False
- `test_dock_batch_matches_individual()` -- batch and single results consistent
- `test_vina_score_range()` -- score in [-15, 0] kcal/mol for drug-like molecules
- `test_cnn_score_range()` -- CNN score in [0, 1]

**4. Score normalization tests:**
- `test_gnina_score_normalization()` -- sigmoid(-vina/3) maps correctly
- `test_better_binder_higher_score()` -- erlotinib scores higher than ethanol

**5. Fallback chain tests:**
- `test_cascade_prefers_gnina()` -- when available, GNINA used over MPNN
- `test_cascade_falls_back()` -- when GNINA unavailable, falls to MPNN/proxy

**6. State-specific docking tests (skip if GNINA not installed):**
- `test_dock_all_states()` -- same molecule produces different scores per state
- `test_docking_result_pydantic()` -- DockingResult serializes to JSON

**7. Integration tests:**
- `test_docking_analysis_runs()` -- analysis module produces summary without crash
- `test_score_heatmap_data()` -- candidate x state matrix has correct dimensions

## Definition of Done

- [ ] GNINA wrapper (`chemistry/docking.py`) docks molecules and returns structured results
- [ ] Receptor preparation script creates PDBQT + box config for each state
- [ ] Docking config (`configs/docking.yaml`) controls all parameters
- [ ] GNINA integrated as tier 0 in scoring cascade (with graceful fallback)
- [ ] State-specific docking analysis produces candidate x state score matrix
- [ ] 20+ tests, all passing (GNINA-dependent tests skipped when not installed)
- [ ] No existing tests broken
- [ ] Known binders (erlotinib, gefitinib, osimertinib) dock with reasonable scores
- [ ] All new functions have type annotations and docstrings

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation -- edge cases, gotchas, implicit assumptions, or things that broke unexpectedly -- add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md`
- **Project-level**: `/CRITICAL.md`

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff -- every line should carry information.
