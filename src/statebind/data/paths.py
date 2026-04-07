"""Centralized path resolution for the data layer.

All data paths flow through this module. No other module should construct
data paths manually.
"""

from pathlib import Path


class DataPaths:
    """Resolve all data-related paths relative to a project root.

    Args:
        project_root: Root directory of the StateBind project.
            Defaults to auto-detection by walking up from this file.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            # Walk up from src/statebind/data/paths.py → project root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.root = Path(project_root).resolve()

    # ── Top-level data directories ──────────────────────────────────────

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def manifests_dir(self) -> Path:
        return self.root / "data" / "manifests"

    @property
    def raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    # ── Raw data subdirectories ─────────────────────────────────────────

    @property
    def raw_context_dir(self) -> Path:
        return self.raw_dir / "context"

    @property
    def raw_structures_dir(self) -> Path:
        return self.raw_dir / "structures"

    @property
    def raw_ligands_dir(self) -> Path:
        return self.raw_dir / "ligands"

    # ── Processed data subdirectories ───────────────────────────────────

    @property
    def processed_context_dir(self) -> Path:
        return self.processed_dir / "context"

    @property
    def processed_structures_dir(self) -> Path:
        return self.processed_dir / "structures"

    @property
    def processed_ligands_dir(self) -> Path:
        return self.processed_dir / "ligands"

    @property
    def docking_receptors_dir(self) -> Path:
        return self.processed_dir / "docking" / "receptors"

    @property
    def docking_results_dir(self) -> Path:
        return self.root / "artifacts" / "docking"

    # ── Specific file paths ─────────────────────────────────────────────

    @property
    def mutation_atlas_path(self) -> Path:
        return self.processed_context_dir / "mutation_atlas.json"

    @property
    def state_atlas_path(self) -> Path:
        return self.processed_structures_dir / "state_atlas.json"

    @property
    def reference_compounds_path(self) -> Path:
        return self.processed_ligands_dir / "reference_compounds.csv"

    # ── Manifest file paths ─────────────────────────────────────────────

    def manifest_path(self, category: str) -> Path:
        """Return the manifest file path for a given category.

        Args:
            category: One of 'context', 'structures', 'ligands'.
        """
        return self.manifests_dir / f"{category}.json"

    # ── Directory creation ──────────────────────────────────────────────

    def ensure_all(self) -> None:
        """Create all data directories if they don't exist."""
        dirs = [
            self.manifests_dir,
            self.raw_context_dir,
            self.raw_structures_dir,
            self.raw_ligands_dir,
            self.processed_context_dir,
            self.processed_structures_dir,
            self.processed_ligands_dir,
            self.docking_receptors_dir,
            self.docking_results_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # ── Introspection ───────────────────────────────────────────────────

    def all_expected_dirs(self) -> list[Path]:
        """Return all directories that should exist in a valid data layout."""
        return [
            self.data_dir,
            self.manifests_dir,
            self.raw_dir,
            self.raw_context_dir,
            self.raw_structures_dir,
            self.raw_ligands_dir,
            self.processed_dir,
            self.processed_context_dir,
            self.processed_structures_dir,
            self.processed_ligands_dir,
            self.docking_receptors_dir,
            self.docking_results_dir,
        ]

    def __repr__(self) -> str:
        return f"DataPaths(root={self.root})"
