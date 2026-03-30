# Project Overview: StateBind

**Last updated:** 2026-03-30T00:00:00+00:00
**Briefing session:** 1 (first briefing)

---

## What StateBind Is

StateBind is a research-grade computational biology pipeline for designing small
molecules that target EGFR (Epidermal Growth Factor Receptor), a protein kinase
central to many cancers. It tests a specific scientific hypothesis:

> **Conformational state-aware molecular design outperforms static single-structure
> design for EGFR-targeted small molecules.**

This is a computational hypothesis-generation system. It produces candidate molecules
and scoring predictions, not experimental results. Every output is a computational
proxy — never a biological claim.

---

## Why Conformational States Matter

EGFR is not a rigid target. Its kinase domain adopts multiple three-dimensional shapes
(conformational states) depending on the positions of two structural elements:

1. **DFG motif** — a conserved Asp-Phe-Gly sequence that can swing "in" (catalytically
   active) or "out" (inactive). This motion opens or closes a deep hydrophobic pocket.

2. **alphaC-helix** — a regulatory helix that can rotate "in" (forming a critical
   salt bridge for catalysis) or "out" (breaking the salt bridge, inactivating the
   kinase).

These two binary switches produce 4 canonical conformational states:

| State | DFG motif | alphaC-helix | Biological Role |
|-------|-----------|--------------|-----------------|
| DFGin/aCin | In | In | Active kinase — the "on" state, catalytically competent |
| DFGin/aCout | In | Out | Src-like inactive — partially shut down, helix rotated |
| DFGout/aCin | Out | In | Intermediate — DFG flipped, unusual and transient |
| DFGout/aCout | Out | Out | Fully inactive — both switches off, deepest pocket |

Each state presents a different binding pocket — different volumes (estimated 450 to
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
- Currently produces 49 candidates via 7 state-conditioned strategies

### Fair Comparison

Both pipelines are scored by the **same unified scoring function** with the same
4 components and the same weights:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Reference similarity | 35% | How similar is this candidate to known EGFR drugs (erlotinib, gefitinib, osimertinib)? |
| Drug-likeness | 30% | Does this candidate have drug-like physicochemical properties? |
| Docking proxy | 20% | How well is this candidate predicted to bind EGFR? |
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

1. **Structural biology** — using the conformational landscape of a protein, not just
   one crystal structure, as the design context.

2. **Machine learning for drug discovery** — a conditional variational autoencoder
   generates novel molecules for specific conformational states, a graph neural network
   predicts binding affinity, and a multi-task predictor evaluates drug safety.

3. **Rigorous benchmarking** — the head-to-head comparison under identical scoring,
   with statistical hypothesis testing (Mann-Whitney U, bootstrap confidence intervals,
   effect sizes), is designed to produce a defensible answer to the central question.

The project's value is not in any single molecule it produces — it is in whether the
conformational-aware approach demonstrably outperforms the naive approach. If the
answer is yes, it motivates a new class of structure-based design methods. If the
answer is no (or inconclusive), that is equally valuable scientific information.

---

## Current Position

The pipeline infrastructure is complete. All modules are built, tested (540 tests),
and integrated. The project is now at a critical juncture: three ML models need
GPU training before the central hypothesis can be tested with real (non-stub)
predictions. The statistical testing framework exists and is ready to run the moment
trained models produce real scores.

The null hypothesis — that the state-aware pipeline does not outperform the static
baseline — has not yet been rejected. The current observed score delta (+0.020 mean,
+0.035 diversity) lacks statistical backing and uses stub/proxy scores for 20% of
the scoring weight.
