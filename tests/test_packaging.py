"""Packaging metadata must agree with the code it describes."""
from __future__ import annotations

import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python 3.10 in CI
    import tomli as tomllib

import conciergeagent

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_package_version_matches_pyproject():
    """A drifting version silently mislabels every /healthz response."""
    assert conciergeagent.__version__ == PYPROJECT["project"]["version"]


def test_helm_chart_tracks_the_package_version():
    import yaml

    chart = yaml.safe_load((REPO_ROOT / "helm" / "Chart.yaml").read_text(encoding="utf-8"))
    assert str(chart["appVersion"]) == conciergeagent.__version__


def test_changelog_documents_the_current_version():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{conciergeagent.__version__}]" in changelog


def test_license_file_exists_and_is_apache():
    licence = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in licence
    assert "Version 2.0" in licence


def test_declared_license_is_apache():
    assert PYPROJECT["project"]["license"] == "Apache-2.0"


def test_runtime_dependency_surface_stays_small():
    """Adding a runtime dependency should be a deliberate, reviewed decision."""
    assert len(PYPROJECT["project"]["dependencies"]) <= 6


def test_requirements_txt_matches_declared_runtime_dependencies():
    declared = {
        line.split(">=")[0].strip()
        for line in PYPROJECT["project"]["dependencies"]
    }
    pinned = {
        line.split(">=")[0].strip()
        for line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert declared == pinned


def test_python_floor_is_declared():
    assert PYPROJECT["project"]["requires-python"] == ">=3.10"


def test_portfolio_url_is_published_in_metadata():
    assert "devunity" in PYPROJECT["project"]["urls"]["Portfolio"]
