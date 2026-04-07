# Evaluation Framework: Static Baseline vs State-Aware Pipeline

## Overview

This document defines the primary comparison framework used to evaluate
whether **state-aware molecular design outperforms a static single-structure
baseline** for EGFR-targeted drug discovery.

The evaluation is designed to be:
- **Fair**: Both pipelines scored with the same function
- **Reproducible**: Deterministic candidate generation, fixed random seeds
- **Honest**: Limitations stated upfront, not buried in appendices

---

## Primary Comparison Framework

### Two Pipelines Under Test

| Pipeline | Structure(s) | Pocket(s) | Generation Strategies |
|----------|-------------|-----------|----------------------|
| Static baseline | 1M17 (active, WT) | Single ATP site | Halogen/methyl swaps only |
| State-aware | 1M17, 2GS7, 3IKU, 4ZAU | 4 state-specific pockets | Hinge opt., back pocket ext., gatekeeper avoidance, volume filling, covalent warhead, P-loop interaction, analogs |

### Unified Scoring Function

Both pipelines are scored with **exactly the same function**:

```
composite = 0.35 × reference_similarity
          + 0.30 × druglikeness
          + 0.20 × docking_proxy      ← 3-tier cascade: MPNN → DockingProxy MLP → stub
          + 0.15 × state_specificity   ← 0 for static baseline
```

**Why these weights?** Reference similarity and druglikeness are the most
informative available axes. The docking proxy carries real signal via a trained
MPNN (RMSE=0.72, R²=0.69). State specificity is included because pocket-specificity is a genuine
design desideratum, but weighted modestly to avoid inflating the advantage.

### Fairness Considerations

1. **state_specificity is structurally zero for the baseline.** This is by
   design: the baseline has no state information, so it cannot earn specificity
   credit. However, this means the comparison has a built-in 0.15 × max_specificity
   advantage for state-aware candidates. All interpretations account for this.

2. **The MPNN scoring cascade is identical for both pipelines.** Both pipelines
   use the same 3-tier cascade (MPNN → DockingProxy MLP → constant 0.5 stub).
   The MPNN provides real discriminative signal (trained on 10,466 EGFR compounds),
   so docking now influences ranking — but identically for both pipelines.

3. **Candidate deduplication**: When merging, if the same SMILES appears in
   both pipelines, the higher-scoring version is kept.

---

## Metrics

### 1. Candidate Pool Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| N candidates | Unique SMILES after filtering | Raw throughput |
| Diversity | 1 − mean pairwise SMILES 3-gram Tanimoto | Chemical space coverage |
| Validity rate | Fraction with parseable SMILES | Sanity check |
| Uniqueness | Unique / total | Deduplication quality |

### 2. Scoring Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| Mean composite score | Mean over all candidates | Central tendency |
| Max composite score | Best single candidate | Upper bound of quality |
| Score std | Standard deviation | Score spread |
| Per-component means | Mean of each scoring axis | Where does the advantage come from? |

### 3. Ranking Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| Global top-K composition | Count per pipeline in top K | Who dominates the best candidates? |
| Mean global rank | Average rank in merged pool | Overall placement |
| Rank shift | pipeline_rank − global_rank | Promoted or demoted by comparison |

### 4. Novelty Metrics

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| SMILES overlap | Jaccard index between pipeline sets | How different are the sets? |
| State-aware only | Candidates not in static baseline | Genuinely new chemistry |
| Static only | Candidates not in state-aware set | Coverage gaps |
| Novel by strategy | Which strategies produce novelty | Source attribution |

---

## Interpretation Rules

### When to claim "state-aware outperforms"

All of the following must hold:
1. State-aware has higher mean composite score (even after removing
   the state_specificity component)
2. State-aware candidates appear in at least 50% of the global top-K
3. Novelty count > 0 (state-aware produces genuinely new candidates)
4. Diversity delta is positive

### When to claim "state-aware is comparable"

- Mean scores are within 1 standard deviation
- Both pipelines have top-K representation
- Novelty exists but is modest

### When to claim "static baseline is sufficient"

- Static baseline matches or exceeds state-aware on all non-specificity
  scoring axes
- Static candidates dominate the global top-K
- Diversity delta is negligible

---

## Common Pitfalls

1. **Docking is an MPNN proxy, not physics-based**: The MPNN cascade provides
   real discriminative signal (RMSE=0.72 pIC50) but is not a substitute for
   physics-based docking. Claims about binding mode or pose are not supported.

2. **Conflating SMILES novelty with chemical novelty**: New SMILES ≠
   new pharmacophore. Some "novel" candidates may be trivially close
   to existing ones in 3D space.

3. **Over-interpreting state_specificity**: This component gives state-aware
   candidates an inherent advantage. Always report results both with and
   without this component.

4. **Cherry-picking top candidates**: Report aggregate metrics (mean, median),
   not just the best individual.

5. **Ignoring overlap**: If most candidates are shared between pipelines,
   the practical difference is small regardless of the top-K composition.

---

## Non-Claims / Limitations

This evaluation framework **does NOT** support claims about:

1. **Binding affinity**: No docking or free energy calculations
2. **Selectivity**: No off-target analysis
3. **Synthetic accessibility**: No retrosynthetic analysis
4. **In vivo efficacy**: No ADMET profiling beyond crude MW/HBA/HBD
5. **Statistical significance**: Sample sizes are too small for formal
   hypothesis testing
6. **Generalization**: Results are specific to EGFR. Other kinase families
   may behave differently.

### What would make the evidence stronger

- Replace MPNN proxy with physics-based AutoDock Vina or GNINA scores
- Add molecular fingerprint-based (ECFP4) similarity instead of SMILES n-grams
- Include synthetic accessibility scoring (SA score or ASKCOS)
- Expand to multiple kinase families
- Validate top candidates with FEP+ or experimental IC50

---

## Reproducibility

All comparisons can be reproduced with:

```bash
python scripts/rerank_candidates.py
python scripts/compare_baseline_vs_state_aware.py
python scripts/report_comparative_results.py
```

No external API calls, no random network fetches, no GPU required.
Candidate generation and scoring are deterministic.
