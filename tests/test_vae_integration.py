"""Tests for VAE data preparation and generation pipeline integration.

Covers:
  1. Data preparation (curated fallback, split logic, format validation)
  2. VAE integration (load_vae_candidates, build_vae_libraries)
  3. Edge cases (unknown state, invalid candidates, torch-dependent)

Total: 17 tests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ── Import data preparation functions via sys.path ───────────────────────
# scripts/ is not a package, so we add it to sys.path for import.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from prepare_vae_data import (  # noqa: E402
    _curated_egfr_compounds,
    _split_train_val,
)

from statebind.baselines.models import CandidateSource  # noqa: E402
from statebind.generation.models import GenerationStrategy  # noqa: E402
from statebind.generation.vae_integration import (  # noqa: E402
    build_vae_libraries,
    load_vae_candidates,
)
from statebind.ml.vae_dataset import DEFAULT_STATE_MAPPING  # noqa: E402
from statebind.ranking.models import PipelineLabel  # noqa: E402
from statebind.ranking.scoring import score_unified  # noqa: E402

# ── Shared test data ─────────────────────────────────────────────────────

_VALID_STATES = set(DEFAULT_STATE_MAPPING.keys())

SAMPLE_VAE_OUTPUT = {
    "candidates": [
        {
            "smiles": "c1ccc(NC(=O)c2ccccc2)cc1",
            "state": "DFGin_aCin",
            "source": "vae_latent_sample",
            "is_valid": True,
            "is_novel": True,
        },
        {
            "smiles": "COc1ccc(NC(=O)c2ccncc2)cc1",
            "state": "DFGin_aCout",
            "source": "vae_latent_sample",
            "is_valid": True,
            "is_novel": True,
        },
        {
            "smiles": "O=C(Nc1ccccc1F)c1ccc(F)cc1",
            "state": "DFGout_aCin",
            "source": "vae_latent_sample",
            "is_valid": True,
            "is_novel": False,
        },
        {
            "smiles": "CC(=O)Nc1ccc(-c2ccncc2)cc1",
            "state": "DFGout_aCin",
            "source": "vae_latent_sample",
            "is_valid": True,
            "is_novel": True,
        },
        {
            "smiles": "INVALID_SMILES_HERE",
            "state": "DFGin_aCin",
            "source": "vae_latent_sample",
            "is_valid": False,
            "is_novel": False,
        },
    ],
    "temperature": 0.8,
    "n_samples_per_state": 100,
    "generated_at": "2026-03-22T00:00:00+00:00",
}


def _write_sample_json(tmp_path: Path) -> Path:
    """Write sample VAE output JSON to tmp_path and return path."""
    path = tmp_path / "vae_candidates.json"
    path.write_text(json.dumps(SAMPLE_VAE_OUTPUT, indent=2))
    return path


# ═════════════════════════════════════════════════════════════════════════
# 1. Data Preparation Tests (5)
# ═════════════════════════════════════════════════════════════════════════


class TestDataPreparation:
    """Tests for the curated fallback and split logic."""

    def test_data_format_train(self) -> None:
        """Train records have 'smiles' and 'state' keys."""
        records = _curated_egfr_compounds()
        train, _val = _split_train_val(records, train_ratio=0.8, seed=42)
        for rec in train:
            assert "smiles" in rec, "Missing 'smiles' key"
            assert "state" in rec, "Missing 'state' key"
            assert isinstance(rec["smiles"], str)
            assert isinstance(rec["state"], str)

    def test_data_format_val(self) -> None:
        """Val records have 'smiles' and 'state' keys."""
        records = _curated_egfr_compounds()
        _train, val = _split_train_val(records, train_ratio=0.8, seed=42)
        for rec in val:
            assert "smiles" in rec, "Missing 'smiles' key"
            assert "state" in rec, "Missing 'state' key"
            assert isinstance(rec["smiles"], str)
            assert isinstance(rec["state"], str)

    def test_state_labels_valid(self) -> None:
        """All state labels are in DEFAULT_STATE_MAPPING."""
        records = _curated_egfr_compounds()
        train, val = _split_train_val(records, train_ratio=0.8, seed=42)
        for rec in train + val:
            assert rec["state"] in _VALID_STATES, (
                f"Invalid state: {rec['state']}"
            )

    def test_no_empty_smiles(self) -> None:
        """No empty or whitespace-only SMILES."""
        records = _curated_egfr_compounds()
        train, val = _split_train_val(records, train_ratio=0.8, seed=42)
        for rec in train + val:
            assert rec["smiles"].strip(), (
                f"Empty SMILES in record: {rec}"
            )

    def test_train_val_no_overlap(self) -> None:
        """No SMILES in both train and val."""
        records = _curated_egfr_compounds()
        train, val = _split_train_val(records, train_ratio=0.8, seed=42)
        train_smiles = {r["smiles"] for r in train}
        val_smiles = {r["smiles"] for r in val}
        overlap = train_smiles & val_smiles
        assert len(overlap) == 0, (
            f"Found {len(overlap)} overlapping SMILES between splits"
        )


# ═════════════════════════════════════════════════════════════════════════
# 2. Integration Tests (6)
# ═════════════════════════════════════════════════════════════════════════


class TestVAEIntegration:
    """Tests for load_vae_candidates and pipeline compatibility."""

    def test_vae_candidates_are_state_conditioned(
        self, tmp_path: Path
    ) -> None:
        """Every candidate has a valid target_state."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        for cand in candidates:
            assert cand.target_state in _VALID_STATES, (
                f"Invalid state: {cand.target_state}"
            )

    def test_vae_candidates_have_correct_source(
        self, tmp_path: Path
    ) -> None:
        """All candidates have source == CandidateSource.ML_GENERATED."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        for cand in candidates:
            assert cand.source == CandidateSource.ML_GENERATED

    def test_vae_candidates_have_correct_strategy(
        self, tmp_path: Path
    ) -> None:
        """All candidates have strategy == GenerationStrategy.VAE_GENERATED."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        for cand in candidates:
            assert cand.strategy == GenerationStrategy.VAE_GENERATED

    def test_vae_candidates_scorable(self, tmp_path: Path) -> None:
        """score_unified() runs without error on VAE candidates."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        assert len(candidates) > 0

        # Build a minimal state_smiles_map
        state_smiles_map: dict[str, set[str]] = {}
        for cand in candidates:
            state_smiles_map.setdefault(cand.target_state, set()).add(
                cand.smiles
            )

        for cand in candidates:
            components, score = score_unified(
                smiles=cand.smiles,
                target_state=cand.target_state,
                pipeline=PipelineLabel.STATE_AWARE,
                state_smiles_map=state_smiles_map,
            )
            assert isinstance(score, float)
            assert len(components) == 4
            assert 0.0 <= score <= 1.0

    def test_vae_candidate_ids_unique(self, tmp_path: Path) -> None:
        """No duplicate candidate_id values."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        ids = [c.candidate_id for c in candidates]
        assert len(ids) == len(set(ids)), (
            f"Duplicate IDs found: {len(ids)} total, {len(set(ids))} unique"
        )

    def test_load_vae_candidates_from_json(self, tmp_path: Path) -> None:
        """Round-trip: write JSON, load, verify field mapping."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)

        # is_valid=False entry should be filtered
        assert len(candidates) == 4

        # Check first candidate fields
        c0 = candidates[0]
        assert c0.smiles == "c1ccc(NC(=O)c2ccccc2)cc1"
        assert c0.target_state == "DFGin_aCin"
        assert c0.source == CandidateSource.ML_GENERATED
        assert c0.strategy == GenerationStrategy.VAE_GENERATED
        assert c0.parent_id == ""
        assert "temperature=0.8" in c0.notes
        assert c0.candidate_id.startswith("vae_DFGin_aCin_")


# ═════════════════════════════════════════════════════════════════════════
# 3. Edge Case & Additional Tests (6)
# ═════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases and additional coverage."""

    def test_generate_with_temperature_zero(self) -> None:
        """Greedy decoding (temperature=0) is deterministic."""
        torch = pytest.importorskip("torch")
        from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig
        from statebind.ml.vocabulary import Vocabulary

        # Tiny model for fast test
        vocab = Vocabulary()
        for token in list("CNOcn()=#12345"):
            vocab.add_token(token)

        config = VAEConfig(
            vocab_size=vocab.size,
            embed_dim=16,
            hidden_dim=32,
            latent_dim=8,
            n_layers=1,
            dropout=0.0,
            n_states=3,
        )
        model = ConditionalSMILESVAE(config)
        model.eval()

        z = torch.zeros(2, config.latent_dim)
        state = torch.zeros(2, 3)
        state[:, 0] = 1.0  # DFGin_aCin

        seq1 = model.generate(z, state, max_len=20, temperature=0, vocab=vocab)
        seq2 = model.generate(z, state, max_len=20, temperature=0, vocab=vocab)
        assert seq1 == seq2, "Greedy decoding should be deterministic"

    def test_generate_empty_latent(self) -> None:
        """Zero-vector latent produces valid (if boring) output."""
        torch = pytest.importorskip("torch")
        from statebind.ml.vae import ConditionalSMILESVAE, VAEConfig
        from statebind.ml.vocabulary import Vocabulary

        vocab = Vocabulary()
        for token in list("CNOcn()=#12345"):
            vocab.add_token(token)

        config = VAEConfig(
            vocab_size=vocab.size,
            embed_dim=16,
            hidden_dim=32,
            latent_dim=8,
            n_layers=1,
            dropout=0.0,
            n_states=3,
        )
        model = ConditionalSMILESVAE(config)
        model.eval()

        z = torch.zeros(1, config.latent_dim)
        state = torch.zeros(1, 3)
        state[0, 2] = 1.0  # DFGout_aCin

        sequences = model.generate(
            z, state, max_len=30, temperature=0, vocab=vocab,
        )
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], list)

    def test_unknown_state_rejected(self, tmp_path: Path) -> None:
        """Invalid state label in JSON raises ValueError."""
        bad_data = {
            "candidates": [
                {
                    "smiles": "CCO",
                    "state": "INVALID_STATE",
                    "is_valid": True,
                },
            ],
            "temperature": 0.8,
        }
        path = tmp_path / "bad_state.json"
        path.write_text(json.dumps(bad_data))

        with pytest.raises(ValueError, match="Invalid state label"):
            load_vae_candidates(path)

    def test_build_vae_libraries_groups_by_state(
        self, tmp_path: Path
    ) -> None:
        """Libraries are grouped correctly by state."""
        path = _write_sample_json(tmp_path)
        candidates = load_vae_candidates(path)
        libraries = build_vae_libraries(candidates)

        # Sample data has 4 valid candidates across 3 states
        assert len(libraries) == 3
        states = [lib.state for lib in libraries]
        assert states == sorted(states), "Libraries should be sorted by state"
        for lib in libraries:
            assert lib.n_candidates == len(lib.candidates)
            assert lib.strategies_used == ["vae_generated"]
            for cand in lib.candidates:
                assert cand.target_state == lib.state

    def test_build_vae_libraries_empty_input(self) -> None:
        """Empty candidate list returns empty library list."""
        libraries = build_vae_libraries([])
        assert libraries == []

    def test_load_vae_candidates_filters_invalid(
        self, tmp_path: Path
    ) -> None:
        """is_valid=False entries are filtered out."""
        data = {
            "candidates": [
                {"smiles": "CCO", "state": "DFGin_aCin", "is_valid": True},
                {"smiles": "BAD", "state": "DFGin_aCin", "is_valid": False},
                {"smiles": "c1ccccc1", "state": "DFGin_aCin", "is_valid": True},
                {"smiles": "", "state": "DFGin_aCin", "is_valid": True},
            ],
            "temperature": 1.0,
        }
        path = tmp_path / "mixed.json"
        path.write_text(json.dumps(data))

        candidates = load_vae_candidates(path)
        # 1 invalid (is_valid=False), 1 empty SMILES → 2 filtered
        assert len(candidates) == 2
        smiles_set = {c.smiles for c in candidates}
        assert "CCO" in smiles_set
        assert "c1ccccc1" in smiles_set
        assert "BAD" not in smiles_set
