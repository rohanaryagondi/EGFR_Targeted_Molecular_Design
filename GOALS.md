# StateBind: Goals, Success Criteria, and Vision

This document defines what StateBind is trying to achieve, how progress is measured, and where the project is headed. It is the reference for prioritization decisions.

---

## 1. The Scientific Thesis

**Claim:** Conformational state-aware molecular design outperforms static single-structure design for EGFR-targeted inhibitors.

**Biological basis:** EGFR kinase exists in four canonical conformational states, defined by two binary structural switches:

| Switch | In | Out |
|--------|:--:|:---:|
| DFG motif | Catalytically competent | Activation loop displaced |
| aC-helix | Stabilizes active site | Opens allosteric pocket |

The four combinations (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout) present structurally distinct binding pockets. Pocket volumes range from 450 A^3 (active, DFGin/aCin) to 850 A^3 (fully inactive, DFGout/aCout). The DFG-out conformations expose a back pocket absent in DFG-in states. The aCout conformations create additional volume from helix rotation. Each state accommodates different inhibitor chemotypes: type-I inhibitors bind the active state, type-II inhibitors exploit the DFG-out back pocket, and allosteric binders target the aCout cavity.

**Why mutations matter:** Clinically important EGFR resistance mutations shift the equilibrium between these states. T790M stabilizes the hydrophobic spine and favors DFG-in (active), making first-generation inhibitors like gefitinib and erlotinib ineffective. L858R destabilizes the inactive conformation, shifting the population toward active. C797S eliminates the covalent binding site on Cys797 without directly altering conformational preference, but forces a switch to non-covalent binding strategies that must compete with ATP in a specific conformational context. A molecule designed against the DFG-out inactive pocket will fail if the relevant mutation stabilizes DFG-in. Knowing which states are populated for a given mutation should inform pocket selection and, downstream, candidate quality.

**The hypothesis in formal terms:** A pipeline that (1) predicts mutation-relevant conformational states, (2) generates molecules conditioned on state-specific pocket geometries, and (3) scores candidates across the state ensemble will produce higher-ranked candidates than a baseline pipeline using a single representative structure.

**Null hypothesis:** State-aware design produces candidates statistically indistinguishable from static single-structure design on all proxy metrics.

**Current status of the null hypothesis:** Not rejected. The state-aware pipeline produces 49 novel candidates and higher diversity, but without real docking scores and formal statistical testing, the observed differences (mean score delta +0.020, diversity delta +0.035) lack significance testing. The null hypothesis remains alive until p < 0.05 on a meaningful metric with the docking stub replaced.

---

## 2. What "Impressive" Means

StateBind is simultaneously a scientific argument, an engineering demonstration, and a portfolio project. "Impressive" requires meeting standards across all three dimensions.

**Scientific standard:**
- A controlled experiment with a clearly defined baseline, identical scoring, and honest limitations.
- Novel ML-generated molecules (from a trained Conditional SMILES VAE) with validity >= 50%, not just SMILES string manipulations.
- A trained MPNN replacing the docking stub with RMSE < 1.0 pIC50 units, providing real binding affinity discrimination.
- Statistical significance (p < 0.05, Mann-Whitney U) on at least one primary metric when comparing state-aware vs. static.
- ADMET safety filtering so candidates are not just novel but drug-like by modern standards (hERG liability, solubility, metabolic stability).

**Engineering standard:**
- RDKit-backed chemistry: Morgan/ECFP4 fingerprints, synthetic accessibility scores, proper molecular validation replacing all SMILES string heuristics.
- CI/CD pipeline via GitHub Actions ensuring tests pass on every push.
- 400+ tests covering all modules including the new ML infrastructure.
- Config-driven, typed, documented, and reproducible from `code + config + public data`.

**Communication standard:**
- Every claim is qualified. "Computationally better-scoring" not "better drugs."
- Limitations are stated alongside results, not buried in appendices.
- The docking stub (or its MPNN replacement) is labeled, not hidden.
- The project tells a coherent story from question to architecture to qualified answer.

---

## 3. Short-Term Goals

These are the immediate priorities, ordered by impact and dependency.

### Priority 1: Prepare ML Training Data

All three ML models require curated training datasets before training can begin.

- **ChEMBL EGFR bioactivity data** for VAE and MPNN training. Extract SMILES + pIC50 for EGFR (target ID CHEMBL203). Filter for IC50/Ki assays, deduplicate by canonical SMILES, split train/val/test (80/10/10). Target: 3,000-5,000 compounds with measured affinities.
- **TDC (Therapeutics Data Commons) datasets** for ADMET model training. Six endpoints: hERG liability (classification), human liver microsomal stability (regression), Caco-2 permeability (regression), aqueous solubility (regression), plasma protein binding (regression), CYP3A4 inhibition (classification). Each endpoint requires independent train/val/test splits.
- **Data validation:** All SMILES must be canonicalized via RDKit. Compounds failing `Chem.MolFromSmiles()` are excluded. Molecular weight range 150-800 Da. No salts, no mixtures, no polymers.

