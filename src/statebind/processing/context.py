"""Context dataset builder: curated EGFR mutations with resistance annotations.

This module contains the v1 hand-curated mutation dataset. Every mutation
is sourced from published literature with PMIDs. No automated scraping —
manual curation ensures quality and traceability.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from statebind.processing.models import (
    ConformationalEffect,
    ConformationalState,
    ContextDataset,
    MechanismCategory,
    MutationRecord,
    Provenance,
    ResistanceGeneration,
)


def _v1_curated_mutations() -> list[MutationRecord]:
    """Return the v1 hand-curated EGFR mutation set.

    Sources:
    - Yun et al., PNAS 2008 (T790M structure)
    - Thress et al., Nat Med 2015 (C797S)
    - Jänne et al., NEJM 2015 (resistance landscape)
    - Kobayashi et al., NEJM 2005 (T790M discovery)
    - Pao et al., PLoS Med 2005 (secondary mutations)
    - Sordella et al., Science 2004 (L858R/exon19del mechanism)
    - Ramalingam et al., NEJM 2020 (osimertinib resistance)
    - Yosaatmadja et al., Struct 2015 (EGFR conformational states)
    - COSMIC database v99
    """
    return [
        # ── Activating mutations (the initial oncogenic drivers) ─────
        MutationRecord(
            mutation_id="L858R",
            position=858,
            wild_type="L",
            mutant="R",
            resistance_generation=ResistanceGeneration.ACTIVATING,
            mechanism_category=MechanismCategory.ACTIVATION_LOOP,
            conformational_effect=ConformationalEffect.DESTABILIZES_INACTIVE,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_affected=[],
            known_drugs_effective=["gefitinib", "erlotinib", "afatinib", "osimertinib"],
            pdb_structures=["2itv", "4i22", "2itz"],
            references=["PMID:15118073", "PMID:15329413"],
            notes="Most common EGFR activating mutation (~40% of EGFR-mutant NSCLC). "
                  "Destabilizes autoinhibitory conformation, shifts equilibrium to active state.",
            provenance=Provenance(sources=["manual", "cosmic"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="G719S",
            position=719,
            wild_type="G",
            mutant="S",
            resistance_generation=ResistanceGeneration.ACTIVATING,
            mechanism_category=MechanismCategory.P_LOOP,
            conformational_effect=ConformationalEffect.DESTABILIZES_INACTIVE,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_effective=["afatinib", "osimertinib"],
            pdb_structures=["2ito"],
            references=["PMID:16187797"],
            notes="Uncommon activating mutation (~3%). P-loop glycine substitution "
                  "disrupts inactive conformation.",
            provenance=Provenance(sources=["manual", "cosmic"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="L861Q",
            position=861,
            wild_type="L",
            mutant="Q",
            resistance_generation=ResistanceGeneration.ACTIVATING,
            mechanism_category=MechanismCategory.ACTIVATION_LOOP,
            conformational_effect=ConformationalEffect.DESTABILIZES_INACTIVE,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_effective=["afatinib", "osimertinib"],
            references=["PMID:16187797"],
            notes="Uncommon activating mutation (~2%). Activation loop.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="S768I",
            position=768,
            wild_type="S",
            mutant="I",
            resistance_generation=ResistanceGeneration.ACTIVATING,
            mechanism_category=MechanismCategory.AC_HELIX,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_effective=["afatinib", "osimertinib"],
            references=["PMID:16187797"],
            notes="Uncommon activating mutation. Near aC-helix.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),

        # ── 1st-generation resistance mutations ────────────────────
        MutationRecord(
            mutation_id="T790M",
            position=790,
            wild_type="T",
            mutant="M",
            resistance_generation=ResistanceGeneration.FIRST,
            mechanism_category=MechanismCategory.GATEKEEPER,
            conformational_effect=ConformationalEffect.STABILIZES_DFGIN,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_affected=["gefitinib", "erlotinib"],
            known_drugs_effective=["osimertinib"],
            pdb_structures=["2jit", "3w2o", "4i22"],
            references=["PMID:15737014", "PMID:18408761"],
            notes="Gatekeeper mutation. Bulky methionine sterically blocks 1st-gen TKIs. "
                  "Stabilizes hydrophobic spine, favoring active DFG-in conformation. "
                  "Present in ~50-60% of 1st/2nd-gen resistance cases.",
            provenance=Provenance(sources=["manual", "cosmic"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="D761Y",
            position=761,
            wild_type="D",
            mutant="Y",
            resistance_generation=ResistanceGeneration.FIRST,
            mechanism_category=MechanismCategory.AC_HELIX,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["gefitinib"],
            references=["PMID:18981003"],
            notes="Rare 1st-gen resistance mutation near aC-helix.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="T854A",
            position=854,
            wild_type="T",
            mutant="A",
            resistance_generation=ResistanceGeneration.FIRST,
            mechanism_category=MechanismCategory.HINGE,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["gefitinib", "erlotinib"],
            references=["PMID:18413839"],
            notes="Hinge region mutation. Disrupts critical H-bond to 1st-gen TKIs.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="L747S",
            position=747,
            wild_type="L",
            mutant="S",
            resistance_generation=ResistanceGeneration.FIRST,
            mechanism_category=MechanismCategory.P_LOOP,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["gefitinib", "erlotinib"],
            references=["PMID:23948351"],
            notes="P-loop resistance mutation. Less common.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),

        # ── 3rd-generation resistance mutations ────────────────────
        MutationRecord(
            mutation_id="C797S",
            position=797,
            wild_type="C",
            mutant="S",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.COVALENT_SITE,
            conformational_effect=ConformationalEffect.NO_DIRECT_CONFORMATIONAL,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_affected=["osimertinib"],
            known_drugs_effective=[],
            pdb_structures=["6lud"],
            references=["PMID:25948941"],
            notes="Eliminates cysteine required for osimertinib covalent binding. "
                  "No direct conformational effect, but forces non-covalent design strategy. "
                  "Most common osimertinib resistance mechanism (~10-26%).",
            provenance=Provenance(sources=["manual", "cosmic"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="G796D",
            position=796,
            wild_type="G",
            mutant="D",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.COVALENT_SITE,
            conformational_effect=ConformationalEffect.STERIC_CLASH,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:29571986"],
            notes="Adjacent to C797. Steric clash with osimertinib acrylamide warhead.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="L792H",
            position=792,
            wild_type="L",
            mutant="H",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.HINGE,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:29571986"],
            notes="Hinge region mutation causing osimertinib resistance.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="G724S",
            position=724,
            wild_type="G",
            mutant="S",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.P_LOOP,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            known_drugs_effective=["afatinib"],
            references=["PMID:30228210"],
            notes="P-loop mutation. Paradoxically sensitive to 2nd-gen TKIs.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),

        # ── Solvent front mutations ─────────────────────────────────
        MutationRecord(
            mutation_id="G796S",
            position=796,
            wild_type="G",
            mutant="S",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.SOLVENT_FRONT,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:29571986"],
            notes="Solvent front mutation near covalent binding site.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="G796R",
            position=796,
            wild_type="G",
            mutant="R",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.SOLVENT_FRONT,
            conformational_effect=ConformationalEffect.STERIC_CLASH,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:29571986"],
            notes="Bulky arginine at solvent front creates steric clash.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),

        # ── Compound resistance ─────────────────────────────────────
        MutationRecord(
            mutation_id="L718Q",
            position=718,
            wild_type="L",
            mutant="Q",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.P_LOOP,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:27979920"],
            notes="P-loop mutation conferring osimertinib resistance.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
        MutationRecord(
            mutation_id="L718V",
            position=718,
            wild_type="L",
            mutant="V",
            resistance_generation=ResistanceGeneration.THIRD,
            mechanism_category=MechanismCategory.P_LOOP,
            conformational_effect=ConformationalEffect.UNKNOWN,
            preferred_states=[],
            known_drugs_affected=["osimertinib"],
            references=["PMID:29571986"],
            notes="Alternative substitution at L718. P-loop.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),

        # ── 4th-gen / emerging ──────────────────────────────────────
        MutationRecord(
            mutation_id="L858R+T790M+C797S",
            position=858,  # Primary mutation position
            wild_type="L",
            mutant="R",
            resistance_generation=ResistanceGeneration.FOURTH,
            mechanism_category=MechanismCategory.OTHER,
            conformational_effect=ConformationalEffect.STABILIZES_ACTIVE,
            preferred_states=[ConformationalState.DFGIN_ACIN],
            known_drugs_affected=["gefitinib", "erlotinib", "osimertinib"],
            known_drugs_effective=[],
            references=["PMID:25948941"],
            notes="Triple mutant. No approved effective therapy. Represents the "
                  "ultimate resistance challenge. Active conformation strongly favored.",
            provenance=Provenance(sources=["manual"], processing_date="2026-03-14"),
        ),
    ]


def build_context_dataset(
    assign_splits: bool = True,
    split_seed: int = 42,
) -> ContextDataset:
    """Build the processed context dataset from curated mutations.

    Args:
        assign_splits: If True, assign train/val/test splits.
        split_seed: Random seed for reproducible splits.

    Returns:
        Populated ContextDataset.
    """
    mutations = _v1_curated_mutations()

    if assign_splits:
        mutations = _assign_splits(mutations, seed=split_seed)

    now = datetime.now(timezone.utc).isoformat()

    return ContextDataset(
        version="1.0.0",
        mutations=mutations,
        generated_at=now,
        processing_version="0.1.0",
    )


def _assign_splits(
    mutations: list[MutationRecord],
    seed: int = 42,
) -> list[MutationRecord]:
    """Assign train/val/test splits to mutations.

    Strategy: The 3 key mutations (T790M, L858R, C797S) go to test.
    Remaining mutations are split ~60/20/20 train/val/test by position hash.
    """
    key_test_mutations = {"T790M", "L858R", "C797S"}

    # First pass: assign by hash
    non_key = []
    for m in mutations:
        if m.mutation_id in key_test_mutations:
            m.split = "test"
        else:
            h = int(hashlib.md5(f"{m.mutation_id}:{seed}".encode()).hexdigest(), 16)
            bucket = h % 10
            if bucket < 6:
                m.split = "train"
            elif bucket < 8:
                m.split = "val"
            else:
                m.split = "test"
            non_key.append(m)

    # Guarantee at least 1 val and 1 train if enough non-key mutations
    splits = {m.split for m in non_key}
    if len(non_key) >= 3:
        if "val" not in splits:
            # Move the first train mutation to val
            for m in non_key:
                if m.split == "train":
                    m.split = "val"
                    break
        if "train" not in {m.split for m in non_key}:
            # Move the last test mutation to train (keep at least 1 test via key)
            for m in reversed(non_key):
                if m.split == "test":
                    m.split = "train"
                    break

    return mutations
