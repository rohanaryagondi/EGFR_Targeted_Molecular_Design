"""Tests for the processing layer: dataset builders, validation, benchmark assembly."""

from pathlib import Path

import pytest

from statebind.processing.context import build_context_dataset
from statebind.processing.structures import build_structure_dataset
from statebind.processing.ligands import build_ligand_dataset
from statebind.processing.mapping import build_mapping_tables
from statebind.processing.validation import validate_dataset, DatasetValidationReport
from statebind.processing.benchmark import assemble_benchmark
from statebind.processing.models import (
    ConformationalState,
    ContextDataset,
    LigandDataset,
    MechanismCategory,
    MutationRecord,
    ResistanceGeneration,
    StructureDataset,
    BenchmarkSummary,
)


# ── Context Dataset Tests ───────────────────────────────────────────────


class TestContextDataset:
    def test_build_returns_dataset(self):
        ds = build_context_dataset()
        assert isinstance(ds, ContextDataset)
        assert len(ds.mutations) > 0

    def test_minimum_mutation_count(self):
        ds = build_context_dataset()
        assert len(ds.mutations) >= 15, f"Only {len(ds.mutations)} mutations, need >= 15"

    def test_key_mutations_present(self):
        ds = build_context_dataset()
        ids = {m.mutation_id for m in ds.mutations}
        assert "T790M" in ids
        assert "L858R" in ids
        assert "C797S" in ids

    def test_no_duplicate_ids(self):
        ds = build_context_dataset()
        ids = [m.mutation_id for m in ds.mutations]
        assert len(ids) == len(set(ids)), f"Duplicates: {[x for x in ids if ids.count(x) > 1]}"

    def test_all_mutations_have_valid_fields(self):
        ds = build_context_dataset()
        for m in ds.mutations:
            assert m.mutation_id, "Empty mutation_id"
            assert len(m.wild_type) == 1, f"Bad wild_type: {m.wild_type}"
            assert len(m.mutant) == 1 or "+" in m.mutation_id, f"Bad mutant: {m.mutant}"
            assert m.position > 0, f"Bad position: {m.position}"

    def test_splits_assigned(self):
        ds = build_context_dataset(assign_splits=True)
        splits = {m.split for m in ds.mutations}
        assert "unassigned" not in splits, "Some mutations not assigned a split"
        assert "test" in splits, "No test split"

    def test_key_mutations_in_test_split(self):
        ds = build_context_dataset(assign_splits=True)
        test_ids = {m.mutation_id for m in ds.mutations if m.split == "test"}
        assert "T790M" in test_ids
        assert "L858R" in test_ids
        assert "C797S" in test_ids

    def test_split_deterministic(self):
        ds1 = build_context_dataset(assign_splits=True, split_seed=42)
        ds2 = build_context_dataset(assign_splits=True, split_seed=42)
        for m1, m2 in zip(ds1.mutations, ds2.mutations):
            assert m1.split == m2.split, f"Non-deterministic split for {m1.mutation_id}"

    def test_provenance_present(self):
        ds = build_context_dataset()
        for m in ds.mutations:
            assert len(m.provenance.sources) > 0, f"No provenance for {m.mutation_id}"

    def test_t790m_annotations(self):
        ds = build_context_dataset()
        t790m = next(m for m in ds.mutations if m.mutation_id == "T790M")
        assert t790m.resistance_generation == ResistanceGeneration.FIRST
        assert t790m.mechanism_category == MechanismCategory.GATEKEEPER
        assert len(t790m.pdb_structures) > 0
        assert len(t790m.references) > 0


# ── Structure Dataset Tests ─────────────────────────────────────────────


class TestStructureDataset:
    def test_build_returns_dataset(self):
        ds = build_structure_dataset()
        assert isinstance(ds, StructureDataset)
        assert len(ds.structures) > 0

    def test_no_duplicate_pdb_ids(self):
        ds = build_structure_dataset()
        ids = [s.pdb_id for s in ds.structures]
        assert len(ids) == len(set(ids))

    def test_all_four_states_represented(self):
        ds = build_structure_dataset()
        states = {s.state for s in ds.structures}
        expected = {
            ConformationalState.DFGIN_ACIN,
            ConformationalState.DFGIN_ACOUT,
            ConformationalState.DFGOUT_ACIN,
            ConformationalState.DFGOUT_ACOUT,
        }
        assert expected.issubset(states), f"Missing states: {expected - states}"

    def test_pdb_ids_are_4_chars_lowercase(self):
        ds = build_structure_dataset()
        for s in ds.structures:
            assert len(s.pdb_id) == 4, f"PDB ID not 4 chars: {s.pdb_id}"
            assert s.pdb_id == s.pdb_id.lower(), f"PDB ID not lowercase: {s.pdb_id}"

    def test_representatives_exist(self):
        ds = build_structure_dataset()
        reps = [s for s in ds.structures if s.is_representative]
        assert len(reps) >= 3, f"Only {len(reps)} representatives"

    def test_apo_structure_has_no_ligand(self):
        ds = build_structure_dataset()
        apo = [s for s in ds.structures if s.is_apo]
        for s in apo:
            assert not s.ligand_bound, f"Apo structure {s.pdb_id} marked ligand_bound"

    def test_mutant_structures_have_mutations(self):
        ds = build_structure_dataset()
        for s in ds.structures:
            if s.mutations_present:
                assert all(len(m) >= 3 for m in s.mutations_present)


# ── Ligand Dataset Tests ────────────────────────────────────────────────


