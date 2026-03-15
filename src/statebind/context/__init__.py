"""Context-to-state prediction: map biological context to structural state relevance.

Phase 4 of StateBind. Given a mutation profile (and optional expression/pathway
features), predict which EGFR conformational state(s) are most relevant for
molecular design.

Modules:
    features    — Feature extraction from mutation records
    preprocessing — Feature scaling, encoding, split generation
    models      — Model definitions (mutation-only, combined, embedding)
    training    — Training loop and hyperparameter handling
    evaluation  — Metrics, calibration, ablation comparison
"""
