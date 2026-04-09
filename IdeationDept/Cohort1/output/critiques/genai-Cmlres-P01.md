---
agent: Maverick Generative AI Specialist
round: 3
date: 2026-04-08
type: critique
proposal_reviewed: mlres-P01
---

# Critique: External Baseline Comparison Framework for StateBind Publication

## Reviewing Agent
Dr. Maverick Generative AI Specialist -- expertise in 3D pocket-conditioned molecular
generation, diffusion and flow matching architectures, SE(3)-equivariant networks,
and benchmark methodology for structure-based drug design. Bringing the perspective
of someone who has surveyed the full 3D generation landscape (DiffSBDD, TargetDiff,
MolCRAFT, FLOWR, MolFORM, 3DSMILES-GPT, Apo2Mol) and understands the nuances of
comparing 1D, 2D, and 3D generation paradigms on the same task.

## Proposal Summary
mlres-P01 proposes running 5 molecular generation methods on EGFR (REINVENT 4,
MolCRAFT, conditioned VAE, unconditioned VAE, random ChEMBL + fingerprint similarity)
under StateBind's unified scoring function and retrospective time-split protocol, with
pre-registered outcome-to-narrative mappings, bootstrap confidence intervals, and a
3-4 week timeline at approximately 40 GPU-hours.

---

## Overall Assessment

**Verdict:** Support with Modifications

**One-line take:** The framework is well-structured and the pre-registered outcome
mapping is a genuine methodological strength, but the 3D baseline selection is outdated,
the REINVENT "state-awareness" design is conceptually flawed, and the comparison as
proposed answers "which generator is best at this task?" more than it answers "does
state-conditioning help?" -- and those are critically different questions.

---

## Strengths

1. **Pre-registered outcome-to-narrative mapping is exceptional.** The five pre-defined
   outcome interpretations (Section "Pre-Registered Framing Strategy") are the single
   best idea in this proposal. By committing to a publishable narrative for every possible
   result pattern -- including the null hypothesis that diversity drives enrichment and the
   uncomfortable outcome where REINVENT dominates -- the proposal eliminates post-hoc
   rationalization. This is increasingly valued at top venues. The recommendation to post
   on OSF with a timestamp is sound and would differentiate the paper from the large
   majority of SBDD publications that fit narratives to results. This alone justifies the
   framework.

2. **The unconditioned VAE ablation is correctly identified as the most important
   experiment.** The proposal is right that this is "the single most important experiment
   in the entire framework." The conditioned-vs-unconditioned comparison is the cleanest
   test of whether state labels add signal beyond chemical diversity. The design -- same
   architecture, same hyperparameters, same training data, state vector zeroed out -- is
   methodologically correct and avoids the confounds that plague the current static-vs-
   state-aware comparison (different candidate counts, different diversity, different
   generation method). Three independent seeds with bootstrap CIs is appropriate. This
   experiment should run first, regardless of whether the external baselines proceed.

3. **Unified scoring across all methods is essential and correctly enforced.** Requiring
   all methods to be evaluated by the same unified scoring function (same 4 components,
   same weights) prevents the common benchmarking error of comparing methods on their
   own preferred metrics. The proposal explicitly forbids per-method scoring adjustments
   and includes a 100-configuration Dirichlet weight sensitivity analysis. This is
   rigorous.

4. **The random ChEMBL and fingerprint similarity baselines provide critical calibration.**
   These two "dumb" baselines establish the floor and the naive-retrieval ceiling. The
   100 random draws for a null distribution is statistically sound. The fingerprint
   similarity baseline -- which tests whether generation adds value over database
   retrieval -- is an underappreciated control that most generation papers omit.

5. **Practical compute estimates are realistic.** The approximately 40 GPU-hour total
   is achievable on a single H200 node in 1-2 days. The 3-4 week timeline for the full
   pipeline (including infrastructure setup, generation, scoring, statistical analysis)
   is honest and accounts for the inevitable debugging of REINVENT + GNINA integration.

---

## Weaknesses

