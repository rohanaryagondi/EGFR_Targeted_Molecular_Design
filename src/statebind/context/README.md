# statebind.context

## Purpose

Mutation-to-state prediction module (Phase 4). Given an EGFR mutation profile (and optional pathway activation proxy features), this module predicts which conformational state(s) are most relevant for molecular design. It provides feature extraction from mutation records, feature preprocessing and scaling, three model tiers (nearest-centroid, logistic regression, embedding MLP), a training pipeline with ablation experiments, and comprehensive evaluation metrics including calibration analysis.

## Public API

| Symbol | Type | Signature | Description |
|--------|------|-----------|-------------|
| `extract_mutation_features` | function | `(m: MutationRecord) -> list[float]` | Extract mutation-only numeric feature vector (position, AA properties, mechanism, resistance gen) |
| `extract_pathway_features` | function | `(m: MutationRecord) -> list[float]` | Extract pathway proxy features (MAPK, PI3K, STAT3, Src activation scores) |
| `extract_all_features` | function | `(m: MutationRecord) -> list[float]` | Extract combined mutation + pathway feature vector |
| `mutation_feature_names` | function | `() -> list[str]` | Return ordered list of mutation-only feature names (17 base + 12 mechanism one-hot) |
| `pathway_feature_names` | function | `() -> list[str]` | Return ordered list of pathway proxy feature names (4 pathways) |
| `all_feature_names` | function | `() -> list[str]` | Return ordered list of all feature names (mutation + pathway) |
| `assign_state_label` | function | `(m: MutationRecord) -> tuple[str, dict[str, float]]` | Assign a primary conformational state label and soft label distribution to a mutation |
| `build_feature_matrix` | function | `(mutations: list[MutationRecord], feature_set: str = "all") -> list[FeatureSet]` | Build feature matrix from mutation records for a given feature set ("mutation", "pathway", "all") |
| `FeatureSet` | dataclass | fields: `mutation_id`, `feature_names`, `values`, `label`, `label_distribution`, `split` | Container for features extracted from a single mutation |
| `fit_scaler` | function | `(X: list[list[float]], feature_names: list[str]) -> ScalerParams` | Fit a standard scaler (mean=0, std=1) on training data |
| `generate_splits` | function | `(feature_sets: list[FeatureSet], scale: bool = True) -> tuple[SplitData, ScalerParams \| None]` | Generate train/val/test splits from pre-assigned FeatureSets with optional scaling |
| `SplitData` | dataclass | -- | Train/val/test split with feature matrices, labels, soft distributions, and IDs |
| `ScalerParams` | dataclass | method: `transform(X) -> list[list[float]]` | Standard scaler parameters with transform method |
| `MutationOnlyBaseline` | class | `fit(X, y)`, `predict(X)`, `predict_proba(X, ids)` | Nearest-centroid classifier using inverse-distance weighted probabilities |
| `CombinedLogistic` | class | `fit(X, y)`, `predict(X)`, `predict_proba(X, ids)` | Multinomial logistic regression with L2 regularization, trained by SGD |
| `EmbeddingMLP` | class | `fit(X, y)`, `predict(X)`, `predict_proba(X, ids)`, `get_embeddings(X)` | Single hidden-layer MLP with ReLU, Xavier init, and learned mutation embedding |
| `create_model` | function | `(config: ModelConfig) -> MutationOnlyBaseline \| CombinedLogistic \| EmbeddingMLP` | Factory function to create a model from config |
| `ModelConfig` | dataclass | fields: `model_type`, `feature_set`, `learning_rate`, `n_epochs`, `hidden_dim`, `dropout`, `l2_reg`, `random_seed`, `temperature` | Model hyperparameter configuration |
| `Prediction` | dataclass | fields: `mutation_id`, `predicted_label`, `probabilities`, `confidence` | Single prediction with label and probability distribution |
| `train_model` | function | `(context: ContextDataset, config: ModelConfig) -> TrainedModel` | Train a single context-to-state model end-to-end |
| `run_ablation_suite` | function | `(context: ContextDataset) -> list[AblationExperiment]` | Run 6 ablation experiments (3 feature sets x 3 model types) |
| `load_data` | function | `(split_seed: int = 42) -> ContextDataset` | Load the context dataset with train/val/test splits assigned |
| `save_predictions` | function | `(predictions: list[Prediction], output_path: Path) -> None` | Save predictions to JSON |
| `save_model_config` | function | `(config: ModelConfig, output_path: Path) -> None` | Save model config to JSON |
| `TrainedModel` | dataclass | fields: `model`, `config`, `split_data`, `scaler`, `train_predictions`, `val_predictions`, `test_predictions` | Container for a trained model with all predictions |
| `AblationExperiment` | dataclass | fields: `name`, `feature_set`, `model_type`, `config`, `trained` | A single ablation experiment result |
| `evaluate_model` | function | `(trained: TrainedModel, split: str = "test") -> EvaluationResult` | Full evaluation: accuracy, precision/recall/F1, confusion matrix, calibration, cross-entropy |
| `compare_ablations` | function | `(experiments: list[AblationExperiment], eval_split: str = "test") -> AblationComparison` | Compare ablation experiments on a given split |
| `compute_accuracy` | function | `(predictions: list[Prediction], true_labels: list[str]) -> float` | Compute classification accuracy |
| `compute_cross_entropy` | function | `(predictions: list[Prediction], true_labels: list[str]) -> float` | Compute cross-entropy loss |
| `compute_confusion_matrix` | function | `(predictions: list[Prediction], true_labels: list[str], class_labels: list[str]) -> list[ConfusionEntry]` | Compute confusion matrix |
| `compute_per_class_metrics` | function | `(predictions: list[Prediction], true_labels: list[str], class_labels: list[str]) -> list[ClassMetrics]` | Compute per-class precision, recall, F1 |
| `compute_calibration` | function | `(predictions: list[Prediction], true_labels: list[str], n_bins: int = 5) -> tuple[float, list[CalibrationBin]]` | Compute expected calibration error and calibration bins |
| `evaluation_to_dict` | function | `(result: EvaluationResult) -> dict` | Serialize evaluation result to a JSON-friendly dict |
| `EvaluationResult` | dataclass | -- | Complete evaluation result for a model on a split |
| `AblationComparison` | dataclass | fields: `rows`, `best_model`, `best_accuracy` | Comparison table across ablation experiments |

