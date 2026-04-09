---
agent: Principal Computational Scientist
round: 3
date: 2026-04-09
type: review-assessment
scope: deliberation
---

# Round 3 Deliberation: Structural Fix Cascade, Revised Timeline, Implementation Order

## Executive Summary

CompBioRev's structural annotation discovery is the single most important finding
of this entire review process. I have now read every relevant source file line by
line. The damage is real, it is deep, and it must be the first thing addressed.
But I want to be precise about *how deep* it actually is, because panic-driven
over-scoping is as dangerous as ignoring the problem.

Bottom line: the structural annotation errors affect **5 source files, 1 config
file, and 3 test files** directly. The cascade into downstream artifacts (atlas,
docking, VAE labels) is significant but containable. Total effort for the
structural fix cascade is **3-5 person-days** -- not weeks. The existing codebase
architecture actually helps here: because the project uses hardcoded curated
features (not computed from PDB coordinates), fixing the annotations does *not*
require re-downloading or re-parsing any PDB files. It requires editing Python
dictionaries and YAML values.

The revised timeline is **18 weeks** (not 16), with the first 1.5 weeks devoted
exclusively to Tier 0 structural and methodological fixes before any new work
begins.

---

## 1. Structural Fix Cascade Analysis

### 1.1 The Four Errors, Ranked by Severity

**Error A: 3iku is not EGFR (ParM filament from E. coli)**

This is the most embarrassing error but, paradoxically, the easiest to fix
structurally because the feature values in `structure/features.py:212-225` are
*literature-curated*, not computed from the PDB file. The values listed for "3iku"
(dfg_asp_phe_dist=10.2, pocket_volume=780) are EGFR DFGout_aCin values taken from
the literature -- they describe the intended conformation, not the actual 3iku PDB
entry. The docking config (`configs/docking.yaml:29`) already uses 3w2r instead of
3iku for the DFGout_aCin representative, confirming someone noticed the issue
during workstream 11 but did not propagate the fix back to structures.py.

Files affected:
- `src/statebind/processing/structures.py:176-187` -- StructureRecord for "3iku"
- `src/statebind/structure/features.py:212-225` -- curated features keyed to "3iku"
- `src/statebind/generation/conditioning.py:96` -- representative_pdb="3iku"
- `src/statebind/processing/ligands.py:140` -- LigandRecord referencing pdb_id="3iku"
- `tests/test_structure.py:146,158,163` -- three test assertions using "3iku"

Fix: Replace "3iku" with "3w2r" everywhere. The feature values for 3w2r already
exist in `features.py:226-239` and are consistent with DFGout_aCin geometry. Then
remove the "3iku" entry from `features.py` and `structures.py`, or replace it
with 3IKA (T790M mutant, genuine EGFR DFGout) with correct mutation annotation.

Effort: **2-3 hours**.

**Error B: 3w2r is T790M/L858R, listed as mutations_present=[]**

In `structures.py:189-199`, 3w2r has `mutations_present=[]`. PDB 3W2R is the
T790M/L858R double mutant of EGFR. This is a metadata fix: change line 196 from
`mutations_present=[]` to `mutations_present=["T790M", "L858R"]`.

Impact on downstream: The `atlas.py` module passes `mutations_present` through to
AtlasEntry (line 68). The clustering module (`clustering.py:111,144`) uses
`mutations_present` to flag `has_mutant_structures` and to generate cluster labels.
Currently, the DFGout_aCin cluster is incorrectly labeled as containing no mutants.
After the fix, it will correctly show mutant structures. This is a label change,
not a score change.

The feature values in `features.py:226-239` for 3w2r do not need to change -- they
describe the actual pocket geometry of that crystal structure, which is correct
regardless of whether we call it WT or mutant. The pocket *is* what it is.

Effort: **15 minutes**.

**Error C: 5d41 is L858R/T790M, listed as mutations_present=[]**

Identical pattern to Error B. In `structures.py:216-225`, 5d41 has
`mutations_present=[]`. PDB 5D41 is L858R/T790M. Fix: change to
`mutations_present=["L858R", "T790M"]`.

