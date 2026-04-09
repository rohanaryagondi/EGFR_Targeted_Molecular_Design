---
agent: Senior ML Researcher
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: compchem-P01
---

# Critique: Physics-Based Validation via Water Thermodynamics and Free Energy Perturbation

## Reviewing Agent
Senior ML Researcher -- expertise in publication strategy, benchmark methodology,
reviewer expectations at JCIM and Nature Computational Science, and prioritization of
experiments for maximum publication impact per unit compute.

## Proposal Summary
compchem-P01 proposes a three-tier physics-based validation stack: (1) GIST water
thermodynamic analysis to show the 4 EGFR conformational states present physically
distinct solvation environments, (2) OpenFE RBFE calculations on the top 20 candidates
to validate binding free energies beyond GNINA scoring, and (3) optional SQM2.20
rescoring as an intermediate physics tier. Estimated cost: 5-7 GPU-days over 3-4 weeks.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** GIST water analysis is a high-value, low-cost experiment that
strengthens the publication narrative, but FEP on 20 cherry-picked candidates carries
significant risk of undermining rather than supporting the paper, and the entire
proposal's priority ranking depends on the target venue.

---

## Strengths

1. **GIST is the single best cost-to-impact experiment in the proposal set.** At less
   than 2 GPU-days, Tier 1 produces a publication-quality figure that no reviewer can
   dismiss. The 4-panel water thermodynamic map showing distinct solvation environments
   across conformational states transforms the paper's core argument from "we observe
   different docking scores" to "we demonstrate physically different binding
   environments." This is the kind of figure that Nature Computational Science editors
   put on the cover. The proposal's literature evidence is strong: Robinson et al.
   (2010, 2014) on SRC, Kim et al. (2018) on PKA, Cyphers et al. (2017) on Aurora
   kinase all establish that water networks differ between kinase conformations. Applying
   this established methodology to EGFR in the context of state-aware design is a novel
   application with well-understood tools.

2. **The accuracy hierarchy framing is reviewer-ready.** The table showing GNINA at
   2-3 kcal/mol RMSE, SQM2.20 at ~1.5 kcal/mol, and FEP at 0.68-1.73 kcal/mol is
   exactly the kind of context that convinces reviewers the authors understand the
   limitations of their tools. This framing preempts the "GNINA is just docking"
   critique by showing the authors proactively moved up the accuracy ladder.

3. **Honest risk assessment.** The proposal acknowledges that FEP may disagree with
   GNINA rankings and frames this as a "valuable finding" rather than a failure. This
   is scientifically mature. The explicit discussion of 3W2R mutation concerns and 4ZAU
   state assignment shows structural awareness. The force field limitation discussion
   (OpenFF Sage coverage for unusual functional groups) reflects real practitioner
   knowledge.

4. **Well-structured tiered approach.** The three-tier design with Tier 1 (cheap,
   high-value) independent of Tier 2 (expensive, high-risk) allows the team to capture
   the biggest publication win first and make an informed decision about whether to
   proceed to FEP.

5. **Ensemble docking addresses a real limitation.** Moving from 1 crystal structure per
   state to 5-10 addresses the obvious reviewer critique about single-structure
   dependence. The published evidence (3-24% improvement in enrichment, Rueda et al.
   2014) sets appropriate expectations.

## Weaknesses

1. **FEP on 20 cherry-picked candidates is a selection bias trap.**
   - **Severity:** Major
   - **Addressable?** Yes, with protocol modifications (see Suggested Modifications)

   The proposal selects the "top 10 state-aware" and "top 10 static" candidates by
   unified score for FEP validation. This is textbook selection bias. A reviewer at
   any competent venue will write: "The authors selected candidates that already scored
   well under their scoring function, then validated those candidates with a more
   expensive method. This circular design cannot distinguish between 'the scoring
   function works' and 'FEP agrees with GNINA on the molecules where GNINA is most
   confident.'"

   The fundamental problem: GNINA is most likely to agree with FEP for the molecules
   it ranks most highly, because high-scoring molecules tend to have better poses and
   more straightforward binding modes. The interesting question -- does FEP rescue
   molecules that GNINA under-ranks, or sink molecules that GNINA over-ranks -- is
   invisible if you only validate the top 20.

   Moreover, if FEP disagrees with GNINA on some of the top 20, the proposal's
   framing of "report honestly" is correct but strategically dangerous. A paper that
   says "our top candidates don't survive physics-based validation" is harder to
   publish than one that never ran the validation. The proposal must have a clear plan
   for what to DO with FEP-GNINA disagreement, not just what to SAY about it.

