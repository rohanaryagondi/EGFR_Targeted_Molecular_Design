# Project Overview: StateBind

**Last updated:** 2026-04-07T20:00:00+00:00
**Briefing session:** 3

---

## Changes Since Last Briefing (Session 2)

- **3 new workstreams completed:** WS11 (GNINA physics-based docking), WS12 (Pareto
  multi-objective optimization), WS13 (retrospective time-split validation)
- **Retrospective validation result:** State-aware pipeline achieves 10x enrichment
  over static baseline for identifying future approved EGFR drugs (EF@10 = 4.95/7.72
  vs 0.47/0.79). This is the project's strongest result and fundamentally changes the
  narrative.
- **Docking cascade expanded:** Physics-based GNINA docking added as top tier (GPU only)
- **Pareto analysis added:** Weight-free comparison method alongside existing weighted-sum
- **Test count:** 548 to 646 (+98). Workstreams: 9 to 12.

---

## What StateBind Is

StateBind is a research-grade computational biology pipeline for designing small
molecules that target EGFR (Epidermal Growth Factor Receptor), a protein kinase
central to many cancers. It tests a specific scientific hypothesis:

> **Conformational state-aware molecular design outperforms static single-structure
> design for EGFR-targeted small molecules.**

This is a computational hypothesis-generation system. It produces candidate molecules
and scoring predictions, not experimental results. Every output is a computational
proxy -- never a biological claim.

---

## Why Conformational States Matter

EGFR is not a rigid target. Its kinase domain adopts multiple three-dimensional shapes
(conformational states) depending on the positions of two structural elements:

1. **DFG motif** -- a conserved Asp-Phe-Gly sequence that can swing "in" (catalytically
   active) or "out" (inactive). This motion opens or closes a deep hydrophobic pocket.

2. **alphaC-helix** -- a regulatory helix that can rotate "in" (forming a critical
   salt bridge for catalysis) or "out" (breaking the salt bridge, inactivating the
   kinase).

These two binary switches produce 4 canonical conformational states:

| State | DFG motif | alphaC-helix | Biological Role |
|-------|-----------|--------------|-----------------|
| DFGin/aCin | In | In | Active kinase -- the "on" state, catalytically competent |
| DFGin/aCout | In | Out | Src-like inactive -- partially shut down, helix rotated |
| DFGout/aCin | Out | In | Intermediate -- DFG flipped, unusual and transient |
| DFGout/aCout | Out | Out | Fully inactive -- both switches off, deepest pocket |

Each state presents a different binding pocket -- different volumes (estimated 450 to
850 cubic angstroms), different shapes, different druggable features. A molecule
designed for the active state may not fit or bind the inactive state, and vice versa.

Most computational drug design pipelines ignore this. They pick one crystal structure
(one conformational snapshot) and design molecules for that single pocket. StateBind
asks: what if we design molecules with explicit awareness of which conformational state
they target?

---

## The Two Pipelines

StateBind runs two parallel molecular design pipelines and compares them head-to-head
under identical scoring conditions:

### Static Baseline
- Uses a single crystal structure (PDB 1M17, an active-state EGFR structure)
- Extracts one pocket definition
- Generates candidate molecules with no knowledge of conformational states
- Currently produces 30 candidates via string-modification strategies

### State-Aware Pipeline
- Uses the full 4-state conformational atlas
- Extracts pocket descriptors for each state
- Generates candidates conditioned on specific conformational states
- Tracks which states each candidate appears in
- Currently produces 461 candidates (36 template + 395 VAE-generated + 30 shared)

### Fair Comparison

Both pipelines are scored by the **same unified scoring function** with the same
4 components and the same weights:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Reference similarity | 35% | How similar is this candidate to known EGFR drugs (erlotinib, gefitinib, osimertinib)? |
| Drug-likeness | 30% | Does this candidate have drug-like physicochemical properties? |
| Docking proxy | 20% | How well is this candidate predicted to bind EGFR? Uses a 4-tier cascade: GNINA physics-based docking (GPU), MPNN affinity predictor (learned), DockingProxy MLP (lightweight), or constant stub. |
| State specificity | 15% | Does this candidate selectively target one conformational state? |

