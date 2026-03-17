"""Tests for docs configuration and documentation dependencies."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"


def _load_pyproject() -> dict:
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)


def _get_pyproject_version() -> str:
    return _load_pyproject()["project"]["version"]


def test_docs_dependency_group_exists():
    """The docs optional-dependency group must be declared in pyproject.toml."""
    data = _load_pyproject()
    optional_deps = data.get("project", {}).get("optional-dependencies", {})
    assert "docs" in optional_deps, (
        "Missing [project.optional-dependencies] docs in pyproject.toml"
    )


def test_docs_group_contains_required_packages():
    """The docs group must include mkdocs, mkdocs-material, mkdocstrings, and mike."""
    data = _load_pyproject()
    docs_deps = data["project"]["optional-dependencies"]["docs"]
    dep_names = {
        dep.split(">")[0].split("<")[0].split("[")[0].strip('"') for dep in docs_deps
    }
    for required in ("mkdocs", "mkdocs-material", "mkdocstrings", "mike"):
        assert required in dep_names, f"Missing required doc dependency: {required}"


def test_mkdocstrings_includes_python_extra():
    """mkdocstrings must include the [python] extra."""
    data = _load_pyproject()
    docs_deps = data["project"]["optional-dependencies"]["docs"]
    mkdocstrings_entries = [d for d in docs_deps if d.startswith("mkdocstrings")]
    assert any("[python]" in entry for entry in mkdocstrings_entries), (
        "mkdocstrings must include [python] extra"
    )


def test_conf_version_matches_pyproject():
    """docs/conf.py release must match the version in pyproject.toml."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("conf", ROOT / "docs" / "conf.py")
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)

    assert conf.release == _get_pyproject_version()


def test_conf_does_not_hardcode_version():
    """docs/conf.py must not contain a hardcoded release string."""
    conf_text = (ROOT / "docs" / "conf.py").read_text()
    assert 'release = "0.0.1"' not in conf_text, (
        "docs/conf.py still contains the hardcoded 0.0.1 version"
    )