class TestLigandDataset:
    def test_build_returns_dataset(self):
        ds = build_ligand_dataset()
        assert isinstance(ds, LigandDataset)
        assert len(ds.ligands) > 0

    def test_no_duplicate_ids(self):
        ds = build_ligand_dataset()
        ids = [lig.ligand_id for lig in ds.ligands]
        assert len(ids) == len(set(ids))

    def test_approved_drugs_present(self):
        ds = build_ligand_dataset()
        approved = [lig for lig in ds.ligands if lig.is_approved]
        assert len(approved) >= 3, "Need at least gefitinib, erlotinib, osimertinib"

    def test_approved_drugs_have_smiles(self):
        ds = build_ligand_dataset()
        for lig in ds.ligands:
            if lig.is_approved:
                assert lig.canonical_smiles, f"No SMILES for approved drug {lig.ligand_id}"

    def test_osimertinib_present(self):
        ds = build_ligand_dataset()
        osi = next((lig for lig in ds.ligands if lig.ligand_id == "osimertinib"), None)
        assert osi is not None
        assert osi.is_approved
        assert osi.generation == "3rd"


# ── Mapping Tests ───────────────────────────────────────────────────────


class TestMappingTables:
    def test_build_mappings(self):
        ctx = build_context_dataset()
        structs = build_structure_dataset()
        ligs = build_ligand_dataset()
        mappings = build_mapping_tables(ctx, structs, ligs)
        assert len(mappings.mutation_structure) > 0
        assert len(mappings.structure_ligand) > 0

    def test_t790m_maps_to_structures(self):
        ctx = build_context_dataset()
        structs = build_structure_dataset()
        ligs = build_ligand_dataset()
        mappings = build_mapping_tables(ctx, structs, ligs)
        t790m_structs = [m.pdb_id for m in mappings.mutation_structure if m.mutation_id == "T790M"]
        assert len(t790m_structs) > 0, "T790M has no structure mappings"

    def test_structure_ligand_mappings_for_bound(self):
        ctx = build_context_dataset()
        structs = build_structure_dataset()
        ligs = build_ligand_dataset()
        mappings = build_mapping_tables(ctx, structs, ligs)
        # Every ligand-bound structure should have a mapping
        bound = [s for s in structs.structures if s.ligand_bound]
        mapped_pdbs = {m.pdb_id for m in mappings.structure_ligand}
        for s in bound:
            assert s.pdb_id in mapped_pdbs, f"Bound structure {s.pdb_id} not in mappings"


# ── Validation Tests ────────────────────────────────────────────────────


class TestValidation:
    def test_full_validation_passes(self):
        ctx = build_context_dataset()
        structs = build_structure_dataset()
        ligs = build_ligand_dataset()
        mappings = build_mapping_tables(ctx, structs, ligs)
        report = validate_dataset(ctx, structs, ligs, mappings)
        assert report.is_valid, f"Validation failed:\n{report.summary()}"

    def test_empty_context_fails(self):
        ctx = ContextDataset(mutations=[])
        report = validate_dataset(context=ctx)
        assert not report.is_valid

    def test_duplicate_mutation_id_fails(self):
        m = MutationRecord(mutation_id="X1Y", position=1, wild_type="X", mutant="Y")
        ctx = ContextDataset(mutations=[m, m])
        report = validate_dataset(context=ctx)
        assert not report.is_valid
        assert any("Duplicate" in e.message for e in report.errors)

    def test_missing_key_mutation_fails(self):
        # Only one mutation, missing T790M/L858R/C797S
        m = MutationRecord(mutation_id="G719S", position=719, wild_type="G", mutant="S")
        ctx = ContextDataset(mutations=[m])
        report = validate_dataset(context=ctx)
        assert not report.is_valid
        assert any("key mutations" in e.message.lower() for e in report.errors)

    def test_invalid_wild_type_fails(self):
        m = MutationRecord(mutation_id="XX1Y", position=1, wild_type="XX", mutant="Y")
        t = MutationRecord(mutation_id="T790M", position=790, wild_type="T", mutant="M")
        l = MutationRecord(mutation_id="L858R", position=858, wild_type="L", mutant="R")
        c = MutationRecord(mutation_id="C797S", position=797, wild_type="C", mutant="S")
        ctx = ContextDataset(mutations=[m, t, l, c])
        report = validate_dataset(context=ctx)
        assert any("wild_type" in e.field for e in report.errors)


# ── Benchmark Assembly Tests ────────────────────────────────────────────


class TestBenchmarkAssembly:
    def test_assemble_produces_files(self, tmp_path):
        summary = assemble_benchmark(output_dir=tmp_path, fail_on_error=True)
        assert isinstance(summary, BenchmarkSummary)
        assert summary.n_mutations >= 15
        assert summary.n_structures > 0
        assert summary.n_ligands > 0

        # Check output files exist
        expected_files = [
            "context.json", "context.csv",
            "structures.json", "structures.csv",
            "ligands.json", "ligands.csv",
            "mappings.json",
            "mapping_mutation_structure.csv",
            "mapping_structure_ligand.csv",
            "summary.json",
            "validation_report.txt",
        ]
        for fname in expected_files:
            assert (tmp_path / fname).exists(), f"Missing output: {fname}"

    def test_assemble_deterministic(self, tmp_path):
        s1 = assemble_benchmark(output_dir=tmp_path / "run1", split_seed=42)
        s2 = assemble_benchmark(output_dir=tmp_path / "run2", split_seed=42)
        assert s1.n_mutations == s2.n_mutations
        assert s1.split_counts == s2.split_counts

    def test_csv_files_not_empty(self, tmp_path):
        assemble_benchmark(output_dir=tmp_path)
        for csv_file in tmp_path.glob("*.csv"):
            lines = csv_file.read_text().strip().split("\n")
            assert len(lines) >= 2, f"CSV {csv_file.name} has no data rows"
