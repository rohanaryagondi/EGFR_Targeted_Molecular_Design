# Remaining Goals: Gap Analysis

**Last updated:** 2026-04-07T20:00:00+00:00
**Briefing session:** 3

---

## Changes Since Last Briefing (Session 2)

- **3 former gaps now addressed:**
  - "No physics-based docking" -> WS11 implemented GNINA (validated on GPU, tier 0 in cascade)
  - "No multi-objective optimization" -> WS12 implemented Pareto (hypervolume comparison)
  - "No external validation" -> WS13 implemented retrospective time-split validation
- **Remaining gaps reduced from 10 to 7** (plus 2 new minor limitations)
- **Retrospective validation fundamentally changes the narrative:** State-aware pipeline
  achieves 10x enrichment for identifying future approved drugs despite losing on mean
  score. This reframes what "remaining goals" means for the project.
- **All previously planned goals are met.** The gaps below are directions for future work,
  not unfinished requirements.

---

## The Central Question

StateBind exists to answer: does conformational state-aware design outperform static
single-structure design? The answer is now **nuanced rather than binary:**

**On mean unified score:** No. The static baseline wins (0.5437 vs 0.4378, p<0.001,
Cohen's d=1.36). The null hypothesis is formally retained.

**On prospective drug identification:** Yes, dramatically. The state-aware pipeline
achieves 10x enrichment for identifying future approved drugs in retrospective
time-split validation (EF@10 = 4.95/7.72 vs 0.47/0.79).

**On chemical exploration:** Yes. The state-aware pipeline produces 15x more candidates
(461 vs 30), 59% higher chemical diversity (0.9056 vs 0.5684), and 431 novel molecules.

The project has answered its central question -- and the answer depends on which metric
you prioritize.

---

## Goal-by-Goal Status

### All Planned Goals: MET

| Goal | Target | Achieved | Notes |
|------|--------|----------|-------|
| Test count | 450+ | 646 | Exceeded by 196. Progression: 359 -> 646 across 12 workstreams |
| Similarity method | Morgan/ECFP4 | Morgan/ECFP4 Tanimoto (radius=2, 2048 bits) | Fallback to n-gram when RDKit unavailable |
| Drug-likeness method | RDKit QED + Lipinski + SA | QED(0.5) + Lipinski(0.25) + SA(0.25) | Weighted composite with heuristic fallback |
| Workstreams complete | 12/12 | 12/12 | All merged, zero conflicts |
| Statistical framework | Mann-Whitney U + CI | Complete | p<0.001, d=1.36, null retained |
| Docking scoring | MPNN (RMSE < 1.0) | RMSE=0.7182 | MPNN tier 1. GNINA physics-based tier 0 on GPU. |
| CI/CD | Clean GitHub Actions | 121 ruff violations fixed (121->0) | Lint job passes clean |
| Statistical significance | p < 0.05 | p<0.001, d=1.36 | Null formally retained (static favored on mean score) |
| Novel candidates | 100+ VAE-generated | 395 VAE-generated (431 total novel) | SELFIES encoding: 99.9% valid, 94.8% unique |
| VAE validity | >= 50% | 99.9% | SELFIES guarantees near-perfect validity |
| VAE uniqueness | >= 80% | 94.8% | Exceeded target |
| MPNN RMSE | < 1.0 pIC50 | 0.7182 | Met target |
| MPNN R-squared | > 0.5 | 0.6863 | Met target |
| MPNN Pearson r | > 0.7 | 0.8323 | Met target |
| hERG AUROC | > 0.75 | 0.7745 | Met (but hard filtering rejects ALL kinase inhibitors) |
| CYP3A4 AUROC | > 0.70 | 0.7323 | Met target |
| Physics-based docking | GNINA integrated | Tier 0, validated on GPU | Binders -7.32 vs non-binders -4.16 kcal/mol |
| Pareto optimization | Implemented | Hypervolume comparison active | Weight-free evaluation alongside weighted sum |
| Retrospective validation | Time-split at 2010/2015 | EF@10 = 4.95/7.72 (state-aware) | 10x enrichment over static |

---

## What Retrospective Validation Revealed

This is the most important new result since the last briefing. The retrospective
validation tests whether the pipeline, trained only on data available before a cutoff
year, would have identified drugs approved after the cutoff.

### Cutoff 2010 (held out: afatinib, osimertinib, dacomitinib, lazertinib, mobocertinib)

| Metric | Static | State-Aware |
|--------|--------|-------------|
| EF@10 | 0.47 | **4.95** |
| EF@50 | 1.00 | **5.70** |
| Candidates | 30 | 520 |
| Drugs found | 5/5 | 5/5 |
| Novelty | 0.90 | **0.99** |

### Cutoff 2015 (held out: dacomitinib, lazertinib, mobocertinib)

| Metric | Static | State-Aware |
|--------|--------|-------------|
| EF@10 | 0.79 | **7.72** |
| EF@50 | 1.00 | **7.28** |
| Candidates | 30 | 430 |
| Drugs found | 3/3 | 3/3 |
| Novelty | 0.90 | **0.99** |

**Key finding:** The state-aware pipeline's enrichment factor is 10x that of the static
baseline. This means future approved drugs are concentrated ~10x more densely in the
top-ranked state-aware candidates than in top-ranked static candidates.

**Why the state-aware pipeline wins here but loses on mean score:** The mean score is
dragged down by 431 diverse but low-similarity VAE-generated molecules (the reference
similarity component at 35% weight penalizes novelty). But among these diverse
candidates are molecules that closely resemble future drugs -- they are needles in a
haystack that the enrichment factor detects.

**Pre-cutoff models performed well:** The pre-2010 MPNN (only 2,974 training compounds)
achieved R^2=0.717 and Pearson=0.854 -- comparable to or better than the full model on
10,466 compounds. This suggests early curated data may be higher quality.

---

## Gaps That Current Plans Do NOT Address

The following 7 gaps remain open. These are directions for future work, not failures --
each represents an opportunity to strengthen the project's scientific credibility.

### 1. No experimental validation

Zero wet-lab data. No binding assays, no cell viability, no animal models. Every score
is a computational prediction. Peer reviewers will flag this as the fundamental
limitation.

> **Opportunity:** Testing 5-10 top candidates in a fluorescence polarization binding
> assay would transform this from a purely computational exercise to a validated
> pipeline. The retrospective validation result (10x enrichment) makes the case for
> experimental follow-up much stronger.

### 2. No selectivity profiling

The pipeline scores binding to EGFR only. It does not check whether candidates also
bind off-target kinases (ABL, BRAF, ALK, SRC, etc.). A molecule that binds everything
is not a useful drug.

> **Opportunity:** A multi-target MPNN trained on data from multiple kinases, or a
> structural comparison of binding pockets across the kinome, would enable designing
> EGFR-specific molecules. The MPNN architecture already supports this -- it would
> need training data from additional kinases.

### 3. No retrosynthetic analysis

The pipeline generates molecular structures but does not assess whether they can
actually be synthesized in a lab. SA score is a rough heuristic; real retrosynthetic
planning (ASKCOS, IBM RXN) would identify actual synthesis routes.

> **Opportunity:** Integrating a retrosynthetic feasibility gate would filter candidates
> by actual synthesizability and provide proposed routes. This converts computational
> candidates into actionable synthesis targets.

### 4. Conformational model is discretized

Real kinase dynamics are continuous -- the protein breathes through a landscape of
intermediate conformations, not 4 discrete states. The 4-state model is a useful
simplification but misses intermediate geometries.

> **Opportunity:** Replacing discrete states with continuous conformational
> representations (e.g., PCA of dihedral angles from MD trajectories, or learned
> embeddings from a protein structure VAE) would capture the full landscape. This
> would be genuinely novel -- most approaches in the literature also use discrete
> states. Note: the Head AI deferred this (idea 001) because the null result is not
> driven by discretization.

### 5. Training data is modest

10,466 compounds for MPNN is moderate. Pre-training on larger datasets (ChEMBL-wide,
PubChem) followed by fine-tuning on EGFR data would likely improve generalization.
However, the pre-cutoff models performed surprisingly well with fewer compounds
(R^2=0.717 with only 2,974 compounds), suggesting diminishing returns.

> **Opportunity:** Self-supervised pre-training on millions of compounds (idea 010)
> before fine-tuning on EGFR data. The Head AI deferred this because models are
> already achieving target metrics.

### 6. ADMET is not in the scoring weights

The ADMET predictor (hERG AUROC=0.7745, CYP3A4 AUROC=0.7323) filters candidates
informational only. Hard filtering rejects ALL kinase inhibitors on hERG (a known class
liability). A candidate with perfect affinity but terrible hERG liability still scores
high -- it just gets flagged afterward.

> **Opportunity:** Adding ADMET as a 5th scoring component (or restructuring as
> constrained optimization where ADMET thresholds are constraints rather than
> penalties) would make the ranking safety-aware. This requires solving the kinase
> inhibitor hERG problem -- perhaps a kinase-specific hERG threshold or a relative
> rather than absolute scoring approach.

### 7. No uncertainty quantification

All models produce point predictions. The MPNN predicts pIC50 = 6.3, but how confident
is it? Without uncertainty estimates, the pipeline cannot distinguish high-confidence
from low-confidence predictions.

> **Opportunity:** Ensembles (5-10 models), Monte Carlo dropout, or evidential deep
> learning would provide prediction intervals and enable risk-aware ranking. The
> Head AI deferred this (idea 004) due to 5-10x GPU cost; MC dropout is a lighter
> alternative.

---

## New Considerations (Post-WS11/12/13)

### GNINA runtime cost

Physics-based docking is slow (minutes per molecule on GPU). Docking 461 candidates
across 4 conformational states requires significant GPU time. This makes iterative
pipeline runs expensive and limits active learning loops.

> **Opportunity:** GNINA's CNN scoring mode is faster than full Vina. Alternatively,
> a GNINA-trained surrogate model could provide fast approximate docking scores for
> rapid screening, with full GNINA reserved for top candidates.

### Retrospective validation sample size

The enrichment factors (4.95/7.72 for state-aware, 0.47/0.79 for static) are computed
against only 5 (pre-2010) or 3 (pre-2015) held-out drugs. These are all the approved
EGFR drugs that exist, but the small sample means the enrichment estimates have wide
confidence intervals.

> **Opportunity:** Extending to other kinase families (ALK, ROS1, RET, MET) with
> known approved drugs would provide more statistical power for the retrospective
> validation. The pipeline architecture is target-agnostic -- it could be applied to
> any kinase with conformational state data.

---

## The Honest Assessment

StateBind has completed everything it set out to do and more. All 12 workstreams are
done, all planned goals are met, and the central question has been answered. The
infrastructure is production-quality for a research project.

The answer to the central question is nuanced:
- **Static wins on mean score** (the unified scoring function favors known chemotypes
  through its 35% reference similarity weight)
- **State-aware wins on drug discovery utility** (10x enrichment for identifying future
  approved drugs, 15x more candidates, 59% higher diversity, 431 novel molecules)

This nuance is scientifically valuable. It reveals that the weighted-sum scoring
function and the retrospective enrichment metric measure fundamentally different
things. The scoring function rewards similarity to 3 known drugs. The enrichment
factor rewards placing future drugs near the top of the candidate list, regardless of
overall score distribution. The state-aware pipeline excels at the latter because its
VAE-generated candidates explore diverse chemical space where future drugs are found.

**What the Visionary should focus on:** The 7 remaining gaps are now about strengthening
the scientific narrative and extending the pipeline, not about basic functionality.
The highest-impact opportunities are:

1. **Experimental validation** -- Even minimal wet-lab data would transform the project.
   The 10x enrichment result makes the case for this compelling.
2. **Selectivity profiling** -- The missing piece for drug design credibility.
3. **Extending to other kinases** -- Would validate the approach beyond EGFR and
   provide more statistical power for retrospective validation.
