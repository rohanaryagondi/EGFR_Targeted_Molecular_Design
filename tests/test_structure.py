"""Test project structure and conventions."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_src_layout_exists():
    assert (PROJECT_ROOT / "src" / "statebind").is_dir()


def test_all_modules_have_init():
    modules = ["context", "structure", "dynamics", "generation", "ranking", "utils"]
    for module in modules:
        init_file = PROJECT_ROOT / "src" / "statebind" / module / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {module}"


def test_configs_exist():
    assert (PROJECT_ROOT / "configs").is_dir()
    assert (PROJECT_ROOT / "configs" / "default.yaml").exists()


def test_docs_exist():
    expected_docs = [
        "PROJECT_CHARTER.md",
        "ARCHITECTURE.md",
        "PHASE_PLAN.md",
        "DECISIONS.md",
        "RUNBOOK.md",
        "BENCHMARK_SPEC.md",
        "RISK_REGISTER.md",
        "GITHUB_STORY.md",
    ]
    for doc in expected_docs:
        assert (PROJECT_ROOT / "docs" / doc).exists(), f"Missing doc: {doc}"


def test_artifacts_dir_exists():
    assert (PROJECT_ROOT / "artifacts").is_dir()


def test_reports_dir_exists():
    assert (PROJECT_ROOT / "reports").is_dir()


def test_pyproject_toml_exists():
    assert (PROJECT_ROOT / "pyproject.toml").exists()
