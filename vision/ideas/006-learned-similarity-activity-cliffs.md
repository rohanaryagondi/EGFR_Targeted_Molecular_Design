# 006: Learned Chemical Similarity from Activity Cliffs

**Category:** ML Improvements, Scientific Rigor
**Priority:** P1: High
**Status:** proposed
**Date proposed:** 2026-03-30
**Effort:** Medium (1-2 weeks)

## Summary

Replace the reference similarity component (35% of scoring weight -- the heaviest single component) with a learned similarity metric trained on thousands of EGFR-active compounds from ChEMBL. Instead of computing Morgan fingerprint Tanimoto similarity to just 3 approved drugs, train a contrastive learning model that learns what makes a molecule "EGFR-like" from the full landscape of known EGFR binders. This captures diverse binding modes, accounts for activity cliffs (structurally similar molecules with vastly different activity), and removes the severe bias toward existing drug scaffolds.

## The Problem

Per `known-limitations.md` (Section 1.2), the reference similarity component computes Tanimoto similarity against exactly 3 approved EGFR drugs: erlotinib, gefitinib, and osimertinib. This is 35% of the total score -- the most influential component -- and it is computed against the narrowest possible reference set. This creates a severe scaffold bias: candidates that look like existing drugs score well, while structurally novel chemotypes that bind EGFR through different interactions are penalized.

Per `known-limitations.md` (Section 5, point 2), peer reviewers will immediately ask "Why only 3 reference molecules for 35% of the score?" ChEMBL contains thousands of compounds with measured EGFR IC50 < 100 nM spanning diverse chemical scaffolds (quinazolines, pyrimidines, indoles, macrocycles, covalent warheads). Using only 3 molecules throws away this information.

Furthermore, Tanimoto similarity on Morgan fingerprints is a crude metric. It measures structural resemblance but not biological activity. Activity cliffs -- pairs of molecules that differ by a single atom but have 100-fold different potency -- are invisible to Tanimoto. A learned metric could capture these non-obvious structure-activity relationships.

## The Vision

After this improvement:

- **Similarity is computed against the full EGFR-active chemical space.** Instead of max Tanimoto to 3 drugs, the score reflects how "EGFR-like" a candidate is based on patterns learned from thousands of known binders.
- **Activity cliffs are modeled.** The learned metric captures that a specific fluorine substitution converts a weak binder to a potent one -- something Tanimoto cannot detect.
- **Diverse chemotypes are rewarded.** A novel scaffold that the model recognizes as EGFR-compatible (based on pharmacophoric patterns shared with known binders) scores well even if it looks nothing like erlotinib.
- **The similarity metric is state-conditioned.** Different conformational states may favor different chemical features. The learned metric can be conditioned on state, assigning different similarity scores depending on which pocket the candidate targets. This would give the state-aware pipeline a new advantage in the heaviest scoring component.

## Impact Assessment

**Significant.** This directly improves 35% of the unified score -- the single largest component. It removes the most obvious bias in the scoring function and adds scientific depth. State-conditioned learned similarity would also give the state-aware pipeline an additional advantage axis beyond the current 15% state specificity component.

Affects: reference similarity scoring (35% weight), training data pipeline (ChEMBL EGFR data), evaluation (diversity of high-scoring candidates).

## Effort Estimate

Medium. Contrastive learning on molecular representations is well-established. The ChEMBL EGFR data is already partially curated (1,678 compounds for MPNN training). Expanding to all EGFR-active compounds and training a contrastive model is a focused ML task. 1-2 weeks for a skilled agent.

## Dependencies

- ChEMBL EGFR bioactivity data (larger set than the current 1,678 -- include all compounds with IC50 data)
- Morgan fingerprints or GNN-based molecular representations (from chemistry module or MPNN encoder)
- Contrastive learning framework (can use SimCLR-style or triplet loss)
- The existing scoring pipeline (to integrate the new metric)

## Implementation Sketch

1. **Data curation: `scripts/build_egfr_similarity_dataset.py`** -- Pull all EGFR bioactivity data from ChEMBL. Label: active (pIC50 >= 6.0, i.e., IC50 < 1 uM) vs inactive/weak (pIC50 < 5.0). This creates ~5,000+ active and ~10,000+ inactive/weak EGFR compounds.

2. **Model architecture: new `ml/similarity.py`** -- Contrastive learning model. Architecture:
   - Encoder: shared MLP or GNN on Morgan fingerprints/molecular graphs -> 128-dim embedding
   - Training: triplet loss or NT-Xpair (SimCLR-style). Positive pairs: two EGFR actives. Negative pairs: one active + one inactive. Hard negative mining: actives with high Tanimoto but low potency (activity cliffs).
   - Output: a similarity function `sim(candidate, EGFR_space) -> [0, 1]` computed as cosine similarity to the centroid of active compound embeddings, or as the maximum similarity to the K nearest active neighbors.

3. **State conditioning (optional, high-value extension):** If conformational state labels are available for training compounds (e.g., from co-crystal structures with different EGFR states), train the encoder with state as a conditioning variable. Then `sim(candidate, state=DFGout_aCout)` measures how similar the candidate is to known binders of the inactive state specifically.

4. **Scoring integration: modify `baselines/scoring.py`** -- Replace `_score_reference_similarity()` with the learned metric. Maintain the Morgan Tanimoto fallback when the learned model is unavailable. The fallback chain: learned similarity -> Morgan Tanimoto to full reference set -> Morgan Tanimoto to 3 drugs -> n-gram Tanimoto.

5. **Testing** -- Verify known EGFR drugs score highly. Verify known non-EGFR-binding molecules (decoys) score lowly. Verify the learned metric captures activity cliffs that Tanimoto misses (identify pairs from ChEMBL where Tanimoto > 0.8 but activity differs > 100-fold).

## Open Questions

- How many EGFR-active compounds are in ChEMBL? A quick search would reveal the exact count. Need the Assistant AI to check.
- Should the encoder use Morgan fingerprints (fast, no GPU needed for inference) or GNN (more expressive, requires torch)? A Morgan-fingerprint-based encoder keeps the scoring function lightweight.
- Is state-conditioned similarity feasible given the available data? How many co-crystal structures exist per conformational state? This may be too sparse for training.
- How to calibrate the learned similarity to the [0, 1] range for compatibility with existing scoring weights?
