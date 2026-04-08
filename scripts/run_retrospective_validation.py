#!/usr/bin/env python3
"""Run retrospective time-split validation.

Executes the full StateBind pipeline under time restriction: for each
cutoff year (2010, 2015), runs static and state-aware pipelines with
restricted reference binders, then computes enrichment and similarity
metrics against held-out future drugs.

Requires: time-split datasets built by ``build_timesplit_datasets.py``.

Usage:
    python scripts/build_timesplit_datasets.py   # first
    python scripts/run_retrospective_validation.py
    python scripts/run_retrospective_validation.py --cutoff 2015 --skip-retrain
"""

from __future__ import annotations

import argparse
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from statebind.baselines.pipeline import run_static_baseline
from statebind.chemistry.fingerprints import compute_max_reference_similarity
from statebind.data.paths import DataPaths
from statebind.evaluation.retrospective import (
    RetrospectiveComparison,
    RetrospectiveResult,
    compute_retrospective_metrics,
    generate_retrospective_summary,
    get_future_drugs,
    to_serializable,
)
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.generation.vae_integration import (
    build_vae_libraries,
    load_vae_candidates,
)
from statebind.ranking.models import RankedPool, UnifiedScoredCandidate
from statebind.ranking.scoring import (
    DEFAULT_WEIGHTS,
    rank_state_aware,
    rank_static_baseline,
)
from statebind.utils.config import load_config
from statebind.utils.io import load_json, save_json

logger = logging.getLogger(__name__)


# ── Re-scoring with restricted references ──────────────────────────────────


