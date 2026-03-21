# statebind.processing

## Purpose

The data layer for StateBind. This module builds processed, validated benchmark datasets from hand-curated raw data covering EGFR kinase mutations, crystal structures, and reference ligands. It defines the canonical Pydantic schemas consumed by all downstream modules, constructs cross-reference mapping tables, runs integrity validation, and assembles the complete benchmark package (JSON + CSV) to disk.

## Public API

Exported from `__init__.py`:

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `build_context_dataset` | `(assign_splits: bool = True, split_seed: int = 42) -> ContextDataset` | Build the processed mutation/context dataset with optional train/val/test splits |
| `build_structure_dataset` | `() -> StructureDataset` | Build the processed EGFR structure dataset from curated PDB metadata |
| `build_ligand_dataset` | `() -> LigandDataset` | Build the processed ligand dataset from curated compounds and approved TKIs |
| `build_mapping_tables` | `(context: ContextDataset, structures: StructureDataset, ligands: LigandDataset) -> MappingTables` | Build cross-reference tables connecting mutations, structures, and ligands |
| `assemble_benchmark` | `(output_dir: Path, split_seed: int = 42, fail_on_error: bool = True) -> BenchmarkSummary` | Full pipeline: build all datasets, validate, write JSON/CSV, return summary |
| `validate_dataset` | `(context: ContextDataset \| None = None, structures: StructureDataset \| None = None, ligands: LigandDataset \| None = None, mappings: MappingTables \| None = None) -> DatasetValidationReport` | Validate processed datasets for integrity (nulls, duplicates, cross-references, splits) |

### Key models (models.py)

| Symbol | Kind | Description |
|--------|------|-------------|
| `ConformationalState` | `str, Enum` | `DFGin_aCin`, `DFGin_aCout`, `DFGout_aCin`, `DFGout_aCout`, `unclassified` |
| `ResistanceGeneration` | `str, Enum` | `1st`, `2nd`, `3rd`, `4th`, `activating`, `unknown` |
| `MechanismCategory` | `str, Enum` | `gatekeeper`, `covalent_site`, `hinge`, `hydrophobic_spine`, `p_loop`, `activation_loop`, `solvent_front`, `ac_helix`, `allosteric`, `activating_mutation`, `other`, `unknown` |
| `ConformationalEffect` | `str, Enum` | `stabilizes_DFGin`, `stabilizes_DFGout`, `stabilizes_active`, `destabilizes_inactive`, `steric_clash`, `no_direct_conformational`, `unknown` |
| `LigandSource` | `str, Enum` | `pdb_cocrystal`, `chembl`, `approved_drug`, `manual` |
| `Provenance` | `BaseModel` | Source tracking: `sources: list[str]`, `processing_version`, `processing_date`, `notes` |
| `MutationRecord` | `BaseModel` | Single EGFR mutation with resistance generation, mechanism category, conformational effect, preferred states, drug annotations, PDB links, references, and split assignment |
| `ContextDataset` | `BaseModel` | Full mutation dataset: `version`, `gene`, `uniprot_id`, `kinase_domain_start/end`, `mutations: list[MutationRecord]` |
| `StructureRecord` | `BaseModel` | Single PDB structure: `pdb_id`, `resolution`, `state`, `chain`, `mutations_present`, `ligand_id`, `ligand_bound`, `is_apo`, `is_representative` |
| `StructureDataset` | `BaseModel` | Full structure dataset: `structures: list[StructureRecord]` |
| `LigandRecord` | `BaseModel` | Single ligand/compound: `ligand_id`, `canonical_smiles`, `source`, `drug_name`, `pIC50`, `mw`, `logp`, `hbd`, `hba`, `is_approved`, `generation` |
| `LigandDataset` | `BaseModel` | Full ligand dataset: `ligands: list[LigandRecord]` |
| `MutationStructureMapping` | `BaseModel` | Maps `mutation_id` to `pdb_id` with chain, state, and ligand |
| `StructureLigandMapping` | `BaseModel` | Maps `pdb_id` to `ligand_id` with chain |
| `MappingTables` | `BaseModel` | Cross-reference tables: `mutation_structure` and `structure_ligand` lists |
| `BenchmarkSummary` | `BaseModel` | Aggregate statistics: counts, states represented, resistance generations, split counts |

### Validation (validation.py)

| Symbol | Kind | Description |
|--------|------|-------------|
| `ValidationIssue` | `@dataclass` | Single issue: `level` (error/warning), `dataset`, `field`, `message` |
| `DatasetValidationReport` | `@dataclass` | Aggregated report with `.errors`, `.warnings`, `.is_valid`, `.add()`, `.summary()` |

