"""Tests for scoring ablation analysis.

Covers:
- generate_ablation_configs: correct count, weight sums, zeroed components
- rerank_with_weights: reranking changes order when weights differ
- Weight renormalization arithmetic
- Edge cases: empty candidates, all-zero weights
"""

from __future__ import annotations

import pytest

from statebind.evaluation.scoring_ablation import (
    AblationConfig,
    AblationResult,
    generate_ablation_configs,
    rerank_with_weights,
)
from statebind.ranking.models import (
    PipelineLabel,
    UnifiedScoreComponent,
    UnifiedScoredCandidate,
)
from statebind.ranking.scoring import DEFAULT_WEIGHTS


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def sample_candidates() -> list[UnifiedScoredCandidate]:
    """Build 5 candidates with distinct per-component scores.

    Designed so that changing weights can flip ranking order.
    """
    candidates = []
    # Candidate A: high ref_sim, low druglikeness
    candidates.append(
        UnifiedScoredCandidate(
            candidate_id="cand_A",
            smiles="c1ccccc1",
            pipeline=PipelineLabel.STATE_AWARE,
            target_state="DFGin_aCin",
            scores=[
                UnifiedScoreComponent(
                    name="reference_similarity", value=0.9, weight=0.35
                ),
                UnifiedScoreComponent(
                    name="druglikeness", value=0.2, weight=0.30
                ),
                UnifiedScoreComponent(
                    name="docking_proxy", value=0.5, weight=0.20
                ),
                UnifiedScoreComponent(
                    name="state_specificity", value=0.8, weight=0.15
                ),
            ],
            composite_score=round(
                0.9 * 0.35 + 0.2 * 0.30 + 0.5 * 0.20 + 0.8 * 0.15, 4
            ),
            rank_in_pipeline=1,
        )
    )
    # Candidate B: low ref_sim, high druglikeness
    candidates.append(
        UnifiedScoredCandidate(
            candidate_id="cand_B",
            smiles="c1ccc(O)cc1",
            pipeline=PipelineLabel.STATE_AWARE,
            target_state="DFGin_aCout",
            scores=[
                UnifiedScoreComponent(
                    name="reference_similarity", value=0.2, weight=0.35
                ),
                UnifiedScoreComponent(
                    name="druglikeness", value=0.9, weight=0.30
                ),
                UnifiedScoreComponent(
                    name="docking_proxy", value=0.5, weight=0.20
                ),
                UnifiedScoreComponent(
                    name="state_specificity", value=0.3, weight=0.15
                ),
            ],
            composite_score=round(
                0.2 * 0.35 + 0.9 * 0.30 + 0.5 * 0.20 + 0.3 * 0.15, 4
            ),
            rank_in_pipeline=2,
        )
    )
    # Candidate C: high docking, low everything else
    candidates.append(
        UnifiedScoredCandidate(
            candidate_id="cand_C",
            smiles="c1ccc(N)cc1",
            pipeline=PipelineLabel.STATE_AWARE,
            target_state="DFGout_aCin",
            scores=[
                UnifiedScoreComponent(
                    name="reference_similarity", value=0.3, weight=0.35
                ),
                UnifiedScoreComponent(
                    name="druglikeness", value=0.3, weight=0.30
                ),
                UnifiedScoreComponent(
                    name="docking_proxy", value=0.95, weight=0.20
                ),
                UnifiedScoreComponent(
                    name="state_specificity", value=0.1, weight=0.15
                ),
            ],
            composite_score=round(
                0.3 * 0.35 + 0.3 * 0.30 + 0.95 * 0.20 + 0.1 * 0.15, 4
            ),
            rank_in_pipeline=3,
        )
    )
    # Candidate D: high state_specificity, medium everything else
    candidates.append(
        UnifiedScoredCandidate(
            candidate_id="cand_D",
            smiles="c1ccc(F)cc1",
            pipeline=PipelineLabel.STATE_AWARE,
            target_state="DFGin_aCin",
            scores=[
                UnifiedScoreComponent(
                    name="reference_similarity", value=0.4, weight=0.35
                ),
                UnifiedScoreComponent(
                    name="druglikeness", value=0.4, weight=0.30
                ),
                UnifiedScoreComponent(
                    name="docking_proxy", value=0.4, weight=0.20
                ),
                UnifiedScoreComponent(
                    name="state_specificity", value=1.0, weight=0.15
                ),
            ],
            composite_score=round(
                0.4 * 0.35 + 0.4 * 0.30 + 0.4 * 0.20 + 1.0 * 0.15, 4
            ),
            rank_in_pipeline=4,
        )
    )
    # Candidate E: uniformly low
    candidates.append(
        UnifiedScoredCandidate(
            candidate_id="cand_E",
            smiles="c1ccc(Cl)cc1",
            pipeline=PipelineLabel.STATE_AWARE,
            target_state="DFGin_aCout",
            scores=[
                UnifiedScoreComponent(
                    name="reference_similarity", value=0.1, weight=0.35
                ),
                UnifiedScoreComponent(
                    name="druglikeness", value=0.1, weight=0.30
                ),
                UnifiedScoreComponent(
                    name="docking_proxy", value=0.1, weight=0.20
                ),
                UnifiedScoreComponent(
                    name="state_specificity", value=0.1, weight=0.15
                ),
            ],
            composite_score=round(
                0.1 * 0.35 + 0.1 * 0.30 + 0.1 * 0.20 + 0.1 * 0.15, 4
            ),
            rank_in_pipeline=5,
        )
    )
    # Sort by composite descending (matching real pipeline behavior)
    candidates.sort(key=lambda x: x.composite_score, reverse=True)
    for i, c in enumerate(candidates):
        c.rank_in_pipeline = i + 1
    return candidates


