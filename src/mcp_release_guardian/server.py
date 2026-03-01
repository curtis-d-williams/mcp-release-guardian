# SPDX-License-Identifier: MIT
"""FastMCP server for mcp-release-guardian.

Deterministic, network-free, read-only release hygiene tools.
Fail-closed: any unresolvable state returns a failing result rather
than raising an exception.
"""

from __future__ import annotations

import asyncio
import tomllib
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("mcp-release-guardian")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_version(path: Path) -> str | None:
    """Read pyproject.toml [project].version; return None if absent or unreadable."""
    pyproject_path = path / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    try:
        with open(pyproject_path, "rb") as fh:
            data = tomllib.load(fh)
        v = data.get("project", {}).get("version")
        return str(v) if v is not None else None
    except Exception:
        return None


def _has_pytest(path: Path) -> bool:
    """Return True if pytest is referenced in the repo's config files."""
    if (path / "pytest.ini").exists():
        return True
    for candidate in ["pyproject.toml", "setup.cfg", "tox.ini"]:
        p = path / candidate
        if p.exists():
            try:
                if "pytest" in p.read_text():
                    return True
            except OSError:
                pass
    return False


# ---------------------------------------------------------------------------
# Tool: check_repo_hygiene
# ---------------------------------------------------------------------------


@mcp.tool()
def check_repo_hygiene(repo_path: str) -> dict:
    """Validate that a repo contains the minimum release hygiene artifacts.

    Runs seven file/directory presence checks as defined in docs/V1_CONTRACT.md.
    No network access. Fail-closed.

    Args:
        repo_path: Absolute or relative path to the repository root.

    Returns:
        {
            "tool": "check_repo_hygiene",
            "repo_path": str,
            "ok": bool,
            "checks": [{"check_id": str, "ok": bool, "details": str}],
            "fail_closed": bool
        }
    """
    path = Path(repo_path).resolve()
    checks: list[dict] = []

    # 1. pyproject.toml OR setup.cfg OR setup.py
    pkg_candidates = ["pyproject.toml", "setup.cfg", "setup.py"]
    found_pkg = next((f for f in pkg_candidates if (path / f).exists()), None)
    checks.append(
        {
            "check_id": "has_package_definition",
            "ok": found_pkg is not None,
            "details": f"Found {found_pkg}"
            if found_pkg
            else f"Not found (checked: {', '.join(pkg_candidates)})",
        }
    )

    # 2. LICENSE
    lic_candidates = ["LICENSE", "LICENSE.txt", "LICENSE.md", "LICENSE.rst"]
    found_lic = next((f for f in lic_candidates if (path / f).exists()), None)
    checks.append(
        {
            "check_id": "has_license",
            "ok": found_lic is not None,
            "details": f"Found {found_lic}"
            if found_lic
            else f"Not found (checked: {', '.join(lic_candidates)})",
        }
    )

    # 3. README
    readme_candidates = ["README.md", "README.rst", "README.txt", "README"]
    found_readme = next((f for f in readme_candidates if (path / f).exists()), None)
    checks.append(
        {
            "check_id": "has_readme",
            "ok": found_readme is not None,
            "details": f"Found {found_readme}"
            if found_readme
            else f"Not found (checked: {', '.join(readme_candidates)})",
        }
    )

    # 4. .github/ISSUE_TEMPLATE/bug_report.yml
    bug_yml = path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
    bug_ok = bug_yml.exists()
    checks.append(
        {
            "check_id": "has_bug_report_template",
            "ok": bug_ok,
            "details": "Found .github/ISSUE_TEMPLATE/bug_report.yml"
            if bug_ok
            else "Not found: .github/ISSUE_TEMPLATE/bug_report.yml",
        }
    )

    # 5. .github/workflows/ directory (presence only)
    workflows_dir = path / ".github" / "workflows"
    wf_ok = workflows_dir.is_dir()
    checks.append(
        {
            "check_id": "has_ci_workflows",
            "ok": wf_ok,
            "details": "Found .github/workflows/" if wf_ok else "Not found: .github/workflows/",
        }
    )

    # 6. docs/V1_CONTRACT.md
    contract_md = path / "docs" / "V1_CONTRACT.md"
    contract_ok = contract_md.exists()
    checks.append(
        {
            "check_id": "has_v1_contract",
            "ok": contract_ok,
            "details": "Found docs/V1_CONTRACT.md" if contract_ok else "Not found: docs/V1_CONTRACT.md",
        }
    )

    # 7. docs/DETERMINISM_NOTES.md
    det_md = path / "docs" / "DETERMINISM_NOTES.md"
    det_ok = det_md.exists()
    checks.append(
        {
            "check_id": "has_determinism_notes",
            "ok": det_ok,
            "details": "Found docs/DETERMINISM_NOTES.md"
            if det_ok
            else "Not found: docs/DETERMINISM_NOTES.md",
        }
    )

    ok = all(c["ok"] for c in checks)
    return {
        "tool": "check_repo_hygiene",
        "repo_path": str(path),
        "ok": ok,
        "checks": checks,
        "fail_closed": not ok,
    }


