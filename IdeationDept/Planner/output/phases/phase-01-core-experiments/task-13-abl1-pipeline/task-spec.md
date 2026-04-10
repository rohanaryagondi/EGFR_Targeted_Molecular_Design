---
phase: "Phase 1: Core Experiments"
task_id: P1-T13
task_name: "ABL1 Pipeline + Retrospective + Gate G4"
implementation_plan_ref: "P12: Multi-Kinase Extension -- ABL1 (steps 6-7)"
status: pending
created: 2026-04-09T23:30:00Z
estimated_effort: "2-3 days"
---

# Task: ABL1 Pipeline + Retrospective + Gate G4

## Objective

Run the complete ABL1 pipeline: generate candidates from the trained ABL1 VAE,
score with GNINA docking against ABL1 receptors, run retrospective enrichment
analysis using ABL1's drug timeline, and perform cross-kinase comparison with
EGFR results. This produces the Gate G4 decision.

## Context

ABL1 has a rich drug approval timeline: imatinib (2001), dasatinib (2006),
nilotinib (2007), bosutinib (2012), ponatinib (2012), asciminib (2021). A
pre-2010 cutoff gives 3 reference drugs and 3 "future" drugs -- a better
retrospective test than EGFR. If ABL1 shows positive enrichment for state-aware,
the multi-kinase generalization strengthens the paper significantly.

**This task is conditional on P1-T12 (ABL1 models trained).**

## Prerequisites

- [x] P1-T12 completed (ABL1 VAE and MPNN trained)
- [x] ABL1 docking config at `configs/docking_abl1.yaml`
- [x] ABL1 receptor PDB files prepared for GNINA
- [x] ABL1 features and conditioning in codebase

## Files to Read (Context)

| File | Why Read It |
|------|------------|
| `scripts/generate_vae_candidates.py` | Generation script (adapt for ABL1) |
| `scripts/run_retrospective_validation.py` | Retrospective validation pattern |
| `src/statebind/evaluation/retrospective.py:33-82` | Drug approval timeline (needs ABL1 drugs) |
| `src/statebind/evaluation/comparison.py:183-256` | run_full_comparison() |
| `configs/docking_abl1.yaml` | ABL1 docking config from P1-T09 |

## Files to Modify

| File | Lines | Change Description |
|------|-------|-------------------|
| NEW: `scripts/run_abl1_pipeline.py` | -- | Complete ABL1 generation + scoring pipeline |
| NEW: `scripts/run_abl1_retrospective.py` | -- | ABL1 retrospective validation |
| NEW: `scripts/slurm_abl1_pipeline.sh` | -- | SLURM script for ABL1 docking |
| `src/statebind/evaluation/retrospective.py` | near 33-82 | Add ABL1 drug approval timeline |

## Implementation Steps

1. **Add ABL1 drug timeline to retrospective.py**:

   Add ABL1 approved drugs alongside the existing EGFR drugs:
   ```python
   ABL1_APPROVED_DRUGS = {
       "imatinib": {"year": 2001, "smiles": "..."},
       "dasatinib": {"year": 2006, "smiles": "..."},
       "nilotinib": {"year": 2007, "smiles": "..."},
       "bosutinib": {"year": 2012, "smiles": "..."},
       "ponatinib": {"year": 2012, "smiles": "..."},
       "asciminib": {"year": 2021, "smiles": "..."},
   }
   ```
   Use canonical SMILES from ChEMBL. Parameterize `get_future_drugs()` with
   `target_gene` argument.

2. **Generate ABL1 candidates**:

   ```bash
   python scripts/generate_vae_candidates.py \
       --config configs/vae_abl1.yaml \
       --checkpoint artifacts/models/vae_abl1/best_model.pt \
       --states <abl1_state_names> \
       --n-per-state 100 \
       --output artifacts/generation/vae_abl1_candidates.json
   ```

3. **Run ABL1 static baseline**:

   Generate candidates from a single ABL1 structure (e.g., 2GQG, DFGin)
   using the analog generation strategies. Score with GNINA against 2GQG receptor.

