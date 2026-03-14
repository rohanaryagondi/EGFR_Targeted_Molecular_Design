#!/usr/bin/env python
"""Generate a markdown report summarizing the v1 benchmark.

Reads the assembled benchmark from data/processed/benchmark/ and
writes reports/phase1_benchmark.md.

Usage:
    python scripts/report_benchmark_summary.py
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark summary report")
    parser.add_argument(
        "--benchmark-dir", type=Path, default=Path("data/processed/benchmark"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/phase1_benchmark.md"),
    )
    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Benchmark directory not found: {args.benchmark_dir}")
        print("Run: python scripts/assemble_benchmark.py")
        sys.exit(1)

    # Load summary
    with open(args.benchmark_dir / "summary.json") as f:
        summary = json.load(f)

    # Load context for detail
    with open(args.benchmark_dir / "context.json") as f:
        context = json.load(f)

    # Load structures for detail
    with open(args.benchmark_dir / "structures.json") as f:
        structures = json.load(f)

    # Load ligands for detail
    with open(args.benchmark_dir / "ligands.json") as f:
        ligands = json.load(f)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report = f"""# Phase 1 Benchmark Report

**Generated:** {now}
**Benchmark version:** {summary['version']}
**Processing version:** {summary['processing_version']}

## Overview

The v1 benchmark is a small, manually curated dataset designed for inspectability
and correctness over scale. Every entry has provenance and literature backing.

| Metric | Count |
|--------|-------|
| Mutations | {summary['n_mutations']} |
| Structures | {summary['n_structures']} |
| Ligands | {summary['n_ligands']} |
| Mutation-Structure mappings | {summary['n_mutation_structure_mappings']} |
| Structure-Ligand mappings | {summary['n_structure_ligand_mappings']} |

## Conformational States Represented

{', '.join(f'`{s}`' for s in summary['states_represented'])}

All 4 canonical EGFR kinase domain conformational states are represented in the
structure dataset.

## Mutation Coverage

### By resistance generation

| Generation | Count |
|-----------|-------|"""

    gen_counts = {}
    for m in context['mutations']:
        gen = m['resistance_generation']
        gen_counts[gen] = gen_counts.get(gen, 0) + 1
    for gen, count in sorted(gen_counts.items()):
        report += f"\n| {gen} | {count} |"

    report += f"""

### By mechanism category

| Category | Count |
|----------|-------|"""

    mech_counts = {}
    for m in context['mutations']:
        mech = m['mechanism_category']
        mech_counts[mech] = mech_counts.get(mech, 0) + 1
    for mech, count in sorted(mech_counts.items()):
        report += f"\n| {mech} | {count} |"

    report += f"""

### Train/Val/Test splits

| Split | Count |
|-------|-------|"""

    for split, count in sorted(summary['split_counts'].items()):
        report += f"\n| {split} | {count} |"

    report += f"""

### Key mutations (test set)

| Mutation | Generation | Mechanism | Conformational Effect |
|----------|-----------|-----------|----------------------|"""

    for m in context['mutations']:
        if m['split'] == 'test':
            report += (f"\n| {m['mutation_id']} | {m['resistance_generation']} | "
                       f"{m['mechanism_category']} | {m['conformational_effect']} |")

    report += f"""

## Structure Coverage

### By conformational state

| State | Count | Representative |
|-------|-------|---------------|"""

    from collections import Counter
    state_counts = Counter(s['state'] for s in structures['structures'])
    reps = {s['state']: s['pdb_id'] for s in structures['structures'] if s['is_representative']}
    for state, count in sorted(state_counts.items()):
        rep = reps.get(state, "—")
        report += f"\n| {state} | {count} | {rep} |"

    report += f"""

### Mutant structures

| PDB ID | Mutations | State | Ligand |
|--------|----------|-------|--------|"""

    for s in structures['structures']:
        if s['mutations_present']:
            report += (f"\n| {s['pdb_id']} | {', '.join(s['mutations_present'])} | "
                       f"{s['state']} | {s['ligand_id']} |")

    report += f"""

## Ligand Coverage

### Approved EGFR TKIs

| Drug | Generation | pIC50 | PDB ID |
|------|-----------|-------|--------|"""

    for lig in ligands['ligands']:
        if lig.get('is_approved'):
            pIC50 = lig.get('pIC50', '—') or '—'
            pdb = lig.get('pdb_id', '—') or '—'
            report += f"\n| {lig['drug_name']} | {lig.get('generation', '—')} | {pIC50} | {pdb} |"

    report += """

## What was excluded from v1

| Data type | Excluded | Reason |
|-----------|----------|--------|
| Exon 19 deletions | Yes | Not point mutations; require different representation |
| Insertions (exon 20) | Yes | Not point mutations |
| Non-kinase domain mutations | Yes | Out of scope for conformational state analysis |
| COSMIC frequency data | Yes | Requires COSMIC account; will add in enrichment step |
| ClinVar annotations | Yes | Will integrate when raw download is available |
| ChEMBL bioactivity panel | Yes | Large download; will integrate for scoring validation |
| AlphaFold structures | Yes | PDB coverage sufficient for v1 |

## Limitations

1. **Small dataset by design.** 18 mutations, 18 structures, 9 ligands. This is
   a curated seed dataset, not a comprehensive database.

2. **Manual curation bias.** Mutations were selected for clinical importance and
   structural characterization. Rare or poorly-characterized mutations are absent.

3. **State classifications are preliminary.** Based on literature/KLIFS annotations,
   not yet validated by our own geometric classifier (Phase 2).

4. **No DFG/αC-helix geometric measurements yet.** The `dfg_distance` and
   `ac_helix_metric` fields are placeholders (null). Phase 2 will populate these.

5. **Ligand SMILES not all RDKit-validated.** Some co-crystal ligand SMILES are
   approximate. Will be validated when RDKit is integrated.

6. **No expression/pathway context yet.** The context dataset is mutation-only.
   Pathway features are a stretch goal.

## Next dependencies

| What | Needed by |
|------|-----------|
| Geometric state classifier | Phase 2 (to validate/refine state assignments) |
| PDB file downloads | Phase 2 (coordinate-level analysis) |
| RDKit integration | Phase 4 (SMILES validation, generation) |
| Docking tool setup | Phase 5 (scoring) |
| COSMIC/ClinVar enrichment | Phase 1 extension (optional) |
"""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
