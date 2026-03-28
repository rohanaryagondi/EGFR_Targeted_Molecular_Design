"""Training data for the EGFR binding proxy.

Known binders: 9 FDA-approved or late-stage EGFR inhibitors with
literature-documented activity (pIC50 > 7).
Decoys: 25 drug-like molecules with no reported kinase activity.

IMPORTANT: This is a discriminative model, not a binding affinity predictor.
It separates EGFR-like molecules from random drug-like molecules.

Sources:
    Binder SMILES from ChEMBL / DrugBank canonical forms.
    Decoy SMILES from DrugBank canonical forms.
    The first three binders (erlotinib, gefitinib, osimertinib) use
    the exact SMILES from baselines/scoring.py:59-66 to ensure
    consistency with _REFERENCE_BINDERS.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrainingCompound:
    """A compound in the proxy training set."""

    smiles: str
    label: int  # 1 = EGFR binder, 0 = decoy
    name: str
    source: str  # literature citation or database ID
    notes: str = ""


# ── EGFR binders (label=1) ───────────────────────────────────────────────

EGFR_BINDERS: list[TrainingCompound] = [
    # 1st-generation reversible inhibitors
    TrainingCompound(
        "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
        1,
        "Erlotinib",
        "Moyer et al. 1997; ChEMBL553",
        "1st-gen reversible; matches _REFERENCE_BINDERS[0]",
    ),
    TrainingCompound(
        "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
        1,
        "Gefitinib",
        "Wakeling et al. 2002; ChEMBL939",
        "1st-gen reversible; matches _REFERENCE_BINDERS[1]",
    ),
    # 3rd-generation mutant-selective
    TrainingCompound(
        "COc1cc(N(C)CCN(C)C)c(NC(=O)/C=C/CN(C)C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
        1,
        "Osimertinib",
        "Cross et al. 2014; ChEMBL3353410",
        "3rd-gen T790M-selective; matches _REFERENCE_BINDERS[2]",
    ),
    # 2nd-generation irreversible pan-HER
    TrainingCompound(
        "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OC1CCOC1",
        1,
        "Afatinib",
        "Li et al. 2008; ChEMBL1173655",
        "2nd-gen irreversible pan-HER",
    ),
    TrainingCompound(
        "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
        1,
        "Lapatinib",
        "Rusnak et al. 2001; ChEMBL554",
        "Dual EGFR/HER2 reversible",
    ),
    TrainingCompound(
        "C#Cc1cccc(Nc2ncnc3cc(OC)c(OCCCN4CCOCC4)cc23)c1",
        1,
        "Dacomitinib",
        "Engelman et al. 2007; ChEMBL2110732",
        "2nd-gen irreversible pan-HER",
    ),
    TrainingCompound(
        "CCOc1cc2ncc(C#N)c(Nc3ccc(OCc4ccccn4)c(Cl)c3)c2cc1NC(=O)/C=C/CN(C)C",
        1,
        "Neratinib",
        "Rabindran et al. 2004; ChEMBL1374573",
        "2nd-gen irreversible pan-HER",
    ),
    TrainingCompound(
        "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3F)c2cc1OCCCN1CCOCC1",
        1,
        "Poziotinib",
        "Kim et al. 2012; ChEMBL3628670",
        "Exon20 insertion-selective",
    ),
    TrainingCompound(
        "COc1cc2c(Nc3ccc(Br)cc3F)ncnc2cc1OCC1CCN(C)CC1",
        1,
        "Vandetanib",
        "Wedge et al. 2002; ChEMBL24828",
        "Multi-kinase (EGFR/VEGFR/RET)",
    ),
]


# ── Decoys (label=0) ─────────────────────────────────────────────────────

DECOYS: list[TrainingCompound] = [
    TrainingCompound("CN(C)C(=N)NC(=N)N", 0, "Metformin", "DrugBank DB00331", "Antidiabetic biguanide"),
    TrainingCompound("CC(=O)Oc1ccccc1C(=O)O", 0, "Aspirin", "DrugBank DB00945", "NSAID"),
    TrainingCompound("CC(C)Cc1ccc(C(C)C(=O)O)cc1", 0, "Ibuprofen", "DrugBank DB01050", "NSAID"),
    TrainingCompound("CC(=O)Nc1ccc(O)cc1", 0, "Acetaminophen", "DrugBank DB00316", "Analgesic"),
    TrainingCompound("Cn1c(=O)c2c(ncn2C)n(C)c1=O", 0, "Caffeine", "DrugBank DB00201", "CNS stimulant"),
    TrainingCompound(
        "CC(C)NCC(O)c1ccc(O)c(O)c1",
        0,
        "Isoproterenol",
        "DrugBank DB01064",
        "Beta-adrenergic agonist",
    ),
    TrainingCompound(
        "COC(=O)C1=C(C)NC(C)=C(C(=O)OC)C1c1ccccc1[N+](=O)[O-]",
        0,
        "Nifedipine",
        "DrugBank DB01115",
        "Calcium channel blocker",
    ),
    TrainingCompound(
        "CC(C)(C)NCC(O)c1ccc(O)c(CO)c1",
        0,
        "Albuterol",
        "DrugBank DB01001",
        "Beta2-adrenergic agonist",
    ),
    TrainingCompound(
        "OC(=O)CC(O)(CC(=O)O)C(=O)O",
        0,
        "Citric acid",
        "DrugBank DB04272",
        "Metabolic acid",
    ),
    TrainingCompound(
        "CC12CCC3c4ccc(O)cc4CCC3C1CCC2O",
        0,
        "Estradiol",
        "DrugBank DB00783",
        "Steroidal estrogen",
    ),
    TrainingCompound(
        "CC(=O)OCC(=O)C1(O)CCC2C3CCC4=CC(=O)CCC4(C)C3C(O)CC21C",
        0,
        "Cortisone",
        "DrugBank DB00741",
        "Corticosteroid",
    ),
    TrainingCompound(
        "NCC(=O)O",
        0,
        "Glycine",
        "DrugBank DB00145",
        "Amino acid",
    ),
    TrainingCompound(
        "OC1C(O)C(O)C(O)C(O)C1O",
        0,
        "Inositol",
        "DrugBank DB00142",
        "Sugar alcohol",
    ),
    TrainingCompound(
        "CC(C)CC(=O)OC1CCC=C2C=CC(C)C(CCC3CC(O)CC(=O)O3)C21",
        0,
        "Lovastatin",
        "DrugBank DB00227",
        "HMG-CoA reductase inhibitor",
    ),
    TrainingCompound(
        "OC(=O)c1cccnc1",
        0,
        "Nicotinic acid",
        "DrugBank DB00627",
        "B vitamin",
    ),
    TrainingCompound(
        "Nc1ccc(S(N)(=O)=O)cc1",
        0,
        "Sulfanilamide",
        "DrugBank DB00259",
        "Sulfonamide antibiotic",
    ),
    TrainingCompound(
        "NCC1(CC(=O)O)CCCCC1",
        0,
        "Gabapentin",
        "DrugBank DB00996",
        "Anticonvulsant",
    ),
    TrainingCompound(
        "CC(C)(C)c1cc(O)c(O)c(C(C)(C)C)c1",
        0,
        "DTBHQ",
        "PubChem CID 16043",
        "Antioxidant (non-drug)",
    ),
    TrainingCompound(
        "O=C(O)c1cc(O)c(O)c(O)c1",
        0,
        "Gallic acid",
        "DrugBank DB04149",
        "Plant polyphenol",
    ),
    TrainingCompound(
        "CC(O)=O",
        0,
        "Acetic acid",
        "DrugBank DB03166",
        "Simple organic acid",
    ),
    TrainingCompound(
        "CC(C)(O)C(=O)O",
        0,
        "Mevalonic acid",
        "PubChem CID 439230",
        "Cholesterol biosynthesis intermediate",
    ),
    TrainingCompound(
        "OC(=O)/C=C/c1ccccc1",
        0,
        "Cinnamic acid",
        "DrugBank DB15896",
        "Plant-derived phenylpropanoid",
    ),
    TrainingCompound(
        "OC(=O)CCC(=O)O",
        0,
        "Succinic acid",
        "DrugBank DB00139",
        "TCA cycle intermediate",
    ),
    TrainingCompound(
        "NC(=O)c1cccnc1",
        0,
        "Nicotinamide",
        "DrugBank DB02701",
        "B3 vitamin",
    ),
    TrainingCompound(
        "c1ccc2[nH]ccc2c1",
        0,
        "Indole",
        "PubChem CID 798",
        "Simple heterocycle (non-drug)",
    ),
]


def get_training_data() -> tuple[list[str], list[int]]:
    """Return (smiles_list, label_list) for model training.

    Combines EGFR_BINDERS (label=1) and DECOYS (label=0) into flat lists.
    """
    all_compounds = EGFR_BINDERS + DECOYS
    smiles_list = [c.smiles for c in all_compounds]
    label_list = [c.label for c in all_compounds]
    return smiles_list, label_list
