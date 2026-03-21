# statebind.generation

## Purpose

Phase 6 of StateBind: generates candidate molecules conditioned on each EGFR conformational state's pocket geometry. Unlike the static baseline (Phase 2) which generates against a single active-state structure, this module generates against all 4 conformational states with pocket-aware SMILES-level modifications tailored to each state's geometry. Implements 7 generation strategies (hinge optimization, back pocket extension, gatekeeper avoidance, volume filling, covalent warhead, P-loop interaction, analog enumeration), applies state-aware chemistry filtering (type-I vs type-II rules), and computes intra/cross-state diversity metrics.

## Public API

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `GenerationStrategy` | `Enum: HINGE_OPTIMIZED, BACK_POCKET_EXTENSION, GATEKEEPER_AVOIDING, VOLUME_FILLING, COVALENT_WARHEAD, P_LOOP_INTERACTION, REFERENCE, ANALOG` | How the candidate was generated relative to the pocket. |
| `StateConditionedCandidate` | `BaseModel(candidate_id, smiles, source, parent_id, target_state, target_pdb_id, strategy, pocket_volume, back_pocket, gatekeeper_clearance, notes)` | A candidate molecule generated conditioned on a specific state. |
| `StateConditionedLibrary` | `BaseModel(state, representative_pdb, pocket_volume, back_pocket_accessible, candidates, n_candidates, strategies_used, generation_config)` | Library of candidates generated for a specific state. |
| `MultiStateGenerationResult` | `BaseModel(version, states, libraries, total_candidates, total_unique_smiles, cross_state_overlap, generated_at, notes)` | Complete output from multi-state generation. |
| `FilteredStateLibrary` | `BaseModel(state, n_input, n_passed, n_failed, pass_rate, candidates, property_stats)` | Filtered candidates for a single state. |
| `MultiStateFilterResult` | `BaseModel(version, states, libraries, total_input, total_passed, overall_pass_rate, generated_at)` | Filtered results across all states. |
| `PocketCondition` | `@dataclass(state, representative_pdb, pocket, strategies, rationale)` | Pocket-derived generation condition for a single state. |
| `get_pocket_conditions()` | `() -> dict[str, PocketCondition]` | Return pocket conditions for all 4 canonical EGFR states with literature-curated volumes. |
| `select_strategies_for_pocket()` | `(pocket: PocketDescriptor) -> list[GenerationStrategy]` | Dynamically select strategies based on arbitrary pocket features. |
| `generate_for_state()` | `(condition: PocketCondition) -> StateConditionedLibrary` | Generate candidates conditioned on a single state's pocket. |
| `generate_all_states()` | `() -> MultiStateGenerationResult` | Generate candidates for all 4 conformational states. |
| `get_filters_for_state()` | `(state: str) -> list[PropertyFilter]` | Return appropriate filters (type-I or type-II) based on conformational state. |
| `filter_state_library()` | `(library: StateConditionedLibrary, filters: list[PropertyFilter] \| None = None) -> FilteredStateLibrary` | Filter candidates for a single state with state-appropriate defaults. |
| `filter_all_states()` | `(generation: MultiStateGenerationResult) -> MultiStateFilterResult` | Filter candidates across all states (type-I for DFGin, type-II for DFGout). |
| `DiversityMetrics` | `@dataclass(n_candidates, n_unique_smiles, mean_pairwise_tanimoto, diversity_score, min_tanimoto, max_tanimoto)` | Diversity metrics for a set of candidates. |
| `StateDiversityReport` | `@dataclass(state, intra_diversity, n_state_unique, n_shared, unique_fraction)` | Per-state diversity analysis. |
| `CrossStateDiversityReport` | `@dataclass(per_state, overlap_matrix, total_unique_across_all, total_candidates, global_diversity)` | Cross-state diversity analysis. |
| `compute_diversity()` | `(smiles_list: list[str], max_pairs: int = 500) -> DiversityMetrics` | Compute diversity metrics using pairwise Tanimoto (sampled for efficiency). |
| `analyze_cross_state_diversity()` | `(filtered: MultiStateFilterResult) -> CrossStateDiversityReport` | Analyze diversity within and across states. |
| `StateEvaluation` | `@dataclass(state, n_generated, n_filtered, filter_pass_rate, validity_rate, uniqueness_rate, diversity_score, n_state_unique, unique_fraction, strategies_used, mean_mw)` | Evaluation metrics for a single state's candidates. |
| `GenerationEvaluation` | `@dataclass(per_state, total_generated, total_filtered, total_unique, global_diversity, cross_state_overlap, baseline_comparison)` | Complete evaluation of multi-state generation. |
| `BaselineComparison` | `@dataclass(static_n_candidates, state_conditioned_n_candidates, state_conditioned_unique, overlap_with_static, state_only_candidates, static_only_candidates, diversity_static, diversity_state_conditioned)` | Comparison between state-conditioned and static baseline. |
| `evaluate_generation()` | `(generation, filtered, diversity_report) -> GenerationEvaluation` | Evaluate multi-state generation results. |
| `compare_with_static_baseline()` | `(filtered: MultiStateFilterResult, static_smiles: set[str]) -> BaselineComparison` | Compare state-conditioned candidates against static baseline. |
| `evaluation_to_dict()` | `(evl: GenerationEvaluation) -> dict` | Serialize evaluation to dict. |
| `save_evaluation()` | `(evl: GenerationEvaluation, path: Path) -> None` | Save evaluation to JSON. |

