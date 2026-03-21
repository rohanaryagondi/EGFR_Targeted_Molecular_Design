# statebind.utils

## Purpose

Shared utility functions used across the StateBind codebase. Provides YAML configuration loading and common file I/O helpers (JSON serialization, directory creation). This is a leaf dependency with no imports from other StateBind subpackages.

## Public API

Exported from `__init__.py`:

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `load_config` | `(config_path: str \| Path) -> dict[str, Any]` | Load a YAML configuration file; returns empty dict for empty files |
| `ensure_dir` | `(path: str \| Path) -> Path` | Create directory (and parents) if it does not exist; returns the `Path` |
| `save_json` | `(data: Any, path: str \| Path) -> None` | Save data as formatted JSON; auto-creates parent directories |
| `load_json` | `(path: str \| Path) -> Any` | Load and return data from a JSON file |

## Internal Files

| File | Responsibility |
|------|---------------|
| `config.py` | YAML config loading via `yaml.safe_load`; raises `FileNotFoundError` for missing files and `yaml.YAMLError` for invalid YAML |
| `io.py` | JSON read/write helpers and `ensure_dir` for directory creation; `save_json` uses `json.dump` with `indent=2` and `default=str` |
| `__init__.py` | Re-exports `load_config`, `ensure_dir`, `load_json`, `save_json` |

## Dependencies

- **Imports from:** No other `statebind` subpackages. External dependencies are `pyyaml` (`yaml`) and the standard library (`json`, `pathlib`).
- **Imported by:** Many modules and scripts throughout the StateBind codebase.

## Data Flow

- **Reads:** YAML configuration files (via `load_config`) and JSON data files (via `load_json`) at paths provided by the caller.
- **Produces:** JSON files on disk (via `save_json`); directories on disk (via `ensure_dir`). No in-memory artifacts beyond the returned dicts/objects.

## Testing

- **Test file:** `tests/test_utils.py`
- **Run:** `pytest tests/test_utils.py -v`
- **Key fixtures:** Uses `tmp_path` (pytest built-in) for all file operations.
- **Tests:**
  - `test_load_config_valid` -- writes a YAML file to `tmp_path`, loads it, asserts correct key/value and nested structure
  - `test_load_config_missing` -- asserts `FileNotFoundError` for nonexistent path
  - `test_load_config_empty` -- empty YAML file returns `{}`
  - `test_ensure_dir` -- creates nested directories (`a/b/c`), verifies they exist and return value matches
  - `test_save_and_load_json` -- round-trip: save dict with nested list, load it back, assert equality

## Patterns to Follow

- Keep utilities stateless and side-effect-free (except file I/O).
- `save_json` always calls `ensure_dir` on the parent directory, so callers never need to create directories manually before writing.
- `load_config` returns `{}` (not `None`) for empty YAML files, so callers can safely use `.get()` without null checks.
- All path parameters accept both `str` and `Path` and are normalized internally via `Path()`.

## Known Limitations

- `load_config` only supports YAML; there is no TOML or INI loader.
- `save_json` uses `default=str` as a fallback serializer, which silently converts non-serializable objects to their string representation rather than raising an error.
- No file locking or atomic writes; concurrent writes to the same path could produce corrupt files.

## Planned Improvements

No workstream modifications are currently planned for this module.