2. **Compute budget is unrealistic if ABFE is needed.**
   - **Severity:** Major
   - **Addressable?** Yes, with explicit contingency budget

   The proposal estimates 120-180 GPU-hours for RBFE but then notes that ABFE may be
   needed for cross-series comparison at "20-40 GPU-hours per compound." With 20
   compounds, that is 400-800 GPU-hours additional -- tripling the compute budget.
   StateBind's VAE generates diverse chemotypes (chemical diversity 0.9056), making
   congeneric series unlikely. The proposal should assume ABFE as the baseline case,
   not RBFE.

   The OpenFE large-scale benchmark (Gapsys et al., 2025) reports weighted RMSE of
   1.73 kcal/mol on public data and 2.44 kcal/mol on private pharma data. The gap
   between these numbers is telling: in real campaigns with diverse chemotypes, FEP
   accuracy degrades. StateBind's VAE-generated molecules are closer to the "private"
   scenario than the "public" benchmark scenario.

3. **SQM2.20 is too niche to justify without strong contextualization.**
   - **Severity:** Minor
   - **Addressable?** Yes, by reframing

   SQM2.20 (Pecina et al., 2024) is a solid method, but it published in Nature
   Communications only in 2024 and has not yet achieved the widespread recognition
   that MM-GBSA or FEP have. Reviewers at JCIM will likely know it; reviewers at
   Nature Computational Science may not. The risk is that adding SQM2.20 as a third
   validation tier looks like the authors are padding the paper with validation methods
   rather than using the one that matters (FEP). The intermediate tier adds
   methodological complexity without proportional insight. If FEP agrees with GNINA,
   SQM2.20 is redundant. If FEP disagrees with GNINA, SQM2.20 sitting in between
   just confuses the narrative.

4. **The "5-7 GPU-day" compute estimate is misleadingly small relative to multi-kinase expansion.**
   - **Severity:** Minor
   - **Addressable?** Yes, by scoping decision

   The Round 2 synthesis notes that datasci-P01 (multi-kinase validation) requires 42
   GPU-days. If the project expands to ABL1 + BRAF + MET, does physics validation need
   to follow? Running GIST on 4 kinases x 3-4 states each = 12-16 GIST analyses,
   plus FEP on expanded candidate sets, could balloon to 30+ GPU-days. The proposal
   does not address whether physics validation is intended as EGFR-only or whether it
   must generalize with the multi-kinase expansion. This scoping decision materially
   affects prioritization.

---

## Feasibility Assessment

### Technical Feasibility
High for Tier 1 (GIST). GIST analysis with cpptraj is mature, well-documented, and
the proposal cites the correct tools and parameters. The protocol for GIST on a
restrained kinase is standard. AmberTools and OpenMM are available on Bouchet and
GPU-accelerated MD at 200-300 ns/day on H200 is realistic.

Moderate for Tier 2 (FEP). OpenFE is production-quality software, but FEP setup for
diverse chemotypes is a known pain point. The Kartograf atom mapper works well for
congeneric series but VAE-generated molecules with diverse scaffolds will likely require
manual intervention. The proposal acknowledges this but underestimates the setup time.
A realistic timeline for a first-time OpenFE user on a new system is 3-4 weeks for
setup and debugging alone, before production runs begin.

### Scientific Feasibility
Tier 1 is almost certain to produce clear results. Kinase conformational states are
known to have different water networks (the cited literature is compelling). The
question is magnitude, not direction.

Tier 2 is uncertain. FEP on VAE-generated molecules with unknown binding modes is
higher-risk than FEP on congeneric series from medicinal chemistry campaigns. The
molecules may adopt unexpected poses, have poor convergence, or reveal that GNINA's
poses (which are the starting point for FEP) are incorrect. Each of these failure
modes is informative but requires careful interpretation.

