# Project Charter: StateBind

## Title

**StateBind: Context-Aware Conformational State Modeling for EGFR-Targeted Molecular Design**

## Thesis (one sentence)

Incorporating EGFR conformational state diversity into computational molecular design — by predicting which kinase states are relevant to a given mutation context and generating molecules against state-specific pockets — yields measurably better-scoring candidates than designing against a single static crystal structure.

## Abstract

EGFR is a validated oncology target with extensive structural coverage in the PDB and well-characterized resistance mutations. Despite this, most computational design campaigns dock against one or two crystal structures, ignoring the fact that clinically important mutations (T790M, C797S, L858R) shift the conformational equilibrium between active (DFG-in, αC-helix-in) and inactive (DFG-out, αC-helix-out) states. StateBind tests whether a state-aware design workflow — one that maps mutation context to conformational state preferences, extracts state-specific pockets, generates molecules against those pockets, and scores across the state ensemble — produces computationally superior candidates compared to a static single-structure baseline. The project makes no claims about biological activity; all outputs are computational hypotheses scored by reproducible proxy metrics (docking score, shape complementarity, cross-state selectivity). The deliverable is a modular, benchmarked, open-source pipeline with a clear experimental result: does state-awareness help, and by how much?

## Central Hypothesis

**Biological framing:** EGFR resistance mutations alter the conformational state equilibrium of the kinase domain. Molecules designed against the mutation-relevant state ensemble should complement the target better than molecules designed against an arbitrary single structure.

**Computational hypothesis:** A pipeline that (1) predicts mutation-relevant conformational states, (2) generates molecules conditioned on state-specific pocket geometries, and (3) scores candidates across the state ensemble will produce higher-ranked candidates (by docking score and cross-state complementarity) than a baseline pipeline using a single representative structure.

**Null hypothesis:** State-aware design produces candidates statistically indistinguishable from static single-structure design on all proxy metrics.

## Evaluation Philosophy

- All results are **computational hypotheses**, not biological claims.
- We report proxy metrics (docking scores, shape complementarity, chemical diversity) and acknowledge their limitations explicitly.
- We make **conservative claims**: "state-aware design produces computationally better-scoring candidates" — not "state-aware design produces better drugs."
- Every claim must be supported by a reproducible comparison against a defined baseline.
- We distinguish between signal (genuine state-dependent scoring differences) and noise (docking score variance, pocket extraction artifacts).

## Exact v1 Scope

### What v1 does

1. **Mutation context curation:** Build a structured atlas of 15–30 clinically relevant EGFR kinase domain mutations with resistance mechanism annotations, sourced from public databases (COSMIC, ClinVar) and published reviews.

2. **Conformational state atlas:** Classify 16 EGFR kinase domain PDB structures into conformational states (DFG-in/out × αC-helix-in/out = 4 canonical states) using literature-curated 9-dimensional structural feature vectors. Define pocket descriptors per state.

3. **State relevance prediction:** Given a mutation (e.g., T790M), predict which conformational states are most relevant. Baseline: curated lookup table. Stretch: lightweight classifier trained on mutation-state co-occurrence from PDB metadata.

4. **Molecular generation:** Generate candidate small molecules for state-specific pockets. Method: fragment-based enumeration or a lightweight pretrained SMILES generator conditioned on pocket descriptors. Baseline: generate against the single most-deposited PDB structure (typically 1M17 or similar).

5. **Scoring and ranking:** Score all candidates with a unified function (reference similarity, druglikeness, docking proxy, state specificity). Apply Lipinski-like property filters. Compare state-aware vs. static baseline on diversity, novelty, score distributions, and top-K composition. _Note: docking proxy uses a 3-tier cascade (MPNN → DockingProxy MLP → stub). Physics-based docking (Vina/GNINA) is planned future work._

6. **Report:** A final comparison showing score distributions, overlap analysis, novelty breakdown, and an honest verdict with stated limitations.

### What v1 does NOT do

