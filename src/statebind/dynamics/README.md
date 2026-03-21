# statebind.dynamics

## Purpose

Phase 5 of StateBind: models the conformational state transition dynamics of EGFR kinase. Constructs literature-curated state sequences (not MD trajectories), estimates Markov transition matrices with Laplace smoothing, learns latent state embeddings via a contrastive-style objective, and trains an MLP-based world model for next-state prediction. Provides a compact "world model" that downstream state-conditioned molecular design can query for state distributions and transition probabilities.

## Public API

| Symbol | Signature | Description |
|--------|-----------|-------------|
| `StateTransition` | `@dataclass(from_state, to_state, context, evidence_type, reference, weight)` | A single observed or inferred state-to-state transition. |
| `StateSequence` | `@dataclass(sequence_id, states, description, provenance, context, is_synthetic)` | An ordered sequence of conformational state visits. |
| `TransitionDataset` | `@dataclass(sequences, transitions, n_sequences, n_transitions, states, generated_at, version, notes)` | Collection of state sequences and pairwise transitions. |
| `build_transition_dataset()` | `() -> TransitionDataset` | Build the complete transition dataset from curated sequences. |
| `extract_transitions()` | `(sequences: list[StateSequence]) -> list[StateTransition]` | Extract all pairwise transitions from state sequences. |
| `TransitionMatrix` | `@dataclass(states, matrix, counts)` | Row-stochastic transition matrix P(to \| from) with `.get_prob()`, `.get_row()`, `.stationary_distribution()`. |
| `TransitionPrediction` | `@dataclass(from_state, predicted_state, probabilities, confidence, model_name)` | Prediction for the next state given current state. |
| `estimate_transition_matrix()` | `(transitions, states, smoothing=1.0) -> TransitionMatrix` | Estimate transition matrix from observed transitions with Laplace smoothing. |
| `UniformBaseline` | `__init__(states: list[str])` | Baseline model: uniform random transition to any state. Methods: `.predict()`, `.predict_sequence()`, `.log_likelihood()`. |
| `MarkovTransitionModel` | `__init__(states: list[str], smoothing: float = 1.0)` | First-order Markov model with Laplace-smoothed transition matrix. Methods: `.fit()`, `.predict()`, `.predict_sequence()`, `.log_likelihood()`, `.get_stationary()`. |
| `StateEmbedding` | `@dataclass(state, vector, dim)` | Embedding vector for a single conformational state. |
| `EmbeddingSpace` | `@dataclass(embeddings, dim, training_loss, states)` | Collection of state embeddings with `.get_vector()`, `.pairwise_distances()`, `.nearest_state()`. |
| `learn_embeddings()` | `(trans_matrix, dim=4, n_epochs=200, learning_rate=0.05, seed=42, feature_centroids=None) -> EmbeddingSpace` | Learn state embeddings that respect transition geometry via SGD. |
| `WorldModelConfig` | `@dataclass(model_type, embedding_dim, embedding_epochs, embedding_lr, mlp_hidden, mlp_epochs, mlp_lr, smoothing, random_seed)` | Configuration for the world model pipeline. |
| `WorldModelOutput` | `@dataclass(config, transition_dataset, transition_matrix, embeddings, stationary_distribution, model_name, test_predictions, train_log_likelihood, test_log_likelihood)` | Complete output from the world model pipeline. |
| `LearnedWorldModel` | `__init__(states: list[str], config: WorldModelConfig)` | MLP-based world model on state embeddings. Methods: `.fit(transitions, embeddings)`, `.predict(from_state, embeddings)`, `.log_likelihood(transitions, embeddings)`. |
| `build_world_model()` | `(config: WorldModelConfig \| None = None) -> WorldModelOutput` | Build the complete world model pipeline (dataset, matrix, embeddings, model, evaluation). |
| `save_world_model()` | `(output: WorldModelOutput, artifact_dir: Path) -> list[Path]` | Save all world model artifacts to disk. |
| `compute_transition_accuracy()` | `(predictions, true_transitions) -> float` | Fraction of transitions where predicted_state matches actual next state. |
| `compute_perplexity()` | `(log_likelihood: float) -> float` | Perplexity = exp(-avg_log_likelihood). |
| `evaluate_transition_model()` | `(model_name, predictions, true_transitions, log_likelihood) -> TransitionMetrics` | Evaluate a transition model and return metrics. |
| `evaluate_embedding_quality()` | `(embeddings, trans_matrix) -> EmbeddingMetrics` | Evaluate how well embeddings reflect transition geometry (Pearson correlation). |
| `compare_models()` | `(dataset_transitions, states, embeddings=None, smoothing=1.0, seed=42) -> ModelComparison` | Compare uniform, Markov, and learned models on train/test split. |
| `metrics_to_dict()` | `(metrics: TransitionMetrics) -> dict` | Serialize transition metrics. |
| `embedding_metrics_to_dict()` | `(metrics: EmbeddingMetrics) -> dict` | Serialize embedding metrics. |

