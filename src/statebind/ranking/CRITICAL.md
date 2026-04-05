# Critical Information -- Ranking

- Scoring weights MUST sum to 1.0, enforced by `_validate_weights()` at `scoring.py:173-181 (_validate_weights)`. Tolerance is 1e-4.
- 4 required weight keys: `reference_similarity`, `druglikeness`, `docking_proxy`, `state_specificity` -- `scoring.py:175 (_validate_weights required set)`. Missing keys raise `ValueError`.
- `scoring.py` is THE conflict zone: WS02 (scoring integration), WS04 (docking proxy), WS08 (MPNN affinity) all modify it. Execute workstreams sequentially.
- Do NOT change `DEFAULT_WEIGHTS` at `scoring.py:86-91 (DEFAULT_WEIGHTS)` without updating `SCORING_METHOD` string at `scoring.py:93-97 (SCORING_METHOD)` -- they must stay in sync.
- `merge_rankings()` at `scoring.py:339-372 (merge_rankings)` deduplicates by SMILES, keeping the HIGHER-scoring version via `model_copy()`.
- `rank_state_aware()` at `scoring.py:288-336 (rank_state_aware)` deduplicates by SMILES across states keeping FIRST occurrence (lines 299-306, seen_smiles dedup).
- `_compute_state_specificity()` at `scoring.py:139-170 (_compute_state_specificity)` uses geometric decay: 1 state=1.0, 2=0.5, 3=0.25, 4+=0.0. Returns 0.0 if `target_state` is empty.
- Static baseline candidates always get `state_specificity=0` because `target_state=""` and `state_smiles_map={}` -- `scoring.py:257,263 (rank_static_baseline empty_map and score_unified call)`.
- `PipelineLabel` enum at `models.py:14-18 (PipelineLabel)` has exactly 2 values: `STATIC="static_baseline"` and `STATE_AWARE="state_aware"`.
- `UnifiedScoredCandidate.global_rank` at `models.py:42 (global_rank field)` is only populated after `merge_rankings()` -- it is 0 in per-pipeline pools.
- `rank_in_pipeline` is assigned post-sort by index+1 at `scoring.py:275-276 (rank_static_baseline)` and `scoring.py:325-327 (rank_state_aware)`.
- `scoring.py` imports `_score_druglikeness`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram` FROM `baselines/scoring.py` at lines 19-26.

**WS02 Scoring Integration (chemistry module wiring):**
- `baselines/scoring.py` imports from `chemistry.fingerprints` and `chemistry.descriptors` inside function bodies (lazy imports) to avoid circular imports with `chemistry/fingerprints.py` which imports `_tanimoto_ngram` and `_REFERENCE_BINDERS` at module level.
- `_score_druglikeness_enhanced(smiles: str) -> float` at `baselines/scoring.py` is the RDKit path (QED+Lipinski+SA); `_score_druglikeness(properties)` is the heuristic fallback. Callers check `_has_rdkit()` to choose.
- `compute_properties()` in `baselines/filtering.py` returns extra keys (`tpsa`, `logp`, `n_rotatable_bonds`) when RDKit available. Safe because all consumers use `.get()`.
- `compute_properties()` must always return `smiles_valid` key — `compute_exact_properties` from chemistry module does NOT include it; the integration code adds it explicitly.
- `SCORING_METHOD` module constant at `scoring.py:93-97 (SCORING_METHOD)`. `_get_scoring_method()` at `scoring.py:100-136 (_get_scoring_method)` returns the dynamic version used in `RankedPool` artifacts.


**WS08 MPNN Affinity Integration (cascading fallback):**
- `_score_docking()` at `scoring.py:29 (_score_docking)` now has 3-tier cascade: MPNN (`ml/affinity_predictor.predict_affinity`) → DockingProxy MLP (`chemistry/docking_proxy.get_default_proxy`) → stub (`baselines/scoring._score_docking_stub`). All imports are lazy (inside function body).
- MPNN availability is checked via `_model_loaded()` (not `score != 0.5`) because `_normalize_pic50(5.0)` legitimately returns 0.5 for pIC50=5 (IC50=10µM).
- `_get_scoring_method()` at `scoring.py:100 (_get_scoring_method)` checks MPNN first, then proxy, then stub for the dynamic method string.
- Without MPNN checkpoint, the cascade falls through gracefully to WS04 DockingProxy or stub. Existing test `test_docking_proxy_status` at `test_ranking.py:178` is unaffected.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references and function name anchors (e.g., `scoring.py:86 (DEFAULT_WEIGHTS)`).
