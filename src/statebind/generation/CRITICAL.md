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

- `vae_integration.py` has NO torch dependency — it reads JSON and wraps in Pydantic models. Safe to import unconditionally.
- `load_vae_candidates()` filters out entries with `is_valid=False` AND entries with empty SMILES. Both are silently dropped (logged at DEBUG/INFO level).
- `load_vae_candidates()` raises `ValueError` on unknown state labels rather than silently dropping them. This is intentional — bad state labels indicate upstream bugs that should not be masked.
- `candidate_id` format is `"vae_{state}_{per_state_counter:04d}"` — counter resets per state, so IDs are unique only within a single `load_vae_candidates()` call.
- `build_vae_libraries()` extracts temperature from the first candidate's `notes` field by string splitting on `"temperature="`. Fragile — will return 0.0 if notes format changes.
- `DEFAULT_STATE_MAPPING` is imported from `ml/vae_dataset.py:41-46` for state validation. If that mapping changes, `vae_integration.py` automatically picks up the change.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
