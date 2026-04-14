---
agent: Publication Strategy Advisor
round: 2
date: 2026-04-14
type: proposal
---

# Publication Strategy Proposal: Post-Random-Label Recovery Plan

## 1. Updated Assessment

The random-label discovery fundamentally transforms the strategic landscape. In Round 1,
I estimated H3 at P=0.50, H2 at P=0.35, H1 at P=0.30. Those estimates were based on
the assumption that state labels carried real biological signal. They were wrong.

**Updated probability estimates:**
- H2 (random labels / no signal in data): **P = 0.80** -- ROOT CAUSE
- H1 (weak conditioning): P = 0.20 -- compounding, irrelevant until data is fixed
- H3 (wrong evaluation): P = 0.20 -- compounding, irrelevant until data is fixed

The shift is not incremental. It invalidates most of my Round 1 decision tree. The
original cascade (multi-pocket docking first, then architecture, then ABL1) assumed the
model had been given real labels and failed to use them. The model was never given real
labels. Multi-pocket docking on randomly-labeled models is uninformative. Architecture
upgrades on randomly-labeled data are pointless. The only path forward starts with
fixing the data.

---

## 2. The Random-Label Discovery Creates a Sixth Narrative Framing

My Round 1 analysis identified 5 framings (A through E). The random-label discovery
creates a new option that is potentially stronger than all of them.

### Framing F: "The Diagnostic Journey" Paper

**Title template:** "When Conditional Generation Fails: Diagnosing Random Labels,
Evaluation Blindness, and Weak Conditioning in State-Aware Molecular Design"

**Main claim:** We pre-registered a hypothesis that conformational state conditioning
improves EGFR molecular generation. The result was a definitive null (d=0.059, 10
seeds). Systematic investigation revealed that training data labels were randomly
assigned (rendering the test uninformative), the evaluation was structurally blind to
state-specific quality, and the conditioning mechanism was the weakest viable option.
After fixing all three issues, we report [updated result]. The diagnostic journey
itself exposes failure modes in automated data pipelines, evaluation design, and
conditioning architectures that generalize beyond this specific system.

**Target venue:** JCIM (full article) or Nature Computational Science (if the fix
yields a strong positive and extends to ABL1)

**Why this is potentially the strongest framing:**

1. **The story structure mirrors the scientific method.** Hypothesis, test, null,
   investigation, root cause, fix, retest. This is more compelling than a
   straightforward positive result because it demonstrates the full cycle of
   scientific reasoning. Reviewers and readers engage with detective stories.

2. **Three independent failure modes is a contribution.** Most papers report one
   finding. This paper identifies three compounding problems (random labels, wrong
   evaluation, weak conditioning), each of which generalizes. Random label assignment
   via fallback logic is a failure mode that any automated pipeline could hit.
   Single-pocket evaluation for multi-state conditioning is a design flaw in every
   state-conditioned molecular generation study that uses a fixed receptor. Prefix-token
   conditioning being the weakest mechanism (Peebles & Xie, 2023) applies to every
   conditional Transformer VAE.

3. **The pre-registration anchors credibility.** The null was committed to before the
   investigation. The fix was motivated by diagnosis, not p-hacking. This is the
   narrative that reviewers trust most.

4. **It subsumes Framings A through E.** Framing F includes the null result (B), the
   evaluation critique (E), the investigation structure (A), and potentially the
   positive result (D). It does not exclude any of the original framings -- it wraps
   them into a more complete story.

**Probability of acceptance:** 0.60-0.75 depending on the post-fix result

**Expected citation impact:** 60-120 citations over 3 years. The diagnostic framework
has high utility. Every group training conditional generative models needs to verify
their labels and evaluation protocol.

### Updated Framing Comparison Table

| Framing | EV (Round 1) | EV (Round 2, updated) | Change | Notes |
|---------|-------------|----------------------|--------|-------|
| A: "When does conditioning work?" | 4.4 | 5.0 | +0.6 | Strengthened by root cause |
| B: Pre-registered null | 4.5 | 3.5 | -1.0 | Weakened: null was on random labels |
| C: Transformer VAE method | 3.0 | 3.0 | 0 | Unchanged, still weakest |
| D: Multi-pocket reveals signal | 4.4 | 3.0 | -1.4 | Moot until data is fixed |
| E: Evaluation benchmark | 4.8 | 4.5 | -0.3 | Still viable but needs fixed data |
| **F: Diagnostic journey** | -- | **5.5** | new | Highest EV if post-fix result exists |

