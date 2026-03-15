"""Tests for Phase 4: context-to-state prediction.

Covers:
- Feature extraction correctness
- Preprocessing and scaling
- Split reproducibility
- Model config handling
- Prediction schema
- Evaluation metrics
- Ablation comparison
"""

from __future__ import annotations

import pytest

from statebind.context.features import (
    FeatureSet,
    all_feature_names,
    assign_state_label,
    build_feature_matrix,
    extract_all_features,
    extract_mutation_features,
    extract_pathway_features,
    mutation_feature_names,
    pathway_feature_names,
)
from statebind.context.models import (
    CombinedLogistic,
    EmbeddingMLP,
    ModelConfig,
    MutationOnlyBaseline,
    Prediction,
    create_model,
)
from statebind.context.preprocessing import (
    ScalerParams,
    SplitData,
    fit_scaler,
    generate_splits,
)
from statebind.context.evaluation import (
    compute_accuracy,
    compute_calibration,
    compute_confusion_matrix,
    compute_cross_entropy,
    compute_per_class_metrics,
    evaluate_model,
    evaluation_to_dict,
)
from statebind.context.training import (
    AblationExperiment,
    TrainedModel,
    load_data,
    run_ablation_suite,
    train_model,
)
from statebind.processing.context import build_context_dataset
from statebind.processing.models import ConformationalState


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def context():
    return build_context_dataset(assign_splits=True, split_seed=42)


@pytest.fixture
def mutations(context):
    return context.mutations


@pytest.fixture
def t790m(mutations):
    return next(m for m in mutations if m.mutation_id == "T790M")


@pytest.fixture
def l858r(mutations):
    return next(m for m in mutations if m.mutation_id == "L858R")


# ── Feature extraction tests ─────────────────────────────────────────────

class TestFeatureExtraction:
    def test_mutation_feature_count(self):
        names = mutation_feature_names()
        assert len(names) == 29  # 17 base + 12 mechanism one-hot

    def test_pathway_feature_count(self):
        names = pathway_feature_names()
        assert len(names) == 4

    def test_all_feature_count(self):
        names = all_feature_names()
        assert len(names) == 33  # 29 + 4

    def test_mutation_features_vector_length(self, t790m):
        vec = extract_mutation_features(t790m)
        assert len(vec) == len(mutation_feature_names())

    def test_pathway_features_vector_length(self, t790m):
        vec = extract_pathway_features(t790m)
        assert len(vec) == len(pathway_feature_names())

    def test_all_features_vector_length(self, t790m):
        vec = extract_all_features(t790m)
        assert len(vec) == len(all_feature_names())

    def test_relative_position_in_range(self, t790m):
        vec = extract_mutation_features(t790m)
        rel_pos = vec[0]
        assert 0.0 <= rel_pos <= 1.0

    def test_t790m_is_gatekeeper_mechanism(self, t790m):
        vec = extract_mutation_features(t790m)
        names = mutation_feature_names()
        idx = names.index("mechanism_gatekeeper")
        assert vec[idx] == 1.0

    def test_t790m_has_drugs_affected(self, t790m):
        vec = extract_mutation_features(t790m)
        names = mutation_feature_names()
        idx = names.index("n_drugs_affected")
        assert vec[idx] >= 2.0  # gefitinib, erlotinib

    def test_l858r_is_activating(self, l858r):
        vec = extract_mutation_features(l858r)
        names = mutation_feature_names()
        gen_idx = names.index("generation_ordinal")
        assert vec[gen_idx] == 0.0  # activating = 0

    def test_pathway_features_nonzero_for_known(self, t790m):
        vec = extract_pathway_features(t790m)
        assert any(v > 0 for v in vec)

    def test_hydrophobicity_delta_correct_sign(self, t790m):
        """T790M: T(polar) -> M(hydrophobic), delta should be negative (wt-mut)."""
        vec = extract_mutation_features(t790m)
        names = mutation_feature_names()
        idx = names.index("delta_hydrophobicity")
        # T has lower hydrophobicity than M, so delta = T - M < 0
        assert vec[idx] < 0


class TestLabelAssignment:
    def test_t790m_label_is_dfgin_acin(self, t790m):
        label, dist = assign_state_label(t790m)
        assert label == "DFGin_aCin"

    def test_l858r_label_is_dfgin_acin(self, l858r):
        label, dist = assign_state_label(l858r)
        assert label == "DFGin_aCin"

    def test_known_mutation_has_peaked_distribution(self, t790m):
        label, dist = assign_state_label(t790m)
        assert dist[label] > 0.5

    def test_unknown_mutation_has_uniform_distribution(self, mutations):
        # Find a mutation with no preferred_states
        unknown = next(m for m in mutations if not m.preferred_states)
        label, dist = assign_state_label(unknown)
        # Should be uniform-ish
        assert all(abs(v - 0.25) < 0.01 for v in dist.values())

    def test_distribution_sums_to_one(self, mutations):
        for m in mutations:
            _label, dist = assign_state_label(m)
            assert abs(sum(dist.values()) - 1.0) < 1e-6


