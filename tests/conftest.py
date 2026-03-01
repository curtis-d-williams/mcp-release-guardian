# SPDX-License-Identifier: MIT
"""Pytest fixtures for mcp-release-guardian V1 tests.

Plain-directory fixtures are used for hygiene, version, and checklist tools
(none of those tools require a git repo).  The legacy clean_python_repo git
fixture is retained for any future git-aware tests.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_PYPROJECT_WITH_VERSION = '[project]\nname = "test-pkg"\nversion = "0.1.0"\n'
_PYPROJECT_NO_VERSION = (
    '[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n'
)


# ---------------------------------------------------------------------------
# Git helpers (kept for clean_python_repo)
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


def _init_git_repo(path: Path) -> Path:
    _git(["init"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test User"], path)
    _git(["add", "."], path)
    _git(["commit", "-m", "Initial commit"], path)
    return path


# ---------------------------------------------------------------------------
# Plain-directory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def full_hygiene_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory containing all 7 V1 hygiene artifacts and version 0.1.0."""
    base = tmp_path_factory.mktemp("full_hygiene_repo")
    (base / "pyproject.toml").write_text(_PYPROJECT_WITH_VERSION)
    (base / "README.md").write_text("# Test\n")
    (base / "LICENSE").write_text("MIT License\n")
    (base / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (base / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").write_text("name: Bug\n")
    (base / ".github" / "workflows").mkdir(parents=True)
    (base / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    (base / "docs").mkdir()
    (base / "docs" / "V1_CONTRACT.md").write_text("# V1 Contract\n")
    (base / "docs" / "DETERMINISM_NOTES.md").write_text("# Determinism Notes\n")
    return base


@pytest.fixture(scope="session")
def minimal_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with only pyproject.toml, README, LICENSE.

    Deliberately missing: .github/workflows/, .github/ISSUE_TEMPLATE/bug_report.yml,
    docs/V1_CONTRACT.md, docs/DETERMINISM_NOTES.md.
    """
    base = tmp_path_factory.mktemp("minimal_repo")
    (base / "pyproject.toml").write_text(_PYPROJECT_WITH_VERSION)
    (base / "README.md").write_text("# Minimal\n")
    (base / "LICENSE").write_text("MIT License\n")
    return base


@pytest.fixture(scope="session")
def no_readme_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with pyproject.toml + LICENSE, missing any README file."""
    base = tmp_path_factory.mktemp("no_readme_repo")
    (base / "pyproject.toml").write_text(_PYPROJECT_WITH_VERSION)
    (base / "LICENSE").write_text("MIT License\n")
    return base


@pytest.fixture(scope="session")
def no_license_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with pyproject.toml + README, missing any LICENSE file."""
    base = tmp_path_factory.mktemp("no_license_repo")
    (base / "pyproject.toml").write_text(_PYPROJECT_WITH_VERSION)
    (base / "README.md").write_text("# No License\n")
    return base


@pytest.fixture(scope="session")
def no_version_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with pyproject.toml that has no [project].version field."""
    base = tmp_path_factory.mktemp("no_version_repo")
    (base / "pyproject.toml").write_text(_PYPROJECT_NO_VERSION)
    (base / "README.md").write_text("# No Version\n")
    (base / "LICENSE").write_text("MIT License\n")
    return base


@pytest.fixture(scope="session")
def no_pyproject_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with README + LICENSE but no pyproject.toml."""
    base = tmp_path_factory.mktemp("no_pyproject_repo")
    (base / "README.md").write_text("# No Pyproject\n")
    (base / "LICENSE").write_text("MIT License\n")
    return base


# ---------------------------------------------------------------------------
# Git-repo fixture (seeded from tests/fixtures/clean_python/)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def clean_python_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo seeded from fixtures/clean_python; pyproject.toml version = 0.1.0."""
    base = tmp_path_factory.mktemp("clean_python_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    return _init_git_repo(base)