1. **MolCRAFT is the wrong 3D baseline -- or at minimum, an incomplete one.**

   The proposal selects MolCRAFT as the sole 3D structure-based representative, citing
   its reference-level Vina scores and 30x speed advantage over diffusion. But MolCRAFT
   uses Bayesian Flow Networks (BFNs), not diffusion or flow matching. It is a singular
   architectural choice, not a representative of the "3D paradigm."

   The field has moved decisively toward flow matching since MolCRAFT's ICML 2024
   publication. FLOWR (Cremer et al., April 2025) achieves 92% PoseBusters validity
   versus MolCRAFT's unreported PoseBusters rate for the base model (only MolPilot, the
   third generation of the series, achieves 95.9% with a specialized VOS scheduling
   strategy). FLOWR also introduces FLOWR:multi, which generates molecules conditioned on
   predefined interaction profiles -- a capability directly relevant to StateBind's
   conformational state hypothesis, since different EGFR states present different
   interaction profiles (hydrogen bond patterns, hydrophobic contacts differ between
   DFG-in and DFG-out pockets).

   More critically: MolCRAFT's base model reports Vina Score -6.59 on CrossDocked2020,
   but MolFORM (ICML 2025) achieves -7.60 using preference-aligned flow matching with
   DPO, and 3DSMILES-GPT (Chemical Science, 2025) achieves -7.72. If the 3D baseline
   underperforms because it uses a 2024 method in a 2026 comparison, reviewers at
   Nature Computational Science will notice.

   The proposal acknowledges DiffSBDD as a supplementary option but dismisses it due
   to 38% PoseBusters validity. This is the right instinct -- but the right conclusion
   is to substitute FLOWR (92% PoseBusters validity, 70x faster than diffusion), not to
   stick with MolCRAFT as the only 3D representative.

   - **Severity:** Major
   - **Addressable?** Yes -- substitute FLOWR as the primary 3D baseline. FLOWR has
     pre-trained models, supports custom pocket inference, and its FLOWR:multi variant
     enables interaction-conditioned generation that could be configured per EGFR state.
     Keep MolCRAFT as a secondary 3D baseline if time permits. This adds approximately
     1 week but substantially strengthens the 3D comparison.

2. **REINVENT's "state-awareness" via per-pocket GNINA scoring is conceptually misleading.**

   The proposal configures REINVENT with 4 state-specific scoring profiles, each using
   GNINA docking against a different EGFR receptor. The proposal correctly notes this
   is "naive state-awareness -- pocket-specific optimization without explicit state
   conditioning." But the framing needs sharper critique.

   REINVENT generates SMILES strings. It has zero 3D awareness during generation. The
   per-state GNINA scoring affects only the RL reward signal -- it tells the generator
   "this molecule docked well in the DFG-out pocket" and the generator updates its RNN
   weights to produce more such SMILES. But the generator never sees the pocket geometry.
   It never learns structural features that distinguish DFG-in from DFG-out. It learns
   statistical correlations between SMILES patterns and high docking scores for each
   pocket -- which is exactly what StateBind's conditioned VAE does with its one-hot
   state vector.

   This means the REINVENT-per-pocket comparison does NOT test "state-conditioning vs
   no state-conditioning." It tests "RL optimization toward pocket-specific docking scores
   vs one-shot VAE generation with state labels." These methods differ on multiple axes
   simultaneously: generation paradigm (RL vs VAE), optimization strategy (iterative vs
   one-shot), conditioning mechanism (docking reward vs concatenated label), and sampling
   budget (REINVENT generates-and-rejects thousands of intermediates; the VAE generates
   1000 in one shot).

   The confounds make interpretation ambiguous. If REINVENT wins, is it because RL > VAE,
   because iterative > one-shot, or because docking-reward-conditioning > label-conditioning?
   If REINVENT loses, is it because SMILES RL is weak, or because REINVENT's prior was
   not fine-tuned on EGFR chemical space?

   - **Severity:** Major
   - **Addressable?** Partially. The cleanest fix is to add a "REINVENT single-pocket"
     control that runs REINVENT with GNINA scoring against only one receptor (e.g., 1M17,
     the static baseline structure). Comparing REINVENT-4-pocket vs REINVENT-1-pocket
     isolates the effect of pocket-specific scoring while holding the generation method
     constant. This mirrors the conditioned-vs-unconditioned VAE ablation and directly
     tests whether pocket diversity helps REINVENT too. The proposal hints at this in
     Outcome 5 ("Compare REINVENT-single-pocket vs REINVENT-4-pocket") but does not
     include it as a formal baseline. It should be.

