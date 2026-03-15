"""Dynamics module: conformational state transition modeling for EGFR.

Phase 5 of StateBind. Models relationships and transitions between EGFR
conformational states. Provides a compact "world model" that downstream
state-conditioned molecular design can query.

Key concepts:
- State sequences: ordered state visits (constructed from literature)
- Transition matrix: P(state_j | state_i) probabilities
- Latent embeddings: compact representations respecting transition geometry
- Next-state prediction: given current state, forecast plausible next states

Modules:
    sequences   — State sequence construction and representation
    transitions — Transition matrix estimation and Markov model
    embeddings  — Latent state embedding learning
    world_model — Unified world model combining all components
    evaluation  — Metrics for transition prediction quality
"""