### Priority 2: Train All Three ML Models

Each model has concrete performance targets.

**Conditional SMILES VAE** (`statebind.ml.vae`):
- Reconstruction accuracy > 80% on validation set.
- Validity of generated SMILES >= 50% (verified by RDKit parsing).
- Uniqueness >= 80% among valid generations.
- KL divergence properly annealed (beta warmup over first 10 epochs).
- State-conditioning must produce measurably different molecular distributions per state.

**Affinity MPNN** (`statebind.ml.mpnn`):
- RMSE < 1.0 pIC50 units on held-out test set.
- R-squared > 0.5 (the model explains more variance than the mean predictor).
- Pearson correlation > 0.7 between predicted and measured pIC50.
- The model must generalize to SMILES outside the training set (no memorization).

**Multi-task ADMET** (`statebind.ml.admet`):
- hERG AUROC > 0.75 (the most safety-critical endpoint).
- CYP3A4 AUROC > 0.70.
- Regression endpoints: Spearman correlation > 0.5 on at least 4 of 6 tasks.
- Multi-task learning must outperform or match single-task baselines on average.

### Priority 3: Core Workstreams (WS01, WS03)

These two workstreams can start immediately and unblock downstream work.

**WS01 -- Chemistry Foundation:** Replace all SMILES string heuristics with RDKit-backed operations. Morgan/ECFP4 fingerprints for similarity. Synthetic accessibility scoring. Proper molecular validation. This unblocks WS02 (scoring integration), WS04 (docking proxy), WS08 (MPNN affinity), and WS09 (ADMET predictor).

**WS03 -- Statistical Testing:** Add scipy-based statistical tests (Mann-Whitney U, bootstrap confidence intervals, effect sizes). This is required to formally reject or fail to reject the null hypothesis. Without it, all comparisons are descriptive only.

---

## 4. Medium-Term Goals

These goals assume the short-term priorities are complete.

### All Nine Workstreams Finished

The full workstream suite transforms the pipeline from a proof-of-concept into a credible computational study:

- WS01 (Chemistry Foundation) + WS02 (Scoring Integration): RDKit throughout, Morgan fingerprints in the scoring function, SA scores filtering unrealizable candidates.
- WS03 (Statistical Testing) + WS05 (Visualization): Formal significance tests with matplotlib figures suitable for publication or README.
- WS04 (Docking Proxy) + WS08 (MPNN Affinity): The docking stub replaced by a trained MPNN that actually discriminates binding quality. The 20% scoring weight currently wasted on a constant 0.5 becomes informative.
- WS06 (CI/CD): GitHub Actions running pytest on every push/PR. No more silent regressions.
- WS07 (Conditional VAE): State-conditioned molecular generation producing genuinely novel chemistry, not SMILES string modifications.
- WS09 (ADMET Predictor): Safety filtering integrated into the generation pipeline. Candidates with hERG liability or poor metabolic stability are flagged before ranking.

### Full Cascade Scoring

With the MPNN trained and integrated, the scoring function becomes:

| Component | Weight | Method (current) | Method (target) |
|-----------|:------:|-------------------|-----------------|
| reference_similarity | 0.35 | SMILES 3-gram Tanimoto | Morgan/ECFP4 Tanimoto |
| druglikeness | 0.30 | Heuristic MW/HBA/HBD | RDKit QED + Lipinski + SA score |
| docking_proxy | 0.20 | Constant 0.5 (stub) | MPNN-predicted pIC50, normalized |
| state_specificity | 0.15 | Geometric decay | Geometric decay (unchanged) |

Every component becomes meaningful. The 20% docking weight now carries real discriminative signal.

### Re-Run the Comparison

With real scoring, regenerate all candidates (VAE-generated, not string-modified), re-score with the full cascade, and re-run the head-to-head comparison. The central question remains the same: does state-awareness help? But the answer now has docking-based evidence and statistical backing.

**Target outcome:** Reject the null hypothesis (p < 0.05) on at least one of: mean composite score, top-10 composition, or binding affinity distribution. If the null hypothesis still cannot be rejected with real scoring, that is a valid and publishable result: "conformational state information does not improve computationally predicted binding quality for EGFR, despite expanding chemical diversity."

### ADMET Filter in Pipeline

