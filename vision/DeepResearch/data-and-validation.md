# Deep Research Briefing: Data Sources, Benchmarks & Validation Frameworks

**Agent mission:** Map the data landscape for expanding StateBind beyond EGFR to multiple
kinase families, and identify the validation frameworks and benchmark standards required
for publication at a top venue (Nature Computational Science, JCIM, Nature Methods).

**Read only this file.** It contains all the project context you need.

---

## 1. What StateBind Is

StateBind is a computational biology pipeline that tests whether **conformational
state-aware molecular design outperforms static single-structure design** for
kinase-targeted small molecules. It currently focuses exclusively on EGFR.

EGFR has 4 conformational states defined by two structural switches (DFG motif
in/out x alphaC helix in/out). Each state presents a different binding pocket.
The pipeline generates molecules conditioned on these states and compares results
against a single-structure static baseline.

### Current Data Assets

| Data | Source | Size | Notes |
|------|--------|------|-------|
| EGFR binding affinity | ChEMBL (CHEMBL203) | 10,466 compounds with pIC50 | Used to train MPNN affinity predictor |
| EGFR active SMILES | ChEMBL (IC50 < 10 uM) | 8,109 train / 2,027 val | Used to train SELFIES VAE |
| ADMET endpoints | TDC benchmarks | 27,698 molecules, 6 endpoints | hERG, CYP3A4, Caco-2, clearance, lipophilicity, solubility |
| EGFR PDB structures | PDB | 4 representatives (1M17, 2GS7, 3W2R, 4ZAU) | One per conformational state, prepared as PDBQT for GNINA |
| EGFR mutations | COSMIC, ClinVar, literature | 18 mutations curated | All map to DFGin/aCin state (limitation) |
| Reference drugs | Literature | 3 (erlotinib, gefitinib, osimertinib) | Used for similarity scoring (35% weight) |
| Pre-cutoff datasets | ChEMBL with date filter | 2,974 (pre-2010), 4,852 (pre-2015) | Used for retrospective validation, leakage-verified |

### Current Pipeline Results

**Head-to-head (EGFR only):**
- Static baseline: 30 candidates, mean score 0.5437, diversity 0.5684
- State-aware: 461 candidates, mean score 0.4378, diversity 0.9056, 431 novel molecules
- Static wins on mean score (p<0.001); state-aware wins on diversity (59% higher) and candidate count (15x)

**Retrospective time-split validation (strongest signal):**

| Cutoff | Held-Out Drugs | State-Aware EF@10 | Static EF@10 | Ratio |
|--------|---------------|-------------------|-------------|-------|
| 2010 | afatinib, osimertinib, dacomitinib, lazertinib, mobocertinib | 4.95 | 0.47 | 10.5x |
| 2015 | dacomitinib, lazertinib, mobocertinib | 7.72 | 0.79 | 9.8x |

All held-out drugs found. VAE novelty = 0.99. Pre-cutoff models retrained from
scratch on time-restricted data (no data leakage).

### ML Models

| Model | Architecture | Training Data | Key Metrics |
|-------|-------------|---------------|-------------|
| SELFIES VAE | GRU, 64D latent, state-conditioned | 8,109 EGFR SMILES | 99.9% valid, 94.8% unique |
| Affinity MPNN | NNConv, 12.7M params | 10,466 ChEMBL EGFR | RMSE=0.7182, Pearson=0.8323 |
| ADMET | GIN, 6 task heads, 187K params | 27,698 TDC molecules | hERG AUROC=0.7745 |
| GNINA | Physics-based (Vina+CNN) | N/A (physics) | Binders -7.32 vs non-binders -4.16 kcal/mol |

---

## 2. The Generalizability Problem

StateBind's results apply to EGFR only. The 10x enrichment is computed against
3-5 held-out approved drugs -- the entire population of approved EGFR-targeted
small molecules. The sample cannot be enlarged within EGFR.

**To make this publication-worthy, we need to show the approach generalizes across
multiple kinase families.** The architecture is target-agnostic -- it needs only:
1. Conformational state classifications for the target kinase
2. ChEMBL bioactivity data for training
3. PDB structures per state for docking
4. Approved drugs for retrospective validation

If we can replicate the 10x enrichment on 3-5 additional kinase targets, the
statistical power and generalizability claims become dramatically stronger.

---

## 3. Current Limitations Relevant to This Research

### 3.1 EGFR-Only

All results are for one kinase. No cross-target validation. Reviewers will ask:
"Does this work for other kinases, or is this an EGFR-specific artifact?"

### 3.2 Small Validation Sample

Enrichment factors computed against 3-5 drugs. A single rank change swings EF
substantially. Confidence intervals are wide.

### 3.3 No SOTA Method Benchmarking

No comparison against published molecular generation methods (REINVENT, DrugEx,
Pocket2Mol, etc.). No standardized benchmark datasets used. Reviewers will demand
contextualization against existing methods.

### 3.4 Reference Similarity Bias

The heaviest scoring component (35% weight) uses only 3 reference drugs. Expanding
to all ChEMBL EGFR actives (thousands with IC50 < 100 nM) would provide more diverse
reference set covering multiple binding modes.

### 3.5 No Clinical Outcome Connection

Pipeline generates and scores candidates computationally. No connection to clinical
efficacy, resistance mechanisms, or patient outcomes. Even retrospective validation
uses approval date, not clinical response data.

---

## 4. Research Questions

Answer each question with **specific, concrete data**: database names, URLs, exact
counts, data formats, access requirements, and your assessment of data quality and
completeness.

### Q1: KLIFS Kinase-Ligand Interaction Fingerprint Database

