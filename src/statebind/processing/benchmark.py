"""Benchmark assembly: combine all datasets into a single benchmark package.

This module orchestrates the full benchmark build:
1. Build context, structure, and ligand datasets
2. Build mapping tables
3. Validate everything
4. Write to data/processed/benchmark/
5. Generate summary statistics
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from statebind.processing.context import build_context_dataset
from statebind.processing.ligands import build_ligand_dataset
from statebind.processing.mapping import build_mapping_tables
from statebind.processing.models import BenchmarkSummary
from statebind.processing.structures import build_structure_dataset
from statebind.processing.validation import validate_dataset


def assemble_benchmark(
    output_dir: Path,
    split_seed: int = 42,
    fail_on_error: bool = True,
) -> BenchmarkSummary:
    """Assemble the full v1 benchmark package.

    Builds all datasets, validates them, writes to output_dir, and returns
    a summary.

    Args:
        output_dir: Directory to write benchmark files to.
        split_seed: Random seed for train/val/test splits.
        fail_on_error: If True, raise on validation errors.

    Returns:
        BenchmarkSummary with dataset statistics.

    Raises:
        ValueError: If fail_on_error and validation errors are found.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build datasets
    context = build_context_dataset(assign_splits=True, split_seed=split_seed)
    structures = build_structure_dataset()
    ligands = build_ligand_dataset()
    mappings = build_mapping_tables(context, structures, ligands)

    # 2. Validate
    report = validate_dataset(
        context=context,
        structures=structures,
        ligands=ligands,
        mappings=mappings,
    )

    print(report.summary())

    if not report.is_valid and fail_on_error:
        raise ValueError(
            f"Benchmark validation failed with {len(report.errors)} errors. "
            f"Fix errors before assembly."
        )

    # 3. Write datasets
    _write_json(context.model_dump(mode="json"), output_dir / "context.json")
    _write_json(structures.model_dump(mode="json"), output_dir / "structures.json")
    _write_json(ligands.model_dump(mode="json"), output_dir / "ligands.json")
    _write_json(mappings.model_dump(mode="json"), output_dir / "mappings.json")

    # 4. Write CSV versions for easy inspection
    _write_context_csv(context, output_dir / "context.csv")
    _write_structures_csv(structures, output_dir / "structures.csv")
    _write_ligands_csv(ligands, output_dir / "ligands.csv")
    _write_mappings_csv(mappings, output_dir)

    # 5. Build summary
    now = datetime.now(timezone.utc).isoformat()
    summary = BenchmarkSummary(
        n_mutations=len(context.mutations),
        n_structures=len(structures.structures),
        n_ligands=len(ligands.ligands),
        n_mutation_structure_mappings=len(mappings.mutation_structure),
        n_structure_ligand_mappings=len(mappings.structure_ligand),
        states_represented=sorted(set(
            s.state.value for s in structures.structures
            if s.state.value != "unclassified"
        )),
        resistance_generations=sorted(set(
            m.resistance_generation.value for m in context.mutations
        )),
        mechanism_categories=sorted(set(
            m.mechanism_category.value for m in context.mutations
        )),
        split_counts={
            split: sum(1 for m in context.mutations if m.split == split)
            for split in ["train", "val", "test", "unassigned"]
        },
        generated_at=now,
        processing_version="0.1.0",
    )

    _write_json(summary.model_dump(mode="json"), output_dir / "summary.json")

    # 6. Write validation report
    with open(output_dir / "validation_report.txt", "w") as f:
        f.write(report.summary())

    return summary


def _write_json(data: dict, path: Path) -> None:
    """Write dict as formatted JSON."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _write_context_csv(context, path: Path) -> None:
    """Write context dataset as CSV for inspection."""
    import csv
    fields = [
        "mutation_id", "position", "wild_type", "mutant", "domain",
        "resistance_generation", "mechanism_category", "conformational_effect",
        "preferred_states", "known_drugs_affected", "known_drugs_effective",
        "pdb_structures", "split", "references",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in context.mutations:
            row = {
                "mutation_id": m.mutation_id,
                "position": m.position,
                "wild_type": m.wild_type,
                "mutant": m.mutant,
                "domain": m.domain,
                "resistance_generation": m.resistance_generation.value,
                "mechanism_category": m.mechanism_category.value,
                "conformational_effect": m.conformational_effect.value,
                "preferred_states": ";".join(s.value for s in m.preferred_states),
                "known_drugs_affected": ";".join(m.known_drugs_affected),
                "known_drugs_effective": ";".join(m.known_drugs_effective),
                "pdb_structures": ";".join(m.pdb_structures),
                "split": m.split,
                "references": ";".join(m.references),
            }
            writer.writerow(row)


def _write_structures_csv(structures, path: Path) -> None:
    """Write structure dataset as CSV."""
    import csv
    fields = [
        "pdb_id", "resolution", "state", "chain", "mutations_present",
        "ligand_id", "ligand_bound", "is_apo", "is_representative",
        "experimental_method", "is_predicted",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in structures.structures:
            writer.writerow({
                "pdb_id": s.pdb_id,
                "resolution": s.resolution,
                "state": s.state.value,
                "chain": s.chain,
                "mutations_present": ";".join(s.mutations_present),
                "ligand_id": s.ligand_id,
                "ligand_bound": s.ligand_bound,
                "is_apo": s.is_apo,
                "is_representative": s.is_representative,
                "experimental_method": s.experimental_method,
                "is_predicted": s.is_predicted,
            })


def _write_ligands_csv(ligands, path: Path) -> None:
    """Write ligand dataset as CSV."""
    import csv
    fields = [
        "ligand_id", "drug_name", "source", "canonical_smiles",
        "pIC50", "mw", "logp", "hbd", "hba",
        "pdb_id", "is_approved", "generation",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lig in ligands.ligands:
            writer.writerow({
                "ligand_id": lig.ligand_id,
                "drug_name": lig.drug_name,
                "source": lig.source.value,
                "canonical_smiles": lig.canonical_smiles,
                "pIC50": lig.pIC50 if lig.pIC50 is not None else "",
                "mw": lig.mw if lig.mw is not None else "",
                "logp": lig.logp if lig.logp is not None else "",
                "hbd": lig.hbd if lig.hbd is not None else "",
                "hba": lig.hba if lig.hba is not None else "",
                "pdb_id": lig.pdb_id,
                "is_approved": lig.is_approved,
                "generation": lig.generation,
            })


def _write_mappings_csv(mappings, output_dir: Path) -> None:
    """Write mapping tables as CSVs."""
    import csv

    with open(output_dir / "mapping_mutation_structure.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["mutation_id", "pdb_id", "chain", "state", "ligand_id"])
        writer.writeheader()
        for m in mappings.mutation_structure:
            writer.writerow({
                "mutation_id": m.mutation_id,
                "pdb_id": m.pdb_id,
                "chain": m.chain,
                "state": m.state.value,
                "ligand_id": m.ligand_id,
            })

    with open(output_dir / "mapping_structure_ligand.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pdb_id", "ligand_id", "chain"])
        writer.writeheader()
        for m in mappings.structure_ligand:
            writer.writerow({
                "pdb_id": m.pdb_id,
                "ligand_id": m.ligand_id,
                "chain": m.chain,
            })