### Timeline Feasibility
Tier 1 at 1 week is realistic. Tier 2 at 2 weeks is optimistic -- 3-4 weeks is more
likely when accounting for setup, debugging, and convergence checking. Total: 4-5
weeks is more realistic than the stated 3-4 weeks.

---

## Suggested Modifications

1. **Prioritize Tier 1 unconditionally, make Tier 2 conditional on Tier 1 results.**
   GIST should run immediately regardless of any other decision. Its cost is trivial,
   its publication value is high, and it is independent of other proposals. FEP should
   be gated on: (a) GIST showing clear state differentiation (confirming the physics
   story is worth pursuing), and (b) a pilot run on 4-6 candidates to assess
   convergence and RBFE feasibility before committing to 20 candidates.

2. **Fix the selection bias in FEP candidate selection.** Instead of "top 10 per
   pipeline," sample candidates across the score distribution: top 5, middle 5, and
   bottom 5 from each pipeline, or use stratified random sampling. This allows the
   paper to claim "FEP validates the scoring function across the full score range,"
   not just "FEP agrees with GNINA on GNINA's favorites." At minimum, include 3-5
   known binders (erlotinib, gefitinib, osimertinib) as positive controls to anchor
   the FEP calculations.

3. **Drop SQM2.20 from the primary paper.** Report FEP as the gold standard and GIST
   as the mechanistic evidence. SQM2.20 can go in supplementary information as a
   robustness check, but including it in the main text dilutes the narrative. Reviewers
   will ask why three levels of validation are needed -- the answer ("because we do not
   trust any single method") is not confidence-inspiring.

4. **Scope physics validation to EGFR only.** GIST and FEP add the most value as deep
   dives on the flagship target. Multi-kinase expansion (datasci-P01) provides breadth;
   physics validation provides depth on one target. Attempting both breadth and depth
   across 4 kinases is computationally prohibitive and narratively unfocused for a
   single paper. A clear division of labor: "We validate breadth across kinases via
   retrospective enrichment, and depth on EGFR via physics-based methods" is a clean
   publication structure.

5. **Budget ABFE as the default, not RBFE.** Given StateBind's chemical diversity,
   assume ABFE will be needed for most cross-series comparisons. Budget 400-800
   GPU-hours for Tier 2 and plan for 4-5 weeks, not 2 weeks.

---

## Alternative Approaches

The same publication goal -- "validate that state-aware candidates are genuinely better
binders" -- could be achieved through alternative paths:

1. **GNINA ensemble consensus + bootstrapped rank stability.** Instead of FEP, re-dock
   all candidates against the 5-structure ensemble (already proposed) and compute
   rank stability across the ensemble. Candidates that rank consistently high across
   all 5 structures per state are more likely to be genuine binders. This costs 1
   GPU-day (vs 5-7 for FEP) and provides a physics-aware confidence estimate without
   the convergence and setup challenges of FEP. This is less rigorous than FEP but
   much more feasible and addresses the "single structure" critique.

2. **Delta-ML approach.** Run FEP on a small training set (10-15 molecules with known
   binding data from ChEMBL) and train a delta-correction from GNINA to FEP. Apply
   the correction to all 461 candidates. This is methodologically novel (Boyles et al.,
   2022, already cited in the proposal) and more publication-friendly than brute-force
   FEP on selected candidates. It also avoids the selection bias problem because the
   training set uses known binders rather than scored candidates.

3. **MM-GBSA as the validation tier.** Less accurate than FEP (RMSE 1.5-3.0 kcal/mol)
   but 100x cheaper and applicable to all candidates without congeneric series
   requirements. For JCIM, MM-GBSA is sufficient; for Nature Computational Science,
   FEP is expected. The venue choice dictates the validation method.

---

## Impact on Publication Narrative

### Does physics validation move the needle for reviewers?

This depends entirely on the target venue:

**For JCIM:** GIST water analysis is a strong differentiator. JCIM reviewers are
computational chemists who will immediately appreciate water thermodynamic maps
showing state-specific solvation. FEP is welcome but not required -- MM-GBSA or even
well-analyzed ensemble docking may suffice. GIST alone justifies physics validation for
JCIM. **Verdict: Tier 1 is high-impact at JCIM. Tier 2 is nice-to-have.**

**For Nature Computational Science:** The bar is higher. GIST is expected (reviewers
would wonder why you did not do it). FEP is the differentiator -- it shows the authors
went beyond standard practice. But FEP on cherry-picked candidates will be attacked.
FEP done correctly (stratified sampling, positive controls, reported honestly) is a
strong contribution. **Verdict: Both Tiers 1 and 2 are needed for Nature Comp Sci,
but Tier 2 must be done rigorously or not at all.**

**For NeurIPS Datasets & Benchmarks:** Physics validation is irrelevant. Reviewers are
ML researchers who care about baselines, ablations, and statistical power, not water
thermodynamics. **Verdict: Skip physics validation for this venue.**

### Priority ranking among the 5 proposals

From a pure publication-impact-per-compute perspective:

1. **mlres-P01 (External baselines):** P0. Without baselines, no venue accepts the
   paper. Non-negotiable.
2. **datasci-P01 (Multi-kinase expansion):** P0. Without statistical power, the
   enrichment claim is indefensible. Non-negotiable.
3. **medchem-P01 (Scoring revision):** P1. Addresses the "static wins on mean score"
   problem, which is the paper's most vulnerable point.
4. **compchem-P01, Tier 1 only (GIST):** P1. High-value, low-cost. Should run in
   parallel with P0 work.
5. **synthbio-P01 (End-to-end drug-ability):** P2. Differentiator for JCIM, not
   required for acceptance.
6. **compchem-P01, Tier 2 (FEP):** P2. Only justified for Nature Computational Science,
   and only if Tier 1 succeeds and the venue decision has been made.

GIST is priority 4 out of 6 workstreams -- it should start immediately because it is
cheap and independent, but it is not the bottleneck. FEP is priority 6 -- it should be
the last experiment attempted, only after baselines, multi-kinase, and scoring revision
are complete.

---

## References

1. Gapsys V, et al. Large-scale collaborative assessment of binding free energy
   calculations for drug discovery using OpenFE. ChemRxiv. 2025.
   doi:10.26434/chemrxiv-2025-7sthd

2. Boyles F, et al. Delta machine learning to improve scoring-ranking-screening
   performances of protein-ligand scoring functions. J Chem Inf Model. 2022;62(12):
   2965-2978. doi:10.1021/acs.jcim.2c00485

3. Robinson DD, et al. Understanding kinase selectivity through energetic analysis of
   binding site waters. ChemMedChem. 2010;5(4):618-627. doi:10.1002/cmdc.200900526

4. Kim J, et al. Water-mediated conformational preselection mechanism in substrate
   binding cooperativity to protein kinase A. PNAS. 2018;115(36):8997-9002.
   doi:10.1073/pnas.1720024115

5. Cyphers S, et al. A water-mediated allosteric network governs activation of Aurora
   kinase A. Nat Chem Biol. 2017;13:402-408. doi:10.1038/nchembio.2296

6. Pecina A, et al. SQM2.20: Semiempirical quantum-mechanical scoring function yields
   DFT-quality protein-ligand binding affinity predictions in minutes. Nat Commun.
   2024;15:1127. doi:10.1038/s41467-024-45431-8

7. Rueda M, et al. Assessing an ensemble docking-based virtual screening strategy for
   kinase targets by considering protein flexibility. J Chem Inf Model. 2014;54(10):
   2826-2836. doi:10.1021/ci500414b

8. Azimi S, et al. Relative binding free energy calculations for ligands with diverse
   scaffolds with the alchemical transfer method. J Chem Inf Model. 2022;62(2):
   309-323. doi:10.1021/acs.jcim.1c01129

9. Wang L, et al. Accurate and reliable prediction of relative ligand binding potency
   in prospective drug discovery by way of a modern free-energy calculation protocol
   and force field. J Am Chem Soc. 2015;137(7):2695-2703.