3. **Missing baseline: LLM-based 3D generators (3DSMILES-GPT, Token-Mol) are the newest
   paradigm and directly bridge StateBind's 1D approach with 3D awareness.**

   3DSMILES-GPT (Chemical Science, 2025) treats 3D molecular generation as a language
   modeling problem -- encoding both SMILES and 3D coordinates as tokens, pre-trained
   on 10 million PubChem molecules. It achieves the highest Vina Score (-7.72) and QED
   (0.76) on CrossDocked2020, with 99% validity and 0.45 seconds per molecule. Token-Mol
   (Nature Communications, 2025) similarly encodes 2D and 3D structural information as
   discrete tokens, improving drug-likeness by approximately 11% and synthetic accessibility
   by approximately 14% over prior methods.

   These LLM-based generators are directly relevant to StateBind because they demonstrate
   that sequence-based generation (like StateBind's SELFIES VAE) can incorporate 3D
   pocket information without abandoning the 1D paradigm entirely. If 3DSMILES-GPT --
   which generates sequences like StateBind but with 3D awareness -- beats StateBind's
   VAE, the implication is not that "3D beats 1D" but that "1D methods should incorporate
   3D structural tokens." This would provide a clearer upgrade path than switching to a
   fundamentally different architecture like FLOWR or MolCRAFT.

   A reviewer familiar with 3DSMILES-GPT will ask why the comparison includes MolCRAFT
   (2024) but not 3DSMILES-GPT (2025), especially given that 3DSMILES-GPT outperforms
   MolCRAFT on every reported metric.

   - **Severity:** Major
   - **Addressable?** Yes, but with effort. 3DSMILES-GPT has a GitHub repository
     (github.com/ashipiling/GPT_3DSMILES) but checkpoint availability and custom pocket
     inference support need verification. If checkpoints are available, adding 3DSMILES-GPT
     as a baseline would take approximately 1 week. If not, acknowledge this as a
     limitation and cite it as future work. At minimum, discuss it in the Related Work
     section to preempt the reviewer question.

4. **CrossDocked2020 leakage: "zero-shot" MolCRAFT on EGFR is not truly zero-shot.**

   CrossDocked2020 was constructed from PDB structures by cross-docking ligands into
   binding pockets with > 50% sequence similarity. EGFR is one of the most-deposited
   kinases in the PDB -- as of 2026 there are over 300 EGFR structures. It is nearly
   certain that EGFR structures (or highly similar kinase structures) are present in
   CrossDocked2020's training set.

   The proposal states: "Zero-shot generation: no retraining on EGFR-specific data (tests
   generalization)." But a model trained on a dataset that almost certainly contains EGFR
   pockets is not performing zero-shot inference on EGFR. It has seen EGFR-like pockets
   (and possibly identical ones) during training. The "zero-shot" label overstates the
   generalization test.

   This matters for interpretation. If MolCRAFT performs well on EGFR, a reviewer could
   argue this is because it memorized EGFR pocket features from training, not because it
   generalizes. If MolCRAFT performs poorly, a defender could argue the training data
   was insufficient for EGFR despite EGFR's presence.

   The CrossDocked2020 train/test split uses protein clustering (>50% sequence similarity
   grouped together), but the split details vary across publications. There is documented
   concern in the literature about data leakage in PDB-derived benchmarks (Harren et al.,
   WIREs Comp Mol Sci, 2024; arxiv 2404.10457, 2024). The proposal should address this
   head-on rather than treating zero-shot as unproblematic.

   - **Severity:** Major
   - **Addressable?** Yes. Three mitigations: (a) Check whether 1M17, 2GS7, 3W2R, 4ZAU
     (or highly similar pockets) appear in CrossDocked2020's training partition. The
     dataset documentation and gnina/models GitHub repository list the PDB IDs. (b) Report
     the result regardless but label it "pre-trained on CrossDocked2020 (which may include
     EGFR-family pockets)" rather than "zero-shot." (c) If EGFR structures are confirmed
     in training, add a fine-tuned condition as well, and report both. The fine-tuned
     result is the upper bound; the "zero-shot" result (with EGFR in training) is an
     intermediate condition.

