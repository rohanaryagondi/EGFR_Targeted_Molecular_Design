"""Test project structure, conventions, and structural atlas modules."""

from pathlib import Path

import pytest
import numpy as np

from statebind.processing.models import ConformationalState
from statebind.structure.models import (
    AtlasEntry,
    PocketDescriptor,
    StateAtlas,
    StateCluster,
    StructuralFeatures,
    PairwiseSimilarity,
)
from statebind.structure.features import extract_features, get_available_pdb_ids
from statebind.structure.clustering import (
    cluster_structures,
    compute_cluster_quality,
    compute_pairwise_distances,
)
from statebind.structure.pocket_comparison import (
    compare_pockets_by_state,
    identify_pocket_differences,
)
from statebind.structure.atlas import build_state_atlas


PROJECT_ROOT = Path(__file__).parent.parent


# ── Project Structure Tests ─────────────────────────────────────────────


def test_src_layout_exists():
    assert (PROJECT_ROOT / "src" / "statebind").is_dir()


def test_all_modules_have_init():
    modules = ["context", "structure", "dynamics", "generation", "ranking", "utils", "data", "processing", "baselines"]
    for module in modules:
        init_file = PROJECT_ROOT / "src" / "statebind" / module / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {module}"


def test_configs_exist():
    assert (PROJECT_ROOT / "configs").is_dir()
    assert (PROJECT_ROOT / "configs" / "default.yaml").exists()


def test_docs_exist():
    expected_docs = [
        "PROJECT_CHARTER.md",
        "ARCHITECTURE.md",
        "PHASE_PLAN.md",
        "DECISIONS.md",
        "RUNBOOK.md",
        "BENCHMARK_SPEC.md",
        "RISK_REGISTER.md",
        "GITHUB_STORY.md",
        "DATA_SOURCES.md",
        "DATA_SCHEMA.md",
        "BENCHMARK_DATASET_CARD.md",
        "STATIC_BASELINE.md",
        "STATE_ATLAS.md",
    ]
    for doc in expected_docs:
        assert (PROJECT_ROOT / "docs" / doc).exists(), f"Missing doc: {doc}"


def test_artifacts_dir_exists():
    assert (PROJECT_ROOT / "artifacts").is_dir()


def test_reports_dir_exists():
    assert (PROJECT_ROOT / "reports").is_dir()


def test_pyproject_toml_exists():
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_data_directories_exist():
    expected = [
        "data",
        "data/manifests",
        "data/raw",
        "data/raw/context",
        "data/raw/structures",
        "data/raw/ligands",
        "data/processed",
        "data/processed/context",
        "data/processed/structures",
        "data/processed/ligands",
    ]
    for d in expected:
        assert (PROJECT_ROOT / d).is_dir(), f"Missing data directory: {d}"


# ── Structural Features Tests ───────────────────────────────────────────


class TestStructuralFeatures:
    def test_feature_vector_length(self):
        feats = StructuralFeatures(
            dfg_asp_phe_dist=5.2, dfg_phe_position=0.5,
            ac_helix_salt_bridge=2.9, ac_helix_rotation=2.0,
            p_loop_displacement=0.0, hinge_angle=155.0,
            activation_loop_rmsd=0.0, gatekeeper_sidechain=-65.0,
            pocket_volume=450.0,
        )
        vec = feats.to_vector()
        assert len(vec) == 9
        assert len(vec) == len(StructuralFeatures.feature_names())

    def test_feature_names_match_vector(self):
        names = StructuralFeatures.feature_names()
        assert "dfg_asp_phe_dist" in names
        assert "pocket_volume" in names
        assert len(names) == 9

    def test_extract_features_known_pdb(self):
        feats, pocket = extract_features("1m17")
        assert isinstance(feats, StructuralFeatures)
        assert isinstance(pocket, PocketDescriptor)
        assert feats.dfg_asp_phe_dist > 0
        assert pocket.pocket_volume > 0

    def test_extract_features_unknown_pdb(self):
        with pytest.raises(KeyError):
            extract_features("xxxx")

    def test_available_pdb_ids(self):
        ids = get_available_pdb_ids()
        assert len(ids) >= 10
        assert "1m17" in ids
        assert "4zau" in ids


class TestFeatureDistinguishesStates:
    """Test that features actually separate conformational states."""

    def test_dfg_distance_separates_in_out(self):
        feats_in, _ = extract_features("1m17")   # DFGin
        feats_out, _ = extract_features("3iku")   # DFGout
        assert feats_in.dfg_asp_phe_dist < 7.0, "DFGin should have short Asp-Phe dist"
        assert feats_out.dfg_asp_phe_dist > 9.0, "DFGout should have long Asp-Phe dist"

    def test_ac_helix_separates_in_out(self):
        feats_in, _ = extract_features("1m17")   # aCin
        feats_out, _ = extract_features("2gs7")   # aCout
        assert feats_in.ac_helix_salt_bridge < 4.0, "aCin should have intact salt bridge"
        assert feats_out.ac_helix_salt_bridge > 8.0, "aCout should have broken salt bridge"

    def test_pocket_volume_increases_with_dfg_out(self):
        _, pocket_in = extract_features("1m17")    # DFGin
        _, pocket_out = extract_features("3iku")    # DFGout
        assert pocket_out.pocket_volume > pocket_in.pocket_volume + 200

    def test_back_pocket_only_in_dfg_out(self):
        _, pocket_in = extract_features("1m17")
        _, pocket_out = extract_features("3iku")
        assert not pocket_in.back_pocket_accessible
        assert pocket_out.back_pocket_accessible

    def test_gatekeeper_changes_with_t790m(self):
        feats_wt, _ = extract_features("1m17")   # WT
        feats_mut, _ = extract_features("2jit")   # T790M
        assert abs(feats_wt.gatekeeper_sidechain - feats_mut.gatekeeper_sidechain) > 50