4. **Dock ABL1 candidates with GNINA** (SLURM):

   Submit docking jobs for ABL1 candidates against state-specific ABL1 receptors:
   - DFGin candidates → 2GQG receptor
   - DFGout candidates → 1IEP receptor
   
   SLURM: `-p priority -A prio_gerstein`

5. **Score with unified function**:

   Score all ABL1 candidates with `score_unified()`:
   - reference_similarity: against ABL1 reference binders (imatinib, dasatinib as references for pre-2010 cutoff)
   - druglikeness: same criteria
   - docking_proxy: GNINA scores against ABL1 receptors
   - state_specificity: based on ABL1 state assignment

6. **Run retrospective evaluation**:

   Pre-2010 cutoff:
   - Reference drugs: imatinib (2001), dasatinib (2006), nilotinib (2007)
   - Future drugs: bosutinib (2012), ponatinib (2012), asciminib (2021)
   
   Compute:
   - EF@10 with BCa bootstrap CIs
   - BEDROC(alpha=20) with CIs
   - For both static and state-aware ABL1 pipelines

7. **Cross-kinase comparison**:

   Compare EGFR vs ABL1 results:
   - EF@10 (state-aware): EGFR vs ABL1
   - EF@10 advantage (state-aware minus static): EGFR vs ABL1
   - Report whether both kinases show positive enrichment advantage

8. **Compile Gate G4 assessment**:

   Create `artifacts/evaluation/abl1_results.json`:
   ```json
   {
     "gate": "G4",
     "abl1_state_aware_ef10": X.X,
     "abl1_static_ef10": X.X,
     "abl1_advantage": X.X,
     "egfr_state_aware_ef10": X.X,
     "egfr_advantage": X.X,
     "cross_kinase_consistent": true/false,
     "recommendation": "GO|CONDITIONAL_GO|NO_GO"
   }
   ```

   Gate G4 criteria:
   - ABL1 EF@10 > 1.0 for state-aware: **GO**
   - Positive direction but wide CIs: **CONDITIONAL GO**
   - ABL1 EF@10 < 1.0: **NO-GO** (investigate; try BRAF)

9. **Update decisions-needed.md** with G4 result.

## Verification

- [ ] ABL1 candidates generated from trained VAE
- [ ] ABL1 candidates docked against correct state-specific receptors
- [ ] Retrospective evaluation uses correct ABL1 drug timeline
- [ ] Pre-2010 cutoff correctly separates reference vs future drugs
- [ ] EF@10 and BEDROC computed with BCa CIs
- [ ] Cross-kinase comparison clearly shows EGFR vs ABL1 patterns
- [ ] Gate G4 decision recorded in decisions-needed.md
- [ ] Results artifact at `artifacts/evaluation/abl1_results.json`
- [ ] `pytest -v --tb=short` -- 669+ tests pass
- [ ] Update `IdeationDept/Planner/output/logs/progress.md`

## Agent Instructions

- ABL1 drug SMILES must be canonical and verified against ChEMBL
- GNINA docking against ABL1 receptors -- make sure the correct receptor
  PDB files are used (NOT EGFR receptors!)
- Use priority queue for all SLURM jobs: `-p priority -A prio_gerstein`
- The cross-kinase comparison is key: if both EGFR and ABL1 show positive
  enrichment, the paper's claim generalizes beyond a single kinase
- If ABL1 results are negative, report honestly. A well-characterized negative
  is still valuable.

## Notes and Gotchas

- **ABL1 reference binders for pre-2010**: imatinib, dasatinib, nilotinib are
  reference drugs. Remove them from the generation training data if they appear.
  Check for temporal data leakage (same issue as osimertinib in EGFR).
- **ABL1 state assignment for generated molecules**: Generated molecules need
  state assignments for state_specificity scoring. Use the same assignment
  logic as EGFR (generated per-state from the state-conditioned VAE).
- **GNINA receptor preparation**: ABL1 receptor files may not exist yet. If not,
  prepare them using `scripts/prepare_docking_receptors.py` adapted for ABL1
  PDB IDs (1IEP, 2GQG, etc.).
- **Cross-kinase comparison framing**: If EGFR advantage is large and ABL1
  advantage is small (or vice versa), explore why. Different kinases may have
  different sensitivity to state conditioning.
