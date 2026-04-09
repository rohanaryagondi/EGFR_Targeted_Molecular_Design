---
agent: Program Director / Chief Scientist
round: 1
date: 2026-04-09
type: review-assessment
---

# Program Director Review: StateBind Publication Strategy Assessment

## Executive Summary

After extensive review of both cohorts' final agendas, all 10 proposals, and
independent competitive landscape research, my assessment is:

**Recommendation: One-paper strategy targeting JCIM, with a clear 12-week
timeline to submission. The benchmark paper is deferred to a second phase.**

The novelty window is narrowing but not closed. DynamicBind (Nature Communications,
2024), DynamicFlow (ICLR 2025), and Apo2Mol (AAAI 2026) all address protein
flexibility in molecular generation, but none condition on discrete conformational
states. StateBind's niche -- "does conditioning on conformational state labels
improve molecular design?" -- remains unclaimed as of April 2026. However, the
field is converging rapidly, and every month of delay increases the risk that
someone publishes a kinase-specific conformational benchmark or state-conditioned
generation paper that preempts the core claim.

The minimum viable paper requires four things: (1) the three pre-publication
fixes (osimertinib leak, structure verification, bootstrap CIs), (2) the ablation
suite proving state information drives enrichment, (3) multi-kinase validation
on 3 additional kinases, and (4) at least one external baseline (REINVENT 4).
Everything else is enhancement, not requirement.

---

## 1. One-Paper vs Two-Paper Strategy

### My Verdict: One Paper First. Decisively.

Cohort1 recommends a single paper (JCIM primary, Nature Comp Sci stretch).
Cohort2 recommends two papers (Nature Comp Sci + JCIM benchmark). I side with
Cohort1's strategy, with modifications.

**Arguments against the two-paper strategy:**

1. **Paper 2 (benchmark) blocks on Paper 1 results.** The benchmark paper requires
   multi-kinase data, external baselines, and evaluation infrastructure that are
   all produced during Paper 1 work. Cohort2 claims the benchmark can proceed "in
   parallel," but the benchmark's credibility depends on having baseline results
   from the primary paper. Publishing a benchmark without the validation paper is
   putting the cart before the horse -- reviewers will ask "has this benchmark been
   used to produce any finding?"

2. **There is not enough material for two genuinely independent papers.** The
   benchmark paper is essentially a repackaging of Paper 1's evaluation framework.
   The "4-task benchmark" (bencharch-P01) is the evaluation protocol of the primary
   paper with a Docker container and a leaderboard. This is supplementary material
   promoted to a paper. JCIM reviewers will recognize this immediately.

3. **Two papers double the review burden with marginal benefit.** Each paper
   requires a separate manuscript, separate review cycles, and separate revision
   rounds. The benchmark paper alone is estimated at 8 weeks (bencharch-P01) with
   1,300-2,500 GPU-hours for baselines. This is substantial effort that delays
   the primary result.

4. **The benchmark paper targets NeurIPS 2026 E&D (May 6 deadline) or JCIM.**
   NeurIPS 2026 is 27 days away -- completely infeasible. NeurIPS 2027 is 13
   months away. JCIM as a secondary venue for a benchmark paper is risky because
   benchmark papers at JCIM are evaluated on utility, and a benchmark with one
   EGFR target has limited utility.

5. **Time-to-first-publication matters more than paper count.** One strong JCIM
   paper published in Q3 2026 is worth more than two papers published in Q1 2027.
   The competitive landscape analysis below shows why.

**The one-paper strategy:**
- Target: JCIM (primary), Nature Comp Sci (stretch if within-method ablations
  succeed across architectures)
- Timeline: 12 weeks to submission (target: early July 2026)
- Content: Multi-kinase validation + ablation suite + at least one external
  baseline + scoring sensitivity analysis + conformational selection narrative

**When does the benchmark paper make sense?** After Paper 1 is submitted and under
review. The benchmark paper then extends Paper 1's evaluation framework to 5+
kinases, adds community infrastructure (Docker, leaderboard), and targets NeurIPS
2027 E&D (deadline ~May 2027). This gives 12 months to build the benchmark
properly. Rushing it now produces a mediocre benchmark and delays a strong primary
paper.

---

## 2. Competitive Landscape Analysis

### 2.1 Direct Competitors

| Method | Publication | What It Does | Overlap with StateBind |
|--------|------------|-------------|----------------------|
| DynamicBind | Nature Communications, Feb 2024 | Predicts ligand-specific protein-ligand complex structures using equivariant generative model | Models ligand-induced conformational change, but does NOT condition on discrete states |
| DynamicFlow | ICLR 2025 (arXiv 2503.03989) | Integrates protein dynamics into drug design via full-atom stochastic flows | Models backbone/sidechain dynamics during generation; NOT state-conditioned |
| Apo2Mol | AAAI 2026 (arXiv 2511.14559) | Generates 3D molecules from apo protein structures, predicting holo conformational changes | Apo-to-holo transition; NOT multi-state conditioning |
| FLOWR | arXiv 2504.10564, 2025 | Flow matching for de novo, interaction- and fragment-based ligand generation | Pocket-conditioned but NOT state-conditioned |
| PLACER | PNAS, Nov 2025 | Models protein-small molecule conformational ensembles | Ensemble prediction, NOT generation conditioning |
| REINVENT 4 | J Cheminformatics, Feb 2024 | Modern RL-driven generative molecule design | Standard baseline; no conformational state awareness |

