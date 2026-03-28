"""ADMET safety filter for candidate molecules.

Runs the MultiTaskADMET model on each candidate and flags or removes those
that fail critical ADMET thresholds.  Designed to slot into the filtering
pipeline after property-based filtering (``generation/filtering.py``).

When the ADMET model is unavailable, all candidates pass through unmodified
with ``n_skipped == n_input`` in the summary.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from pydantic import BaseModel, Field

from statebind.generation.models import StateConditionedCandidate

logger = logging.getLogger(__name__)


class ADMETFilterResult(BaseModel):
    """ADMET filter outcome for a single candidate."""

    candidate_id: str
    smiles: str
    predictions: dict[str, float] = Field(default_factory=dict)
    passed: bool = True
    failed_tasks: list[str] = Field(default_factory=list)


class ADMETFilterSummary(BaseModel):
    """Aggregate ADMET filtering statistics."""

    n_input: int = 0
    n_passed: int = 0
    n_failed: int = 0
    n_skipped: int = 0
    pass_rate: float = 0.0
    failure_counts: dict[str, int] = Field(default_factory=dict)
    results: list[ADMETFilterResult] = Field(default_factory=list)


def filter_candidates_admet(
    candidates: list[StateConditionedCandidate],
    thresholds: dict[str, tuple[str, float]] | None = None,
    remove_failures: bool = False,
) -> tuple[list[StateConditionedCandidate], ADMETFilterSummary]:
    """Apply ADMET safety filtering to a candidate list.

    Args:
        candidates: Input candidates to filter.
        thresholds: Per-task thresholds (see
            :func:`~statebind.ml.admet_predictor.check_admet_pass`).
        remove_failures: If ``True``, exclude failing candidates from
            output.  If ``False`` (default), include all but flag failures.

    Returns:
        ``(filtered_candidates, summary)``.  When the model is unavailable,
        returns all candidates with ``n_skipped == n_input``.
    """
    n_input = len(candidates)
    if n_input == 0:
        return [], ADMETFilterSummary()

    # Lazy import — keeps Pydantic models importable without torch
    try:
        from statebind.ml.admet_predictor import check_admet_pass, predict_admet_batch
    except ImportError:
        logger.info("ADMET predictor not available — skipping ADMET filter")
        return candidates, ADMETFilterSummary(
            n_input=n_input, n_skipped=n_input,
        )

    try:
        smiles_list = [c.smiles for c in candidates]
        all_predictions = predict_admet_batch(smiles_list)

        results: list[ADMETFilterResult] = []
        output: list[StateConditionedCandidate] = []
        n_passed = 0
        n_failed = 0
        n_skipped = 0
        failure_counts: dict[str, int] = defaultdict(int)

        for candidate, preds in zip(candidates, all_predictions):
            if not preds:
                # Model returned empty — SMILES failed or model unavailable
                results.append(ADMETFilterResult(
                    candidate_id=candidate.candidate_id,
                    smiles=candidate.smiles,
                ))
                n_skipped += 1
                output.append(candidate)
                continue

            passed, failed_tasks = check_admet_pass(preds, thresholds)

            results.append(ADMETFilterResult(
                candidate_id=candidate.candidate_id,
                smiles=candidate.smiles,
                predictions=preds,
                passed=passed,
                failed_tasks=failed_tasks,
            ))

            if passed:
                n_passed += 1
                output.append(candidate)
            else:
                n_failed += 1
                for task in failed_tasks:
                    failure_counts[task] += 1
                if not remove_failures:
                    output.append(candidate)

        summary = ADMETFilterSummary(
            n_input=n_input,
            n_passed=n_passed,
            n_failed=n_failed,
            n_skipped=n_skipped,
            pass_rate=round(n_passed / max(n_input, 1), 4),
            failure_counts=dict(failure_counts),
            results=results,
        )
        return output, summary

    except Exception:
        logger.warning("ADMET filter failed — passing all candidates", exc_info=True)
        return candidates, ADMETFilterSummary(
            n_input=n_input, n_skipped=n_input,
        )