## Internal Files

| File | Responsibility |
|------|---------------|
| `models.py` | Pydantic models and enums defining the schema for every processed table |
| `context.py` | Hand-curated EGFR mutation set (17 mutations); builds `ContextDataset` with deterministic train/val/test splits via position-hash bucketing |
| `structures.py` | Hand-curated EGFR PDB structures (18 structures across 4 conformational states plus apo); builds `StructureDataset` |
| `ligands.py` | Hand-curated EGFR TKIs and co-crystal ligands (9 compounds); builds `LigandDataset` |
| `mapping.py` | Constructs `MappingTables` by cross-referencing mutation PDB lists, structure mutation fields, and ligand-bound structures |
| `benchmark.py` | Orchestrates full benchmark build: calls all builders, validates, writes JSON + CSV outputs, generates `BenchmarkSummary` |
| `validation.py` | Checks nulls, duplicates, schema integrity, split coverage, key mutation presence, cross-dataset reference integrity, and provenance completeness |
| `__init__.py` | Re-exports the six public builder/validator functions |

## Dependencies

- **Imports from:** No other `statebind` subpackages. Uses only `pydantic`, standard library (`datetime`, `hashlib`, `json`, `csv`, `pathlib`, `enum`).
- **Imported by:** `statebind.structure`, `statebind.context`, and other downstream modules that consume processed data schemas.

## Data Flow

- **Reads:** No external files at build time. All data is embedded as curated Python literals in `context.py`, `structures.py`, and `ligands.py`.
- **Produces (via `assemble_benchmark`):**
  - `context.json` / `context.csv` -- mutation dataset
  - `structures.json` / `structures.csv` -- structure dataset
  - `ligands.json` / `ligands.csv` -- ligand dataset
  - `mappings.json` -- cross-reference tables
  - `mapping_mutation_structure.csv` / `mapping_structure_ligand.csv` -- mapping tables as CSV
  - `summary.json` -- benchmark statistics
  - `validation_report.txt` -- human-readable validation output
- **Config format:** YAML config files consumed by other modules reference the output paths of these datasets.

## Testing

- **Test file:** `tests/test_processing.py`
- **Run:** `pytest tests/test_processing.py -v`
- **Key fixtures:** Uses `tmp_path` (pytest built-in) for benchmark assembly file output tests.
- **Test classes:**
  - `TestContextDataset` -- minimum count (>=15), key mutation presence (T790M, L858R, C797S), no duplicates, valid fields, split assignment, split determinism, provenance, T790M annotation correctness
  - `TestStructureDataset` -- no duplicate PDB IDs, all 4 conformational states represented, 4-char lowercase PDB IDs, representative structures, apo consistency
  - `TestLigandDataset` -- no duplicate IDs, approved drugs present (>=3), SMILES for approved drugs, osimertinib detail check
  - `TestMappingTables` -- T790M maps to structures, every ligand-bound structure has a mapping
  - `TestValidation` -- full validation passes, empty context fails, duplicate ID detection, missing key mutations, invalid wild_type
  - `TestBenchmarkAssembly` -- all output files produced, deterministic across runs, CSV files have data rows

## Patterns to Follow

- All dataset schemas are Pydantic `BaseModel` subclasses in `models.py`; add new entity types there.
- Curated data is stored as Python literals inside builder functions (`_v1_curated_*`), not in external files.
- Every record carries a `Provenance` object tracking source databases and processing date.
- The `assemble_benchmark` function is the single entry point that orchestrates the full build-validate-write cycle.
- Validation is layered: per-dataset checks first, then cross-dataset reference integrity.
- Train/val/test splits are deterministic given a seed, using MD5 hash bucketing on `mutation_id:seed`.

## Known Limitations

- All curated data is for EGFR only; no other kinase targets.
- SMILES for one co-crystal ligand (`DJK`) is a placeholder empty string.
- Molecular properties (MW, logP, HBD, HBA) are only populated for approved drugs, not co-crystal ligands.
- The `ConformationalEffect` annotation is `unknown` for several resistance mutations where the structural mechanism has not been characterized.
- `dfg_distance` and `ac_helix_metric` fields on `StructureRecord` are all `None` in v1 (geometric classification was done by visual inspection, not automated measurement).

## Planned Improvements

No workstream modifications are currently planned for this module.

## Current Status

Complete. All 18 mutations, 16 structures, and 9 ligands are curated as Python literals. Benchmark assembly and validation are tested.

## Remaining Work for AI Agents

No pending workstream work. Future: expand mutation annotations for multi-state preferences if new literature data becomes available.
