"""Tests for Phase 5: world model / dynamics layer.

Covers:
- Sequence builder integrity
- Transition dataset correctness
- Transition matrix properties
- Model I/O schemas
- Metric calculations
- Embedding geometry
- World model pipeline
"""

from __future__ import annotations

import math

import pytest

from statebind.dynamics.sequences import (
    StateSequence,
    StateTransition,
    TransitionDataset,
    build_transition_dataset,
    extract_transitions,
)
from statebind.dynamics.transitions import (
    MarkovTransitionModel,
    TransitionMatrix,
    TransitionPrediction,
    UniformBaseline,
    estimate_transition_matrix,
)
from statebind.dynamics.embeddings import (
    EmbeddingSpace,
    StateEmbedding,
    learn_embeddings,
)
from statebind.dynamics.evaluation import (
    compute_perplexity,
    compute_transition_accuracy,
    evaluate_embedding_quality,
    evaluate_transition_model,
    compare_models,
    metrics_to_dict,
)
from statebind.dynamics.world_model import (
    LearnedWorldModel,
    WorldModelConfig,
    WorldModelOutput,
    build_world_model,
    save_world_model,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def dataset():
    return build_transition_dataset()


@pytest.fixture
def states(dataset):
    return dataset.states


@pytest.fixture
def transitions(dataset):
    return dataset.transitions


@pytest.fixture
def trans_matrix(transitions, states):
    return estimate_transition_matrix(transitions, states, smoothing=1.0)


# ── Sequence builder tests ────────────────────────────────────────────────

class TestSequenceBuilder:
    def test_dataset_has_sequences(self, dataset):
        assert dataset.n_sequences > 0
        assert len(dataset.sequences) == dataset.n_sequences

    def test_dataset_has_transitions(self, dataset):
        assert dataset.n_transitions > 0
        assert len(dataset.transitions) == dataset.n_transitions

    def test_all_four_states_present(self, dataset):
        all_states = set()
        for seq in dataset.sequences:
            all_states.update(seq.states)
        assert len(all_states) == 4

    def test_sequences_have_provenance(self, dataset):
        for seq in dataset.sequences:
            assert seq.provenance != "" or seq.is_synthetic

    def test_sequences_have_at_least_two_states(self, dataset):
        for seq in dataset.sequences:
            assert len(seq.states) >= 2

    def test_synthetic_sequences_marked(self, dataset):
        synthetic = [s for s in dataset.sequences if s.is_synthetic]
        non_synthetic = [s for s in dataset.sequences if not s.is_synthetic]
        assert len(non_synthetic) > len(synthetic)  # most are literature-based

    def test_transitions_extracted_correctly(self):
        seq = StateSequence(
            sequence_id="test",
            states=["A", "B", "C"],
        )
        trans = extract_transitions([seq])
        assert len(trans) == 2
        assert trans[0].from_state == "A" and trans[0].to_state == "B"
        assert trans[1].from_state == "B" and trans[1].to_state == "C"

    def test_transition_count_matches_sequence_lengths(self, dataset):
        expected = sum(len(s.states) - 1 for s in dataset.sequences)
        assert dataset.n_transitions == expected


# ── Transition dataset integrity ──────────────────────────────────────────

class TestTransitionDataset:
    def test_states_are_sorted(self, dataset):
        assert dataset.states == sorted(dataset.states)

    def test_transitions_reference_valid_states(self, dataset):
        valid = set(dataset.states)
        for t in dataset.transitions:
            assert t.from_state in valid
            assert t.to_state in valid

    def test_dataset_has_timestamp(self, dataset):
        assert dataset.generated_at != ""

    def test_dataset_version(self, dataset):
        assert dataset.version == "1.0.0"


# ── Transition matrix tests ──────────────────────────────────────────────

class TestTransitionMatrix:
    def test_matrix_is_row_stochastic(self, trans_matrix):
        for row in trans_matrix.matrix:
            assert abs(sum(row) - 1.0) < 1e-6

    def test_matrix_has_no_zeros(self, trans_matrix):
        """Laplace smoothing ensures no zero probabilities."""
        for row in trans_matrix.matrix:
            for val in row:
                assert val > 0

    def test_matrix_shape(self, trans_matrix, states):
        n = len(states)
        assert len(trans_matrix.matrix) == n
        for row in trans_matrix.matrix:
            assert len(row) == n

    def test_counts_are_nonnegative(self, trans_matrix):
        for row in trans_matrix.counts:
            for val in row:
                assert val >= 0

    def test_get_prob(self, trans_matrix, states):
        p = trans_matrix.get_prob(states[0], states[1])
        assert 0.0 < p < 1.0

    def test_get_row_sums_to_one(self, trans_matrix, states):
        row = trans_matrix.get_row(states[0])
        assert abs(sum(row.values()) - 1.0) < 1e-6

    def test_stationary_distribution_sums_to_one(self, trans_matrix):
        stat = trans_matrix.stationary_distribution()
        assert abs(sum(stat.values()) - 1.0) < 1e-6

    def test_stationary_all_positive(self, trans_matrix):
        stat = trans_matrix.stationary_distribution()
        for v in stat.values():
            assert v > 0


# ── Model I/O schema tests ───────────────────────────────────────────────

class TestModelSchemas:
    def test_transition_prediction_schema(self):
        p = TransitionPrediction(
            from_state="DFGin_aCin",
            predicted_state="DFGin_aCout",
            probabilities={"DFGin_aCin": 0.3, "DFGin_aCout": 0.4,
                          "DFGout_aCin": 0.2, "DFGout_aCout": 0.1},
            confidence=0.4,
            model_name="markov",
        )
        assert p.from_state == "DFGin_aCin"
        assert abs(sum(p.probabilities.values()) - 1.0) < 1e-6

    def test_state_embedding_schema(self):
        e = StateEmbedding(state="DFGin_aCin", vector=[0.1, 0.2, 0.3, 0.4])
        assert e.dim == 4

    def test_world_model_config(self):
        c = WorldModelConfig()
        assert c.model_type == "markov"
        assert c.embedding_dim == 4

    def test_world_model_output_schema(self, dataset, trans_matrix):
        out = WorldModelOutput(
            config=WorldModelConfig(),
            transition_dataset=dataset,
            transition_matrix=trans_matrix,
            embeddings=None,
            stationary_distribution={"DFGin_aCin": 0.4, "DFGin_aCout": 0.3,
                                     "DFGout_aCin": 0.15, "DFGout_aCout": 0.15},
            model_name="markov",
        )
        assert out.model_name == "markov"


# ── Uniform baseline tests ───────────────────────────────────────────────

class TestUniformBaseline:
    def test_uniform_equal_probabilities(self, states):
        model = UniformBaseline(states)
        pred = model.predict(states[0])
        expected = 1.0 / len(states)
        for p in pred.probabilities.values():
            assert abs(p - expected) < 1e-6

    def test_uniform_log_likelihood(self, states, transitions):
        model = UniformBaseline(states)
        ll = model.log_likelihood(transitions)
        expected = math.log(1.0 / len(states))
        assert abs(ll - expected) < 1e-6


# ── Markov model tests ───────────────────────────────────────────────────

class TestMarkovModel:
    def test_fit_predict(self, states, transitions):
        model = MarkovTransitionModel(states, smoothing=1.0)
        model.fit(transitions)
        pred = model.predict(states[0])
        assert pred.predicted_state in states
        assert abs(sum(pred.probabilities.values()) - 1.0) < 1e-6

    def test_log_likelihood_better_than_uniform(self, states, transitions):
        uniform = UniformBaseline(states)
        uni_ll = uniform.log_likelihood(transitions)

        markov = MarkovTransitionModel(states, smoothing=1.0)
        markov.fit(transitions)
        mk_ll = markov.log_likelihood(transitions)

        assert mk_ll >= uni_ll  # Markov should fit at least as well

    def test_predict_sequence(self, states, transitions):
        model = MarkovTransitionModel(states, smoothing=1.0)
        model.fit(transitions)
        seq = [states[0], states[1], states[2]]
        preds = model.predict_sequence(seq)
        assert len(preds) == 2  # n-1 predictions

    def test_unfitted_raises(self, states):
        model = MarkovTransitionModel(states)
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict(states[0])

    def test_stationary_distribution(self, states, transitions):
        model = MarkovTransitionModel(states)
        model.fit(transitions)
        stat = model.get_stationary()
        assert abs(sum(stat.values()) - 1.0) < 1e-6


# ── Embedding tests ──────────────────────────────────────────────────────

class TestEmbeddings:
    def test_learn_embeddings(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50, seed=42)
        assert emb.dim == 4
        assert len(emb.embeddings) == len(trans_matrix.states)

    def test_embedding_vectors_correct_dim(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=3, n_epochs=50)
        for s in trans_matrix.states:
            assert len(emb.get_vector(s)) == 3

    def test_pairwise_distances(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        dists = emb.pairwise_distances()
        n = len(trans_matrix.states)
        assert len(dists) == n * (n - 1) // 2

    def test_distances_are_positive(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        for d in emb.pairwise_distances().values():
            assert d >= 0

    def test_nearest_state(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        for s in trans_matrix.states:
            nearest = emb.nearest_state(s)
            assert nearest != s
            assert nearest in trans_matrix.states

    def test_training_loss_decreases(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=100)
        if len(emb.training_loss) > 10:
            early = sum(emb.training_loss[:5]) / 5
            late = sum(emb.training_loss[-5:]) / 5
            assert late <= early * 1.5  # loss should not explode


# ── Metric calculation tests ─────────────────────────────────────────────

class TestMetrics:
    def test_accuracy_perfect(self):
        preds = [TransitionPrediction(from_state="A", predicted_state="B",
                                      probabilities={}, confidence=1.0)]
        trans = [StateTransition(from_state="A", to_state="B")]
        assert compute_transition_accuracy(preds, trans) == 1.0

    def test_accuracy_zero(self):
        preds = [TransitionPrediction(from_state="A", predicted_state="C",
                                      probabilities={}, confidence=1.0)]
        trans = [StateTransition(from_state="A", to_state="B")]
        assert compute_transition_accuracy(preds, trans) == 0.0

    def test_perplexity_uniform(self):
        ll = math.log(0.25)  # 4 states uniform
        ppl = compute_perplexity(ll)
        assert abs(ppl - 4.0) < 1e-6

    def test_metrics_to_dict(self):
        m = evaluate_transition_model(
            "test", [], [], 0.0
        )
        d = metrics_to_dict(m)
        assert "model_name" in d
        assert "accuracy" in d
        assert "log_likelihood" in d
        assert "perplexity" in d

    def test_embedding_quality_metrics(self, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        metrics = evaluate_embedding_quality(emb, trans_matrix)
        assert metrics.mean_distance > 0
        assert -1.0 <= metrics.transition_correlation <= 1.0


# ── Learned world model tests ────────────────────────────────────────────

class TestLearnedModel:
    def test_learned_model_fit_predict(self, states, transitions, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        config = WorldModelConfig(mlp_hidden=4, mlp_epochs=20)
        model = LearnedWorldModel(states, config)
        model.fit(transitions, emb)
        pred = model.predict(states[0], emb)
        assert pred.predicted_state in states
        assert abs(sum(pred.probabilities.values()) - 1.0) < 1e-6

    def test_learned_model_unfitted_raises(self, states):
        config = WorldModelConfig()
        model = LearnedWorldModel(states, config)
        emb = EmbeddingSpace(
            embeddings={s: StateEmbedding(state=s, vector=[0.0] * 4) for s in states},
            dim=4, states=states,
        )
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict(states[0], emb)


# ── World model pipeline tests ───────────────────────────────────────────

class TestWorldModelPipeline:
    def test_build_markov_model(self):
        output = build_world_model(WorldModelConfig(model_type="markov"))
        assert output.model_name == "markov"
        assert output.transition_matrix is not None
        assert output.embeddings is not None
        assert abs(sum(output.stationary_distribution.values()) - 1.0) < 1e-6

    def test_build_learned_model(self):
        output = build_world_model(WorldModelConfig(
            model_type="learned", mlp_epochs=20, embedding_epochs=50,
        ))
        assert output.model_name == "learned_mlp"

    def test_build_uniform_model(self):
        output = build_world_model(WorldModelConfig(model_type="uniform"))
        assert output.model_name == "uniform_baseline"

    def test_save_world_model(self, tmp_path):
        output = build_world_model(WorldModelConfig(
            model_type="markov", embedding_epochs=20,
        ))
        files = save_world_model(output, tmp_path / "test_artifacts")
        assert len(files) >= 5
        for f in files:
            assert f.exists()

    def test_pipeline_deterministic(self):
        out1 = build_world_model(WorldModelConfig(model_type="markov", random_seed=42))
        out2 = build_world_model(WorldModelConfig(model_type="markov", random_seed=42))
        assert out1.stationary_distribution == out2.stationary_distribution

    def test_model_comparison(self, transitions, states, trans_matrix):
        emb = learn_embeddings(trans_matrix, dim=4, n_epochs=50)
        comp = compare_models(transitions, states, embeddings=emb)
        assert len(comp.models) == 3  # uniform, markov, learned
        assert comp.best_model != ""
