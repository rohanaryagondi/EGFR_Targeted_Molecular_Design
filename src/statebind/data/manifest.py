"""Manifest models and utilities for tracking data provenance.

Every raw or processed file in the data layer must have a manifest entry
recording its source, download date, hash, and status.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ManifestEntry(BaseModel):
    """A single entry in a data manifest."""

    file_path: str = Field(description="Relative path from project root")
    description: str = Field(description="Human-readable description of the file")
    source_name: str = Field(description="Source database name (e.g., 'cosmic', 'pdb')")
    source_version: str = Field(default="", description="Database version or release identifier")
    source_url: str = Field(default="", description="URL used for retrieval")
    download_date: str = Field(
        default="",
        description="ISO 8601 date when file was downloaded",
    )
    file_hash: str = Field(default="", description="SHA-256 hash prefixed with 'sha256:'")
    file_size_bytes: int = Field(default=0, description="File size in bytes")
    format: str = Field(default="", description="File format (tsv, json, pdb, csv, sdf, xml)")
    status: Literal["pending", "downloaded", "validated", "processed"] = Field(
        default="pending",
        description="Lifecycle status",
    )
    notes: str = Field(default="", description="Free-text notes")

    def compute_hash(self, project_root: Path) -> str:
        """Compute SHA-256 hash of the file and update the entry.

        Args:
            project_root: Project root directory for resolving relative paths.

        Returns:
            The computed hash string.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        full_path = project_root / self.file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Cannot hash: {full_path}")
        sha256 = hashlib.sha256(full_path.read_bytes()).hexdigest()
        self.file_hash = f"sha256:{sha256}"
        self.file_size_bytes = full_path.stat().st_size
        return self.file_hash

    def file_exists(self, project_root: Path) -> bool:
        """Check if the manifest file exists on disk."""
        return (project_root / self.file_path).exists()


class Manifest(BaseModel):
    """A data manifest tracking all files in a category."""

    manifest_version: str = Field(default="1.0.0")
    category: str = Field(description="Data category (context, structures, ligands)")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    entries: list[ManifestEntry] = Field(default_factory=list)

    def add_entry(self, entry: ManifestEntry) -> None:
        """Add an entry, replacing any existing entry with the same file_path."""
        self.entries = [e for e in self.entries if e.file_path != entry.file_path]
        self.entries.append(entry)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_entry(self, file_path: str) -> ManifestEntry | None:
        """Look up an entry by file path."""
        for entry in self.entries:
            if entry.file_path == file_path:
                return entry
        return None

    def files_by_status(self, status: str) -> list[ManifestEntry]:
        """Return all entries with a given status."""
        return [e for e in self.entries if e.status == status]

    def save(self, path: Path) -> None:
        """Save manifest to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        """Load manifest from a JSON file.

        Args:
            path: Path to the manifest JSON file.

        Returns:
            Loaded Manifest instance.

        Raises:
            FileNotFoundError: If manifest file does not exist.
        """
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")
        with open(path) as f:
            data = json.load(f)
        return cls.model_validate(data)

    def summary(self) -> dict[str, int]:
        """Return count of entries by status."""
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.status] = counts.get(entry.status, 0) + 1
        return counts

    def __len__(self) -> int:
        return len(self.entries)
