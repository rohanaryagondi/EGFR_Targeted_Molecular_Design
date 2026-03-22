# statebind.chemistry

## Purpose

RDKit-backed molecular computations with graceful fallbacks. Provides Morgan fingerprints, exact molecular descriptors, SMILES validation/canonicalization, and synthetic accessibility scoring. Every function returns a safe default when RDKit is not installed so the base pipeline is never blocked.

## Public API

| Symbol | Type | Signature | Description |
|--------|------|-----------|-------------|
| `HAS_RDKIT` | bool | — | `True` when `rdkit` is importable |
| `compute_morgan_fingerprint` | function | `(smiles, radius=2, n_bits=2048) -> Any \| None` | Morgan/ECFP4 bit vector; `None` without RDKit |
| `compute_morgan_similarity` | function | `(smiles_a, smiles_b, radius=2, n_bits=2048) -> float` | Tanimoto similarity in [0, 1]; falls back to n-gram |
| `compute_max_reference_similarity` | function | `(smiles, references=None) -> float` | Max similarity to reference EGFR binders |
| `compute_exact_properties` | function | `(smiles) -> dict[str, float \| None]` | Exact MW, HBA, HBD, rings, heavy atoms, TPSA, LogP, rotatable bonds |
| `validate_smiles` | function | `(smiles) -> bool` | `True` if valid; permissive `True` without RDKit |
| `canonicalize_smiles` | function | `(smiles) -> str \| None` | Canonical SMILES; original string without RDKit |
| `compute_sa_score` | function | `(smiles) -> float` | SA score in [1, 10]; `5.0` without RDKit |

## Internal Files

| File | Responsibility |
|------|---------------|
| `fingerprints.py` | Morgan fingerprint computation, Tanimoto similarity, `HAS_RDKIT` flag |
| `descriptors.py` | Exact molecular property computation via RDKit `Descriptors` and `rdMolDescriptors` |
| `validation.py` | SMILES validation (`MolFromSmiles`) and canonicalization (`MolToSmiles`) |
| `sa_score.py` | Synthetic accessibility scoring: Contrib sascorer -> simplified heuristic -> 5.0 |
| `__init__.py` | Package docstring and re-exports |

## Optional Dependencies

| Package | Flag | Purpose |
|---------|------|---------|
| `rdkit` | `HAS_RDKIT` | All chemistry computations; listed in `pyproject.toml [chemistry]` extra |

## Dependencies

- **Imports from:** `statebind.baselines.scoring` (`_tanimoto_ngram` for fallback, `_REFERENCE_BINDERS` for reference binders)
- **Imported by:** (future) WS02 wires into `baselines/scoring.py` and `ranking/scoring.py`; WS04 adds `docking_proxy.py` here

## Data Flow

Pure computation — reads no files, produces no artifacts.

## Testing

- **Test file:** `tests/test_chemistry.py`
- **Run:** `pytest tests/test_chemistry.py -v`
- **Coverage:** Fingerprints, descriptors, validation, SA score; both RDKit-present and fallback paths

## Known Limitations

- **SA score without Contrib:** Falls back to a simplified ring/stereo/size heuristic that is less accurate than the fragment-based Ertl approach.
- **N-gram fallback:** When RDKit is unavailable, similarity uses SMILES character 3-grams — a crude textual proxy, not a molecular fingerprint.
- **Property key names:** Uses `estimated_mw` etc. for backward compatibility with `baselines/filtering.py`, even though values are exact when RDKit is available.

## Current Status

Complete. All functions implemented with RDKit paths and graceful fallbacks.
