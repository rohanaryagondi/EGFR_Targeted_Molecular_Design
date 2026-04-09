---
agent: Orchestrator
round: 1
date: 2026-04-08
type: roundtable
---

# Round 1 Synthesis: Cross-Domain Research Findings

## Executive Summary

Seven domain specialists conducted deep internet research (4,928 lines, 198 citations
total). The research reveals that StateBind occupies a genuinely novel niche -- no
published paper conditions molecular generation on discrete conformational state labels --
but the current evidence is statistically fragile and the comparison is confounded. The
path to publication requires 4 parallel workstreams: (1) multi-kinase validation for
statistical power, (2) ablation to isolate state-conditioning from diversity, (3) external
baselines for reviewer credibility, and (4) scoring function revision to reflect real
drug design practice.

A critical data leakage issue was identified: osimertinib (approved 2015) is used as a
reference molecule in the pre-2015 retrospective validation, contaminating the scoring
function with future information. This must be corrected immediately.

---

## Theme 1: Novelty Is Confirmed -- StateBind Owns This Niche

**Consensus: mlres, genai (corroborated by all)**

No published paper explicitly conditions molecular generation on discrete protein
conformational state labels. genai surveyed the entire 3D generation landscape (DiffSBDD,
TargetDiff, MolCRAFT, FLOWR, Pocket2Mol, DecompDiff) and found that while pocket-
conditioned generation exists, NONE condition on multiple conformational states of the
SAME protein. The closest work (Apo2Mol) handles apo-to-holo transitions, not multi-state
conditioning.

