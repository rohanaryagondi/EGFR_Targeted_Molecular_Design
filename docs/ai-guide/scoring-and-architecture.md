# Scoring System & Dependency Architecture

Reference doc for AI agents. Auto-loaded CLAUDE.md points here.

---

## Dependency Graph

```
data/ + utils/ + chemistry/ -> processing/ -> baselines/, structure/, context/, dynamics/
                                                  |            |
                                                  v            v
                                               ml/ (torch, torch_geometric, rdkit)
                                              / | \
                                             v  v  v
                                      generation/  |
                                          |        |
                                       ranking/ <--+
                                          |
                                      evaluation/
```

| Upstream | Downstream | Why |
|----------|------------|-----|
| chemistry | baselines, ranking | Morgan fingerprints, descriptors, docking proxy |
| processing | structure, context | Read processed PDB/mutation datasets |
| baselines | generation | Reuses candidate filtering and scoring functions |
| baselines | ranking | `ranking/scoring.py` imports `_score_*` from `baselines/scoring.py` |
| structure | generation | Pocket descriptors condition the generator |
| ml | generation | VAE generates state-conditioned candidates |
| ml | ranking | MPNN replaces docking_proxy stub in scoring |
| ml | evaluation | ADMET predictions for safety profiling |
| generation | ranking, evaluation | Candidate models consumed; diversity computed |
| ranking | evaluation | MergedRanking is input to all comparison functions |

**No circular dependencies.** The direction is always downward. Verify before adding
any cross-module import.

---

## Scoring Function Deep Dive

Both pipelines are scored by `ranking/scoring.py:score_unified()` (line 184). The
function delegates to component scorers defined in `baselines/scoring.py`.

### Component Table

| Component | Weight | Implementation | File:Line | Status |
|-----------|--------|---------------|-----------|--------|
| reference_similarity | 0.35 | Morgan/ECFP4 fingerprint Tanimoto vs 3 reference binders (falls back to SMILES 3-gram) | `baselines/scoring.py:76` (`_score_reference_similarity`) | Complete (WS02: Morgan fingerprints) |
| druglikeness | 0.30 | RDKit QED + Lipinski Ro5 (falls back to linear approximation) | `baselines/scoring.py:99` (`_score_druglikeness`) | Complete (WS02: RDKit descriptors) |
| docking_proxy | 0.20 | 4-tier cascade: GNINA -> MPNN -> DockingProxy MLP -> constant 0.5 stub | `ranking/scoring.py:38` (`_score_docking`) | GNINA (WS11) provides physics-based Vina + CNN scores. GPU guard prevents CPU docking. MPNN active as fallback (RMSE=0.72, R²=0.69, Pearson=0.83). |
| state_specificity | 0.15 | Geometric decay: 1.0/0.5/0.25/0.0 by number of states candidate appears in | `ranking/scoring.py:193` (`_compute_state_specificity`) | Functional; always 0 for static baseline |

### Weight Definition & Validation

- **Weights defined:** `ranking/scoring.py:125-130` (`DEFAULT_WEIGHTS` dict)
- **Weights validated:** `ranking/scoring.py:227-235` (`_validate_weights()`) -- checks
  all 4 keys present and sum == 1.0 (tolerance 1e-4)
- **Method string:** `ranking/scoring.py:132-136` (`SCORING_METHOD`) -- human-readable
  description embedded in every RankedPool artifact

### Reference Binders

Defined at `baselines/scoring.py:57-66`:
- Erlotinib: `COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC`
- Gefitinib: `COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1`
- Osimertinib: `COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1`

### Cascading Fallback Plan for docking_proxy

The docking_proxy component has a planned 3-tier fallback (see
`workstreams/INTERFACES.md` Contract 4):

```
Priority 0: GNINA physics-informed docking (WS11)
    - Requires: bin/gnina binary + prepared receptors + GPU detected
    - Implemented in: chemistry/docking.py (wrapper) + ranking/scoring.py:_score_docking_gnina()
    - Score: sigmoid(-vina_score / 3) maps kcal/mol to [0, 1]
    - GPU guard: only attempted when torch.cuda.is_available() or CUDA_VISIBLE_DEVICES set

Priority 1: MPNN prediction (AffinityMPNN predicts pIC50, normalize via sigmoid)
    - Requires: trained model at artifacts/models/mpnn/best_model.pt + torch
    - Implemented in: ml/mpnn.py (model) + ml/affinity_predictor.py (integration adapter)

Priority 2: DockingProxy MLP (WS04, lightweight numpy-based)
    - Requires: trained proxy from chemistry/docking_proxy.py
    - Interface: DockingProxy.predict(smiles) -> float in [0.0, 1.0]

Priority 3: Constant 0.5 stub (current default)
    - File: baselines/scoring.py:200-216 (_score_docking_stub)
    - Always available, zero discriminative power
```

### Baseline vs Unified Scoring Difference

The baseline has its OWN scorer at `baselines/scoring.py:246` (`score_candidates()`)
with slightly different weights (0.4/0.3/0.3, no state_specificity). The UNIFIED scorer
at `ranking/scoring.py:238` (`score_unified()`) uses 0.35/0.30/0.20/0.15. The unified
scorer is what matters for the head-to-head comparison. The baseline scorer exists only
for Phase 2 standalone runs.