**Key insight:** Framing B drops sharply because a null result on random labels is not
informative -- the pre-registration tested the wrong thing (or rather, tested with
broken data). The null cannot be presented as evidence against the thesis; it is
evidence that the experimental setup was flawed. Framing F acknowledges this honestly
and turns the flaw into a contribution.

---

## 3. Updated Decision Tree

The Round 1 cascade is replaced. The new critical path is:

```
WEEK 0: CONFIRM THE ROOT CAUSE
  |
  |-- [D0] Scaffold overlap analysis (CPU, 2 hrs)
  |   Compute Bemis-Murcko Jaccard between state-labeled groups.
  |   Expected: Jaccard > 0.85 (identical scaffolds across "states")
  |   This is the 2-hour confirmation that labels are random.
  |
  |-- [D1] MW-tercile positive control (2-3 GPU-hrs)
  |   Train with MW-based labels using same architecture.
  |   If MW conditioning works (d > 0.5): architecture is fine, data is the problem.
  |   If MW fails too: architecture also needs fixing.
  |
  v
WEEK 1-3: FIX THE DATA
  |
  |-- Option A: KLIFS-based EGFR re-annotation
  |   Use KLIFS (Kooistra et al., 2016) to map ChEMBL compounds to PDB structures
  |   with known DFG/aC conformations. Coverage: likely 500-2000 compounds with
  |   confident labels (far fewer than 8,109 but REAL).
  |
  |-- Option B: ABL1 dataset construction (parallel)
  |   ABL1 has genuine type I (dasatinib, bosutinib) vs type II (imatinib, nilotinib,
  |   ponatinib) chemotype distinction. ChEMBL has ~15,000 ABL1 compounds.
  |   KLIFS has high-quality DFG annotations for ABL.
  |
  |-- Decision: Run BOTH in parallel if resources allow.
  |   EGFR-fix is the minimum (tests thesis on original target).
  |   ABL1 is the strength multiplier (tests generalization).
  |
  v
WEEK 3-5: RETRAIN AND EVALUATE
  |
  |-- Retrain VAE with real labels (EGFR and/or ABL1)
  |   Use SAME architecture first (prefix tokens) to isolate the data-fix effect.
  |   10 seeds, same evaluation protocol.
  |
  |-- [G2-RETEST] Apply pre-registered thresholds to retrained model
  |
  |-- BRANCH:
  |   |
  |   |-- d > 0.5 (GO): Data was the problem. Write Framing F with positive ending.
  |   |   Proceed to architecture upgrade (FiLM/adaLN) for even stronger result.
  |   |   Target: JCIM full article or Nature Comp Sci (if ABL1 also positive).
  |   |
  |   |-- d in [0.3, 0.5) (PIVOT): Weak signal. Data helped but not enough.
  |   |   Run architecture upgrade (FiLM, 2 days) + multi-pocket evaluation.
  |   |   Target: JCIM full article (Framing A or F).
  |   |
  |   |-- d < 0.3 (NO_GO again): Data fix alone insufficient.
  |   |   Now H1 and H3 become relevant.
  |   |   Run FiLM conditioning (2 days) + multi-pocket docking (1 day).
  |   |   If still null: thesis may be genuinely false for EGFR.
  |   |   Check ABL1 result.
  |   |
  v
WEEK 5-7: SECOND-ORDER FIXES (if needed)
  |
  |-- Architecture upgrade: FiLM or adaLN-Zero (2-5 days)
  |-- Multi-pocket evaluation: 20,400 GNINA runs (4-8 GPU-hrs)
  |-- Classifier-free guidance: inference-time amplification (1 day)
  |
  v
WEEK 6-8: PREPRINT DECISION
  |
  |-- If ANY positive result: ChemRxiv preprint with Framing F.
  |-- If all null on EGFR but ABL1 positive: Framing F with kinase-dependent story.
  |-- If all null everywhere: Framing B (strengthened negative) + E (evaluation).
  |   The diagnostic journey is STILL the story -- it just ends differently.
```

### Timeline Comparison: Round 1 vs Round 2

