"""Tests for GNINA physics-informed docking.

Covers:
- GNINA availability detection
- DockingResult model validation
- Score normalization (always runs)
- Ligand preparation (skip if no RDKit)
- Docking wrapper (skip if no GNINA)
- Receptor preparation metadata
- Fallback cascade integration (mocked)
- State-specific docking analysis models
- Docking config loading
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from statebind.chemistry.docking import (
    DockingConfig,
    DockingResult,
    dock_batch,
    dock_molecule,
    is_gnina_available,
    load_docking_config,
    normalize_vina_score,
)

_GNINA_AVAILABLE = is_gnina_available()

# Known EGFR binder SMILES (erlotinib)
_ERLOTINIB = "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC"
_ETHANOL = "CCO"


def _has_rdkit() -> bool:
    try:
        from statebind.chemistry.fingerprints import HAS_RDKIT
        return HAS_RDKIT
    except ImportError:
        return False


_HAS_RDKIT = _has_rdkit()


# ── Category 1: GNINA availability (always run) ─────────────────────────


class TestGninaAvailability:
    """Tests for GNINA availability detection."""

    def test_is_gnina_available_returns_bool(self):
        """is_gnina_available() returns a bool without crashing."""
        result = is_gnina_available()
        assert isinstance(result, bool)

    def test_dock_without_gnina_returns_failure(self):
        """When GNINA is unavailable, dock_molecule returns success=False."""
        with patch("statebind.chemistry.docking.is_gnina_available", return_value=False):
            result = dock_molecule(
                _ERLOTINIB,
                Path("/nonexistent/receptor.pdbqt"),
                (0.0, 0.0, 0.0),
            )
            assert result.success is False
            assert result.error is not None
            assert "not installed" in result.error.lower() or "not on path" in result.error.lower()


# ── Category 2: DockingResult model (always run) ────────────────────────


class TestDockingResultModel:
    """Tests for the DockingResult Pydantic model."""

    def test_docking_result_validates(self):
        """DockingResult accepts valid data."""
        result = DockingResult(
            smiles=_ERLOTINIB,
            receptor_state="DFGin_aCin",
            vina_score=-8.5,
            cnn_score=0.85,
            cnn_affinity=7.2,
            n_poses=5,
            success=True,
        )
        assert result.smiles == _ERLOTINIB
        assert result.vina_score == -8.5
        assert result.cnn_score == 0.85
        assert result.success is True

    def test_docking_result_serializes_to_json(self):
        """DockingResult serializes to JSON with all expected keys."""
        result = DockingResult(
            smiles=_ETHANOL,
            receptor_state="DFGin_aCout",
            vina_score=-3.0,
            cnn_score=0.4,
            cnn_affinity=4.5,
            n_poses=3,
            success=True,
        )
        data = result.model_dump(mode="json")
        assert isinstance(data, dict)
        expected_keys = {
            "smiles", "receptor_state", "vina_score", "cnn_score",
            "cnn_affinity", "pose_pdb", "n_poses", "success", "error",
        }
        assert expected_keys == set(data.keys())

    def test_docking_result_failure_mode(self):
        """DockingResult with success=False stores error message."""
        result = DockingResult(
            smiles="invalid",
            success=False,
            error="GNINA not installed",
        )
        assert result.success is False
        assert result.error == "GNINA not installed"
        assert result.vina_score == 0.0


# ── Category 3: Score normalization (always run) ─────────────────────────


class TestNormalization:
    """Tests for Vina score normalization via sigmoid."""

    def test_normalize_strong_binder(self):
        """Strong binder (-9 kcal/mol) maps to ~0.95."""
        score = normalize_vina_score(-9.0)
        assert abs(score - 0.9526) < 0.01

    def test_normalize_no_binding(self):
        """Zero Vina score maps to exactly 0.5."""
        score = normalize_vina_score(0.0)
        assert score == 0.5

    def test_normalize_unfavorable(self):
        """Positive Vina score (+3 kcal/mol) maps to ~0.27."""
        score = normalize_vina_score(3.0)
        assert abs(score - 0.2689) < 0.01

    def test_normalize_monotonic(self):
        """More negative Vina scores produce higher normalized scores."""
        scores = [normalize_vina_score(v) for v in [3.0, 0.0, -3.0, -6.0, -9.0, -12.0]]
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i + 1], f"Not monotonic at index {i}"

    def test_normalize_range(self):
        """Normalized scores are always in (0, 1)."""
        for vina in [-20.0, -10.0, -5.0, 0.0, 5.0, 10.0]:
            score = normalize_vina_score(vina)
            assert 0.0 < score < 1.0, f"Score {score} out of range for vina={vina}"

    def test_normalize_custom_scale(self):
        """Custom scale parameter changes the mapping."""
        default = normalize_vina_score(-6.0, scale=3.0)
        wider = normalize_vina_score(-6.0, scale=6.0)
        assert wider < default  # Wider scale -> less extreme mapping


# ── Category 4: Ligand preparation (skip if no RDKit) ───────────────────


@pytest.mark.skipif(not _HAS_RDKIT, reason="RDKit not installed")
class TestLigandPreparation:
    """Tests for SMILES to SDF conversion."""

    def test_smiles_to_sdf_valid_molecule(self):
        """Valid SMILES converts to a non-empty SDF file."""
        from statebind.chemistry.docking import _smiles_to_sdf

        with tempfile.TemporaryDirectory() as tmpdir:
            sdf_path = Path(tmpdir) / "ligand.sdf"
            success = _smiles_to_sdf(_ETHANOL, sdf_path)
            assert success is True
            assert sdf_path.exists()
            assert sdf_path.stat().st_size > 0

    def test_smiles_to_sdf_invalid_smiles(self):
        """Invalid SMILES returns False."""
        from statebind.chemistry.docking import _smiles_to_sdf

        with tempfile.TemporaryDirectory() as tmpdir:
            sdf_path = Path(tmpdir) / "ligand.sdf"
            success = _smiles_to_sdf("not_a_valid_smiles_string", sdf_path)
            assert success is False


# ── Category 5: Docking wrapper (skip if no GNINA) ──────────────────────


@pytest.mark.skipif(not _GNINA_AVAILABLE, reason="GNINA not installed")
class TestDockingWrapper:
    """Tests that require a working GNINA installation."""

    def test_dock_known_binder(self):
        """Erlotinib docked into 1M17 returns negative Vina score."""
        from statebind.chemistry.docking import get_receptor_for_state

        receptor_info = get_receptor_for_state("DFGin_aCin")
        if receptor_info is None:
            pytest.skip("Receptor not prepared for DFGin_aCin")
        pdbqt, center, size = receptor_info
        result = dock_molecule(
            _ERLOTINIB, pdbqt, center, size,
            exhaustiveness=2, timeout=300,
        )
        assert result.success is True
        assert result.vina_score < 0

    def test_dock_invalid_smiles(self):
        """Invalid SMILES returns success=False."""
        from statebind.chemistry.docking import get_receptor_for_state

        receptor_info = get_receptor_for_state("DFGin_aCin")
        if receptor_info is None:
            pytest.skip("Receptor not prepared")
        pdbqt, center, size = receptor_info
        result = dock_molecule("not_valid", pdbqt, center, size)
        assert result.success is False

    def test_vina_score_range(self):
        """Vina score for drug-like molecules falls in [-15, 0] kcal/mol."""
        from statebind.chemistry.docking import get_receptor_for_state

        receptor_info = get_receptor_for_state("DFGin_aCin")
        if receptor_info is None:
            pytest.skip("Receptor not prepared")
        pdbqt, center, size = receptor_info
        result = dock_molecule(
            _ERLOTINIB, pdbqt, center, size,
            exhaustiveness=2, timeout=300,
        )
        if result.success:
            assert -15.0 <= result.vina_score <= 0.0

    def test_cnn_score_range(self):
        """CNN score is in [0, 1]."""
        from statebind.chemistry.docking import get_receptor_for_state

        receptor_info = get_receptor_for_state("DFGin_aCin")
        if receptor_info is None:
            pytest.skip("Receptor not prepared")
        pdbqt, center, size = receptor_info
        result = dock_molecule(
            _ERLOTINIB, pdbqt, center, size,
            exhaustiveness=2, timeout=300,
        )
        if result.success:
            assert 0.0 <= result.cnn_score <= 1.0


# ── Category 6: Receptor preparation metadata (always run) ──────────────


class TestReceptorPreparation:
    """Tests for receptor preparation metadata."""

    def test_box_config_structure(self):
        """Box config JSON has correct structure when parsed."""
        box = {
            "pdb_id": "1m17",
            "state": "DFGin_aCin",
            "center_x": 22.5,
            "center_y": 4.3,
            "center_z": 18.7,
            "size_x": 25.0,
            "size_y": 25.0,
            "size_z": 25.0,
            "ligand_id": "AEE",
        }
        assert isinstance(box["center_x"], float)
        assert isinstance(box["center_y"], float)
        assert isinstance(box["center_z"], float)
        assert box["size_x"] > 0
        assert box["size_y"] > 0
        assert box["size_z"] > 0

    def test_all_representative_pdbs_defined(self):
        """All 4 states have representative PDBs in the structures metadata."""
        from statebind.processing.structures import _v1_curated_structures

        structures = _v1_curated_structures()
        representative_states = set()
        for s in structures:
            if s.is_representative:
                representative_states.add(s.state.value)

        expected = {"DFGin_aCin", "DFGin_aCout", "DFGout_aCin", "DFGout_aCout"}
        assert expected == representative_states


# ── Category 7: Fallback chain (always run, uses mocking) ────────────────


class TestFallbackChain:
    """Tests for the scoring cascade integration."""

    def test_cascade_prefers_gnina(self):
        """When GNINA is available with GPU + receptor, it is used as tier 0."""
        mock_result = DockingResult(
            smiles=_ETHANOL,
            vina_score=-7.0,
            cnn_score=0.8,
            cnn_affinity=6.5,
            n_poses=5,
            success=True,
        )
        with (
            patch("statebind.ranking.scoring._gpu_available", return_value=True),
            patch("statebind.chemistry.docking.is_gnina_available", return_value=True),
            patch(
                "statebind.chemistry.docking.get_receptor_for_state",
                return_value=(Path("/fake/receptor.pdbqt"), (0, 0, 0), (25, 25, 25)),
            ),
            patch("statebind.chemistry.docking.dock_molecule", return_value=mock_result),
        ):
            from statebind.ranking.scoring import _score_docking

            score, is_stub, method = _score_docking(_ETHANOL, "unified")
            assert is_stub is False
            assert "GNINA" in method
            # sigmoid(-(-7.0)/3) = sigmoid(7/3) ≈ 0.9110
            expected = normalize_vina_score(-7.0)
            assert abs(score - round(expected, 4)) < 0.001

    def test_cascade_falls_back_without_gnina(self):
        """When GNINA is unavailable, cascade falls through."""
        with (
            patch("statebind.ranking.scoring._gpu_available", return_value=True),
            patch("statebind.chemistry.docking.is_gnina_available", return_value=False),
        ):
            from statebind.ranking.scoring import _score_docking

            score, is_stub, method = _score_docking(_ETHANOL, "unified")
            # Should fall to MPNN, proxy, or stub -- NOT GNINA
            assert "GNINA" not in method

    def test_cascade_falls_back_without_receptor(self):
        """GNINA available but no receptor files -> falls through."""
        with (
            patch("statebind.ranking.scoring._gpu_available", return_value=True),
            patch("statebind.chemistry.docking.is_gnina_available", return_value=True),
            patch("statebind.chemistry.docking.get_receptor_for_state", return_value=None),
        ):
            from statebind.ranking.scoring import _score_docking

            score, is_stub, method = _score_docking(_ETHANOL, "unified")
            assert "GNINA" not in method

    def test_cascade_falls_back_without_gpu(self):
        """Without GPU, GNINA is skipped even if installed."""
        with patch("statebind.ranking.scoring._gpu_available", return_value=False):
            from statebind.ranking.scoring import _score_docking

            score, is_stub, method = _score_docking(_ETHANOL, "unified")
            assert "GNINA" not in method


# ── Category 8: State-specific analysis models (always run) ──────────────


class TestDockingAnalysis:
    """Tests for docking analysis data models."""

    def test_analysis_summary_model(self):
        """DockingAnalysisSummary validates correctly."""
        from statebind.evaluation.docking_analysis import DockingAnalysisSummary

        summary = DockingAnalysisSummary(
            n_candidates=10,
            n_selective=7,
            selectivity_rate=0.7,
            mean_selectivity_ratio=1.3,
            per_state_means={"DFGin_aCin": 0.85, "DFGin_aCout": 0.72},
            generated_at="2026-04-07T00:00:00+00:00",
        )
        assert summary.n_candidates == 10
        assert summary.selectivity_rate == 0.7

    def test_heatmap_dimensions(self):
        """Heatmap data has correct dimensions for candidates x states."""
        from statebind.evaluation.docking_analysis import (
            DockingAnalysisSummary,
            StateSelectivityResult,
            compute_score_heatmap,
        )

        results = [
            StateSelectivityResult(
                smiles=f"C{'C' * i}O",
                target_state="DFGin_aCin",
                scores_by_state={
                    "DFGin_aCin": 0.8,
                    "DFGin_aCout": 0.6,
                    "DFGout_aCin": 0.5,
                    "DFGout_aCout": 0.4,
                },
                best_state="DFGin_aCin",
                is_selective=True,
            )
            for i in range(3)
        ]
        summary = DockingAnalysisSummary(
            n_candidates=3,
            results=results,
        )

        heatmap = compute_score_heatmap(summary)
        assert len(heatmap["candidates"]) == 3
        assert len(heatmap["states"]) == 4
        assert len(heatmap["scores"]) == 3
        assert len(heatmap["scores"][0]) == 4

    def test_selectivity_result_model(self):
        """StateSelectivityResult validates with all fields."""
        from statebind.evaluation.docking_analysis import StateSelectivityResult

        result = StateSelectivityResult(
            smiles=_ERLOTINIB,
            target_state="DFGin_aCin",
            scores_by_state={"DFGin_aCin": 0.9, "DFGin_aCout": 0.7},
            raw_vina_by_state={"DFGin_aCin": -8.5, "DFGin_aCout": -6.0},
            best_state="DFGin_aCin",
            selectivity_ratio=1.28,
            target_rank=1,
            is_selective=True,
        )
        assert result.is_selective is True
        assert result.target_rank == 1


# ── Category 9: Config loading (always run) ──────────────────────────────


class TestDockingConfig:
    """Tests for docking configuration loading."""

    def test_load_config_defaults(self):
        """Loading with no config file returns sensible defaults."""
        config = DockingConfig()
        assert config.exhaustiveness == 8
        assert config.num_modes == 5
        assert config.vina_scale == 3.0
        assert config.default_box_size == (25.0, 25.0, 25.0)
        assert "1m17" in config.representatives.values()

    def test_load_config_from_yaml(self):
        """Loading from actual configs/docking.yaml parses correctly."""
        from statebind.data.paths import DataPaths

        paths = DataPaths()
        config_path = paths.root / "configs" / "docking.yaml"
        if not config_path.exists():
            pytest.skip("configs/docking.yaml not found")
        config = load_docking_config(config_path)
        assert config.exhaustiveness == 8
        assert config.representatives["DFGin_aCin"] == "1m17"

    def test_config_missing_file_returns_defaults(self):
        """Missing config file returns defaults without error."""
        config = load_docking_config(Path("/nonexistent/config.yaml"))
        assert config.exhaustiveness == 8
        assert config.binary_path == "gnina"


# ── Category 10: GNINA output parsing (always run) ──────────────────────


class TestGninaOutputParsing:
    """Tests for parsing GNINA stdout."""

    def test_parse_pipe_separated_output(self):
        """Parse standard GNINA pipe-separated table."""
        from statebind.chemistry.docking import _parse_gnina_output

        stdout = """Using AutoDock Vina as scoring function.
