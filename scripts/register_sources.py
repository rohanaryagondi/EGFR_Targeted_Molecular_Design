#!/usr/bin/env python
"""Register all known data sources and create manifest files.

This script creates the data directory structure and writes initial
manifest files based on the source registry. It does NOT download data.

Usage:
    python scripts/register_sources.py
    python scripts/register_sources.py --project-root /path/to/project
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from statebind.data.paths import DataPaths
from statebind.data.registry import SourceRegistry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register data sources and create manifest files",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory",
    )
    args = parser.parse_args()

    paths = DataPaths(args.project_root)

    # Create directory structure
    print("Creating data directory structure...")
    paths.ensure_all()

    # Build registry
    registry = SourceRegistry.default()
    print(f"Registry contains {len(registry)} source specifications")
    print()

    # Build and save manifests
    manifests = registry.build_all_manifests()
    for category, manifest in manifests.items():
        manifest_path = paths.manifest_path(category)
        manifest.save(manifest_path)
        print(f"  [{category}] {len(manifest)} entries → {manifest_path.relative_to(paths.root)}")

    print()
    print("Source registration complete.")
    print("Next steps:")
    print("  1. Download raw data files according to notes in each manifest")
    print("  2. Run: python scripts/validate_data_layout.py")
    print("  3. Run: python scripts/summarize_data_inventory.py")

    # Print required files
    print()
    print("Required files to obtain:")
    for spec in registry.required_specs():
        print(f"  [{spec.source_name}] {spec.file_path}")
        if spec.notes:
            print(f"           {spec.notes}")


if __name__ == "__main__":
    main()