## Internal Files

| File | Responsibility |
|------|---------------|
| `__init__.py` | Package docstring; documents Phase 6 purpose and module layout. |
| `models.py` | Pydantic models: `GenerationStrategy` enum, `StateConditionedCandidate`, `StateConditionedLibrary`, `MultiStateGenerationResult`, `FilteredStateLibrary`, `MultiStateFilterResult`. |
| `conditioning.py` | Pocket-to-modification mapping: `PocketCondition` dataclass, `get_pocket_conditions()` with literature-curated pocket volumes for all 4 states, `select_strategies_for_pocket()` for dynamic strategy selection. |
| `generator.py` | Core generation engine: 6 strategy-specific SMILES transformation functions (`_hinge_optimized`, `_back_pocket_extension`, `_gatekeeper_avoiding`, `_volume_filling`, `_covalent_warhead`, `_p_loop_interaction`), plus `_generate_analogs` wrapping Phase 2 enumeration. Strategy dispatch table `_STRATEGY_FN`. Top-level `generate_for_state()` and `generate_all_states()`. |
| `filtering.py` | State-aware chemistry filtering: `_type1_filters()` (MW<=600) for DFGin states, `_type2_filters()` (MW<=800) for DFGout states, `filter_state_library()`, `filter_all_states()`. |
| `diversity.py` | Intra-state and cross-state diversity analysis: `compute_diversity()` using SMILES n-gram Tanimoto with pair sampling, `analyze_cross_state_diversity()` for overlap matrices and state-unique counts. |
| `evaluation.py` | Generation quality evaluation: per-state metrics (validity, uniqueness, diversity, MW), baseline comparison, serialization to JSON. |

## Dependencies

- **Imports from:**
  - `statebind.baselines.candidates` (`_enumerate_simple_analogs`, `build_reference_candidates`)
  - `statebind.baselines.filtering` (`_count_rings`, `_estimate_heavy_atom_count`, `_estimate_hba`, `_estimate_hbd`, `_estimate_mw`, `_is_valid_smiles`, `compute_properties`)
  - `statebind.baselines.scoring` (`_tanimoto_ngram`)
  - `statebind.baselines.models` (`CandidateSource`, `PropertyFilter`)
  - `statebind.structure.models` (`PocketDescriptor`)
  - `statebind.processing.models` (`ConformationalState`)
