# Critical Information -- Utils

- `load_config()` at `config.py:9-32` uses `yaml.safe_load()` -- safe against arbitrary code execution. Returns empty dict `{}` for empty YAML files (`config.py:29-30`).
- `load_config()` raises `FileNotFoundError` if path does not exist (`config.py:23-24`) and `yaml.YAMLError` for invalid YAML.
- `save_json()` at `io.py:15-20` auto-creates parent directories via `ensure_dir(path.parent)` -- safe to call with non-existent paths.
- `save_json()` uses `default=str` for JSON serialization (`io.py:20`) -- this silently converts non-serializable objects (Path, datetime) to strings. Can mask bugs.
- `load_json()` at `io.py:23-26` does NOT create directories or handle missing files -- it raises `FileNotFoundError` on missing paths.
- This module has ZERO statebind imports (leaf module) -- `__init__.py:8-9` imports only from `statebind.utils.*` submodules.
- Any module in the codebase can safely import from `utils/` without creating circular dependencies.
- `ensure_dir()` at `io.py:8-12` returns the `Path` object after creation -- useful for chaining.
- All other statebind modules depend on utils (directly or transitively) for config loading and JSON I/O.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