# ---------------------------------------------------------------------------
# Tool: check_version_alignment
# ---------------------------------------------------------------------------


@mcp.tool()
def check_version_alignment(
    repo_path: str,
    expected_tag: str | None = None,
) -> dict:
    """Check that pyproject.toml [project].version matches an optional expected tag.

    No network access. Fail-closed when version cannot be detected.

    Args:
        repo_path:    Absolute or relative path to the repository root.
        expected_tag: Optional target tag, e.g. "v0.1.0". Leading "v" is stripped
                      before comparison with the file-level version string.

    Returns:
        {
            "tool": "check_version_alignment",
            "repo_path": str,
            "ok": bool,
            "expected_tag": str | null,
            "detected": {"version": str | null, "source": str | null},
            "details": str,
            "fail_closed": bool
        }
    """
    path = Path(repo_path).resolve()

    detected_version = _detect_version(path)
    detected_source = "pyproject.toml" if detected_version is not None else None
    fail_closed = detected_version is None

    if detected_version is None:
        ok = False
        details = "Could not detect version: pyproject.toml missing or [project].version absent"
    elif expected_tag is None:
        ok = True
        details = (
            f"Detected version {detected_version} from {detected_source}; "
            "no expected_tag provided"
        )
    else:
        normalized = expected_tag.lstrip("v")
        ok = detected_version == normalized
        details = (
            f"Version {detected_version} matches expected tag {expected_tag}"
            if ok
            else (
                f"Version mismatch: detected {detected_version!r}, "
                f"expected {normalized!r} (from tag {expected_tag!r})"
            )
        )

    return {
        "tool": "check_version_alignment",
        "repo_path": str(path),
        "ok": ok,
        "expected_tag": expected_tag,
        "detected": {"version": detected_version, "source": detected_source},
        "details": details,
        "fail_closed": fail_closed,
    }


# ---------------------------------------------------------------------------
# Tool: generate_release_checklist
# ---------------------------------------------------------------------------


@mcp.tool()
def generate_release_checklist(repo_path: str, target_tag: str) -> dict:
    """Deterministically generate a release checklist based on local repo state.

    No network access. Reads pyproject.toml version, CI workflow presence, and
    bug template presence to tailor the checklist.

    Args:
        repo_path:  Absolute or relative path to the repository root.
        target_tag: Target release tag, e.g. "v0.1.0".

    Returns:
        {
            "tool": "generate_release_checklist",
            "repo_path": str,
            "target_tag": str,
            "checklist_markdown": str,
            "inputs_used": {
                "detected_version": str | null,
                "has_ci_workflows": bool,
                "has_bug_template": bool
            },
            "fail_closed": bool
        }
    """
    path = Path(repo_path).resolve()

    detected_version = _detect_version(path)
    has_ci_workflows = (path / ".github" / "workflows").is_dir()
    has_bug_template = (path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").exists()
    test_cmd = "pytest -q" if _has_pytest(path) else "run repo tests"

    lines: list[str] = [
        f"# Release Checklist — {target_tag}",
        "",
        "## Version alignment",
        f"- [ ] Confirm version alignment: run `check_version_alignment` with `expected_tag={target_tag}`",
        "",
        "## Tests",
        f"- [ ] Run tests: `{test_cmd}` — all must pass before tagging",
        "",
        "## Tag",
        "- [ ] Create and push git tag:",
        f"      `git tag {target_tag} && git push origin {target_tag}`",
        "",
        "## Release notes",
        f"- [ ] Update CHANGELOG / release notes with entries for {target_tag}",
        "",
        "## Adoption hooks",
        "- [ ] Verify adoption hooks are in place:",
        f"  - Bug report template (.github/ISSUE_TEMPLATE/bug_report.yml): {'✓ present' if has_bug_template else '✗ missing'}",
        f"  - CI workflows (.github/workflows/): {'✓ present' if has_ci_workflows else '✗ missing'}",
        "  - Confirm pinned issues are set if applicable",
    ]

    return {
        "tool": "generate_release_checklist",
        "repo_path": str(path),
        "target_tag": target_tag,
        "checklist_markdown": "\n".join(lines),
        "inputs_used": {
            "detected_version": detected_version,
            "has_ci_workflows": has_ci_workflows,
            "has_bug_template": has_bug_template,
        },
        "fail_closed": detected_version is None,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Launch the mcp-release-guardian MCP server over stdio."""
    try:
        mcp.run(transport="stdio")
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Clean exit on Ctrl+C / cancellation
        return
    except BaseException as e:
        # Some runtimes raise ExceptionGroup on cancellation; suppress only if it's purely cancellation.
        if isinstance(e, ExceptionGroup) and all(
            isinstance(x, (KeyboardInterrupt, asyncio.CancelledError)) for x in e.exceptions
        ):
            return
        raise


if __name__ == "__main__":
    main()