| Milestone | Round 1 Estimate | Round 2 Estimate | Change |
|-----------|-----------------|-----------------|--------|
| First diagnostic | Week 0-1 | Week 0 (day 1) | Faster: scaffold overlap is trivial |
| First actionable result | Week 2-3 (docking) | Week 1 (positive control) | Faster: MW test is cheaper |
| Data fix complete | Week 8-10 (ABL1) | Week 1-3 (EGFR relabel) | Much faster: relabeling vs new kinase |
| Retrained model result | N/A | Week 3-5 | New: was not in Round 1 plan |
| Preprint-ready | Week 4-6 | Week 6-8 | Slightly later but with stronger content |
| Full paper submission | Week 12-16 | Week 10-14 | Similar but higher expected quality |

---

## 4. The Story Structure: Why the Diagnostic Journey Is the Best Paper

### 4.1 Comparison to Straightforward Positive

A paper that says "we conditioned a VAE on kinase states and it worked" is incremental.
PocketXMol (Cell, February 2026) already does pocket conditioning at a more
sophisticated level. FRATTVAE (Nature Comm Chem, 2025) is a better VAE architecture.
A straightforward positive result would need to clear a high bar to justify publication
in a top venue.

A paper that says "we pre-registered a conditioning hypothesis, got a null, discovered
three compounding failure modes through systematic investigation, fixed them, and
THEN got a positive result" is a fundamentally different contribution. It is:

1. **A methodology paper** (the diagnostic framework)
2. **A cautionary tale** (random labels in automated pipelines)
3. **An evaluation critique** (single-pocket blindness)
4. **A conditioning architecture comparison** (prefix vs FiLM vs adaLN)
5. **A positive result** (if the fix works)

This multi-layered structure maps naturally to a JCIM full article (6,000-8,000 words)
with 5-6 figures, each telling a different aspect of the story.

### 4.2 Precedent for "Failure-to-Success" Narratives

High-impact precedents for this story structure in computational chemistry and ML:

- Cieplinski et al. (JCIM 2023): Started from the observation that generative models
  fail at docking, proposed a benchmark. 80-120+ citations.
- Handa et al. (J Cheminformatics 2023): Started from the observation that
  retrospective validation is unreliable on proprietary data. High citation rate.
- Gao et al. (ICLR 2025): Started from the observation that high Vina scores do not
  equal practical utility. Conference publication at a top venue.

These papers all follow the pattern: "the community assumes X works, we show it
doesn't, we explain why, we propose what to do instead." StateBind's Framing F adds
the additional arc of "and then we actually did it and here's what happened."

### 4.3 The 10-Seed False Alarm Becomes Even More Important

In Round 1, I noted the d=0.71 (3 seeds) to d=-0.02 (10 seeds, greedy) collapse as
a cautionary tale about small-sample evaluation. With the random-label discovery, this
becomes MORE significant:

- The d=0.71 result on 3 seeds with RANDOM labels shows how easily noise can masquerade
  as signal with insufficient replication.
- This is a concrete, quantitative demonstration of the small-sample problem that is
  rampant in molecular generation (most papers use 1-3 seeds).
- A reviewer at JCIM or J Cheminformatics would find this alone worth publishing.

---

## 5. Top 3 Strategic Actions (Ranked by Expected Value)

### Action 1: Fix EGFR Labels via KLIFS + Retrain (HIGHEST PRIORITY)

**What:** Re-annotate EGFR training compounds using KLIFS structure-activity
relationships and inhibitor type classifications. Replace random state assignments
with either (a) KLIFS-derived labels for compounds with co-crystal structures, or
(b) a classifier trained on KLIFS-labeled compounds to predict labels for the rest.
Retrain the VAE with identical architecture (prefix tokens) using real labels. Run
the G2 ablation again with 10 seeds.

**Why this is the top action:**
- It directly addresses the root cause (P=0.80).
- By keeping the architecture unchanged, it isolates the data effect. If real labels
  produce d > 0.3 with the same weak conditioning mechanism, the story is clean:
  "the data was the problem, not the model."
- If real labels still produce d < 0.3, it eliminates H2 and focuses the investigation
  on H1 and H3. Either way, the experiment is maximally informative.

**Effort:** 1-3 weeks for relabeling, 1-2 weeks for retraining and evaluation.
Total: 2-5 weeks, ~50-100 GPU-hours for 10-seed training.