Same downstream impact as Error B -- label-only, no score change.

Effort: **15 minutes**.

**Error D: 4zau may be DFGin, not DFGout**

This is the one error that could require significant refactoring. 4ZAU is the
*sole representative* for the DFGout_aCout state. It appears in:

- `structures.py:203-213` -- as ConformationalState.DFGOUT_ACOUT representative
- `features.py:242-255` -- curated features with DFGout-like values
  (dfg_asp_phe_dist=11.0, pocket_volume=850)
- `conditioning.py:115-135` -- representative_pdb="4zau" for DFGout_aCout
- `docking.py:148,196` -- docking representative for DFGout_aCout
- `configs/docking.yaml:30` -- DFGout_aCout: 4zau
- `tests/test_structure.py:138` -- asserts "4zau" is in available IDs

If 4ZAU is confirmed to be DFGin (active conformation bound to osimertinib/a Type I
covalent inhibitor), the entire DFGout_aCout state loses its sole representative
structure. The project drops from 4 states to 3.

**However**: The curated feature values in `features.py:242-255` describe a
DFGout_aCout geometry (dfg_asp_phe_dist=11.0, ac_helix_salt_bridge=10.5,
pocket_volume=850). These values were taken from the literature for the DFGout_aCout
state archetype, not measured from 4ZAU coordinates. So the *feature values* are
internally consistent with the state label -- they just may not match the actual
4ZAU crystal structure.

This needs the 1-2 hour coordinate inspection that CompBioRev recommended. If 4ZAU
is confirmed DFGin, see Section 1.2 below.

Effort for verification: **1-2 hours** (PyMOL/ChimeraX coordinate measurement).
Effort for fix if DFGin: see Section 1.2.

### 1.2 Scenario Analysis: What If 4ZAU Is DFGin?

If 4ZAU is confirmed DFGin, we have two options:

**Option 1: Move to 3-state model (DFGin_aCin, DFGin_aCout, DFGout_aCin)**

Files requiring changes:

| File | Location | Change | Effort |
|------|----------|--------|--------|
| `processing/models.py:51-55` | ConformationalState enum | Keep DFGOUT_ACOUT in enum (backward compat) or remove | 30 min |
| `processing/structures.py:201-226` | 4zau + 5d41 records | Remove both or relabel | 30 min |
| `structure/features.py:241-269` | 4zau + 5d41 features | Remove both entries | 15 min |
| `generation/conditioning.py:115-135` | DFGout_aCout pocket condition | Remove entire block | 15 min |
| `chemistry/docking.py:148,196` | DFGout_aCout representative | Remove mapping entry | 15 min |
| `configs/docking.yaml:30` | DFGout_aCout: 4zau | Remove line | 5 min |
| `ml/vae_dataset.py:41-46` | DEFAULT_STATE_MAPPING | Change to 3 states | 15 min |
| `ml/vae.py:83-84` | VAEConfig.n_states=4 | Change default to 3 | 10 min |
| `evaluation/docking_analysis.py:26` | _STATES list | Remove DFGout_aCout | 10 min |
| `dynamics/sequences.py:27` | _CLS alias | Remove or stub | 15 min |
| `context/features.py` | State probability outputs | Change from 4 to 3 states | 30 min |
| Tests: `test_structure.py`, `test_generation.py`, `test_vae_integration.py`, `test_dynamics.py`, `test_context.py`, `test_docking.py`, `test_ranking.py` | Various assertions on 4 states | Update to expect 3 states | 2-3 hours |

Total effort for 3-state conversion: **1-1.5 person-days**.

Critical consideration: The VAE must be retrained. The current model has
`n_states=4`, which means the one-hot conditioning vector has dimension 4. Changing
to 3 states changes the input dimension of the encoder GRU (from
`embed_dim + 4` to `embed_dim + 3`) and the z_proj layer (from `latent_dim + 4` to
`latent_dim + 3`). Existing checkpoints are incompatible. VAE retraining on the
Bouchet cluster takes approximately 2-4 hours on an H200, but the training data
also needs to be re-curated to remove DFGout_aCout-labeled molecules.

