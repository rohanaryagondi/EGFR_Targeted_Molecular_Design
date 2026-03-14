"""Dataset validation: null checks, duplicate checks, schema integrity.

Every processed dataset must pass validation before being written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.processing.models import (
    BenchmarkSummary,
    ContextDataset,
    LigandDataset,
    MappingTables,
    StructureDataset,
)


@dataclass
class ValidationIssue:
    """A single validation issue."""

    level: str  # "error" or "warning"
    dataset: str  # "context", "structures", "ligands", "mappings"
    field: str
    message: str


@dataclass
class DatasetValidationReport:
    """Aggregated validation results for processed datasets."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, level: str, dataset: str, field_name: str, message: str) -> None:
        self.issues.append(ValidationIssue(
            level=level, dataset=dataset, field=field_name, message=message,
        ))

    def summary(self) -> str:
        lines = [f"Dataset Validation: {'PASS' if self.is_valid else 'FAIL'}"]
        lines.append(f"  Errors:   {len(self.errors)}")
        lines.append(f"  Warnings: {len(self.warnings)}")
        for issue in self.issues:
            prefix = "ERROR" if issue.level == "error" else "WARN "
            lines.append(f"  [{prefix}] {issue.dataset}.{issue.field}: {issue.message}")
        return "\n".join(lines)


def validate_dataset(
    context: ContextDataset | None = None,
    structures: StructureDataset | None = None,
    ligands: LigandDataset | None = None,
    mappings: MappingTables | None = None,
) -> DatasetValidationReport:
    """Validate processed datasets for integrity.

    Checks:
    - No null/empty required fields
    - No duplicate IDs
    - Required columns present
    - Split integrity (if splits assigned)
    - Cross-dataset reference integrity
    - Provenance completeness

    Args:
        context: Context dataset to validate.
        structures: Structure dataset to validate.
        ligands: Ligand dataset to validate.
        mappings: Mapping tables to validate.

    Returns:
        DatasetValidationReport with all issues found.
    """
    report = DatasetValidationReport()

    if context is not None:
        _validate_context(context, report)
    if structures is not None:
        _validate_structures(structures, report)
    if ligands is not None:
        _validate_ligands(ligands, report)
    if mappings is not None:
        _validate_mappings(mappings, context, structures, report)

    return report


def _validate_context(ctx: ContextDataset, report: DatasetValidationReport) -> None:
    """Validate context dataset."""

    if len(ctx.mutations) == 0:
        report.add("error", "context", "mutations", "No mutations in dataset")
        return

    # Duplicate ID check
    ids = [m.mutation_id for m in ctx.mutations]
    dupes = [mid for mid in ids if ids.count(mid) > 1]
    if dupes:
        report.add("error", "context", "mutation_id", f"Duplicate IDs: {set(dupes)}")

    # Required field checks
    for m in ctx.mutations:
        if not m.mutation_id:
            report.add("error", "context", "mutation_id", "Empty mutation_id")
        if not m.wild_type or len(m.wild_type) != 1:
            report.add("error", "context", "wild_type",
                        f"Invalid wild_type '{m.wild_type}' for {m.mutation_id}")
        if not m.mutant or len(m.mutant) != 1:
            report.add("error", "context", "mutant",
                        f"Invalid mutant '{m.mutant}' for {m.mutation_id}")
        if m.position <= 0:
            report.add("error", "context", "position",
                        f"Invalid position {m.position} for {m.mutation_id}")

        # Check position is in kinase domain
        if not (ctx.kinase_domain_start <= m.position <= ctx.kinase_domain_end):
            # Compound mutations may have position of primary mutation
            if "+" not in m.mutation_id:
                report.add("warning", "context", "position",
                            f"{m.mutation_id} position {m.position} outside kinase domain "
                            f"({ctx.kinase_domain_start}-{ctx.kinase_domain_end})")

        # Provenance check
        if not m.provenance.sources:
            report.add("warning", "context", "provenance",
                        f"No provenance sources for {m.mutation_id}")

    # Key mutations must be present
    key_mutations = {"T790M", "L858R", "C797S"}
    present = {m.mutation_id for m in ctx.mutations}
    missing_key = key_mutations - present
    if missing_key:
        report.add("error", "context", "key_mutations",
                    f"Missing key mutations: {missing_key}")

    # Split integrity
    splits = {m.split for m in ctx.mutations}
    assigned = [m for m in ctx.mutations if m.split != "unassigned"]
    if assigned:
        split_counts = {}
        for m in ctx.mutations:
            split_counts[m.split] = split_counts.get(m.split, 0) + 1
        if "test" not in split_counts:
            report.add("warning", "context", "splits", "No test split mutations")


