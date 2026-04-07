# 004: Ensemble Uncertainty Quantification and Active Learning Loop

**Category:** ML Improvements, Scientific Rigor
**Priority:** P1: High
**Status:** deferred
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Train ensembles of 5-10 models (MPNN, ADMET) with different random seeds to produce prediction uncertainty estimates alongside point predictions. Use these uncertainties to implement an active learning loop: generate candidates, score them, identify the most uncertain/promising molecules, retrain models on augmented data, and generate again. This transforms StateBind from a one-shot pipeline into an iterative design engine and gives every prediction a confidence interval -- addressing two fundamental limitations simultaneously.

## The Problem

Per `known-limitations.md` (Section 3.3), all models produce point predictions with no uncertainty estimate. The MPNN might predict pIC50 = 7.2 for a candidate, but is this based on many similar training examples (high confidence) or a wild extrapolation to unseen chemical space (low confidence)? The pipeline cannot tell the difference. Ranking candidates by point predictions alone ignores epistemic uncertainty and could promote unreliable predictions to the top of the list.

Per `known-limitations.md` (Section 3.5), the pipeline is one-shot: generate, score, rank, done. There is no mechanism to learn from results and improve. Per `remaining-goals.md`, the training data is modest (1,678 compounds for MPNN). An active learning loop would make the most of this limited data by strategically selecting which candidates to investigate further.

## The Vision

After this improvement:

- **Every prediction comes with a confidence interval.** Instead of "pIC50 = 7.2", the output is "pIC50 = 7.2 +/- 0.8 (ensemble disagreement)". Rankings become uncertainty-aware: a candidate predicted at 7.2 +/- 0.3 ranks higher than one at 7.5 +/- 2.0.
- **Risk-aware scoring.** The unified scoring function can incorporate uncertainty: `risk_adjusted_score = predicted_score - lambda * uncertainty`. Lambda controls the exploration-exploitation tradeoff.
- **Active learning cycle.** Round 1: generate 200 candidates, score with ensemble, identify the 20 most uncertain (high disagreement). Round 2: query ChEMBL for measured bioactivity data on molecules similar to the uncertain 20. Retrain ensemble on augmented data. Round 3: regenerate, rescore with improved model. Repeat.
- **Evaluation upgrade.** The head-to-head comparison can report not just "state-aware is better" but "state-aware is better with higher confidence" -- a much stronger scientific claim.

## Impact Assessment

**Significant.** Uncertainty quantification is increasingly expected in ML-for-drug-discovery publications. Peer reviewers will note its absence. Active learning is a natural extension that maximizes the value of limited training data. Together, they transform both the scientific rigor (confidence intervals on the central claim) and practical utility (iteratively improving candidates) of the pipeline.

Affects: all ML models (ensembling), scoring function (uncertainty adjustment), evaluation (confidence intervals on comparison), data pipeline (active learning data augmentation).

## Effort Estimate

Medium. Deep ensembles are straightforward to implement -- train the same architecture N times with different seeds. The infrastructure overhead is training time (5-10x single model) and storing multiple checkpoints. Active learning requires a data querying strategy and retraining loop, which is more complex but builds on existing training scripts.

## Dependencies

- Trained base models (MPNN, ADMET) -- need at least one working model before ensembling
- GPU time (5-10x current training budget for ensemble)
- ChEMBL API access (for active learning data augmentation)
- Statistical testing framework (WS03, for uncertainty propagation)

## Implementation Sketch

1. **Ensemble training: modify `ml/trainer.py`** -- Add an `ensemble_size` parameter to TrainerConfig. Training loop creates N model instances with different random seeds, trains each independently, saves N checkpoints to `artifacts/models/{name}/ensemble/model_{i}.pt`.

2. **Ensemble prediction: new `ml/ensemble.py`** -- Load N models, run inference on each, return mean prediction + standard deviation (epistemic uncertainty). For classification tasks (hERG, CYP3A4), use predictive entropy or mutual information.

3. **Uncertainty-aware scoring: modify `ranking/scoring.py`** -- Add optional `uncertainty_penalty` parameter to score_unified(). When ensemble predictions are available, compute `adjusted_score = score - lambda * total_uncertainty` where total_uncertainty aggregates docking and ADMET uncertainties.

4. **Active learning loop: new `scripts/active_learning_cycle.py`** -- Orchestrates the iterative loop:
   ```
   for round in range(max_rounds):
       generate_candidates()
       score_with_ensemble()
       select_informative_candidates(strategy='max_uncertainty' or 'expected_improvement')
       query_similar_compounds_from_chembl()
       retrain_ensemble_on_augmented_data()
   ```

5. **Evaluation enhancement: modify `evaluation/comparison.py`** -- Report confidence intervals on all comparison metrics. "State-aware mean score: 0.55 +/- 0.03 vs static: 0.53 +/- 0.04 (overlapping CIs)" is more informative than bare point estimates.

6. **Testing** -- Verify ensemble variance is well-calibrated: high uncertainty correlates with actual prediction error on a held-out test set. Verify active learning improves model performance over random data augmentation.

## Open Questions

- What ensemble size is sufficient? Literature suggests 5 models is usually enough for calibrated uncertainty. 10 is better but doubles training time.
- Should we use deep ensembles, MC dropout, or both? MC dropout is cheaper (single model, multiple forward passes with dropout active) but often under-estimates uncertainty. Deep ensembles are the gold standard but expensive.
- For active learning, what acquisition function works best? Uncertainty sampling (pick most uncertain), expected improvement (pick candidates with highest expected score improvement), or a hybrid?
- How to handle uncertainty across different scoring components? Docking uncertainty (from MPNN ensemble) and ADMET uncertainty are in different scales and units.