**Critical finding: No published paper conditions molecular generation on discrete
conformational states of the same protein.** The Cohort1 research confirming this
gap (genai-R02, 30+ searches) is independently verified by my own searches above.
DynamicBind, DynamicFlow, and Apo2Mol all model conformational flexibility
implicitly (through apo-holo transitions or side-chain dynamics), but none ask
the question "does providing explicit state labels improve generation?"

This is StateBind's genuine novelty. The question, not the model, is the contribution.

### 2.2 Competitive Risk Assessment

**Risk: Medium-High, time-sensitive.**

The field is converging on dynamics-aware molecular generation:
- DynamicFlow (ICLR 2025) shows that modeling protein dynamics during generation
  is feasible and improves results.
- Apo2Mol (AAAI 2026) uses a curated dataset of 24,000 apo-holo pairs to train
  dynamics-aware generation.
- PLACER (PNAS 2025, Baker Lab) generates conformational ensembles for protein-
  ligand complexes.
- The BMCS "Conformational Design in Drug Discovery" symposium (2024, with a 3rd
  edition planned for 2026) shows growing community interest.

**The gap between "implicit dynamics" and "explicit state conditioning" will close.**
Someone will inevitably ask: "If I provide DFG-in vs DFG-out labels to my
generator, does enrichment improve?" StateBind should be the paper that answers
this question first.

**Relay Therapeutics** is the most visible commercial competitor. Their Dynamo
platform (cryo-EM + MD + ML for conformational dynamics) has produced zovegalisib
(PI3Kalpha, Phase 3 registration). However, Relay publishes clinical results, not
methodology papers. Their platform details remain largely proprietary. StateBind as
an "open-source, generalizable framework" is a complementary, not competitive,
positioning. Both cohorts correctly identified this framing.

**Insilico Medicine** (Chemistry42) focuses on generative chemistry with multi-
objective optimization (16.7% hit rate on TNIK, Nature Medicine 2025). Their
approach is generative model + ADMET-in-the-loop, not conformational state-aware.
Different lane.

**Academic groups (Welling, Coley, Bronstein):** No published work on state-
conditioned kinase generation from these groups as of April 2026. However, these
are exactly the groups that could rapidly produce such work given their diffusion
model and equivariant GNN expertise.

### 2.3 Competitive Timeline Estimate

Based on the convergence rate: I estimate a 30-40% probability that a directly
competing paper (explicit state-conditioned generation for kinases) appears within
12 months. This drops to <15% if StateBind publishes first and defines the
benchmark, because subsequent papers would cite StateBind rather than compete
with it. **First-mover advantage is real and time-limited.**

---

## 3. Venue Analysis

### 3.1 Nature Computational Science

- **Impact Factor:** 18.3 (June 2025)
- **Fit for StateBind:** Conditional. Nature Comp Sci wants generality and impact.
  A single-kinase case study will be desk-rejected. A 4-kinase study showing a
  transferable principle (state-conditioning improves enrichment across kinases AND
  across generation architectures) has a shot, but the bar is high.
- **Desk rejection risk:** ~60-70% for the current scope. Would drop to ~40-50%
  with within-method ablations showing architecture-agnostic state benefit.
- **Review timeline:** ~3-4 months from submission to decision.
- **My recommendation:** Aspirational stretch target only. Do not optimize the
  paper for Nature Comp Sci. Write for JCIM, and if the within-method ablations
  (REINVENT 4-pocket vs 1-pocket, FLOWR 4-pocket vs 1-pocket) show strong results,
  consider upgrading the submission.

Recent Nature Comp Sci publications in molecular design include SynGFN (bridging
design and synthesis), ECloudGen (electron cloud diffusion), and DiffGui (guided
equivariant diffusion published in Nature Communications 2025). These are all
methodologically novel architectures. StateBind's contribution is a benchmark/
framework question, which is a harder sell at Nature Comp Sci unless the
transferable principle result is very strong.

### 3.2 JCIM

- **Impact Factor:** ~6 (CiteScore ~12.3)
- **Fit for StateBind:** Strong. JCIM regularly publishes benchmarking studies,
  framework papers, and retrospective validations. The "does state-conditioning
  improve molecular design?" question is exactly the kind of computational
  hypothesis paper JCIM values.
- **Desk rejection risk:** <15% if the paper has multi-kinase results and external
  baselines.
- **Review timeline:** ~6-8 weeks for first decision (based on SciRev data).
- **My recommendation:** Primary target. Write the paper for JCIM reviewers.