def _validate_structures(structs: StructureDataset, report: DatasetValidationReport) -> None:
    """Validate structure dataset."""

    if len(structs.structures) == 0:
        report.add("error", "structures", "structures", "No structures in dataset")
        return

    # Duplicate PDB ID check
    ids = [s.pdb_id for s in structs.structures]
    dupes = [sid for sid in ids if ids.count(sid) > 1]
    if dupes:
        report.add("error", "structures", "pdb_id", f"Duplicate PDB IDs: {set(dupes)}")

    for s in structs.structures:
        if not s.pdb_id or len(s.pdb_id) != 4:
            report.add("error", "structures", "pdb_id",
                        f"Invalid PDB ID: '{s.pdb_id}'")
        if s.resolution <= 0 and not s.is_predicted:
            report.add("warning", "structures", "resolution",
                        f"Non-positive resolution for {s.pdb_id}")
        if not s.provenance.sources:
            report.add("warning", "structures", "provenance",
                        f"No provenance for {s.pdb_id}")

    # Check state coverage
    from statebind.processing.models import ConformationalState
    states = {s.state for s in structs.structures}
    states.discard(ConformationalState.UNCLASSIFIED)
    if len(states) < 2:
        report.add("warning", "structures", "state_coverage",
                    f"Only {len(states)} conformational states represented")

    # Check for representatives
    reps = [s for s in structs.structures if s.is_representative]
    if len(reps) == 0:
        report.add("warning", "structures", "representative",
                    "No representative structures designated")


def _validate_ligands(ligs: LigandDataset, report: DatasetValidationReport) -> None:
    """Validate ligand dataset."""

    if len(ligs.ligands) == 0:
        report.add("error", "ligands", "ligands", "No ligands in dataset")
        return

    # Duplicate ID check
    ids = [lig.ligand_id for lig in ligs.ligands]
    dupes = [lid for lid in ids if ids.count(lid) > 1]
    if dupes:
        report.add("error", "ligands", "ligand_id", f"Duplicate IDs: {set(dupes)}")

    for lig in ligs.ligands:
        if not lig.ligand_id:
            report.add("error", "ligands", "ligand_id", "Empty ligand_id")
        if not lig.provenance.sources:
            report.add("warning", "ligands", "provenance",
                        f"No provenance for {lig.ligand_id}")

    # Check for approved drugs
    approved = [lig for lig in ligs.ligands if lig.is_approved]
    if len(approved) == 0:
        report.add("warning", "ligands", "approved",
                    "No approved drugs in dataset")


def _validate_mappings(
    mappings: MappingTables,
    context: ContextDataset | None,
    structures: StructureDataset | None,
    report: DatasetValidationReport,
) -> None:
    """Validate mapping table integrity."""

    if context is not None:
        mut_ids = {m.mutation_id for m in context.mutations}
        for mapping in mappings.mutation_structure:
            if mapping.mutation_id not in mut_ids:
                # Check compound mutation components
                components = mapping.mutation_id.split("+") if "+" in mapping.mutation_id else []
                if not components:
                    report.add("warning", "mappings", "mutation_structure",
                                f"Mutation '{mapping.mutation_id}' in mapping but not in context")

    if structures is not None:
        struct_ids = {s.pdb_id for s in structures.structures}
        for mapping in mappings.structure_ligand:
            if mapping.pdb_id not in struct_ids:
                report.add("warning", "mappings", "structure_ligand",
                            f"PDB '{mapping.pdb_id}' in mapping but not in structures")
