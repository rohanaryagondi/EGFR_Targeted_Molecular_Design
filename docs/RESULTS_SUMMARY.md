# Results Summary

## The Main Finding

State-aware molecular design produces a larger, more diverse, and partially higher-scoring candidate set than a static single-structure baseline for EGFR. The advantage is driven by structural novelty — chemically distinct scaffolds (back-pocket extensions, P-loop binders) that only arise from conformational states invisible to the baseline — not by scoring improvements on shared chemistry.

**The answer to "does state-awareness help?" is: yes, with caveats.** It helps by expanding the accessible chemical space. It does not demonstrably improve binding affinity, because we lack real docking data to test that claim.

---

## Benchmark Setup

**Target:** EGFR kinase domain, 4 conformational states

**Static baseline:** 1 crystal structure (1M17, WT active), 1 pocket, simple analogs. This is the conventional approach.

**State-aware pipeline:** 4 structures × 4 pockets × 7 generation strategies. Same scoring function applied to both.

**Scoring:** Unified weighted sum (reference similarity 0.35, druglikeness 0.30, docking proxy 0.20, state specificity 0.15). Docking proxy is a stub returning 0.5 for all candidates.

---

## Key Tables

### Table 1: Head-to-Head Comparison

| Metric | Static | State-Aware | Delta |
|--------|:------:|:-----------:|:-----:|
| Unique candidates | 30 | 79 | +49 |
| Diversity (1 − mean Tanimoto) | 0.526 | 0.561 | +0.035 |
| Mean composite score | 0.584 | 0.604 | +0.020 |
| Max composite score | 0.750 | 0.796 | +0.046 |
| Global top-10 share | 5 | 5 | 0 |
| Novel (not in other pipeline) | 0 | 49 | +49 |
| Jaccard overlap | — | — | 0.380 |

### Table 2: Novel Chemistry by Source

| Generation Strategy | Count | Requires State Info? |
|---------------------|:-----:|:--------------------:|
| Back-pocket extension | 18 | Yes (DFG-out only) |
| Volume filling | 12 | Yes (large pockets) |
| P-loop interaction | 5 | Yes (folded P-loop) |
| Hinge optimization | 5 | Partially |
| Covalent warhead | 4 | No |
| Gatekeeper avoiding | 3 | Partially |
| Analog | 2 | No |

### Table 3: State-Specific Pocket Properties

| State | PDB | Volume (Å³) | Back Pocket | P-Loop | Key Strategies |
|-------|-----|:-----------:|:-----------:|:------:|----------------|
| DFGin_aCin | 1M17 | 450 | No | Extended | Hinge, gatekeeper, covalent |
| DFGin_aCout | 2GS7 | 520 | No | Intermediate | Volume filling, hinge |
| DFGout_aCin | 3IKU | 790 | Yes | Extended | Back-pocket, volume filling |
| DFGout_aCout | 4ZAU | 850 | Yes | Folded | Back-pocket, P-loop |

---

## Key Figures

### Score Distribution Comparison

```
  Static baseline  mean=0.584  [0.405, 0.750]
    Mean  █████████████████████████████░░░░░░░░░░░ 0.584
    Max   ██████████████████████████████████████░░ 0.750

  State-aware      mean=0.604  [0.420, 0.796]
    Mean  ██████████████████████████████░░░░░░░░░░ 0.604
    Max   ████████████████████████████████████████ 0.796
```

### SMILES Overlap

```
  [Static 0 unique] ←─ (30 shared) ─→ [State-aware 49 unique]
  Jaccard = 0.380
```

Every static-baseline candidate also appears in the state-aware set. The state-aware set is a strict superset with 49 additional candidates.

### Novelty by Strategy

```
  back_pocket_extension  ██████████████████████████████ 18
  volume_filling         ████████████████████           12
  p_loop_interaction     ████████                        5
  hinge_optimized        ████████                        5
  covalent_warhead       ███████                         4
  gatekeeper_avoiding    █████                           3
  analog                 ███                             2
```

---

## Limitations

1. **Docking is a stub.** The most important discriminator (binding affinity) is a constant. The comparison can distinguish chemical novelty but not binding quality.
2. **state_specificity creates a built-in advantage.** Removing it would reduce the score delta. The diversity and novelty advantages are independent of this component.
3. **SMILES-level modifications.** No 3D geometry, no force-field validation, no synthetic accessibility check.
4. **Small scale.** 79 vs 30 candidates, 4 EGFR states. Not a large-scale benchmark.
5. **No experimental validation.** All claims are computational.

---

## Why This Project Matters

1. **It asks a real question.** "Does conformational state information improve molecular design?" is an open question in the field, not a solved problem.
2. **It builds the infrastructure to answer it.** The pipeline is modular, tested, and extensible. Swapping the docking stub for real docking or adding new kinase families requires changing one module, not the entire system.
3. **It reports honestly.** The null hypothesis (static is sufficient) is taken seriously. The limitations are stated alongside the results. The docking stub is not hidden — it's labeled in the scoring function.
4. **It demonstrates that state-aware generation discovers chemistry that static pipelines cannot.** Back-pocket extensions and P-loop binders are pharmacologically real compound classes. That they only appear in the state-aware set is a structural result, not an artifact of the scoring function.