Recent JCIM publications include cross-docking benchmarks for kinases (2025),
3D structure-based molecule generator benchmarks (2025), and molecular generation
reviews. The venue is receptive to exactly this type of work.

### 3.3 NeurIPS 2026 E&D Track

- **Deadline:** May 6, 2026 (27 days from now)
- **Fit:** The benchmark paper (bencharch-P01) would be appropriate for this track.
  The track explicitly welcomes "evaluation as an object of scientific study."
- **Feasibility:** Completely infeasible for May 2026. The benchmark requires
  multi-kinase data, Docker containers, baseline runs, and evaluation code that
  do not exist yet.
- **My recommendation:** Target NeurIPS 2027 E&D for the benchmark paper, after
  Paper 1 is published. Deadline would be ~May 2027, giving 13 months.

### 3.4 ICML 2026

- **Deadline:** January 28, 2026 (already passed)
- **Irrelevant for current planning.**

---

## 4. Priority Ranking by Expected Value

I use Expected Value = (Impact x P(success)) / Effort, where Impact is on a 1-10
scale (10 = transforms the paper from unpublishable to publishable), P(success) is
probability of achieving the desired result, and Effort is in person-weeks.

### Tier 1: Non-Negotiable (Must Do)

| # | Work Item | Impact | P(success) | Effort (pw) | EV | Rationale |
|---|-----------|--------|------------|-------------|-----|-----------|
| 1 | Osimertinib reference leak fix | 9 | 0.99 | 0.1 | 89.1 | Reviewer kill-shot. Hours of work. Infinite EV. |
| 2 | Bootstrap CIs + BEDROC | 9 | 0.99 | 0.2 | 44.6 | No CIs = unpublishable. Hours of work. |
| 3 | Structure verification (3W2R, 4ZAU) | 8 | 0.95 | 0.5 | 15.2 | Structural biology reviewers will check. Days. |
| 4 | Ablation C: Unconditioned VAE | 10 | 0.90 | 1.0 | 9.0 | Thesis-critical. Without this, cannot claim state effect. |
| 5 | Multi-kinase validation (ABL1, BRAF, MET) | 9 | 0.75 | 8.0 | 0.84 | N=5 held-out drugs is statistically embarrassing. Must expand. |
| 6 | External baseline: REINVENT 4 | 8 | 0.85 | 2.0 | 3.4 | Reviewers will ask "vs REINVENT?" -- must answer. |

### Tier 2: High Value (Should Do)

| # | Work Item | Impact | P(success) | Effort (pw) | EV | Rationale |
|---|-----------|--------|------------|-------------|-----|-----------|
| 7 | Ablation suite (remaining: D, E, F, G) | 7 | 0.90 | 1.5 | 4.2 | Isolates state effect from count/diversity confounds. |
| 8 | Scoring sensitivity analysis (Dirichlet) | 7 | 0.95 | 0.5 | 13.3 | Pre-empts "you chose weights to win" attack. Low effort. |
| 9 | Conformational selection narrative | 6 | 0.95 | 1.0 | 5.7 | Zero-compute. Elevates paper's biological depth. |
| 10 | 3-component scoring (no state_specificity) | 7 | 0.95 | 0.3 | 22.2 | Mandatory fairness check for non-state-aware baselines. |

### Tier 3: Valuable Enhancement (Nice to Have)

| # | Work Item | Impact | P(success) | Effort (pw) | EV | Rationale |
|---|-----------|--------|------------|-------------|-----|-----------|
| 11 | GIST water thermodynamics | 5 | 0.80 | 2.0 | 2.0 | Beautiful figure, physics-based validation. Not required for JCIM. |
| 12 | Survival funnel (ADMETlab + AiZynthFinder) | 5 | 0.85 | 2.0 | 2.1 | Differentiates from academic exercises. Worth doing if time allows. |
| 13 | External baseline: FLOWR | 4 | 0.70 | 1.5 | 1.9 | 3D baseline. Valuable but REINVENT 4 is sufficient for JCIM. |
| 14 | Within-method state ablations | 7 | 0.60 | 3.0 | 1.4 | Nature Comp Sci upgrade. High value IF it works. Uncertain. |
| 15 | Conformational classification mapping | 3 | 0.95 | 0.5 | 5.7 | Reviewer defense table. Low effort, moderate value. |

### Tier 4: Defer (Not for This Paper)