**Expected value:** P(success) = 0.45 (real labels help significantly) x Impact(8) +
P(partial) = 0.25 x Impact(6) + P(null) = 0.30 x Impact(4, eliminates H2) = **EV = 5.7**

**SLURM specs:** 10 training jobs, each ~5-10 GPU-hours on H200 or RTX 5000 Ada.
Use `--array=0-9` for seed parallelism. Priority queue (`-A prio_gerstein`) for
faster turnaround.

**Risk:** EGFR may be fundamentally unsuitable. If 90%+ of compounds are type I
regardless of labeling, even real labels will show minimal chemical distinction between
DFGin_aCin and DFGin_aCout. kinchembio's analysis suggests this is a real concern.
Mitigation: run ABL1 in parallel (Action 2).

### Action 2: Build ABL1 Dataset in Parallel

**What:** Construct an ABL1 dataset with real DFGin/DFGout labels from KLIFS. ABL1 has
genuine chemotype distinction: dasatinib/bosutinib (type I, DFGin) vs imatinib/nilotinib/
ponatinib (type II, DFGout). ChEMBL has ~15,000 ABL1 compounds. KLIFS has extensive
DFG annotation for ABL structures.

**Why this is the second action:**
- ABL1 is the strongest positive control for the thesis. If state conditioning works
  ANYWHERE for kinases, it should work for ABL1 where the chemotype distinction is
  established biological fact.
- A two-kinase story (EGFR null or weak, ABL1 positive) is significantly more
  publishable than a single-kinase story. It answers the question "when does
  conditioning work?" with a concrete biological criterion: when the target has
  chemically distinct ligand populations across conformational states.
- It de-risks the EGFR-only path. If EGFR labels are fixed and conditioning still
  fails (because EGFR chemistry is too homogeneous), ABL1 can rescue the paper.

**Effort:** 3-5 weeks total (1-2 weeks dataset construction, 1-2 weeks training,
1 week evaluation). ~100-150 GPU-hours. Can run FULLY in parallel with Action 1.

**Expected value:** P(ABL1 positive) = 0.55 x Impact(9, two-kinase story enables
Nature Comp Sci) + P(ABL1 null) = 0.45 x Impact(3, eliminates thesis entirely) =
**EV = 6.3**

**Responding to kinchembio's ABL1 proposal:** I agree with kinchembio that ABL1 is the
strongest validation target. The key strategic question is timing. In Round 1, I placed
ABL1 at Week 8-10 (last in the cascade). Given the random-label finding, I now
recommend starting ABL1 dataset construction in Week 1, running it in parallel with
EGFR relabeling. The marginal cost is person-hours for dataset curation; GPU hours
are additive but can be parallelized across the cluster. The publication value of a
two-kinase comparison justifies the parallel investment.

**The two-kinase publication value:** A paper comparing EGFR (homogeneous chemotypes,
weak or no conditioning benefit) with ABL1 (distinct chemotypes, strong conditioning
benefit) provides a principled answer to "when does conformational conditioning work?"
This is the paper that cites well because it gives the field a decision criterion, not
just a single data point.

### Action 3: Run Diagnostic Battery Before Any Fixes

**What:** Before spending weeks on relabeling or ABL1, run the 1-day diagnostic battery
to confirm the root cause and calibrate expectations:

1. Scaffold overlap analysis (CPU, 2 hrs) -- confirm random labels produce identical
   scaffold distributions across states
2. MW-tercile positive control (2-3 GPU-hrs) -- confirm the architecture CAN condition
   on a meaningful property
3. Probing classifier on z (5 min GPU) -- confirm state information is absent from
   latent space
4. State classifier on Morgan fingerprints (2 hrs CPU) -- confirm states are chemically
   indistinguishable in training data

**Why this is essential despite being "obvious":**
- It converts speculation into evidence. We SUSPECT labels are random based on code
  inspection and distribution analysis. These diagnostics PROVE it empirically.
- The MW-tercile test is the single most informative experiment. If MW conditioning
  works with prefix tokens, we know the architecture is sufficient for any real signal.
  If it fails, we need FiLM/adaLN even with good labels.
- The diagnostics become figures in the paper. Each diagnostic result is a panel in
  the "investigation" figure of Framing F. They are not just confirmatory -- they are
  publication content.

