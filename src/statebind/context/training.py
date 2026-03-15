"""Training orchestration for context-to-state models.

Handles:
- Data loading and preprocessing
- Model creation and training
- Artifact serialization
- Ablation experiment setup
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from statebind.context.features import build_feature_matrix
from statebind.context.models import (
    CombinedLogistic,
    EmbeddingMLP,
    ModelConfig,
    MutationOnlyBaseline,
    Prediction,
    create_model,
)
from statebind.context.preprocessing import ScalerParams, SplitData, generate_splits
from statebind.processing.context import build_context_dataset
from statebind.processing.models import ContextDataset


@dataclass
class TrainedModel:
    """Container for a trained model with metadata."""

    model: MutationOnlyBaseline | CombinedLogistic | EmbeddingMLP
    config: ModelConfig
    split_data: SplitData
    scaler: ScalerParams | None
    train_predictions: list[Prediction] = field(default_factory=list)
    val_predictions: list[Prediction] = field(default_factory=list)
    test_predictions: list[Prediction] = field(default_factory=list)


@dataclass
class AblationExperiment:
    """A single ablation experiment result."""

    name: str
    feature_set: str
    model_type: str
    config: ModelConfig
    trained: TrainedModel | None = None


def load_data(split_seed: int = 42) -> ContextDataset:
    """Load the context dataset with splits assigned."""
    return build_context_dataset(assign_splits=True, split_seed=split_seed)


def train_model(
    context: ContextDataset,
    config: ModelConfig,
) -> TrainedModel:
    """Train a single context-to-state model.

    Args:
        context: Context dataset with mutations and splits.
        config: Model configuration.

    Returns:
        TrainedModel with predictions on all splits.
    """
    # Extract features
    feature_sets = build_feature_matrix(
        context.mutations, feature_set=config.feature_set
    )

    # Generate splits
    split_data, scaler = generate_splits(feature_sets, scale=True)

    # Create and train model
    model = create_model(config)
    model.fit(split_data.train_X, split_data.train_y)

    # Predict on all splits
    train_preds = model.predict_proba(split_data.train_X, ids=split_data.train_ids)
    val_preds = (
        model.predict_proba(split_data.val_X, ids=split_data.val_ids)
        if split_data.val_X else []
    )
    test_preds = (
        model.predict_proba(split_data.test_X, ids=split_data.test_ids)
        if split_data.test_X else []
    )

    return TrainedModel(
        model=model,
        config=config,
        split_data=split_data,
        scaler=scaler,
        train_predictions=train_preds,
        val_predictions=val_preds,
        test_predictions=test_preds,
    )


def run_ablation_suite(
    context: ContextDataset,
) -> list[AblationExperiment]:
    """Run the full ablation experiment suite.

    Experiments:
    1. Mutation-only features + nearest centroid
    2. Pathway-only features + nearest centroid
    3. Combined features + nearest centroid
    4. Mutation-only features + logistic regression
    5. Combined features + logistic regression
    6. Combined features + embedding MLP

    Returns:
        List of AblationExperiment objects with trained models.
    """
    experiments = [
        AblationExperiment(
            name="mutation_only_centroid",
            feature_set="mutation",
            model_type="mutation_only",
            config=ModelConfig(
                model_type="mutation_only", feature_set="mutation"
            ),
        ),
        AblationExperiment(
            name="pathway_only_centroid",
            feature_set="pathway",
            model_type="mutation_only",
            config=ModelConfig(
                model_type="mutation_only", feature_set="pathway"
            ),
        ),
        AblationExperiment(
            name="combined_centroid",
            feature_set="all",
            model_type="mutation_only",
            config=ModelConfig(
                model_type="mutation_only", feature_set="all"
            ),
        ),
        AblationExperiment(
            name="mutation_only_logistic",
            feature_set="mutation",
            model_type="combined_logistic",
            config=ModelConfig(
                model_type="combined_logistic", feature_set="mutation",
                learning_rate=0.01, n_epochs=150, l2_reg=0.01,
            ),
        ),
        AblationExperiment(
            name="combined_logistic",
            feature_set="all",
            model_type="combined_logistic",
            config=ModelConfig(
                model_type="combined_logistic", feature_set="all",
                learning_rate=0.01, n_epochs=150, l2_reg=0.01,
            ),
        ),
        AblationExperiment(
            name="combined_embedding_mlp",
            feature_set="all",
            model_type="embedding_mlp",
            config=ModelConfig(
                model_type="embedding_mlp", feature_set="all",
                learning_rate=0.005, n_epochs=200, hidden_dim=16,
                l2_reg=0.005, random_seed=42,
            ),
        ),
    ]

    for exp in experiments:
        exp.trained = train_model(context, exp.config)

    return experiments


def save_predictions(
    predictions: list[Prediction],
    output_path: Path,
) -> None:
    """Save predictions to JSON."""
    data = [
        {
            "mutation_id": p.mutation_id,
            "predicted_label": p.predicted_label,
            "probabilities": p.probabilities,
            "confidence": p.confidence,
        }
        for p in predictions
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def save_model_config(config: ModelConfig, output_path: Path) -> None:
    """Save model config to JSON."""
    data = {
        "model_type": config.model_type,
        "feature_set": config.feature_set,
        "learning_rate": config.learning_rate,
        "n_epochs": config.n_epochs,
        "hidden_dim": config.hidden_dim,
        "dropout": config.dropout,
        "l2_reg": config.l2_reg,
        "random_seed": config.random_seed,
        "temperature": config.temperature,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