| # | Work Item | Impact | P(success) | Effort (pw) | EV | Rationale |
|---|-----------|--------|------------|-------------|-----|-----------|
| 16 | Scoring reform (change reference similarity) | 5 | 0.70 | 3.0 | 1.2 | Changing scoring invites "you gamed the metric" attack. Too risky for primary analysis. |
| 17 | Kinetic scoring (tauRAMD) | 4 | 0.50 | 6.0 | 0.33 | 150-250 GPU-days for uncertain return. cheminfo critique correctly identified Tier 3 redundancy. |
| 18 | OpenFE FEP validation | 5 | 0.65 | 4.0 | 0.81 | 120-180 GPU-hours. Nice but not decisive for JCIM. |
| 19 | Benchmark infrastructure (Docker, leaderboard) | 3 | 0.80 | 4.0 | 0.60 | Paper 2 scope. Defer. |
| 20 | Pocket-aware scoring (DrugCLIP) | 4 | 0.55 | 3.0 | 0.73 | Interesting but adds complexity. Not needed for JCIM submission. |
| 21 | C797S resistance docking | 3 | 0.60 | 3.0 | 0.60 | Translational story is nice but not required. AF2 DFGout structures have known issues (87% DFGin bias). |
| 22 | Experimental validation design | 2 | 0.90 | 1.0 | 1.8 | Zero compute, but SPR/HDX-MS are $40-100K and require collaborator. Discussion section only. |

### Items to Cut Entirely

| Work Item | Why Cut |
|-----------|---------|
| Kinetic scoring as 5th component | cheminfo critique proved Tier 3 is redundant with state_specificity. Adding a 5th component before understanding the 4 you have is scope creep. |
| Full scoring reform as primary analysis | Changing scoring to make state-aware win = confirmation bias perception. Report original scoring as primary, sensitivity analysis as supplementary. |
| Pocket representation ablation (ESM-2, ProstT5, KLIFS fingerprint) | Paper 2 scope. Interesting ML question but not needed for the primary publication question. |
| Uni-Mol comparison | Marginal improvement over Morgan FPs for this application. The Praski & Adamczyk (2025) benchmark showed most pretrained embeddings fail to beat ECFP baselines. |
| PKSmart PK predictions | Cohort1 correctly demoted to supplementary. medchem critique noted R-squared too low. |

---

## 5. Timeline and Milestones

### 12-Week Plan to JCIM Submission

```
WEEK 0 (April 9-11): PRE-PUBLICATION FIXES
  [x] Fix osimertinib reference leakage (hours)
  [x] Verify 3W2R and 4ZAU against KLIFS/KinCore (1-2 days)
  [x] Compute BCa bootstrap CIs on current EGFR results (hours)
  [x] Add BEDROC(alpha=20) to current evaluation (hours)
  GO/NO-GO: If 3W2R mutation critically affects results, find
    WT DFGout structure immediately. If none exists, adjust 
    to 3-state model (DFGin/aCin, DFGin/aCout, DFGout/aCin).

WEEKS 1-2 (April 14-25): ABLATION SUITE + BASELINE SETUP
  [ ] Train unconditioned VAE (Experiment C) -- 1-2 GPU-days
  [ ] Run ablation Experiments C, E, F, G on EGFR (1-2 days each)
  [ ] Set up REINVENT 4 with EGFR GNINA scoring (1-2 weeks)
  [ ] Begin ABL1 conformational atlas from KLIFS (1 week)
  MILESTONE: Ablation C result available.
  GO/NO-GO: If unconditioned VAE matches state-conditioned on
    enrichment (Cohen's d < 0.5), the paper pivots to "diverse
    generation" narrative. Still publishable at JCIM, but a 
    different story. Decision point: proceed with state-aware
    framing or pivot.

WEEKS 2-3 (April 28 - May 9): MULTI-KINASE DATA PREPARATION
  [ ] BRAF and MET conformational atlas preparation (1-2 weeks)
  [ ] ChEMBL bioactivity extraction for ABL1, BRAF, MET
  [ ] Run REINVENT 4 generation on EGFR
  [ ] Run ablation suite Experiment D (state-aware template only)
  [ ] Begin conformational selection narrative draft (1 week)
  MILESTONE: All multi-kinase data curated.

WEEKS 3-5 (May 12 - May 23): MULTI-KINASE TRAINING + GENERATION
  [ ] Train VAE + MPNN for ABL1, BRAF, MET (~10 GPU-days each)
  [ ] Generate candidates for each kinase per state
  [ ] GNINA docking for all kinases (~10 GPU-days)
  [ ] REINVENT 4 on EGFR complete; score and evaluate
  [ ] 3-component scoring run (no state_specificity) for fairness
  MILESTONE: Multi-kinase generation complete.
  GO/NO-GO: If any kinase shows zero enrichment, report honestly
    but check for data quality issues. If 2 of 3 new kinases fail,
    the multi-kinase generalization claim weakens. Fall back to
    "kinases with rich conformational data" framing.

WEEKS 5-7 (May 26 - June 12): EVALUATION + ANALYSIS
  [ ] Retrospective enrichment on all 4 kinases (per-kinase + pooled)
  [ ] Bootstrap CIs on all enrichment metrics
  [ ] Pareto analysis across kinases
  [ ] Scoring sensitivity analysis (1,000+ Dirichlet samples)
  [ ] Survival funnel: ADMETlab 3.0 profiling on all candidates
  [ ] RAscore + AiZynthFinder on top 50 per pipeline
  MILESTONE: All quantitative results available.

WEEKS 7-8 (June 15-26): FIGURES + SUPPLEMENTARY
  [ ] Generate all publication figures (6-8 main, 4-6 supplementary)
  [ ] Conformational classification mapping table
  [ ] Conformational selection Discussion section
  [ ] State-selectivity analysis (DFGout targeting fraction)
  MILESTONE: All figures drafted.

WEEKS 8-10 (June 29 - July 10): MANUSCRIPT WRITING
  [ ] Introduction + Related Work
  [ ] Methods
  [ ] Results
  [ ] Discussion + Conclusion
  [ ] Supplementary Information
  MILESTONE: Complete manuscript draft.

WEEKS 10-12 (July 13-24): REVISION + SUBMISSION
  [ ] Internal review and revision
  [ ] Code/data availability preparation
  [ ] Submit to JCIM
  MILESTONE: Paper submitted.
  TARGET DATE: Week of July 20, 2026.
```

