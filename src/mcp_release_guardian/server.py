"""FastMCP server for mcp-release-guardian.

Deterministic, network-free, read-only release hygiene tools.
Fail-closed: any error or missing state returns a failing result rather
than raising an exception.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("mcp-release-guardian")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git command; returns (returncode, stdout, stderr). Never raises."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", str(exc)


# ---------------------------------------------------------------------------
# Tool: check_repo_hygiene
# ---------------------------------------------------------------------------


@mcp.tool()
def check_repo_hygiene(repo_path: str) -> dict:
    """Check repository hygiene for release readiness.

    Runs six deterministic, read-only checks against a local git repository.
    Returns a JSON object with per-check results and an overall pass/fail flag.
    No network access. Fail-closed: any unreadable state marks that check failed.

    Args:
        repo_path: Absolute or relative path to the local repository root.

    Returns:
        {
            "repo_path": str,          # resolved absolute path
            "checks": [
                {
                    "name": str,       # check identifier
                    "passed": bool,
                    "detail": str      # human-readable explanation
                }
            ],
            "all_passed": bool
        }
    """
    path = Path(repo_path).resolve()
    checks: list[dict] = []

    # Check 1: is_git_repo
    is_git = path.is_dir() and (path / ".git").exists()
    checks.append({
        "name": "is_git_repo",
        "passed": is_git,
        "detail": f"{path / '.git'} exists" if is_git else "No .git directory found",
    })

    if not is_git:
        return {"repo_path": str(path), "checks": checks, "all_passed": False}

    # Run git status once; reuse for checks 2 and 3
    rc, stdout, stderr = _run_git(["status", "--porcelain"], path)
    status_ok = rc == 0
    status_lines = stdout.splitlines() if status_ok else []

    # Check 2: clean_working_tree (no staged/modified tracked files)
    if not status_ok:
        clean = False
        clean_detail = f"git status failed: {stderr.strip()}"
    else:
        dirty = [ln for ln in status_lines if ln and not ln.startswith("??")]
        clean = len(dirty) == 0
        clean_detail = (
            "Working tree is clean"
            if clean
            else f"{len(dirty)} modified/staged file(s)"
        )
    checks.append({"name": "clean_working_tree", "passed": clean, "detail": clean_detail})

    # Check 3: no_untracked_files
    if not status_ok:
        no_untracked = False
        untracked_detail = "git status failed"
    else:
        untracked = [ln for ln in status_lines if ln.startswith("??")]
        no_untracked = len(untracked) == 0
        untracked_detail = (
            "No untracked files"
            if no_untracked
            else f"{len(untracked)} untracked file(s)"
        )
    checks.append({
        "name": "no_untracked_files",
        "passed": no_untracked,
        "detail": untracked_detail,
    })

    # Check 4: has_readme
    readme_candidates = ["README.md", "README.rst", "README.txt", "README"]
    found_readme = next((f for f in readme_candidates if (path / f).exists()), None)
    checks.append({
        "name": "has_readme",
        "passed": found_readme is not None,
        "detail": f"Found {found_readme}" if found_readme else "No README file found",
    })

    # Check 5: has_license
    license_candidates = ["LICENSE", "LICENSE.txt", "LICENSE.md", "LICENSE.rst"]
    found_license = next((f for f in license_candidates if (path / f).exists()), None)
    checks.append({
        "name": "has_license",
        "passed": found_license is not None,
        "detail": f"Found {found_license}" if found_license else "No LICENSE file found",
    })

    # Check 6: has_changelog
    changelog_candidates = [
        "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt", "CHANGELOG", "HISTORY.md",
    ]
    found_changelog = next((f for f in changelog_candidates if (path / f).exists()), None)
    checks.append({
        "name": "has_changelog",
        "passed": found_changelog is not None,
        "detail": (
            f"Found {found_changelog}" if found_changelog else "No CHANGELOG file found"
        ),
    })

    all_passed = all(c["passed"] for c in checks)
    return {"repo_path": str(path), "checks": checks, "all_passed": all_passed}


# ---------------------------------------------------------------------------
# Tool: check_version_alignment
# ---------------------------------------------------------------------------


@mcp.tool()
def check_version_alignment(repo_path: str, expected_tag: str) -> dict:
    """Check that version strings across source files and git tags are aligned.

    Inspects pyproject.toml (PEP 621 and Poetry layouts), package.json, and
    the local git tag list. No network access. Fail-closed: missing files are
    omitted from sources; a missing git tag is reported as unaligned.

    Args:
        repo_path:    Absolute or relative path to the local repository root.
        expected_tag: The release tag to validate against, e.g. "v0.1.0".
                      The leading "v" is stripped when comparing to file-level
                      version strings (e.g. "0.1.0" in pyproject.toml).

    Returns:
        {
            "repo_path":    str,
            "expected_tag": str,
            "sources": [
                {
                    "source":  str,          # "pyproject.toml" | "package.json" | "git_tag"
                    "version": str | null,   # version found, or null if absent/unreadable
                    "aligned": bool
                }
            ],
            "all_aligned": bool              # false if sources is empty (fail-closed)
        }
    """
    path = Path(repo_path).resolve()
    expected_version = expected_tag.lstrip("v")
    sources: list[dict] = []

    if not path.exists():
        return {
            "repo_path": str(path),
            "expected_tag": expected_tag,
            "sources": [],
            "all_aligned": False,
            "error": "repo_path does not exist",
        }

    # Source 1: pyproject.toml
    pyproject_path = path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as fh:
                data = tomllib.load(fh)
            version = data.get("project", {}).get("version") or (
                data.get("tool", {}).get("poetry", {}).get("version")
            )
            sources.append({
                "source": "pyproject.toml",
                "version": version,
                "aligned": version == expected_version,
            })
        except Exception as exc:
            sources.append({
                "source": "pyproject.toml",
                "version": None,
                "aligned": False,
                "error": str(exc),
            })

    # Source 2: package.json
    package_json_path = path / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path) as fh:
                data = json.load(fh)
            version = data.get("version")
            sources.append({
                "source": "package.json",
                "version": version,
                "aligned": version == expected_version,
            })
        except Exception as exc:
            sources.append({
                "source": "package.json",
                "version": None,
                "aligned": False,
                "error": str(exc),
            })

    # Source 3: git tag (always checked when .git exists)
    if (path / ".git").exists():
        rc, stdout, _ = _run_git(["tag", "--list", expected_tag], path)
        tag_exists = rc == 0 and stdout.strip() == expected_tag
        sources.append({
            "source": "git_tag",
            "version": expected_tag if tag_exists else None,
            "aligned": tag_exists,
        })

    # Fail-closed: empty sources → not aligned
    all_aligned = bool(sources) and all(s["aligned"] for s in sources)
    return {
        "repo_path": str(path),
        "expected_tag": expected_tag,
        "sources": sources,
        "all_aligned": all_aligned,
    }


# ---------------------------------------------------------------------------
# Tool: generate_release_checklist
# ---------------------------------------------------------------------------

_CHECKLIST: list[dict] = [
    {
        "item": "Repository working tree is clean (no uncommitted or untracked changes)",
        "category": "hygiene",
        "required": True,
    },
    {
        "item": "Version string updated in pyproject.toml or package.json",
        "category": "versioning",
        "required": True,
    },
    {
        "item": "CHANGELOG updated with entries for this release",
        "category": "documentation",
        "required": True,
    },
    {
        "item": "All tests pass locally",
        "category": "quality",
        "required": True,
    },
    {
        "item": "README reflects current feature set and usage",
        "category": "documentation",
        "required": False,
    },
    {
        "item": "LICENSE file present in repository root",
        "category": "hygiene",
        "required": True,
    },
    {
        "item": "No debug or temporary code committed",
        "category": "hygiene",
        "required": True,
    },
    {
        "item": "Dependencies pinned or bounded appropriately in lock file",
        "category": "quality",
        "required": False,
    },
    {
        "item": "Release artifacts built, tested, and verified",
        "category": "release",
        "required": False,
    },
]


@mcp.tool()
def generate_release_checklist(repo_path: str, version: str) -> dict:
    """Generate a deterministic release checklist for the given version.

    Returns a fixed, ordered list of checklist items. Output is always
    identical for the same inputs. No filesystem reads beyond resolving the
    path. No network access.

    Args:
        repo_path: Absolute or relative path to the local repository root.
        version:   The target release version string, e.g. "v0.1.0".

    Returns:
        {
            "repo_path":      str,
            "version":        str,
            "checklist": [
                {
                    "item":     str,   # human-readable action
                    "category": str,   # "hygiene" | "versioning" | "documentation"
                                       # | "quality" | "release"
                    "required": bool
                }
            ],
            "total":          int,
            "required_count": int
        }
    """
    path = Path(repo_path).resolve()

    # Stamp the version into the tag-creation item so output is deterministic
    # per (repo_path, version) pair.
    checklist = [
        {**item} for item in _CHECKLIST
    ]
    # Insert version-specific tag item after the last required versioning item
    version_tag_item = {
        "item": f"Git tag {version} created and pushed to remote",
        "category": "versioning",
        "required": True,
    }
    checklist.insert(4, version_tag_item)

    return {
        "repo_path": str(path),
        "version": version,
        "checklist": checklist,
        "total": len(checklist),
        "required_count": sum(1 for it in checklist if it["required"]),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Launch the mcp-release-guardian MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