# ═══════════════════════════════════════════════════════════════════════════
# Tests for generate_ablation_configs
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateAblationConfigs:
    """Tests for ablation config generation."""

    def test_produces_five_configs(self) -> None:
        """DEFAULT_WEIGHTS (4 components) produces 5 configs: 1 baseline + 4."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        assert len(configs) == 5

    def test_baseline_is_first(self) -> None:
        """First config is always the baseline (unchanged weights)."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        assert configs[0].name == "baseline"
        assert configs[0].zeroed_component is None

    def test_baseline_preserves_weights(self) -> None:
        """Baseline config has identical weights to the input."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        for key in DEFAULT_WEIGHTS:
            assert configs[0].weights[key] == DEFAULT_WEIGHTS[key]

    def test_all_weights_sum_to_one(self) -> None:
        """Every config's weights must sum to 1.0 within tolerance."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        for config in configs:
            total = sum(config.weights.values())
            assert abs(total - 1.0) < 1e-4, (
                f"Config '{config.name}' weights sum to {total}, "
                f"expected 1.0"
            )

    def test_zeroed_component_is_zero(self) -> None:
        """In each ablation config, the zeroed component has weight 0.0."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        for config in configs[1:]:  # skip baseline
            assert config.zeroed_component is not None
            assert config.weights[config.zeroed_component] == 0.0

    def test_each_component_zeroed_once(self) -> None:
        """Every component from base_weights appears as a zeroed component."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        zeroed = {c.zeroed_component for c in configs if c.zeroed_component}
        assert zeroed == set(DEFAULT_WEIGHTS.keys())

    def test_renormalization_arithmetic(self) -> None:
        """Zeroing reference_similarity (0.35) renormalizes remaining 0.65.

        druglikeness: 0.30/0.65 = 0.4615
        docking_proxy: 0.20/0.65 = 0.3077
        state_specificity: 0.15/0.65 = 0.2308
        """
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        no_ref = [c for c in configs if c.zeroed_component == "reference_similarity"][0]

        assert no_ref.weights["reference_similarity"] == 0.0
        assert abs(no_ref.weights["druglikeness"] - 0.30 / 0.65) < 0.001
        assert abs(no_ref.weights["docking_proxy"] - 0.20 / 0.65) < 0.001
        assert abs(no_ref.weights["state_specificity"] - 0.15 / 0.65) < 0.001

    def test_custom_weights(self) -> None:
        """Works with non-DEFAULT weight distributions."""
        custom = {
            "reference_similarity": 0.25,
            "druglikeness": 0.25,
            "docking_proxy": 0.25,
            "state_specificity": 0.25,
        }
        configs = generate_ablation_configs(custom)
        assert len(configs) == 5

        # Each ablation should give remaining 3 components weight 1/3
        for config in configs[1:]:
            for k, v in config.weights.items():
                if k == config.zeroed_component:
                    assert v == 0.0
                else:
                    assert abs(v - 1.0 / 3.0) < 0.001

    def test_empty_weights_raises(self) -> None:
        """Empty weight dict raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            generate_ablation_configs({})

    def test_all_zero_weights_raises(self) -> None:
        """All-zero weights raise ValueError."""
        zeros = {k: 0.0 for k in DEFAULT_WEIGHTS}
        with pytest.raises(ValueError, match="All weights are zero"):
            generate_ablation_configs(zeros)

    def test_single_nonzero_raises_on_that_component(self) -> None:
        """If only one component is nonzero, zeroing it raises."""
        single = {k: 0.0 for k in DEFAULT_WEIGHTS}
        single["druglikeness"] = 1.0
        # Zeroing the single nonzero component leaves all remaining at zero
        with pytest.raises(ValueError, match="cannot renormalize"):
            generate_ablation_configs(single)


# ═══════════════════════════════════════════════════════════════════════════
# Tests for rerank_with_weights
# ═══════════════════════════════════════════════════════════════════════════


class TestRerankWithWeights:
    """Tests for weight-based reranking."""

    def test_baseline_weights_preserve_order(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Reranking with original weights preserves order."""
        reranked = rerank_with_weights(sample_candidates, DEFAULT_WEIGHTS)
        original_ids = [c.candidate_id for c in sample_candidates]
        reranked_ids = [c.candidate_id for c in reranked]
        assert original_ids == reranked_ids

    def test_changed_weights_change_order(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Reranking with different weights changes candidate order."""
        # Give all weight to druglikeness -- cand_B should rise
        heavy_drug = {
            "reference_similarity": 0.0,
            "druglikeness": 1.0,
            "docking_proxy": 0.0,
            "state_specificity": 0.0,
        }
        reranked = rerank_with_weights(sample_candidates, heavy_drug)
        # cand_B has druglikeness=0.9 (highest)
        assert reranked[0].candidate_id == "cand_B"

    def test_heavy_docking_promotes_cand_c(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Giving all weight to docking_proxy promotes cand_C (0.95)."""
        heavy_dock = {
            "reference_similarity": 0.0,
            "druglikeness": 0.0,
            "docking_proxy": 1.0,
            "state_specificity": 0.0,
        }
        reranked = rerank_with_weights(sample_candidates, heavy_dock)
        assert reranked[0].candidate_id == "cand_C"

    def test_composite_score_recomputed(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Composite scores reflect the new weights, not the old ones."""
        uniform = {k: 0.25 for k in DEFAULT_WEIGHTS}
        reranked = rerank_with_weights(sample_candidates, uniform)
        for c in reranked:
            expected = round(sum(s.value * 0.25 for s in c.scores), 4)
            assert abs(c.composite_score - expected) < 1e-4

    def test_ranks_are_sequential(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """After reranking, rank_in_pipeline is 1..N."""
        reranked = rerank_with_weights(sample_candidates, DEFAULT_WEIGHTS)
        ranks = [c.rank_in_pipeline for c in reranked]
        assert ranks == list(range(1, len(reranked) + 1))

    def test_does_not_mutate_input(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Reranking creates copies -- original list is unchanged."""
        original_scores = [c.composite_score for c in sample_candidates]
        original_ids = [c.candidate_id for c in sample_candidates]

        heavy_drug = {
            "reference_similarity": 0.0,
            "druglikeness": 1.0,
            "docking_proxy": 0.0,
            "state_specificity": 0.0,
        }
        _ = rerank_with_weights(sample_candidates, heavy_drug)

        assert [c.composite_score for c in sample_candidates] == original_scores
        assert [c.candidate_id for c in sample_candidates] == original_ids

    def test_empty_candidates_raises(self) -> None:
        """Empty candidate list raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            rerank_with_weights([], DEFAULT_WEIGHTS)

    def test_weights_not_summing_to_one_raises(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """Weights not summing to 1.0 raises ValueError."""
        bad = {k: v * 2 for k, v in DEFAULT_WEIGHTS.items()}
        with pytest.raises(ValueError, match="must sum to 1.0"):
            rerank_with_weights(sample_candidates, bad)

    def test_zeroing_state_specificity_fairness(
        self, sample_candidates: list[UnifiedScoredCandidate]
    ) -> None:
        """P11 fairness: zeroing state_specificity + renormalize still works."""
        configs = generate_ablation_configs(DEFAULT_WEIGHTS)
        no_spec = [c for c in configs if c.zeroed_component == "state_specificity"][0]
        reranked = rerank_with_weights(sample_candidates, no_spec.weights)

        # All candidates should have state_specificity weight == 0
        for c in reranked:
            spec_comp = [s for s in c.scores if s.name == "state_specificity"][0]
            assert spec_comp.weight == 0.0

        # Composite should ignore state_specificity
        for c in reranked:
            expected = round(
                sum(
                    s.value * s.weight
                    for s in c.scores
                    if s.name != "state_specificity"
                ),
                4,
            )
            assert abs(c.composite_score - expected) < 1e-4


# ═══════════════════════════════════════════════════════════════════════════
# Tests for AblationResult and AblationConfig models
# ═══════════════════════════════════════════════════════════════════════════


class TestModels:
    """Tests for Pydantic model validation and serialization."""

    def test_ablation_config_roundtrip(self) -> None:
        """AblationConfig survives JSON roundtrip."""
        config = AblationConfig(
            name="no_docking_proxy",
            weights={"a": 0.5, "b": 0.5},
            zeroed_component="c",
        )
        data = config.model_dump(mode="json")
        restored = AblationConfig.model_validate(data)
        assert restored.name == config.name
        assert restored.weights == config.weights
        assert restored.zeroed_component == config.zeroed_component

    def test_ablation_result_roundtrip(self) -> None:
        """AblationResult survives JSON roundtrip."""
        result = AblationResult(
            config=AblationConfig(
                name="baseline",
                weights=DEFAULT_WEIGHTS,
            ),
            ef_at_10=4.95,
            ef_ci_lower=3.0,
            ef_ci_upper=6.5,
            bedroc=0.85,
            bedroc_ci_lower=0.75,
            bedroc_ci_upper=0.92,
            mean_score=0.5437,
            n_candidates=100,
        )
        data = result.model_dump(mode="json")
        restored = AblationResult.model_validate(data)
        assert restored.ef_at_10 == 4.95
        assert restored.bedroc == 0.85
        assert restored.n_candidates == 100

    def test_ablation_result_optional_bedroc(self) -> None:
        """BEDROC fields are optional (None when RDKit unavailable)."""
        result = AblationResult(
            config=AblationConfig(name="test", weights={"a": 1.0}),
            ef_at_10=2.0,
            ef_ci_lower=1.0,
            ef_ci_upper=3.0,
            mean_score=0.5,
            n_candidates=50,
        )
        assert result.bedroc is None
        assert result.bedroc_ci_lower is None
        assert result.bedroc_ci_upper is None