## Internal Files

| File | Responsibility |
|------|---------------|
| `__init__.py` | Package docstring and module-level documentation. |
| `sequences.py` | Literature-curated EGFR state sequences (16 canonical sequences), `StateTransition`/`StateSequence`/`TransitionDataset` dataclasses, `extract_transitions()`, `build_transition_dataset()`. |
| `transitions.py` | Transition matrix estimation with Laplace smoothing, `UniformBaseline` and `MarkovTransitionModel` classes, stationary distribution computation via power iteration. |
| `embeddings.py` | Latent state embedding learning with contrastive-style SGD objective. Initializes via random projection from feature centroids or random init. |
| `world_model.py` | Unified world model combining all components. Contains `LearnedWorldModel` (hand-rolled MLP: Embedding -> Linear -> ReLU -> Linear -> Softmax), `build_world_model()` pipeline, and `save_world_model()` artifact serialization. |
| `evaluation.py` | Evaluation metrics: accuracy, log-likelihood, perplexity, embedding geometry quality, and multi-model comparison. |

## Dependencies

- **Imports from:** `statebind.processing.models` (`ConformationalState` enum used in `sequences.py` for state aliases)
- **Imported by:** None directly. Consumed downstream via serialized JSON artifacts (transition matrix, embeddings, stationary distribution).

## Data Flow

**Reads:**
- No external config files. All state sequences are hardcoded from literature curation in `sequences.py`.

**Produces (via `save_world_model()`):**
- `transition_matrix.json` -- row-stochastic matrix with states, probabilities, and raw counts
- `sequences.json` -- all curated state sequences with provenance
- `transition_summary.json` -- per-pair transition counts and probabilities
- `state_embeddings.json` -- learned embedding vectors, pairwise distances, final training loss
- `stationary_distribution.json` -- equilibrium state distribution
- `evaluation.json` -- model name, train/test log-likelihood, dataset sizes
- `config.json` -- model configuration used

## Testing

- **Test file:** `tests/test_dynamics.py`
- **Run:** `pytest tests/test_dynamics.py -v`
- **Key fixtures:** `dataset` (calls `build_transition_dataset()`), `states`, `transitions`, `trans_matrix` (estimated from full dataset)
- **Test classes:** `TestSequenceBuilder` (16 sequences, provenance, extraction), `TestTransitionDataset` (integrity), `TestTransitionMatrix` (row-stochastic, no zeros, stationary), `TestModelSchemas`, `TestUniformBaseline`, `TestMarkovModel` (fit/predict, beats uniform, unfitted raises), `TestEmbeddings` (dimensionality, distances, loss decreases), `TestMetrics` (accuracy, perplexity, embedding quality), `TestLearnedModel`, `TestWorldModelPipeline` (all 3 model types, save/load, determinism, comparison)

## Patterns to Follow

- All state sequences must have a `provenance` field documenting their literature source (or `is_synthetic=True`).
- The `LearnedWorldModel` in `world_model.py` uses a hand-rolled MLP with Xavier initialization, manual forward/backward passes, and softmax output. This pattern (no NumPy/PyTorch dependency) is the template for the docking proxy model in Workstream 04.
- Helper functions `_softmax()` and `_dot()` in `world_model.py` are the reusable math primitives.
- Transition matrix always uses Laplace smoothing (default `smoothing=1.0`) to avoid zero probabilities.
- All pipeline functions are deterministic given a `random_seed` parameter.

## Known Limitations

- State sequences are literature-curated pseudo-trajectories, **not** molecular dynamics simulations. The module docstrings are explicit about this.
- Only 4 EGFR conformational states are modeled (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout).
- The MLP world model has a small architecture (default hidden=8) due to the small state space (4 states). It may not significantly outperform the Markov model.
- Embedding learning uses a simple contrastive-style loss on 6 state pairs; with only 4 states the geometry is highly constrained.
- No external data loading -- all sequences are hardcoded.

## Planned Improvements

- No workstreams currently plan to modify this module directly.
- Workstream 04 (docking proxy) will reuse the hand-rolled MLP pattern from `world_model.py` as a template for the docking scoring model.