# ── Clustering Tests ────────────────────────────────────────────────────


class TestClustering:
    def _build_entries(self) -> list[AtlasEntry]:
        from statebind.processing.structures import build_structure_dataset
        available = set(get_available_pdb_ids())
        entries = []
        for s in build_structure_dataset().structures:
            if s.pdb_id in available:
                feats, pocket = extract_features(s.pdb_id)
                entries.append(AtlasEntry(
                    pdb_id=s.pdb_id, state_label=s.state,
                    resolution=s.resolution,
                    mutations_present=s.mutations_present,
                    ligand_id=s.ligand_id, ligand_bound=s.ligand_bound,
                    is_apo=s.is_apo, is_representative=s.is_representative,
                    features=feats, pocket=pocket,
                ))
        return entries

    def test_cluster_produces_4_clusters(self):
        entries = self._build_entries()
        entries, clusters = cluster_structures(entries, n_clusters=4)
        assert len(clusters) == 4
        assert all(e.cluster_id >= 0 for e in entries)

    def test_cluster_labels_agree_with_states(self):
        entries = self._build_entries()
        entries, clusters = cluster_structures(entries, n_clusters=4)
        quality = compute_cluster_quality(entries)
        assert quality["label_agreement"] > 0.8, \
            f"Label agreement {quality['label_agreement']:.1%} too low"

    def test_separation_ratio_reasonable(self):
        entries = self._build_entries()
        entries, clusters = cluster_structures(entries, n_clusters=4)
        quality = compute_cluster_quality(entries)
        assert quality["separation_ratio"] > 1.5, \
            f"Separation ratio {quality['separation_ratio']:.2f} too low"

    def test_pairwise_distances_computed(self):
        entries = self._build_entries()
        entries, _ = cluster_structures(entries, n_clusters=4)
        pairwise = compute_pairwise_distances(entries)
        n = len(entries)
        expected_pairs = n * (n - 1) // 2
        assert len(pairwise) == expected_pairs

    def test_same_state_closer_than_different(self):
        entries = self._build_entries()
        entries, _ = cluster_structures(entries, n_clusters=4)
        pairwise = compute_pairwise_distances(entries)
        same = [p.feature_distance for p in pairwise if p.state_a == p.state_b]
        diff = [p.feature_distance for p in pairwise if p.state_a != p.state_b]
        if same and diff:
            mean_same = sum(same) / len(same)
            mean_diff = sum(diff) / len(diff)
            assert mean_same < mean_diff, \
                f"Same-state mean {mean_same:.2f} >= different-state {mean_diff:.2f}"


# ── Pocket Comparison Tests ─────────────────────────────────────────────


class TestPocketComparison:
    def _build_entries(self):
        from statebind.processing.structures import build_structure_dataset
        available = set(get_available_pdb_ids())
        entries = []
        for s in build_structure_dataset().structures:
            if s.pdb_id in available:
                feats, pocket = extract_features(s.pdb_id)
                entries.append(AtlasEntry(
                    pdb_id=s.pdb_id, state_label=s.state,
                    features=feats, pocket=pocket,
                    is_representative=s.is_representative,
                ))
        return entries

    def test_comparison_covers_all_states(self):
        entries = self._build_entries()
        comp = compare_pockets_by_state(entries)
        assert len(comp) >= 4

    def test_volume_increases_in_to_out(self):
        entries = self._build_entries()
        comp = compare_pockets_by_state(entries)
        active = comp.get("DFGin_aCin", {})
        inactive = comp.get("DFGout_aCout", {})
        if active and inactive:
            assert inactive["mean_volume"] > active["mean_volume"]

    def test_pocket_differences_found(self):
        entries = self._build_entries()
        comp = compare_pockets_by_state(entries)
        diffs = identify_pocket_differences(comp)
        assert len(diffs) >= 2
        features_found = {d["feature"] for d in diffs}
        assert "pocket_volume" in features_found


# ── Atlas Builder Tests ─────────────────────────────────────────────────


class TestStateAtlas:
    def test_build_atlas_returns_atlas(self):
        atlas = build_state_atlas(n_clusters=4)
        assert isinstance(atlas, StateAtlas)
        assert atlas.n_structures > 0
        assert atlas.n_clusters == 4

    def test_atlas_has_all_components(self):
        atlas = build_state_atlas(n_clusters=4)
        assert len(atlas.entries) > 0
        assert len(atlas.clusters) == 4
        assert len(atlas.pairwise_similarities) > 0
        assert len(atlas.feature_names) == 9

    def test_atlas_serialization_roundtrip(self, tmp_path):
        atlas = build_state_atlas(n_clusters=4, output_dir=tmp_path)
        expected = [
            "state_atlas.json", "atlas_table.csv",
            "clusters.json", "pocket_comparison.json",
            "pocket_differences.json", "clustering_quality.json",
            "pairwise_distances.csv",
        ]
        for fname in expected:
            assert (tmp_path / fname).exists(), f"Missing: {fname}"

    def test_atlas_entries_have_features(self):
        atlas = build_state_atlas(n_clusters=4)
        for e in atlas.entries:
            assert e.features.dfg_asp_phe_dist > 0
            assert e.pocket.pocket_volume > 0
            assert e.cluster_id >= 0

    def test_atlas_csv_not_empty(self, tmp_path):
        build_state_atlas(n_clusters=4, output_dir=tmp_path)
        csv_path = tmp_path / "atlas_table.csv"
        lines = csv_path.read_text().strip().split("\n")
        assert len(lines) >= 2