### Post-Submission Phase (Weeks 13+)

```
WEEKS 13-16: OPTIONAL ENHANCEMENTS (during review)
  [ ] GIST water thermodynamics (if time)
  [ ] FLOWR baseline (if time)
  [ ] Within-method state ablations (REINVENT 4-pocket vs 1-pocket)
  [ ] If within-method ablations strong: prepare Nature Comp Sci upgrade
  [ ] Begin benchmark infrastructure for Paper 2

WEEKS 16-20: RESPOND TO REVIEWS
  [ ] Address reviewer comments
  [ ] Run additional experiments if requested
  [ ] Resubmit

MONTHS 6-12: PAPER 2 (BENCHMARK)
  [ ] Extend to 5+ kinases
  [ ] Build Docker/Singularity containers
  [ ] Run additional baselines (FLOWR, MolCRAFT, DiffSBDD)
  [ ] Target NeurIPS 2027 E&D (deadline ~May 2027)
```

---

## 6. Kill Criteria

### Per Work Item

| Work Item | Kill Criterion | Pivot Strategy |
|-----------|---------------|----------------|
| Ablation C (unconditioned VAE) | Cohen's d < 0.5 for state effect after 3 runs | Pivot to "diverse generation outperforms template-based design." Still a valid JCIM paper with a different narrative. |
| Multi-kinase validation | 0 of 3 new kinases show enrichment | Fall back to 2-kinase paper (EGFR + best second). Re-examine whether the state atlas is correct for failed kinases. If atlas is correct and enrichment is zero, report as honest negative result per pre-registration. |
| Multi-kinase validation | 1 of 3 new kinases show enrichment | Report mixed results honestly. Frame as "state-conditioning helps when conformational diversity exists in PDB structures." Examine what distinguishes the responsive kinase. |
| REINVENT 4 setup | Setup takes >2 weeks or fails | Use fingerprint search + random ChEMBL as baselines. These are weaker but sufficient for JCIM if the ablation suite is strong. |
| REINVENT 4 outperforms StateBind on all metrics | EF@10 for REINVENT 4 > state-aware on all kinases | Frame StateBind as evaluation framework, not generator. The paper becomes "does state-conditioning help?" with the answer being "REINVENT 4 with per-state scoring outperforms REINVENT 4 with single-pocket scoring" -- this is still the transferable principle. |
| GIST water analysis | Convergence issues, no clear state discrimination | Cut from paper. Not required for JCIM. |
| Scoring sensitivity | >80% of Dirichlet samples favor static | Serious problem. But this is already known (56% favor static with original weights). Report transparently. The enrichment metrics (EF@10, BEDROC) tell the real story, not mean composite score. |

### Program-Level Kill Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Total timeline | >16 weeks to submission | Cut Tier 3 items. Submit with Tier 1 + Tier 2 only. |
| Compute budget | >60 GPU-days consumed | Reduce multi-kinase to 2 kinases (EGFR + ABL1 only). |
| Ablation C fails AND multi-kinase fails | State-conditioning shows no benefit in any experiment | Pivot entire paper to "multi-kinase molecular generation benchmark" without state-conditioning claim. Publish as a benchmark/framework paper at JCIM. The infrastructure has independent value. |

---

## 7. Minimum Viable Paper

### What MUST Be in the JCIM Submission

1. **Pre-publication fixes done:** Osimertinib leak fixed, structures verified,
   bootstrap CIs computed, BEDROC added.

2. **Ablation suite (at minimum Experiments C and E):** Proves state information
   contributes to enrichment beyond diversity/count effects.

3. **Multi-kinase validation on 3+ kinases (EGFR + 2 of {ABL1, BRAF, MET}):**
   Per-kinase enrichment with bootstrap CIs. Pooled enrichment. I-squared
   heterogeneity test.

4. **At least one external baseline (REINVENT 4):** Scored under the same
   evaluation protocol.

5. **3-component scoring as secondary analysis:** Demonstrates fairness to
   non-state-aware methods by removing the state_specificity handicap.

6. **Scoring sensitivity analysis:** 1,000+ Dirichlet-sampled weight configurations.
   Reports fraction favoring each pipeline.

