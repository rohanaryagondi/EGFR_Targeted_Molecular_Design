#!/usr/bin/env python
"""Validate the data directory structure and manifest integrity.

Checks that all expected directories exist, manifests are valid, and
registered files are present when expected.

Usage:
    python scripts/validate_data_layout.py
    python scripts/validate_data_layout.py --strict
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.data.validation import validate_data_layout


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate data directory structure and manifests",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    report = validate_data_layout(args.project_root)

    print(report.summary())

    if args.strict and report.warnings:
        print("\n--strict mode: warnings treated as errors")
        sys.exit(1)

    if not report.is_valid:
        sys.exit(1)

    print("\nData layout validation passed.")


if __name__ == "__main__":
    main()