MPNN is not directly affected (it does not condition on state). ADMET is not
affected.

**Option 2: Keep 4-state model with honest disclosure**

Keep 4ZAU as the DFGout_aCout representative but:
1. Fix `mutations_present` for 5d41 (Error C above)
2. Note in the paper that 4ZAU's DFG conformation is ambiguous
3. Perform and report the sensitivity analysis: does the 4th state contribute
   meaningfully to enrichment?

This avoids retraining the VAE and changing the architecture. The paper can frame
DFGout_aCout as "based on the KLIFS classification, which we note is contested for
this specific structure."

My recommendation: **Start with Option 2 (keep 4 states, disclose). If ablation
shows DFGout_aCout contributes negligibly to enrichment, switch to 3 states.** This
preserves existing artifacts while the verification proceeds.

### 1.3 Does This Require Re-running Docking?

No, at least not for the structural fix itself. Here is why:

The docking config (`configs/docking.yaml:23-30`) already uses 3w2r (not 3iku)
for DFGout_aCin. It uses 4zau for DFGout_aCout. The docking scores in existing
artifacts were computed against the correct PDB files (3w2r and 4zau), even though
the metadata about those files was wrong. Fixing the mutation annotations does not
change the PDB coordinates, and therefore does not change the docking scores.

The one exception: if we drop to a 3-state model, then DFGout_aCout docking scores
become irrelevant and should be excluded from the analysis. But this is an analysis
change, not a re-docking.

### 1.4 Does This Require Re-training the VAE?

**Only if we change n_states from 4 to 3.** If we keep the 4-state model (my
recommendation), no retraining is needed. The VAE conditioning labels (DFGout_aCin,
DFGout_aCout) describe the *intended pocket geometry*, and the curated feature
values match those geometries. The fact that the underlying PDB entry IDs were
wrong or misannotated does not invalidate the conditioning labels -- the labels
describe pocket archetypes, not specific PDB entries.

This is a nuanced point that the paper must address explicitly: "State labels
represent idealized pocket geometries defined by DFG motif position and aC-helix
rotation, not specific PDB structures."

### 1.5 Cascade Summary

| Error | Direct fix | Downstream cascade | Re-run needed? | Effort |
|-------|-----------|-------------------|----------------|--------|
| 3iku -> 3w2r | 5 files | Atlas cluster labels | No docking, no VAE | 2-3 hrs |
| 3w2r mutations | 1 file | Atlas cluster labels | No | 15 min |
| 5d41 mutations | 1 file | Atlas cluster labels | No | 15 min |
| 4zau verification | 0 files (inspect only) | Potentially everything | Only if 3-state | 1-2 hrs |
| 4zau -> 3-state (if needed) | 11 files, 7 tests | VAE retraining | Yes: VAE | 1.5 days |
| **Total (keep 4 states)** | | | | **4-6 hours** |
| **Total (switch to 3 states)** | | | | **2-2.5 days** |

---

## 2. Revised Timeline (18 Weeks)

The original 16-week Scenario B from ProgDir did not account for the structural
fix cascade (discovered in Round 2). Adding Tier 0 work and adjusting for
cascading dependencies yields 18 weeks.

### Phase 0: Structural & Methodological Fixes (Weeks 0-1.5)

All items are blocking. Nothing else proceeds until these are done.

| Item | Days | Dependencies | Go/No-Go |
|------|------|-------------|----------|
| 4ZAU coordinate inspection | 0.25 | None | Is it DFGin or DFGout? |
| Fix 3iku -> 3w2r everywhere | 0.25 | None | Passes all tests |
| Fix 3w2r mutations_present | 0.1 | None | Passes all tests |
| Fix 5d41 mutations_present | 0.1 | None | Passes all tests |
| 3-state conversion (if 4ZAU is DFGin) | 1.5 | 4ZAU result | All 646 tests pass with n_states=3 |
| Honest disclosure framing (if 4 states kept) | 0.5 | 4ZAU result | Written and reviewed |
| Fix osimertinib reference leakage | 0.25 | None | Osimertinib removed from reference set |
| MPNN scaffold + temporal split | 2.0 | None | R^2 reported under all 3 splits |
| Bootstrap CIs + BEDROC | 0.5 | None | 95% CIs computed for EF@10, BEDROC |
| Pre-registration document | 0.25 | All above | Timestamped, committed to repo |
| **Total Phase 0** | **~5-7 days** | | |

