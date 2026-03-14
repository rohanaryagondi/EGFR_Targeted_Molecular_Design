# Risk Register

Each risk is assessed by likelihood (L), impact (I), and has a defined mitigation and fallback.

---

## R1: Insufficient PDB Coverage for Underrepresented States

| Aspect | Detail |
|--------|--------|
| **Category** | Data limitation |
| **Description** | Some EGFR conformational states (especially DFGout-αCout) may have very few (<3) deposited PDB structures, making it impossible to build a reliable pocket for that state. |
| **Likelihood** | High |
| **Impact** | Medium — limits state atlas to 3 of 4 canonical states |
| **Mitigation** | Accept that not all 4 states will be equally populated. Document which states are data-rich vs. data-poor. Use KLIFS database to identify additional structures. |
| **Fallback** | Reduce to 3 states (or even 2: active vs. inactive) if necessary. The core comparison (state-aware vs. static) still works with ≥2 states. |

## R2: Docking Scores Too Noisy to Distinguish Pipelines

| Aspect | Detail |
|--------|--------|
| **Category** | Scientific ambiguity |
| **Description** | Docking scores (Vina, smina) have well-known noise and limited accuracy. The difference between state-aware and baseline may be smaller than docking noise. |
| **Likelihood** | Medium-High |
| **Impact** | High — core claim becomes unsubstantiated |
| **Mitigation** | Generate enough candidates (≥100 per track) for statistical power. Use multiple scoring functions if feasible. Report effect sizes, not just p-values. Use cross-state selectivity as a complementary metric (less score-dependent). |
| **Fallback** | If docking scores are uninformative, pivot the comparison to shape complementarity (SuCOS or similar) or pharmacophore overlap. Report the null result for docking honestly. |

## R3: Pocket Extraction Inconsistency Across States

| Aspect | Detail |
|--------|--------|
| **Category** | Toolchain / methodology |
| **Description** | Different conformational states have different pocket shapes and volumes. If pocket extraction is inconsistent (different radii, different residue sets), the comparison is confounded — we'd be comparing pockets, not states. |
| **Likelihood** | Medium |
| **Impact** | Medium — confounds the benchmark |
| **Mitigation** | Use a consistent pocket extraction method across all states (same radius, same reference residues). Validate by visual inspection of extracted pockets against known co-crystal ligand positions. Report pocket volumes per state. |
| **Fallback** | Use the co-crystallized ligand's binding site (if available) as the pocket definition, which is the gold standard for that structure. |

## R4: Mutation→State Lookup Table Too Sparse

| Aspect | Detail |
|--------|--------|
| **Category** | Data limitation |
| **Description** | The literature may not provide clear conformational state preferences for most mutations, leaving the lookup table sparse (only T790M and L858R have strong evidence). |
| **Likelihood** | Medium |
| **Impact** | Medium — Dynamics module adds limited value |
| **Mitigation** | Accept sparsity. For mutations without literature evidence, use PDB metadata (which states are observed in structures containing that mutation). |
| **Fallback** | Run the benchmark on only the 2–3 mutations with clear state preferences. The argument still holds if the comparison works for those mutations, and we acknowledge the limited scope. |

## R5: Generation Method Produces Low-Quality Candidates

| Aspect | Detail |
|--------|--------|
| **Category** | Toolchain |
| **Description** | Lightweight generation methods (fragment enumeration, SMILES sampling) may produce chemically invalid, unrealistic, or low-diversity candidates. |
| **Likelihood** | Medium |
| **Impact** | Medium — weakens the generation comparison |
| **Mitigation** | Apply strict post-generation filters (validity, Lipinski, SA score). Report generation quality metrics (validity rate, uniqueness, diversity) before scoring. Use a proven pretrained model (e.g., REINVENT or a simple RNN) if fragment enumeration fails. |
| **Fallback** | Use curated ZINC fragments as the candidate source instead of de novo generation. This reduces novelty but ensures chemical quality. The state-aware vs. static comparison still works because the comparison is about pocket selection, not generation quality. |