The state specificity component is the **only axis** where the state-aware pipeline can
outperform the static baseline. For the static pipeline, state specificity is always
zero (it has no state information). For the state-aware pipeline, a candidate that
appears in only one state scores 1.0; a candidate appearing in all four states scores
0.0. This 15% weight is the measurable premium for conformational awareness.

The comparison is designed to be conservative: the state-aware pipeline must overcome
a scoring system where 85% of the weight is state-agnostic. If it still wins, the
signal is meaningful.

---

## What Makes This Interesting

StateBind sits at the intersection of three fields:

1. **Structural biology** -- using the conformational landscape of a protein, not just
   one crystal structure, as the design context. Physics-based docking (GNINA) provides
   real binding energy estimates across all 4 conformational states.

2. **Machine learning for drug discovery** -- a conditional variational autoencoder
   generates novel molecules for specific conformational states, a graph neural network
   predicts binding affinity, and a multi-task predictor evaluates drug safety.

3. **Rigorous benchmarking** -- the head-to-head comparison under identical scoring,
   with statistical hypothesis testing (Mann-Whitney U, bootstrap confidence intervals,
   effect sizes), Pareto multi-objective optimization (weight-free comparison via
   hypervolume), and retrospective time-split validation (testing whether the pipeline
   would have identified future drugs from historical data) is designed to produce a
   defensible answer to the central question.

The project's value is not in any single molecule it produces -- it is in whether the
conformational-aware approach demonstrably outperforms the naive approach. If the
answer is yes, it motivates a new class of structure-based design methods. If the
answer is no (or inconclusive), that is equally valuable scientific information.

---

## Current Position

The pipeline infrastructure is complete. All 12 workstreams are done, tested (646 tests),
and integrated. All three ML models have been trained and their predictions are active
in the pipeline. Physics-based docking (GNINA) is available on GPU nodes. Pareto
multi-objective optimization provides a weight-free evaluation method. Retrospective
time-split validation has tested the pipeline against historical drug discovery data.

### The Central Question: A Nuanced Answer

The null hypothesis -- that the state-aware pipeline does not outperform the static
baseline -- was **formally retained on mean unified score.** The static baseline
achieved higher mean scores (0.5437 vs 0.4378, p<0.001, Cohen's d=1.36 favoring
static). Weight sensitivity analysis shows 56% of random weight combinations favor
static, 44% favor state-aware.

However, the state-aware pipeline excels on every other metric:

| Metric | Static | State-Aware | Advantage |
|--------|--------|-------------|-----------|
| Mean unified score | 0.5437 | 0.4378 | Static (+0.1059) |
| Max score | 0.7288 | 0.7794 | State-aware |
| Candidate count | 30 | 461 | State-aware (15x) |
| Chemical diversity | 0.5684 | 0.9056 | State-aware (+59%) |
| Novel molecules | 0 | 431 | State-aware |

### Retrospective Validation: The Strongest Signal

The most compelling evidence comes from retrospective time-split validation. When
trained only on data available before a cutoff year, the state-aware pipeline identifies
future approved EGFR drugs with dramatically higher enrichment:

| Cutoff | State-Aware EF@10 | Static EF@10 | Enrichment Ratio |
|--------|-------------------|--------------|-----------------|
| 2010 | 4.95 | 0.47 | 10.5x |
| 2015 | 7.72 | 0.79 | 9.8x |

All held-out drugs were found (5/5 pre-2010, 3/3 pre-2015). The state-aware pipeline
produced 430-520 candidates (mostly VAE-generated) compared to 30 for static. Novelty
was 0.99 -- the VAE generates genuinely new molecules, not memorized training compounds.

This means the state-aware pipeline, despite losing on mean score, is dramatically
better at the task that matters most: placing future successful drugs near the top of
its candidate list.