| Explicitly out of scope | Why |
|------------------------|-----|
| Targets other than EGFR kinase domain | Scope discipline. One target done rigorously. |
| Full molecular dynamics simulations | Compute budget; would delay all downstream phases. |
| Training large generative models from scratch | Disproportionate effort for marginal gain over lightweight methods. |
| Covalent binder design (despite C797S relevance) | Requires specialized scoring; revisit in v2. |
| Biologics, PROTACs, peptide design | Small molecule scope only. |
| Wet-lab validation or biological activity claims | Not a pharma project. Computational hypotheses only. |
| Multi-target selectivity panels | Single target. |
| ADMET optimization | Beyond v1 scope; scoring is structural only. |
| AlphaFold structure prediction | Use existing PDB structures; AF models only if PDB coverage is insufficient for a state. |
| Private or proprietary data | All data must be publicly available and redistributable. |

## Biological Motivation

EGFR (Epidermal Growth Factor Receptor) is among the most important oncology drug targets. Three generations of EGFR tyrosine kinase inhibitors (TKIs) exist:

- **1st gen (gefitinib, erlotinib):** Target the active conformation. Effective against activating mutations (L858R, exon 19 deletions). Resistance emerges via T790M gatekeeper mutation.
- **2nd gen (afatinib, dacomitinib):** Irreversible inhibitors. Still susceptible to T790M.
- **3rd gen (osimertinib):** Designed to overcome T790M by targeting C797. Resistance emerges via C797S, which eliminates the covalent binding site.

Each resistance mutation alters the conformational landscape:
- **T790M** stabilizes the hydrophobic spine, favoring the active (DFG-in) state and sterically blocking 1st-gen inhibitors.
- **L858R** destabilizes the inactive state, shifting equilibrium toward active.
- **C797S** does not change conformation directly but eliminates the covalent warhead target, requiring non-covalent binders that must compete with ATP in a specific conformational context.

**The design implication:** A molecule designed against the DFG-out inactive pocket will fail if the mutation stabilizes DFG-in. Knowing which states are relevant to a given mutation context should inform pocket selection and, downstream, candidate quality.

## Target Audience

| Audience | What they care about |
|----------|---------------------|
| **Research engineer / hiring manager** | Clean code, modularity, testing, reproducibility, system design |
| **Computational biology scientist** | Scientific rigor, conservative claims, meaningful benchmarks, biological motivation |
| **Recruiter (technical screen)** | Project scope, completion, communication clarity, GitHub presentation |

The project must satisfy all three: it is simultaneously a portfolio piece, a technical demonstration, and a scientific argument.

## Success Criteria

### Must-have (v1 ships only if all are met)

- [ ] End-to-end pipeline runs from mutation input to ranked candidate output with a single command
- [ ] Baseline (static single-structure) produces scored candidates
- [ ] State-aware pipeline produces scored candidates
- [ ] Statistical comparison between the two is reported with effect sizes
- [ ] All results are reproducible from `config + code + public data`
- [ ] Repository has passing tests, typed code, and documentation

### Should-have (strengthens the project significantly)

- [ ] Comparison across ≥ 3 mutation contexts (e.g., T790M, L858R, C797S)
- [ ] At least one visualization figure suitable for a README hero image
- [ ] Generation diversity metrics (unique scaffolds, Tanimoto distance distribution)
- [ ] Cross-state selectivity analysis (do state-aware molecules score well on the intended state and poorly on others?)

### Nice-to-have (stretch goals)

- [ ] Lightweight ML state predictor (beyond lookup table)
- [ ] Interactive demo notebook
- [ ] Comparison to a second baseline (e.g., random SMILES from ZINC)

## Constraints

- All data must be publicly available and redistributable
- All tools must be open-source or freely available for academic use
- Compute budget: single GPU or CPU-only workflows
- Timeline: phased delivery, each phase independently demonstrable
- No hard-coded paths, thresholds, or credentials in source code
