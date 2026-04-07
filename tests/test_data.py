"""Tests for the data layer: manifests, registry, paths, validation."""

import json
from pathlib import Path

import pytest

from statebind.data.manifest import Manifest, ManifestEntry
from statebind.data.paths import DataPaths
from statebind.data.registry import SourceRegistry, SourceSpec
from statebind.data.validation import validate_data_layout, ValidationReport

PROJECT_ROOT = Path(__file__).parent.parent


# ── ManifestEntry tests ─────────────────────────────────────────────────


class TestManifestEntry:
    def test_create_entry(self):
        entry = ManifestEntry(
            file_path="data/raw/context/test.tsv",
            description="Test file",
            source_name="test",
        )
        assert entry.status == "pending"
        assert entry.file_hash == ""

    def test_file_exists_false(self, tmp_path):
        entry = ManifestEntry(
            file_path="nonexistent.txt",
            description="Missing",
            source_name="test",
        )
        assert entry.file_exists(tmp_path) is False

    def test_file_exists_true(self, tmp_path):
        test_file = tmp_path / "data" / "test.txt"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("hello")
        entry = ManifestEntry(
            file_path="data/test.txt",
            description="Present",
            source_name="test",
        )
        assert entry.file_exists(tmp_path) is True

    def test_compute_hash(self, tmp_path):
        test_file = tmp_path / "data" / "test.txt"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("hello world")
        entry = ManifestEntry(
            file_path="data/test.txt",
            description="Hash test",
            source_name="test",
        )
        result = entry.compute_hash(tmp_path)
        assert result.startswith("sha256:")
        assert entry.file_hash == result
        assert entry.file_size_bytes > 0

    def test_compute_hash_missing(self, tmp_path):
        entry = ManifestEntry(
            file_path="missing.txt",
            description="Missing",
            source_name="test",
        )
        with pytest.raises(FileNotFoundError):
            entry.compute_hash(tmp_path)


# ── Manifest tests ──────────────────────────────────────────────────────


class TestManifest:
    def test_create_empty_manifest(self):
        m = Manifest(category="context")
        assert len(m) == 0
        assert m.category == "context"

    def test_add_entry(self):
        m = Manifest(category="context")
        entry = ManifestEntry(
            file_path="data/raw/context/test.tsv",
            description="Test",
            source_name="test",
        )
        m.add_entry(entry)
        assert len(m) == 1

    def test_add_entry_replaces_duplicate(self):
        m = Manifest(category="context")
        e1 = ManifestEntry(
            file_path="data/test.tsv",
            description="First",
            source_name="test",
        )
        e2 = ManifestEntry(
            file_path="data/test.tsv",
            description="Second",
            source_name="test",
        )
        m.add_entry(e1)
        m.add_entry(e2)
        assert len(m) == 1
        assert m.entries[0].description == "Second"

    def test_get_entry(self):
        m = Manifest(category="context")
        entry = ManifestEntry(
            file_path="data/test.tsv",
            description="Test",
            source_name="test",
        )
        m.add_entry(entry)
        found = m.get_entry("data/test.tsv")
        assert found is not None
        assert found.description == "Test"

    def test_get_entry_missing(self):
        m = Manifest(category="context")
        assert m.get_entry("nonexistent") is None

    def test_files_by_status(self):
        m = Manifest(category="context")
        m.add_entry(ManifestEntry(
            file_path="a.txt", description="A", source_name="t", status="pending",
        ))
        m.add_entry(ManifestEntry(
            file_path="b.txt", description="B", source_name="t", status="downloaded",
        ))
        m.add_entry(ManifestEntry(
            file_path="c.txt", description="C", source_name="t", status="pending",
        ))
        assert len(m.files_by_status("pending")) == 2
        assert len(m.files_by_status("downloaded")) == 1
        assert len(m.files_by_status("validated")) == 0

    def test_save_and_load(self, tmp_path):
        m = Manifest(category="structures")
        m.add_entry(ManifestEntry(
            file_path="data/raw/structures/test.pdb",
            description="Test PDB",
            source_name="pdb",
            format="pdb",
        ))
        save_path = tmp_path / "test_manifest.json"
        m.save(save_path)

        loaded = Manifest.load(save_path)
        assert len(loaded) == 1
        assert loaded.category == "structures"
        assert loaded.entries[0].source_name == "pdb"

    def test_load_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Manifest.load(tmp_path / "nonexistent.json")

    def test_summary(self):
        m = Manifest(category="context")
        m.add_entry(ManifestEntry(
            file_path="a.txt", description="A", source_name="t", status="pending",
        ))
        m.add_entry(ManifestEntry(
            file_path="b.txt", description="B", source_name="t", status="pending",
        ))
        m.add_entry(ManifestEntry(
            file_path="c.txt", description="C", source_name="t", status="downloaded",
        ))
        s = m.summary()
        assert s == {"pending": 2, "downloaded": 1}


# ── DataPaths tests ─────────────────────────────────────────────────────


