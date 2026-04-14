---
agent: Publication Strategy Advisor
round: 1
date: 2026-04-14
type: research-note
---

# Publication Strategy Investigation: G2 Recovery Path Analysis

## 1. Executive Assessment

The Gate G2 NO_GO result (Cohen's d = 0.059, n=10 seeds) is not a crisis -- it is a
decision point with multiple viable paths forward. The pre-registration (commit 9e7cf96)
transforms what could be dismissed as "didn't try hard enough" into a rigorous test of a
specific hypothesis. The Transformer VAE itself (EF@10 = 5-8, drug scaffold recovery,
64/64 active latent dimensions) is a genuine methodological contribution independent of
the conditioning thesis.

**Bottom line:** The project has 3-4 publishable paths, even in the worst case. The
question is which path maximizes impact given time constraints and competitive pressure.
The optimal strategy is a sequential diagnostic cascade: cheapest tests first, with
go/no-go gates that redirect the narrative at each stage.

**Probability-weighted assessment of recovery paths:**

| Path | P(success) | Time | Expected venue | Expected value |
|------|------------|------|----------------|----------------|
| H3 fix (multi-pocket docking) | 0.55 | 2-3 weeks | JCIM / J Cheminformatics | 0.55 x 8 = 4.4 |
| H1 fix (stronger conditioning) | 0.35 | 4-6 weeks | JCIM / NeurIPS workshop | 0.35 x 7 = 2.5 |
| H2 fix (different kinase) | 0.40 | 8-10 weeks | JCIM | 0.40 x 8 = 3.2 |
| Negative result publication | 0.90 | 3-4 weeks | JCIM / J Cheminformatics | 0.90 x 5 = 4.5 |
| Benchmark/evaluation paper | 0.80 | 4-5 weeks | JCIM / ICLR workshop | 0.80 x 6 = 4.8 |

Impact scale: 1-10 where 10 = Nature Computational Science, 8 = JCIM with strong
contribution, 5 = JCIM brief communication.

---

## 2. Publication Landscape for Negative Results in Molecular Generation

### 2.1 Precedent: Critical/Negative Results That Achieved High Impact

The molecular generation field has a growing tradition of high-impact papers whose
primary contribution is revealing limitations rather than improvements. These papers
are among the most cited in the subfield because they reshape how the community
evaluates methods.

**Paper 1: "Generative Models Should at Least Be Able to Design Molecules That Dock
Well: A New Benchmark"**
- Authors: Cieplinski, Danel, Podlewska, Jastrzebski
- Venue: JCIM, 2023 (63(11):3238-3247)
- Key negative finding: Various graph-based generative models fail to propose molecules
  with high docking scores when trained on realistically sized datasets
- Why it was impactful: Proposed a concrete benchmark (SMINA docking) and showed that
  models that look good on distribution metrics (validity, novelty, FCD) fail at a
  basic functional task
- Framing: Not "models are bad" but "here is a better way to evaluate them"
- Estimated citations: 80-120+ (high for JCIM)
- Relevance to StateBind: Same structural insight -- evaluation design matters more
  than model architecture

**Paper 2: "On the Difficulty of Validating Molecular Generative Models Realistically"**
- Authors: Handa, Thomas, Kageyama, Iijima, Bender
- Venue: Journal of Cheminformatics, 2023 (15:108)
- Key negative finding: REINVENT trained on early-stage compounds recovers only 0.00-0.04%
  of middle/late-stage compounds in proprietary datasets (vs 0.21-1.60% on public data)
- Why it was impactful: First systematic comparison of retrospective validation on
  public vs proprietary data, revealing fundamental limitations of retrospective evaluation
- Framing: "Evaluating de novo compound design appears difficult or even impossible to
  do retrospectively"
- Relevance to StateBind: Directly validates the importance of retrospective evaluation
  design as a contribution. StateBind's 10-seed false alarm (d=0.71 to d=-0.02) is a
  concrete example of this difficulty

**Paper 3: "In Search of Beautiful Molecules: A Perspective on Generative Modeling for
Drug Design"**
- Authors: Multiple (perspective article)
- Venue: JCIM, 2025
- Key finding: Despite rapid progress, GenAI has yet to demonstrate clear and consistent
  value in prospective drug discovery applications
- Why it was impactful: Senior perspective acknowledging the field-wide gap between
  computational metrics and real-world utility
- Relevance: StateBind's null result is a specific instance of this general finding

**Paper 4: "Reframing Structure-Based Drug Design Model Evaluation via Metrics
Correlated to Practical Needs"**
- Authors: Gao, Tan et al.
- Venue: ICLR 2025 (conference paper)
- Key finding: Despite achieving high Vina scores, current SBDD models fall
  significantly short of matching reference ligand quality on practical metrics
- Three-level evaluation framework: similarity to actives, virtual screening ability,
  binding affinity estimation
- Relevance: Directly supports the argument that evaluation design is itself a
  contribution. StateBind's H3 (wrong metric) aligns with this perspective

**Paper 5: "Benchmarking Real-World Applicability of Molecular Generative Models"
(MolGenBench)**
- Authors: Multiple
- Venue: bioRxiv, November 2025
- Key finding: Significant gaps between current generative models and demands of
  real-world drug development across 120 protein targets
- Relevance: Large-scale benchmarking of generative models revealing systematic failures

### 2.2 Why Negative Results Are Publishable in This Subfield

The molecular generation field is experiencing a credibility crisis (Cieplinski et al.,
2023; Gao et al., ICLR 2025; JCIM perspective 2025). There are too many papers
claiming improvements on distribution metrics that don't translate to functional
improvements. In this environment, well-designed negative results that expose
evaluation blind spots are actively sought by editors.

Key factors that make a negative result publishable:

1. **Pre-registration**: StateBind's pre-registration (commit 9e7cf96) with fixed
   thresholds (GO >= 0.5, NO_GO < 0.3) is rare in computational chemistry. This
   alone differentiates the work from post-hoc analyses
2. **Scale**: 10 seeds, ~6,800 molecules, 2 generation modes, 4 scoring components.
   This is not a 1-seed anecdote
3. **Working model**: The Transformer VAE generates real drug scaffolds (erlotinib,
   gefitinib, osimertinib, lazertinib). The null is about conditioning, not generation
4. **Identified evaluation flaw**: Section 6.2 of the G2 report explicitly identifies
   the single-pocket scoring limitation. This is an actionable finding
5. **False alarm lesson**: The n=3 to n=10 collapse (d=0.71 to d=-0.02) is a
   cautionary tale about small-sample EF@10 that the field needs to hear

### 2.3 Journal Landscape for Negative/Critical Results

| Journal | IF (2024) | Accepts negative results? | Time to decision | Notes |
|---------|-----------|--------------------------|-------------------|-------|
| JCIM | ~6.2 | Yes, if methodologically rigorous | 3-6 months | Best fit for evaluation-focused papers |
| J Cheminformatics | ~8.5 | Yes, open access, explicit benchmark focus | 2-4 months | Fast, open access, good for benchmark papers |
| Nature Computational Science | ~12.0 | Only with broad impact | 4-8 months | Would need positive multi-kinase result |
| Bioinformatics | ~5.8 | Yes, if computational rigor is high | 3-5 months | Application notes possible |
| PLOS Computational Biology | ~4.3 | Yes, replication and null results valued | 4-6 months | Lower impact but values rigor |
| ChemRxiv | N/A | Preprint, no peer review | Immediate | Priority establishment |

---

## 3. Narrative Framing Options

### 3.1 Framing A: "When Does Conformational Conditioning Work?" (Investigation Paper)

**Main claim:** Discrete conformational state conditioning does not improve generic
molecular quality for EGFR, but the evaluation itself is structurally unable to detect
state-specific improvements. We identify three necessary conditions for conditioning
to show benefit and test each.

**Target venue:** JCIM (full article)

**Probability of acceptance:** 0.65

**Expected citation impact:** Medium-high (50-100 citations over 3 years). This framing
positions the paper as a diagnostic contribution rather than a negative result.

**Structure:**
1. Pre-registered hypothesis and experimental design
2. Working Transformer VAE (validation, drug scaffold recovery)
3. Definitive null on generic quality (10 seeds, d=0.059)
4. Diagnosis: three hypotheses with evidence for each
5. Resolution: multi-pocket docking reveals state-specific signal (if H3 confirmed)
6. Guidelines: when to expect conditioning to work

**Why reviewers would accept:** Novel evaluation framework, pre-registration, working
model, actionable guidelines. The null result is the setup for the investigation, not
the conclusion.

**What reviewers would attack:**
- "Why not test H3 before publishing?" (Must run multi-pocket docking first)
- "Only one kinase" (Mitigate with ABL1 analysis or explicit scope limitation)
- "Comparison to REINVENT?" (Need at least one external baseline)

### 3.2 Framing B: "Pre-Registered Null Result in State-Conditioned Generation"
(Negative Result Paper)

**Main claim:** We pre-registered a hypothesis that conformational state conditioning
improves molecular generation quality for EGFR. After 10 seeds and ~6,800 molecules,
the result is a definitive null (d=0.059). The Transformer VAE is a working generator,
but conditioning provides no benefit under our evaluation protocol. We identify the
evaluation design flaw that prevents detection of state-specific improvements.

**Target venue:** J Cheminformatics (full article) or JCIM (communication)

**Probability of acceptance:** 0.80

**Expected citation impact:** Medium (30-60 citations). Higher if small-sample EF@10
unreliability resonates with the field.

**Structure:**
1. Problem: state conditioning is theoretically motivated but untested
2. Pre-registration with fixed thresholds
3. GRU-to-Transformer transition (methodological contribution)
4. Definitive null with full statistical analysis
5. n=3 false alarm as cautionary tale
6. Evaluation design limitations and proposed improvements

**Why reviewers would accept:** Pre-registration is rare and valuable. The false alarm
lesson (d=0.71 to d=-0.02) is a direct contribution to evaluation methodology.

**What reviewers would attack:**
- "Obvious that single-pocket scoring can't detect multi-pocket benefit" (Fair, but
  many papers in the field make this mistake)
- "No external baselines" (Weakness; mitigate with REINVENT comparison)

### 3.3 Framing C: "Transformer VAE for EGFR Molecular Generation with Retrospective
Validation" (Method Paper)

**Main claim:** We present a Transformer VAE that generates pharmacologically relevant
EGFR inhibitors, recovering known drug scaffolds (erlotinib, gefitinib, osimertinib,
lazertinib) with EF@10 = 5-8 in retrospective validation. We solved posterior collapse
in molecular VAEs by switching from GRU+SELFIES to Transformer+SMILES with free-bits
KL. State conditioning does not improve generic quality but opens questions about
multi-pocket evaluation.

**Target venue:** J Cheminformatics or Bioinformatics (application note)

**Probability of acceptance:** 0.75

**Expected citation impact:** Low-medium (20-40 citations). The VAE contribution alone
is incremental given FRATTVAE (Nature Comm Chem, 2025), PCF-VAE (Scientific Reports,
2025), and TGVAE (Biophysical Journal, 2025).

**Why this is the weakest framing:** The Transformer VAE landscape is crowded. Without
the conditioning investigation or evaluation framework, this is just another VAE paper.

### 3.4 Framing D: "Multi-Pocket Evaluation Reveals Hidden Signal in State-Conditioned
Generation" (Positive Result Paper)

**Main claim:** Conventional single-pocket evaluation fails to detect the benefit of
conformational state conditioning. When molecules are docked against their target
state's pocket, conditioned molecules show [X] improvement over unconditioned molecules.
We propose a multi-pocket evaluation protocol for state-conditioned generation.

**Target venue:** JCIM (full article) or Nature Computational Science (if effect is large
and multi-kinase)

**Probability of acceptance:** 0.50 (contingent on finding the signal)

**Expected citation impact:** High (80-150 citations if positive and multi-kinase).
This is the home run scenario.

**Contingency:** This framing is only available if H3 is confirmed (multi-pocket docking
shows state-specific improvement). If the docking shows no signal, this path is dead.

### 3.5 Framing E: "The Evaluation Gap: Why Molecular Generation Benchmarks Miss
State-Specific Improvements" (Benchmark/Methodology Paper)

**Main claim:** Current evaluation protocols for molecular generation assess generic
quality but are structurally blind to conditional improvements. We demonstrate this
with a case study in EGFR state-conditioned generation, propose a multi-pocket
evaluation framework, and benchmark it against existing protocols.

**Target venue:** JCIM or ICLR/NeurIPS ML4Drug workshop

**Probability of acceptance:** 0.70

**Expected citation impact:** Medium-high (40-80 citations). Evaluation/benchmark
papers have high utility citations.

**Why this works:** Aligns with the field's growing recognition that evaluation
methodology is the bottleneck (Cieplinski et al., 2023; Gao et al., ICLR 2025;
MolGenBench, 2025). StateBind becomes a detailed case study illustrating a general
problem.

---

## 4. Decision Tree for Sequential Investigation

The optimal strategy is a cascade of increasingly expensive tests, each with clear
go/no-go criteria. The key insight is that every outcome produces a publishable paper
-- the question is which framing.

```
START (Week 0)
  |
  v
[DIAGNOSTIC 1: Latent Space Analysis] -- Cost: 1-2 days, 0 GPU hours
  |  - Do conditioned models learn state-distinct latent distributions?
  |  - Measure: KL divergence between per-state latent distributions
  |  - Measure: Classifier accuracy on z -> state (random baseline = 33%)
  |
  |-- If classifier accuracy > 60%: Conditioning reaches latent space.
  |   Signal exists but doesn't propagate to scoring. -> Prioritize H3
  |
  |-- If classifier accuracy ~ 33%: Conditioning doesn't reach latent space.
  |   Architecture is too weak. -> Prioritize H1
  |
  v
[DIAGNOSTIC 2: Training Data Chemistry Analysis] -- Cost: 1-2 days, 0 GPU hours
  |  - Compute Tanimoto similarity matrices within and between states
  |  - Count shared vs unique Murcko scaffolds across states
  |  - Measure: inter-state vs intra-state chemical diversity
  |
  |-- If inter-state diversity >> intra-state: States are chemically distinct.
  |   Signal should be learnable. -> H2 is unlikely
  |
  |-- If inter-state ~ intra-state: Same chemistry across states.
  |   No signal to learn. -> H2 is primary cause
  |
  v
[TEST 1: Multi-Pocket Docking] -- Cost: 2-3 weeks, ~60 GPU hours
  |  Tests H3: Is the evaluation blind to real signal?
  |
  |  - Dock all ~6,800 molecules against 3 pocket conformers:
  |    1M17 (DFGin/aCin), 4HJO (DFGin/aCout), 3W2S (DFGout/aCin)
  |  - For conditioned molecules: compare docking to target vs non-target pocket
  |  - For unconditioned molecules: dock against all 3 pockets
  |  - Metric: paired t-test on target-pocket docking scores,
  |    conditioned vs unconditioned
  |
  |-- GO (d > 0.3 on target-pocket docking):
  |   H3 CONFIRMED. The conditioning signal exists but was invisible to
  |   single-pocket evaluation. -> Framing D (positive result paper)
  |   Continue to multi-kinase if time permits.
  |
  |-- WEAK SIGNAL (d in [0.1, 0.3]):
  |   Partial H3 confirmation. Conditioning helps a little for matching
  |   pockets. -> Framing A or E (investigation or benchmark paper)
  |
  |-- NO SIGNAL (d < 0.1):
  |   H3 refuted. Even with the right evaluation, conditioning doesn't help.
  |   -> Proceed to Test 2 (H1)
  |
  v
[TEST 2: Stronger Conditioning Mechanism] -- Cost: 4-6 weeks, ~200 GPU hours
  |  Tests H1: Is prefix-token conditioning too weak?
  |
  |  - Implement cross-attention conditioning (state embedding attended to
  |    at every decoder layer)
  |  - Or: FiLM conditioning (Feature-wise Linear Modulation)
  |  - Train 10 seeds, re-run ablation
  |  - Same evaluation protocol (both single-pocket and multi-pocket)
  |
  |-- GO (d > 0.3 on any metric):
  |   H1 CONFIRMED. Stronger conditioning works. -> Framing D
  |
  |-- NO GO (d < 0.3):
  |   Architecture was not the issue. -> Proceed to Test 3 or accept null.
  |
  v
[TEST 3: Different Kinase (ABL1)] -- Cost: 8-10 weeks, ~300 GPU hours
  |  Tests H2: Is the problem EGFR-specific?
  |
  |  - ABL1 has genuine DFGout structures (imatinib-bound, PDB 1IEP)
  |  - More distinct chemistry across states (Type I vs Type II inhibitors)
  |  - Same pipeline: VAE + scoring + retrospective evaluation
  |
  |-- GO (ABL1 shows conditioning benefit):
  |   H2 CONFIRMED for EGFR. EGFR states are chemically similar but
  |   conditioning works for kinases with distinct state chemistries.
  |   -> Framing D (multi-kinase) or Framing A
  |
  |-- NO GO:
  |   Conditioning doesn't work for either kinase. -> Accept null.
  |   Framing B (negative result) or E (evaluation paper)
  |
  v
[DECISION POINT: Accept null or continue]
  |
  |-- If tests 1-3 all negative:
  |   Strong evidence that discrete state conditioning does not improve
  |   molecular generation for kinases. This IS a contribution.
  |   -> Framing B (pre-registered negative) + E (evaluation framework)
  |
  |-- If any test positive:
  |   Conditional positive result. -> Framing A or D depending on strength
```

### 4.1 Key Decision Gates with Timelines

| Gate | Week | Test | GO criterion | NO_GO action |
|------|------|------|-------------|--------------|
| D0 | 0-1 | Latent space diagnostics | Classifier > 60% | Deprioritize H3, focus H1 |
| D1 | 0-1 | Training data chemistry | Inter > intra diversity | H2 unlikely |
| G3 | 2-3 | Multi-pocket docking | d > 0.3 target-pocket | Proceed to H1 test |
| G4 | 6-8 | Stronger conditioning | d > 0.3 any metric | Accept partial null |
| G5 | 14-16 | ABL1 pipeline | ABL1 EF@10 > 1.0 | Accept full null |
| PUB | Any gate | Publication decision | Enough for a story | Pivot to negative |

---

## 5. Competitive Timing Analysis

### 5.1 Current Competitive Landscape (April 2026)

**Closest competitors and their trajectories:**

1. **Volkamer Group (Charite Berlin)**: KLIFS-based kinase analysis, KinFragLib,
   CustomKinFragLib (ACS Omega 2025). Focus is on subpocket-based fragmentation, not
   state-conditioned generation. They have the data infrastructure (KLIFS) but have
   NOT published state-conditioned generation. Risk: medium (15-20% within 6 months).
   Mitigant: They are more likely to publish a KinFragLib extension than a full
   state-conditioned pipeline.

2. **PocketXMol (Cell, February 2026)**: Pocket-conditioned foundation model for 3D
   molecular generation. Different mechanism (atom-level 3D geometry, not 1D SMILES +
   discrete state labels). Achieved state-of-the-art on 11/13 benchmarks. Risk: low
   for exact overlap but high for general pocket-conditioned generation. The existence
   of PocketXMol raises the bar for what "pocket conditioning" means.

3. **KASSPer (bioRxiv, January 2026)**: Predicts kinase active site conformational
   states using protein and ligand language models. Directly relevant to the state
   assignment problem. Not molecular generation but could be combined with generation.

4. **AlphaFold2 Multi-State Modeling for Kinases (Scientific Reports, October 2024)**:
   MSM protocol for kinase structures using state-specific templates. Showed EF1%
   improvement from 6.6 (standard AF2) to 8.2 (MSM). ABL1 showed dramatic improvement
   (15.83 vs 6.0). This is the closest published work to StateBind's multi-pocket
   concept, but focused on virtual screening, not generation.

5. **DynamicBind (Nature Communications, 2024)**: Predicts ligand-specific protein
   conformational changes including DFG-in/out transitions. Different task (docking,
   not generation) but validates the importance of conformational awareness.

6. **DiffGui (Nature Communications, August 2025)**: Target-conditioned E(3)-equivariant
   diffusion model with property guidance. 3D generation, not 1D string generation.
   Different approach but shows the field is moving toward more sophisticated
   conditioning mechanisms.

7. **FRATTVAE (Nature Comm Chemistry, 2025)**: Fragment tree-transformer VAE. Better
   molecular VAE architecture but no conformational conditioning. Shows the VAE
   landscape is crowded.

### 5.2 Scooping Risk Assessment

**Within 6 months (by October 2026):** 15-20% probability that someone publishes
discrete-state-conditioned molecular generation with a proper evaluation.
- Most likely source: Volkamer group or a new group combining KLIFS + generation
- Mitigant: StateBind's pre-registration is timestamped and unique

**Within 12 months (by April 2027):** 30-40% probability.
- The combination of KASSPer (state prediction) + any generation model could close
  the gap

**Key differentiators that are hard to replicate:**
1. Pre-registration with fixed thresholds
2. 10-seed definitive null (most papers use 1-3 seeds)
3. GRU-to-Transformer diagnostic journey
4. Explicit evaluation design critique (H3)
5. Retrospective enrichment framework with false alarm analysis

### 5.3 Priority Establishment Strategy

**Recommendation: ChemRxiv preprint within 4-6 weeks.**

ChemRxiv preprints are indexed by search engines, assigned DOIs, and tracked for
views/downloads. ACS journals (including JCIM) explicitly allow prior ChemRxiv
posting (ACS Prior Publication Policy).

The preprint should be posted after completing Test 1 (multi-pocket docking), regardless
of outcome. This establishes priority for:
- The pre-registered framework
- The Transformer VAE for EGFR
- The evaluation design critique
- Whatever signal (or lack thereof) the multi-pocket docking reveals

**Timing considerations:**
- Too early (now): Preprint without multi-pocket results looks incomplete
- Optimal (week 4-6): After multi-pocket docking, before stronger conditioning
- Too late (week 12+): Risk of being scooped on the evaluation framework

---

## 6. Minimum Publishable Unit Assessment

### 6.1 What Is Publishable Right Now?

**Yes, a paper could be published with current results.** The minimum publishable unit
consists of:

1. Pre-registered hypothesis with fixed thresholds (rare in computational chemistry)
2. GRU-to-Transformer transition (0% to 2-4% reconstruction, 0 to 64 active dims)
3. Working Transformer VAE (EF@10 = 5-8, drug scaffold recovery)
4. Definitive null on state conditioning (d=0.059, 10 seeds)
5. n=3 false alarm analysis (d=0.71 to d=-0.02)
6. Explicit identification of evaluation design flaw (H3)

This maps to Framing B (negative result paper) and would be suitable for:
- J Cheminformatics (full article, 2-4 month review)
- JCIM (communication or full article, 3-6 month review)

**What's missing for a stronger paper:**
- Multi-pocket docking to actually test H3 (2-3 weeks)
- External baseline (REINVENT comparison)
- Latent space diagnostics to distinguish H1 vs H2

**Assessment: Publishing now is defensible but suboptimal.** The 2-3 week investment
in multi-pocket docking would significantly strengthen any narrative. Every framing
(A through E) benefits from knowing whether H3 is confirmed.

### 6.2 Value-of-Information Analysis

The multi-pocket docking test costs ~2-3 weeks and ~60 GPU hours. The information it
provides:

- If H3 confirmed: Unlocks Framing D (positive result, JCIM full article) or
  Framing E (evaluation paper). Expected additional value: +3 impact points.
- If H3 refuted: Strengthens Framing B (negative result, all hypotheses tested).
  Expected additional value: +1 impact point.

**Expected value of running Test 1: 0.55 x 3 + 0.45 x 1 = 2.1 impact points.**
This is an excellent return on 2-3 weeks of work.

---

## 7. Recovery Path Assessment

### 7.1 Path 1: H3 Evaluation Fix (Multi-Pocket Docking)

**What:** Dock all ~6,800 molecules against 3 pocket conformers (1M17, 4HJO, 3W2S).
Test whether conditioned molecules for state X dock better to pocket X than
unconditioned molecules.

**Cost:** 2-3 weeks, ~20,400 docking runs, 3 SLURM GPU jobs (~60 H200 GPU-hours).
Uses existing GNINA infrastructure.

**Probability of success:** 0.55

**Reasoning for probability:**
- FOR (signal likely): The G2 report Section 6.2 explicitly acknowledges the evaluation
  is blind to state-specific improvements. If the conditioning mechanism teaches the
  model ANYTHING about state chemistry, it should show up in state-specific docking.
  AlphaFold2 MSM for kinases (Sci Reports, 2024) showed EF1% improvement from 6.6
  to 8.2 when using state-specific templates, demonstrating that multi-state evaluation
  reveals hidden signal.
- AGAINST (signal unlikely): The centroid distances are only 0.26-0.42 (6-10% of latent
  space scale). The model generates the same drug scaffolds regardless of state. If
  the latent space doesn't distinguish states, the molecules won't be state-specific.

**Expected venue if successful:** JCIM full article (Framing D)
**Expected venue if unsuccessful:** Strengthens Framing A or B

**Risk:** GNINA v1.1 on the cluster (GLIBC 2.28 limitation). Need to verify that all
3 receptor conformers are prepared and working.

### 7.2 Path 2: H1 Architecture Fix (Stronger Conditioning)

**What:** Replace prefix-token conditioning with cross-attention or FiLM conditioning.
Train 10 seeds each for conditioned/unconditioned, re-run full ablation.

**Cost:** 4-6 weeks, ~200 GPU hours (20 training runs x ~10 GPU hours each).
Requires code changes to `ml/vae.py` and `ml/transformer_vae.py`.

**Probability of success:** 0.35

**Reasoning:**
- FOR: Prefix tokens are a weak conditioning mechanism. The Transformer decoder has
  8 layers of self-attention that can route around prefix tokens. Cross-attention
  forces the model to attend to state information at every layer. Recent conditional
  generation work (DiffMC-Gen, Advanced Science 2025; DiffGui, Nat Commun 2025) uses
  much stronger conditioning mechanisms.
- AGAINST: If the training data doesn't contain state-specific chemical information
  (H2), no conditioning mechanism can extract signal that isn't there. Stronger
  conditioning may just overfit to noise.

**Expected venue if successful:** JCIM full article
**Expected venue if unsuccessful:** Informs the narrative but doesn't change venue

### 7.3 Path 3: H2 Different Kinase (ABL1)

**What:** Run the full StateBind pipeline on ABL1. ABL1 has genuine DFGout structures
(imatinib-bound, PDB 1IEP), distinct Type I/Type II inhibitor chemistries across
states, and better retrospective drug timeline (imatinib 2001, dasatinib 2006,
nilotinib 2007, bosutinib 2012, ponatinib 2012, asciminib 2021).

**Cost:** 8-10 weeks, ~300 GPU hours. Full pipeline from data curation to evaluation.

**Probability of success:** 0.40

**Reasoning:**
- FOR: ABL1 has fundamentally more distinct state chemistries than EGFR. DFGin-binding
  (dasatinib, bosutinib) vs DFGout-binding (imatinib, nilotinib, ponatinib) represents
  genuinely different pharmacophores. AlphaFold2 MSM showed the most dramatic improvement
  for ABL1 specifically (EF1% from 6.0 to 15.83). The retrospective drug timeline
  provides a richer test (6 drugs spanning 2001-2021 vs 5 for EGFR).
- AGAINST: Data curation is expensive. ChEMBL ABL1 assay heterogeneity is messier than
  EGFR. State annotation verification is required (lesson from EGFR errors).

**Expected venue if successful:** JCIM full article (multi-kinase)
**Expected venue if unsuccessful:** Strengthens negative result narrative

### 7.4 Path 4: Negative Result Publication

**What:** Write up the full story with current results. Frame as pre-registered null
with evaluation design critique.

**Cost:** 3-4 weeks writing time. No additional compute.

**Probability of acceptance:** 0.90 (high certainty of publication)

**Reasoning:** Pre-registered negative results with working models are rare and
valuable. The false alarm analysis is a direct contribution.

**Expected venue:** J Cheminformatics (full article) or JCIM (communication)
**Expected citation impact:** 30-60 citations over 3 years

### 7.5 Path 5: Benchmark/Evaluation Paper

**What:** Frame the entire investigation as a case study in evaluation design for
conditional molecular generation. Include multi-pocket evaluation framework,
comparison of single-pocket vs multi-pocket metrics, and guidelines for when to
expect conditioning to work.

**Cost:** 4-5 weeks (including multi-pocket docking from Path 1).

**Probability of acceptance:** 0.80

**Expected venue:** JCIM or NeurIPS/ICLR ML4Drug workshop
**Expected citation impact:** 40-80 citations

---

## 8. Career Impact Assessment

### 8.1 How a Hiring Committee Views This

A hiring committee in computational biology or cheminformatics would evaluate the
project trajectory based on:

**Positives:**
1. **Pre-registration discipline**: Demonstrates scientific rigor uncommon in
   computational chemistry. Shows awareness of reproducibility crisis.
2. **End-to-end pipeline**: 91 source files, 646 tests, 12 workstreams, SLURM
   infrastructure. Shows engineering maturity.
3. **Honest reporting of null**: Following pre-registered thresholds rather than
   p-hacking or selective reporting demonstrates integrity.
4. **Diagnostic capability**: The systematic H1/H2/H3 investigation shows
   intellectual depth beyond "run model, report numbers."
5. **Architectural debugging**: GRU-to-Transformer transition (0% to 2-4%
   reconstruction) shows ability to diagnose and fix model failures.

**Negatives:**
1. **No positive result (yet)**: A null result with investigation is less impactful
   than a positive result with validation.
2. **Single target**: EGFR-only limits the generalizability claim.
3. **No external baseline**: Without REINVENT or similar comparison, the evaluation
   scope appears narrow.

**Assessment:** A JCIM paper (any framing) with an honest null result and strong
investigation is better than no paper. The pre-registration and diagnostic depth
are differentiators that a committee would recognize. The project is strongest if
framed as "I found that the standard evaluation was wrong, here's how to do it
right" (Framing E).

### 8.2 Grant Reviewer Perspective

An NIH/NSF grant reviewer would see:
- **Innovation**: State-conditioned generation for kinases (novel)
- **Rigor**: Pre-registration, 10-seed design, bootstrap CIs (high rigor)
- **Preliminary data**: EF@10 = 5-8 for the Transformer VAE (working model)
- **Feasibility**: Infrastructure exists, compute available

The null result is NOT disqualifying. A grant proposal framed as "We discovered that
standard evaluation metrics miss state-specific improvements; we propose to develop
multi-pocket evaluation and test across 5 kinases" is competitive.

---

## 9. The Combined Sequential Strategy

### 9.1 Recommended Timeline

| Week | Activity | Deliverable | Gate |
|------|----------|-------------|------|
| 0-1 | Latent space diagnostics + training data analysis | Diagnostic reports | D0, D1 |
| 1-3 | Multi-pocket docking (all 6,800 molecules x 3 pockets) | Docking results | G3 |
| 3-4 | Write ChemRxiv preprint (whatever the docking shows) | Preprint | Priority |
| 4-6 | If G3 positive: write full JCIM paper (Framing D or E) | Draft | -- |
| 4-8 | If G3 negative: implement stronger conditioning (H1 test) | Ablation results | G4 |
| 6-8 | Submit preprint to ChemRxiv | Priority established | -- |
| 8-10 | If G4 positive: expand paper to include architecture comparison | Revised draft | -- |
| 8-10 | If G4 negative: accept null, write Framing B or E paper | Final draft | -- |
| 10-12 | Submit to JCIM or J Cheminformatics | Submission | -- |
| 12-16 | ABL1 pipeline (if positive results warrant multi-kinase) | ABL1 results | G5 |

### 9.2 Resource Requirements

| Resource | Amount | SLURM partition | Notes |
|----------|--------|-----------------|-------|
| Multi-pocket docking | ~60 GPU hours | gpu or gpu_devel | 20,400 GNINA runs |
| Stronger conditioning training | ~200 GPU hours | gpu_h200 | 20 VAE training runs |
| ABL1 pipeline | ~300 GPU hours | gpu_h200 | Full pipeline |
| Writing time | ~80 person-hours | N/A | Across 3-4 weeks |
| Total GPU | ~260-560 GPU hours | | Depends on gates |

### 9.3 Publication Strategy by Outcome

**Outcome 1: Multi-pocket docking shows signal (P = 0.55)**
- Paper: "Multi-Pocket Evaluation Reveals Hidden Signal in State-Conditioned Generation"
- Venue: JCIM full article
- Timeline: Submit by week 10
- Follow-up: ABL1 for multi-kinase generalization

**Outcome 2: Multi-pocket negative, stronger conditioning positive (P = 0.16)**
- Paper: "Architectural Requirements for State-Conditioned Molecular Generation"
- Venue: JCIM full article
- Timeline: Submit by week 12

**Outcome 3: Both negative, ABL1 positive (P = 0.12)**
- Paper: "When Does State Conditioning Work? A Multi-Kinase Investigation"
- Venue: JCIM full article
- Timeline: Submit by week 18

**Outcome 4: All negative (P = 0.17)**
- Paper: "Pre-Registered Null Result: State Conditioning Does Not Improve Kinase
  Inhibitor Generation"
- Venue: J Cheminformatics full article
- Timeline: Submit by week 10 (no additional experiments needed)

**Note:** Even Outcome 4 produces a publishable paper. The worst case is a
J Cheminformatics paper, not zero output.

---

## 10. When to Pivot to Negative-Result Publication

### 10.1 Pivot Trigger Conditions

Pivot to a pure negative-result publication if:

1. **Gate G3 negative AND latent space analysis shows no state separation** (weeks 3-4):
   If multi-pocket docking shows no signal and the latent space classifier is near
   chance, the conditioning mechanism never learned state information. This is a clean
   null that doesn't require further investigation. Pivot immediately.

2. **Gates G3 and G4 both negative** (week 8): Multi-pocket docking and stronger
   conditioning both failed. The null is robust to both evaluation design and
   architecture changes. Pivot.

3. **Week 12 deadline**: If no positive results by week 12, pivot regardless. The
   competitive landscape is closing and a published null is better than an unpublished
   positive-in-progress.

### 10.2 What Makes the Negative Result Paper Strong

The negative result paper is not a consolation prize. It is a genuine contribution if
it includes:

1. **Pre-registration**: Commit hash, fixed thresholds, analysis plan
2. **Working model**: Transformer VAE validation (EF@10 = 5-8)
3. **Scale**: 10 seeds, ~6,800 molecules, 2 generation modes
4. **False alarm analysis**: n=3 to n=10 collapse (d=0.71 to d=-0.02)
5. **Evaluation design critique**: Explicit identification of H3
6. **Multi-pocket docking results**: Even if negative, this tests H3 properly
7. **Guidelines**: Recommendations for future work on conditional generation evaluation

---

## 11. Hypothesis Probability Assessment

Based on the evidence from the G2 report, my assessment of the three hypotheses:

### H1: Weak Conditioning Mechanism -- P(root cause) = 0.30

**Evidence for:**
- Centroid distances 0.26-0.42 (6-10% of latent space scale) indicate weak separation
- Prefix tokens are a demonstrably weak conditioning mechanism for Transformers
- The Transformer decoder has 8 self-attention layers that can route around 8 prefix tokens
- Recent work (DiffGui, DiffMC-Gen) uses much stronger conditioning (cross-attention,
  FiLM, classifier guidance)

**Evidence against:**
- Even weak conditioning should produce SOME effect if the underlying signal is strong
- 64/64 active latent dimensions suggests the model has capacity
- Free-bits KL at 0.25/dim ensures latent dimensions carry information

### H2: Insufficient State-Specific Data -- P(root cause) = 0.35

**Evidence for:**
- The model generates the same drug scaffolds (erlotinib, gefitinib, osimertinib,
  lazertinib) regardless of state conditioning -- this is the strongest evidence for H2
- EGFR has limited genuine DFGout structures in the PDB
- 4-anilinoquinazolines appear across all states
- ChEMBL bioactivity data is not inherently state-labeled; assignments are inferred
  from crystal structures

**Evidence against:**
- The implementation plan identified 8,109 EGFR molecules, which is a reasonable
  training set size for a VAE
- State assignments were verified in Phase 0 (structural verification)

### H3: Wrong Evaluation Metric -- P(root cause) = 0.50

**Evidence for:**
- Section 6.2 of the G2 report explicitly acknowledges: "the ablation was structurally
  unable to detect the conditioning signal even if it existed"
- docking_proxy uses fixed 1M17 pocket (DFGin/aCin only)
- state_specificity was zeroed for fairness, eliminating 15% of the scoring signal
- AlphaFold2 MSM for kinases showed that multi-state evaluation reveals hidden
  improvements (EF1% from 6.6 to 8.2)
- The ICLR 2025 paper by Gao et al. showed that standard metrics (Vina scores) miss
  practical improvements -- same structural argument

**Evidence against:**
- The 3 non-zeroed scoring components (reference_similarity, druglikeness, docking_proxy)
  account for 85% of the score. If conditioning improved ANY generic property, it
  should show up
- Component analysis shows no effect on any individual component (all d < 0.07)

**Note:** H3 has the highest probability AND is the cheapest to test. This is why
multi-pocket docking is the first priority.

**Important caveat:** These hypotheses are not mutually exclusive. The null result
likely reflects a combination of all three: weak conditioning (H1) applied to
insufficiently differentiated data (H2) evaluated by a metric that can't detect the
signal anyway (H3). The diagnostic cascade is designed to disentangle these.

---

## 12. Specific Recommendations

### 12.1 Immediate Actions (This Week)

1. **Run latent space diagnostics** (1-2 days, zero GPU): Train a simple classifier
   (logistic regression) on encoded latent vectors to predict state labels. If accuracy
   is near 33% (random), the conditioning mechanism never learned state information.

2. **Run training data chemistry analysis** (1-2 days, zero CPU): Compute per-state
   Murcko scaffold counts and inter-state Tanimoto similarity. This distinguishes H2
   from H1/H3.

3. **Prepare 3 receptor conformers for GNINA** (1 day): Verify that 1M17, 4HJO, and
   3W2S are properly prepared as PDBQT files with box definitions.

### 12.2 Weeks 1-3: Multi-Pocket Docking

4. **Submit 3 SLURM array jobs**: Dock all ~6,800 molecules against 3 pockets. Use
   `gpu` partition with RTX 5000 Ada for GNINA.

5. **Analyze results**: Compute paired effect sizes for conditioned-vs-target-pocket
   docking. This is the critical G3 gate.

### 12.3 Weeks 3-6: Write and Preprint

6. **Draft ChemRxiv preprint** based on results through G3. Post regardless of outcome.

### 12.4 Weeks 6-12: Conditional on G3 Outcome

7. If G3 positive: Expand to full JCIM paper (Framing D or E)
8. If G3 negative: Implement stronger conditioning (G4) or pivot to Framing B

---

## 13. References

1. Cieplinski, T., Danel, T., Podlewska, S., & Jastrzebski, S. (2023). Generative
   Models Should at Least Be Able to Design Molecules That Dock Well: A New Benchmark.
   *Journal of Chemical Information and Modeling*, 63(11), 3238-3247.

2. Handa, K., Thomas, M.C., Kageyama, M., Iijima, T., & Bender, A. (2023). On the
   Difficulty of Validating Molecular Generative Models Realistically: A Case Study on
   Public and Proprietary Data. *Journal of Cheminformatics*, 15:108.

3. Gao, B., Tan, C., et al. (2025). Reframing Structure-Based Drug Design Model
   Evaluation via Metrics Correlated to Practical Needs. *ICLR 2025*.

4. Peng, X., et al. (2026). Unified Modeling of 3D Molecular Generation via Atomic
   Interactions with PocketXMol. *Cell*, February 2026.

5. Lu, W., Zhang, J., Huang, W., et al. (2024). DynamicBind: Predicting Ligand-Specific
   Protein-Ligand Complex Structure with a Deep Equivariant Generative Model. *Nature
   Communications*, 15, 1071.

6. Hilpert, C., et al. (2024). Improving Docking and Virtual Screening Performance
   Using AlphaFold2 Multi-State Modeling for Kinases. *Scientific Reports*, 14, 24567.

7. Volkamer, A., et al. (2014). KLIFS: A Knowledge-Based Structural Database to
   Navigate Kinase-Ligand Interaction Space. *Journal of Medicinal Chemistry*, 57(2),
   249-277.

8. CustomKinFragLib: Filtering the Kinase-Focused Fragmentation Library. *ACS Omega*,
   2025.

9. FRATTVAE: Leveraging Tree-Transformer VAE with Fragment Tokenization for High-
   Performance Large Chemical Model Generation. *Communications Chemistry*, 2025.

10. PCF-VAE: Posterior Collapse Free Variational Autoencoder for De Novo Drug Design.
    *Scientific Reports*, 2025.

11. Loeffler, H.H., et al. (2025). Transformer Graph Variational Autoencoder for
    Generative Molecular Design. *Biophysical Journal*.

12. In Search of Beautiful Molecules: A Perspective on Generative Modeling for Drug
    Design. *JCIM*, 2025.

13. Benchmarking Real-World Applicability of Molecular Generative Models from De Novo
    Design to Lead Optimization with MolGenBench. *bioRxiv*, November 2025.

14. MoGE: A Benchmark for Comprehensive Evaluation of Molecular Generation Models
    in De Novo Drug Design. Springer, 2025.

15. Loeffler, H., et al. (2024). Reinvent 4: Modern AI-Driven Generative Molecule
    Design. *Journal of Cheminformatics*, 16:20.

16. KASSPer: Kinase Active Site Structure Prediction using Protein and Ligand Language
    Models and Its Application to Virtual Screening. *bioRxiv*, January 2026.

17. An Efficient Computational Chemistry Approach to Generating Negative Data for Drug
    Discovery Pipeline Validation. *ChemRxiv*, 2024 (published Frontiers in
    Bioinformatics, 2026).

18. Guo, Z., et al. (2025). DiffMC-Gen: A Dual Denoising Diffusion Model for Multi-
    Conditional Molecular Generation. *Advanced Science*.

19. DiffGui: Target-Aware 3D Molecular Generation Based on Guided Equivariant
    Diffusion. *Nature Communications*, August 2025.

20. Geometry-Constrained Prediction of Catalytically Competent Kinase Domains Across
    the Human Kinome. *bioRxiv*, November 2025.

21. Structure-Based Generation of 3D Small-Molecule Drugs: Are We There Yet? *Journal
    of Medicinal Chemistry*, 2025.

22. Benchmarking 3D Structure-Based Molecule Generators. *JCIM*, 2025.

23. SCAGE: A Self-Conformation-Aware Pre-Training Framework for Molecular Property
    Prediction with Substructure Interpretability. *Nature Communications*, May 2025.

24. Generative AI for Computational Chemistry: A Roadmap to Predicting Emergent
    Phenomena. *PNAS*, 2025.

25. Exploring Pocket-Aware Inhibitors of BTK Kinase by Generative Deep Learning,
    Molecular Docking, and Molecular Dynamics Simulations. *RSC Advances*, 2025.

---

## 14. Summary of Key Findings

1. **The G2 null is publishable as-is**, but 2-3 weeks of multi-pocket docking
   significantly improves every narrative framing.

2. **H3 (wrong evaluation) is the most probable root cause** (P = 0.50) AND the
   cheapest to test. It should be tested first.

3. **The competitive landscape is closing** but StateBind's pre-registration,
   10-seed design, and evaluation critique are differentiators that are hard to
   replicate.

4. **A ChemRxiv preprint should be posted by week 6** to establish priority.

5. **The optimal strategy is a sequential cascade**: diagnostics (week 0-1) ->
   multi-pocket docking (week 1-3) -> preprint (week 3-4) -> conditional on results,
   either expand to positive paper or accept null.

6. **Every outcome produces a publishable paper.** The question is JCIM full article
   vs J Cheminformatics article, not published vs unpublished.

7. **The n=3 false alarm lesson (d=0.71 to d=-0.02)** is a standalone contribution
   that the field needs regardless of the conditioning result.

8. **ABL1 is the highest-value second kinase** if the project extends to multi-kinase.
   ABL1 has genuine DFGout structures and distinct state chemistries, making it a
   stronger test of the thesis than EGFR.
