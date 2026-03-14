"""Source registry: defines all known data sources and their expected files.

The registry is the authoritative list of what data StateBind expects.
It does not download data — it registers what should exist and creates
manifest entries for tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from statebind.data.manifest import Manifest, ManifestEntry


@dataclass
class SourceSpec:
    """Specification for a single expected data file."""

    file_path: str
    description: str
    source_name: str
    source_url: str = ""
    source_version: str = ""
    format: str = ""
    required: bool = True
    notes: str = ""


@dataclass
class SourceRegistry:
    """Registry of all known data sources for StateBind.

    This class holds the ground truth for what files the project expects.
    Use `build_manifests()` to create manifest files from the registry.
    """

    specs: list[SourceSpec] = field(default_factory=list)

    @classmethod
    def default(cls) -> SourceRegistry:
        """Create the default registry with all v1 data sources."""
        registry = cls()

        # ── Context sources ─────────────────────────────────────────
        registry.add(SourceSpec(
            file_path="data/raw/context/cosmic_egfr_mutations.tsv",
            description="COSMIC somatic mutations for EGFR, filtered to kinase domain",
            source_name="cosmic",
            source_url="https://cancer.sanger.ac.uk/cosmic/download",
            format="tsv",
            required=True,
            notes="Requires COSMIC account. Download CosmicMutantExport, filter to EGFR.",
        ))
        registry.add(SourceSpec(
            file_path="data/raw/context/clinvar_egfr_variants.xml",
            description="ClinVar variant records for EGFR",
            source_name="clinvar",
            source_url="https://www.ncbi.nlm.nih.gov/clinvar/",
            format="xml",
            required=True,
            notes="Query via Entrez efetch for EGFR[gene] with clinical significance.",
        ))
        registry.add(SourceSpec(
            file_path="data/raw/context/manual_curated_mutations.json",
            description="Hand-curated EGFR resistance mutations with conformational annotations",
            source_name="manual",
            format="json",
            required=True,
            notes="Primary gold-standard annotation source. Created by project author.",
        ))

        # ── Structure sources ───────────────────────────────────────
        registry.add(SourceSpec(
            file_path="data/raw/structures/pdb_metadata.json",
            description="RCSB PDB metadata for EGFR kinase domain structures",
            source_name="pdb",
            source_url="https://data.rcsb.org/rest/v1/core/entry/",
            format="json",
            required=True,
            notes="Query RCSB search API for EGFR kinase domain, human, X-ray, <=3.0A.",
        ))
        registry.add(SourceSpec(
            file_path="data/raw/structures/klifs_egfr.csv",
            description="KLIFS kinase classification data for EGFR",
            source_name="klifs",
            source_url="https://klifs.net/",
            format="csv",
            required=True,
            notes="Used as validation reference for conformational state classification.",
        ))
        registry.add(SourceSpec(
            file_path="data/raw/structures/uniprot_p00533.json",
            description="UniProt entry for human EGFR (P00533)",
            source_name="uniprot",
            source_url="https://rest.uniprot.org/uniprotkb/P00533.json",
            format="json",
            required=True,
        ))

        # ── Ligand sources ──────────────────────────────────────────
        registry.add(SourceSpec(
            file_path="data/raw/ligands/chembl_egfr_binders.csv",
            description="ChEMBL bioactivity data for EGFR (CHEMBL203), IC50 < 1 uM",
            source_name="chembl",
            source_url="https://www.ebi.ac.uk/chembl/",
            format="csv",
            required=True,
            notes="Query ChEMBL API for target CHEMBL203, IC50 < 1000 nM, single protein assays.",
        ))
        registry.add(SourceSpec(
            file_path="data/raw/ligands/approved_egfr_tkis.json",
            description="Approved EGFR TKIs with SMILES and clinical annotations",
            source_name="manual",
            format="json",
            required=False,
            notes="Small reference set: gefitinib, erlotinib, afatinib, osimertinib, etc.",
        ))

        return registry

    def add(self, spec: SourceSpec) -> None:
        """Add a source specification to the registry."""
        # Replace existing spec for the same file_path
        self.specs = [s for s in self.specs if s.file_path != spec.file_path]
        self.specs.append(spec)

    def get_specs_by_category(self, category: str) -> list[SourceSpec]:
        """Return specs matching a data category (context, structures, ligands)."""
        return [s for s in self.specs if f"/{category}/" in s.file_path]

    def required_specs(self) -> list[SourceSpec]:
        """Return only required source specs."""
        return [s for s in self.specs if s.required]

    def build_manifest(self, category: str) -> Manifest:
        """Build a manifest for a category from registry specs.

        Args:
            category: One of 'context', 'structures', 'ligands'.

        Returns:
            A Manifest populated with pending entries for the category.
        """
        specs = self.get_specs_by_category(category)
        manifest = Manifest(category=category)
        for spec in specs:
            entry = ManifestEntry(
                file_path=spec.file_path,
                description=spec.description,
                source_name=spec.source_name,
                source_version=spec.source_version,
                source_url=spec.source_url,
                format=spec.format,
                status="pending",
                notes=spec.notes,
            )
            manifest.add_entry(entry)
        return manifest

    def build_all_manifests(self) -> dict[str, Manifest]:
        """Build manifests for all categories."""
        categories = ["context", "structures", "ligands"]
        return {cat: self.build_manifest(cat) for cat in categories}

    def __len__(self) -> int:
        return len(self.specs)
