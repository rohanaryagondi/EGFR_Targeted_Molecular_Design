# statebind.data

## Purpose

Data access layer for the StateBind project. This module provides centralized path resolution, a source registry defining all expected data files, manifest-based provenance tracking for raw and processed data, and validation of the data directory layout. No other module should construct data paths manually -- all path resolution flows through `DataPaths`.

## Public API

| Symbol | Type | Signature | Description |
|--------|------|-----------|-------------|
| `DataPaths` | class | `(project_root: Path \| None = None)` | Centralized path resolver; properties for all data directories and specific file paths |
| `DataPaths.ensure_all` | method | `() -> None` | Create all expected data directories if they do not exist |
| `DataPaths.all_expected_dirs` | method | `() -> list[Path]` | Return all directories that should exist in a valid data layout |
| `DataPaths.manifest_path` | method | `(category: str) -> Path` | Return manifest file path for a given category ("context", "structures", "ligands") |
| `SourceRegistry` | dataclass | field: `specs: list[SourceSpec]` | Registry of all known data sources; authoritative list of what data StateBind expects |
| `SourceRegistry.default` | classmethod | `() -> SourceRegistry` | Create the default registry with all v1 data sources (8 files across 3 categories) |
| `SourceRegistry.add` | method | `(spec: SourceSpec) -> None` | Add a source specification (replaces existing entry for same file_path) |
| `SourceRegistry.get_specs_by_category` | method | `(category: str) -> list[SourceSpec]` | Return specs matching a data category |
| `SourceRegistry.required_specs` | method | `() -> list[SourceSpec]` | Return only required source specs |
| `SourceRegistry.build_manifest` | method | `(category: str) -> Manifest` | Build a manifest for a category from registry specs |
| `SourceRegistry.build_all_manifests` | method | `() -> dict[str, Manifest]` | Build manifests for all categories (context, structures, ligands) |
| `SourceSpec` | dataclass | fields: `file_path`, `description`, `source_name`, `source_url`, `source_version`, `format`, `required`, `notes` | Specification for a single expected data file |
| `Manifest` | Pydantic model | fields: `manifest_version`, `category`, `created_at`, `updated_at`, `entries` | Data manifest tracking all files in a category |
| `Manifest.add_entry` | method | `(entry: ManifestEntry) -> None` | Add an entry, replacing any existing entry with the same file_path |
| `Manifest.get_entry` | method | `(file_path: str) -> ManifestEntry \| None` | Look up an entry by file path |
| `Manifest.files_by_status` | method | `(status: str) -> list[ManifestEntry]` | Return all entries with a given status |
| `Manifest.save` | method | `(path: Path) -> None` | Save manifest to a JSON file |
| `Manifest.load` | classmethod | `(path: Path) -> Manifest` | Load manifest from a JSON file |
| `Manifest.summary` | method | `() -> dict[str, int]` | Return count of entries by status |
| `ManifestEntry` | Pydantic model | fields: `file_path`, `description`, `source_name`, `source_version`, `source_url`, `download_date`, `file_hash`, `file_size_bytes`, `format`, `status`, `notes` | Single entry in a data manifest with lifecycle status |
| `ManifestEntry.compute_hash` | method | `(project_root: Path) -> str` | Compute SHA-256 hash of the file and update the entry |
| `ManifestEntry.file_exists` | method | `(project_root: Path) -> bool` | Check if the manifest file exists on disk |
| `validate_data_layout` | function | `(project_root: Path \| None = None) -> ValidationReport` | Validate directory structure, manifest presence, manifest parsing, and file existence |
| `check_file_coverage` | function | `(project_root: Path \| None = None) -> dict[str, dict[str, int]]` | Summarize data file coverage by category and status |
| `ValidationReport` | dataclass | properties: `errors`, `warnings`, `is_valid`; method: `summary() -> str` | Aggregated validation results |
| `ValidationIssue` | dataclass | fields: `level`, `category`, `message`, `path` | Single validation issue (error or warning) |

## Internal Files

| File | Responsibility |
|------|---------------|
| `paths.py` | `DataPaths` class: centralized path resolution relative to project root; properties for data_dir, manifests_dir, raw/processed subdirectories, specific file paths; directory creation |
| `registry.py` | `SourceRegistry` and `SourceSpec`: defines all expected data files (COSMIC, ClinVar, manual mutations, PDB metadata, KLIFS, UniProt, ChEMBL, approved TKIs) with source URLs and notes |
| `manifest.py` | `Manifest` and `ManifestEntry` Pydantic models: provenance tracking with file hash (SHA-256), lifecycle status (pending/downloaded/validated/processed), save/load to JSON |
| `validation.py` | `validate_data_layout` and `check_file_coverage`: directory structure validation, manifest integrity checks, file existence verification |
| `__init__.py` | Re-exports: `SourceRegistry`, `Manifest`, `ManifestEntry`, `DataPaths`, `validate_data_layout` |

## Dependencies

- **Imports from:** None (this is a leaf module with no statebind dependencies)
- **External:** `pydantic` (for Manifest and ManifestEntry models), `hashlib` (for SHA-256 hashing)
- **Imported by:** `statebind.processing`, `statebind.scripts` (and any module that needs to resolve data paths)

## Data Flow

**Reads:**
- Manifest JSON files from `data/manifests/{context,structures,ligands}.json`
- Data files referenced by manifest entries (for hash computation and existence checks)

**Produces:**
- Manifest JSON files via `Manifest.save()`
- `ValidationReport` objects from `validate_data_layout()`
- Data directories via `DataPaths.ensure_all()`

## Testing

- **Test file:** `tests/test_data.py`
- **Run:** `pytest tests/test_data.py -v`
- **Key fixtures:** `PROJECT_ROOT` constant; `tmp_path` (pytest built-in) for testing file operations and hashing
- **Coverage:** ManifestEntry creation, file existence checks, hash computation, Manifest add/get/save/load, SourceRegistry default creation, specs by category, manifest building, DataPaths resolution, data layout validation

## Patterns to Follow

- All data paths go through `DataPaths` -- never construct paths manually in other modules.
- Every file in the data layer has a corresponding `ManifestEntry` tracking its provenance.
- `ManifestEntry.status` follows a lifecycle: `pending` -> `downloaded` -> `validated` -> `processed`.
- The source registry is the authoritative definition of what data StateBind expects. It does not download data.
- Validation distinguishes errors (missing directories, corrupted manifests) from warnings (missing manifests, pending files).
- Hashes are prefixed with `sha256:` for format identification.

## Known Limitations

- **No download capability:** The registry defines what should exist but does not fetch data. Users must manually download or use external scripts.
- **No incremental manifest updates:** `add_entry` replaces by file_path, but there is no merge/diff capability for manifest evolution.
- **Validation does not verify hashes:** `validate_data_layout` checks file existence but does not re-verify SHA-256 hashes against stored values.

## Planned Improvements

No currently planned workstream modifications. Future work could add automated download scripts, hash verification during validation, and manifest diffing for data versioning.

## Current Status

Complete. All path resolution, manifests, registry, and validation functionality is implemented and tested.

## Remaining Work for AI Agents

No pending workstream work. This is a stable leaf module.
