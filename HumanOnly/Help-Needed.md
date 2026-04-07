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

## 3. Review 12 Vision Ideas

The Visionary AI proposed 12 strategic improvements. They need your judgment on priorities. You can either review them yourself or delegate to the Head AI.

**Ideas (in `vision/ideas/`):**
1. Continuous conformational conditioning (replace discrete 4-state with continuous)
2. 3D pocket-aware diffusion model
3. Kinome-wide selectivity panel
4. Ensemble uncertainty quantification
5. GNINA neural docking integration
6. Learned molecular similarity (contrastive)
7. Retrosynthetic feasibility scoring
8. Pareto multi-objective optimization
9. Time-split validation protocol
10. Self-supervised molecular pretraining
11. Explicit water thermodynamics
12. RL-guided molecular optimization

**Quick recommendation:** Ideas 5 (GNINA docking), 7 (retrosynthetic feasibility), and 9 (time-split validation) have the highest impact-to-effort ratio. Ideas 1 (continuous conditioning) and 8 (Pareto optimization) are the most scientifically interesting.

---

## 4. Real Docking Validation

The docking component (20% of scoring weight) uses a 3-tier cascade: MPNN (trained, active) → DockingProxy MLP → constant 0.5 stub. The MPNN provides learned affinity predictions but is still a proxy — not physics-based docking.

**Options:**
- **AutoDock Vina** — Open source, well-established, moderate accuracy. Requires prepared receptor + ligand PDB files.
- **GNINA** — Neural network-augmented docking, better than Vina for CNNscore. Open source.
- **Glide/FEP+** — Schrodinger commercial software. Gold standard but expensive.

**What you'd need:** Prepared EGFR receptor structures (4 states) in PDBQT format. The 16 PDB structures are already cataloged in the structure atlas.

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
- [x] Clean CI passing (548 tests, ruff clean)
- [x] README updated with real results
- [x] Statistical testing complete (Mann-Whitney U, bootstrap CI, Cohen's d, weight sensitivity)
- [x] Clear limitations section

**Still needed for a paper:**
1. Real docking scores (GNINA/Vina) — MPNN is a learned proxy, not physics-based
2. Ablation study: what happens when you remove state_specificity from scoring?
3. Comparison to at least one existing tool (e.g., ReinventSMILES, GENTRL)
4. Address the scoring function bias: reference similarity (35% weight) inherently penalizes novel VAE candidates

**Key result to frame:** Null hypothesis retained — state-aware design does not produce statistically superior composite scores (p<0.001, static favored, d=1.36). However, it dramatically expands chemical space (431 novel candidates, diversity 0.9056 vs 0.5684). The tension between novelty and similarity-based scoring is itself a publishable finding.
