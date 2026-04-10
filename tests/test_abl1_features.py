"""Tests for ABL1 structural features, pocket conditions, and atlas.

Verifies:
- ABL1 curated features are present and physically reasonable
- ABL1 pocket conditions defined for each conformational state
- ABL1 state atlas builds correctly
- ABL1 docking config has correct state-representative mappings
- Feature separation between DFGin and DFGout
- No regressions in EGFR features
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from statebind.processing.models import ConformationalState
from statebind.structure.features import (
    extract_features,
    get_available_pdb_ids,
)
from statebind.structure.models import (
    PocketDescriptor,
    StateAtlas,
    StructuralFeatures,
)
from statebind.generation.conditioning import (
    PocketCondition,
    get_pocket_conditions,
    select_strategies_for_pocket,
)
from statebind.generation.models import GenerationStrategy


PROJECT_ROOT = Path(__file__).parent.parent

# ABL1 PDB IDs that must have curated features
ABL1_PDB_IDS = ["1iep", "2gqg", "2g1t", "3cs9", "3pyy"]

# State classification for each ABL1 PDB (KLIFS-verified)
ABL1_STATE_MAP = {
    "2gqg": "DFGin_aCin",
    "2g1t": "DFGin_aCout",
    "1iep": "DFGout_aCin",
    "3cs9": "DFGout_aCin",
    "3pyy": "DFGout_aCin",
}


# ── ABL1 Curated Features Tests ───────────────────────────────────────


class TestABL1FeaturesPresent:
    """Verify all ABL1 structures have curated features."""

    @pytest.mark.parametrize("pdb_id", ABL1_PDB_IDS)
    def test_abl1_features_exist(self, pdb_id: str):
        feats, pocket = extract_features(pdb_id)
        assert isinstance(feats, StructuralFeatures)
        assert isinstance(pocket, PocketDescriptor)

    def test_abl1_pdb_ids_in_available(self):
        available = get_available_pdb_ids()
        for pdb_id in ABL1_PDB_IDS:
            assert pdb_id in available, f"{pdb_id} not in available PDB IDs"

    def test_abl1_pdb_ids_filtered(self):
        abl1_ids = get_available_pdb_ids(target_gene="ABL1")
        assert len(abl1_ids) == len(ABL1_PDB_IDS)
        for pdb_id in ABL1_PDB_IDS:
            assert pdb_id in abl1_ids

    def test_egfr_pdb_ids_filtered(self):
        egfr_ids = get_available_pdb_ids(target_gene="EGFR")
        assert "1m17" in egfr_ids
        # ABL1 IDs should NOT be in EGFR list
        for pdb_id in ABL1_PDB_IDS:
            assert pdb_id not in egfr_ids

    def test_all_pdb_ids_include_both(self):
        all_ids = get_available_pdb_ids()
        # Must include both EGFR and ABL1
        assert "1m17" in all_ids  # EGFR
        assert "1iep" in all_ids  # ABL1


class TestABL1FeatureValues:
    """Verify ABL1 feature values are physically reasonable."""

    def test_dfg_distance_positive(self):
        for pdb_id in ABL1_PDB_IDS:
            feats, _ = extract_features(pdb_id)
            assert feats.dfg_asp_phe_dist > 0

    def test_pocket_volume_positive(self):
        for pdb_id in ABL1_PDB_IDS:
            _, pocket = extract_features(pdb_id)
            assert pocket.pocket_volume > 0

    def test_dfgin_has_short_dfg_distance(self):
        """DFGin structures should have Asp-Phe distance < 7 Å."""
        for pdb_id in ["2gqg", "2g1t"]:
            feats, _ = extract_features(pdb_id)
            assert feats.dfg_asp_phe_dist < 7.0, (
                f"{pdb_id}: DFGin should have short Asp-Phe dist, "
                f"got {feats.dfg_asp_phe_dist}"
            )

    def test_dfgout_has_long_dfg_distance(self):
        """DFGout structures should have Asp-Phe distance > 9 Å."""
        for pdb_id in ["1iep", "3cs9", "3pyy"]:
            feats, _ = extract_features(pdb_id)
            assert feats.dfg_asp_phe_dist > 9.0, (
                f"{pdb_id}: DFGout should have long Asp-Phe dist, "
                f"got {feats.dfg_asp_phe_dist}"
            )

    def test_acin_has_intact_salt_bridge(self):
        """aCin structures should have K271-E286 salt bridge < 4 Å."""
        for pdb_id in ["2gqg", "1iep", "3cs9", "3pyy"]:
            feats, _ = extract_features(pdb_id)
            assert feats.ac_helix_salt_bridge < 4.0, (
                f"{pdb_id}: aCin should have intact salt bridge, "
                f"got {feats.ac_helix_salt_bridge}"
            )

    def test_acout_has_broken_salt_bridge(self):
        """aCout (2G1T) should have broken K271-E286 salt bridge > 8 Å."""
        feats, _ = extract_features("2g1t")
        assert feats.ac_helix_salt_bridge > 8.0, (
            f"2G1T: aCout should have broken salt bridge, "
            f"got {feats.ac_helix_salt_bridge}"
        )

    def test_back_pocket_only_in_dfgout(self):
        """Back pocket should be accessible only in DFGout structures."""
        for pdb_id in ["2gqg", "2g1t"]:
            _, pocket = extract_features(pdb_id)
            assert not pocket.back_pocket_accessible, (
                f"{pdb_id}: DFGin should not have back pocket accessible"
            )
        for pdb_id in ["1iep", "3cs9", "3pyy"]:
            _, pocket = extract_features(pdb_id)
            assert pocket.back_pocket_accessible, (
                f"{pdb_id}: DFGout should have back pocket accessible"
            )

    def test_abl1_lacks_covalent_cys(self):
        """ABL1 lacks the C797 equivalent, so covalent_cys_exposed should be False."""
        for pdb_id in ABL1_PDB_IDS:
            _, pocket = extract_features(pdb_id)
            assert not pocket.covalent_cys_exposed, (
                f"{pdb_id}: ABL1 should not have covalent Cys exposed"
            )

    def test_dfgout_larger_pocket_than_dfgin(self):
        """DFGout pocket volume should be > DFGin by at least 200 Å³."""
        _, pocket_in = extract_features("2gqg")    # DFGin_aCin
        _, pocket_out = extract_features("1iep")    # DFGout_aCin
        assert pocket_out.pocket_volume > pocket_in.pocket_volume + 200, (
            f"DFGout pocket ({pocket_out.pocket_volume}) should be "
            f"at least 200 Å³ larger than DFGin ({pocket_in.pocket_volume})"
        )


class TestABL1FeaturesSeparateStates:
    """Verify features actually discriminate between ABL1 conformational states."""

    def test_dfg_distance_separates_in_out(self):
        feats_in, _ = extract_features("2gqg")   # DFGin_aCin
        feats_out, _ = extract_features("1iep")   # DFGout_aCin
        gap = feats_out.dfg_asp_phe_dist - feats_in.dfg_asp_phe_dist
        assert gap > 4.0, f"DFG distance gap should be > 4 Å, got {gap}"

    def test_salt_bridge_separates_acin_acout(self):
        feats_in, _ = extract_features("2gqg")   # aCin
        feats_out, _ = extract_features("2g1t")   # aCout
        gap = feats_out.ac_helix_salt_bridge - feats_in.ac_helix_salt_bridge
        assert gap > 5.0, f"Salt bridge gap should be > 5 Å, got {gap}"

    def test_ac_rotation_separates_in_out(self):
        feats_in, _ = extract_features("2gqg")   # aCin
        feats_out, _ = extract_features("2g1t")   # aCout
        assert feats_out.ac_helix_rotation > feats_in.ac_helix_rotation + 10, (
            f"αC rotation gap should be > 10°"
        )


# ── ABL1 Pocket Conditions Tests ──────────────────────────────────────


class TestABL1PocketConditions:
    """Verify ABL1 pocket conditions are defined for each state."""

    def test_abl1_conditions_have_3_states(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        assert len(conditions) == 3, f"Expected 3 ABL1 states, got {len(conditions)}"

    def test_abl1_dfgin_acin_defined(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        key = ConformationalState.DFGIN_ACIN.value
        assert key in conditions
        cond = conditions[key]
        assert isinstance(cond, PocketCondition)
        assert cond.representative_pdb == "2gqg"

    def test_abl1_dfgin_acout_defined(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        key = ConformationalState.DFGIN_ACOUT.value
        assert key in conditions
        cond = conditions[key]
        assert cond.representative_pdb == "2g1t"

    def test_abl1_dfgout_acin_defined(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        key = ConformationalState.DFGOUT_ACIN.value
        assert key in conditions
        cond = conditions[key]
        assert cond.representative_pdb == "1iep"

    def test_abl1_dfgout_has_back_pocket_strategy(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        key = ConformationalState.DFGOUT_ACIN.value
        cond = conditions[key]
        strategies = cond.strategies
        assert GenerationStrategy.BACK_POCKET_EXTENSION in strategies

    def test_abl1_dfgin_has_hinge_strategy(self):
        conditions = get_pocket_conditions(target_gene="ABL1")
        key = ConformationalState.DFGIN_ACIN.value
        cond = conditions[key]
        assert GenerationStrategy.HINGE_OPTIMIZED in cond.strategies

    def test_abl1_no_covalent_warhead_strategy(self):
        """ABL1 lacks C797 equivalent -> no covalent warhead strategy."""
        conditions = get_pocket_conditions(target_gene="ABL1")
        for key, cond in conditions.items():
            assert GenerationStrategy.COVALENT_WARHEAD not in cond.strategies, (
                f"ABL1 state {key} should not have COVALENT_WARHEAD strategy"
            )

    def test_egfr_conditions_still_work(self):
        """Backward compat: EGFR conditions unchanged."""
        conditions = get_pocket_conditions(target_gene="EGFR")
        assert len(conditions) == 3
        assert ConformationalState.DFGIN_ACIN.value in conditions

    def test_default_is_egfr(self):
        """Default target_gene should be EGFR."""
        conditions = get_pocket_conditions()
        assert conditions[ConformationalState.DFGIN_ACIN.value].representative_pdb == "1m17"

    def test_select_strategies_for_abl1_dfgout_pocket(self):
        """Dynamic strategy selection should work with ABL1 DFGout pocket."""
        conditions = get_pocket_conditions(target_gene="ABL1")
        pocket = conditions[ConformationalState.DFGOUT_ACIN.value].pocket
        strategies = select_strategies_for_pocket(pocket)
        assert GenerationStrategy.BACK_POCKET_EXTENSION in strategies
        assert GenerationStrategy.VOLUME_FILLING in strategies
        # ABL1 pocket has covalent_cys_exposed=False, so no covalent
        assert GenerationStrategy.COVALENT_WARHEAD not in strategies


# ── ABL1 Docking Config Tests ─────────────────────────────────────────


class TestABL1DockingConfig:
    """Verify ABL1 docking config file."""

    @pytest.fixture
    def config(self):
        config_path = PROJECT_ROOT / "configs" / "docking_abl1.yaml"
        assert config_path.exists(), "configs/docking_abl1.yaml not found"
        with open(config_path) as f:
            return yaml.safe_load(f)

    def test_config_has_gnina_section(self, config):
        assert "gnina" in config
        assert config["gnina"]["exhaustiveness"] == 8
        assert config["gnina"]["num_modes"] == 5

    def test_config_has_states(self, config):
        assert "states" in config
        reps = config["states"]["representatives"]
        assert reps["DFGin_aCin"] == "2gqg"
        assert reps["DFGin_aCout"] == "2g1t"
        assert reps["DFGout_aCin"] == "1iep"

    def test_config_has_target_section(self, config):
        assert "target" in config
        assert config["target"]["gene"] == "ABL1"

    def test_config_matches_egfr_params(self, config):
        """ABL1 docking params should match EGFR defaults."""
        egfr_path = PROJECT_ROOT / "configs" / "docking.yaml"
        with open(egfr_path) as f:
            egfr = yaml.safe_load(f)
        assert config["gnina"]["exhaustiveness"] == egfr["gnina"]["exhaustiveness"]
        assert config["gnina"]["num_modes"] == egfr["gnina"]["num_modes"]
        assert config["gnina"]["cnn_scoring"] == egfr["gnina"]["cnn_scoring"]


# ── ABL1 State Atlas Tests ────────────────────────────────────────────


_has_sklearn = False
try:
    import sklearn  # noqa: F401
    _has_sklearn = True
except ImportError:
    pass


@pytest.mark.skipif(not _has_sklearn, reason="scikit-learn not installed")
class TestABL1StateAtlas:
    """Verify build_state_atlas works for ABL1."""

    def test_build_abl1_atlas_returns_atlas(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        assert isinstance(atlas, StateAtlas)
        assert atlas.target_gene == "ABL1"

    def test_abl1_atlas_has_structures(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        assert atlas.n_structures == 5  # 5 ABL1 structures with features

    def test_abl1_atlas_default_3_clusters(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        assert atlas.n_clusters == 3

    def test_abl1_atlas_has_3_states(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        states = {e.state_label for e in atlas.entries}
        assert len(states) == 3
        assert ConformationalState.DFGIN_ACIN in states
        assert ConformationalState.DFGIN_ACOUT in states
        assert ConformationalState.DFGOUT_ACIN in states

    def test_abl1_atlas_entries_have_features(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        for e in atlas.entries:
            assert e.features.dfg_asp_phe_dist > 0
            assert e.pocket.pocket_volume > 0
            assert e.cluster_id >= 0

    def test_abl1_atlas_pairwise_distances(self):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1")
        n = atlas.n_structures
        expected_pairs = n * (n - 1) // 2
        assert len(atlas.pairwise_similarities) == expected_pairs

    def test_egfr_atlas_still_works(self):
        """Backward compat: EGFR atlas unchanged."""
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="EGFR", n_clusters=4)
        assert isinstance(atlas, StateAtlas)
        assert atlas.target_gene == "EGFR"
        assert atlas.n_structures > 0

    def test_default_target_is_egfr(self):
        """Default target_gene should be EGFR with 4 clusters."""
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas()
        assert atlas.target_gene == "EGFR"
        assert atlas.n_clusters == 4

    def test_abl1_atlas_serialization(self, tmp_path):
        from statebind.structure.atlas import build_state_atlas
        atlas = build_state_atlas(target_gene="ABL1", output_dir=tmp_path)
        expected = [
            "state_atlas.json", "atlas_table.csv",
            "clusters.json", "pocket_comparison.json",
        ]
        for fname in expected:
            assert (tmp_path / fname).exists(), f"Missing: {fname}"


# ── EGFR Regression Tests ─────────────────────────────────────────────


class TestEGFRRegression:
    """Verify EGFR features are not broken by ABL1 additions."""

    def test_egfr_1m17_features_unchanged(self):
        feats, pocket = extract_features("1m17")
        assert feats.dfg_asp_phe_dist == 5.2
        assert pocket.pocket_volume == 450.0

    def test_egfr_2gs7_features_unchanged(self):
        feats, pocket = extract_features("2gs7")
        assert feats.ac_helix_salt_bridge == 9.2
        assert pocket.pocket_volume == 520.0

    def test_egfr_3w2r_features_unchanged(self):
        feats, pocket = extract_features("3w2r")
        assert feats.dfg_asp_phe_dist == 10.5
        assert pocket.back_pocket_accessible is True