**Effort:** 1 day, <5 GPU-hours total.

**Expected value:** Pure information gain. Prevents spending 5 weeks on a fix that
cannot work (e.g., if the architecture is also broken). **EV = high but indirect --
it modifies the EV of Actions 1 and 2.**

---

## 6. Revised Publication Timeline

| Week | Activity | Deliverable | Gate |
|------|----------|-------------|------|
| 0 | Diagnostic battery (all 4 tests) | Root cause confirmation | D0: Labels confirmed random? |
| 0 | Begin EGFR relabeling (KLIFS) | -- | -- |
| 0 | Begin ABL1 dataset construction | -- | -- |
| 1 | MW-tercile positive control result | Architecture assessment | D1: Can architecture condition? |
| 1-3 | Complete EGFR relabeling | Properly labeled EGFR dataset | D2: Sufficient label coverage? |
| 2-4 | Complete ABL1 dataset | Properly labeled ABL1 dataset | -- |
| 3-5 | Retrain EGFR VAE (10 seeds) | G2 retest result | G2': d > 0.3? |
| 4-6 | Retrain ABL1 VAE (10 seeds) | ABL1 conditioning result | G2-ABL1: d > 0.3? |
| 5-6 | If needed: FiLM upgrade + retrain | Architecture-fixed result | G3: FiLM helps? |
| 5-6 | Multi-pocket docking evaluation | State-matched docking scores | G4: Multi-pocket helps? |
| 6-8 | Write paper (Framing F or fallback) | Manuscript draft | -- |
| 7-9 | ChemRxiv preprint | Priority established | -- |
| 10-14 | Peer review submission (JCIM) | Submitted manuscript | -- |

**Compared to Round 1 timeline:** The critical path is now 7-9 weeks to preprint
(vs 4-6 weeks in Round 1). This is slightly longer but the content is substantially
stronger because it includes the data fix and retest. The Round 1 timeline assumed
the preprint would go up after multi-pocket docking alone; the Round 2 timeline waits
for the full diagnostic-fix-retest cycle.

**Scooping risk update:** The 15-20% scooping risk within 6 months (from Round 1)
is unchanged. The random-label discovery does not change the competitive landscape --
other groups are not investigating StateBind's data pipeline. The 7-9 week timeline
to preprint is well within the 6-month window.

---

## 7. Publication Outcome Matrix

Every terminal node in the decision tree maps to a publishable paper:

| EGFR Result | ABL1 Result | Best Framing | Target Venue | Expected Citations |
|-------------|-------------|-------------|-------------|-------------------|
| Positive (d>0.5) | Positive | F: Full diagnostic journey, two kinases | Nature Comp Sci / JCIM | 100-200 |
| Positive | Null | F: EGFR diagnostic journey | JCIM | 60-100 |
| Positive | Not run | F: EGFR-only diagnostic journey | JCIM | 50-80 |
| Null | Positive | F: Kinase-dependent conditioning | JCIM | 70-120 |
| Null | Null | B+E: Pre-registered negative + evaluation | J Cheminformatics | 30-60 |
| Weak (0.3-0.5) | Positive | F: Conditioning works when chemistry allows | JCIM | 80-130 |
| Weak | Null | A: "When does conditioning work?" | JCIM | 40-70 |

**There is no unpublishable outcome.** The worst case (all null, both kinases) produces
a rigorous pre-registered negative result with diagnostic investigation, evaluation
critique, and architecture comparison. This is a J Cheminformatics full article with
30-60 expected citations. The best case (both positive) produces a Nature Computational
Science candidate with 100-200 citations.

---

## 8. Expected Citation Impact: Diagnostic Journey vs Direct Result

The diagnostic journey (Framing F) has higher expected citation impact than a direct
positive or negative result because it provides multiple citable components:

| Component | Who Cites It | Estimated Fraction of Total Citations |
|-----------|-------------|--------------------------------------|
| Random-label failure mode | Groups building automated data pipelines | 20-25% |
| Single-pocket evaluation critique | All state-conditioned generation papers | 25-30% |
| Conditioning mechanism comparison | All conditional molecular generation papers | 15-20% |
| Pre-registered null methodology | Papers arguing for rigor in computational chemistry | 10-15% |
| Small-sample false alarm (10-seed) | Papers discussing evaluation reproducibility | 10-15% |
| Positive conditioning result (if any) | Direct competitors and followers | 15-20% |