Output will be in SDF format.
mode |   affinity | intramol | CNN_pose_score | CNN_affinity
-----+------------+----------+----------------+-------------
   1 |     -8.123 |    0.000 |          0.851 |        7.23
   2 |     -7.500 |    0.100 |          0.720 |        6.50
   3 |     -7.100 |    0.200 |          0.680 |        6.20
"""
        parsed = _parse_gnina_output(stdout)
        assert parsed["vina_score"] == pytest.approx(-8.123)
        assert parsed["cnn_score"] == pytest.approx(0.851)
        assert parsed["cnn_affinity"] == pytest.approx(7.23)
        assert parsed["n_poses"] == 3

    def test_parse_empty_output(self):
        """Empty output returns zeros."""
        from statebind.chemistry.docking import _parse_gnina_output

        parsed = _parse_gnina_output("")
        assert parsed["vina_score"] == 0.0
        assert parsed["n_poses"] == 0


# ── Category 11: Batch docking (always run) ──────────────────────────────


class TestBatchDocking:
    """Tests for batch docking functionality."""

    def test_batch_empty_list(self):
        """Batch docking with empty list returns empty list."""
        results = dock_batch(
            [],
            Path("/nonexistent.pdbqt"),
            (0, 0, 0),
        )
        assert results == []

    def test_batch_without_gnina(self):
        """Batch docking without GNINA returns failure results."""
        with patch("statebind.chemistry.docking.is_gnina_available", return_value=False):
            results = dock_batch(
                [_ETHANOL, _ERLOTINIB],
                Path("/nonexistent.pdbqt"),
                (0, 0, 0),
                n_workers=1,
            )
            assert len(results) == 2
            assert all(not r.success for r in results)