ADMET predictions are applied as a post-generation filter before ranking. Candidates flagged for hERG liability (probability > 0.5) or poor solubility are either removed or penalized in ranking. This ensures the final candidate list is not just computationally high-scoring but pharmacologically plausible.

---

## 5. Long-Term Vision

These goals extend beyond the current v1 scope. They are recorded here for directional planning, not as commitments.

### Real Physics-Based Docking

Replace or augment the MPNN proxy with physics-based docking using AutoDock Vina or GNINA. Dock each candidate against each of the 4 state-specific receptor structures (prepared as PDBQT files). This provides pose-level information (binding mode, key interactions) that ML proxies cannot. Estimated effort: 2-3 days for receptor preparation and Vina integration, plus compute time proportional to candidate count.

### Experimental Validation via FEP+

For the top 10-20 candidates from the re-scored comparison, compute binding free energies using free energy perturbation (FEP+, Schrodinger) or absolute binding free energy methods. This is the closest computational analog to experimental IC50 measurement and would provide the strongest evidence for or against the state-aware hypothesis. Requires commercial software or collaboration.

### Multi-Target Expansion

Replicate the pipeline for additional kinase families to test generalization:

- **ABL:** Well-characterized DFG-out preference (imatinib binds DFG-out). Strong test case for type-II inhibitor design.
- **ALK:** Distinct conformational landscape with clinical resistance mutations (G1202R, L1196M).
- **BRAF:** V600E mutation alters DFG conformation. Existing drugs (vemurafenib, dabrafenib) target specific states.

Each new target tests whether the state-aware advantage observed for EGFR generalizes. If it does, the thesis strengthens. If it does not, the thesis is refined: state-awareness may help only for targets with large conformational diversity.

### Active Learning Loop

Connect the VAE, MPNN, and pipeline into an iterative design cycle:

1. VAE generates candidate molecules conditioned on target state.
2. MPNN scores candidates for predicted binding affinity.
3. Top candidates are added to the MPNN training set (with predicted labels initially, experimental labels if available).
4. MPNN is retrained on the expanded dataset.
5. Updated MPNN scores guide the next round of VAE generation (reward signal for reinforcement learning or Bayesian optimization).

This closes the loop between generation and evaluation, enabling the pipeline to improve its own candidate quality over iterations.

### Multi-Objective Optimization

Replace the weighted linear scoring function with Pareto frontier optimization. Instead of collapsing affinity, druglikeness, selectivity, and ADMET into a single number, maintain them as separate objectives and identify the Pareto-optimal set: candidates where no single metric can be improved without degrading another. This produces a diverse set of candidates optimized along different tradeoff axes, better reflecting real drug design decisions.

---

## 6. Success Criteria Table

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Passing tests | 359 | 450+ | In progress |
| Docking scoring | Stub (constant 0.5) | Trained MPNN (RMSE < 1.0) | Not started |
| Similarity method | SMILES 3-gram Tanimoto | Morgan/ECFP4 Tanimoto | Not started |
| Statistical testing | None (descriptive only) | p < 0.05 Mann-Whitney U | Not started |
| Novel candidates | 49 (string-modified) | 100+ (VAE-generated) | Not started |
| VAE validity | N/A (model not trained) | >= 50% valid SMILES | Not started |
| VAE reconstruction | N/A | > 80% accuracy | Not started |
| MPNN RMSE | N/A (model not trained) | < 1.0 pIC50 | Not started |
| MPNN R-squared | N/A | > 0.5 | Not started |
| hERG AUROC | N/A (model not trained) | > 0.75 | Not started |
| ADMET endpoints passing | N/A | >= 4 of 6 with Spearman > 0.5 | Not started |
| CI/CD | None (local only) | GitHub Actions on push/PR | Not started |
| Druglikeness method | Heuristic MW/HBA/HBD | RDKit QED + Lipinski | Not started |
| Synthetic accessibility | None | RDKit SA score filtering | Not started |
| Null hypothesis | Not rejected | Rejected or formally retained | Pending |
| Workstreams complete | 0 of 9 | 9 of 9 | Not started |
| Training data prepared | None | ChEMBL EGFR + TDC ADMET | Not started |
| State-conditioned generation | SMILES string mods | Conditional VAE sampling | Not started |

---

## 7. What Each Workstream Accomplishes

**WS01 -- Chemistry Foundation:** Replaces all SMILES string heuristics with RDKit-backed molecular operations (Morgan fingerprints, canonical SMILES, SA scores, molecular validation), establishing the chemical infrastructure every downstream workstream depends on.

**WS02 -- Scoring Integration:** Swaps the crude n-gram Tanimoto and heuristic druglikeness components in the unified scoring function with Morgan/ECFP4 similarity and RDKit QED scoring, making the 65% of score weight currently carried by approximations chemically rigorous.

