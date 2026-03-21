# Critical Information -- Generation

- VAE-generated candidates MUST use `source=CandidateSource.ML_GENERATED` and `strategy=GenerationStrategy.VAE_GENERATED` -- `models.py:29,57`.
- All candidates must conform to the `StateConditionedCandidate` Pydantic model at `models.py:32-45`. Missing fields default to empty/zero.
- `GenerationStrategy` enum at `models.py:18-29` has 9 values (7 original + REFERENCE + VAE_GENERATED). Do NOT duplicate existing strategies.
- `CandidateSource` is imported from `baselines/models.py:53-57` -- it is NOT defined in this module. Changing it there breaks generation.
- `target_state` on `StateConditionedCandidate` at `models.py:39` must match `ConformationalState` enum values exactly: DFGin_aCin, DFGin_aCout, DFGout_aCin, DFGout_aCout.
- `MultiStateFilterResult` at `models.py:86-95` is consumed by `ranking/scoring.py:rank_state_aware()` at line 192. Changing its schema breaks ranking.
- `FilteredStateLibrary.candidates` at `models.py:82` contains `StateConditionedCandidate` objects, NOT base `Candidate` objects.
- `StateConditionedLibrary.generation_config` at `models.py:58` uses `dict[str, object]` -- Pydantic will serialize this but complex objects may lose type info.
- `rank_state_aware()` deduplicates across states by SMILES, keeping the first occurrence -- `ranking/scoring.py:202-209`.
- Cross-state overlap tracking at `models.py:69` is a `dict[str, int]` (pair label to count), populated during generation.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