- **Imported by:**
  - `statebind.ranking.models` (imports `FilteredStateLibrary`, `MultiStateFilterResult` -- used in `scoring.py`)
  - `statebind.ranking.scoring` (imports `FilteredStateLibrary`, `MultiStateFilterResult`)
  - `statebind.evaluation` (imports diversity functions)

## Data Flow

**Reads:**
- Reference compounds from `statebind.baselines.candidates.build_reference_candidates()` (approved EGFR TKIs).
- Pocket conditions are hardcoded in `conditioning.py` with literature-curated pocket volumes (450-850 cubic angstroms).

**Produces:**
- `MultiStateGenerationResult`: per-state candidate libraries with strategy metadata, cross-state SMILES overlap counts.
- `MultiStateFilterResult`: filtered candidates with property statistics per state.
- `CrossStateDiversityReport`: intra/cross-state diversity metrics, overlap matrix, state-unique counts.
- `GenerationEvaluation` (serialized via `save_evaluation()` to JSON): validity rates, filter pass rates, diversity scores, strategy usage.

## Testing

- **Test file:** `tests/test_generation.py`
- **Run:** `pytest tests/test_generation.py -v`
- **Key fixtures:** `conditions` (calls `get_pocket_conditions()`), `generation` (calls `generate_all_states()`), `filtered` (calls `filter_all_states(generation)`)
- **Test classes:** `TestCandidateSchema` (field presence, state/strategy tracking), `TestConditioning` (4 states covered, strategy assignments per state, dynamic selection), `TestGeneration` (all states produce candidates, cross-state overlap, correct strategy assignment per state, deduplication, determinism), `TestFiltering` (type-I vs type-II MW thresholds, pass rate ranges, valid SMILES), `TestDiversity` (single/identical/different SMILES, cross-state unique candidates), `TestEvaluation` (per-state output, dict serialization, baseline comparison), `TestMetadataTracking` (timestamps, generation config, parent tracking, pocket volumes)

## Patterns to Follow

- Each generation strategy is a standalone function with signature `(smiles: str, parent_id: str, state: str) -> list[StateConditionedCandidate]`, registered in the `_STRATEGY_FN` dispatch dict.
- All SMILES transformations are string-level (no RDKit). Chemical realism is approximate.
- Candidate IDs are deterministic MD5 hashes of `smiles:state:strategy`.
- DFGin states use type-I filters (MW <= 600); DFGout states use type-II filters (MW <= 800).
- Diversity computation uses SMILES 3-gram Tanimoto (from `baselines.scoring._tanimoto_ngram`) with pair sampling capped at `max_pairs=500`.
- Deduplication by SMILES is applied within each state in `generate_for_state()`.

## Known Limitations

- All modifications are SMILES string manipulations, not 3D-aware. No docking or conformer generation.
- Pocket volumes are literature-curated estimates, not computed from PDB structures.
- Diversity computation uses SMILES n-gram Tanimoto, which is an approximation of Morgan fingerprint Tanimoto.
- Strategy-specific transformations are simple (e.g., appending functional groups, swapping atoms) and may produce chemically invalid or synthetically infeasible molecules.
- The `_gatekeeper_avoiding` strategy uses naive string matching (`"OC"`, `"Cl"` in SMILES) which can match unintended substructures.

## Planned Improvements

- **Workstream 02** will upgrade diversity computation in `diversity.py` to use Morgan fingerprints instead of SMILES n-gram Tanimoto.

## Current Status

Complete for rule-based generation (7 strategies). VAE integration is pending (WS07). ADMET filtering is pending (WS09).

## Remaining Work for AI Agents

- **WS07** creates VAE integration to load ML-generated candidates as `StateConditionedCandidate` objects with `source=ML_GENERATED`, `strategy=VAE_GENERATED`. Read `workstreams/07-conditional-vae.md`.
- **WS09** creates `generation/admet_filter.py` for ADMET safety filtering. Read `workstreams/09-admet-predictor.md`.
- See `generation/CRITICAL.md` for non-obvious facts.
