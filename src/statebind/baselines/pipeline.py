"""Static baseline pipeline: end-to-end orchestration.

This module ties together structure selection, pocket definition,
candidate generation, filtering, scoring, and evaluation into a
single reproducible pipeline.

The static baseline deliberately:
- Uses ONE structure (1M17, WT EGFR, active conformation)
- Uses ONE pocket definition (literature-derived ATP site)
- Ignores conformational state information
- Uses simple scoring (similarity + properties + docking stub)

This is the baseline that state-aware design must beat.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from statebind.baselines.candidates import build_candidate_library
from statebind.baselines.evaluation import evaluate_baseline
from statebind.baselines.filtering import apply_filters
from statebind.baselines.models import (
    BaselineEvaluation,
    CandidateLibrary,
    FilteredLibrary,
    PocketDefinition,
    RankedCandidates,
)
from statebind.baselines.pocket import get_baseline_pocket, select_baseline_structure
from statebind.baselines.scoring import score_candidates


@dataclass
class BaselineResult:
    """All artifacts from a static baseline run."""

    structure_metadata: dict
    pocket: PocketDefinition
    library: CandidateLibrary
    filtered: FilteredLibrary
    ranked: RankedCandidates
    evaluation: BaselineEvaluation


def run_static_baseline(
    output_dir: Path | None = None,
    enumerate_analogs: bool = True,
    top_k: int = 10,
) -> BaselineResult:
    """Run the complete static baseline pipeline.

    Steps:
    1. Select baseline structure (1M17)
    2. Define pocket (literature ATP-binding site)
    3. Build candidate library (reference + enumerated analogs)
    4. Apply property filters (Lipinski-like)
    5. Score and rank candidates
    6. Evaluate output quality

    Args:
        output_dir: If provided, write all artifacts to this directory.
        enumerate_analogs: Generate SMILES analogs of reference compounds.
        top_k: Number of top candidates for evaluation.

    Returns:
        BaselineResult with all intermediate and final artifacts.
    """
    # 1. Structure selection
    structure_meta = select_baseline_structure()
    pdb_id = structure_meta["pdb_id"]
    print(f"[1/6] Structure: {pdb_id} ({structure_meta['state']})")

    # 2. Pocket definition
    pocket = get_baseline_pocket(pdb_id=pdb_id)
    print(f"[2/6] Pocket: {pocket.pocket_id} ({len(pocket.residues)} residues)")

    # 3. Candidate library
    library = build_candidate_library(
        target_pdb_id=pdb_id,
        pocket_id=pocket.pocket_id,
        enumerate_analogs=enumerate_analogs,
    )
    print(f"[3/6] Candidates: {library.n_candidates} total")

    # 4. Filtering
    filtered = apply_filters(library)
    print(f"[4/6] Filtering: {filtered.n_passed}/{filtered.n_input} passed")

    # 5. Scoring
    ranked = score_candidates(filtered, target_pdb_id=pdb_id)
    print(f"[5/6] Ranked: {ranked.n_ranked} candidates")

    # 6. Evaluation
    evaluation = evaluate_baseline(ranked, top_k=top_k)
    print("[6/6] Evaluation complete")

    result = BaselineResult(
        structure_metadata=structure_meta,
        pocket=pocket,
        library=library,
        filtered=filtered,
        ranked=ranked,
        evaluation=evaluation,
    )

    # Write artifacts
    if output_dir is not None:
        _write_artifacts(result, output_dir)

    return result


def _write_artifacts(result: BaselineResult, output_dir: Path) -> None:
    """Write all baseline artifacts to disk."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def _dump(data, filename: str) -> None:
        with open(output_dir / filename, "w") as f:
            json.dump(data, f, indent=2, default=str)

    # Structure selection
    _dump(result.structure_metadata, "structure_selection.json")

    # Pocket definition
    _dump(result.pocket.model_dump(mode="json"), "pocket_definition.json")

    # Candidate library
    _dump(result.library.model_dump(mode="json"), "candidate_library.json")

    # Filtered library
    _dump(result.filtered.model_dump(mode="json"), "filtered_library.json")

    # Ranked candidates
    _dump(result.ranked.model_dump(mode="json"), "ranked_candidates.json")

    # Evaluation
    _dump(result.evaluation.model_dump(mode="json"), "evaluation.json")

    # Human-readable summary table
    _write_summary_table(result, output_dir / "ranking_table.csv")

    print(f"\nArtifacts written to {output_dir}/")
    for f in sorted(output_dir.iterdir()):
        if f.name != ".gitkeep":
            print(f"  {f.name:<35} {f.stat().st_size:>8} bytes")


def _write_summary_table(result: BaselineResult, path: Path) -> None:
    """Write a CSV ranking table for easy inspection."""
    import csv

    fields = [
        "rank", "candidate_id", "smiles",
        "composite_score", "reference_similarity", "druglikeness", "docking_proxy",
    ]

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in result.ranked.candidates:
            writer.writerow({
                "rank": c.rank,
                "candidate_id": c.candidate_id,
                "smiles": c.smiles,
                "composite_score": c.composite_score,
                "reference_similarity": c.get_score("reference_similarity") or "",
                "druglikeness": c.get_score("druglikeness") or "",
                "docking_proxy": c.get_score("docking_proxy") or "",
            })
