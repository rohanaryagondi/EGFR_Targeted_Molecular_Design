# Recruiter Summary: StateBind

## What Is This Project?

StateBind is a computational biology pipeline that tests whether knowing the 3D shape of a drug target helps you design better drug candidates. Most drug design software treats the target protein as frozen in one shape. But proteins move, and cancer mutations change which shapes they prefer. StateBind builds a system that designs different molecules for each shape and measures whether that approach beats the standard one.

The target is EGFR, a protein responsible for many lung cancers and the focus of three generations of targeted therapies.

---

## Skills Demonstrated

### Software Engineering
- **Modular architecture:** 12 subpackages with typed interfaces (Pydantic v2), each independently testable
- **548 passing tests** across 19 test files, covering schemas, pipelines, metrics, ML models, and figures
- **CI/CD:** GitHub Actions workflow for automated testing on push/PR
- **Config-driven design:** No hard-coded paths, YAML configuration, deterministic reproducibility
- **Clean packaging:** PEP 621 pyproject.toml, src/ layout, CLI entry point, optional dependency groups
- **33 runnable scripts** that produce reproducible artifacts from the same codebase

### Data Science / ML
- Feature engineering (33-dimensional mutation feature vectors)
- Three-tier model progression (nearest centroid → logistic regression → MLP)
- Markov transition models with contrastive embedding learning
- Ablation studies and honest reporting of single-class dataset limitations
- Unified scoring functions with explicit weight justification

### Computational Biology
- EGFR kinase domain conformational state classification
- Literature-curated structural features (DFG distance, αC-helix rotation, pocket volume)
- Pocket-conditioned molecular generation (type-I vs type-II inhibitor design)
- Resistance mutation mechanism mapping (T790M gatekeeper, C797S covalent site, L858R activation loop)

### Scientific Communication
- 7 phase reports with honest findings and stated limitations
- Comparison framework with defined fairness rules
- Explicit non-claims and conservative interpretation
- Findings framed as "qualified yes" rather than overclaimed results

---

## What Makes This Project Unusual

1. **It tests a hypothesis, not just implements a tool.** The pipeline is designed around one question with a measurable answer.
2. **The null result is acceptable.** The project reports limitations alongside results, treating "static is sufficient" as a valid outcome.
3. **It has a real baseline.** The static pipeline is implemented first, scored with the same function, and compared fairly.
4. **The documentation is stronger than most production codebases.** 17 docs files, 7 phase reports, architecture decisions, risk register, and a benchmark specification — all written before or during implementation.

---

## Resume-Ready Bullets

- Built a 9-workstream computational biology pipeline (84 Python files, 12 subpackages, 548 tests) that benchmarks conformational state-aware molecular design against a static single-structure baseline for EGFR-targeted drug discovery
- Designed a unified scoring framework with 3-tier MPNN docking cascade, Morgan/ECFP4 similarity, and ADMET filtering, producing a head-to-head comparison with statistical testing (Mann-Whitney U, Cohen's d=1.36)
- Implemented pocket-conditioned candidate generation (including VAE with 9.5M params) across 4 EGFR conformational states, discovering 431 novel candidates with diversity 0.91 inaccessible to the static baseline
- Created Markov state-transition models with contrastive embedding learning, achieving −0.91 correlation between embedding distance and transition frequency
- Engineered a modular, config-driven Python package (Pydantic v2, PEP 621, typed throughout) with deterministic reproducibility and no external API dependencies

---

## Interview Talking Points

**"Walk me through the project."**
> I built StateBind to test whether conformational state information improves computational molecular design. Kinase proteins like EGFR switch between active and inactive shapes, and mutations associated with drug resistance change which shape the protein prefers. I designed a pipeline that generates different drug candidates for each shape and compared the results against the standard approach of using just one shape. The null hypothesis was formally retained — static has a higher mean score — but the state-aware pipeline found 431 novel candidates with much higher chemical diversity (0.91 vs 0.57), demonstrating that state-awareness expands the accessible chemical space.

**"What was the hardest technical decision?"**
> Designing the docking component as a 3-tier cascade (trained MPNN, MLP fallback, constant stub) rather than claiming physics-based results. The MPNN achieves RMSE=0.72, which is informative but still a proxy. It would have been easy to overstate this as "docking-validated results," but the comparison framework is designed so real physics-based docking (Vina/GNINA) can be swapped in later without changing any other module.

**"What would you do with more time?"**
> Three things: (1) Replace the MPNN docking proxy with physics-based docking (AutoDock Vina or GNINA) for true binding affinity prediction. (2) Expand to additional kinase families (ABL, ALK, BRAF) to test whether the state-aware advantage generalizes beyond EGFR. (3) Add MD-derived transition matrices to replace the literature-curated Markov model. [Note: ECFP4 fingerprints, SA scoring, statistical testing, CI/CD, and ADMET profiling are now complete.]

**"What did you learn?"**
> That honest benchmarking is harder than building the pipeline. Defining what "outperforms" means before running the experiment, keeping the comparison fair, and reporting limitations alongside results required more careful thought than any individual module. The project also reinforced that modular design pays off — when I found a bug in Phase 5's evaluation script, I fixed it without touching any other phase.
