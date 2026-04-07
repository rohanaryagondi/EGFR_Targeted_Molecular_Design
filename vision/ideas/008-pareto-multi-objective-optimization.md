# 008: Pareto Multi-Objective Optimization

**Category:** Novel Approaches, Scientific Rigor
**Priority:** P1: High
**Status:** accepted
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Replace the fixed weighted-sum scoring with Pareto multi-objective optimization. Instead of collapsing 4 objectives into a single number with human-chosen weights, find the Pareto front -- the set of candidates where improving any objective necessarily worsens another. This eliminates the arbitrary weight selection problem, prevents the compensation effect (where high similarity masks zero docking), and produces a richer, more informative comparison between the static and state-aware pipelines.

## The Problem

Per `known-limitations.md` (Section 1.4), the unified score is a fixed linear combination: `0.35*similarity + 0.30*druglikeness + 0.20*docking + 0.15*state`. This has two fundamental problems:

1. **Arbitrary weights.** The 0.35/0.30/0.20/0.15 split is human-chosen with no empirical basis. There is no evidence that reference similarity should be weighted 2.3x more than state specificity. The weight sensitivity analysis (WS03) can test robustness, but it cannot determine the "right" weights because there are no right weights -- the objectives are genuinely competing.

2. **Compensation effect.** A candidate with excellent similarity to erlotinib (0.8) but zero docking affinity (0.0) scores 0.35*0.8 + 0.30*0.5 + 0.20*0.0 + 0.15*1.0 = 0.58 -- higher than a candidate with moderate similarity (0.4), good docking (0.7), good drug-likeness (0.6), and moderate state specificity (0.5): 0.35*0.4 + 0.30*0.6 + 0.20*0.7 + 0.15*0.5 = 0.535. The weighted sum rewards a one-dimensional candidate over a balanced one.

This is a known flaw of scalarized multi-objective optimization. The drug discovery community has increasingly adopted Pareto-based approaches for exactly this reason.

## The Vision

After this improvement:

- **No single "best" molecule.** Instead, a Pareto front of non-dominated candidates representing optimal trade-offs. One candidate has the best docking; another has the best drug-likeness; a third balances all objectives.
- **The comparison becomes multi-dimensional.** Instead of "state-aware mean score is 0.02 higher," the comparison is: "the state-aware Pareto front dominates the static front in 73% of the objective space" -- a much richer and more publishable result.
- **Weight-free evaluation.** The hypervolume indicator (volume of objective space dominated by the Pareto front) provides a single metric for comparing pipeline quality without choosing weights. A pipeline with a larger hypervolume is objectively better across all possible weight combinations.
- **Interactive exploration.** Practitioners can navigate the Pareto front to find candidates that match their specific priorities (e.g., "I care most about docking and synthesis, less about novelty").
- **ADMET naturally integrates.** Safety objectives join the Pareto front as additional dimensions rather than requiring weight re-normalization.

## Impact Assessment

**Significant.** This addresses one of the most fundamental methodological criticisms and aligns the project with best practices in multi-objective molecular optimization. The hypervolume comparison is a strictly more informative metric than the weighted-sum comparison. It also enables cleaner integration of new scoring components (selectivity, ADMET, synthesis) without the arbitrary weight allocation problem.

Affects: scoring function (conceptual replacement), evaluation (Pareto-based comparison, hypervolume indicator), visualization (Pareto front plots), the scientific narrative.

## Effort Estimate

Medium. Multi-objective optimization algorithms (NSGA-II, MOEA/D) are well-implemented in libraries like pymoo and DEAP. Computing the Pareto front from pre-scored candidates is trivial. The main work is modifying the evaluation pipeline to use hypervolume indicators and Pareto dominance instead of (or alongside) scalar score comparisons. 1-2 weeks.

## Dependencies

- Existing scored candidates (from ranking module)
- pymoo or DEAP (lightweight Python multi-objective optimization libraries)
- Visualization libraries (matplotlib, already available)
- Statistical testing framework (for hypervolume confidence intervals)

## Implementation Sketch

1. **Pareto computation: new `ranking/pareto.py`** -- Compute the Pareto front from multi-objective score vectors. Input: N candidates x M objectives matrix. Output: indices of non-dominated candidates (the Pareto front), hypervolume indicator, crowding distances.

2. **Hypervolume comparison: new `evaluation/pareto_comparison.py`** -- Compare Pareto fronts of static vs state-aware candidates.
   - Hypervolume indicator for each pipeline (reference point: worst score across all candidates per objective)
   - Pareto front coverage: what fraction of the static front is dominated by the state-aware front?
   - Per-objective Pareto analysis: which objectives does each pipeline excel at?

3. **Visualization: add to `evaluation/figures.py`** -- 2D Pareto front projections (every pair of objectives). 3D Pareto surface plots for top-3 objectives. Parallel coordinates plot showing all objectives simultaneously.

4. **Compatibility with existing scoring** -- Keep the weighted-sum score as a secondary metric for backward compatibility. The Pareto analysis runs alongside, not instead of, the existing comparison. This ensures the current statistical tests still work.

5. **Optional: Pareto-guided generation** -- If combined with active learning (Idea 004), use expected hypervolume improvement as the acquisition function: select candidates whose inclusion would most expand the Pareto front. This is the gold standard for multi-objective optimization in molecular design.

6. **Testing** -- Verify Pareto front computation on synthetic data. Verify hypervolume is monotonically increasing as more candidates are added. Compare Pareto rankings with weighted-sum rankings to understand where they diverge.

## Open Questions

- Should the Pareto analysis replace the weighted-sum comparison or complement it? Complementing is safer; replacing is bolder.
- What reference point should be used for hypervolume computation? The standard choice (worst observed per objective) is data-dependent. A fixed reference point (e.g., [0, 0, 0, 0]) gives absolute rather than relative hypervolume.
- How to visualize a 4+ objective Pareto front effectively? Parallel coordinates, radar plots, and 2D projections all have trade-offs.
- Should ADMET be added as additional Pareto objectives (making it 5-6 objectives) or kept as hard constraints? More objectives make the Pareto front sparser.
