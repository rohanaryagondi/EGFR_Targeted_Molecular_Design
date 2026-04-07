# 009: Retrospective Time-Split Validation

**Category:** Validation, Scientific Rigor
**Priority:** P0: Critical
**Status:** accepted
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Validate the pipeline retrospectively using a time-split strategy: train models using only EGFR data available before a cutoff date (e.g., 2015), then test whether the pipeline can identify molecules that were later approved or advanced to clinical trials. If the state-aware pipeline retrospectively identifies osimertinib (approved 2015) or later-generation inhibitors using only pre-2015 data, the central hypothesis gains powerful experimental support without any wet lab work. This is the most impactful validation strategy available to a purely computational project.

## The Problem

Per `known-limitations.md` (Section 2.1), there is zero experimental validation at any level. No binding assays, no cell viability, no animal models. Per the peer reviewer critique (Section 5, point 1), "Where is the experimental validation?" will be the first question asked.

Per `remaining-goals.md`, the "honest assessment" acknowledges that the scientific question remains unanswered. Even with trained models, the pipeline will validate against itself (random train/test splits of the same data), which does not test real-world predictive power.

The project cannot run wet-lab experiments. But it can run a rigorous retrospective validation -- a gold-standard technique in drug discovery informatics. Retrospective validation tests whether a method could have predicted known outcomes from historical data. If the answer is yes, the method has demonstrated predictive validity.

## The Vision

After this improvement:

- **Time-split experiment design:** Use only data available before 2015 (erlotinib approved 2004, gefitinib approved 2003) to train models and generate candidates. Then test: does the pipeline identify molecules similar to osimertinib (approved 2015), rociletinib (clinical trials ~2015), or other third-generation EGFR inhibitors?
- **Multiple validation checkpoints:** Use cutoffs at 2010, 2013, and 2015 to create multiple independent validation experiments. Each cutoff removes different approved drugs from the training set.
- **State-aware vs static head-to-head on historical data:** Does the state-aware pipeline better predict the trajectory of EGFR drug development? The emergence of DFG-out targeting (type II inhibitors) and covalent inhibitors represents exactly the kind of conformational-state-aware innovation the pipeline claims to enable.
- **Quantitative validation metrics:** Enrichment factor (are later-approved drugs enriched in the top-K?), ROC-AUC for distinguishing future actives from decoys, and novelty (are the generated candidates structurally different from the pre-cutoff training set?).

## Impact Assessment

**Transformative.** This is the single most impactful thing a computational-only project can do for scientific credibility. A positive result -- "our state-aware pipeline would have identified third-generation EGFR inhibitors using only pre-2015 data" -- is a publishable finding that demonstrates real predictive power. It directly addresses the #1 peer review concern without any wet lab work.

A negative result is equally valuable: it identifies where the pipeline fails and motivates specific improvements. Either way, the experiment produces a defensible answer.

Affects: validation claims, publication narrative, credibility with practitioners, the central hypothesis.

## Effort Estimate

Medium. The ChEMBL database includes deposition dates, so creating time-split datasets is straightforward. The pipeline is already built -- the work is re-running it with restricted training data and evaluating against held-out future compounds. 1-2 weeks including data curation, multiple runs, and analysis.

## Dependencies

- ChEMBL with deposition/publication dates (available via API or download)
- Trained models (or ability to retrain on restricted datasets)
- The full pipeline (all phases, all scoring)
- Drug approval date database (DrugBank, FDA Orange Book)

## Implementation Sketch

1. **Historical data curation: `scripts/build_timesplit_datasets.py`** -- Pull all EGFR bioactivity data from ChEMBL. Split by first_publication date:
   - Training set: compounds published before cutoff (2010, 2013, or 2015)
   - Validation set: compounds published after cutoff
   - Held-out "future drugs": approved drugs not in training set (e.g., osimertinib for 2010 cutoff, rociletinib, lazertinib for 2015 cutoff)

2. **Time-restricted pipeline run: `scripts/run_retrospective_validation.py`** -- Execute the full StateBind pipeline using only pre-cutoff data:
   - Retrain MPNN on pre-cutoff compounds only
   - Use pre-cutoff reference binders only (remove osimertinib from reference set for 2010/2013 cutoffs)
   - Generate candidates, score, rank
   - Static and state-aware pipelines both run under the same time restriction

3. **Validation metrics: new `evaluation/retrospective.py`** --
   - Enrichment factor: are post-cutoff actives enriched among top-ranked candidates?
   - Structural similarity to future drugs: do generated candidates resemble compounds that were later found to be active?
   - State-prediction accuracy: does the pipeline predict which conformational states are targeted by future drugs?
   - Novelty analysis: are generated candidates novel relative to the pre-cutoff chemical space?

4. **Multi-cutoff comparison** -- Run the retrospective validation at 3+ cutoffs. Plot performance vs cutoff date to show how predictive power changes with available data.

5. **Testing** -- Verify time splits are clean (no data leakage). Verify known post-cutoff drugs are not in the pre-cutoff training set. Verify enrichment factors are computed correctly on synthetic data.

## Open Questions

- What cutoff dates are most informative? 2015 is a natural choice (osimertinib approval), but earlier cutoffs (2010) test whether the pipeline could have predicted second-generation inhibitors.
- How many post-cutoff EGFR actives exist in ChEMBL? Need the Assistant AI to check. If the number is very small (< 50), statistical power may be limited.
- Should the reference binder list be time-restricted? If the 2010 cutoff is used, osimertinib (published 2009 in ChEMBL, approved 2015) should be excluded. But erlotinib and gefitinib were both approved pre-2010 and can remain.
- How to handle the conformational state atlas? PDB structures for EGFR span many years. Should we also restrict which PDB structures are available in the time-split? This would be very rigorous but may reduce the structure dataset to too few examples.
- Is there a risk of implicit data leakage through molecular featurization? Pre-trained chemical representations may encode information from post-cutoff data.
