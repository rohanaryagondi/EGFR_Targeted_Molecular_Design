# Workstream 01: Chemistry Foundation (RDKit Integration)

## Goal

Create a new `src/statebind/chemistry/` package that provides proper cheminformatics functions using RDKit. This replaces the crude SMILES-based approximations currently used throughout the pipeline with scientifically valid implementations. Every function must gracefully fall back to existing behavior when RDKit is not installed.

## Why This Matters

- **reference_similarity** (35% of score weight) currently uses SMILES character 3-gram Tanimoto, which is 10-20x less discriminative than Morgan/ECFP4 fingerprints
- **druglikeness** (30% of score weight) uses regex-based property estimation with +/-10-20% error
- No SMILES validation exists — invalid SMILES silently produce wrong scores
- No synthetic accessibility scoring — some candidates may be unrealizable
- RDKit is already listed in `pyproject.toml` under `[project.optional-dependencies] chemistry`

## Files to Create

### `src/statebind/chemistry/__init__.py`
```python
"""Chemistry module: RDKit-backed molecular computations with graceful fallbacks."""

from statebind.chemistry.fingerprints import (
    compute_morgan_fingerprint,
    compute_morgan_similarity,
    compute_max_reference_similarity,
    HAS_RDKIT,
)
from statebind.chemistry.descriptors import compute_exact_properties
from statebind.chemistry.validation import validate_smiles, canonicalize_smiles
from statebind.chemistry.sa_score import compute_sa_score

__all__ = [
    "compute_morgan_fingerprint",
    "compute_morgan_similarity",
    "compute_max_reference_similarity",
    "compute_exact_properties",
    "validate_smiles",
    "canonicalize_smiles",
    "compute_sa_score",
    "HAS_RDKIT",
]
```

### `src/statebind/chemistry/fingerprints.py`
Morgan fingerprint computation and Tanimoto similarity.

Key functions:
```python
HAS_RDKIT: bool  # module-level flag

def compute_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> Any | None:
    """Compute Morgan fingerprint. Returns None if SMILES invalid or RDKit unavailable."""

def compute_morgan_similarity(smiles_a: str, smiles_b: str, radius: int = 2, n_bits: int = 2048) -> float:
    """Morgan fingerprint Tanimoto similarity in [0, 1]. Falls back to n-gram if no RDKit."""

def compute_max_reference_similarity(smiles: str, references: list[str] | None = None) -> float:
    """Max Morgan similarity to reference EGFR binders. Falls back to n-gram if no RDKit."""
```

Reference binders to reuse from `baselines/scoring.py:59-66`:
```python
_REFERENCE_BINDERS = [
    "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",           # Erlotinib
    "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",      # Gefitinib
    "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",  # Osimertinib
]
```

Fallback pattern:
```python
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, DataStructs
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
```

### `src/statebind/chemistry/descriptors.py`
Exact molecular property computation.

Key function:
```python
def compute_exact_properties(smiles: str) -> dict[str, float | None]:
    """Compute exact molecular properties via RDKit.

    Returns dict with keys matching baselines/filtering.py for backward compat:
        estimated_mw, estimated_hba, estimated_hbd, n_rings, n_heavy_atoms
    Plus additional descriptors:
        tpsa, logp, n_rotatable_bonds

    Falls back to None values if RDKit unavailable or SMILES invalid.
    """
```

Use: `Descriptors.MolWt`, `Descriptors.NumHAcceptors`, `Descriptors.NumHDonors`, `Descriptors.RingCount`, `rdMolDescriptors.CalcNumHeavyAtoms`, `Descriptors.TPSA`, `Descriptors.MolLogP`, `rdMolDescriptors.CalcNumRotatableBonds`

### `src/statebind/chemistry/validation.py`
SMILES validation and canonicalization.

```python
def validate_smiles(smiles: str) -> bool:
    """Check if SMILES is valid. Returns True if RDKit unavailable (permissive fallback)."""

def canonicalize_smiles(smiles: str) -> str | None:
    """Canonicalize SMILES. Returns original string if RDKit unavailable."""
```

### `src/statebind/chemistry/sa_score.py`
Synthetic Accessibility scoring using the Ertl/Schuffenhauer approach.

```python
def compute_sa_score(smiles: str) -> float:
    """Synthetic accessibility score in [1, 10]. 1=easy to synthesize, 10=hard.
    Returns 5.0 (neutral) if RDKit unavailable."""
```

Implementation: Use `rdkit.Chem.RDConfig.RDContribDir` to load the SA_Score fragment data, or implement a simplified version using the fragment-based approach from the Ertl paper.

### `src/statebind/chemistry/README.md`
Per-module README following the project template (see other module READMEs for format).

### `tests/test_chemistry.py`
Target: ~25-30 tests across these categories:

1. **Fingerprint tests:**
   - `test_morgan_similarity_self()` — erlotinib vs itself = 1.0
   - `test_morgan_similarity_range()` — all values in [0, 1]
   - `test_morgan_more_discriminative_than_ngram()` — higher variance across reference set
   - `test_morgan_similarity_symmetric()` — sim(a,b) == sim(b,a)
   - `test_max_reference_similarity()` — known binders score high
   - `test_fallback_without_rdkit()` — mock ImportError, verify n-gram fallback

2. **Descriptor tests:**
   - `test_exact_properties_erlotinib()` — known MW ~393.4, verify within 1%
   - `test_exact_properties_keys()` — must include backward-compat keys
   - `test_exact_properties_invalid_smiles()` — returns None values
   - `test_additional_descriptors()` — tpsa, logp, n_rotatable_bonds present

3. **Validation tests:**
   - `test_validate_valid_smiles()` — parametrized across reference binders
   - `test_validate_invalid_smiles()` — "not_a_smiles", "", "X"
   - `test_canonicalize_smiles()` — known canonical forms

4. **SA score tests:**
   - `test_sa_score_range()` — values in [1, 10]
   - `test_sa_score_simple_molecule()` — benzene should score low (easy)
   - `test_sa_score_complex_molecule()` — highly complex SMILES should score higher
   - `test_sa_score_fallback()` — returns 5.0 without RDKit

## Files NOT to Touch

- `src/statebind/baselines/*` — Workstream 02 handles wiring
- `src/statebind/ranking/*` — Workstream 02 handles wiring
- `src/statebind/evaluation/*` — separate workstreams
- Any existing test files

## Existing Code to Reuse

| What | Where | How |
|------|-------|-----|
| Reference binder SMILES | `baselines/scoring.py:59-66` | Copy the list constant |
| N-gram Tanimoto (fallback) | `baselines/scoring.py:31-54` | Import for fallback: `from statebind.baselines.scoring import _tanimoto_ngram` |
| Property key names | `baselines/filtering.py:26-31` | Match `estimated_mw`, `estimated_hba`, etc. |

## Definition of Done

- [ ] All 5 `.py` files created in `src/statebind/chemistry/`
- [ ] Module README.md created
- [ ] `tests/test_chemistry.py` with 25+ tests
- [ ] All tests pass with RDKit installed (`pip install rdkit`)
- [ ] All tests pass without RDKit (fallback paths exercised)
- [ ] No existing tests broken (`pytest -v --tb=short` passes all 359+ tests)
- [ ] `HAS_RDKIT` flag correctly reflects availability
- [ ] All functions have type annotations and docstrings
