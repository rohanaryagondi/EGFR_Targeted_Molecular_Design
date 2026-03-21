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

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
