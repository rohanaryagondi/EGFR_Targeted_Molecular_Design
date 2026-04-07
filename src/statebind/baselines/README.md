# statebind.baselines

## Purpose

Static single-structure design pipeline (Phase 2) that serves as the baseline that state-aware design must beat. It uses one EGFR structure (1M17), one literature-derived ATP-binding pocket definition, and conventional scoring -- deliberately ignoring conformational state information. The pipeline covers structure selection, pocket definition, candidate library construction, property filtering, scoring/ranking, and evaluation.

## Public API

| Symbol | Type | Signature | Description |
|--------|------|-----------|-------------|
| `get_baseline_pocket` | function | `(pdb_id: str = "1m17", chain: str = "A") -> PocketDefinition` | Return the literature-defined EGFR ATP-binding pocket for the static baseline |
| `select_baseline_structure` | function | `() -> dict` | Select and return metadata for the baseline structure (1M17) |
| `build_reference_candidates` | function | `() -> list[Candidate]` | Build candidates from the curated reference ligand dataset |
| `build_candidate_library` | function | `(target_pdb_id: str = "1m17", pocket_id: str = "1m17_A_ATP", enumerate_analogs: bool = True) -> CandidateLibrary` | Build the full candidate library (reference compounds + optional enumerated analogs) |
| `compute_properties` | function | `(smiles: str) -> dict[str, float \| None]` | Compute estimated molecular properties from SMILES |
| `apply_filters` | function | `(library: CandidateLibrary, filters: list[PropertyFilter] \| None = None) -> FilteredLibrary` | Apply property filters (default: Lipinski-like) to a candidate library |
| `score_candidates` | function | `(filtered: FilteredLibrary, target_pdb_id: str = "1m17", weights: dict[str, float] \| None = None) -> RankedCandidates` | Score and rank filtered candidates by weighted composite (similarity + druglikeness + docking stub) |
| `evaluate_baseline` | function | `(ranked: RankedCandidates, top_k: int = 10) -> BaselineEvaluation` | Evaluate a baseline run for validity, uniqueness, diversity, and score statistics |
| `run_static_baseline` | function | `(output_dir: Path \| None = None, enumerate_analogs: bool = True, top_k: int = 10) -> BaselineResult` | Run the complete 6-step static baseline pipeline end-to-end |
| `BaselineResult` | dataclass | fields: `structure_metadata`, `pocket`, `library`, `filtered`, `ranked`, `evaluation` | Container for all artifacts from a static baseline run |
| `PocketDefinition` | Pydantic model | -- | Binding pocket definition with residues, volume, source |
| `PocketResidue` | Pydantic model | -- | Single residue in a binding pocket |
| `Candidate` | Pydantic model | -- | A candidate molecule with SMILES and source metadata |
| `CandidateLibrary` | Pydantic model | -- | Collection of candidates for a baseline run |
| `PropertyFilter` | Pydantic model | -- | Single property filter criterion (property name, min/max) |
| `FilterResult` | Pydantic model | -- | Result of applying property filters to one candidate |
| `FilteredLibrary` | Pydantic model | -- | Candidates that passed property filtering |
| `ScoreComponent` | Pydantic model | -- | Single scoring component (name, value, weight, method, is_stub) |
| `ScoredCandidate` | Pydantic model | -- | Candidate with computed scores and composite rank |
| `RankedCandidates` | Pydantic model | -- | Final ranked output from the baseline pipeline |
| `BaselineEvaluation` | Pydantic model | -- | Evaluation metrics for a baseline run |
| `DEFAULT_FILTERS` | constant | `list[PropertyFilter]` | Default Lipinski-like filters (MW 200-600, HBA 1-10, HBD 0-5, heavy atoms 15-50, rings 1-8) |

## Internal Files