5. **PoseBusters should be applied to StateBind's GNINA-docked poses, not just to
   MolCRAFT's 3D outputs.**

   The proposal applies PoseBusters only to MolCRAFT's generated 3D poses. But
   StateBind's pipeline also produces 3D poses -- via GNINA docking of SELFIES-generated
   molecules. These GNINA-docked poses have their own physical plausibility issues:
   steric clashes, distorted bond angles, and unrealistic conformations are common in
   docking outputs, especially for novel scaffolds.

   Applying PoseBusters to ALL methods' final 3D poses (MolCRAFT's generated poses,
   GNINA's docked poses for SELFIES-generated molecules, GNINA's docked poses for
   REINVENT-generated molecules) would create a fairer comparison. It would also reveal
   whether StateBind's claimed 99.9% "chemical validity" (2D validity from SELFIES)
   translates to physically valid 3D poses after docking. If GNINA-docked poses fail
   PoseBusters at high rates, this undermines the "1D methods avoid 3D validity problems"
   narrative. If they pass at high rates, it supports the pipeline's practical validity.

   - **Severity:** Minor
   - **Addressable?** Yes -- straightforward. Run PoseBusters on all GNINA-docked poses.
     Report PoseBusters pass rates for every method's final evaluated poses, not just
     the 3D generator's native poses. This adds approximately 1 day of compute and
     strengthens the paper's rigor.

6. **Sampling budget of 1000 molecules per method does not account for 3D method
   sensitivity to sampling parameters.**

   The proposal generates 250 molecules per state (1000 total) for all methods. This
   is reasonable for REINVENT (which generates quickly via RL) and the VAE (one-shot).
   But for MolCRAFT and any other 3D method, sample quality is highly sensitive to
   sampling parameters:

   - MolCRAFT (BFN): the number of flow steps affects output quality. Too few steps
     produce noisy, invalid molecules; too many waste compute. The MolPilot paper showed
     that a VOS scheduling strategy improved PoseBusters validity from approximately 83%
     (Pilot) to 95.9% (MolPilot) without changing the underlying model.
   - FLOWR: at 20 steps, it is 70x faster than Pilot but with lower quality; at 100
     steps, it achieves 92% PoseBusters validity.
   - Diffusion models (DiffSBDD, TargetDiff): use 1000 timesteps for training and
     typically 1000 for inference. Reducing to 100-200 steps via DDIM degrades quality.

   The proposal does not specify the number of sampling/flow/diffusion steps for 3D
   methods. If MolCRAFT is run with default sampling parameters that are suboptimal for
   EGFR pockets, the 3D baseline is handicapped. Conversely, if extensive parameter
   tuning is done for MolCRAFT but not for REINVENT, the comparison is unfair in the
   other direction.

   Furthermore, 250 molecules per pocket may be insufficient to capture the diversity of
   the generative distribution. Diffusion and flow models produce stochastic samples;
   at N=250, the sample may not be representative. The PMO benchmark (Gao et al., 2022)
   used 10,000 oracle calls as its standard budget. DiffSBDD and MolCRAFT papers
   typically report results over 100 molecules per pocket for benchmarking but recommend
   larger samples for practical use.

   - **Severity:** Minor
   - **Addressable?** Yes. (a) Specify the exact number of sampling/flow steps for each
     3D method, using the published recommended defaults. (b) Generate 1000 molecules
     per pocket (4000 total) for 3D methods, then subsample to 250 per pocket for the
     fair N-matched comparison. Report both the full-sample and subsampled results.
     (c) Include a sampling-budget sensitivity analysis: how do results change at N=100,
     250, 500, 1000 per pocket? This costs additional GPU time (approximately doubling
     the 3D generation budget) but eliminates a reviewer objection.