7. **Conformational selection narrative:** Discussion section linking state-aware
   DFGout design to the conformational selection mechanism and published residence
   time data.

8. **Code and data availability:** GitHub repo (or Zenodo) with evaluation code,
   configs, and instructions to reproduce.

### What Is NOT Required for JCIM

- GIST water thermodynamics (nice figure, not required)
- FLOWR or any 3D baseline (REINVENT 4 is sufficient)
- Survival funnel (ADMETlab + AiZynthFinder) -- supplementary at best
- FEP validation (deferred to Nature Comp Sci upgrade)
- Kinetic scoring component (deferred entirely)
- Pocket-aware scoring (DrugCLIP/ProFSA) (Paper 2)
- Experimental validation design (Discussion section mention only)
- Benchmark infrastructure (Docker, leaderboard) (Paper 2)

---

## 8. Key Disagreements Between Cohorts and My Resolution

### 8.1 Scoring Reform: Cohort2's Priority 1 vs Cohort1's "Supplementary Only"

**Cohort2 position:** Scoring reform is the #1 publication blocker. Must expand
reference set from 3 drugs to 100-300 ChEMBL centroids, test multiple similarity
metrics, add pocket-aware scoring.

**Cohort1 position:** Do NOT revise scoring for primary analysis. Report original
scoring as primary, sensitivity analysis as supplementary. Changing scoring to
make state-aware win invites bias perception.

**My resolution:** Cohort1 is right. The primary analysis MUST use the original,
pre-existing scoring function (0.35/0.30/0.20/0.15). Any modification to scoring
that happens to favor state-aware will be attacked as post-hoc optimization.
However, both cohorts agree on reporting 3-component scoring (removing
state_specificity) as a mandatory fairness check, and Dirichlet sensitivity analysis
as supplementary. These are analysis additions, not scoring changes. The story is:
"Under the original scoring function, enrichment metrics (EF@10, BEDROC) favor
state-aware despite mean composite score favoring static. Sensitivity analysis
shows this is robust across weight configurations."

Cohort2's reference set expansion (3 drugs to ChEMBL centroids) is scientifically
motivated but tactically wrong for the primary paper. It changes the baseline. Save
it for Paper 2 or a follow-up study.

### 8.2 Kinase Panel

**Cohort1:** EGFR + ABL1 + BRAF + MET (4 kinases). Dropped RET, JAK2, ALK.

**Cohort2:** EGFR + ABL1 + BRAF + (MET or CDK2) (3-4 kinases). Dropped JAK2.
ALK supplementary only.

**My resolution:** Both cohorts agree on EGFR + ABL1 + BRAF as the core set.
The fourth kinase (MET vs CDK2) matters less than getting the first three right.
My recommendation: EGFR + ABL1 + BRAF + MET. MET has a stronger clinical
rationale (most common EGFR resistance mechanism, 15-18% of cases, keeping the
NSCLC focus). CDK2 has more structures (400+) but weaker clinical narrative.
Start with ABL1 (most data, best characterized DFGout), then BRAF, then MET.
If MET's structural data is too sparse, drop to 3 kinases. Three kinases with
strong results is better than four kinases with one weak result.

### 8.3 Venue Strategy

**Cohort1:** JCIM primary, Nature Comp Sci stretch.

**Cohort2:** Nature Comp Sci primary, JCIM fallback.

**My resolution:** JCIM primary. Nature Comp Sci has IF~18.3 and probably
60-70% desk rejection for this scope. The paper's contribution is a benchmark
question ("does state-conditioning help?"), not a methodological innovation.
Nature Comp Sci's recent molecular design publications (SynGFN, ECloudGen) are
methodologically novel architectures. StateBind is a rigorous evaluation of a
design principle -- excellent JCIM material, borderline Nature Comp Sci.

The Nature Comp Sci upgrade path exists: if within-method ablations (REINVENT
4-pocket vs 1-pocket, FLOWR 4-pocket vs 1-pocket) show that state-conditioning
improves enrichment across architectures, the claim elevates to "state-conditioning
is a transferable design principle." This is Nature Comp Sci material. But this
requires additional work (FLOWR setup, within-method ablations) that should not
block the JCIM submission.

---

## 9. Resource Allocation

### Compute Budget

| Phase | GPU-Days | Priority |
|-------|----------|----------|
| Pre-publication fixes | <0.1 | P0 |
| Ablation suite (EGFR) | 2-5 | P0 |
| REINVENT 4 baseline | 1-2 | P0 |
| Multi-kinase (ABL1 training + docking) | 10-14 | P0 |
| Multi-kinase (BRAF training + docking) | 10-14 | P0 |
| Multi-kinase (MET training + docking) | 10-14 | P0 |
| Sensitivity analysis | 0.5 | P1 |
| **Total P0-P1** | **~34-50** | |
| GIST (if pursued) | 2-4 | P2 |
| Survival funnel | <0.1 | P2 |
| FLOWR (if pursued) | 1-2 | P2 |
| **Total with P2** | **~38-57** | |

