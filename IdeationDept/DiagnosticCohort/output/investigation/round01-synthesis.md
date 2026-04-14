---
agent: Orchestrator (Investigation Lead)
round: 1
date: 2026-04-14
type: roundtable
scope: synthesis-of-5-independent-investigations
---

# Round 1 Synthesis: Where Does the G2 Failure Come From?

## 1. Executive Summary

Five specialists independently investigated the G2 NO_GO result (Cohen's d = 0.059)
from three angles: conditioning architecture (condgen), training data biology
(kinchembio), evaluation design (evaldes), model internals (mldebug), and
publication strategy (pubstrat).

**The smoking gun is in the data.** kinchembio discovered that state labels in the
training data are **randomly assigned** via `rng.choice()` for the vast majority of
the 8,109 EGFR molecules. The distribution is almost perfectly uniform (24.5-26.1%
per state), confirming random assignment. Only ~55 hand-curated compounds (0.5% of
the dataset) have meaningful state labels. mldebug independently corroborated this
finding from the metadata. **A model that learns to ignore random labels is behaving
correctly.** The null result is the expected outcome.

This finding reshuffles all three hypotheses:

| Hypothesis | Pre-Investigation | Post-Investigation | Primary Evidence |
|------------|------------------|-------------------|-----------------|
| H2: Bad data | 33% | **70-80%** | Random state labels, 0.5% meaningful annotations |
| H1: Weak architecture | 33% | **15-25%** (secondary) | Prefix tokens are weakest mechanism, but irrelevant if labels are noise |
| H3: Wrong evaluation | 33% | **15-25%** (compounding) | Real flaws exist but moot until labels are fixed |

---

## 2. What Each Specialist Found

### 2.1 condgen (Conditional Generation Expert) -- H1

**H1 probability: 70-80%** as a contributor, but only 30-40% that strengthening
conditioning alone produces d > 0.3.

Key findings:
- Prefix-token conditioning is the weakest mechanism in the modern hierarchy. DiT
  (Peebles & Xie, 2023) showed in-context/prefix conditioning produces FID nearly 2x
  worse than adaLN-Zero in a controlled comparison.
- The state one-hot (3 dims) occupies only 4.5% of the z-projection input (67 dims),
  making it a tiny perturbation.
- 1.58 bits of state information spread across 8 prefix tokens yields ~0.2 bits/token,
  easily overwhelmed by the 60-80 molecule tokens.
- Published conditional generation papers show d >> 1.0 when conditioning works. The
  observed d = 0.059 is what "no conditioning signal" looks like.

Recommendations: FiLM conditioning (~2 days), adaLN-Zero (~3-5 days), classifier-free
guidance (~1 day), and a "conditioning strength ladder" experiment (7 rungs, ~75 GPU-hours).

Critical proposal: A **positive control** using MW-tercile labels (instead of state
labels) with the same architecture. If MW conditioning works but state conditioning
doesn't, H2 is confirmed regardless of mechanism.

### 2.2 kinchembio (Kinase Chemical Biology Expert) -- H2

**H2 probability: 75-85%.** The primary root cause.

**The smoking gun:** `prepare_vae_data.py` assigns states via `rng.choice()` for all
ChEMBL API compounds (the vast majority). The assignment function
`_assign_state_from_type("")` receives an empty string (ChEMBL API doesn't return
inhibitor type), which triggers uniform random assignment across states.

State distribution confirms randomness:
| State | Count | Percentage |
|-------|-------|-----------|
| DFGin_aCin | 2,017 | 24.9% |
| DFGin_aCout | 1,993 | 24.6% |
| DFGout_aCin | 1,985 | 24.5% |
| DFGout_aCout | 2,114 | 26.1% |

Additional findings:
- **26% of data silently dropped**: The VAE config uses 3 states but data contains 4.
  ~2,114 DFGout_aCout molecules are skipped during training.
- **EGFR is type I-dominated**: >90% of known EGFR inhibitors are type I (DFGin).
  Zero approved type II. Even with perfect labels, class imbalance would be extreme.
- **No WT EGFR DFGout structures exist**: The DFGout_aCin representative (3W2R) is
  a T790M/L858R double mutant.

Recommendations: Run state classifier experiment (2 hours, CPU-only) as definitive
confirmation, then either properly annotate EGFR via KLIFS/KinCoRe or switch to
**ABL1** where genuine DFGin (dasatinib) vs DFGout (imatinib) chemotype distinction
exists.

### 2.3 evaldes (Evaluation Design Expert) -- H3

**H3 probability: 55-65%.**

Three structural evaluation flaws identified:
1. **state_specificity = 0**: Removes the only component that could differentiate
   state-conditioned molecules (15% weight zeroed).
2. **Fixed 1M17 pocket**: 2/3 of conditioned molecules scored against the wrong
   pocket -- molecules designed for DFGout get zero credit.
3. **Type I reference molecules (35% weight)**: Erlotinib/gefitinib references
   actively penalize generation of DFGout-specific chemistry.

Proposed multi-pocket docking protocol: 20,400 GNINA runs (6,800 molecules x 3
pockets), estimated 4-8 GPU-hours on H200. All receptor PDBQTs already prepared.
Includes pocket-preference matrix design and Delta Score framework (Gao et al.,
ICML 2024).

Quick diagnostic: 100-molecule pilot (300 docking runs, ~3-4 hours).

### 2.4 mldebug (ML Diagnostics Expert) -- All H's

**H2: ~45%, H1: ~35%, H3: ~20%.**

Critical architectural observation: The model has an **information shortcut**. The
decoder receives `state_onehot` directly via `[z; state_onehot] -> prefix projection`,
so the encoder has no incentive to encode state into z. This is a well-documented
conditional VAE failure mode (Nguyen et al., 2023) -- but it is also the EXPECTED
optimal behavior when state labels carry no information.

Designed a 7-experiment diagnostic battery executable in <30 GPU-minutes:
1. Probing classifier on z (root diagnostic, 5 min)
2. Encoder hidden state probe (5 min)
3. Prefix token attention analysis (10 min)
4. State-swap experiment (15 min)
5. Per-state scaffold overlap (2 min, CPU)
6. Per-dimension KL analysis (5 min)
7. Mutual information I(z; state) (5 min)

Critical pre-check: Compute Bemis-Murcko scaffold overlap in training data between
states. If Jaccard > 0.7, H2 is confirmed before touching a GPU.

### 2.5 pubstrat (Publication Strategy Advisor) -- Recovery Paths

**H3: P=0.50, H2: P=0.35, H1: P=0.30.**

Five narrative framings analyzed:
| Framing | Target Venue | P(accept) | Expected Citations |
|---------|-------------|-----------|-------------------|
| A: "When does conditioning work?" | JCIM | 0.65 | 50-100 |
| B: Pre-registered null result | J Cheminformatics | 0.80 | 30-60 |
| C: Transformer VAE method paper | J Cheminformatics | 0.75 | 20-40 |
| D: Multi-pocket reveals hidden signal | JCIM / Nat Comp Sci | 0.50 | 80-150 |
| E: Evaluation gap / benchmark paper | JCIM / ICLR workshop | 0.70 | 40-80 |

Highest expected value paths: benchmark paper (EV=4.8), negative result (EV=4.5),
multi-pocket docking (EV=4.4). Every terminal node in the decision tree is publishable.

ChemRxiv preprint recommended within 4-6 weeks to establish priority. Scooping risk:
15-20% within 6 months (mainly Volkamer group).

---

## 3. Where Agents Agree

### 3.1 Universal Agreement: Cheapest Diagnostic First

All 5 agents converge on running cheap diagnostics before any expensive fixes:
- **State classifier** (kinchembio): Random Forest on Morgan fingerprints, ~2 hours CPU
- **Probing classifier** (mldebug): Logistic regression on latent z, ~5 min GPU
- **Scaffold overlap** (mldebug): Bemis-Murcko Jaccard between states, ~30 min CPU
- **Positive control** (condgen): MW-tercile conditioning with same architecture, ~2-3 GPU-hours

**Estimated total for diagnostic battery: <1 day, <5 GPU-hours.**

### 3.2 Strong Agreement: The Architecture Is Suboptimal

condgen and mldebug agree that prefix-token conditioning is the weakest viable
mechanism. The DiT comparison (Peebles & Xie, 2023) provides quantitative evidence.
FiLM or adaLN-Zero would be strictly better. However, both note this is IRRELEVANT
if the labels are noise.

### 3.3 Strong Agreement: The Evaluation IS Flawed

evaldes, condgen, and pubstrat agree that the single-pocket evaluation structurally
cannot detect multi-state benefit. The G2 report itself acknowledges this (Section
6.2). The multi-pocket docking evaluation is a necessary follow-up regardless of
data fixes.

### 3.4 Strong Agreement: Every Outcome Is Publishable

pubstrat demonstrates that even a total null produces a publishable paper. The
pre-registration, 10-seed design, GRU-to-Transformer transition, and false alarm
analysis are genuine contributions. The worst case is a JCIM communication, not
unpublishable work.

---

## 4. Where Agents Disagree

### 4.1 Primary Disagreement: What to Fix First

| Agent | Priority 1 | Priority 2 | Priority 3 |
|-------|-----------|-----------|-----------|
| condgen | Architecture (FiLM/adaLN) | Evaluation (multi-pocket) | Data |
| kinchembio | **Data (fix labels/ABL1)** | Evaluation | Architecture |
| evaldes | **Evaluation (multi-pocket)** | Architecture | Data |
| mldebug | **Diagnostics first** | Data | Architecture |
| pubstrat | Evaluation (cheapest) | Architecture | Data/ABL1 |

**Resolution:** kinchembio's random-label finding resolves this disagreement. If
labels are random noise:
- Fixing the architecture cannot help (no signal to extract)
- Multi-pocket docking cannot help (model never learned state-specific generation)
- Only fixing the data creates a path forward

The priority order becomes: **Data > Evaluation > Architecture** (or: diagnose >
fix data > fix evaluation > fix architecture).

### 4.2 Secondary Disagreement: H3 Probability

evaldes assigns H3 probability of 55-65%, making it the most likely root cause.
kinchembio argues H3 is **moot** if labels are random -- the evaluation may be
flawed, but this is invisible behind the data problem. mldebug sides with kinchembio
(H2 at 45% vs H3 at 20%).

**Resolution:** evaldes's analysis is technically correct -- the evaluation IS
structurally flawed. But it is IRRELEVANT to the current failure because the model
was never given meaningful conditioning signal. H3 becomes relevant only AFTER H2
is fixed. The correct framing is: **H2 is the root cause; H3 and H1 are compounding
factors that would need to be fixed even after H2 is resolved.**

### 4.3 Tertiary Disagreement: ABL1 vs EGFR

kinchembio champions switching to ABL1 as the primary kinase (genuine DFGin vs DFGout
chemotype distinction). pubstrat cautions against this (8-10 weeks, highest cost
option). condgen notes it's irrelevant if the architecture is broken.

**Resolution:** ABL1 is the strongest positive control for the thesis, but it should
be a LATER step. First fix EGFR data (cheaper, tests thesis on original target),
then extend to ABL1 if EGFR shows promise.

---

## 5. Consensus Root Cause Assessment

Integrating all 5 reports with the random-label finding as the key evidence:

| Hypothesis | Probability | Role | Evidence Strength |
|------------|------------|------|------------------|
| **H2: Random state labels** | **70-80%** | **ROOT CAUSE** | Direct: code inspection shows `rng.choice()`, uniform distribution confirms. |
| H1: Weak conditioning mechanism | 15-25% | Compounding factor | Indirect: DiT comparison, information-theoretic argument. Would need fixing after H2 but is not the proximate cause. |
| H3: Wrong evaluation metric | 15-25% | Compounding factor | Direct: 3 structural flaws in evaluation. Would need fixing after H2 but cannot explain the null when labels are random. |

**The failure chain:** Random labels (H2) → model correctly ignores labels → weak
centroid separation → no state-specific generation → evaluation confirms no benefit
(which it couldn't detect even if there were benefit, due to H3 flaws).

All three hypotheses need to be addressed for a positive result, but they must be
fixed in order: H2 first (data), then H3 (evaluation), then H1 (architecture).

---

## 6. Unresolved Questions for Round 2

The following questions remain open and should be addressed by the specialists in
their Round 2 proposals:

1. **How to fix the labels for EGFR:** KLIFS annotation, docking-based assignment,
   ML prediction (Rodriguez-Perez & Bajorath 2020), or literature curation? What is
   the expected quality and coverage of each approach?

2. **Is EGFR salvageable at all?** If 90%+ of EGFR inhibitors are type I regardless
   of proper labeling, is there enough chemical diversity to support conditioning?
   What minimum class balance is needed?

3. **The positive control experiment:** MW-tercile conditioning is the most informative
   single experiment. It disentangles mechanism from data in one training run. Should
   this be run BEFORE or AFTER fixing labels?

4. **Multi-pocket docking timing:** Should we run the 20,400-docking evaluation on
   the CURRENT (random-label) models to establish a baseline? Or wait until models
   are retrained with proper labels?

5. **Which conditioning mechanism to use when retraining:** If we fix labels AND
   retrain, should we use FiLM/adaLN-Zero from the start, or re-test prefix tokens
   first (to isolate the data fix)?

6. **Publication strategy given the random-label finding:** Does discovering that the
   labels were random CHANGE the narrative? Is "we discovered our labels were noise
   and here's what happened when we fixed them" a stronger story than the original
   thesis?

---

## 7. Instructions for Round 2

Each specialist should write a proposal (DiagnosticCohort/output/proposals/
{shortname}-prop-R02.md) containing:

1. **Your top 3 concrete actions**, ranked by expected value (probability x impact x
   1/effort). Account for the random-label finding.

2. **Response to other agents' key findings:**
   - condgen: Respond to kinchembio's random-label finding. Does this change your
     recommendation for a conditioning strength ladder? Is the positive control
     (MW-tercile) still your top recommendation?
   - kinchembio: Respond to condgen's positive control proposal. Respond to evaldes's
     multi-pocket docking. Do you think EGFR is salvageable or should we switch to ABL1?
   - evaldes: Respond to the random-label finding. Is multi-pocket docking still
     useful on current models? Should we run it as a baseline before fixing data?
   - mldebug: Given random labels, which diagnostics are still informative? Can you
     design a diagnostic that CONFIRMS the labels are the problem (beyond the
     classifier)?
   - pubstrat: Reframe the decision tree accounting for the random-label discovery.
     How does this change the publication narrative?

3. **Your probability estimate for each hypothesis** (updated from Round 1).

4. **A timeline for your proposed actions** with effort estimates and SLURM specs.