7. **The fundamental question: this framework tests "which generator is best for EGFR?"
   more than "does state-conditioning help?"**

   The proposal's stated goal is to test state-conditioning. But 3 of the 5 baselines
   (REINVENT, MolCRAFT, random/similarity) compare different generation METHODS against
   the StateBind VAE. Only 1 of the 5 (unconditioned VAE) directly tests the effect of
   state-conditioning while holding the method constant.

   The cross-method comparisons are useful for publication but scientifically muddled.
   Each method differs from StateBind's VAE on multiple axes: architecture (RNN vs VAE
   vs BFN), representation (SMILES vs SELFIES vs 3D coordinates), conditioning
   (RL reward vs one-hot label vs pocket geometry), optimization (iterative RL vs
   one-shot sampling), and training data (ChEMBL prior vs SELFIES corpus vs
   CrossDocked2020).

   To cleanly answer "does state-conditioning help?", the framework needs more
   within-method ablations. The unconditioned VAE ablation is one. But the framework
   should also include:
   - REINVENT-1-pocket vs REINVENT-4-pocket (does pocket-specific RL help REINVENT?)
   - MolCRAFT-1-pocket vs MolCRAFT-4-pocket (does running on all 4 pockets help
     MolCRAFT, or is the best single pocket sufficient?)
   - State-aware VAE with shuffled labels (does the VAE learn state-specific features,
     or does any categorical conditioning produce the same diversity benefit?)

   Without these within-method ablations, the framework cannot separate the effect of
   state-conditioning from the effect of the generation method. The proposal acknowledges
   this tension in Outcome 5 but does not fully resolve it.

   - **Severity:** Major
   - **Addressable?** Partially. Adding REINVENT-1-pocket is cheap (one additional run,
     approximately 1 GPU-hour). Adding MolCRAFT-1-pocket is also cheap. The shuffled-
     label ablation is the most informative: train a VAE with randomly permuted state
     labels, preserving the categorical structure but destroying the state-specific
     signal. If the shuffled-label VAE matches the conditioned VAE, the conditioning
     provides no state-specific information -- the diversity benefit comes from having
     any multi-class label, not from the state labels being correct. This is a
     devastating test and should be included.

---

## Feasibility Assessment

### Technical Feasibility
High. All proposed tools (REINVENT 4, MolCRAFT, GNINA, StateBind's scoring
infrastructure) are open-source with documented APIs. The REINVENT + GNINA plugin
integration is the highest-risk component but has a clear mitigation (fall back to
AutoDock Vina). MolCRAFT pocket preparation for EGFR structures is straightforward
given the HuggingFace checkpoint and documented custom pocket inference. The
unconditioned VAE is a config change. The random and similarity baselines are trivial.

### Scientific Feasibility
Moderate to High. The framework will produce results -- the question is whether those
results cleanly answer the target question. As discussed in Weakness 7, the cross-method
comparisons conflate generation method with conditioning strategy. The unconditioned VAE
ablation is scientifically clean. The REINVENT and MolCRAFT comparisons are
scientifically valuable for publication (reviewers want them) but provide weaker evidence
about state-conditioning specifically. Adding the within-method ablations (REINVENT-1-pocket,
shuffled-label VAE) would substantially increase the scientific yield.

The pre-registered outcome mapping significantly strengthens scientific credibility.
However, one concern: if the actual result pattern does not fit any of the 5 pre-defined
outcomes (e.g., unconditioned VAE beats conditioned VAE AND REINVENT, but MolCRAFT beats
both), the mapping has a gap. The proposal should include a "mixed results" outcome
category for patterns that do not cleanly match the pre-registered narratives.

### Timeline Feasibility
Realistic with the proposed scope. The 3-4 week estimate accounts for debugging.
However, adding the modifications I suggest (FLOWR as primary 3D baseline, REINVENT-
1-pocket control, shuffled-label ablation, expanded sampling) would extend the timeline
to approximately 5-6 weeks. Given that this is the paper's central comparison table,
the additional 2 weeks is justified.

---

## Suggested Modifications

1. **Substitute FLOWR for MolCRAFT as the primary 3D baseline.** FLOWR achieves 92%
   PoseBusters validity (vs unreported for MolCRAFT base model), offers FLOWR:multi
   for interaction-conditioned generation, and introduces the higher-quality SPINDR
   benchmark. Keep MolCRAFT as secondary if time permits. If FLOWR setup proves
   difficult, MolCRAFT remains an acceptable fallback.

