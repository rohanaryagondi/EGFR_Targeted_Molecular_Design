# Help Needed

Things only you (the human) can do, or where your judgment is required. Ordered by impact.

---

## 1. GPU Training (Highest Priority)

The 3 ML models are code-complete but untrained. Training requires CUDA. AI agents can't do this — it needs your HPC cluster.

**What to do:**
```bash
git checkout ML
pip install -e ".[ml]"

# Verify GPU is available
python -c "import torch; print(torch.cuda.is_available())"  # Must print True

# Train (can run all three sequentially or in parallel on separate GPUs)
python scripts/train_vae.py --config configs/vae.yaml      # 2-4 hours
python scripts/train_mpnn.py --config configs/mpnn.yaml     # 1-2 hours
python scripts/train_admet.py --config configs/admet.yaml   # 2-3 hours
```

**What to watch for:**
- VAE: KL collapse (all generated molecules identical) — reduce `kl_weight` in `configs/vae.yaml` from 0.01 to 0.005
- MPNN: Overfitting (train loss drops, val loss rises) — increase `dropout` from 0.1 to 0.2
- ADMET: One task dominating loss — adjust `task_weights` in `configs/admet.yaml`

**Checkpoints go to:** `artifacts/models/{vae,mpnn,admet}/best_model.pt` — do NOT commit these to git.

---

## 2. Fix CI/CD (Ruff Violations)

~40 pre-existing ruff violations across `src/` guarantee CI failure on every push. Mostly auto-fixable.

**What to do:**
```bash
ruff check --fix src/     # Auto-fix I001, F401, most E501
ruff check src/           # See what's left (manual fixes needed)
pytest -v --tb=short      # Verify nothing broke
```

**Risk:** Removing "unused" imports (F401) could break things if they're re-exported. Check each removal.

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

The docking_proxy component (20% of scoring weight) is currently either a stub (constant 0.5) or a lightweight MLP proxy. Neither is real docking.

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
| 18 mutations, ~80 candidates | Too small for strong statistical claims | Moderate — expand mutation set or generation |
| Single kinase family (EGFR only) | Can't claim generalizability | Hard — full pipeline rebuild for new targets |

---

## 7. Publication Readiness

**What's needed for a paper:**
1. Trained ML models with metrics meeting targets (see Section 1)
2. Real docking scores (at minimum MPNN, ideally GNINA/Vina)
3. Statistical significance on at least one primary metric (p < 0.05)
4. Ablation study: what happens when you remove state_specificity from scoring?
5. At least a brief comparison to one existing tool (e.g., ReinventSMILES, GENTRL)

**What's needed for a portfolio piece (lower bar):**
1. Trained ML models
2. Clean CI passing
3. Updated README with real (non-stub) results
4. Clear limitations section (already exists)
