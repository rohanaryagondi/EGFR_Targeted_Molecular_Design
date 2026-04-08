# Help Needed

Things only you (the human) can do, or where your judgment is required. Ordered by impact.

---

## 1. ~~GPU Training~~ DONE

All 3 ML models trained on Bouchet HPC (2026-04-06):

| Model | Key Metrics | Training |
|-------|------------|----------|
| **MPNN** | RMSE=0.7182, R²=0.6863, Pearson=0.8323 | 217s on H200, 12.7M params, 10,466 compounds |
| **ADMET** | hERG AUROC=0.7745, CYP3A4 AUROC=0.7323 | 197s on L40S, 187K params, 27,698 molecules |
| **VAE v3** | 99.9% valid (SELFIES), 94.8% unique | 31 min on H200, 9.5M params, 300 epochs |

Checkpoints at `artifacts/models/{vae,mpnn,admet}/best_model.pt`.

---

## 2. ~~Fix CI/CD (Ruff Violations)~~ DONE

All 121 ruff violations fixed (2026-04-06). CI lint passes clean. Ruff config in `pyproject.toml` ignores N803/N806/N815 (scientific convention) and E402 (lazy imports in `scoring.py`).

---

## 3. ~~Review 12 Vision Ideas~~ DONE

All 12 Visionary ideas reviewed. 3 accepted and completed as workstreams:
- **005 → WS11:** GNINA physics-based docking (merged 2026-04-07)
- **008 → WS12:** Pareto multi-objective optimization (merged 2026-04-07)
- **009 → WS13:** Retrospective time-split validation (merged 2026-04-08)

9 deferred (revisit post-paper): 001, 002, 003, 004, 006, 007, 010, 011, 012.

---

## 4. ~~Real Docking Validation~~ DONE (WS11)

GNINA physics-based docking integrated as tier 0 of the 4-tier scoring cascade:
GNINA → MPNN → DockingProxy MLP → constant 0.5 stub.

GNINA provides real Vina scores + CNN scores with 3D binding poses. Receptors prepared for all 4 conformational states. GPU guard prevents CPU docking. Validation: binders -7.32 vs non-binders -4.16 kcal/mol (33 tests).

---

## 5. Experimental Validation (If Available)

All results are computational. The project explicitly states it cannot make biological claims. But if you have access to a wet lab or collaborators:

- **IC50 assays** for top-scoring candidates against EGFR (wild-type and T790M mutant)
- **Selectivity panels** against other kinases (to check off-target effects)
- **ADMET profiling** (microsomal stability, Caco-2, hERG patch clamp)

Even 2-3 validated compounds would transform this from a computational exercise into a publishable result.

---

## 6. Known Architectural Debts

Issues that are "working as designed" but limit scientific claims:

| Issue | Impact | Fix Difficulty |
|-------|--------|---------------|
| All 17 mutations map to DFGin_aCin (active state) | Context model evaluation is trivially 100% accurate | Hard — need multi-state mutation data |
| `state_specificity` gives state-aware a built-in 0.15 weight advantage | Fair comparison is debatable | Easy — can run ablation with weight = 0 |
| SMILES-level chemistry (string manipulation) | No 3D pose verification | Moderate — needs 3D conformer generation |
| 18 mutations, 461 candidates (395 VAE-generated) | VAE candidates expand space but dilute mean score | See null hypothesis discussion |
| Single kinase family (EGFR only) | Can't claim generalizability | Hard — full pipeline rebuild for new targets |

---

## 7. Publication Readiness

**Already achieved (portfolio-ready):**
- [x] All 3 ML models trained with metrics meeting/exceeding targets
- [x] Clean CI passing (646 tests, ruff clean)
- [x] README updated with real results
- [x] Statistical testing complete (Mann-Whitney U, bootstrap CI, Cohen's d, weight sensitivity)
- [x] Clear limitations section

**Still needed for a paper:**
1. ~~Real docking scores~~ DONE (WS11: GNINA integrated)
2. ~~Retrospective validation~~ DONE (WS13: 10x enrichment over static, time-split at 2010/2015)
3. Ablation study: what happens when you remove state_specificity from scoring?
4. Comparison to at least one existing tool (e.g., ReinventSMILES, GENTRL)
5. Address the scoring function bias: reference similarity (35% weight) inherently penalizes novel VAE candidates

**Key result to frame:** Null hypothesis retained — state-aware design does not produce statistically superior composite scores (p<0.001, static favored, d=1.36). However, it dramatically expands chemical space (431 novel candidates, diversity 0.9056 vs 0.5684). The tension between novelty and similarity-based scoring is itself a publishable finding.