Go/No-Go Gate 0: After MPNN scaffold split, if R^2 drops below 0.30, MPNN is not
credible as a scoring component. Fallback: rely entirely on GNINA + docking proxy.
This is survivable because MPNN is one of four cascading scoring tiers.

### Phase 1: Core Experiments (Weeks 2-8)

| Item | Weeks | Dependencies | Parallelizable? |
|------|-------|-------------|-----------------|
| Ablation C: unconditioned VAE | 1.5 | Phase 0 complete | Yes (independent) |
| Replace VAE validity with FCD + reconstruction | 0.5 | Phase 0 complete | Yes (independent) |
| Fixed oracle call budget comparison | 1.5 | Phase 0 complete | Yes (independent) |
| REINVENT 4 + GNINA scoring bridge | 2.0 | Phase 0 complete | Yes (independent) |
| Incremental ABL1 codebase extension | 5-6 | Phase 0 complete | Partially (blocks ABL1 pipeline) |
| Ablation E (scoring weights) | 0.5 | Phase 0 complete | Yes |
| Ablation F (fingerprint radius) | 0.5 | Phase 0 complete | Yes |
| Ablation G (docking exhaustiveness) | 0.5 | Ablation C result | Yes |

Go/No-Go Gate 1 (Week 4): Ablation C result. If Cohen's d < 0.5 between
conditioned and unconditioned VAE on EGFR, the state-conditioning hypothesis is
weak. Not fatal (enrichment might still come from multi-pocket docking) but
changes the paper narrative fundamentally.

Go/No-Go Gate 2 (Week 6): ABL1 codebase extension compiles, ABL1 data curated,
first ABL1 pipeline run produces non-trivial enrichment (EF@10 > 1.0). If ABL1
fails here, cut scope to EGFR-only paper.

### Phase 2: Extension & Strengthening (Weeks 5-12)

| Item | Weeks | Dependencies | Parallelizable? |
|------|-------|-------------|-----------------|
| ABL1 full pipeline execution | 2 | ABL1 codebase ready | After Gate 2 |
| ABL1 retrospective enrichment | 1 | ABL1 pipeline done | Sequential |
| BRAF data curation + pipeline | 2 | ABL1 working | Can start week 8 |
| Conformal prediction (TorchCP) | 1 | MPNN scaffold split done | Yes |
| Scoring sensitivity (Dirichlet 1,000+) | 0.5 | Phase 0 | Yes (analysis only) |
| Chemical space UMAP + FCD | 0.5 | Phase 0 | Yes (analysis only) |
| Conformational selection narrative | 0.5 | Phase 0 | Yes (writing only) |

Go/No-Go Gate 3 (Week 10): ABL1 enrichment must show EF@10 > 2.0 for
state-aware over static. If not, the multi-kinase generalization claim is dead.
Fall back to EGFR-only with honest disclosure that ABL1 did not replicate.

### Phase 3: Writing & Submission (Weeks 10-18)

| Item | Weeks | Dependencies |
|------|-------|-------------|
| ChemRxiv preprint (EGFR core results) | 1.5 | Phase 1 complete, Gate 1 passed |
| Survival funnel (ADMETlab 3.0 + AiZynthFinder) | 1.5 | Phase 1 complete |
| Full manuscript draft (JCIM target) | 3 | All experiments complete |
| Revision buffer | 2 | Manuscript submitted |

### Phase 4: Post-Submission / Paper 2 (Deferred)

- 3D baseline (DiffSBDD)
- Full multi-kinase generalization (MET, SRC, beyond ABL1/BRAF)
- REINVENT within-method ablations
- Docker benchmark infrastructure
- OpenFE FEP validation

### Timeline Visual

