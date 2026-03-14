# Data Sources

This document catalogues every public data source StateBind may consume, organized by category. Each entry specifies relevance, format, licensing, quality concerns, and whether it is required for v1.

---

## 1. Context Data (Mutations & Resistance)

### 1.1 COSMIC (Catalogue of Somatic Mutations in Cancer)

| Field | Detail |
|-------|--------|
| **URL** | https://cancer.sanger.ac.uk/cosmic |
| **Relevance** | Primary source for EGFR somatic mutation frequencies in human cancers. Links mutations to tumor type, tissue, and clinical annotation. |
| **Expected format** | TSV/CSV download (CosmicMutantExport) |
| **License** | Free for academic/non-commercial use. Requires registration. Redistribution restricted — we store only derived summaries, not raw COSMIC files. |
| **Quality concerns** | Contains many passenger mutations. Frequency counts are biased by sequencing study coverage. Not all mutations are functionally characterized. |
| **v1 status** | **Required** — primary mutation frequency source |
| **v1 subset** | EGFR gene only, missense mutations in kinase domain (residues 696–1022, EGFR numbering) |

### 1.2 ClinVar

| Field | Detail |
|-------|--------|
| **URL** | https://www.ncbi.nlm.nih.gov/clinvar/ |
| **Relevance** | Clinical significance annotations for EGFR variants. Links variants to pathogenicity, drug response, review status. |
| **Expected format** | XML or VCF download; also queryable via Entrez API |
| **License** | Public domain (NCBI) |
| **Quality concerns** | Variable submission quality. "Drug response" annotations are sparse for resistance mutations. Some entries lack functional evidence. |
| **v1 status** | **Required** — clinical annotation source |
| **v1 subset** | EGFR gene, variants with "drug response" or "pathogenic" clinical significance |

### 1.3 Published EGFR Resistance Reviews (Manual Curation)

| Field | Detail |
|-------|--------|
| **URL** | N/A — curated from literature |
| **Relevance** | Gold-standard mutation→mechanism→conformational effect mapping. Key papers: Yun et al. 2008 (T790M structure), Thress et al. 2015 (C797S), Jänne et al. 2015 (resistance landscape). |
| **Expected format** | Manual JSON curation by project author |
| **License** | Fair use of published scientific findings |
| **Quality concerns** | Manual curation is labor-intensive and may miss recent papers. Interpretations of conformational effects are sometimes debated. |
| **v1 status** | **Required** — provides conformational effect annotations that COSMIC/ClinVar lack |
| **v1 subset** | 15–30 mutations with documented resistance mechanism and conformational preference |

### 1.4 OncoKB

| Field | Detail |
|-------|--------|
| **URL** | https://www.oncokb.org/ |
| **Relevance** | Curated oncogenic/resistance annotations with drug-level evidence tiers. |
| **Expected format** | API (JSON) or TSV download |
| **License** | Free for academic use with attribution |
| **Quality concerns** | Focused on clinical actionability, not structural biology. May not annotate conformational effects. |
| **v1 status** | **Optional** — enriches resistance annotations but not required |
| **v1 subset** | EGFR resistance mutations with Level 1-3 evidence |

---

## 2. Structural Data (EGFR Conformations)

### 2.1 RCSB PDB

| Field | Detail |
|-------|--------|
| **URL** | https://www.rcsb.org/ |
| **Relevance** | Primary source for EGFR kinase domain crystal structures. Needed for conformational state classification, pocket extraction, and docking. |
| **Expected format** | PDB or mmCIF files; metadata via REST API (JSON) |
| **License** | Public domain (CC0) |
| **Quality concerns** | Resolution varies (1.5–3.5 Å). Some structures have missing loops, especially in the activation loop (DFG region). Crystal packing artifacts may bias conformation. Ligand-bound structures may trap non-physiological states. |
| **v1 status** | **Required** — core structural data source |
| **v1 subset** | Human EGFR kinase domain structures, resolution ≤3.0 Å, 30–80 structures across conformational states |

### 2.2 KLIFS (Kinase–Ligand Interaction Fingerprints and Structures)

| Field | Detail |
|-------|--------|
| **URL** | https://klifs.net/ |
| **Relevance** | Pre-classified kinase structures with DFG/αC-helix annotations. Provides standardized residue numbering and pocket definitions. Can serve as ground truth for our state classification. |
| **Expected format** | REST API (JSON), downloadable CSV, MOL2 pocket files |
| **License** | Free for academic use |
| **Quality concerns** | Classification may differ from our geometric criteria. Not all PDB structures are in KLIFS. |
| **v1 status** | **Required** — validation reference for state classification |
| **v1 subset** | EGFR entries with DFG and αC-helix annotations |

### 2.3 UniProt

