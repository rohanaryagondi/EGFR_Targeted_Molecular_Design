# Project Charter: StateBind

## Vision

Build a research-grade computational pipeline demonstrating that conformational state-aware molecular design produces better EGFR binders than static single-structure approaches.

## Goals

1. **Curate** a mutation-annotated EGFR context dataset linking clinical resistance mutations to conformational state preferences
2. **Build** a structural atlas of EGFR conformational states from publicly available PDB structures
3. **Predict** which conformational states are most relevant given a mutation context
4. **Generate** candidate molecules conditioned on state-specific pocket geometries
5. **Benchmark** state-aware designs against static-structure baselines using reproducible scoring

## Non-Goals

- This is NOT a general-purpose drug discovery platform
- We do NOT claim biological validation or clinical relevance
- We do NOT train large foundation models from scratch
- We do NOT target multiple kinase families (EGFR only for v1)
- We do NOT replace experimental validation

## Success Criteria

- [ ] End-to-end pipeline runs from mutation input to ranked candidate output
- [ ] Baseline comparison shows measurable difference between state-aware and static approaches
- [ ] All results are reproducible from config + code + data
- [ ] Repository is clean, documented, and demo-ready

## Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| EGFR kinase domain | Other kinase families |
| Public PDB structures | Private/proprietary structures |
| Computational scoring (docking, shape) | Wet-lab validation |
| Lightweight ML models / adapters | Training large generative models from scratch |
| Static + dynamic pocket analysis | Full MD simulations (>100ns) |
| Small molecule binders | Biologics, PROTACs, peptides |

## Stakeholders

- Primary: Portfolio / recruiting demonstration
- Secondary: Computational biology community (open-source contribution)

## Constraints

- All data must be publicly available
- All tools must be open-source or freely available for academic use
- Compute budget: single GPU or CPU-only workflows
- Timeline: phased delivery, each phase independently useful