## R6: Scope Creep

| Aspect | Detail |
|--------|--------|
| **Category** | Project management |
| **Description** | Temptation to add MD simulations, multi-target analysis, deep learning models, ADMET scoring, or other extensions before the core pipeline is complete. |
| **Likelihood** | High |
| **Impact** | High — project never ships |
| **Mitigation** | This charter document. Phase plan with pass/fail conditions. Each phase must pass before the next begins. No new scope unless current phase is complete. |
| **Fallback** | If a phase is blocked, skip it with a documented "TODO" and move to the next phase. A partial pipeline with honest documentation is better than a complete pipeline that never ships. |

## R7: RDKit or Docking Tool Installation Issues

| Aspect | Detail |
|--------|--------|
| **Category** | Toolchain |
| **Description** | RDKit and docking tools (Vina, smina) can be difficult to install, especially on macOS. Version conflicts with other dependencies. |
| **Likelihood** | Low-Medium |
| **Impact** | Low — delays but doesn't block |
| **Mitigation** | Pin versions in pyproject.toml. Document installation in RUNBOOK. Test on clean virtual environment. Keep RDKit and docking as optional dependencies (don't break imports if they're missing). |
| **Fallback** | Use conda for RDKit. For docking, use Vina's standalone binary rather than Python bindings. |

## R8: Benchmark Overfitting to EGFR

| Aspect | Detail |
|--------|--------|
| **Category** | Scientific ambiguity |
| **Description** | Results may be specific to EGFR and not generalizable to other kinases. Reviewers may question external validity. |
| **Likelihood** | High (this is a known limitation) |
| **Impact** | Low — explicitly out of scope for v1 |
| **Mitigation** | Acknowledge in the report. Frame as "proof of concept on a well-characterized target." Note that the pipeline architecture is target-agnostic even if the data is EGFR-specific. |
| **Fallback** | N/A — this is accepted. |

## R9: No Clear Winner (Null Result)

| Aspect | Detail |
|--------|--------|
| **Category** | Scientific ambiguity |
| **Description** | State-aware design may not beat static design on any metric. |
| **Likelihood** | Medium |
| **Impact** | Medium for portfolio framing, but low for scientific value |
| **Mitigation** | Frame the project as "testing a hypothesis" not "proving a method." A null result is still a finding. Report it with analysis of why (e.g., docking noise, insufficient state diversity, pocket similarity across states). |
| **Fallback** | Reframe deliverable as: "We built a pipeline to test state-awareness. Here's what we found. Here's what would need to change for state-awareness to matter." |

## R10: Time/Motivation Stall Between Phases

| Aspect | Detail |
|--------|--------|
| **Category** | Project management |
| **Description** | Each phase is independently useful, but the project loses momentum between phases. |
| **Likelihood** | Medium |
| **Impact** | Medium — incomplete project |
| **Mitigation** | Each phase produces a visible deliverable (artifact, report, figure). Phase pass conditions are designed to be achievable in focused sessions. Keep phases small and completable. |
| **Fallback** | Even Phase 1 + Phase 2 alone (mutation atlas + structure atlas) are demonstrable portfolio artifacts. |

---

## Risk Summary Matrix

| Risk | Likelihood | Impact | Priority |
|------|-----------|--------|----------|
| R1: PDB coverage gaps | High | Medium | Monitor |
| R2: Docking noise | Med-High | High | **Mitigate actively** |
| R3: Pocket inconsistency | Medium | Medium | Mitigate |
| R4: Sparse lookup table | Medium | Medium | Accept |
| R5: Low-quality generation | Medium | Medium | Mitigate |
| R6: Scope creep | High | High | **Mitigate actively** |
| R7: Toolchain issues | Low-Med | Low | Accept |
| R8: EGFR-specific results | High | Low | Accept |
| R9: Null result | Medium | Medium | Accept & reframe |
| R10: Momentum stall | Medium | Medium | Mitigate with phase design |
