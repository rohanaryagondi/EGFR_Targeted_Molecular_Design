"""Test that all modules can be imported."""


def test_import_statebind():
    import statebind
    assert hasattr(statebind, "__version__")
    assert statebind.__version__ == "0.1.0"


def test_import_context():
    import statebind.context


def test_import_structure():
    import statebind.structure


def test_import_dynamics():
    import statebind.dynamics


def test_import_generation():
    import statebind.generation


def test_import_ranking():
    import statebind.ranking


def test_import_utils():
    import statebind.utils
    from statebind.utils.config import load_config
    from statebind.utils.io import ensure_dir, save_json, load_json


def test_import_data():
    import statebind.data
    from statebind.data.registry import SourceRegistry
    from statebind.data.manifest import Manifest, ManifestEntry
    from statebind.data.paths import DataPaths
    from statebind.data.validation import validate_data_layout


def test_import_processing():
    import statebind.processing
    from statebind.processing.models import MutationRecord, StructureRecord, LigandRecord
    from statebind.processing.context import build_context_dataset
    from statebind.processing.structures import build_structure_dataset
    from statebind.processing.ligands import build_ligand_dataset
    from statebind.processing.mapping import build_mapping_tables
    from statebind.processing.validation import validate_dataset
    from statebind.processing.benchmark import assemble_benchmark


def test_import_baselines():
    import statebind.baselines
    from statebind.baselines.models import PocketDefinition, Candidate, ScoredCandidate
    from statebind.baselines.pocket import get_baseline_pocket
    from statebind.baselines.candidates import build_candidate_library
    from statebind.baselines.filtering import apply_filters
    from statebind.baselines.scoring import score_candidates
    from statebind.baselines.evaluation import evaluate_baseline
    from statebind.baselines.pipeline import run_static_baseline


def test_import_structure_modules():
    from statebind.structure.models import StateAtlas, AtlasEntry, StructuralFeatures
    from statebind.structure.features import extract_features, get_available_pdb_ids
    from statebind.structure.clustering import cluster_structures, compute_cluster_quality
    from statebind.structure.pocket_comparison import compare_pockets_by_state
    from statebind.structure.atlas import build_state_atlas


def test_import_context_modules():
    from statebind.context.features import (
        extract_mutation_features, extract_pathway_features,
        extract_all_features, build_feature_matrix, assign_state_label,
    )
    from statebind.context.preprocessing import fit_scaler, generate_splits
    from statebind.context.models import (
        MutationOnlyBaseline, CombinedLogistic, EmbeddingMLP,
        ModelConfig, Prediction, create_model,
    )
    from statebind.context.training import train_model, run_ablation_suite
    from statebind.context.evaluation import (
        evaluate_model, compare_ablations, evaluation_to_dict,
    )