**Implication:** The publication contribution is the QUESTION ("does conformational
state-awareness improve molecular design?"), not the MODEL (a VAE). This supports a
framework/benchmark paper framing rather than a methods paper.

---

## Theme 2: The 10x Enrichment Is Statistically Fragile

**Primary source: datasci; corroborated by mlres**

The headline result (EF@10 = 4.95 for pre-2010, 7.72 for pre-2015 vs static 0.47/0.79)
is based on N=3-5 held-out drugs. datasci demonstrates:

- **95% CI with N=5 spans roughly 0.5x to 8.7x** -- the lower bound includes 1.0
- **N >= 15 held-out drugs needed** for publishable precision (CI width ~[2.5, 7.4])
- **BEDROC(alpha=20)** should replace EF@10 as the primary metric (better statistical
  properties for small sample sizes)
- **Enrichment CI width estimates by sample size:**

| N (held-out drugs) | Approx 95% CI Width | Interpretation |
|---------------------|---------------------|----------------|
| 5 (current EGFR) | [0.5, 9.4] | Marginal significance |
| 15 (3 kinases) | [2.5, 7.4] | Moderate precision |
| 21 (6 kinases) | [3.0, 6.9] | Publishable |

**Critical finding:** Multi-kinase expansion is not a nice-to-have; it is a statistical
requirement for publication.

---

## Theme 3: The Comparison Is Confounded

**Primary source: datasci; corroborated by mlres, medchem**

The state-aware vs static comparison conflates at least 4 factors:

1. **State awareness** (the thesis): 4 states vs 1 state
2. **Generation method**: VAE vs templates only
3. **Candidate count**: 461 vs 30
4. **Chemical diversity**: 0.9056 vs 0.5684

datasci proposes a 6-experiment ablation matrix to isolate each factor:

| Experiment | State? | Generator | N candidates | Isolates |
|-----------|--------|-----------|-------------|----------|
| Static baseline | No | Template | 30 | Current |
| State-aware full | Yes | VAE+Tmpl | 461 | Current |
| Ablation A | No | VAE | ~400 | State effect |
| Ablation B | Yes | Template | ~36 | VAE effect |
| Ablation C | Yes | VAE | 30 (subsample) | Count effect |
| Random baseline | No | Random | 461 | Lower bound |

**Risk noted:** The unconditioned VAE ablation (Experiment A) might show diversity alone
drives enrichment, not state-conditioning. If EF@10 drops from 4.95 to 3.5 (not to
0.47), the contribution is real but modest. datasci argues this must be reported honestly
and that pre-registration makes ANY outcome publishable.

---

## Theme 4: Data Leakage Identified

**Primary source: datasci**

Osimertinib (approved November 2015) is used as one of 3 reference molecules in the
scoring function (35% weight via Tanimoto similarity). In the pre-2015 retrospective
validation, this means the scoring function contains information about a drug from the
held-out set. This is a form of temporal data leakage.

**Required fix:** Re-run pre-2015 validation with osimertinib removed from reference
molecules (use only erlotinib + gefitinib). The pre-2010 validation is clean (osimertinib
not yet approved).

---

## Theme 5: Structural Data Issues

**Primary source: structbio**

structbio flagged two potential discrepancies in StateBind's structural data:

1. **3W2R** is a T790M/L858R double mutant (not wild-type as implied). Using a mutant
   structure to represent a wild-type conformational state conflates mutational and
   conformational effects. Reviewers will notice.

2. **4ZAU** may contain osimertinib rather than EAI045 (allosteric inhibitor). The
   conformational state assignment (DFGout/aCout) needs verification against KLIFS and
   KinCore.

Additional structural concerns:
- **Modi/Dunbrack classification has 8 primary states**, not 4. StateBind's model captures
  major basins but misses intermediates. Publication must include explicit mapping to
  published classification systems.
- **Erlotinib is NOT conformationally selective** (Park et al., 2012) -- it binds both
  active and inactive EGFR. This complicates using erlotinib as a reference molecule
  for state-specific design.
- **1 structure per state ignores massive within-state diversity.** KinCore has 107 EGFR
  chains in active state and 79 in Src-like inactive.

---

## Theme 6: The Conformational State-Selectivity Connection

**Primary source: medchem, structbio (strong agreement)**

Both independently found that **type II (DFG-out) inhibitors are significantly more
selective than type I** across kinase panels:

- medchem: Gini selectivity 0.76 vs 0.58 (p < 10^-4)
- structbio: Gini 0.64-0.80 vs 0.49-0.74 for type II vs type I

This is StateBind's strongest unexploited argument: state-aware design that targets
DFG-out conformations inherently favors more selective molecules. The DFG-out pocket is
less conserved across kinases, providing a structural basis for selectivity.

**Publication opportunity:** "Conformational state-aware design inherently selects for
kinase selectivity" -- a claim supported by decades of structural biology literature.

structbio also identified **type V bivalent inhibitors** as the ultimate biological
validation of state-aware design: these molecules literally require knowledge of
conformational states.

---

## Theme 7: Scoring Function Needs Fundamental Revision

**Primary sources: medchem, synthbio; corroborated by compchem, datasci**

Current scoring: reference similarity (0.35), drug-likeness (0.30), docking (0.20),
state specificity (0.15).

Key problems identified:

1. **Reference similarity (35%)** -- Largest single component, uses Tanimoto to only 3
   drugs (erlotinib, gefitinib, osimertinib). Rewards me-too compounds, penalizes novelty.
   Primary driver of static's mean-score advantage. medchem found BSI (Bioactivity
   Similarity Index) achieves 12x improvement over Tanimoto in mean active rank.

2. **Drug-likeness (30%)** -- QED penalizes kinase inhibitors. Osimertinib scores 0.31
   QED. 48% of approved kinase inhibitors violate Rule of 5 (Roskoski 2026). The metric
   actively penalizes the drug class being designed.

3. **ADMET absent from scoring** -- Despite a trained model being available. synthbio
   found ADMET-in-the-loop is now standard practice (REINVENT 4, ADMETrix, Chemistry42).

4. **No selectivity component** -- Zero weight, despite selectivity being the #1 clinical
   concern for kinase inhibitors.