def rescore_with_restricted_refs(
    pool: RankedPool,
    pre_cutoff_refs: list[str],
    weights: dict[str, float] | None = None,
) -> RankedPool:
    """Re-score candidates replacing reference_similarity with restricted refs.

    Post-processes a scored pool WITHOUT modifying ``ranking/scoring.py``.
    Replaces only the ``reference_similarity`` component using pre-cutoff
    reference binders, then recomputes composite scores and re-ranks.

    Args:
        pool: Scored candidate pool from ``rank_static_baseline()`` or
            ``rank_state_aware()``.
        pre_cutoff_refs: SMILES of reference binders available before cutoff.
        weights: Scoring weights (defaults to ``DEFAULT_WEIGHTS``).

    Returns:
        The pool with updated scores and ranks (modified in-place).
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    for candidate in pool.candidates:
        # Compute restricted reference similarity
        restricted_sim = compute_max_reference_similarity(
            candidate.smiles, references=pre_cutoff_refs,
        )

        # Update reference_similarity component
        for sc in candidate.scores:
            if sc.name == "reference_similarity":
                sc.value = round(restricted_sim, 4)
                break

        # Recompute composite score
        candidate.composite_score = round(
            sum(sc.value * sc.weight for sc in candidate.scores), 4,
        )

    # Re-sort and re-rank
    pool.candidates.sort(key=lambda x: x.composite_score, reverse=True)
    for i, c in enumerate(pool.candidates):
        c.rank_in_pipeline = i + 1

    return pool


def _candidates_to_dicts(
    candidates: list[UnifiedScoredCandidate],
) -> list[dict[str, Any]]:
    """Convert scored candidates to simple dicts for metric computation."""
    return [
        {"smiles": c.smiles, "composite_score": c.composite_score}
        for c in candidates
    ]


# ── MPNN checkpoint management ────────────────────────────────────────────


def _swap_mpnn_checkpoint(
    cutoff_year: int,
    paths: DataPaths,
) -> Path | None:
    """Swap the default MPNN checkpoint for the pre-cutoff version.

    Backs up the original checkpoint (if any), copies the pre-cutoff
    checkpoint to the default location, and resets the affinity predictor
    singleton so the next prediction call loads the new model.

    Args:
        cutoff_year: The temporal cutoff year.
        paths: DataPaths instance.

    Returns:
        Path to the backup file (or None if no original existed).
    """
    default_ckpt = paths.root / "artifacts" / "models" / "mpnn" / "best_model.pt"
    pre_cutoff_ckpt = (
        paths.root / "artifacts" / "models" / f"mpnn_pre{cutoff_year}" / "best_model.pt"
    )

    if not pre_cutoff_ckpt.exists():
        logger.warning(
            "Pre-cutoff MPNN checkpoint not found: %s. Using default model.",
            pre_cutoff_ckpt,
        )
        return None

    # Backup original if it exists
    backup_path = None
    if default_ckpt.exists():
        backup_path = default_ckpt.with_suffix(".pt.bak")
        shutil.copy2(default_ckpt, backup_path)
        logger.info("Backed up original MPNN: %s", backup_path)

    # Copy pre-cutoff checkpoint
    default_ckpt.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pre_cutoff_ckpt, default_ckpt)
    logger.info(
        "Swapped MPNN checkpoint to pre-%d: %s",
        cutoff_year, pre_cutoff_ckpt,
    )

    # Reset singleton so next call loads the new model
    try:
        from statebind.ml.affinity_predictor import reset_singleton

        reset_singleton()
        logger.info("MPNN affinity predictor singleton reset")
    except ImportError:
        logger.warning("Could not reset MPNN singleton (import failed)")

    return backup_path


def _restore_mpnn_checkpoint(backup_path: Path | None, paths: DataPaths) -> None:
    """Restore the original MPNN checkpoint from backup."""
    default_ckpt = paths.root / "artifacts" / "models" / "mpnn" / "best_model.pt"

    if backup_path is not None and backup_path.exists():
        shutil.copy2(backup_path, default_ckpt)
        backup_path.unlink()
        logger.info("Restored original MPNN checkpoint")
    elif default_ckpt.exists():
        # No backup means there was no original — remove the swapped one
        default_ckpt.unlink()
        logger.info("Removed swapped MPNN checkpoint (no original)")

    # Reset singleton again
    try:
        from statebind.ml.affinity_predictor import reset_singleton

        reset_singleton()
    except ImportError:
        pass


# ── Single cutoff pipeline ─────────────────────────────────────────────────


def _merge_vae_candidates(
    generation: Any,
    vae_candidates_path: Path,
) -> Any:
    """Merge VAE-generated candidates into template-generated results.

    Loads VAE candidates from a JSON artifact, groups by state, and
    merges into existing ``MultiStateGenerationResult`` libraries.

    Args:
        generation: The template-based ``MultiStateGenerationResult``.
        vae_candidates_path: Path to VAE candidates JSON.

    Returns:
        Updated generation result with VAE candidates merged in.
    """
    from statebind.generation.models import (
        MultiStateGenerationResult,
        StateConditionedLibrary,
    )

    if not vae_candidates_path.exists():
        logger.warning(
            "VAE candidates not found: %s — skipping merge",
            vae_candidates_path,
        )
        return generation

    try:
        candidates = load_vae_candidates(vae_candidates_path)
        vae_libraries = build_vae_libraries(candidates)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Failed to load VAE candidates: %s", exc)
        return generation

    if not vae_libraries:
        logger.info("No valid VAE candidates to merge")
        return generation

    logger.info(
        "Merging %d VAE candidates across %d states",
        len(candidates), len(vae_libraries),
    )

    existing: dict[str, StateConditionedLibrary] = {
        lib.state: lib for lib in generation.libraries
    }

    merged_libraries: list[StateConditionedLibrary] = list(generation.libraries)
    total = generation.total_candidates
    all_smiles: set[str] = set()
    for lib in merged_libraries:
        all_smiles.update(c.smiles for c in lib.candidates)

    for vae_lib in vae_libraries:
        if vae_lib.state in existing:
            for i, mlib in enumerate(merged_libraries):
                if mlib.state == vae_lib.state:
                    combined = list(mlib.candidates) + list(vae_lib.candidates)
                    strategies = list(set(mlib.strategies_used + vae_lib.strategies_used))
                    merged_libraries[i] = StateConditionedLibrary(
                        state=mlib.state,
                        representative_pdb=mlib.representative_pdb,
                        pocket_volume=mlib.pocket_volume,
                        back_pocket_accessible=mlib.back_pocket_accessible,
                        candidates=combined,
                        n_candidates=len(combined),
                        strategies_used=strategies,
                        generation_config=mlib.generation_config,
                    )
                    total += vae_lib.n_candidates
                    all_smiles.update(c.smiles for c in vae_lib.candidates)
                    break
        else:
            merged_libraries.append(vae_lib)
            total += vae_lib.n_candidates
            all_smiles.update(c.smiles for c in vae_lib.candidates)

    return MultiStateGenerationResult(
        states=sorted({lib.state for lib in merged_libraries}),
        libraries=merged_libraries,
        total_candidates=total,
        total_unique_smiles=len(all_smiles),
        cross_state_overlap=generation.cross_state_overlap,
        generated_at=generation.generated_at,
        notes=generation.notes + " VAE candidates merged.",
    )


def run_single_cutoff(
    cutoff_year: int,
    config: dict[str, Any],
    output_dir: Path,
    use_retrained_mpnn: bool = False,
    vae_candidates_path: Path | None = None,
) -> list[RetrospectiveResult]:
    """Run both pipelines for one cutoff year and compute metrics.

    Args:
        cutoff_year: Temporal cutoff year.
        config: Loaded retrospective config.
        output_dir: Output directory for results.
        use_retrained_mpnn: If True, swap the MPNN checkpoint to the
            pre-cutoff version before running the pipeline.
        vae_candidates_path: If provided, merge these VAE candidates into
            the state-aware pipeline's generation output.

    Returns a list of two ``RetrospectiveResult`` objects: one for static,
    one for state-aware.
    """
    retro_config = config.get("retrospective", {})
    k_values = retro_config.get("enrichment_k_values", [10, 50, 100])
    threshold = retro_config.get("similarity_threshold", 0.4)

    paths = DataPaths()

    # Load time-split metadata
    meta_path = paths.processed_dir / f"timesplit_{cutoff_year}_metadata.json"
    if not meta_path.exists():
        logger.error(
            "Time-split metadata not found: %s. Run build_timesplit_datasets.py first.",
            meta_path,
        )
        return []

    meta = load_json(meta_path)
    pre_cutoff_refs = meta.get("pre_cutoff_reference_binders", [])

    # Load training SMILES for novelty computation
    train_path = paths.processed_dir / f"timesplit_{cutoff_year}_train.json"
    if train_path.exists():
        train_data = load_json(train_path)
        training_smiles = {str(r["smiles"]) for r in train_data}
    else:
        training_smiles = set()

    # Future drugs
    future_drugs = get_future_drugs(cutoff_year)
    logger.info(
        "Cutoff %d: %d pre-cutoff refs, %d future drugs",
        cutoff_year, len(pre_cutoff_refs), len(future_drugs),
    )

    # ── Swap MPNN if requested ─────────────────────────────────────────
    mpnn_backup = None
    if use_retrained_mpnn:
        mpnn_backup = _swap_mpnn_checkpoint(cutoff_year, paths)

    try:
        # ── Run static baseline ────────────────────────────────────────
        logger.info("Running static baseline pipeline...")
        baseline = run_static_baseline()
        static_pool = rank_static_baseline(baseline.filtered)
        static_pool = rescore_with_restricted_refs(static_pool, pre_cutoff_refs)

        # ── Run state-aware pipeline ───────────────────────────────────
        logger.info("Running state-aware pipeline...")
        generation = generate_all_states()

        # Merge VAE candidates if provided
        if vae_candidates_path is not None:
            generation = _merge_vae_candidates(generation, vae_candidates_path)

        filtered = filter_all_states(generation)
        state_pool = rank_state_aware(filtered)
        state_pool = rescore_with_restricted_refs(state_pool, pre_cutoff_refs)
    finally:
        # Always restore original MPNN
        if use_retrained_mpnn:
            _restore_mpnn_checkpoint(mpnn_backup, paths)

    # ── Compute metrics ────────────────────────────────────────────────
    results: list[RetrospectiveResult] = []

    for pipeline_name, pool in [("static", static_pool), ("state_aware", state_pool)]:
        cand_dicts = _candidates_to_dicts(pool.candidates)
        result = compute_retrospective_metrics(
            candidates=cand_dicts,
            future_drugs=future_drugs,
            training_smiles=training_smiles,
            pipeline=pipeline_name,
            cutoff_year=cutoff_year,
            k_values=k_values,
            threshold=threshold,
        )
        results.append(result)

        logger.info(
            "  %s: EF@10=%.2f, EF@50=%.2f, max_sim=%.3f, novelty=%.2f",
            pipeline_name,
            result.enrichment_factor_10,
            result.enrichment_factor_50,
            result.max_similarity_to_future,
            result.novelty_vs_training,
        )

    # Save per-cutoff results
    use_label = "_retrained" if use_retrained_mpnn else ""
    notes_parts = [
        f"Retrospective validation at cutoff {cutoff_year}.",
        f"Reference binders restricted to pre-{cutoff_year} approved drugs.",
    ]
    if use_retrained_mpnn:
        notes_parts.append(f"MPNN retrained on pre-{cutoff_year} data.")
    if vae_candidates_path is not None:
        notes_parts.append(f"VAE candidates from {vae_candidates_path.name} merged.")

    cutoff_output = {
        "cutoff_year": cutoff_year,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mpnn_model": f"mpnn_pre{cutoff_year}" if use_retrained_mpnn else "mpnn_default",
        "vae_candidates": str(vae_candidates_path) if vae_candidates_path else None,
        "results": [to_serializable(r) for r in results],
        "notes": " ".join(notes_parts),
    }
    save_json(
        cutoff_output,
        output_dir / f"retrospective_{cutoff_year}{use_label}.json",
    )

    return results


# ── Main ───────────────────────────────────────────────────────────────────


def run_retrospective_validation(
    config_path: str | Path = "configs/retrospective.yaml",
    cutoff: int | None = None,
    output_dir: Path | None = None,
    use_retrained_mpnn: bool = False,
    use_retrained_vae: bool = False,
) -> RetrospectiveComparison:
    """Run full retrospective validation across all configured cutoffs.

    Args:
        config_path: Path to retrospective configuration YAML.
        cutoff: If specified, only run for this cutoff year.
        output_dir: Output directory (default: artifacts/evaluation/).
        use_retrained_mpnn: If True, use pre-cutoff MPNN checkpoints.
        use_retrained_vae: If True, merge pre-cutoff VAE candidates
            into the state-aware pipeline.

    Returns:
        ``RetrospectiveComparison`` with results for all cutoffs.
    """
    config = load_config(str(config_path))
    retro_config = config.get("retrospective", {})
    cutoffs = retro_config.get("cutoffs", [2010, 2015])

    if cutoff is not None:
        cutoffs = [cutoff]

    if output_dir is None:
        output_dir = Path(
            config.get("evaluation", {}).get("output_dir", "artifacts/evaluation/")
        )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[RetrospectiveResult] = []

    for c in cutoffs:
        logger.info("=" * 60)
        logger.info("Running retrospective validation: cutoff %d", c)
        if use_retrained_mpnn:
            logger.info("Using retrained MPNN (pre-%d checkpoint)", c)
        if use_retrained_vae:
            logger.info("Using retrained VAE candidates (pre-%d)", c)
        logger.info("=" * 60)

        # Resolve VAE candidates path for this cutoff
        vae_path = None
        if use_retrained_vae:
            vae_path = (
                DataPaths().root / "artifacts" / "generation"
                / f"vae_candidates_pre{c}.json"
            )

        results = run_single_cutoff(
            c, config, output_dir,
            use_retrained_mpnn=use_retrained_mpnn,
            vae_candidates_path=vae_path,
        )
        all_results.extend(results)

    comparison = RetrospectiveComparison(
        results=all_results,
        cutoffs=cutoffs,
    )
    comparison.summary = generate_retrospective_summary(comparison)

    # Save comprehensive results
    summary_output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cutoffs": cutoffs,
        "summary": comparison.summary,
        "results": [to_serializable(r) for r in all_results],
        "notes": (
            "Retrospective time-split validation of StateBind pipeline. "
            "Trained on pre-cutoff data, evaluated against post-cutoff drugs."
        ),
    }
    save_json(summary_output, output_dir / "retrospective_summary.json")

    # Print summary
    print(f"\n{comparison.summary}\n")

    return comparison


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run retrospective time-split validation",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/retrospective.yaml",
        help="Path to retrospective config YAML",
    )
    parser.add_argument(
        "--cutoff",
        type=int,
        default=None,
        help="Run only for this cutoff year (default: all configured)",
    )
    parser.add_argument(
        "--use-retrained-mpnn",
        action="store_true",
        help="Use pre-cutoff MPNN checkpoints (from artifacts/models/mpnn_pre{year}/)",
    )
    parser.add_argument(
        "--use-retrained-vae",
        action="store_true",
        help="Merge pre-cutoff VAE candidates into state-aware pipeline",
    )
    parser.add_argument(
        "--skip-retrain",
        action="store_true",
        help="(Deprecated, ignored) Use --use-retrained-mpnn instead",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: artifacts/evaluation/)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output = Path(args.output_dir) if args.output_dir else None
    run_retrospective_validation(
        config_path=args.config,
        cutoff=args.cutoff,
        output_dir=output,
        use_retrained_mpnn=args.use_retrained_mpnn,
        use_retrained_vae=args.use_retrained_vae,
    )


if __name__ == "__main__":
    main()
