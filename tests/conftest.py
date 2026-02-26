"""Pytest fixtures: create temporary git repos from fixture seeds."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> None:
    """Run a git command in cwd; raises CalledProcessError on failure."""
    subprocess.run(
        ["git"] + args,
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _init_git_repo(path: Path, tag: str | None = None) -> Path:
    """Initialise a git repo in *path*, commit all existing files, optionally tag."""
    _git(["init"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test User"], path)
    _git(["add", "."], path)
    _git(["commit", "-m", "Initial commit"], path)
    if tag:
        _git(["tag", tag], path)
    return path


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def clean_python_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Clean git repo seeded from fixtures/clean_python, tagged v0.1.0."""
    base = tmp_path_factory.mktemp("clean_python_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    return _init_git_repo(base, tag="v0.1.0")


@pytest.fixture(scope="session")
def no_readme_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo identical to clean_python but without a README file."""
    base = tmp_path_factory.mktemp("no_readme_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    (base / "README.md").unlink()
    return _init_git_repo(base)


@pytest.fixture(scope="session")
def no_license_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo identical to clean_python but without a LICENSE file."""
    base = tmp_path_factory.mktemp("no_license_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    (base / "LICENSE").unlink()
    return _init_git_repo(base)


@pytest.fixture(scope="session")
def dirty_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo with an untracked file (simulates a dirty working tree)."""
    base = tmp_path_factory.mktemp("dirty_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    _init_git_repo(base)
    # Add an untracked file without staging/committing it
    (base / "dirty.txt").write_text("dirty\n")
    return base


@pytest.fixture(scope="session")
def modified_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo with a modified tracked file (simulates staged changes)."""
    base = tmp_path_factory.mktemp("modified_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    _init_git_repo(base)
    # Modify a tracked file without committing
    (base / "README.md").write_text("# Modified\n")
    return base


@pytest.fixture(scope="session")
def misaligned_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Git repo with pyproject.toml version 0.1.0 but no tags."""
    base = tmp_path_factory.mktemp("misaligned_repo")
    shutil.copytree(FIXTURES_DIR / "clean_python", base, dirs_exist_ok=True)
    return _init_git_repo(base)  # intentionally no tag


@pytest.fixture(scope="session")
def non_git_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Plain directory that is NOT a git repo."""
    base = tmp_path_factory.mktemp("non_git_dir")
    (base / "README.md").write_text("# Hello\n")
    return base