A direct positive result paper would be cited primarily by direct competitors (a
narrow pool). The diagnostic framework paper is cited by a much broader audience:
anyone building conditional generative models, anyone designing evaluation protocols,
anyone constructing training datasets from automated pipelines. This breadth is why
Cieplinski et al. (2023) and Gao et al. (ICLR 2025) have high citation counts --
their contributions are methodological, not system-specific.

**Estimated citation comparison:**
- Direct positive result only: 40-80 citations (3 years)
- Direct negative result only: 20-40 citations (3 years)
- Framing F (diagnostic journey with fix): 60-150 citations (3 years)

The premium for Framing F is 50-100% higher expected citations because each diagnostic
finding is independently citable.

---

## 9. Responses to Other Agents

### 9.1 Response to kinchembio (ABL1 Proposal)

Strongly agree that ABL1 should be pursued, but I recommend parallel execution rather
than sequential. In Round 1, ABL1 was at Week 8-10 -- the expensive last resort. With
the random-label finding, the calculus shifts: we now KNOW EGFR labels need fixing,
so the question is not "should we try ABL1?" but "when?" Starting ABL1 dataset
construction in Week 1 (while EGFR relabeling proceeds in parallel) costs person-hours
but saves calendar time. The two-kinase comparison is worth the parallel investment
because it transforms the paper from a single-system study to a generalizable finding.

### 9.2 Response to condgen (MW-Tercile Positive Control)

This remains the single most informative experiment and should run on Day 1, before
any data fixes. It answers: "can the architecture condition at all?" If MW works,
prefix tokens are sufficient for meaningful conditioning, and the data is confirmed as
the bottleneck. If MW fails, we need FiLM/adaLN even after fixing labels. Either
answer saves weeks of misdirected effort.

### 9.3 Response to evaldes (Multi-Pocket Docking)

Agree the evaluation is structurally flawed, but I downgrade the priority of running
multi-pocket docking on CURRENT (random-label) models. The expected information value
is near zero: the model was trained on random labels, so there is no state-specific
generation signal to detect regardless of evaluation protocol. Multi-pocket docking
should be run AFTER retraining with real labels (Week 5-6 in the revised timeline).
The one exception: running a 100-molecule pilot on current models as a BASELINE could
be useful for the before/after comparison in the paper (30 minutes, trivial cost).

### 9.4 Response to mldebug (Diagnostic Battery)

The 7-experiment battery is valuable but should be triaged. The scaffold overlap
analysis and probing classifier are the two highest-value diagnostics and should run
immediately. The attention analysis (experiment 3) and state-swap experiment
(experiment 4) are more informative AFTER retraining with real labels, when we want
to verify the conditioning signal is actually propagating through the model. Running
the full battery twice (before and after data fix) creates a compelling before/after
figure for the paper.

---

## 10. Summary of Recommendations

1. **Run the diagnostic battery on Day 1** -- especially scaffold overlap and MW-tercile
   positive control. Cost: 1 day. Value: confirms root cause, calibrates architecture.

2. **Fix EGFR labels AND build ABL1 dataset in parallel** starting Week 1. EGFR
   relabeling is the minimum viable fix. ABL1 is the strength multiplier. Running
   both in parallel costs person-hours but saves 3-4 weeks of calendar time compared
   to sequential execution.

3. **Retrain with real labels using the SAME architecture first.** Isolate the data
   effect. If real labels + prefix tokens produce d > 0.3, the story is clean. If not,
   then upgrade to FiLM/adaLN as a second-order fix.

4. **Target Framing F** (diagnostic journey) for the paper. This subsumes all other
   framings and has the highest expected citation impact. Every intermediate result
   (diagnostics, false alarm, root cause, fix, retest) becomes a figure.

5. **ChemRxiv preprint at Week 7-9** after at least one kinase shows a post-fix result.
   This establishes priority within the 6-month scooping window.

6. **The paper writes itself as the experiments proceed.** Each diagnostic, each fix,
   each retest is a section. Start writing the introduction and methods now; fill in
   results as they arrive. The manuscript structure is: pre-registration, null,
   investigation (3 failure modes), fix (3 fixes), retest (2 kinases), guidelines.