medchem proposes revised weights: reference similarity 0.10, drug-likeness 0.15,
docking 0.20, state specificity 0.20, ADMET 0.20, selectivity 0.15.

**Tension:** datasci cautions that changing the scoring function to make state-aware win
is scientifically questionable. The solution is to report results under BOTH scoring
regimes and test robustness across weight configurations.

---

## Theme 8: External Baselines Are Non-Negotiable

**Primary sources: mlres, genai**

Reviewers at any credible venue will demand comparison against existing generative methods.

**Must-have baselines:**
1. **REINVENT 4** (Apache 2.0, 720 GitHub stars, v4.7) -- The most widely used molecular
   optimization tool. Can be configured with GNINA docking oracle per state. Setup: 1-2
   weeks.
2. **MolCRAFT or DiffSBDD** (pre-trained checkpoints available) -- Zero-shot 3D generation
   on EGFR pockets. Tests whether pocket-conditioned 3D methods outperform 1D state-
   conditioned methods. Setup: days.

**Surprising finding from genai:** 3D methods do NOT universally beat 1D/2D methods. A
June 2024 benchmark showed AutoGrow4 (a 2D genetic algorithm) achieves competitive docking
scores against 3D methods. The case for 3D rests on structural conditioning, not raw score.

**SOTA has shifted from diffusion to flow matching:** MolCRAFT, FLOWR, PropMolFlow,
MolFORM are the new leaders, offering 10-70x sampling speedups. Vision idea 002
(DiffSBDD/TargetDiff) is outdated as of 2025-2026.

---

## Theme 9: Physics-Based Validation Opportunities

**Primary source: compchem**

compchem identified a tiered approach to adding physics-based rigor:

| Method | Cost | Impact | Timeline |
|--------|------|--------|----------|
| GIST water thermodynamics (4 states) | 2 GPU-days | Shows states have different water networks | Tier 1 |
| Ensemble docking (5 KLIFS structures/state) | 3 GPU-days | 3-24% enrichment improvement | Tier 1 |
| OpenFE RBFE on top 30 candidates | 800-1400 GPU-hours | Rigorous computational validation | Tier 2 |
| SQM2.20 rescoring of top 50 | 3 CPU-days | DFT-quality scoring (R²=0.69) | Tier 2 |
| Enhanced sampling MD (4 states) | 2-4 weeks | Pocket ensembles, transition paths | Tier 3 |

**GIST water analysis** is the highest-value per-compute-cost experiment: it directly
shows the 4 conformational states present physically different water networks in the
binding pocket, validating the fundamental thesis that states are meaningfully different
for drug design.

---

## Theme 10: End-to-End Pipeline Differentiation

**Primary source: synthbio**

Most AI drug design papers stop at generation + scoring. Going end-to-end differentiates:

1. **RAscore** (4500x faster than AiZynthFinder) as scoring proxy for synthesis feasibility
2. **AiZynthFinder 4.0** (71% route-finding rate) for full retrosynthetic validation of top
   candidates
3. **ADMETlab 3.0** (free API, 119 endpoints) for comprehensive ADMET profiling with no
   training required
4. **PKSmart** for directional PK projections (accuracy limited but useful for ranking)

Key finding: **AI-generated 3D molecules have only 3-22% true synthesis feasibility**
(round-trip verified). If StateBind's 1D SELFIES VAE shows higher synthesis feasibility,
this is a strong publication point.

synthbio proposes integration timeline: Week 1 ADMETlab API, Weeks 2-3 RAscore +
AiZynthFinder, Weeks 3-5 kinase-calibrated thresholds, Weeks 4-6 PKSmart projections.

---

## Theme 11: Venue Strategy

**Primary source: mlres; corroborated by all**

