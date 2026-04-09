---
agent: Orchestrator
round: 2
date: 2026-04-08
type: roundtable
---

# Round 2 Synthesis: Proposals and Critical Revisions

## Executive Summary

Five formal proposals and two focused research notes were produced in Round 2. The
proposals are largely complementary and converge on a unified research agenda. However,
structbio's R02 research reveals a critical revision needed in the multi-kinase plan:
RET and JAK2 are structurally infeasible, and the 4-state model cannot be applied
uniformly. The recommended expansion set is ABL1 + BRAF + MET with a practical 3-state
model.

---

## The Five Proposals at a Glance

| ID | Title | Lead | Timeline | Compute | Key Contribution |
|----|-------|------|----------|---------|------------------|
| datasci-P01 | Multi-kinase validation + statistics | datasci | 6 weeks | 42 GPU-days | Statistical backbone |
| mlres-P01 | External baseline comparison | mlres | 3-4 weeks | 40 GPU-hrs | Reviewer requirement |
| medchem-P01 | Scoring revision (ADMET + selectivity) | medchem | 2-3 weeks | 200 GPU-hrs | Scoring credibility |
| synthbio-P01 | End-to-end drug-ability | synthbio | 3-4 weeks | <2 hrs | Publication differentiator |
| compchem-P01 | Physics validation (GIST + FEP) | compchem | 2-3 weeks | 5-7 GPU-days | Physics credibility |

**Total estimated timeline:** 6-8 weeks (proposals overlap significantly)
**Total estimated compute:** ~55 GPU-days (dominated by multi-kinase expansion)

---

## Critical Revision: Multi-Kinase Target Selection

structbio-R02 conducted detailed per-kinase structural feasibility assessment. The
results fundamentally change datasci-P01's kinase selection:

| Kinase | KinCore Chains | DFGout Coverage | All 4 States? | Feasibility |
|--------|----------------|-----------------|---------------|-------------|
| **ABL1** | 136 | 55 chains (40%) | Yes | **HIGH** |
| **BRAF** | 218 | 73 chains | Yes (7 states!) | **HIGH** |
| **MET** | 126 | Multiple | Yes (7 states!) | **HIGH** |
| ALK | 68 | 2 chains | No (no aCout) | LOW-MODERATE |
| RET | 38 | 0 chains | No (100% active) | **NOT FEASIBLE** |
| JAK2 | 61 | 0 chains (JH1) | No (100% DFGin) | **LOW** |

**Revised recommendation:** EGFR + ABL1 + BRAF + MET (4 kinases total)
- Drops RET and JAK2 (structurally impossible)
- ALK as optional stretch (limited DFGout)
- Yields ~18 held-out drugs (pre-2015 cutoff), exceeding N >= 15 threshold

**Additional structural finding:** The 4-state model cannot be applied uniformly. A
practical 3-state model (DFGin/aCin, DFGin/aCout, DFGout/aCin) works across all HIGH
feasibility kinases. The DFGout/aCout state is rare kinome-wide (~1%) and should be
treated as optional.

---

## Proposal Interactions and Dependencies

### Strong Synergies
1. **datasci-P01 + mlres-P01**: The ablation suite in datasci feeds directly into the
   baseline comparison in mlres. The unconditioned VAE ablation appears in both.
   Should be merged into a single experimental protocol.

2. **medchem-P01 + synthbio-P01**: Scoring revision adds ADMET to scoring; end-to-end
   adds retrosynthesis and PK. Together they create a comprehensive drug-ability scoring
   and assessment framework. RAscore from synthbio could be the 6th scoring component
   alongside medchem's proposed 5.

3. **compchem-P01 + structbio-R02**: GIST water analysis needs the right structures;
   ensemble docking needs multiple structures per state. structbio's KLIFS data provides
   the structural foundation.

### Tensions to Resolve
1. **Scoring revision vs fair comparison**: medchem-P01 proposes new weights; datasci-P01
   needs stable scoring across kinases. Resolution: lock original scoring for primary
   endpoint, report revised scoring as secondary analysis.

2. **Number of scoring components**: medchem adds ADMET + selectivity (6 components);
   synthbio adds RAscore (7 components). More components = more weight sensitivity
   concerns. Resolution: keep primary comparison at 4 components, show robustness at 6-7.

3. **3-state vs 4-state model**: structbio shows 3 states are practical across kinases;
   StateBind has 4 states for EGFR. Resolution: EGFR uses 4 states, other kinases use
   3 states, report both.

---

## Novelty Verification Update

genai-R02 exhaustively verified: **no published paper conditions generation on discrete
conformational states as of April 2026**. Closest work (Apo2Mol, DynamicFlow, CSDesign)
addresses adjacent but distinct problems. Patent landscape is clear.

**Time pressure identified:** Multiple groups (DynamicFlow, DynamicBind, Apo2Mol,
YuelDesign) are converging on protein dynamics in SBDD. StateBind should publish within
3-6 months before independent discovery.

---

## Round 3 Assignments: Cross-Domain Critique

Each proposal receives 2-3 reviewers from outside the proposing domain.

### datasci-P01 reviewers:
- **structbio**: Kinase feasibility (MUST incorporate R02 findings showing RET/JAK2 infeasible)
- **medchem**: Clinical appropriateness of kinase selection and reference molecules

### mlres-P01 reviewers:
- **genai**: Are baseline method choices current? Missing any critical comparisons?
- **datasci**: Is the statistical protocol rigorous? Multiple testing handled correctly?

### medchem-P01 reviewers:
- **datasci**: Does dual reporting prevent scoring manipulation? Statistical soundness?
- **compchem**: Physics perspective on scoring changes. Water/solvation missing?
- **synthbio**: Does ADMET integration design match end-to-end pipeline?

### synthbio-P01 reviewers:
- **medchem**: Clinical validity of ADMET thresholds and drug-ability criteria
- **mlres**: Publication impact assessment and integration with baseline comparison

### compchem-P01 reviewers:
- **structbio**: Structural soundness for MD setup. Crystal artifact concerns?
- **mlres**: Publication impact. Does physics validation move the needle for reviewers?
