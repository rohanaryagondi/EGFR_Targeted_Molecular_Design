# Critical Information -- Evaluation

- `run_full_comparison()` signature at `comparison.py:176-179` takes `(merged: MergedRanking, top_k: int = 10)`. WS03 may add an optional parameter -- do not break existing callers.
- `ComparativeResult` at `comparison.py:75-86` is a DATACLASS, not a Pydantic model. Do not call `.model_dump()` or `.model_json_schema()` on it.
- All sub-result types (`OverlapAnalysis`, `DiversityComparison`, `ScoreComparison`, `TopKComparison`, `NoveltyAnalysis`) are also dataclasses -- `comparison.py:24-72`.
- ASCII figures in `figures.py` are the current visualization system. No matplotlib dependency is required. `figures.py:1-8` documents this design choice.
- Tables in `tables.py` use plain `list[dict[str, object]]` return types and string formatting -- `tables.py:18-19`.
- `compute_novelty()` at `comparison.py:152-173` identifies candidates unique to state-aware pipeline by SMILES set difference.
- The module imports `compute_diversity` from `generation/diversity.py` at `comparison.py:11` -- the evaluation module depends on generation.
- The module imports `mean_rank_by_pipeline`, `pipeline_representation_in_top_k`, `score_distribution_by_pipeline` from `ranking/aggregation.py` at `comparison.py:12-16`.
- No cherry-picking: all candidates are included in comparisons, not selected subsets -- this is a project-wide rule.
- `TopKComparison.state_aware_fraction` at `comparison.py:61` divides by `max(k, 1)` to avoid zero-division.

## WS03: Statistical Testing

- `statistics.py` uses dataclasses (not Pydantic) for `StatisticalTest` and `BootstrapCI` — consistent with evaluation module convention.
- `statistics.py:14-18`: scipy is optional. `HAS_SCIPY` flag controls whether `mannwhitneyu` is used or falls back to `permutation_test()`.
- `sensitivity.py:52-66` `_rescore_merged()` recomputes composites from stored component values via `candidate.get_score(name)` — does NOT call `score_unified()` (avoids needing `state_smiles_map` which isn't in `MergedRanking`).
- `sensitivity.py:20` `_COMPONENT_NAMES` must match `DEFAULT_WEIGHTS` keys exactly: `["reference_similarity", "druglikeness", "docking_proxy", "state_specificity"]`.
- `comparison.py:87-88`: `ComparativeResult` has two new fields (`statistical_tests: list`, `sensitivity: object`) with defaults. Backward-compatible — existing code that constructs `ComparativeResult` without these fields still works.
- `comparison.py:200`: `run_full_comparison()` now accepts `run_statistics: bool = False`. Default preserves original behavior.
- `figures.py:119-145` `generate_all_figures()` conditionally includes `statistical_summary` and `sensitivity_heatmap` figures only when data is present. Returns 5 figures when `run_statistics=False` (backward compat with `test_evaluation.py:227` assertion).
- `sensitivity.py:110-128` ablation renormalization: remaining weights are divided by their sum to preserve ratios. A rounding fix adjusts the last non-zero component so weights sum exactly to 1.0.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