```
Week  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18
      [Phase 0: Fixes   ]
         [Ablation C.....]
         [Oracle budget...]
         [REINVENT setup......]
         [ABL1 codebase..............]
                     G1           G2
                              [ABL1 pipeline.....]
                                    [BRAF........]
                                                 G3
                                       [Preprint..]
                                             [ADMETlab...]
                                                   [Manuscript........]
                                                               [Buffer]
```

---

## 3. Implementation Order (Dependency-Driven)

### 3.1 Critical Path (Serial Dependencies)

```
4ZAU inspect -> decide 3 vs 4 states -> fix structures.py -> fix features.py
    -> fix conditioning.py -> fix docking config -> run full test suite
    -> (if 3-state) retrain VAE -> update VAE dataset config
    -> MPNN scaffold split -> re-evaluate MPNN R^2
    -> bootstrap CIs on current results
    -> pre-registration document
    -> [Gate 0: proceed to Phase 1]
```

This critical path is **7-10 days** end-to-end. Nothing in Phase 1 can start
before this completes.

### 3.2 Parallel Tracks After Phase 0

Once Phase 0 is done, four independent tracks can run simultaneously:

**Track A: ML Experiments (1 person)**
- Ablation C (unconditioned VAE)
- Replace validity metric
- Conformal prediction for MPNN
- Ablation E, F, G

**Track B: Infrastructure (1 person)**
- REINVENT 4 setup + GNINA bridge
- Fixed oracle call budget implementation
- ADMETlab 3.0 integration

**Track C: Multi-Kinase Extension (1 person)**
- ABL1 data curation
- ABL1 codebase extension (incremental)
- ABL1 pipeline execution
- BRAF (follows ABL1 template)

**Track D: Analysis & Writing (can overlap with A/B/C)**
- Scoring sensitivity analysis (Dirichlet)
- Chemical space visualization
- Conformational selection narrative
- ChemRxiv preprint draft

Realistically, this is a 1-person project, so these tracks execute in
priority order with interleaving. The order should be:

1. Phase 0 fixes (blocking everything)
2. Ablation C (blocking the core narrative)
3. MPNN evaluation + CIs (blocking all claims)
4. ABL1 extension (blocking multi-kinase claim)
5. Oracle budget comparison (blocking fairness claim)
6. REINVENT 4 (enhancing but not blocking)
7. Everything else

### 3.3 Go/No-Go Decision Points

| Gate | Week | Criterion | Pass | Fail |
|------|------|-----------|------|------|
| G0 | 1.5 | MPNN scaffold R^2 >= 0.30 | Proceed | Drop MPNN from scoring; GNINA + proxy only |
| G1 | 4 | Ablation C Cohen's d >= 0.5 | State-conditioning narrative confirmed | Reframe: diversity + multi-pocket docking |
| G2 | 6 | ABL1 first run EF@10 > 1.0 | Multi-kinase generalization alive | EGFR-only paper |
| G3 | 10 | ABL1 EF@10 > 2.0 (state-aware vs static) | Include ABL1 results | Disclose ABL1 negative result |
| G4 | 12 | BRAF EF@10 > 1.5 | 3-kinase paper | 2-kinase paper with honest discussion |

---

## 4. Remaining Codebase Concerns

### 4.1 The Curated Feature Values Are Not From PDB Coordinates

Every structural feature in `structure/features.py` is a hardcoded Python literal,
not computed from PDB files. The docstring says "literature-curated" and cites
references (Ung & Bhatt 2020, Modi & Bhatt 2021, Roskoski 2019, KLIFS). But the
specific values (e.g., dfg_asp_phe_dist=10.2 for "3iku") are not directly traceable
to any publication I can verify.

**Risk:** A reviewer could ask "where did dfg_asp_phe_dist=10.2 come from for your
DFGout_aCin representative?" If the answer is "we estimated it from the literature,"
that is defensible but must be disclosed. If the answer is "we measured it from 3iku
coordinates" -- well, 3iku is not EGFR, so those coordinates are meaningless.

**Mitigation:** For the structures that remain in the atlas (1m17, 2gs7, 3w2r, 4zau
or equivalent), compute actual geometric features from PDB coordinates using
BioPython. This validates the curated values. If they match within 10-15%, the
literature curation is defensible. If they diverge, the features need correction.

