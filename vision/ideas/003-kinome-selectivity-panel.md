# 003: Kinome-Wide Selectivity Panel

**Category:** Pipeline Gaps, Scientific Rigor
**Priority:** P0: Critical
**Status:** deferred
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Add a selectivity scoring component that evaluates each candidate molecule against a panel of 10-20 kinases (ABL, BRAF, ALK, SRC, HER2, MET, etc.) in addition to EGFR. Score candidates by their selectivity ratio: how much more strongly they bind EGFR compared to off-target kinases. A molecule that binds everything is a toxicity hazard, not a drug. This addresses the most glaring gap a drug discovery practitioner would identify in the current pipeline.

## The Problem

Per `known-limitations.md` (Section 2.5), the pipeline scores binding to EGFR only. It does not check whether candidates also bind kinases with similar ATP-binding pockets. Per the practitioner critique (Section 6), no selectivity profiling is one of the most naive aspects of the pipeline. The kinase superfamily has over 500 members, many with highly conserved ATP-binding sites. A Type I inhibitor designed for EGFR's active site will almost certainly hit multiple kinases unless selectivity is explicitly designed in.

This is not an academic concern. The known EGFR reference binders illustrate the problem: erlotinib is relatively selective for EGFR/HER2 but gefitinib has broader kinase activity. Osimertinib was specifically designed to be mutant-selective (T790M). The pipeline currently has no way to distinguish between a selective candidate and a promiscuous one -- both score the same under the unified scoring function.

## The Vision

After this improvement:

- **Every candidate gets a selectivity profile** -- predicted affinity against 10-20 off-target kinases alongside EGFR.
- **A selectivity index** enters the scoring function (or acts as a hard constraint). Candidates that bind EGFR strongly but off-targets weakly are rewarded. Promiscuous binders are penalized or filtered.
- **State-specific selectivity** -- a molecule designed for the DFGout/aCout pocket may have better selectivity than one designed for the active state, because the inactive-state pocket is more structurally distinct from other kinases. This would be a powerful finding supporting the state-aware hypothesis.
- **Kinome heatmaps** in the evaluation module showing predicted activity across the panel for top candidates from each pipeline.

## Impact Assessment

**Significant.** Selectivity is table-stakes for any drug design pipeline claiming practical relevance. Adding it transforms the evaluation from "which pipeline produces higher-scoring molecules" to "which pipeline produces more selective molecules" -- a much more meaningful comparison that drug discovery practitioners would respect. It could also provide a new axis where state-aware design wins: if inactive-state pockets are more structurally unique, state-aware candidates may naturally be more selective.

Affects: scoring function (new component or constraint), evaluation (selectivity comparison), the scientific narrative (stronger practical relevance).

## Effort Estimate

Medium. The MPNN architecture already predicts affinity from molecular graphs -- training it on multi-kinase data is a retraining exercise, not a new architecture. The main work is curating the multi-kinase training dataset from ChEMBL (several thousand compounds per kinase) and modifying the scoring/evaluation pipeline.

## Dependencies

- Trained MPNN (or at minimum, the MPNN architecture ready for multi-target training)
- ChEMBL bioactivity data for 10-20 kinases (publicly available via ChEMBL API)
- Kinase target ChEMBL IDs (well-documented)

## Implementation Sketch

1. **Data curation: `scripts/build_kinome_dataset.py`** -- Query ChEMBL for bioactivity data (IC50, Ki) for a panel of kinases. Target selection: prioritize kinases commonly hit by EGFR inhibitors (ABL, BRAF, ALK, SRC, HER2/ERBB2, MET, VEGFR2, FGFR1, JAK2, Aurora A). Filter for assay quality (pChEMBL >= 5, single protein target, confidence >= 7).

2. **Multi-target MPNN: modify `ml/mpnn.py`** or create `ml/selectivity_mpnn.py` -- Two approaches:
   - **Option A: Single model with target conditioning.** Add a target embedding (one-hot or learned) as a global feature. The same MPNN predicts affinity for any kinase given the target identity. Simpler, allows transfer learning across kinases.
   - **Option B: EGFR-specific model + off-target ensemble.** Keep the EGFR MPNN. Train separate lightweight models per off-target kinase. More modular but less transfer learning.

3. **Selectivity scoring: new function in `ranking/scoring.py`** -- Compute selectivity index: `selectivity = sigmoid(pIC50_EGFR - max(pIC50_offtargets))`. A candidate with pIC50 = 8.0 for EGFR and max off-target pIC50 = 5.0 has a selectivity index near 1.0. A promiscuous binder (EGFR = 7.0, off-target = 6.8) has an index near 0.5.

4. **Integration into scoring weights** -- Either add as a 5th component (re-normalize weights) or use as a hard filter (selectivity index > threshold). The weight sensitivity analysis framework (WS03) can determine the optimal approach.

5. **Evaluation enhancement: `evaluation/selectivity.py`** -- Kinome heatmaps, selectivity distributions by pipeline, correlation between state specificity and selectivity.

6. **Testing** -- Verify known selective drugs (osimertinib) score higher than known promiscuous inhibitors (staurosporine) on the selectivity index.

## Open Questions

- How many kinases should be in the panel? 10 is practical, 20 is thorough, 50+ is ambitious. What is the minimum needed for a credible selectivity claim?
- Should selectivity be a scoring component or a hard constraint? Practitioners typically treat it as a constraint ("must have >100x selectivity over hERG"). For the head-to-head comparison, a scoring component is more informative. Could do both.
- Is there enough multi-kinase training data for a reliable multi-target MPNN? ChEMBL has extensive data for major kinases, but coverage is uneven.
- How does this interact with the conformational state model? Each kinase has its own conformational landscape. Should selectivity be computed per-state or across all states?