KLIFS (Kinase-Ligand Interaction Fingerprints and Structures) is potentially the most
important database for our expansion. Research thoroughly:
- What conformational state classifications does KLIFS use? How do they map to our
  DFG in/out x alphaC in/out scheme?
- How many kinase structures are in KLIFS total? How many per kinase family?
- Does KLIFS provide pre-classified conformational states per structure?
- What interaction fingerprint data is available?
- API access, data formats, download options
- Are there companion tools (e.g., KinaseMD, CORAL, KiSSim) that extend KLIFS?

### Q2: Multi-Kinase PDB Structure Availability Per Conformational State

For each of the following kinase targets, determine:
- How many PDB crystal structures exist?
- How many structures per conformational state (DFGin/aCin, DFGin/aCout, DFGout/aCin, DFGout/aCout)?
- What resolution ranges are available?
- Are there representative high-quality structures suitable for docking per state?

**Kinase targets to investigate:**
- ALK (Anaplastic Lymphoma Kinase)
- BRAF (B-Raf proto-oncogene)
- ABL1 (Abelson tyrosine kinase, BCR-ABL)
- MET (Hepatocyte growth factor receptor)
- RET (Rearranged during transfection)
- ROS1 (Proto-oncogene tyrosine-protein kinase)
- FGFR1/2/3 (Fibroblast growth factor receptors)
- SRC (Proto-oncogene tyrosine-protein kinase Src)
- KIT (Mast/stem cell growth factor receptor)
- FLT3 (FMS-like tyrosine kinase 3)
- JAK2 (Janus kinase 2)
- CDK4/6 (Cyclin-dependent kinases)

### Q3: Multi-Kinase ChEMBL Bioactivity Data Availability

For each kinase target listed in Q2:
- How many compounds with binding affinity data (IC50 or Ki) exist in ChEMBL?
- What is the ChEMBL target ID?
- What pIC50 range is covered?
- Are there enough compounds (>2,000) for training an MPNN affinity predictor?
- What is the temporal distribution (how many pre-2010, pre-2015)?

### Q4: Approved Kinase Inhibitor Timeline for Retrospective Validation

For each kinase target listed in Q2:
- List ALL FDA-approved small molecule inhibitors
- Include: drug name, approval year, target(s), generation, mechanism (type I/II/III)
- How many drugs would be held out at each time cutoff (2010, 2015)?
- Are there enough held-out drugs (>=3) for meaningful enrichment factors?

This is critical: we need targets where >=3 drugs were approved after our training
data cutoff to compute enrichment factors.

### Q5: Benchmark Datasets for Molecular Generation

What standardized benchmark datasets should we use and report results on?
- MOSES (Molecular Sets) -- metrics, baselines, how to run
- GuacaMol -- metrics, baselines, how to run
- Therapeutics Data Commons (TDC) -- which benchmarks are most relevant?
- CrossDocked2020 -- for 3D generation benchmarking
- PDBbind -- for binding affinity benchmarking
- DUD-E -- for virtual screening benchmarking
- CASF -- for scoring function benchmarking
- Practical Molecular Optimization (PMO) benchmark
- For each: what are the standard metrics, what baselines exist, what do top methods achieve?

### Q6: Published Temporal/Retrospective Validation Methodologies

How do top papers validate drug discovery pipelines without wet-lab data?
- Time-split validation approaches (what cutoff years are standard?)
- Enrichment factor computation standards (EF@1%, EF@5%, EF@10%?)
- Bootstrap confidence intervals for enrichment factors
- Cross-target transfer as validation
- Virtual screening benchmarks (DUD-E, MUV, LIT-PCBA)
- What do Nature Methods / Nature Comp Sci / JCIM specifically require?
- What are examples of highly-cited papers that used retrospective-only validation?

### Q7: Clinical Outcome Data for Kinase Inhibitors

Is there data connecting molecular features to clinical response?
- Clinical trial databases with molecular features (NCT, TCGA, cBioPortal)
- Resistance mutation databases (COSMIC, OncoKB)
- Duration of response data for approved kinase inhibitors
- Pharmacogenomic data linking drug structure to patient outcomes
- Any published datasets connecting in-silico predictions to clinical efficacy?

### Q8: Multi-Kinase Selectivity Datasets

What datasets exist for training selectivity models?
- KINOMEscan / DiscoverX kinase panel data
- Published kinase selectivity matrices
- ChEMBL cross-target activity data
- How many compounds have been tested against multiple kinases?
- Selectivity entropy (Ssel) reference values for approved kinase inhibitors

### Q9: Conformational State Databases Beyond KLIFS

Are there other databases or resources that classify kinase conformational states?
- KinaseMD (Kinase Mutation and Drug response)
- CORAL (COnformational classification using Random forest ALgorithm)
- KiSSim (Kinase Structural Similarity)
- Dunbrack kinase classification
- MD simulation trajectory databases (GPCRmd-like for kinases?)
- AlphaFold Protein Structure Database -- does it contain multiple conformations?

### Q10: Data Quality and Completeness Assessment

For the most promising 3-5 kinase targets for expansion (based on your Q2-Q4 answers):
- Is the data sufficient to replicate our full pipeline?
- What gaps exist (missing states, insufficient compounds, too few approved drugs)?
- What is the most realistic expansion plan?
- Rank the targets by: data availability, number of approved drugs, conformational diversity

---

## 5. Output Format

For each question, provide:
1. **Summary** (2-3 sentences: what exists and your assessment)
2. **Specific data** — exact counts, URLs, database names, access methods
3. **Recommendation for StateBind** — which databases/datasets are highest priority
4. **Data gaps** — what's missing or incomplete, and how to work around it