| Venue | Framing | Requirements | Feasibility |
|-------|---------|-------------|-------------|
| **JCIM** (primary) | Framework/benchmark | External baselines, ablations, multi-kinase | High |
| **Nature Comp Sci** (aspirational) | Multi-kinase validation + biological insight | 4+ kinases, physics validation, narrative | Medium |
| **NeurIPS** | Not viable | Would need architectural novelty | Low |
| **Bioinformatics** | Methods/tool | Reproducibility, benchmark release | Backup |

mlres proposes: **"Does Conformational State-Awareness Improve Molecular Design? A Multi-
Kinase Benchmark"** targeting JCIM primary, Nature Comp Sci aspirational.

The mean-score loss (static wins 0.5437 vs 0.4378) should be reframed as a publishable
insight: conventional known-drug-similarity scoring systematically undervalues novel
exploration -- exactly the problem state-aware design addresses.

---

## Convergence Map: Where Agents Agree

| Finding | Agents Agreeing | Strength |
|---------|----------------|----------|
| Multi-kinase validation is #1 priority | All 7 | Universal |
| Novelty confirmed (no prior multi-state conditioning) | mlres, genai | Strong |
| Ablation suite required | datasci, mlres | Strong |
| External baselines required (esp. REINVENT 4) | mlres, genai | Strong |
| State-selectivity connection is underexploited | medchem, structbio | Strong |
| Scoring function needs revision | medchem, synthbio, compchem | Strong |
| ADMET should enter scoring | medchem, synthbio | Strong |
| Reference similarity weight too high | medchem, datasci, mlres | Strong |
| hERG threshold needs kinase calibration | medchem, synthbio | Strong |
| JCIM is the right primary venue | mlres (others defer) | Moderate |

## Divergence Map: Where Agents Disagree

| Tension | Agents | Resolution |
|---------|--------|-----------|
| Revise scoring to fix mean-score gap vs maintain fair comparison | medchem vs datasci | Report under BOTH regimes |
| 3D generation upgrade vs 1D framework paper | genai vs mlres | Include 3D as baseline, not replacement |
| FEP/MD validation priority vs statistical/baseline priority | compchem vs datasci | Parallel workstreams, statistics first |
| Scope of end-to-end additions | synthbio (comprehensive) vs mlres (focused) | Tier based on timeline |

---

## Critical Action Items (Pre-Publication Blockers)

1. **Fix osimertinib reference leakage** -- Re-run pre-2015 validation without osimertinib
   as reference molecule (IMMEDIATE)
2. **Verify 3W2R and 4ZAU** -- Check conformational state assignments against KLIFS/KinCore,
   find WT alternatives if needed (IMMEDIATE)
3. **Run ablation suite** -- Especially unconditioned VAE (DAYS, decisive for thesis)
4. **Compute bootstrap CIs** -- BCa with 10,000 resamples on all enrichment metrics (DAYS)
5. **Run REINVENT 4 baseline** -- Minimum viable external comparison (1-2 WEEKS)
6. **Multi-kinase expansion** -- At minimum ABL + one more (2-4 WEEKS)

---

## Proposed Research Agenda (Preliminary Ranking)

| Priority | Direction | Owner(s) | Impact | Effort |
|----------|-----------|----------|--------|--------|
| P0 | Multi-kinase validation + statistical rigor | datasci + structbio | Transformative | 4-6 weeks |
| P0 | Ablation suite (isolate state-conditioning) | datasci + mlres | Decisive | 1-2 weeks |
| P0 | External baselines (REINVENT 4 + MolCRAFT) | mlres + genai | Required | 2-3 weeks |
| P1 | Scoring revision (ADMET + selectivity) | medchem + synthbio | Major | 2-3 weeks |
| P1 | GIST water + ensemble docking | compchem + structbio | High per cost | 1 week |
| P2 | End-to-end pipeline (retrosynthesis + PK) | synthbio | Differentiating | 3-5 weeks |
| P2 | FEP validation on top candidates | compchem | Rigorous | 2-3 weeks |
| P3 | 3D generation comparison (flow matching) | genai | Forward-looking | 1-2 months |
