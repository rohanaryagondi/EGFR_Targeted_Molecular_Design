"""File I/O helpers."""

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it doesn't exist. Returns the Path."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Any, path: str | Path) -> None:
    """Save data as JSON."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str | Path) -> Any:
    """Load data from JSON file."""
    with open(path) as f:
        return json.load(f)
