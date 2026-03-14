# Benchmark Specification

## Purpose

This document defines exactly what StateBind measures, how it measures it, and what constitutes a meaningful result. Every metric has a definition, a computation method, and a threshold for interpretability.

---

## Primary Task Definitions

### Task 1: State-Relevant Pocket Selection

**Question:** Given a mutation context, can we select the conformational state whose pocket is most relevant for molecular design?

**Operationalization:** For mutations with known structural preferences (from literature), does our state prediction rank the literature-supported state highest?

**Ground truth:** Literature-curated mutation→state associations (e.g., T790M → DFG-in favored, L858R → active state stabilized).

### Task 2: State-Conditioned Molecular Generation

**Question:** Does generating molecules against state-predicted pockets produce different (and computationally better-scoring) candidates than generating against a single static pocket?

**Operationalization:** Compare docking scores, chemical properties, and cross-state selectivity between state-aware and baseline candidate sets.

### Task 3: Cross-State Selectivity

**Question:** Do state-aware candidates show selectivity — scoring well against the intended state and worse against other states — more than baseline candidates do?

**Operationalization:** Compute per-candidate score variance across states. State-aware candidates should have higher cross-state variance (more selective) than baseline candidates.

---

## Baseline Definitions

| ID | Name | Description | What it controls for |
|----|------|-------------|---------------------|
| **B1** | Static single-structure | Generate + score against the highest-resolution wild-type EGFR structure (e.g., PDB 1M17 or 4HJO) | Whether state selection matters at all |
| **B2** | Random state | Generate + score against a randomly selected state's pocket | Whether informed state selection beats random state selection |
| **B3** | Random molecules (stretch) | Score random drug-like SMILES from ZINC against state pockets | Whether our generation method beats random sampling |

**B1 is the primary baseline.** The core claim of the project is tested by comparing state-aware results to B1.

B2 and B3 are secondary. B2 tests whether state *prediction* matters (vs. just using multiple structures). B3 is a sanity check.

---

## Metric Definitions

### Candidate Quality Metrics (per-molecule)

| Metric | Definition | Computation | Target |
|--------|-----------|-------------|--------|
| **Chemical validity** | Fraction of generated SMILES that parse as valid molecules | RDKit `Chem.MolFromSmiles()` success rate | >90% |
| **Uniqueness** | Fraction of unique canonical SMILES in candidate set | Deduplicate canonical SMILES | >80% |
| **Drug-likeness (Lipinski)** | Fraction passing Lipinski rule of 5 | MW<500, logP<5, HBD≤5, HBA≤10 | >70% |
| **QED** | Quantitative Estimate of Drug-likeness | RDKit `QED.qed()` | Mean >0.4 |
| **Synthetic accessibility** | SA score (1=easy, 10=hard) | RDKit `sascorer` | Mean <5 |

### Generation Diversity Metrics (per-set)

| Metric | Definition | Computation | Target |
|--------|-----------|-------------|--------|
| **Tanimoto diversity** | Mean pairwise Tanimoto distance (1 - similarity) | ECFP4 fingerprints, all-pairs mean | >0.5 |
| **Scaffold diversity** | Number of unique Murcko scaffolds / total molecules | RDKit `MurckoScaffold` | >0.3 |
| **Internal diversity** | 1 - mean max-similarity-to-rest | ECFP4 nearest-neighbor | >0.4 |

### Docking / Scoring Metrics (per-molecule-per-pocket)

| Metric | Definition | Computation | Notes |
|--------|-----------|-------------|-------|
| **Docking score** | Predicted binding affinity (kcal/mol) | AutoDock Vina or smina | Lower (more negative) = better |
| **Best pose RMSD** | RMSD of best-scoring pose to pocket center | From docking output | Sanity check; very high RMSD suggests bad docking |

### Ranking Metrics (comparing state-aware vs. baseline)

| Metric | Definition | Computation | What a "win" looks like |
|--------|-----------|-------------|------------------------|
| **Mean top-10 score** | Mean docking score of the 10 best-scoring candidates | Sort by score, take mean of top 10 | State-aware top-10 mean < baseline top-10 mean |
| **Mean top-50 score** | Mean docking score of the 50 best-scoring candidates | Sort by score, take mean of top 50 | State-aware < baseline |
| **Hit rate at threshold** | Fraction of candidates below a docking score threshold (e.g., -8.0 kcal/mol) | Count below threshold / total | State-aware hit rate > baseline hit rate |
| **Score distribution shift** | Shift in score distribution between state-aware and baseline | Mann-Whitney U test, report U statistic + p-value + effect size (rank-biserial correlation) | p < 0.05 with meaningful effect size (r > 0.2) |

### State Relevance Metrics

| Metric | Definition | Computation | Target |
|--------|-----------|-------------|--------|
| **Top-1 accuracy** | Fraction of mutations where predicted top state matches literature | Compare to curated ground truth | >60% on curated mutations |
| **Coverage** | Fraction of atlas mutations with non-uniform predictions | Count non-uniform / total | >50% |
| **Calibration (stretch)** | Does predicted state probability correlate with PDB state frequency? | Spearman correlation of predicted prob vs. observed frequency | ρ > 0.3 |

### Cross-State Selectivity Metrics

| Metric | Definition | Computation | What a "win" looks like |
|--------|-----------|-------------|------------------------|
| **Score variance** | Per-candidate variance of docking scores across all states | `var(scores across states)` for each candidate | State-aware candidates have higher mean variance than baseline (they are more state-selective) |
| **Selectivity index** | `(worst_state_score - best_state_score) / |best_state_score|` | Per candidate | State-aware selectivity > baseline selectivity |
| **Intended-state rank** | For state-aware candidates: does the intended state give the best score? | Rank states by score per candidate, check if intended state is rank 1 | Intended state is top-ranked for >50% of state-aware candidates |

---

## What Constitutes a "Win"

### Primary win condition

State-aware top-10 mean docking score is significantly better (lower) than baseline top-10 mean docking score, with p < 0.05 (Mann-Whitney U) and effect size r > 0.2.

### Secondary win conditions (any of these strengthen the claim)

- State-aware candidates show higher cross-state selectivity than baseline candidates
- State-aware hit rate at threshold exceeds baseline hit rate by ≥10 percentage points
- State-aware candidates score best on their intended state >50% of the time

### Acceptable null result

If state-aware design does NOT beat static design on any metric, this is still a valid and reportable result, provided:
- Both pipelines ran correctly and produced valid candidates
- The comparison was properly controlled (same generation method, same scoring, same number of candidates)
- The null result is reported honestly with effect sizes (not just "p > 0.05")

A well-characterized null result ("state-awareness does not improve docking scores for EGFR, possibly because [reason]") is scientifically more valuable than a poorly characterized positive result.

### What is NOT a win

- State-aware scores are "better" but the comparison is confounded (different generation methods, different candidate counts)
- Marginal improvement with no statistical test
- Cherry-picked mutations where state-awareness helps while ignoring mutations where it doesn't
- Claiming biological activity based on docking scores

---

## Reporting Requirements

The final benchmark report must include:

1. **Table:** Per-mutation results (state-aware vs. baseline scores) for at least T790M, L858R, C797S
2. **Figure 1:** Score distribution comparison (violin or box plot, state-aware vs. baseline)
3. **Figure 2:** Cross-state selectivity comparison
4. **Table:** Summary statistics with effect sizes and p-values
5. **Limitations section** acknowledging: docking score limitations, small sample of mutations, no experimental validation