| Field | Detail |
|-------|--------|
| **URL** | https://www.uniprot.org/ (P00533 for human EGFR) |
| **Relevance** | Canonical sequence, domain boundaries, variant annotations, cross-references to PDB. |
| **Expected format** | FASTA (sequence), JSON/XML (annotations) |
| **License** | CC BY 4.0 |
| **Quality concerns** | None significant — gold standard for sequence data. |
| **v1 status** | **Required** — reference sequence and domain boundaries |
| **v1 subset** | P00533, kinase domain (residues 696–1022) |

### 2.4 AlphaFold Protein Structure Database

| Field | Detail |
|-------|--------|
| **URL** | https://alphafold.ebi.ac.uk/ |
| **Relevance** | Predicted structure for EGFR. Useful only if PDB coverage is insufficient for a conformational state. |
| **Expected format** | mmCIF/PDB |
| **License** | CC BY 4.0 |
| **Quality concerns** | AlphaFold predicts a single conformation (typically active-like). Not useful for conformational diversity. pLDDT scores may be low in flexible regions. |
| **v1 status** | **Stretch** — only if a state has <2 PDB structures |
| **v1 subset** | AF-P00533 (human EGFR) |

---

## 3. Ligand Data (Known Binders & References)

### 3.1 ChEMBL

| Field | Detail |
|-------|--------|
| **URL** | https://www.ebi.ac.uk/chembl/ |
| **Relevance** | Largest public bioactivity database. EGFR has thousands of measured IC50/Ki values. Provides reference compounds for generation quality assessment. |
| **Expected format** | REST API (JSON), downloadable SDF/CSV |
| **License** | CC BY-SA 3.0 |
| **Quality concerns** | Assay heterogeneity (different cell lines, conditions). IC50 values not directly comparable across studies. Some SMILES have stereochemistry or salt issues. |
| **v1 status** | **Required** — reference ligand set for generation assessment |
| **v1 subset** | EGFR target (CHEMBL203), compounds with IC50 < 1 μM, single-protein assays only |

### 3.2 PDB Ligand Expo / Co-crystallized Ligands

| Field | Detail |
|-------|--------|
| **URL** | Extracted from PDB structures |
| **Relevance** | Ligands co-crystallized with EGFR structures. Gold standard for pocket validation — the ligand position defines the "true" binding site. |
| **Expected format** | SDF/MOL2 extracted from PDB entries |
| **License** | Public domain (part of PDB deposition) |
| **Quality concerns** | Some ligands are buffer molecules or crystallization artifacts, not true binders. Must filter by known EGFR inhibitors. |
| **v1 status** | **Required** — pocket validation |
| **v1 subset** | Ligands from EGFR co-crystal structures in our state atlas |

### 3.3 DrugBank

| Field | Detail |
|-------|--------|
| **URL** | https://go.drugbank.com/ |
| **Relevance** | Approved EGFR drugs with clinical annotations. Provides reference set of "successful" binders. |
| **Expected format** | SDF, XML |
| **License** | CC BY-NC 4.0 (academic use) |
| **Quality concerns** | Small set (only ~10 approved EGFR TKIs). |
| **v1 status** | **Optional** — small reference set |
| **v1 subset** | Approved EGFR TKIs (gefitinib, erlotinib, afatinib, osimertinib, etc.) |

### 3.4 ZINC (for baseline random molecules)

| Field | Detail |
|-------|--------|
| **URL** | https://zinc.docking.org/ |
| **Relevance** | Large library of purchasable, drug-like molecules. Used only for baseline B3 (random molecule comparison). |
| **Expected format** | SMILES (TSV) |
| **License** | Free for academic use |
| **Quality concerns** | Huge library. Must subsample carefully. |
| **v1 status** | **Stretch** — only for baseline B3 |
| **v1 subset** | 1,000 random drug-like SMILES (MW 200–500, logP 0–5) |

---

## Recommended v1 Data Bundle

The minimum data required to run the full v1 pipeline:

| Category | Source | Subset | Estimated size |
|----------|--------|--------|---------------|
| Context | COSMIC (derived summary) | EGFR kinase domain missense mutations | <1 MB |
| Context | ClinVar (derived summary) | EGFR drug-response variants | <1 MB |
| Context | Manual curation | 15–30 mutations with conformational annotations | <100 KB |
| Structure | RCSB PDB | 30–80 EGFR kinase domain structures | 50–200 MB |
| Structure | KLIFS | EGFR state classifications | <5 MB |
| Structure | UniProt | P00533 sequence + annotations | <1 MB |
| Ligands | ChEMBL (subset) | EGFR binders, IC50 < 1 μM | <10 MB |
| Ligands | PDB co-crystal ligands | Ligands from state atlas structures | <5 MB |

**Total estimated size: ~100–250 MB**

All raw data is downloaded to `data/raw/`, never modified in place. Processed derivatives go to `data/processed/`. Every file has a manifest entry with provenance.
