#!/usr/bin/env python
"""Run the structure module: build EGFR conformational state atlas."""

import argparse
import sys

from statebind.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR conformational state atlas")
    parser.add_argument(
        "--config", "-c",
        default="configs/structure.yaml",
        help="Path to structure config file",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Loaded config for module: {config.get('module', 'unknown')}")
    print("Structure module not yet implemented (Phase 2).")
    sys.exit(1)


if __name__ == "__main__":
    main()
