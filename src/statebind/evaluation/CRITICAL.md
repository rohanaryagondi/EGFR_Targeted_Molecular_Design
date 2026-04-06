# Critical Information -- Evaluation

- `run_full_comparison()` signature at `comparison.py:179-183` takes `(merged: MergedRanking, top_k: int = 10, run_statistics: bool = False)`. Default preserves original behavior.
- `ComparativeResult` at `comparison.py:75-89` is a DATACLASS, not a Pydantic model. Do not call `.model_dump()` or `.model_json_schema()` on it.
- All sub-result types (`OverlapAnalysis`, `DiversityComparison`, `ScoreComparison`, `TopKComparison`, `NoveltyAnalysis`) are also dataclasses -- `comparison.py:25-72`.
- ASCII figures in `figures.py` are the current visualization system. No matplotlib dependency is required. `figures.py:1-8` documents this design choice.
- Tables in `tables.py` use plain `list[dict[str, object]]` return types and string formatting -- `tables.py:18-19`.
- `compute_novelty()` at `comparison.py:155-176` identifies candidates unique to state-aware pipeline by SMILES set difference.
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

## WS05: Matplotlib Visualization

- `plotting.py` uses `matplotlib.use("Agg")` at import time (`plotting.py:28`) — figures are always non-interactive. No display server required.
- `_save_figure()` at `plotting.py:63` does NOT close the figure — the caller or `generate_all_plots` orchestrator closes via `plt.close(fig)`. This allows tests to inspect returned Figure objects.
- `generate_all_plots()` at `plotting.py:330` returns dict keys prefixed with `plot_` (e.g., `plot_score_distributions`) to avoid collision with the 5 ASCII figure keys in `figures.py`.
- `figures.py:generate_all_figures()` has `generate_plots: bool = False` default to preserve backward compat with `test_evaluation.py:227` which asserts `len(figures) == 5`. Only opt-in when `generate_plots=True AND output_dir is not None`.
- `plot_score_distributions()` uses summary statistics (mean/std/min/max) from `ComparativeResult.scores`, NOT raw score arrays. Renders as grouped bar chart with error bars, not a violin plot.
- `plot_sensitivity_heatmap()` accepts `object | None` type for the summary parameter and does `isinstance(summary, SensitivitySummary)` check — safe to call with `result.sensitivity` directly.
- `plot_sa_score_distribution()` has a triple guard: HAS_MATPLOTLIB + import `chemistry.sa_score` + HAS_RDKIT. Returns None if any unavailable.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