| File | Responsibility |
|------|---------------|
| `models.py` | Pydantic data models for every intermediate and output artifact (pocket, candidate, filtering, scoring, evaluation) |
| `pocket.py` | Literature-derived EGFR ATP-binding pocket definition (19 residues) and baseline structure selection (1M17) |
| `candidates.py` | Candidate library construction from reference ligands plus simple SMILES-based analog enumeration (halogen swaps, methyl/methoxy swaps, N-demethylation) |
| `filtering.py` | SMILES-based heuristic property estimation (MW, HBA, HBD, heavy atoms, rings) and Lipinski-like filtering |
| `scoring.py` | Three-component scoring: SMILES n-gram Tanimoto similarity to reference binders, property-based druglikeness, and docking stub (constant 0.5) |
| `pipeline.py` | End-to-end orchestration of the 6-step pipeline; artifact serialization to JSON and CSV |
| `evaluation.py` | Validity, uniqueness, diversity (intra-set Tanimoto), and per-score-component statistics |
| `__init__.py` | Package docstring |

## Dependencies

- **Imports from:** `statebind.processing.ligands` (build_ligand_dataset, used by candidates.py)
- **Imported by:** `statebind.generation` (candidates, filtering), `statebind.ranking` (scoring functions), `statebind.evaluation` (via ranking)

## Data Flow

**Reads:**
- Curated ligand dataset via `statebind.processing.ligands.build_ligand_dataset()`

**Produces (when output_dir is set):**
- `structure_selection.json` -- baseline structure metadata
- `pocket_definition.json` -- pocket residue list
- `candidate_library.json` -- all candidates with sources
- `filtered_library.json` -- filter pass/fail results with computed properties
- `ranked_candidates.json` -- scored and ranked candidates
- `evaluation.json` -- validity, uniqueness, diversity, score stats
- `ranking_table.csv` -- human-readable ranking summary

## Testing

- **Test file:** `tests/test_baselines.py`
- **Run:** `pytest tests/test_baselines.py -v`
- **Key fixtures:** Uses pytest classes (`TestPocketDefinition`, etc.) organized by pipeline stage
- **Coverage:** Pocket definition, candidate library construction, property estimation, SMILES validity, filtering, Tanimoto similarity, scoring, evaluation metrics, end-to-end pipeline

## Patterns to Follow

- Every intermediate artifact has a typed Pydantic model in `models.py`.
- Heuristic/approximate methods are clearly documented as such in docstrings with explicit `NOT a substitute for RDKit` warnings.
- Stub components set `is_stub=True` on `ScoreComponent` so downstream consumers can identify them.
- Scoring weights are configurable via the `weights` dict parameter.
- All functions that produce artifacts include timestamps via `datetime.now(timezone.utc)`.

## Known Limitations

- **SMILES n-gram similarity:** Fallback only. Primary similarity uses Morgan/ECFP4 fingerprints (radius=2, 2048 bits) via WS02. SMILES 3-gram Tanimoto is used only when RDKit is unavailable.
- **Docking stub:** Last fallback in the 3-tier scoring cascade (MPNN -> DockingProxy MLP -> constant 0.5 stub). The stub is only reached when neither trained MPNN nor DockingProxy MLP checkpoints are available.
- **Heuristic property estimation:** MW, HBA, HBD, ring count, and heavy atom count are estimated from SMILES string patterns, not computed from a molecular graph. Accuracy is approximately +/-10-20%.
- **SMILES validity check:** `_is_valid_smiles` uses heuristic checks (balanced parens/brackets, atom characters present), not a real SMILES parser.
- **Analog enumeration:** Simple string-level substitutions that may produce invalid or unsynthesizable molecules.
- **Single-class dataset in practice:** All 17 curated mutations map to DFGin_aCin, so the baseline cannot differentiate across states by design.

## Completed Improvements

- **Workstream 01 (Chemistry foundation):** Replaced SMILES-based heuristics with RDKit-based property calculations and Morgan fingerprint similarity.
- **Workstream 02 (Scoring integration):** WS02 added Morgan/ECFP4 similarity and RDKit-based druglikeness (QED + Lipinski + SA score) into the scoring pipeline.
- **Workstream 04 (Docking proxy):** WS04 added DockingProxy MLP as tier-2 fallback in the 3-tier docking cascade (MPNN -> MLP -> stub).

## Current Status

Complete. All workstreams (WS01, WS02, WS04) are done. Scoring uses Morgan/ECFP4 fingerprints for similarity, RDKit descriptors for druglikeness, and the 3-tier docking cascade (MPNN -> DockingProxy MLP -> constant 0.5 stub). SMILES n-gram similarity and heuristic property estimation serve as fallbacks when RDKit is unavailable.

See `baselines/CRITICAL.md` for non-obvious facts about this module.
