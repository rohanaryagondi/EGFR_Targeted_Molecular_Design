---
agent: Maverick Data Scientist / Statistician
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: mlres-P01
---

# Critique: External Baseline Comparison Framework for StateBind Publication

## Reviewing Agent

Dr. Maverick Data Scientist / Statistician. Expertise in power analysis, enrichment
factor statistics, multiple testing correction, benchmark contamination and data leakage,
and pre-registration methodology. This review evaluates the statistical design of the
5-method comparison, the adequacy of sample sizes and power, the appropriateness of
the multiple testing correction, the pre-registered outcome-to-narrative mapping, and
a potential target leakage concern with MolCRAFT.

---

## Proposal Summary

mlres-P01 proposes running 5 molecular generation methods on the EGFR task (REINVENT 4,
MolCRAFT, StateBind conditioned VAE, StateBind unconditioned VAE ablation, and
random/similarity ChEMBL baselines), all evaluated under the same unified scoring
function and retrospective time-split protocol. Five pre-registered outcome-to-narrative
mappings define how each possible result pattern translates into a publication claim.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** This is the single most important proposal in the IdeationDept
portfolio -- external baselines are a non-negotiable publication requirement -- but the
statistical protocol has specific gaps in power analysis, multiple testing methodology,
and leakage assessment that must be addressed to withstand peer review.

---

## Strengths

1. **The proposal correctly identifies this as a P0 priority.** Without external
   baselines, the paper is desk-rejected. This is not speculation -- it is the
   universal consensus of the IdeationDept team and reflects the current state of
   the field. The PMO benchmark (Gao et al. 2022) and the "Beyond Affinity" benchmark
   (arXiv 2601.14283, 2025) have established that multi-method comparison is the
   minimum standard for any molecular generation paper. The proposal positions StateBind
   within this landscape rather than in isolation.

2. **The unconditioned VAE ablation is correctly identified as the decisive experiment.**
   The proposal devotes appropriate emphasis to this ablation: it is the experiment that
   isolates state-conditioning from VAE diversity. The 4-way confound in the current
   comparison (state awareness, generation method, candidate count, diversity) cannot
   be resolved without this experiment. I note with approval that the proposal specifies
   identical hyperparameters, training data, epoch count, and latent dimension, differing
   only in the zeroed state vector. This is a clean ablation design.

3. **The pre-registered outcome-to-narrative mapping is excellent methodology.** The 5
   outcome scenarios (state-aware dominates, helps modestly, diversity drives, 3D
   subsumes, REINVENT dominates) are well-constructed and each maps to a specific,
   publishable narrative. This eliminates the most common criticism of generative design
   papers: that the narrative was constructed post-hoc to match the results. The proposal
   correctly recommends posting on OSF with a timestamp.