**WS03 -- Statistical Testing:** Adds scipy-based significance tests (Mann-Whitney U, bootstrap confidence intervals, Cohen's d effect sizes) to the evaluation module, enabling the project to formally reject or retain the null hypothesis instead of reporting descriptive deltas.

**WS04 -- Docking Proxy:** Builds a learned docking proxy (initially a simple regression model on molecular descriptors) as an intermediate step toward the full MPNN, replacing the constant-0.5 stub with a model that at least discriminates between molecular structures.

**WS05 -- Visualization:** Creates publication-quality matplotlib/seaborn figures (score distributions, chemical space UMAP, state atlas heatmaps) for the README hero image and comparison report, making results immediately interpretable without reading tables.

**WS06 -- CI/CD:** Adds a GitHub Actions workflow running pytest, ruff, and type checking on every push and pull request, preventing silent test regressions and enforcing code quality standards automatically.

**WS07 -- Conditional VAE:** Trains the conditional SMILES VAE on EGFR-relevant chemistry so the state-aware pipeline generates genuinely novel molecules by sampling from a learned latent space conditioned on conformational state, replacing the current SMILES string modification approach.

**WS08 -- MPNN Affinity:** Trains the message-passing neural network on ChEMBL EGFR bioactivity data to predict pIC50 from molecular graphs, providing the replacement for the docking stub that transforms the 20% docking score weight from dead weight into real binding affinity signal.

**WS09 -- ADMET Predictor:** Trains the multi-task ADMET model on TDC datasets to predict six safety and pharmacokinetic endpoints, enabling post-generation filtering that removes candidates with hERG liability, poor solubility, or metabolic instability before they reach the ranking stage.

---

## 8. The Story This Project Tells

### For Presentations and Portfolio Review

**Lead with the question, not the answer.** "Does knowing which conformational state a drug target is in help you design better molecules?" is a genuinely open question in computational drug design. Most pipelines dock against one crystal structure. StateBind tests whether using structural biology knowledge about conformational diversity makes a measurable difference.

**Show the architecture.** The pipeline is modular, config-driven, and testable. Twelve subpackages in a sequential, acyclic dependency graph. Pydantic models at module boundaries. YAML configs. Disk-based artifact communication. This is not a Jupyter notebook experiment; it is engineered software that happens to answer a scientific question.

**Present qualified results.** The state-aware pipeline discovers 49 novel candidates inaccessible to the static approach (back-pocket extensions, P-loop binders, type-II scaffolds) with higher chemical diversity. But the docking component is a stub (or an MPNN proxy, depending on when the audience sees the project), and the comparison lacks (or includes) formal statistical testing. State the limitations in the same breath as the results.

**Emphasize what makes this rigorous.** The baseline is built and scored before the state-aware pipeline runs. Both pipelines are scored with the same function. The controlled variable is generation strategy, not scoring. The null hypothesis is taken seriously. A null result (state-awareness does not help) would be reported with the same thoroughness.

### For a Computational Biology Paper

**Framing:** A computational experiment with controlled variables and reproducible methodology. The independent variable is whether conformational state information is used during molecular generation. The dependent variables are chemical diversity, novelty, composite score, and (with MPNN) predicted binding affinity. Confounding variables (scoring function bias from state_specificity, small sample size) are identified and discussed.

**Structure the argument:**
1. Biological motivation: EGFR resistance mutations shift conformational equilibrium.
2. Hypothesis: state-conditioned design captures chemistry that static design misses.
3. Method: matched pipeline comparison with identical scoring.
4. Results: diversity and novelty advantages confirmed, affinity advantage pending.
5. Limitations: small scale, proxy metrics, single target.
6. Conclusion: state-awareness expands accessible chemical space; whether it improves binding remains open.

**Honest framing of negative or ambiguous results.** If the null hypothesis cannot be rejected even with real docking, the paper reports: "Despite generating a more diverse candidate set, state-aware design did not produce statistically superior binding affinity predictions for EGFR, suggesting that conformational state information primarily benefits chemical space exploration rather than binding quality optimization." This is a valid finding.

### The Narrative Arc

The project documentation (see `docs/GITHUB_STORY.md`) defines the narrative principles:

1. Lead with the question, not the answer.
2. Demonstrate engineering through structure, not volume.
3. Be explicit about what you did not do.
4. Frame the null result as acceptable.
5. Never claim biological activity from computational scores.

The story StateBind tells is not "we designed better drugs." It is: "we built the infrastructure to rigorously test whether a specific piece of structural biology knowledge improves computational molecular design, we ran the experiment under controlled conditions, and we reported the result with its limitations." That story holds regardless of whether the null hypothesis is ultimately rejected.
