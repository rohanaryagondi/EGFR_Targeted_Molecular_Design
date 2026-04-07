# Testing Patterns & Optional Dependencies

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Running Tests

```bash
pytest -v --tb=short                    # All tests
pytest tests/test_ranking.py -v         # Single module
pytest tests/test_ranking.py::test_unified_scoring -v   # Single test
pytest -k "scoring" -v                  # Tests matching keyword
pytest --co -q                          # List all tests without running
```

## Conventions

- One test file per subpackage: `tests/test_{module}.py`.
- `test_imports.py` is a smoke test that verifies all modules are importable and
  key classes/functions exist. This catches broken imports early.
- Test functions follow `test_{what_is_being_tested}` naming.
- Tests import directly from source: `from statebind.ranking.scoring import score_unified`.
- Tests construct their own data inline rather than using shared conftest fixtures.

## Optional Dependency Testing

For ML modules that require torch/torch_geometric/rdkit, use `pytest.importorskip()`:

```python
def test_mpnn_forward():
    torch = pytest.importorskip("torch")
    pyg = pytest.importorskip("torch_geometric")
    # ... test code that requires torch and PyG
```

Alternatively, check the module-level flags:

```python
from statebind.ml import HAS_TORCH
@pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")
def test_vae_training():
    ...
```

## Test Count

If you add tests, the total count must be >= 618. Never delete or skip existing
tests without explicit justification.

---

## SLURM GPU Testing Policy

**Audience:** Head AI, Modular Agents working on scoring/ML/docking/evaluation.

### Three Test Tiers

| Tier | Command | When | Time | What It Proves |
|------|---------|------|------|----------------|
| **Quick local** | `pytest -v --tb=short` | Every code change, before any commit | ~30s | Core logic, no optional deps |
| **Full local** | `pip install -e ".[dev,science]" && pytest -v --tb=short` | After adding tests or changing imports | ~30s | + sklearn/scipy/matplotlib tests |
| **Full SLURM GPU** | Submit `scripts/run_tests_all.slurm` | See trigger list below | ~65 min | ALL 618 tests pass, 0 skips, 0 failures |

### When Full SLURM GPU Tests Are Required

A SLURM GPU test run (**Tier 3**) is **mandatory** before pushing to GitHub when
ANY of the following files are modified:

- `src/statebind/ranking/scoring.py` — scoring cascade, weight validation
- `src/statebind/ranking/pareto.py` — Pareto front computation
- `src/statebind/chemistry/docking.py` — GNINA wrapper
- `src/statebind/ml/` — any ML model code, adapters, predictors
- `src/statebind/evaluation/` — comparison, figures, docking analysis, Pareto comparison
- `tests/test_docking.py` — docking test changes
- `tests/test_admet_integration.py` — ADMET model quality tests
- `tests/test_pareto.py` — Pareto tests
- `configs/docking.yaml` — docking configuration

For changes to **other** files (data/, utils/, processing/, baselines/, generation/,
context/, dynamics/, structure/, scripts/, docs/), Tier 1 (quick local) is sufficient.

### SLURM Test Environment

The canonical SLURM test script is `scripts/run_tests_all.slurm`. It uses:

```bash
module purge
module load Python/3.12.3
module load CUDA/12.6.0 cuDNN/9.5.1.17-CUDA-12.6.0
source "$HOME/projects/statebind/envs/statebind/bin/activate"
```

This venv contains: torch 2.6.0+cu124, torch_geometric 2.7.0, sklearn 1.8.0,
pymoo 0.6.1, rdkit, and all project extras.

**Time limit:** Use `-t 02:00:00` (2 hours). The GNINA docking tests add ~60 minutes
because each `dock_molecule()` call takes 1-2 minutes on GPU, and the evaluation
tests trigger GNINA for all scored candidates when a GPU is detected.

**Partition:** `scavenge_gpu` (broadest access, preemptable) or `gpu_devel` (dedicated
but limited). Add `--requeue` for scavenge to handle preemption.

### What "All Tests Pass" Means

The gold standard is **618 passed, 0 skipped, 0 failures** on a GPU node with all
dependencies installed. This was verified on 2026-04-07 (SLURM job 7587145, L40S GPU).

**Acceptable skips:** Only if an external binary is genuinely unavailable (e.g., GNINA
not installed on a particular node). Missing pip packages (torch, sklearn, pymoo,
torch_geometric) are NOT acceptable reasons to skip — install them.

### Avoiding Redundant Test Runs

- Do NOT re-run SLURM GPU tests for documentation-only changes (*.md files, comments).
- Do NOT re-run SLURM GPU tests for changes to `scripts/` pipeline scripts (they
  don't affect test outcomes).
- If only adding new tests (not changing existing code), Tier 2 (full local) is
  sufficient unless the new tests require GPU.
- Multiple commits can be batched into a single SLURM test run before pushing.

---

## Optional Dependencies

### The Pattern

The canonical pattern for optional dependencies is demonstrated in `ml/__init__.py`
(lines 22-40):

```python
# Module-level boolean flags
HAS_TORCH: bool
try:
    import torch as _torch  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
```

### Key Principles

1. **Boolean flags at module level.** Callers check `HAS_TORCH` rather than catching
   ImportError themselves. Flags are defined in the `__init__.py` of the module that
   owns the dependency.

2. **Pydantic configs are always importable.** `VAEConfig`, `MPNNConfig`, `ADMETConfig`,
   `TrainerConfig` are all Pydantic models that require ONLY pydantic (a core dep).

3. **Neural network classes are guarded.** The actual model classes use `TYPE_CHECKING`
   guards and are only instantiable when torch is present.

4. **Fallback behavior is always defined.** Every function that might use an optional
   dep must specify what happens when the dep is missing:
   - Scoring: falls back to n-gram Tanimoto (no RDKit)
   - Docking: falls back to constant 0.5 (no MPNN)
   - ADMET: falls back to permissive pass (no model)
   - Validation: falls back to permissive True (no RDKit)

### Dependency Groups (from `pyproject.toml`)

| Extra | Packages | Purpose |
|-------|----------|---------|
| (core) | numpy, pandas, pyyaml, pydantic, typer, rich | Base pipeline, always available |
| `[dev]` | pytest, pytest-cov, ruff, mypy | Testing and linting |
| `[science]` | scikit-learn, scipy, matplotlib, seaborn | Statistical analysis, visualization |
| `[structure]` | biopython | PDB structure parsing |
| `[chemistry]` | rdkit | Molecular fingerprints, descriptors, validation |
| `[ml]` | torch, torch-geometric, rdkit | Neural network training and inference |

**Additional runtime dependencies** (not in pyproject.toml extras):
| Package | Install | Purpose |
|---------|---------|---------|
| pymoo | `pip install pymoo` | Exact hypervolume computation for Pareto (WS12). Falls back to numpy without it. |
| selfies | `pip install selfies` | SELFIES↔SMILES conversion for VAE generation. |
| openbabel-wheel | `pip install openbabel-wheel` | PDBQT conversion for GNINA receptor preparation. |

**External binaries** (not pip-installable):
| Binary | Location | Purpose |
|--------|----------|---------|
| GNINA v1.1 | `bin/gnina` (gitignored) | Physics-informed molecular docking. Download from GNINA releases. |
