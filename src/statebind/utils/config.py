"""Configuration loading utilities."""

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is not valid YAML.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    if config is None:
        return {}

    return config