class TestDataPaths:
    def test_paths_from_project_root(self):
        paths = DataPaths(PROJECT_ROOT)
        assert paths.data_dir == PROJECT_ROOT / "data"
        assert paths.raw_dir == PROJECT_ROOT / "data" / "raw"
        assert paths.processed_dir == PROJECT_ROOT / "data" / "processed"

    def test_category_dirs(self):
        paths = DataPaths(PROJECT_ROOT)
        assert paths.raw_context_dir == PROJECT_ROOT / "data" / "raw" / "context"
        assert paths.raw_structures_dir == PROJECT_ROOT / "data" / "raw" / "structures"
        assert paths.raw_ligands_dir == PROJECT_ROOT / "data" / "raw" / "ligands"

    def test_manifest_path(self):
        paths = DataPaths(PROJECT_ROOT)
        assert paths.manifest_path("context").name == "context.json"
        assert paths.manifest_path("structures").name == "structures.json"

    def test_ensure_all(self, tmp_path):
        paths = DataPaths(tmp_path)
        paths.ensure_all()
        for d in paths.all_expected_dirs():
            assert d.is_dir(), f"Directory not created: {d}"

    def test_all_expected_dirs(self):
        paths = DataPaths(PROJECT_ROOT)
        dirs = paths.all_expected_dirs()
        assert len(dirs) == 12  # data, manifests, raw, raw/3, processed, processed/3, docking/2

    def test_specific_file_paths(self):
        paths = DataPaths(PROJECT_ROOT)
        assert paths.mutation_atlas_path.name == "mutation_atlas.json"
        assert paths.state_atlas_path.name == "state_atlas.json"
        assert paths.reference_compounds_path.name == "reference_compounds.csv"


# ── SourceRegistry tests ────────────────────────────────────────────────


class TestSourceRegistry:
    def test_default_registry(self):
        registry = SourceRegistry.default()
        assert len(registry) > 0

    def test_default_registry_has_required_sources(self):
        registry = SourceRegistry.default()
        required = registry.required_specs()
        paths = [s.file_path for s in required]
        assert any("cosmic" in p for p in paths)
        assert any("clinvar" in p for p in paths)
        assert any("manual_curated" in p for p in paths)
        assert any("pdb_metadata" in p for p in paths)
        assert any("chembl" in p for p in paths)

    def test_get_specs_by_category(self):
        registry = SourceRegistry.default()
        context_specs = registry.get_specs_by_category("context")
        assert all("context" in s.file_path for s in context_specs)

    def test_build_manifest(self):
        registry = SourceRegistry.default()
        manifest = registry.build_manifest("context")
        assert manifest.category == "context"
        assert len(manifest) > 0
        assert all(e.status == "pending" for e in manifest.entries)

    def test_build_all_manifests(self):
        registry = SourceRegistry.default()
        manifests = registry.build_all_manifests()
        assert "context" in manifests
        assert "structures" in manifests
        assert "ligands" in manifests

    def test_add_replaces_existing(self):
        registry = SourceRegistry()
        registry.add(SourceSpec(
            file_path="test.txt", description="First", source_name="t",
        ))
        registry.add(SourceSpec(
            file_path="test.txt", description="Second", source_name="t",
        ))
        assert len(registry) == 1
        assert registry.specs[0].description == "Second"


# ── Validation tests ────────────────────────────────────────────────────


class TestValidation:
    def test_validate_project_layout(self):
        """Validate the actual project data layout."""
        report = validate_data_layout(PROJECT_ROOT)
        # Directories should exist (we created them)
        dir_errors = [i for i in report.errors if i.category == "directory"]
        assert len(dir_errors) == 0, f"Missing directories: {dir_errors}"

    def test_validate_empty_project(self, tmp_path):
        """An empty directory should produce errors."""
        report = validate_data_layout(tmp_path)
        assert len(report.errors) > 0
        assert not report.is_valid

    def test_validate_with_manifests(self, tmp_path):
        """A properly set up project should validate."""
        paths = DataPaths(tmp_path)
        paths.ensure_all()

        # Create a simple manifest
        m = Manifest(category="context")
        m.add_entry(ManifestEntry(
            file_path="data/raw/context/test.json",
            description="Test",
            source_name="test",
            status="pending",
        ))
        m.save(paths.manifest_path("context"))

        report = validate_data_layout(tmp_path)
        # No directory errors
        dir_errors = [i for i in report.errors if i.category == "directory"]
        assert len(dir_errors) == 0

    def test_validation_report_summary(self):
        report = ValidationReport()
        report.add("error", "directory", "Missing dir")
        report.add("warning", "manifest", "Missing manifest")
        summary = report.summary()
        assert "FAIL" in summary
        assert "Errors:   1" in summary
        assert "Warnings: 1" in summary

    def test_validation_catches_missing_file_with_downloaded_status(self, tmp_path):
        """If manifest says 'downloaded' but file is missing, should error."""
        paths = DataPaths(tmp_path)
        paths.ensure_all()

        m = Manifest(category="context")
        m.add_entry(ManifestEntry(
            file_path="data/raw/context/missing.json",
            description="Missing file",
            source_name="test",
            status="downloaded",  # Claims downloaded but file doesn't exist
        ))
        m.save(paths.manifest_path("context"))

        report = validate_data_layout(tmp_path)
        file_errors = [i for i in report.errors if i.category == "file"]
        assert len(file_errors) == 1