2. **Add a REINVENT-1-pocket control** that runs REINVENT with GNINA scoring against
   only 1M17 (the static baseline structure). This isolates the effect of pocket-specific
   scoring for REINVENT and directly parallels the conditioned-vs-unconditioned VAE
   ablation. Minimal additional cost (approximately 1 GPU-hour).

3. **Add a shuffled-label VAE ablation.** Train the StateBind VAE with randomly permuted
   state labels (molecules assigned to random states). This tests whether the diversity
   benefit comes from having any multi-class conditioning or specifically from correct
   state assignments. If shuffled-label performs as well as correct-label conditioning,
   the state labels provide no state-specific signal. This is the most informative
   ablation possible and costs approximately 4 GPU-hours (same as unconditioned VAE).

4. **Verify and report CrossDocked2020 EGFR overlap.** Check whether 1M17, 2GS7, 3W2R,
   4ZAU (or kinases with >50% sequence similarity) are in CrossDocked2020's training
   partition. Report the finding transparently. Relabel "zero-shot" as "out-of-
   distribution inference" if EGFR is absent from training, or "in-distribution
   inference" if present. Either way, the result is informative.

5. **Apply PoseBusters to all methods' final 3D poses**, not just MolCRAFT. Run
   PoseBusters on GNINA-docked poses from VAE-generated and REINVENT-generated
   molecules. This creates a fair 3D quality comparison across all methods and tests
   whether "1D generation + docking" produces physically valid poses.

6. **Include a sampling-budget sensitivity curve** for the 3D baseline. Generate 1000
   molecules per pocket and report metrics at N=100, 250, 500, 1000. This costs
   approximately 4x additional GPU time for 3D generation (still only approximately
   8 GPU-hours total for MolCRAFT/FLOWR) but eliminates the reviewer concern that the
   3D method was under-sampled.

7. **Discuss 3DSMILES-GPT in Related Work at minimum.** If checkpoints and custom pocket
   inference are available, include it as a baseline. If not, cite it as the LLM-based
   paradigm that bridges 1D and 3D approaches and note it as future work. Do not ignore
   it -- reviewers who follow the 2025 Chemical Science literature will know it.

8. **Add a "mixed results" category to the pre-registration** for outcome patterns that
   do not cleanly match the 5 defined narratives. This is methodologically honest and
   prevents the awkward situation of having to force-fit complex results into simple
   narratives.

---

## Alternative Approaches

The proposal's core framework (5 methods, unified scoring, pre-registered outcomes) is
the right structure. The alternative is not a different framework but a different
emphasis within the same framework.

**Specifically: prioritize within-method ablations over cross-method comparisons.**

The most publishable finding from this framework is not "StateBind VAE beats REINVENT"
or "MolCRAFT beats StateBind." Those are method comparisons that will be superseded by
the next benchmark paper. The most durable finding is: "State-conditioning improves
retrospective enrichment WITHIN a given generation method, regardless of which method
is used." If REINVENT-4-pocket beats REINVENT-1-pocket, AND conditioned VAE beats
unconditioned VAE, AND MolCRAFT-4-pocket beats MolCRAFT-best-single-pocket, then
state-conditioning is a transferable principle -- not a property of one specific
architecture. That is a Nature Computational Science finding. A single method comparison
is a JCIM finding.

This reframing does not require abandoning the cross-method comparisons. It requires
adding the within-method controls described above and shifting the paper's central
claim from "our VAE is the best method for EGFR" to "conformational state-awareness
improves molecular generation across architectures." The latter is a much stronger
and more general claim.

**Evidence supporting this approach:** The "Beyond Affinity" benchmark (arXiv
2601.14283, 2025) showed that "no methods can dominate structure-based drug design in
all evaluation metrics" -- 1D methods win on drug-likeness, 3D methods win on binding,
search-based methods win on optimization. Method-vs-method comparisons are inherently
fragile. The robust claim is about the conditioning strategy, not the architecture.

---

