#!/usr/bin/env python
"""Summarize available data coverage across all categories.

Reads manifests and reports counts by category and status.

Usage:
    python scripts/summarize_data_inventory.py
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.data.manifest import Manifest
from statebind.data.paths import DataPaths
from statebind.data.validation import check_file_coverage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize available data across all categories",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory",
    )
    args = parser.parse_args()

    paths = DataPaths(args.project_root)

    print("=" * 60)
    print("StateBind Data Inventory")
    print("=" * 60)
    print()

    coverage = check_file_coverage(args.project_root)

    for category, counts in coverage.items():
        print(f"── {category.upper()} {'─' * (50 - len(category))}")
        if "no_manifest" in counts:
            print("  No manifest found. Run: python scripts/register_sources.py")
        elif "manifest_error" in counts:
            print("  Manifest parse error. Check manifest file.")
        else:
            total = counts.get("total_registered", 0)
            present = counts.get("files_present", 0)
            pending = counts.get("pending", 0)
            downloaded = counts.get("downloaded", 0)
            validated = counts.get("validated", 0)
            processed = counts.get("processed", 0)

            print(f"  Registered: {total}")
            print(f"  Files present on disk: {present}")
            print(f"  Status breakdown:")
            print(f"    pending:    {pending}")
            print(f"    downloaded: {downloaded}")
            print(f"    validated:  {validated}")
            print(f"    processed:  {processed}")
        print()

    # Print detailed manifest entries
    print("=" * 60)
    print("Detailed File Listing")
    print("=" * 60)
    print()

    categories = ["context", "structures", "ligands"]
    for category in categories:
        manifest_path = paths.manifest_path(category)
        if not manifest_path.exists():
            continue
        try:
            manifest = Manifest.load(manifest_path)
        except Exception:
            continue

        print(f"── {category.upper()} {'─' * (50 - len(category))}")
        for entry in manifest.entries:
            exists = "✓" if entry.file_exists(paths.root) else "✗"
            print(f"  [{exists}] {entry.status:<12} {entry.file_path}")
            print(f"      source: {entry.source_name}  format: {entry.format}")
            if entry.notes:
                print(f"      notes: {entry.notes}")
        print()


if __name__ == "__main__":
    main()
