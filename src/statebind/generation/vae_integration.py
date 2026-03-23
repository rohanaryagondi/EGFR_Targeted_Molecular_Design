"""Convert VAE-generated candidates to StateConditionedCandidate objects.

Reads the JSON artifact produced by ``scripts/generate_vae_candidates.py``
and wraps each valid candidate as a :class:`StateConditionedCandidate` for
the ranking pipeline.  No torch dependency — pure JSON→Pydantic mapping.

Integration point: the resulting candidates can be merged into the
state-aware candidate pool before ``ranking/scoring.py:rank_state_aware()``
scores them alongside template-generated candidates.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from statebind.baselines.models import CandidateSource
from statebind.generation.models import (
    GenerationStrategy,
    StateConditionedCandidate,
    StateConditionedLibrary,
)
from statebind.ml.vae_dataset import DEFAULT_STATE_MAPPING
from statebind.utils.io import load_json

logger = logging.getLogger(__name__)

_VALID_STATES = set(DEFAULT_STATE_MAPPING.keys())


def load_vae_candidates(
    path: Path | str,
) -> list[StateConditionedCandidate]:
    """Load VAE candidates from JSON and wrap as StateConditionedCandidate.

    Reads the JSON artifact at *path*, which must have a ``"candidates"``
    key containing a list of objects with ``"smiles"`` and ``"state"``
    fields (plus optional ``"is_valid"``, ``"is_novel"``, ``"source"``).

    Candidates with ``is_valid == False`` are filtered out.  Invalid
    state labels raise :class:`ValueError`.

    Each candidate gets:
        - ``source = CandidateSource.ML_GENERATED``
        - ``strategy = GenerationStrategy.VAE_GENERATED``
        - ``candidate_id = "vae_{state}_{index:04d}"``

    Parameters
    ----------
    path:
        Path to the VAE candidates JSON artifact.

    Returns
    -------
    list[StateConditionedCandidate]
        Valid VAE candidates wrapped in pipeline-compatible models.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If JSON is missing the ``"candidates"`` key or contains
        invalid state labels.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"VAE candidates file not found: {path}")

    data = load_json(path)

    if not isinstance(data, dict) or "candidates" not in data:
        raise ValueError(
            f"VAE candidates JSON must have a 'candidates' key, got: "
            f"{type(data).__name__}"
        )

    raw_candidates: list[dict] = data["candidates"]
    temperature = data.get("temperature", 0.0)

    # Per-state counters for candidate IDs
    state_counters: dict[str, int] = defaultdict(int)
    results: list[StateConditionedCandidate] = []
    n_filtered_invalid = 0
    n_filtered_state = 0

    for entry in raw_candidates:
        smiles = entry.get("smiles", "")
        state = entry.get("state", "")
        is_valid = entry.get("is_valid", True)

        if not smiles:
            n_filtered_invalid += 1
            continue

        if not is_valid:
            n_filtered_invalid += 1
            logger.debug(
                "Filtered invalid VAE candidate: %.40s...", smiles
            )
            continue

        if state not in _VALID_STATES:
            raise ValueError(
                f"Invalid state label '{state}' for SMILES '{smiles[:40]}...'. "
                f"Valid states: {sorted(_VALID_STATES)}"
            )

        idx = state_counters[state]
        state_counters[state] += 1

        candidate = StateConditionedCandidate(
            candidate_id=f"vae_{state}_{idx:04d}",
            smiles=smiles,
            source=CandidateSource.ML_GENERATED,
            parent_id="",
            target_state=state,
            target_pdb_id="",
            strategy=GenerationStrategy.VAE_GENERATED,
            pocket_volume=0.0,
            back_pocket=False,
            gatekeeper_clearance=0.0,
            notes=f"VAE latent sample, temperature={temperature}",
        )
        results.append(candidate)

    if n_filtered_invalid:
        logger.info(
            "Filtered %d invalid VAE candidates", n_filtered_invalid
        )
    if n_filtered_state:
        logger.info(
            "Filtered %d candidates with bad state labels",
            n_filtered_state,
        )

    logger.info(
        "Loaded %d valid VAE candidates across %d states",
        len(results),
        len(state_counters),
    )

    return results


def build_vae_libraries(
    candidates: list[StateConditionedCandidate],
) -> list[StateConditionedLibrary]:
    """Group VAE candidates by target_state into StateConditionedLibrary objects.

    Parameters
    ----------
    candidates:
        Flat list of VAE candidates (as returned by
        :func:`load_vae_candidates`).

    Returns
    -------
    list[StateConditionedLibrary]
        One library per unique ``target_state``, sorted by state name.
    """
    if not candidates:
        return []

    by_state: dict[str, list[StateConditionedCandidate]] = defaultdict(list)
    for cand in candidates:
        by_state[cand.target_state].append(cand)

    # Extract temperature from the first candidate's notes if available
    temperature = 0.0
    if candidates:
        notes = candidates[0].notes
        if "temperature=" in notes:
            try:
                temperature = float(notes.split("temperature=")[1])
            except (ValueError, IndexError):
                pass

    libraries: list[StateConditionedLibrary] = []
    for state in sorted(by_state):
        state_candidates = by_state[state]
        libraries.append(
            StateConditionedLibrary(
                state=state,
                representative_pdb="",
                pocket_volume=0.0,
                back_pocket_accessible=False,
                candidates=state_candidates,
                n_candidates=len(state_candidates),
                strategies_used=["vae_generated"],
                generation_config={
                    "source": "conditional_smiles_vae",
                    "temperature": temperature,
                },
            )
        )

    return libraries