## Impact on Publication Narrative

This proposal, with the suggested modifications, strengthens the publication narrative
significantly. The core contribution of the paper should be:

**"Conformational state-conditioning is a transferable principle that improves molecular
generation across architectures (VAE, RL, 3D pocket-conditioned) and evaluation metrics
(enrichment, binding, drug-likeness)."**

The external baselines serve two purposes: (1) calibrating StateBind's absolute
performance against established methods (required for credibility), and (2) testing
whether state-conditioning helps methods OTHER than StateBind's VAE (required for
generality).

Without modification, the proposal accomplishes (1) well but (2) only partially (via
the REINVENT per-pocket comparison, which is confounded as discussed). With the
REINVENT-1-pocket control and shuffled-label ablation added, the proposal accomplishes
both.

The 3D baseline choice matters for venue. If the paper targets Nature Computational
Science, the 3D comparison must use a method published in 2025 or later (FLOWR, MolFORM,
or 3DSMILES-GPT). Using only MolCRAFT (ICML 2024) as the 3D representative risks the
perception that the comparison was designed to make the 1D method look good by choosing
a weaker 3D opponent.

---

## References

1. Cremer, J. et al. "FLOWR: Flow Matching for Structure-Aware De Novo, Interaction-
   and Fragment-Based Ligand Generation." arXiv:2504.10564, 2025.
   https://arxiv.org/abs/2504.10564

2. Qu, Y. et al. "MolCRAFT: Structure-Based Drug Design in Continuous Parameter Space."
   ICML, 2024. https://arxiv.org/abs/2404.12141

3. "Piloting Structure-Based Drug Design via Modality-Specific Optimal Schedule"
   (MolPilot). arXiv:2505.07286, 2025. https://arxiv.org/abs/2505.07286

4. Shi, A. et al. "3DSMILES-GPT: 3D molecular pocket-based generation with token-only
   large language model." Chemical Science 16, 2025.
   https://doi.org/10.1039/D4SC06864E

5. "Token-Mol 1.0: tokenized drug design with large language models." Nature
   Communications, 2025. https://doi.org/10.1038/s41467-025-59628-y

6. Gao, W. et al. "Sample Efficiency Matters: A Benchmark for Practical Molecular
   Optimization." NeurIPS Datasets & Benchmarks, 2022.
   https://arxiv.org/abs/2206.12411

7. "Structure-based Drug Design Benchmark: Do 3D Methods Really Dominate?"
   arXiv:2406.03403, 2024.

8. "Beyond Affinity: A Benchmark of 1D, 2D, and 3D Methods Reveals Critical Trade-offs
   in Structure-Based Drug Design." arXiv:2601.14283, 2025.

9. Harren, T. et al. "Modern machine-learning for binding affinity estimation of
   protein-ligand complexes: Progress, opportunities, and challenges." WIREs Comp Mol
   Sci 14, 2024. https://doi.org/10.1002/wcms.1716

10. "Revealing data leakage in protein interaction benchmarks."
    arXiv:2404.10457, 2024.

11. Francoeur, P.G. et al. "Three-Dimensional Convolutional Neural Networks and a
    CrossDocked Dataset for Structure-Based Drug Design." JCIM 60(9), 4200-4215, 2020.
    https://doi.org/10.1021/acs.jcim.0c00411

12. Schneuing, A. et al. "Structure-based drug design with equivariant diffusion models."
    Nature Computational Science 4, 2024.
    https://doi.org/10.1038/s43588-024-00737-x

13. Buttenschoen, M. et al. "PoseBusters: AI-based docking methods fail to generate
    physically valid poses or generalise to novel sequences." Chemical Science 15, 2024.
    https://doi.org/10.1039/D3SC04185A

14. Loeffler, H.H. et al. "Reinvent 4: Modern AI-driven generative molecule design."
    J. Cheminformatics 16, 2024.
    https://doi.org/10.1186/s13321-024-00812-5

15. Bhati, A.P. et al. "Optimal Molecular Design: Generative Active Learning Combining
    REINVENT with Precise Binding Free Energy Ranking Simulations." JCTC, 2024.
    https://doi.org/10.1021/acs.jctc.4c00576