4. **The random ChEMBL baseline with 100 draws provides a proper null distribution.**
   Sampling 461 random drug-like molecules 100 times and scoring all with the unified
   function creates an empirical null distribution for EF@10, enabling formal hypothesis
   testing (is any method's enrichment significantly above random?). This is statistically
   correct and provides the foundation for p-value computation.

5. **The fingerprint similarity baseline tests the fundamental value proposition.**
   If similarity search of existing databases matches generative methods, the entire
   field's premise (that generation adds value over retrieval) is challenged. This is
   an uncomfortable but necessary comparison that most papers avoid. Including it
   demonstrates intellectual honesty.

6. **Per-method failure rate tracking is good practice.** The proposal explicitly tracks
   invalid SMILES, failed chemistry, and failed docking rates, and reports
   "valid-candidate yield" as a metric. This is important because methods with high
   failure rates effectively generate fewer candidates, creating an implicit confound
   in any fixed-N comparison.

---

## Weaknesses

1. **Is 1000 molecules per method sufficient for robust enrichment comparison? No power
   analysis is provided.**

   - **Severity:** Major
   - **Addressable?** Yes -- add a formal power analysis

   The proposal fixes N=1000 generated molecules per method (250 per state x 4 states),
   subsampled to N=461 for comparison. But the enrichment factor is computed against
   N=3-5 held-out approved drugs. The question is: given the variance inherent in EF@10
   with N_drugs=5, what is the power to detect a meaningful difference BETWEEN two
   methods' enrichment factors?

   Let me be concrete. Under the pre-2010 time-split with N_drugs=5:
   - EF@10 can take values 0, 2, 4, 6, 8, 10 (it is 0, 1/5, 2/5, ... of the drugs
     in the top 10%, multiplied by 1/0.10 = 10).
   - If method A places 3/5 drugs in the top 10% and method B places 1/5, the EF@10
     values are 6.0 and 2.0 respectively.
   - But these are point estimates from a single realization. A bootstrap over
     candidates provides CIs on the ranking, not on the number of drugs captured.
   - The fundamental constraint is that N_drugs=5 creates discrete jumps of 2.0 in
     EF@10. You cannot detect differences smaller than this.

   The proposal should include an explicit power analysis:
   - Under the null hypothesis that two methods have equal probability of placing a
     drug in the top 10%, what sample size (N_drugs) gives 80% power to detect a 2x
     difference in enrichment at alpha=0.005 (Bonferroni-corrected)?
   - Using Fisher's exact test or a permutation test on the 2x2 table {method} x
     {drug in top 10% or not}, with N_drugs=5, the power to detect an odds ratio of
     5x at alpha=0.005 is approximately 15-25%. This is catastrophically underpowered.
   - With N_drugs=15-20 (from multi-kinase expansion via datasci-P01), power rises to
     approximately 60-75%. This underscores that mlres-P01 DEPENDS on datasci-P01's
     multi-kinase expansion to achieve adequate statistical power.

   The candidate count (461 vs 1000) primarily affects the resolution of the ranking,
   not the power of the enrichment comparison. The bottleneck is N_drugs, not N_candidates.
   The proposal should explicitly state this dependency and note that the EGFR-only
   comparison will be underpowered for formal hypothesis testing. The multi-kinase
   pooled analysis is where statistical significance becomes achievable.

   For the candidate-level metrics (mean score, diversity, validity), 461 candidates
   per method provides adequate power. A Mann-Whitney U test on unified scores with
   N1=N2=461 has >99% power to detect a Cohen's d of 0.3 at alpha=0.005. So
   distributional comparisons are well-powered; enrichment comparisons are not.

2. **The 5 pre-registered outcome-to-narrative mappings are not exhaustive and contain
   a gap.**

   - **Severity:** Moderate
   - **Addressable?** Yes -- add missing scenarios

   The 5 outcomes assume a clean ordering of methods. Several plausible scenarios are
   missing:

   **Missing Outcome 6: Time-split inconsistency.** The conditioned VAE wins at pre-2010
   but loses at pre-2015 (or vice versa). This is plausible because the held-out drugs
   differ between splits, and N is tiny. What narrative applies? If the pre-registered
   plan does not address this, the authors will be forced into post-hoc rationalization.

   **Missing Outcome 7: No method significantly outperforms the similarity search
   baseline.** This is distinct from Outcome 5 (REINVENT dominates). If the fingerprint
   similarity search achieves enrichment comparable to all generative methods, the
   narrative shifts from "which generator is best?" to "generation adds no value over
   retrieval for EGFR." The proposal briefly mentions this possibility but does not
   pre-register a narrative for it.

   **Missing Outcome 8: The unconditioned VAE outperforms the conditioned VAE.** Outcome
   3 covers "approximately equal." But what if unconditioned is significantly BETTER?
   This could happen if state-conditioning constrains the VAE's latent space in a way
   that reduces diversity below the optimum. The narrative would be "state-conditioning
   is counterproductive: it restricts chemical diversity without compensating benefit."

   **Recommendation:** Add these 3 scenarios to the pre-registered mapping. The goal is
   not to predict every possible result but to ensure that no result pattern forces
   post-hoc narrative construction. The coverage should be exhaustive over the
   qualitatively distinct orderings of 5 methods.

3. **Bonferroni correction across 10 pairwise comparisons is overly conservative.
   Benjamini-Hochberg would be more appropriate.**

   - **Severity:** Moderate
   - **Addressable?** Yes -- switch to BH or use a structured comparison plan

   The proposal specifies Bonferroni correction for 10 pairwise comparisons (5 methods
   choose 2), yielding an effective alpha of 0.005 per test. For the candidate-level
   metrics (Mann-Whitney U on unified scores), this is feasible because the tests are
   well-powered with N=461.

   But for enrichment comparisons with N_drugs=5, Bonferroni at alpha/10 = 0.005 is
   devastating: even a true 5x enrichment difference has near-zero power at this
   threshold. Benjamini-Hochberg (BH) controls the false discovery rate (FDR) rather
   than the family-wise error rate (FWER). With 10 tests, BH at q=0.05 accepts the
   largest p-value below 0.05*(10/10) = 0.05, the next below 0.05*(9/10) = 0.045, etc.
   This is substantially less conservative and more appropriate for an exploratory
   comparison study.

   The choice between Bonferroni and BH depends on the study's inferential goal. For
   a confirmatory study (testing a single pre-specified hypothesis), Bonferroni is
   appropriate. For an exploratory comparison of 5 methods (which this is), BH is
   standard. The Polaris consortium guidelines (JCIM 2025) recommend BH for method
   comparison studies with >5 pairwise tests.

   **Structured alternative:** Instead of correcting for all 10 pairwise comparisons,
   define a pre-specified comparison hierarchy:
   - **Primary comparison:** Conditioned VAE vs unconditioned VAE (tests the thesis).
     No correction needed -- single test.
   - **Secondary comparisons:** Conditioned VAE vs REINVENT, conditioned VAE vs MolCRAFT
     (2 tests). BH correction at q=0.05.
   - **Exploratory comparisons:** All remaining pairs (7 tests). BH correction at
     q=0.10.

   This hierarchical approach allocates the most statistical power to the most important
   comparison and is standard in clinical trial design (Bretz et al., 2009, Statistics
   in Medicine).

4. **The unconditioned VAE ablation specification must be consistent with datasci-P01.**

   - **Severity:** Moderate
   - **Addressable?** Yes -- harmonize the specifications

   Both mlres-P01 and datasci-P01 propose an unconditioned VAE ablation, but there are
   subtle specification differences that must be reconciled:

   | Parameter | mlres-P01 | datasci-P01 |
   |-----------|-----------|-------------|
   | State vector | "zeroed out (replaced with a constant zero vector)" | "no state vector" |
   | N generated | 1000, subsampled to 461 | ~400 |
   | Seeds | 3 independent | Not specified for EGFR |
   | Training data | "Same training data" | "Same training data" |
   | Epochs | 300 | Not specified |
   | Evaluation | Unified scoring + retrospective | BEDROC as primary |

   The discrepancy in how the state vector is handled (zeroed vs removed) may produce
   different model behaviors. A zero vector is not the same as no conditioning signal:
   the decoder still has the conditioning pathway, it just receives zeros. If the model
   has learned to use the conditioning pathway (e.g., if the decoder has a non-zero bias
   on the conditioning input), a zero vector is a specific conditioning signal, not an
   unconditioned generation. The correct approach is to remove the conditioning pathway
   entirely from the architecture, or equivalently, to use a separate architecture
   identical in all other respects but without the conditioning input layer.

   Additionally, the subsampling strategy differs: mlres-P01 generates 1000 and
   subsamples to 461; datasci-P01 generates ~400 directly. These yield different
   candidate pools. To ensure consistency, both proposals should use the same
   unconditioned VAE checkpoint and the same candidate pool.

   **Recommendation:** Create a single shared specification document for the
   unconditioned VAE ablation. Both proposals reference this specification. The
   specification should address: (a) whether the state vector is zeroed or the
   conditioning pathway is removed (I recommend removal), (b) the exact number of
   molecules generated before subsampling, (c) the subsampling strategy (random vs
   top-scoring), and (d) the number of independent training seeds.

5. **MolCRAFT zero-shot: potential target leakage from CrossDocked2020 training data.**

   - **Severity:** Major
   - **Addressable?** Yes -- verify and document

   MolCRAFT was pre-trained on CrossDocked2020, which was constructed by cross-docking
   PDB ligands into structurally similar binding pockets across the entire PDB
   (Francoeur et al., JCIM 2020). CrossDocked2020 contains 22.5 million poses derived
   from PDB protein-ligand complexes. EGFR is one of the most structurally characterized
   kinases in the PDB, with 200+ crystal structures. It is virtually certain that
   CrossDocked2020 contains EGFR binding pocket structures and EGFR-bound ligands.

   This creates a potential target leakage concern: MolCRAFT's generative model may
   have seen EGFR pocket geometries and EGFR-bound small molecules during training.
   When asked to generate molecules for EGFR pockets in a "zero-shot" setting, it
   is not truly zero-shot with respect to the target -- it is zero-shot only with
   respect to the specific held-out drugs.

   The severity of this leakage depends on what MolCRAFT learned:
   - If MolCRAFT learned general pocket-to-ligand mapping (desirable generalization),
     EGFR pocket exposure during training is not problematic.
   - If MolCRAFT memorized specific EGFR-ligand associations, its performance on EGFR
     is inflated relative to a truly novel target.

   The proposal acknowledges this partially by noting MolCRAFT "was trained on
   CrossDocked2020 structural data, not EGFR activity data." But the distinction between
   "structural data" and "activity data" is blurred: CrossDocked2020 contains co-crystal
   structures of EGFR with known inhibitors, which implicitly encodes activity
   information (these molecules are binders).

   **Required investigation:**
   1. Determine exactly which EGFR PDB structures appear in CrossDocked2020's training
      set. The dataset's types files at https://github.com/gnina/models list all
      PDB codes used.
   2. Check whether the 4 EGFR structures used by StateBind (1M17, 2GS7, 3W2R, 4ZAU)
      or closely related structures appear in the training set.
   3. Check whether any of the held-out approved EGFR drugs (afatinib, dacomitinib,
      osimertinib, lazertinib, sunvozertinib) appear as ligands in CrossDocked2020
      training structures.
   4. If EGFR structures ARE in the training set (likely), document this as a known
      limitation and discuss the implications. MolCRAFT's EGFR performance should be
      interpreted as an upper bound on what a 3D method achieves with pocket familiarity.
   5. If any held-out drugs appear as training ligands, the retrospective enrichment
      comparison is compromised for MolCRAFT and must be flagged.

   This investigation is straightforward (download the types files, grep for EGFR PDB
   codes) and must be done before claiming the comparison is fair.

6. **The state-specificity score creates a systematic 15% handicap for non-state-aware
   methods.**

   - **Severity:** Moderate
   - **Addressable?** Yes -- report both with and without state specificity component

   The proposal notes that non-state-aware methods (unconditioned VAE, random, similarity
   search) receive state specificity = 0.0, losing 15% of the maximum unified score.
   REINVENT and MolCRAFT receive state specificity = 1.0 because molecules are assigned
   to the pocket they were generated for. This creates a systematic bias: methods without
   explicit state assignment are handicapped by 0.15 * 1.0 = 0.15 points on a [0, 1]
   scale.

   The proposal mentions reporting "results both with and without the state specificity
   component" as an alternative but does not commit to this. This should be mandatory,
   not optional. Specifically:

   - **Primary comparison (4 components):** Use the original 4-component scoring with
     state specificity included, as designed. This is the fair comparison for the
     thesis claim.
   - **Secondary comparison (3 components):** Remove state specificity, re-normalize
     weights to sum to 1.0 over the remaining 3 components. This tests whether
     methods differ on "drug quality" independent of state assignment.

   The primary comparison tests: "Is state-aware generation better overall, including
   its state specificity advantage?" The secondary tests: "Do state-aware candidates
   have better drug-like properties (affinity, drug-likeness, similarity) even when
   the state specificity bonus is removed?" If state-aware wins on both, the case is
   strong. If it wins only on the primary (with state specificity), a reviewer could
   argue the advantage is tautological -- the model was trained to assign states, so
   of course it gets the state specificity bonus.

---

## Feasibility Assessment

### Technical Feasibility

Moderate-High. REINVENT 4 installation and GNINA plugin development are the main
technical risks. The proposal acknowledges this and provides a fallback (AutoDock Vina).
MolCRAFT zero-shot setup is lower risk (pre-trained checkpoint, documented inference).
The unconditioned VAE requires only a configuration change. The random and similarity
baselines are trivial. Overall, the technical plan is realistic.

### Scientific Feasibility

High, conditional on the multi-kinase expansion from datasci-P01. On EGFR alone, the
enrichment comparisons will be underpowered (N_drugs=5 is insufficient for pairwise
significance testing at any reasonable alpha). The distributional comparisons (mean
score, diversity, validity) will be well-powered. The proposal's scientific value is
maximized when combined with datasci-P01 to pool enrichment across 4+ kinases.

### Timeline Feasibility

The 3-4 week estimate is optimistic. REINVENT 4 + GNINA integration could consume 2
weeks alone if debugging is required. A more realistic estimate is 4-6 weeks, with
REINVENT integration as the critical path. The fallback to Vina scoring mitigates this
but introduces a non-identical scoring concern. The unconditioned VAE training (3 seeds
x 300 epochs) may require 1-2 days of GPU time each, which is straightforward on
Bouchet's H200 nodes.

---

## Suggested Modifications

1. **Add a formal power analysis for enrichment comparisons.** Compute the minimum
   N_drugs needed to detect a 2x enrichment difference between any two methods at
   alpha=0.005 (Bonferroni) or q=0.05 (BH) with 80% power. Use Fisher's exact test
   or a permutation framework. Report this power analysis in the paper's methods
   section. Explicitly state that the EGFR-only comparison is underpowered for
   enrichment and that the multi-kinase expansion (datasci-P01) provides the
   necessary sample size.

2. **Replace Bonferroni with Benjamini-Hochberg for the full pairwise comparison,
   or adopt a hierarchical testing strategy.** The hierarchical approach is more
   powerful and more interpretable:
   - Tier 1 (no correction): conditioned VAE vs unconditioned VAE (the thesis test).
   - Tier 2 (BH at q=0.05): conditioned VAE vs REINVENT, conditioned VAE vs MolCRAFT.
   - Tier 3 (BH at q=0.10): all remaining pairwise comparisons.
   Pre-specify this hierarchy in the analysis plan.

3. **Add 3 missing outcome scenarios to the pre-registered mapping.** At minimum:
   (6) time-split inconsistency, (7) similarity search matches all generative methods,
   (8) unconditioned VAE outperforms conditioned VAE. Each needs a pre-specified
   narrative and venue implication.

4. **Harmonize the unconditioned VAE specification with datasci-P01.** Create a single
   shared specification covering: conditioning pathway removal (not zeroing),
   generation count, subsampling strategy, and seed count. Both proposals reference
   this specification. The unconditioned VAE checkpoint and candidate pool should be
   identical across both proposals.

5. **Investigate and document CrossDocked2020 EGFR content.** Before running MolCRAFT,
   download the CrossDocked2020 types files from the gnina/models GitHub repository.
   Search for EGFR PDB codes (1M17, 2GS7, 3W2R, 4ZAU, and related structures like
   1M14, 2J6M, 4HJO, etc.). Search for held-out drug ligand names. Document findings
   in the methods section. If EGFR structures are present (highly likely), add a
   "MolCRAFT performance should be interpreted as having pocket familiarity with EGFR"
   caveat. If held-out drugs are present as training ligands, flag this as a critical
   leakage concern and consider excluding MolCRAFT from the retrospective enrichment
   comparison (retaining it for distributional comparisons only).

6. **Report the 3-component comparison (without state specificity) as a mandatory
   secondary analysis.** This is not optional. It directly addresses the reviewer
   concern that the state-aware advantage is tautological (the model gets credit for
   doing the thing it was trained to do). If state-aware candidates are better even
   without the state specificity bonus, the case is strong.

7. **Use BEDROC(alpha=20) as the primary enrichment metric alongside EF@10.** The
   proposal lists BEDROC in the metrics table but does not designate it as primary or
   secondary. BEDROC is superior to EF for the reasons documented in datasci-P01
   (Truchon & Bayly 2007): threshold-independence, well-understood null distribution,
   exponential early-rank weighting. Designate BEDROC as the primary enrichment metric
   for the pre-registered analysis plan, with EF@10 and EF@5 as secondary.

---

## Alternative Approaches

**Alternative 1: Paired comparison via shared candidate re-ranking.** Rather than
having each method generate its own candidate pool, generate a SINGLE large candidate
pool (union of all methods' outputs) and rank it under different scoring regimes (one
per method's scoring philosophy). This tests whether methods differ in what they
generate vs how they rank. However, this fundamentally changes the comparison from
"which method generates better candidates?" to "which scoring regime better ranks a
shared pool," which is a different scientific question.

**Alternative 2: Bootstrap-paired comparisons.** Instead of comparing EF@10 point
estimates across methods, use a paired bootstrap: for each bootstrap sample of the
held-out drugs, compute EF@10 for all 5 methods, then compute pairwise differences
within each bootstrap sample. The 95% CI on the pairwise difference directly tests
whether method A's enrichment significantly exceeds method B's. This is more powerful
than independent CIs because it accounts for the correlation between methods evaluated
on the same held-out drugs. Ash & Bhardwaj (J Cheminformatics 2022) provide the
framework for confidence bands on enrichment curves that enables this paired comparison.

**Alternative 3: Nested model comparison instead of pairwise testing.** Instead of
testing all pairs, define a nested sequence of models:
  1. Random baseline (no information)
  2. Similarity search (known-drug information only)
  3. Unconditioned VAE (learned chemistry, no state)
  4. Conditioned VAE (learned chemistry + state)
  5. REINVENT (RL optimization + pocket)
  6. MolCRAFT (3D pocket conditioning)

Test whether each step in the hierarchy provides significant improvement over the
previous step. This reduces the number of tests from 10 to 5 and aligns with a
natural "what does each component add?" narrative.

---

## Impact on Publication Narrative

This proposal is the backbone of the publication. Without it, there is no paper. With
it (and with the statistical modifications above), the paper can make one of three
honest claims:

1. **Best case:** "State-aware generation outperforms all baselines, including
   unconditioned VAE, REINVENT, and MolCRAFT, on retrospective enrichment. The
   advantage is attributable to conformational state-conditioning, not to VAE diversity
   or candidate count."

2. **Good case:** "State-aware generation matches or exceeds external baselines while
   providing unique state-specificity information. The advantage over unconditioned VAE
   confirms that state-conditioning provides incremental benefit."

3. **Honest case:** "State-conditioning does not provide significant enrichment benefit
   beyond diverse generation (unconditioned VAE matches conditioned). However, the
   state-aware framework generates candidates with explicit conformational preferences,
   enabling selectivity-aware design. This is a distinct contribution from raw enrichment."

All three are publishable at JCIM. Case 1 is publishable at Nature Computational
Science if multi-kinase validation (datasci-P01) confirms the finding. The pre-
registration ensures that whichever case emerges, the paper reports it honestly.

The critical dependency between mlres-P01 and datasci-P01 must be acknowledged: the
multi-kinase expansion is not a separate project but the statistical power source that
makes the enrichment comparisons in mlres-P01 meaningful. These two proposals should
be treated as a single experimental program.

---

## References

1. Gao W, et al. (2022). Sample Efficiency Matters: A Benchmark for Practical Molecular
   Optimization. *NeurIPS Datasets & Benchmarks*. arXiv:2206.12411 -- PMO benchmark
   establishing REINVENT as the minimum required baseline.

2. Truchon JF, Bayly CI. (2007). Evaluating Virtual Screening Methods: Good and Bad
   Metrics for the Early Recognition Problem. *JCIM*, 47(2):488-508. DOI:
   10.1021/ci600426e -- BEDROC as superior enrichment metric.

3. Ash JR, Bhardwaj RM. (2022). Confidence bands and hypothesis tests for hit
   enrichment curves. *J Cheminformatics*, 14:48. DOI: 10.1186/s13321-022-00629-0 --
   Framework for paired bootstrap comparison of enrichment curves.

4. Bretz F, Maurer W, Brannath W, Posch M. (2009). A graphical approach to sequentially
   rejective multiple test procedures. *Statistics in Medicine*, 28(4):586-604. --
   Hierarchical testing strategies for structured comparisons.

5. Benjamini Y, Hochberg Y. (1995). Controlling the false discovery rate: a practical
   and powerful approach to multiple testing. *JRSS Series B*, 57(1):289-300. -- BH
   procedure; standard reference.

6. Francoeur PG, et al. (2020). Three-Dimensional Convolutional Neural Networks and a
   Cross-Docked Data Set for Structure-Based Drug Design. *JCIM*, 60(9):4200-4215. DOI:
   10.1021/acs.jcim.0c00411 -- CrossDocked2020 dataset; 22.5M poses from PDB-wide
   cross-docking. EGFR structures highly likely included.

7. Nicholls A. (2016). Confidence limits, error bars, and method comparison in molecular
   modeling. *JCAMD*, 30:103-126. DOI: 10.1007/s10822-015-9861-4 -- EF variance with
   <20 actives is "extremely large."

8. Polaris Consortium. (2025). Practically significant method comparison protocols for
   molecular property prediction. *JCIM*, 65:18. -- BH recommended for method comparison
   studies; multi-dataset evaluation standard.

9. Clark RD, Webster-Clark DJ. (2016). Managing bias in ROC curves. *J Cheminformatics*,
   8:1-17. DOI: 10.1186/s13321-016-0189-4 -- Power metric as additional robust
   enrichment measure.

10. Qu Y, et al. (2024). MolCRAFT: Structure-Based Drug Design in Continuous Parameter
    Space. *ICML*. arXiv:2404.12141 -- Pre-trained on CrossDocked2020; HuggingFace
    checkpoint.

11. Empereur-mot C, et al. (2022). EmProc: Enrichment confidence bands for hit
    enrichment curves. *J Cheminformatics*, 14:48. -- Proper inference on enrichment
    curves is "almost never considered."

12. Sorgenfrei FA, et al. (2024). Kinase-Bench: Comprehensive Benchmarking Tools and
    Guidance for Achieving Selectivity in Kinase Drug Discovery. *JCIM*, 64(24):
    9528-9550. -- 6875 selective ligands, 75 kinases.
