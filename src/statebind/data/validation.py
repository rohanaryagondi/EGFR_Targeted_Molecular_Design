"""Data layout validation: check that expected directories and files exist.

This module verifies the data layer integrity without downloading anything.
It checks directory structure, manifest presence, and file status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from statebind.data.manifest import Manifest
from statebind.data.paths import DataPaths


@dataclass
class ValidationIssue:
    """A single validation issue."""

    level: str  # "error" or "warning"
    category: str  # "directory", "manifest", "file"
    message: str
    path: str = ""


@dataclass
class ValidationReport:
    """Aggregated validation results."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def is_valid(self) -> bool:
        """True if there are no errors (warnings are acceptable)."""
        return len(self.errors) == 0

    def add(self, level: str, category: str, message: str, path: str = "") -> None:
        self.issues.append(ValidationIssue(
            level=level, category=category, message=message, path=path,
        ))

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = []
        lines.append(f"Validation: {'PASS' if self.is_valid else 'FAIL'}")
        lines.append(f"  Errors:   {len(self.errors)}")
        lines.append(f"  Warnings: {len(self.warnings)}")
        if self.issues:
            lines.append("")
            for issue in self.issues:
                prefix = "ERROR" if issue.level == "error" else "WARN "
                lines.append(f"  [{prefix}] {issue.category}: {issue.message}")
                if issue.path:
                    lines.append(f"           path: {issue.path}")
        return "\n".join(lines)


def validate_data_layout(project_root: Path | None = None) -> ValidationReport:
    """Validate the data directory structure and manifest integrity.

    Checks:
    1. All expected directories exist
    2. Manifest files exist for each category
    3. Manifest files are valid JSON and parse correctly
    4. For each manifest entry, checks if the referenced file exists

    Args:
        project_root: Project root directory. Auto-detected if None.

    Returns:
        ValidationReport with all issues found.
    """
    paths = DataPaths(project_root)
    report = ValidationReport()

    # 1. Check directories
    for expected_dir in paths.all_expected_dirs():
        if not expected_dir.is_dir():
            report.add(
                level="error",
                category="directory",
                message=f"Missing directory: {expected_dir.relative_to(paths.root)}",
                path=str(expected_dir),
            )

    # 2. Check manifests
    categories = ["context", "structures", "ligands"]
    for category in categories:
        manifest_path = paths.manifest_path(category)
        if not manifest_path.exists():
            report.add(
                level="warning",
                category="manifest",
                message=f"Manifest not found for category '{category}'",
                path=str(manifest_path),
            )
            continue

        # 3. Parse manifest
        try:
            manifest = Manifest.load(manifest_path)
        except Exception as e:
            report.add(
                level="error",
                category="manifest",
                message=f"Invalid manifest for '{category}': {e}",
                path=str(manifest_path),
            )
            continue

        # 4. Check files referenced in manifest
        for entry in manifest.entries:
            if entry.status == "pending":
                # Pending files are expected to be missing
                continue
            full_path = paths.root / entry.file_path
            if not full_path.exists():
                report.add(
                    level="error" if entry.status in ("downloaded", "validated") else "warning",
                    category="file",
                    message=f"Manifest entry '{entry.file_path}' has status "
                            f"'{entry.status}' but file is missing",
                    path=str(full_path),
                )

    return report


def check_file_coverage(
    project_root: Path | None = None,
) -> dict[str, dict[str, int]]:
    """Summarize data file coverage by category and status.

    Returns:
        Dict mapping category → {status: count}.
    """
    paths = DataPaths(project_root)
    coverage: dict[str, dict[str, int]] = {}

    categories = ["context", "structures", "ligands"]
    for category in categories:
        manifest_path = paths.manifest_path(category)
        if not manifest_path.exists():
            coverage[category] = {"no_manifest": 0}
            continue

        try:
            manifest = Manifest.load(manifest_path)
            coverage[category] = manifest.summary()
            # Also count actual files present
            present = sum(
                1 for e in manifest.entries
                if e.file_exists(paths.root)
            )
            coverage[category]["files_present"] = present
            coverage[category]["total_registered"] = len(manifest)
        except Exception:
            coverage[category] = {"manifest_error": 0}

    return coverage
