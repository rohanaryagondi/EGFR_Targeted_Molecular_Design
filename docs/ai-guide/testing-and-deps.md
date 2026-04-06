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

If you add tests, the total count must be >= 548. Never delete or skip existing
tests without explicit justification.

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
