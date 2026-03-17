"""Tests to verify docs/conf.py reads the version dynamically from pyproject.toml."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _get_pyproject_version() -> str:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


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