Effort: **2-3 days** for a PyMOL/BioPython measurement script covering all
representative structures.

### 4.2 The DFGout_aCin State Has Only Mutant Representatives

After fixing 3iku (Error A), the DFGout_aCin state is represented by:
- 3w2r: T790M/L858R double mutant

There is no WT EGFR DFGout_aCin structure in the PDB. CompBioRev confirmed this.
This is not an error in the codebase -- it reflects the biological reality that
WT EGFR rarely adopts DFGout conformations. But it means:

1. The DFGout_aCin pocket descriptors reflect a mutant pocket
2. Docking against 3w2r evaluates mutant binding, not WT state-specific binding
3. This must be disclosed in the paper

**Defense:** T790M is the gatekeeper residue, which is not in the DFG motif or the
binding pocket. The DFGout conformation is primarily defined by the DFG motif
position and the activation loop, not by residues 790 or 858. A pocket volume
comparison between 3w2r (DFGout) and 1m17 (DFGin) would show that the
conformational difference (volume: 800 vs 450 Angstrom^3) dominates the mutational
difference. But this argument must be made with actual structural overlay data, not
just asserted.

### 4.3 Osimertinib in Reference Binders

As noted in Round 2 and prior rounds, `baselines/scoring.py:63` includes
osimertinib in `_REFERENCE_BINDERS`. Since osimertinib is a known EGFR drug in the
retrospective validation set, this is a reference leakage. Must be removed.

Effort: **15 minutes** to remove from the list, plus verification that the scoring
function still produces reasonable similarity scores without it.

### 4.4 The `_STATES` Hardcoded List in evaluation/docking_analysis.py

Line 26 of `evaluation/docking_analysis.py`:
```python
_STATES = ["DFGin_aCin", "DFGin_aCout", "DFGout_aCin", "DFGout_aCout"]
```

This should derive from `ConformationalState` enum, not be a hardcoded list. If
we move to 3 states, this is another place that needs manual updating. Low effort
to fix but a maintenance hazard.

### 4.5 The Docking Config Has a Comment Acknowledging the 3iku Issue

`configs/docking.yaml:24-25`:
```yaml
# 3iku from the curated atlas is not EGFR; 3w2r (T790M/L858R EGFR,
# DFGout_aCin) is used instead for actual docking.
```

Someone on the team already knew 3iku was wrong. This knowledge was not propagated
to `structures.py` or `features.py`. This is a process failure, not a code failure.
The fix cascade must include removing this comment and making the primary data
source (structures.py) authoritative.

### 4.6 VAE State Dimension Is a Constructor Parameter

Good news: `VAEConfig.n_states` defaults to 4 but is configurable. The VAE
architecture (`vae.py:83-84, 128, 234`) uses `config.n_states` everywhere, not a
hardcoded 4. If we move to 3 states, the model definition itself does not need
source code changes -- only the config value changes. But existing checkpoints are
incompatible (dimension mismatch), so retraining is still required.

### 4.7 Missing Test Coverage for Structural Annotation Integrity

There are no tests that verify:
- That `mutations_present` matches the actual PDB metadata
- That `is_representative` structures are genuinely WT (or that mutant status is
  correct)
- That PDB IDs in the curated set are actually EGFR structures

Adding a test that validates curated metadata against the PDB REST API would
prevent this class of error from recurring. This is a 1-day task.

---

## 5. Response to Other Reviewers

### To CompBioRev (Structural Annotations)

Your findings are correct and I have confirmed them through code inspection.
The cascade is significant but containable. I want to push back slightly on one
point: you suggest the entire DFGout selectivity narrative is "built on mutant
structures." That is true for the PDB entries, but the curated feature values in
`features.py` describe idealized DFGout geometry, not the specific mutant pocket.
The features are internally consistent with the DFGout archetype. This is a valid
(if imperfect) approach that should be disclosed, not a fatal flaw.

The 3iku discovery is unambiguous -- it must be removed. The 4ZAU question needs
the coordinate inspection you recommended, and I have budgeted 2 hours for it.

