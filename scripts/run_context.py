#!/usr/bin/env python
"""Run the context module: build EGFR mutation atlas."""

import argparse
import sys

from statebind.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EGFR mutation atlas")
    parser.add_argument(
        "--config", "-c",
        default="configs/context.yaml",
        help="Path to context config file",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Loaded config for module: {config.get('module', 'unknown')}")
    print("Context module not yet implemented (Phase 1).")
    sys.exit(1)


if __name__ == "__main__":
    main()
