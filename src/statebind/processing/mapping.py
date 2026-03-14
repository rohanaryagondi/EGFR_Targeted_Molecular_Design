"""ID mapping: connect mutations, structures, and ligands.

Builds cross-reference tables from the individual datasets so downstream
modules can traverse mutation→structure→ligand relationships.
"""

from __future__ import annotations

from datetime import datetime, timezone

from statebind.processing.models import (
    ContextDataset,
    LigandDataset,
    MappingTables,
    MutationStructureMapping,
    StructureDataset,
    StructureLigandMapping,
)


def build_mapping_tables(
    context: ContextDataset,
    structures: StructureDataset,
    ligands: LigandDataset,
) -> MappingTables:
    """Build cross-reference tables from individual datasets.

    Creates:
    1. mutation_structure: links each mutation to PDB structures containing it
    2. structure_ligand: links each structure to its co-crystallized ligand

    Args:
        context: Processed context dataset.
        structures: Processed structure dataset.
        ligands: Processed ligand dataset.

    Returns:
        Populated MappingTables.
    """
    mut_struct_mappings: list[MutationStructureMapping] = []
    struct_lig_mappings: list[StructureLigandMapping] = []

    # Build a lookup of structure records by pdb_id
    struct_by_pdb = {s.pdb_id: s for s in structures.structures}

    # Build ligand lookup by ligand_id
    lig_ids = {lig.ligand_id for lig in ligands.ligands}

    # 1. Mutation → Structure mappings
    for mutation in context.mutations:
        for pdb_id in mutation.pdb_structures:
            struct = struct_by_pdb.get(pdb_id)
            if struct is not None:
                mut_struct_mappings.append(MutationStructureMapping(
                    mutation_id=mutation.mutation_id,
                    pdb_id=pdb_id,
                    chain=struct.chain,
                    state=struct.state,
                    ligand_id=struct.ligand_id,
                ))
            else:
                # Structure referenced by mutation but not in structure dataset
                # Still record the mapping with defaults
                mut_struct_mappings.append(MutationStructureMapping(
                    mutation_id=mutation.mutation_id,
                    pdb_id=pdb_id,
                ))

    # Also map structures that contain mutations in their mutations_present field
    for struct in structures.structures:
        for mut_id in struct.mutations_present:
            # Check if this mapping already exists
            exists = any(
                m.mutation_id == mut_id and m.pdb_id == struct.pdb_id
                for m in mut_struct_mappings
            )
            if not exists:
                mut_struct_mappings.append(MutationStructureMapping(
                    mutation_id=mut_id,
                    pdb_id=struct.pdb_id,
                    chain=struct.chain,
                    state=struct.state,
                    ligand_id=struct.ligand_id,
                ))

    # 2. Structure → Ligand mappings
    for struct in structures.structures:
        if struct.ligand_bound and struct.ligand_id:
            struct_lig_mappings.append(StructureLigandMapping(
                pdb_id=struct.pdb_id,
                ligand_id=struct.ligand_id,
                chain=struct.chain,
            ))

    now = datetime.now(timezone.utc).isoformat()

    return MappingTables(
        version="1.0.0",
        mutation_structure=mut_struct_mappings,
        structure_ligand=struct_lig_mappings,
        generated_at=now,
    )