### To MLRev (Compute-Matched Comparison)

I concur that the 30 vs 461 comparison is indefensible for ML venues. I have
placed the fixed oracle call budget comparison in Phase 1 with 1.5 weeks of effort.
One practical note: the PMO benchmark framework (Gao et al., 2022) provides
reference implementations. We should use their framework directly rather than
re-implementing the oracle call budget mechanism. This reduces effort and improves
credibility.

On the incremental ABL1 approach preserving ML rigor: yes, it does. The
incremental approach adds ABL1 as a second kinase without refactoring the core
architecture. All ML components (VAE, MPNN, ADMET) remain EGFR-specific in the
first paper. ABL1 uses the same architecture with ABL1-specific training data.
This is standard practice (e.g., Huang et al., 2021; Liao et al., 2024 both
evaluate kinase-specific models separately before claiming generalization).

### To Associate (DiffSBDD Concerns)

Your findings on DiffSBDD (Python 3.10, unmaintained) reinforce my position that
the 3D baseline should be deferred. The setup cost (1-2 weeks) combined with the
EGFR overlap in CrossDocked2020 makes it a poor return on investment for the first
paper. For JCIM, the key comparison is REINVENT 4 (same paradigm, no
state-conditioning) + the ablation battery. DiffSBDD becomes relevant for Nature
Computational Science or a second paper.

### To ProgDir (Timeline Revision)

Your 16-week Scenario B was reasonable before the structural discovery. I have
extended to 18 weeks to accommodate the Phase 0 fixes (1.5 weeks) and a small
buffer for the ABL1 extension uncertainty. The ChemRxiv preprint target moves from
week 6-8 to week 10-11, which still keeps us ahead of the 6-month scooping
window.

