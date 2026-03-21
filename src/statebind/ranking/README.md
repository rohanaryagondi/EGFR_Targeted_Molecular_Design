# statebind.ranking

## Purpose

Phase 7 of StateBind: provides a unified scoring and ranking framework that applies the same scoring function to both static-baseline and state-conditioned candidates, enabling fair comparison. Scores candidates on four axes (reference similarity, druglikeness, docking proxy, state specificity), ranks each pipeline independently, then merges both pools into a global ranking with SMILES-based deduplication. Includes rank-shift analysis to identify candidates promoted or demoted by the unified comparison.

## Public API

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `PipelineLabel` | `Enum: STATIC = "static_baseline", STATE_AWARE = "state_aware"` | Which pipeline produced the candidate. |
| `UnifiedScoreComponent` | `BaseModel(name, value, weight, method, is_stub)` | A single scoring axis with value, weight, and method description. |
| `UnifiedScoredCandidate` | `BaseModel(candidate_id, smiles, pipeline, target_state, strategy, scores, composite_score, rank_in_pipeline, global_rank)` | A candidate scored under the unified scheme, with `.get_score(name)` lookup. |
| `RankedPool` | `BaseModel(pipeline, scoring_method, candidates, generated_at, notes)` | Ranked candidates from a single pipeline, with `.n_ranked` property. |
| `MergedRanking` | `BaseModel(static_pool, state_aware_pool, merged, generated_at, notes)` | Merged ranking of candidates from both pipelines, with `.n_total` property. |
| `RankShift` | `BaseModel(candidate_id, smiles, pipeline, pipeline_rank, global_rank, shift, composite_score)` | How a candidate's rank changed from pipeline-local to global (positive = promoted). |
| `DEFAULT_WEIGHTS` | `dict` | `{"reference_similarity": 0.35, "druglikeness": 0.30, "docking_proxy": 0.20, "state_specificity": 0.15}` |
| `_validate_weights()` | `(weights: dict[str, float]) -> None` | Verify scoring weights sum to 1.0 and all required keys present. Raises `ValueError` on failure. |
| `_compute_state_specificity()` | `(smiles, target_state, state_smiles_map) -> float` | Reward candidates unique to their target state: 1.0 (1 state), 0.5 (2 states), 0.25 (3 states), 0.0 (4 states or no target). |
| `score_unified()` | `(smiles, target_state, pipeline, state_smiles_map, weights=None) -> tuple[list[UnifiedScoreComponent], float]` | Score a single candidate under the unified scheme; returns (components, composite_score). |
| `rank_static_baseline()` | `(filtered: FilteredLibrary, weights=None) -> RankedPool` | Score and rank static baseline candidates; state_specificity is always 0. |
| `rank_state_aware()` | `(filtered: MultiStateFilterResult, weights=None) -> RankedPool` | Score and rank state-conditioned candidates with cross-state deduplication. |
| `merge_rankings()` | `(static_pool: RankedPool, state_aware_pool: RankedPool) -> MergedRanking` | Merge both pools into global ranking, deduplicating by SMILES (keeps higher score). |
| `compute_rank_shifts()` | `(merged: MergedRanking) -> list[RankShift]` | Compute rank shifts for every candidate (shift = pipeline_rank - global_rank). |
| `top_k_by_pipeline()` | `(merged: MergedRanking, k: int = 10) -> dict[str, list[UnifiedScoredCandidate]]` | Extract top-K candidates from each pipeline's own ranking. |
| `top_k_global()` | `(merged: MergedRanking, k: int = 10) -> list[UnifiedScoredCandidate]` | Extract top-K candidates from the merged global ranking. |
| `pipeline_representation_in_top_k()` | `(merged: MergedRanking, k: int = 10) -> dict[str, int]` | Count how many of the global top-K come from each pipeline. |
| `mean_rank_by_pipeline()` | `(merged: MergedRanking) -> dict[str, float]` | Mean global rank of candidates from each pipeline. |
| `score_distribution_by_pipeline()` | `(merged: MergedRanking) -> dict[str, dict[str, float]]` | Compute score statistics (mean, std, min, max, n) per pipeline. |

## Internal Files

| File | Responsibility |
|------|---------------|
| `__init__.py` | Package docstring; states the unified scoring principle. |
| `models.py` | Pydantic models: `PipelineLabel`, `UnifiedScoreComponent`, `UnifiedScoredCandidate`, `RankedPool`, `MergedRanking`, `RankShift`. |
| `scoring.py` | Unified scoring engine: `DEFAULT_WEIGHTS`, `SCORING_METHOD` description string, `_validate_weights()`, `_compute_state_specificity()`, `score_unified()`, `rank_static_baseline()`, `rank_state_aware()`, `merge_rankings()`. |
| `aggregation.py` | Rank aggregation and analysis: `compute_rank_shifts()`, `top_k_by_pipeline()`, `top_k_global()`, `pipeline_representation_in_top_k()`, `mean_rank_by_pipeline()`, `score_distribution_by_pipeline()`. |

