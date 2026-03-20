#!/usr/bin/env python3
"""Phase 7 — Step 1: Rerank all candidates under a unified scoring scheme.

Runs both pipelines end-to-end, scores every candidate with the SAME
function, and produces merged rankings.

Outputs:
  artifacts/ranking/static_pool.json
  artifacts/ranking/state_aware_pool.json
  artifacts/ranking/merged_ranking.json
"""

from __future__ import annotations

import json
from pathlib import Path

from statebind.baselines.pipeline import run_static_baseline
from statebind.generation.filtering import filter_all_states
from statebind.generation.generator import generate_all_states
from statebind.ranking.scoring import (
    merge_rankings,
    rank_state_aware,
    rank_static_baseline,
)


def main() -> None:
    output_dir = Path("artifacts/ranking")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Run static baseline ───────────────────────────────────────
    print("=" * 60)
    print("Step 1/4: Running static baseline pipeline")
    print("=" * 60)
    baseline = run_static_baseline()
    print(f"  Static baseline: {baseline.filtered.n_passed} filtered candidates")

    # ── 2. Run state-conditioned generation ──────────────────────────
    print("\n" + "=" * 60)
    print("Step 2/4: Running state-conditioned generation + filtering")
    print("=" * 60)
    generation = generate_all_states()
    filtered = filter_all_states(generation)
    print(f"  State-aware: {filtered.total_passed} filtered candidates across {len(filtered.states)} states")

    # ── 3. Score under unified scheme ────────────────────────────────
    print("\n" + "=" * 60)
    print("Step 3/4: Scoring all candidates under unified scheme")
    print("=" * 60)
    static_pool = rank_static_baseline(baseline.filtered)
    state_pool = rank_state_aware(filtered)
    print(f"  Static pool:      {static_pool.n_ranked} scored")
    print(f"  State-aware pool: {state_pool.n_ranked} scored")

    # ── 4. Merge rankings ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Step 4/4: Merging into global ranking")
    print("=" * 60)
    merged = merge_rankings(static_pool, state_pool)
    print(f"  Merged pool: {merged.n_total} unique candidates")

    # ── Write artifacts ──────────────────────────────────────────────
    def _dump(data, filename: str) -> None:
        path = output_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Wrote {path}")

    _dump(static_pool.model_dump(mode="json"), "static_pool.json")
    _dump(state_pool.model_dump(mode="json"), "state_aware_pool.json")
    _dump(merged.model_dump(mode="json"), "merged_ranking.json")

    # Print top-5 from each
    print("\n── Top-5 Static Baseline ──")
    for c in static_pool.candidates[:5]:
        print(f"  #{c.rank_in_pipeline}  score={c.composite_score:.4f}  {c.smiles[:60]}")

    print("\n── Top-5 State-Aware ──")
    for c in state_pool.candidates[:5]:
        print(f"  #{c.rank_in_pipeline}  score={c.composite_score:.4f}  state={c.target_state}  {c.smiles[:50]}")

    print("\n── Top-5 Global ──")
    for c in merged.merged[:5]:
        print(f"  #{c.global_rank}  score={c.composite_score:.4f}  pipeline={c.pipeline.value}  {c.smiles[:50]}")

    print(f"\nDone. Artifacts in {output_dir}/")


if __name__ == "__main__":
    main()
