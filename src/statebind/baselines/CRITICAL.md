# Critical Information -- Baselines

- Docking stub at `scoring.py:202-216` (`_score_docking_stub`) returns constant 0.5 for ALL candidates regardless of input. This is the #1 score-quality bottleneck.
- Reference binders (erlotinib, gefitinib, osimertinib) are SMILES literals at `scoring.py:59-66`. Adding or removing references changes ALL similarity scores.
- `_tanimoto_ngram` at `scoring.py:43-54` uses SMILES character 3-grams, NOT Morgan/ECFP4 fingerprints. It is a crude text-similarity proxy (fallback only since WS02).
- `_score_druglikeness` at `scoring.py:101-147` uses heuristic property ranges, NOT RDKit descriptors. Returns 0.0 if all properties are None. `_score_druglikeness_enhanced` at `scoring.py:150` uses RDKit QED+Lipinski+SA (WS02).
- `compute_properties()` in `filtering.py` estimates MW, HBA, HBD, heavy atoms, and rings from SMILES regex patterns -- these are rough approximations.
- Baseline scoring weights (0.4/0.3/0.3) at `scoring.py:269-273` (`score_candidates`) DIFFER from unified weights (0.35/0.30/0.20/0.15) at `ranking/scoring.py:86-91`. They are two separate scoring paths.
- `scoring.py` is the conflict zone for WS02 (scoring integration), WS04 (docking proxy), and WS08 (MPNN affinity) -- these workstreams must execute sequentially.
- `CandidateSource` enum at `models.py:53-57` has 4 values: REFERENCE, ENUMERATED, EXTERNAL, ML_GENERATED. The `generation/` module imports this enum.
- `FilteredLibrary` at `models.py:105-113` is consumed by both `baselines/scoring.py:score_candidates()` and `ranking/scoring.py:rank_static_baseline()`.
- `ScoreComponent` at `models.py:119-126` is distinct from `UnifiedScoreComponent` in `ranking/models.py:21-28` -- do not confuse them.
- DEFAULT_FILTERS in `filtering.py:25-31` define Lipinski-like thresholds (MW 200-600, HBA 1-10, HBD 0-5, heavy atoms 15-50, rings 1-8).

- `_score_docking()` at `scoring.py:219-240` implements cascading fallback: DockingProxy MLP → constant 0.5 stub. Returns `(score, is_stub, method_string)` tuple.
- `_score_docking_stub()` at `scoring.py:202-216` is KEPT as the final fallback — do NOT delete it.
- Docking stub line numbers shifted after WS04 additions. The stub is now around line 202, `_score_docking` is around line 219.
- `score_candidates()` now uses `_score_docking()` instead of `_score_docking_stub()` directly. The `is_stub` and `method` on `ScoreComponent` are dynamic.
- WS08 should extend `_score_docking()` to check MPNN first: MPNN → DockingProxy → stub.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
