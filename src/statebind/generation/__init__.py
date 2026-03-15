"""Generation module: state-conditioned molecular candidate generation.

Phase 6 of StateBind. Generates candidate molecules conditioned on structural
state and pocket context. Each state's pocket geometry drives different
modifications, producing state-specific candidate sets.

Key difference from static baseline (Phase 2):
- Phase 2 generates against a SINGLE structure (1M17, active state)
- Phase 6 generates against ALL 4 conformational states, with pocket-aware
  modifications tailored to each state's geometry

Modules:
    models        — Pydantic models for state-conditioned candidates
    conditioning  — Pocket-to-modification mapping logic
    generator     — State-conditioned candidate generation
    filtering     — Chemistry filtering with state-aware rules
    diversity     — Intra-state and cross-state diversity analysis
    evaluation    — Generation quality metrics per state
"""
