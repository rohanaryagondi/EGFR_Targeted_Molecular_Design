# Critical Information -- Dynamics

- The MLP for next-state prediction is hand-rolled numpy, NOT PyTorch -- this module has zero ML library dependencies.
- 16 state sequences are literature-curated pseudo-trajectories, NOT molecular dynamics simulations -- `sequences.py:1-13`.
- State aliases at `sequences.py:25-28`: `_ACT=DFGin_aCin`, `_SRC=DFGin_aCout`, `_OUT=DFGout_aCin`, `_CLS=DFGout_aCout`.
- 4x4 transition matrix (`TransitionMatrix` at `transitions.py:22-29`) uses Laplace smoothing for unseen transitions -- `transitions.py:1-11`.
- `TransitionMatrix.matrix` is row-stochastic: `matrix[i][j] = P(state_j | state_i)` -- `transitions.py:23-25`.
- Contrastive embeddings are 4-dimensional -- `embeddings.py:37-43`. States with frequent transitions are pulled closer in embedding space.
- `EmbeddingSpace.pairwise_distances()` at `embeddings.py:49` computes Euclidean distances between all state pairs.
- `stationary_distribution()` at `transitions.py:43-49` uses power iteration (max 1000 iters, tol 1e-8).
- `StateTransition` dataclass at `sequences.py:32-40` has a `weight` field (confidence weight, default 1.0) used in transition counting.
- `StateSequence.is_synthetic` at `sequences.py:56` flags algorithmically generated sequences vs literature-derived ones.

---

> AI agents: when you discover new critical facts about this module, add them here with file:line references.