## Dependencies

- **Imports from:**
  - `statebind.baselines.scoring` (`_score_druglikeness`, `_score_reference_similarity`, `_score_docking_stub`, `_tanimoto_ngram`)
  - `statebind.baselines.filtering` (`compute_properties`)
  - `statebind.baselines.models` (`FilteredLibrary`)
  - `statebind.generation.models` (`FilteredStateLibrary`, `MultiStateFilterResult`)
- **Imported by:**
  - `statebind.evaluation` (imports `MergedRanking` and aggregation functions)

## Data Flow

**Reads:**
- `FilteredLibrary` from the static baseline pipeline (Phase 2) -- passed to `rank_static_baseline()`.
- `MultiStateFilterResult` from the generation pipeline (Phase 6) -- passed to `rank_state_aware()`.
- Scoring components (`_score_reference_similarity`, `_score_druglikeness`, `_score_docking_stub`) from `statebind.baselines.scoring`.

**Produces:**
- `RankedPool` for each pipeline (static and state-aware), containing scored and ranked candidates with per-component breakdowns.
- `MergedRanking` with SMILES-deduplicated global ranking across both pipelines.
- `list[RankShift]` showing how each candidate's rank changed from pipeline-local to global.
- Score distribution statistics per pipeline (mean, std, min, max).

## Testing

- **Test file:** `tests/test_ranking.py`
- **Run:** `pytest tests/test_ranking.py -v`
- **Key fixtures:** `baseline` (calls `run_static_baseline()`, module-scoped), `state_filtered` (generates + filters all states, module-scoped), `static_pool`, `state_pool`, `merged`
- **Test classes:** `TestRankingModels` (Pydantic schema validation, `PipelineLabel` values, `get_score()` lookup, `n_ranked`/`n_total` properties), `TestUnifiedScoring` (4 components returned, static has zero specificity, specificity geometric decay for 1/2/4 states, composite is weighted sum, docking proxy is stub at 0.5, weights sum to 1.0), `TestPipelineRanking` (non-empty pools, correct labels, sequential ranks, descending scores, static all-zero specificity), `TestMergeRanking` (non-empty, unique SMILES, sequential global ranks, descending scores, both pipelines present, size bounded), `TestAggregation` (rank shift count and formula, top-K extraction, pipeline representation, mean rank, score distribution stats)

## Patterns to Follow

- The same `score_unified()` function is used for both pipelines. The only dimension where state-aware candidates gain an advantage is `state_specificity`; all other components are identical.
- `DEFAULT_WEIGHTS` must always sum to 1.0 -- enforced by `_validate_weights()`.
- State specificity uses geometric decay: `1/2^(n-1)` where n is the number of states the candidate appears in.
- Deduplication in `merge_rankings()` keeps the higher-scoring version when the same SMILES appears in both pipelines.
- Deduplication in `rank_state_aware()` keeps the first occurrence when the same SMILES appears across multiple states.
- All `RankedPool` and `MergedRanking` objects include timestamps and scoring method documentation.

## Known Limitations

- The `docking_proxy` component is a **stub** that always returns 0.5. It does not perform any actual docking computation.
- State specificity is a simple count-based heuristic, not a binding-affinity-based metric.
- `_score_reference_similarity` uses SMILES 3-gram Tanimoto (from baselines), not Morgan fingerprint similarity.
- Deduplication by SMILES does not account for different stereochemistry or tautomers that produce different SMILES strings for the same molecule.
- The `SCORING_METHOD` string is hardcoded; changing weights requires updating it manually.

## Planned Improvements

- **Workstream 02** will update scoring method strings and may adjust the diversity/similarity computation used in reference_similarity.
- **Workstream 04** will replace the `docking_proxy` stub (constant 0.5) with an actual docking score using Vina or GNINA, following the MLP pattern from `statebind.dynamics.world_model`.

## Current Status

Complete but docking component is a stub (constant 0.5), wasting 20% of score weight. Three workstreams will modify `scoring.py` sequentially.

## Remaining Work for AI Agents

**CONFLICT ZONE**: Three workstreams modify `scoring.py`. They MUST execute in this order:
1. **WS02** (first): Updates scoring method strings, wires in RDKit chemistry. Read `workstreams/02-scoring-integration.md`.
2. **WS04** (second): Adds DockingProxy MLP as fallback. Read `workstreams/04-docking-proxy.md`.
3. **WS08** (third): Adds MPNN as primary docking scorer with cascading fallback. Read `workstreams/08-mpnn-affinity.md`.

Do NOT change `DEFAULT_WEIGHTS` values or `_validate_weights()` signature.
See `ranking/CRITICAL.md` for non-obvious facts.
