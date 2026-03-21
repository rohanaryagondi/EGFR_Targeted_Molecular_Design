# Critical Information -- Data

- `DataPaths.__init__` at `paths.py:18-22` walks up 4 parent directories from `paths.py` to find project root: `Path(__file__).resolve().parent.parent.parent.parent`. This is fragile if the file is moved.
- `DataPaths` accepts an explicit `project_root` parameter as fallback -- `paths.py:18`. Always use this in tests or non-standard layouts.
- `ensure_all()` at `paths.py:96-108` creates 7 directories with `mkdir(parents=True, exist_ok=True)` -- safe to call repeatedly.
- Manifests track file hashes for data provenance -- `manifest.py` via `ManifestEntry`. These are not checksummed automatically; scripts must update them.
- This module has ZERO statebind imports (leaf module) -- `__init__.py:3-6` imports only from `statebind.data.*` submodules.
- Any module in the codebase can safely import from `data/` without creating circular dependencies.
- `SourceRegistry` and `Manifest` are re-exported from `__init__.py:3-4` for convenience.
- `validate_data_layout()` at `__init__.py:6` checks that all expected directories exist -- call it before running the pipeline.
- All path properties return `Path` objects, not strings -- consumers must handle `Path` or call `str()`.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