This is feasible on Yale Bouchet with 2-3 H200 nodes over 6-8 weeks. The H200
nodes provide 80GB HBM3 memory, more than sufficient for VAE/MPNN training.
GNINA docking is CPU-bound; use day partition nodes.

### Person-Week Budget

| Phase | Person-Weeks | Notes |
|-------|-------------|-------|
| Pre-publication fixes | 0.5 | Mostly automated |
| Ablation suite | 1.5 | VAE training + evaluation |
| REINVENT 4 setup + run | 2.0 | Biggest setup overhead |
| Multi-kinase data curation | 2.0 | ChEMBL extraction, KLIFS structures |
| Multi-kinase training | 3.0 | Parallelizable across kinases |
| Evaluation + analysis | 2.0 | Enrichment, sensitivity, Pareto |
| Figures | 1.5 | 6-8 main + supplementary |
| Manuscript writing | 3.0 | Full paper |
| Revision + submission | 1.0 | Formatting, code release |
| **Total** | **~16.5** | |

This is tight but achievable for a single focused researcher over 12 weeks.
The critical path is multi-kinase training (weeks 3-5), which is parallelizable
on the HPC.

---

## 10. Specific Concerns and Recommendations

### 10.1 The Mean Score Problem

Both cohorts correctly identify that the static pipeline wins on mean composite
score (0.5437 vs 0.4378) while losing on enrichment metrics (EF@10 = 4.95 vs
0.47). This is not a bug -- it is a feature of the analysis. The paper should
embrace this tension:

"Static design produces candidates that score higher on aggregate metrics
dominated by structural similarity to known drugs. State-aware design produces
candidates that are more likely to be actual drugs, as measured by retrospective
enrichment for approved therapeutics. This divergence reveals a fundamental
tension in how the field evaluates generative molecular design: optimizing for
similarity to known drugs penalizes the novel scaffolds that generative models
are designed to produce."

This is a publishable insight in its own right. Do not try to "fix" the scoring
function to make state-aware win on mean score. Let the enrichment metrics speak.

### 10.2 Pre-Registration

Cohort1's proposal to pre-register analysis decisions (primary endpoint BEDROC,
secondary EF@10, kinase set, time-split, reference molecules, success criteria)
before running experiments is excellent. This should be formalized:

- Write the analysis plan before Week 3 (before multi-kinase results are available)
- Record it with a timestamp (git commit or OSF preregistration)
- Report all pre-specified analyses, including nulls
- Clearly distinguish pre-specified vs exploratory analyses in the paper

This is rare in computational drug discovery papers and will be noted favorably
by reviewers.

### 10.3 Asciminib (ABL1)

Both cohorts flagged that asciminib binds the myristate allosteric pocket (not
ATP site). It should be excluded from enrichment analysis or treated as a
pre-registered negative control. This is a detail, but getting it wrong would
undermine the entire ABL1 validation. Ponatinib (approved 2012) is in the
training set for pre-2015 splits and must also be handled correctly.

### 10.4 CrossDocked2020 Leakage

Cohort1 correctly identified that CrossDocked2020 likely contains EGFR structures.
If FLOWR or any 3D baseline trained on CrossDocked2020 is used, the training set
must be checked for EGFR structure overlap. This does not affect REINVENT 4
(trained on ChEMBL SMILES), which is another reason REINVENT 4 is the preferred
primary baseline.

---

## 11. Final Recommendations

### Do Now (This Week)

1. Fix osimertinib reference leakage
2. Verify 3W2R and 4ZAU structures
3. Compute bootstrap CIs on current results
4. Add BEDROC to current evaluation
5. Write pre-registration document (analysis plan)

### Do in Weeks 1-5 (Core Work)

6. Train unconditioned VAE and run Ablation C
7. Run ablation Experiments E, F, G
8. Set up and run REINVENT 4 on EGFR
9. Prepare multi-kinase data (ABL1, BRAF, MET)
10. Train and generate for all kinases

### Do in Weeks 5-8 (Evaluation)

11. Retrospective enrichment across all kinases
12. Scoring sensitivity analysis
13. 3-component scoring as fairness check
14. Conformational selection narrative

### Do in Weeks 8-12 (Paper)

15. Write manuscript targeting JCIM
16. Generate figures
17. Prepare code/data release
18. Submit

### Do NOT Do (Explicitly Cut)

- Scoring reform (changing reference similarity function)
- Kinetic scoring (tauRAMD or any 5th component)
- Pocket-aware scoring (DrugCLIP/ProFSA)
- Full benchmark infrastructure (Docker, leaderboard)
- Pocket representation ablation (ESM-2, ProstT5)
- C797S resistance docking as standalone component
- AF2-MSM multi-state modeling (high risk, AF2 DFGin bias)
- PKSmart PK predictions
- Experimental collaboration outreach (premature)

### Defer to Paper 2 / Follow-Up

