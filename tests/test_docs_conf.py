"""Tests for docs configuration and documentation dependencies."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
ZENSICAL_PATH = ROOT / "zensical.toml"


def _load_pyproject() -> dict:
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)


def _load_zensical() -> dict:
    with open(ZENSICAL_PATH, "rb") as f:
        return tomllib.load(f)


def test_docs_dependency_group_exists():
    """The docs optional-dependency group must be declared in pyproject.toml."""
    data = _load_pyproject()
    optional_deps = data.get("project", {}).get("optional-dependencies", {})
    assert "docs" in optional_deps, (
        "Missing [project.optional-dependencies] docs in pyproject.toml"
    )


def test_docs_group_contains_required_packages():
    """The docs group must include zensical, mkdocstrings, mkdocs-click, and mike."""
    data = _load_pyproject()
    docs_deps = data["project"]["optional-dependencies"]["docs"]
    dep_names = {
        dep.split(">")[0].split("<")[0].split("[")[0].strip('"') for dep in docs_deps
    }
    for required in ("zensical", "mkdocstrings", "mkdocs-click", "mike"):
        assert required in dep_names, f"Missing required doc dependency: {required}"


def test_mkdocstrings_includes_python_extra():
    """mkdocstrings must include the [python] extra."""
    data = _load_pyproject()
    docs_deps = data["project"]["optional-dependencies"]["docs"]
    mkdocstrings_entries = [d for d in docs_deps if d.startswith("mkdocstrings")]
    assert any("[python]" in entry for entry in mkdocstrings_entries), (
        "mkdocstrings must include [python] extra"
    )


def test_zensical_toml_exists():
    """zensical.toml must exist at the project root."""
    assert ZENSICAL_PATH.exists(), "zensical.toml not found at project root"


def test_zensical_toml_has_site_name():
    """zensical.toml must define a site_name."""
    data = _load_zensical()
    assert data["project"]["site_name"] == "fbcm"


def test_zensical_toml_has_mkdocstrings_plugin():
    """zensical.toml must configure the mkdocstrings plugin."""
    data = _load_zensical()
    plugins = data["project"]["plugins"]
    assert "mkdocstrings" in plugins, (
        "mkdocstrings plugin not configured in zensical.toml"
    )


def test_zensical_toml_has_nav():
    """zensical.toml must define a navigation structure."""
    data = _load_zensical()
    nav = data["project"]["nav"]
    assert len(nav) > 0, "Navigation must have at least one entry"


def test_sphinx_files_removed():
    """Sphinx configuration files must not exist."""
    docs_dir = ROOT / "docs"
    for sphinx_file in ("conf.py", "Makefile", "make.bat"):
        assert not (docs_dir / sphinx_file).exists(), (
            f"Sphinx file docs/{sphinx_file} should have been removed"
        )


def test_rst_files_removed():
    """RST source files must not exist in docs/."""
    docs_dir = ROOT / "docs"
    rst_files = list(docs_dir.glob("*.rst"))
    assert len(rst_files) == 0, (
        f"RST files should have been converted to Markdown: {rst_files}"
    )


def test_markdown_docs_exist():
    """Converted Markdown documentation files must exist."""
    docs_dir = ROOT / "docs"
    for md_file in ("index.md", "usage.md", "cli.md", "api.md"):
        assert (docs_dir / md_file).exists(), f"docs/{md_file} not found"
