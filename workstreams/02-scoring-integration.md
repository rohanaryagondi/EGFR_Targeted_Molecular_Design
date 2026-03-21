# Workstream 02: Scoring Integration

## Goal

Wire the chemistry module (from Workstream 01) into the existing scoring pipeline so that Morgan fingerprints replace n-gram similarity, RDKit descriptors replace heuristic property estimation, and scoring method strings accurately reflect which backend is active. All existing function signatures and return types must be preserved for backward compatibility.

## Prerequisites

**Workstream 01 must be complete.** This workstream imports from `statebind.chemistry`.

**Cannot run in parallel with Workstream 04** — both modify `baselines/scoring.py` and `ranking/scoring.py`.

## Files to Modify

### `src/statebind/baselines/scoring.py`

**Change 1: Replace n-gram similarity with Morgan fingerprint similarity**

Current (lines 69-77):
```python
def _score_reference_similarity(smiles: str) -> float:
    similarities = [_tanimoto_ngram(smiles, ref) for ref in _REFERENCE_BINDERS]
    return max(similarities) if similarities else 0.0
```

New:
```python
def _score_reference_similarity(smiles: str) -> float:
    try:
        from statebind.chemistry.fingerprints import compute_max_reference_similarity, HAS_RDKIT
        if HAS_RDKIT:
            return compute_max_reference_similarity(smiles, _REFERENCE_BINDERS)
    except ImportError:
        pass
    # Fallback to n-gram
    similarities = [_tanimoto_ngram(smiles, ref) for ref in _REFERENCE_BINDERS]
    return max(similarities) if similarities else 0.0
```

**Change 2: Update ScoreComponent.method strings**

In `score_candidates()` (line 198), update the `method` string for `reference_similarity`:
```python
# Dynamically set method string
try:
    from statebind.chemistry.fingerprints import HAS_RDKIT
    sim_method = "Morgan/ECFP4 Tanimoto (radius=2, 2048 bits)" if HAS_RDKIT else "SMILES 3-gram Tanimoto"
except ImportError:
    sim_method = "SMILES 3-gram Tanimoto"
```

### `src/statebind/baselines/filtering.py`

**Change: Upgrade `compute_properties()` to use RDKit when available**

Current `compute_properties()` (around line 147) uses regex heuristics. Add a branch:
```python
def compute_properties(smiles: str) -> dict[str, float | None]:
    try:
        from statebind.chemistry.descriptors import compute_exact_properties
        from statebind.chemistry.fingerprints import HAS_RDKIT
        if HAS_RDKIT:
            return compute_exact_properties(smiles)
    except ImportError:
        pass
    # Existing heuristic path (unchanged)
    return _compute_heuristic_properties(smiles)
```

Extract the existing heuristic logic into `_compute_heuristic_properties()` (private function) so the fallback is clean.

### `src/statebind/ranking/scoring.py`

**Change 1: Update SCORING_METHOD string (line 47-52)**

Make it dynamic:
```python
def _get_scoring_method() -> str:
    try:
        from statebind.chemistry.fingerprints import HAS_RDKIT
        if HAS_RDKIT:
            return (
                "Unified weighted sum: reference_similarity(0.35, Morgan/ECFP4) + "
                "druglikeness(0.30, RDKit descriptors) + docking_proxy(0.20) + "
                "state_specificity(0.15). docking_proxy is a STUB (constant 0.5)."
            )
    except ImportError:
        pass
    return SCORING_METHOD  # original string
```

**Change 2: Update UnifiedScoreComponent method strings in `score_unified()` (lines 122-148)**

Same pattern — dynamically set `method` based on `HAS_RDKIT`.

### `src/statebind/generation/diversity.py`

**Change: Upgrade diversity computation to use Morgan fingerprints**

Current (line 14): `from statebind.baselines.scoring import _tanimoto_ngram`

Add Morgan fingerprint branch in `compute_diversity()`:
```python
def _pairwise_similarity(smiles_a: str, smiles_b: str) -> float:
    try:
        from statebind.chemistry.fingerprints import compute_morgan_similarity, HAS_RDKIT
        if HAS_RDKIT:
            return compute_morgan_similarity(smiles_a, smiles_b)
    except ImportError:
        pass
    return _tanimoto_ngram(smiles_a, smiles_b)
```

### `tests/test_baselines.py`

Add tests:
- `test_scoring_uses_morgan_when_available()` — verify method string changes
- `test_scoring_falls_back_to_ngram()` — mock ImportError
- `test_properties_use_rdkit_when_available()` — verify exact vs heuristic

### `tests/test_ranking.py`

Add test:
- `test_scoring_method_string_reflects_backend()` — verify dynamic method string

## Files NOT to Touch

- `src/statebind/chemistry/*` — Workstream 01 owns this
- `src/statebind/evaluation/*` — separate workstreams
- `src/statebind/dynamics/*`, `src/statebind/context/*`, `src/statebind/structure/*`
- Docking stub (`_score_docking_stub`) — Workstream 04 owns this

## Interface Contract

All existing function signatures MUST be preserved:
- `_score_reference_similarity(smiles: str) -> float` — same signature
- `_score_druglikeness(properties: dict[str, float | None]) -> float` — same signature
- `compute_properties(smiles: str) -> dict[str, float | None]` — same signature, same required keys
- `score_candidates(filtered, target_pdb_id, weights) -> RankedCandidates` — same signature
- `score_unified(smiles, target_state, pipeline, state_smiles_map, weights) -> tuple` — same signature
- `compute_diversity(smiles_list) -> DiversityMetrics` — same signature

## Definition of Done

- [ ] `_score_reference_similarity()` uses Morgan fingerprints when RDKit available
- [ ] `compute_properties()` uses RDKit descriptors when available
- [ ] Both fall back cleanly to existing behavior without RDKit
- [ ] Method strings dynamically reflect which backend is active
- [ ] Diversity computation uses Morgan fingerprints when available
- [ ] All existing 359+ tests pass
- [ ] New tests verify both RDKit and fallback paths
- [ ] No function signature changes

---

## Critical Information Maintenance

When you discover non-obvious facts during implementation — edge cases, gotchas, implicit assumptions, or things that broke unexpectedly — add them to the relevant CRITICAL.md file(s):

- **Module-level**: `src/statebind/{module}/CRITICAL.md` for facts specific to the module you modified
- **Project-level**: `/CRITICAL.md` for facts that cross module boundaries

Format: one fact per line, include `file:line` references. Be detailed yet concise.

## Agent Instructions

Be detailed yet concise in all code, comments, and documentation. Include `file:line` references when noting important locations. No fluff — every line should carry information.
