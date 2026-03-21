# statebind.evaluation

## Purpose

Head-to-head comparative analysis of the static baseline pipeline versus the state-aware pipeline. This terminal module computes overlap, diversity, score distribution, top-K composition, and novelty metrics between the two candidate pools, then renders the results as structured tables and portable ASCII figures. Every metric is computed across all candidates with no cherry-picking.

## Public API

### comparison.py

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `OverlapAnalysis` | `@dataclass` with fields `static_total`, `state_aware_total`, `shared`, `static_only`, `state_aware_only`, `jaccard` | SMILES overlap between pipelines |
| `DiversityComparison` | `@dataclass` with fields `static: DiversityMetrics`, `state_aware: DiversityMetrics`, `delta_diversity: float` | Side-by-side diversity metrics |
| `ScoreComparison` | `@dataclass` with fields `static_stats: dict[str, float]`, `state_aware_stats: dict[str, float]`, `delta_mean: float` | Score distribution comparison |
| `TopKComparison` | `@dataclass` with fields `k: int`, `static_count`, `state_aware_count`, `state_aware_fraction` | Pipeline composition of the global top-K |
| `NoveltyAnalysis` | `@dataclass` with fields `n_novel`, `novel_smiles`, `novel_strategies`, `novel_states` | Candidates unique to the state-aware pipeline |
| `ComparativeResult` | `@dataclass` aggregating `overlap`, `diversity`, `scores`, `top_k`, `novelty`, `mean_ranks`, `static_n`, `state_aware_n` | Complete comparison container |
| `compute_overlap` | `(merged: MergedRanking) -> OverlapAnalysis` | Compute SMILES Jaccard overlap between pipelines |
| `compute_diversity_comparison` | `(merged: MergedRanking) -> DiversityComparison` | Compare diversity of both candidate pools |
| `compute_score_comparison` | `(merged: MergedRanking) -> ScoreComparison` | Compare score distributions using per-pipeline stats |
| `compute_top_k_comparison` | `(merged: MergedRanking, k: int = 10) -> TopKComparison` | Count pipeline representation in global top-K |
| `compute_novelty` | `(merged: MergedRanking) -> NoveltyAnalysis` | Identify candidates unique to the state-aware pipeline |
| `run_full_comparison` | `(merged: MergedRanking, top_k: int = 10) -> ComparativeResult` | Run the complete comparison suite |

### tables.py

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `summary_table` | `(result: ComparativeResult) -> list[dict[str, object]]` | Head-to-head summary (one row per metric) |
| `top_candidates_table` | `(merged: MergedRanking, k: int = 10) -> list[dict[str, object]]` | Global top-K candidates with scores and metadata |
| `per_pipeline_top_table` | `(merged: MergedRanking, k: int = 5) -> dict[str, list[dict[str, object]]]` | Top-K from each pipeline's own ranking |
| `rank_shift_table` | `(merged: MergedRanking, top_n: int = 10) -> dict[str, list[dict[str, object]]]` | Most promoted and most demoted candidates |
| `novelty_by_strategy_table` | `(result: ComparativeResult) -> list[dict[str, object]]` | Novel state-aware candidates broken down by generation strategy |
| `novelty_by_state_table` | `(result: ComparativeResult) -> list[dict[str, object]]` | Novel state-aware candidates broken down by target conformational state |

### figures.py

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `score_distribution_ascii` | `(result: ComparativeResult) -> str` | ASCII histogram comparing score distributions |
| `diversity_comparison_ascii` | `(result: ComparativeResult) -> str` | ASCII bar chart comparing diversity |
| `top_k_composition_ascii` | `(result: ComparativeResult) -> str` | ASCII chart showing pipeline composition of top-K |
| `novelty_breakdown_ascii` | `(result: ComparativeResult) -> str` | ASCII breakdown of novel candidates by strategy |
| `overlap_venn_ascii` | `(result: ComparativeResult) -> str` | Text-based Venn diagram of SMILES overlap |
| `generate_all_figures` | `(result: ComparativeResult, merged: MergedRanking, output_dir: Path \| None = None) -> dict[str, str]` | Generate all ASCII figures; optionally write to files |

## Internal Files

| File | Responsibility |
|------|---------------|
| `comparison.py` | Dataclasses for every comparison metric; pure-function computation of overlap, diversity, scores, top-K, and novelty |
| `tables.py` | Formats `ComparativeResult` and `MergedRanking` into lists-of-dicts suitable for markdown, CSV, or JSON serialization |
| `figures.py` | Renders ASCII (text-based) figures for embedding in reports without any graphics dependency |
| `__init__.py` | Module docstring only; no re-exports |

## Dependencies

- **Imports from:**
  - `statebind.generation.diversity` -- `compute_diversity`, `DiversityMetrics`
  - `statebind.ranking.aggregation` -- `mean_rank_by_pipeline`, `pipeline_representation_in_top_k`, `score_distribution_by_pipeline`, `compute_rank_shifts`, `top_k_by_pipeline`, `top_k_global`
  - `statebind.ranking.models` -- `MergedRanking`, `PipelineLabel`, `UnifiedScoredCandidate`
- **Imported by:** scripts only (this is a terminal module in the dependency graph)

## Data Flow

- **Reads:** A `MergedRanking` object produced by `statebind.ranking.scoring.merge_rankings`, which contains scored candidate pools from both the static baseline and state-aware pipelines.
- **Produces:** `ComparativeResult` dataclass, lists-of-dicts tables (suitable for JSON/CSV/markdown), and ASCII figure strings. `generate_all_figures` can optionally write `.txt` files to an output directory.

## Testing

- **Test file:** `tests/test_evaluation.py`
- **Run:** `pytest tests/test_evaluation.py -v`
- **Key fixtures:**
  - `pipelines` (module-scoped) -- runs both the static baseline and state-aware pipelines end-to-end, merges rankings, and executes `run_full_comparison`; shared by all tests
  - `merged` -- the `MergedRanking` extracted from `pipelines`
  - `result` -- the `ComparativeResult` extracted from `pipelines`
- **Test classes:** `TestComparisonMetrics` (overlap consistency, Jaccard range, diversity delta, top-K sum, novelty), `TestTables` (row counts, required columns, per-pipeline tables, rank shifts), `TestFigures` (ASCII content assertions, file writing to `tmp_path`)

## Patterns to Follow

- All tables are returned as `list[dict[str, object]]` for uniform serialization.
- Figures use only ASCII characters (block elements and basic text) so they embed directly in markdown without graphics libraries.
- Comparison functions are pure: they receive a `MergedRanking` and return a result dataclass with no side effects.
- The `_bar()` helper in `figures.py` normalizes values to a fixed-width bar for consistent visual alignment.

## Known Limitations

- Figures are text-only; no matplotlib PNG output is generated yet.
- No statistical significance testing (p-values, confidence intervals) is performed on any comparison metric.
- The `novelty_breakdown_ascii` function only breaks down by strategy, not by target state (the state breakdown is only available as a table).
- Tables use `object` typing for values, so downstream consumers must handle mixed int/float/str types.

## Planned Improvements

- **Workstream 03:** A `statistics` sub-module will be added here to provide p-values and confidence intervals for score and diversity deltas.
- **Workstream 05:** Matplotlib-based PNG plotting will be added alongside the existing ASCII figures via `generate_all_figures`.
