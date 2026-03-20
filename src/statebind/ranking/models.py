"""Data models for the unified ranking pipeline.

All models are Pydantic v2 for schema validation and serialization.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class PipelineLabel(str, Enum):
    """Which pipeline produced the candidate."""

    STATIC = "static_baseline"
    STATE_AWARE = "state_aware"


class UnifiedScoreComponent(BaseModel):
    """A single scoring axis applied identically to both pipelines."""

    name: str
    value: float
    weight: float = Field(default=1.0)
    method: str = Field(default="")
    is_stub: bool = Field(default=False)


class UnifiedScoredCandidate(BaseModel):
    """A candidate scored under the unified scheme."""

    candidate_id: str
    smiles: str
    pipeline: PipelineLabel
    target_state: str = Field(default="", description="Empty for static baseline")
    strategy: str = Field(default="", description="Generation strategy or 'static'")
    scores: list[UnifiedScoreComponent] = Field(default_factory=list)
    composite_score: float = Field(default=0.0)
    rank_in_pipeline: int = Field(default=0, description="Rank within own pipeline")
    global_rank: int = Field(default=0, description="Rank in merged pool")

    def get_score(self, name: str) -> float | None:
        for s in self.scores:
            if s.name == name:
                return s.value
        return None


class RankedPool(BaseModel):
    """Ranked candidates from a single pipeline."""

    pipeline: PipelineLabel
    scoring_method: str = Field(default="")
    candidates: list[UnifiedScoredCandidate] = Field(default_factory=list)
    generated_at: str = Field(default="")
    notes: str = Field(default="")

    @property
    def n_ranked(self) -> int:
        return len(self.candidates)


class MergedRanking(BaseModel):
    """Merged ranking of candidates from both pipelines."""

    static_pool: RankedPool
    state_aware_pool: RankedPool
    merged: list[UnifiedScoredCandidate] = Field(default_factory=list)
    generated_at: str = Field(default="")
    notes: str = Field(default="")

    @property
    def n_total(self) -> int:
        return len(self.merged)


class RankShift(BaseModel):
    """How a candidate's rank changed from pipeline-local to global."""

    candidate_id: str
    smiles: str
    pipeline: PipelineLabel
    pipeline_rank: int
    global_rank: int
    shift: int = Field(description="pipeline_rank - global_rank; positive = promoted")
    composite_score: float = Field(default=0.0)