## Internal Files

| File | Responsibility |
|------|---------------|
| `features.py` | Feature extraction from MutationRecord: amino acid property tables (hydrophobicity, volume, charge, MW), mechanism one-hot encoding, resistance generation ordinal, pathway proxy scores, state label assignment with soft distributions |
| `preprocessing.py` | Standard scaling (fit on train only), train/val/test split generation from pre-assigned splits, SplitData and ScalerParams containers |
| `models.py` | Three model implementations (MutationOnlyBaseline, CombinedLogistic, EmbeddingMLP) with shared fit/predict/predict_proba interface; softmax, dot product, and Euclidean distance utilities; ModelConfig and Prediction dataclasses |
| `training.py` | Training orchestration: data loading, model creation and fitting, prediction generation on all splits, ablation suite (6 experiments), artifact serialization |
| `evaluation.py` | Accuracy, cross-entropy, confusion matrix, per-class precision/recall/F1, expected calibration error (ECE), ablation comparison, serialization to dict |
| `__init__.py` | Package docstring listing submodules |

## Dependencies

- **Imports from:** `statebind.processing.context` (build_context_dataset), `statebind.processing.models` (MutationRecord, ConformationalState, MechanismCategory, ResistanceGeneration, ContextDataset)
- **External:** None (all models implemented from scratch with only `math` and `random` from stdlib)
- **Imported by:** downstream phases that need state predictions for conditioned generation

## Data Flow

**Reads:**
- Context dataset via `statebind.processing.context.build_context_dataset()`
- Curated pathway proxy scores from internal `_PATHWAY_SCORES` lookup table in `features.py`
- Amino acid property tables (Kyte-Doolittle hydrophobicity, residue volumes, charges, molecular weights) in `features.py`

**Produces:**
- `TrainedModel` objects with predictions on train/val/test splits
- Prediction JSON files via `save_predictions()`
- Model config JSON files via `save_model_config()`
- `EvaluationResult` and `AblationComparison` artifacts

## Testing

- **Test file:** `tests/test_context.py`
- **Run:** `pytest tests/test_context.py -v`
- **Key fixtures:** Tests use direct imports from all submodules; no external fixtures required
- **Coverage:** Feature extraction correctness, preprocessing and scaling, split reproducibility, model config handling, prediction schema, evaluation metrics (accuracy, cross-entropy, confusion matrix, per-class metrics, calibration), ablation comparison

## Patterns to Follow

- All three models share a common interface: `fit(X, y) -> self`, `predict(X) -> list[str]`, `predict_proba(X, ids) -> list[Prediction]`.
- Feature vectors maintain consistent ordering via `*_feature_names()` functions.
- Scaling is always fit on the training split only, then applied to val/test.
- State labels include both a hard label (primary state) and a soft distribution across all 4 states.
- Models are created via the `create_model(config)` factory function.
- Temperature-scaled softmax is used for calibrated probability outputs.

## Known Limitations

- **Single-class dataset:** All 17 curated mutations map to `DFGin_aCin` (the active state). The model cannot learn to discriminate between states from this data alone.
- **Pathway features are proxies:** The 4 pathway activation scores (MAPK, PI3K, STAT3, Src) are hand-curated proxy values, not real expression or pathway data.
- **No external ML library:** Models are implemented from scratch (no PyTorch, scikit-learn) which limits complexity and training efficiency.
- **Small dataset:** 17 mutations total, split across train/val/test, severely limits what any model can learn.
- **Soft labels are heuristic:** The 0.7/0.3 split for preferred/non-preferred states is an assumption, not empirically calibrated.

## Planned Improvements

No currently planned workstream modifications targeting this module directly. Future improvements would involve expanding the mutation dataset with multi-state annotations and replacing proxy pathway features with real expression data.