- Benchmark paper (NeurIPS 2027 E&D)
- FLOWR baseline (add during review if requested)
- GIST water thermodynamics (add during review if requested)
- Within-method state ablations (Nature Comp Sci upgrade)
- Survival funnel (supplementary for Paper 1 or Paper 2)
- OpenFE FEP validation

---

## 12. The Bottom Line

StateBind has a genuinely novel question ("does conformational state-conditioning
improve molecular design?"), a strong headline result (10x enrichment), and a
viable path to publication at JCIM within 12 weeks. The competitive landscape
shows the novelty window is open but narrowing -- DynamicFlow, Apo2Mol, and
PLACER demonstrate growing interest in dynamics-aware molecular design, and
someone will ask StateBind's question within 12-18 months.

The biggest risks are: (1) Ablation C showing that diversity, not state
information, drives enrichment (medium probability, mitigatable by pivot to
"diverse generation" narrative), and (2) multi-kinase validation failing to
replicate (low-medium probability, mitigatable by honest reporting of mixed
results).

The most common mistake would be scope creep: trying to do scoring reform,
kinetic scoring, pocket-aware scoring, benchmark infrastructure, experimental
design, AND multi-kinase validation before submitting. This is 6-12 months of
work for a 1-2 person team. The minimum viable paper is achievable in 12 weeks.
Everything else is for Paper 2 or revisions.

**Ship the paper. Do not let the perfect be the enemy of the published.**

---

## References

1. Lu W, Zhang J, Huang W, et al. DynamicBind: predicting ligand-specific protein-ligand complex structure with a deep equivariant generative model. Nature Communications. 2024;15:1071.

2. DynamicFlow: Integrating Protein Dynamics into Structure-Based Drug Design via Full-Atom Stochastic Flows. ICLR 2025. arXiv:2503.03989.

3. Zheng X, et al. Apo2Mol: 3D Molecule Generation via Dynamic Pocket-Aware Diffusion Models. AAAI 2026. arXiv:2511.14559.

4. FLOWR: Flow Matching for Structure-Aware De Novo, Interaction- and Fragment-Based Ligand Generation. arXiv:2504.10564, 2025.

5. Anishchenko I, et al. Modeling protein-small molecule conformational ensembles with PLACER. PNAS. 2025;122(45):e2427161122.

6. Loeffler HH, et al. Reinvent 4: Modern AI-driven generative molecule design. J Cheminformatics. 2024;16:20.

7. Song Y, et al. A comprehensive exploration of the druggable conformational space of protein kinases using AI-predicted structures. PLOS Computational Biology. 2024;20(7):e1012302.

8. Nicholls A. The statistics of virtual screening and lead optimization. J Comput-Aided Mol Des. 2016;29:1205.

9. Truchon JF, Bayly CI. Evaluating virtual screening methods: good and bad metrics for the "early recognition" problem. JCIM. 2007;47:488-508.

10. Gao W, et al. Sample efficiency matters: a benchmark for practical molecular optimization. NeurIPS D&B. 2022.

11. Ung PMU, et al. Conformational analysis of the DFG-out kinase motif and biochemical profiling of structurally validated type II inhibitors. J Med Chem. 2015;58:5494-5502.

12. Wells CI, et al. The Kinase Chemogenomic Set (KCGS): An open science resource for kinase vulnerability identification in drug discovery. Int J Mol Sci. 2021;22:566.

13. Relay Therapeutics. Dynamo Platform. https://relaytx.com/dynamo-platform/. Accessed April 2026.

14. Insilico Medicine. ISM001-055 Phase IIa results in idiopathic pulmonary fibrosis. Nature Medicine. 2025.

15. NeurIPS 2026 Evaluations & Datasets Track Call for Papers. https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets. Accessed April 2026.

16. Nature Computational Science: Generative modeling for molecular design and discovery collection. https://www.nature.com/collections/cdaccfegbc. Accessed April 2026.

17. Fourth-generation EGFR-TKI to overcome C797S mutation: past, present, and future. J Enzyme Inhibition Med Chem. 2025;40(1):2481392.

18. Benchmarking 3D Structure-Based Molecule Generators. JCIM. 2025.

19. Benchmarking Cross-Docking Strategies in Kinase Drug Discovery. JCIM. 2025.

20. Praski A, Adamczyk J. Benchmarking pretrained molecular embeddings against ECFP baselines. 2025.

21. Li Y, et al. Conformalized GNN fusion for ADMET prediction. JCIM. 2024.

22. Copeland RA. The drug-target residence time model: a 10-year retrospective. Nature Reviews Drug Discovery. 2016;15:87-95.

23. Baillif B, et al. GenBench3D: Benchmarking 3D generation of molecules from protein pockets. 2024.

24. Nie Y, et al. Durian: A benchmark for structure-based drug design. JCIM. 2025.

25. BMCS 3rd Conformational Design in Drug Discovery Symposium 2026. https://www.rscbmcs.org/events/conformationaldesign26/.