class TestFeatureMatrix:
    def test_build_returns_correct_count(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        assert len(fsets) == len(mutations)

    def test_feature_set_has_label(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        for fs in fsets:
            assert fs.label != ""

    def test_feature_set_has_split(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        for fs in fsets:
            assert fs.split in ("train", "val", "test")

    def test_invalid_feature_set_raises(self, mutations):
        with pytest.raises(ValueError, match="Unknown feature_set"):
            build_feature_matrix(mutations, feature_set="invalid")


# ── Preprocessing tests ──────────────────────────────────────────────────

class TestPreprocessing:
    def test_scaler_fit_produces_correct_length(self):
        X = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        scaler = fit_scaler(X, ["a", "b", "c"])
        assert len(scaler.means) == 3
        assert len(scaler.stds) == 3

    def test_scaler_transform_normalizes(self):
        X = [[0.0, 10.0], [2.0, 20.0], [4.0, 30.0]]
        scaler = fit_scaler(X, ["a", "b"])
        transformed = scaler.transform(X)
        # Mean should be ~0
        col0_mean = sum(row[0] for row in transformed) / 3
        assert abs(col0_mean) < 1e-6

    def test_scaler_handles_constant_feature(self):
        X = [[1.0, 5.0], [1.0, 10.0]]
        scaler = fit_scaler(X, ["const", "var"])
        transformed = scaler.transform(X)
        # Constant feature should be 0
        assert transformed[0][0] == 0.0
        assert transformed[1][0] == 0.0


class TestSplitGeneration:
    def test_splits_are_deterministic(self, mutations):
        fsets1 = build_feature_matrix(mutations, feature_set="mutation")
        fsets2 = build_feature_matrix(mutations, feature_set="mutation")
        split1, _ = generate_splits(fsets1, scale=True)
        split2, _ = generate_splits(fsets2, scale=True)
        assert split1.train_ids == split2.train_ids
        assert split1.test_ids == split2.test_ids

    def test_key_mutations_in_test(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        assert "T790M" in split.test_ids
        assert "L858R" in split.test_ids
        assert "C797S" in split.test_ids

    def test_train_not_empty(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        assert len(split.train_X) > 0

    def test_test_not_empty(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        assert len(split.test_X) > 0

    def test_no_id_overlap(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        train_set = set(split.train_ids)
        test_set = set(split.test_ids)
        val_set = set(split.val_ids)
        assert not train_set & test_set
        assert not train_set & val_set
        assert not test_set & val_set

    def test_scaling_returns_scaler(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        _, scaler = generate_splits(fsets, scale=True)
        assert scaler is not None
        assert len(scaler.means) == len(mutation_feature_names())


# ── Model config tests ────────────────────────────────────────────────────

class TestModelConfig:
    def test_default_config(self):
        config = ModelConfig()
        assert config.model_type == "mutation_only"
        assert config.feature_set == "mutation"

    def test_create_model_mutation_only(self):
        config = ModelConfig(model_type="mutation_only")
        model = create_model(config)
        assert isinstance(model, MutationOnlyBaseline)

    def test_create_model_logistic(self):
        config = ModelConfig(model_type="combined_logistic")
        model = create_model(config)
        assert isinstance(model, CombinedLogistic)

    def test_create_model_mlp(self):
        config = ModelConfig(model_type="embedding_mlp")
        model = create_model(config)
        assert isinstance(model, EmbeddingMLP)

    def test_create_model_invalid(self):
        config = ModelConfig(model_type="invalid")
        with pytest.raises(ValueError, match="Unknown model_type"):
            create_model(config)


# ── Prediction schema tests ──────────────────────────────────────────────

class TestPredictionSchema:
    def test_prediction_has_required_fields(self):
        p = Prediction(
            mutation_id="T790M",
            predicted_label="DFGin_aCin",
            probabilities={"DFGin_aCin": 0.7, "DFGin_aCout": 0.1,
                          "DFGout_aCin": 0.1, "DFGout_aCout": 0.1},
            confidence=0.7,
        )
        assert p.mutation_id == "T790M"
        assert p.predicted_label == "DFGin_aCin"
        assert abs(sum(p.probabilities.values()) - 1.0) < 1e-6
        assert p.confidence == 0.7


class TestModelTraining:
    def test_centroid_fit_predict(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        model = MutationOnlyBaseline()
        model.fit(split.train_X, split.train_y)
        preds = model.predict(split.test_X)
        assert len(preds) == len(split.test_X)

    def test_centroid_predict_proba(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="mutation")
        split, _ = generate_splits(fsets)
        model = MutationOnlyBaseline()
        model.fit(split.train_X, split.train_y)
        preds = model.predict_proba(split.test_X, ids=split.test_ids)
        for p in preds:
            assert abs(sum(p.probabilities.values()) - 1.0) < 1e-6
            assert p.confidence > 0

    def test_logistic_fit_predict(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="all")
        split, _ = generate_splits(fsets)
        config = ModelConfig(
            model_type="combined_logistic", feature_set="all",
            n_epochs=20, learning_rate=0.01,
        )
        model = CombinedLogistic(config)
        model.fit(split.train_X, split.train_y)
        preds = model.predict(split.test_X)
        assert len(preds) == len(split.test_X)

    def test_mlp_fit_predict(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="all")
        split, _ = generate_splits(fsets)
        config = ModelConfig(
            model_type="embedding_mlp", feature_set="all",
            n_epochs=20, hidden_dim=8,
        )
        model = EmbeddingMLP(config)
        model.fit(split.train_X, split.train_y)
        preds = model.predict(split.test_X)
        assert len(preds) == len(split.test_X)

    def test_mlp_get_embeddings(self, mutations):
        fsets = build_feature_matrix(mutations, feature_set="all")
        split, _ = generate_splits(fsets)
        config = ModelConfig(
            model_type="embedding_mlp", feature_set="all",
            n_epochs=20, hidden_dim=8,
        )
        model = EmbeddingMLP(config)
        model.fit(split.train_X, split.train_y)
        embeddings = model.get_embeddings(split.test_X)
        assert len(embeddings) == len(split.test_X)
        assert len(embeddings[0]) == 8  # hidden_dim

    def test_unfitted_model_raises(self):
        model = MutationOnlyBaseline()
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict_proba([[1.0, 2.0]])


# ── Evaluation tests ─────────────────────────────────────────────────────

class TestEvaluation:
    def test_accuracy_perfect(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="X",
                      probabilities={"X": 1.0}, confidence=1.0),
            Prediction(mutation_id="b", predicted_label="Y",
                      probabilities={"Y": 1.0}, confidence=1.0),
        ]
        acc = compute_accuracy(preds, ["X", "Y"])
        assert acc == 1.0

    def test_accuracy_zero(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="Y",
                      probabilities={"Y": 1.0}, confidence=1.0),
        ]
        acc = compute_accuracy(preds, ["X"])
        assert acc == 0.0

    def test_cross_entropy_perfect(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="X",
                      probabilities={"X": 0.99, "Y": 0.01}, confidence=0.99),
        ]
        ce = compute_cross_entropy(preds, ["X"])
        assert ce < 0.1  # low loss for high-confidence correct

    def test_confusion_matrix_shape(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="X",
                      probabilities={"X": 0.7, "Y": 0.3}, confidence=0.7),
        ]
        cm = compute_confusion_matrix(preds, ["X"], ["X", "Y"])
        assert len(cm) == 4  # 2x2

    def test_per_class_metrics(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="X",
                      probabilities={"X": 1.0}, confidence=1.0),
            Prediction(mutation_id="b", predicted_label="X",
                      probabilities={"X": 1.0}, confidence=1.0),
        ]
        metrics = compute_per_class_metrics(preds, ["X", "Y"], ["X", "Y"])
        x_metrics = next(m for m in metrics if m.label == "X")
        assert x_metrics.precision == 0.5  # 1 TP, 1 FP
        assert x_metrics.recall == 1.0  # 1 TP, 0 FN

    def test_calibration_returns_bins(self):
        preds = [
            Prediction(mutation_id="a", predicted_label="X",
                      probabilities={"X": 0.9}, confidence=0.9),
        ]
        ece, bins = compute_calibration(preds, ["X"], n_bins=5)
        assert len(bins) == 5
        assert ece >= 0.0

    def test_evaluation_to_dict_has_keys(self, context):
        config = ModelConfig(model_type="mutation_only", feature_set="mutation")
        trained = train_model(context, config)
        result = evaluate_model(trained, "test")
        d = evaluation_to_dict(result)
        assert "accuracy" in d
        assert "predictions" in d
        assert "confusion_matrix" in d
        assert "calibration" in d


# ── Training orchestration tests ──────────────────────────────────────────

class TestTrainingOrchestration:
    def test_train_model_returns_trained(self, context):
        config = ModelConfig(model_type="mutation_only", feature_set="mutation")
        trained = train_model(context, config)
        assert isinstance(trained, TrainedModel)
        assert trained.model.fitted
        assert len(trained.test_predictions) > 0

    def test_ablation_suite_runs_all(self, context):
        experiments = run_ablation_suite(context)
        assert len(experiments) == 6
        for exp in experiments:
            assert exp.trained is not None
            assert exp.trained.model.fitted

    def test_ablation_suite_deterministic(self, context):
        exp1 = run_ablation_suite(context)
        exp2 = run_ablation_suite(context)
        for e1, e2 in zip(exp1, exp2):
            assert e1.trained is not None
            assert e2.trained is not None
            preds1 = [p.predicted_label for p in e1.trained.test_predictions]
            preds2 = [p.predicted_label for p in e2.trained.test_predictions]
            assert preds1 == preds2