I agree with your 4-gate approach. My gate criteria are slightly more conservative
than yours (I require Cohen's d >= 0.5, not 0.3, for Ablation C), because a
d = 0.3 effect is too small to build a paper around.

---

## 6. Final Recommendations

### 6.1 Priority-Ordered Work Items (Final Position)

1. **4ZAU coordinate inspection** (0.25 days) -- BLOCKING
2. **3iku -> 3w2r fix cascade** (0.25 days) -- BLOCKING
3. **3w2r + 5d41 mutation annotation fixes** (0.1 days) -- BLOCKING
4. **Osimertinib reference leakage fix** (0.1 days) -- BLOCKING
5. **MPNN scaffold + temporal split** (2 days) -- BLOCKING
6. **Bootstrap CIs + BEDROC** (0.5 days) -- BLOCKING
7. **3-state vs 4-state decision** (contingent on item 1) -- BLOCKING if 3-state
8. **Pre-registration document** (0.25 days) -- blocks nothing but timestamps claims
9. **Ablation C: unconditioned VAE** (1.5 weeks) -- GO/NO-GO for narrative
10. **VAE metric replacement (FCD + reconstruction)** (3-5 days)
11. **Fixed oracle call budget** (1.5 weeks)
12. **ABL1 incremental extension** (5-6 weeks)
13. **REINVENT 4 + GNINA bridge** (2 weeks)
14. **Conformal prediction via TorchCP** (1 week)
15. **Scoring sensitivity (Dirichlet)** (2-3 days)
16. **ABL1 full pipeline + retrospective** (3 weeks)
17. **BRAF data + pipeline** (2 weeks, contingent on ABL1 success)
18. **Chemical space UMAP + FCD** (2-3 days)
19. **ChemRxiv preprint** (1.5 weeks)
20. **ADMETlab 3.0 survival funnel** (1.5 weeks)
21. **Gini selectivity analysis** (2-3 days)
22. **Full manuscript** (3 weeks)

### 6.2 Venue Recommendation

**Primary: JCIM (Journal of Chemical Information and Modeling)**

Rationale:
- JCIM regularly publishes computational kinase design studies
- The EGFR + ABL1 scope is sufficient for JCIM
- JCIM reviewers will appreciate the ablation battery and honest disclosure
- Turnaround is 6-10 weeks typically

**Stretch: Nature Computational Science**

Would require:
- 3+ kinases with consistent enrichment
- 3D baseline comparison (DiffSBDD or MolPilot)
- Wet lab validation or strong computational validation (FEP)
- None of these are achievable in the 18-week timeline

**Alternative: Briefings in Bioinformatics or Bioinformatics**

If the ablation C result is weak (d < 0.5 but d > 0.3), the paper might be a
better fit for a methods-focused venue that appreciates the benchmark framework
itself, even if the state-conditioning advantage is modest.

### 6.3 What NOT to Do

- Do NOT start multi-kinase work before Phase 0 is complete
- Do NOT attempt DiffSBDD/MolPilot integration in the first paper
- Do NOT report MPNN R^2 under random split (report scaffold split only, with
  random split in supplement for transparency)
- Do NOT claim the feature values are "measured from PDB coordinates" -- say
  "literature-curated"
- Do NOT claim "zero-shot generalization" for any 3D baseline trained on
  CrossDocked2020
- Do NOT change n_states without retraining the VAE
- Do NOT run Ablation C and ABL1 extension in parallel on the same GPU allocation
  (contention risk)

### 6.4 Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 4ZAU is DFGin, need 3-state | 40% | Medium (1.5 days + VAE retrain) | Budget time in Phase 0 |
| MPNN scaffold R^2 < 0.30 | 25% | Medium (lose MPNN as component) | GNINA + proxy as fallback |
| Ablation C d < 0.5 | 30% | High (weakens core narrative) | Reframe as benchmark + multi-pocket |
| ABL1 enrichment < 1.0 | 20% | Medium (lose multi-kinase claim) | EGFR-only paper |
| REINVENT 4 GNINA integration fails | 15% | Low (REINVENT is enhancement) | Use current pipeline as baseline |
| Scooped before preprint | 10-15% | High | Accelerate preprint to week 8-10 |
| ADMETlab 3.0 service instability | 30% | Low (not critical path) | Local ADMET models as fallback |

---

## References

Files inspected for this analysis:
- `/home/rag88/projects/statebind/repo/src/statebind/processing/structures.py` (lines 20-259)
- `/home/rag88/projects/statebind/repo/src/statebind/structure/features.py` (lines 25-300)
- `/home/rag88/projects/statebind/repo/src/statebind/structure/atlas.py` (lines 29-217)
- `/home/rag88/projects/statebind/repo/src/statebind/generation/conditioning.py` (lines 37-168)
- `/home/rag88/projects/statebind/repo/src/statebind/chemistry/docking.py` (lines 107-199, 532-579)
- `/home/rag88/projects/statebind/repo/src/statebind/ml/vae.py` (lines 69-176)
- `/home/rag88/projects/statebind/repo/src/statebind/ml/vae_dataset.py` (lines 40-90)
- `/home/rag88/projects/statebind/repo/src/statebind/baselines/scoring.py` (lines 57-66)
- `/home/rag88/projects/statebind/repo/src/statebind/ranking/scoring.py` (lines 1-80)
- `/home/rag88/projects/statebind/repo/src/statebind/evaluation/docking_analysis.py` (lines 25-60)
- `/home/rag88/projects/statebind/repo/src/statebind/processing/models.py` (lines 51-56)
- `/home/rag88/projects/statebind/repo/src/statebind/dynamics/sequences.py` (lines 22-28)
- `/home/rag88/projects/statebind/repo/configs/docking.yaml` (all 32 lines)
- `/home/rag88/projects/statebind/repo/tests/test_structure.py` (lines 137-164)
- `/home/rag88/projects/statebind/repo/tests/test_generation.py` (lines 123-232)
- `/home/rag88/projects/statebind/repo/tests/test_vae_integration.py` (lines 61-306)
- `/home/rag88/projects/statebind/repo/tests/test_dynamics.py` (lines 190-215)
- `/home/rag88/projects/statebind/repo/tests/test_context.py` (lines 298-300)
- `/home/rag88/projects/statebind/repo/tests/test_docking.py` (lines 295-405)
- `/home/rag88/projects/statebind/repo/tests/test_ranking.py` (lines 153-167)
