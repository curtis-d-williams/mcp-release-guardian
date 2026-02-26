"""Tests for the three V1 MCP tools.

All assertions are derived from the frozen V1 contract in docs/V1_CONTRACT.md.
Tools are called directly (not via MCP protocol) so pytest can exercise
input/output schemas without running the full server.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_release_guardian.server import (
    check_repo_hygiene,
    check_version_alignment,
    generate_release_checklist,
)

# ---------------------------------------------------------------------------
# Constants from the frozen V1 contract
# ---------------------------------------------------------------------------

_TOOL_HYGIENE = "check_repo_hygiene"
_TOOL_VERSION = "check_version_alignment"
_TOOL_CHECKLIST = "generate_release_checklist"

# Ordered list as specified in docs/V1_CONTRACT.md
V1_CHECK_IDS = [
    "has_package_definition",
    "has_license",
    "has_readme",
    "has_bug_report_template",
    "has_ci_workflows",
    "has_v1_contract",
    "has_determinism_notes",
]


def _stable_json(obj: object) -> str:
    """Stable JSON string with sorted keys for determinism comparisons."""
    return json.dumps(obj, sort_keys=True)


# ---------------------------------------------------------------------------
# check_repo_hygiene
# ---------------------------------------------------------------------------


class TestCheckRepoHygiene:

    # --- schema ---

    def test_top_level_keys(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert set(result.keys()) == {"tool", "repo_path", "ok", "checks", "fail_closed"}

    def test_tool_field_value(self, full_hygiene_repo: Path) -> None:
        assert check_repo_hygiene(str(full_hygiene_repo))["tool"] == _TOOL_HYGIENE

    def test_check_item_keys(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        for check in result["checks"]:
            assert set(check.keys()) == {"check_id", "ok", "details"}
            assert isinstance(check["check_id"], str)
            assert isinstance(check["ok"], bool)
            assert isinstance(check["details"], str)

    def test_repo_path_is_resolved_absolute(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert Path(result["repo_path"]).is_absolute()
        assert result["repo_path"] == str(full_hygiene_repo)

    # --- check count and IDs ---

    def test_exactly_seven_checks(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert len(result["checks"]) == 7

    def test_check_ids_match_contract_in_order(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert [c["check_id"] for c in result["checks"]] == V1_CHECK_IDS

    # --- ok / fail_closed semantics ---

    def test_all_checks_present_ok_true(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert result["ok"] is True
        assert result["fail_closed"] is False

    def test_missing_artifacts_ok_false(self, minimal_repo: Path) -> None:
        # minimal_repo lacks workflows, docs, and bug template
        result = check_repo_hygiene(str(minimal_repo))
        assert result["ok"] is False
        assert result["fail_closed"] is True

    def test_fail_closed_equals_not_ok(self, full_hygiene_repo: Path, minimal_repo: Path) -> None:
        for path in (full_hygiene_repo, minimal_repo):
            r = check_repo_hygiene(str(path))
            assert r["fail_closed"] is (not r["ok"])

    # --- individual check correctness ---

    def test_has_readme_false_when_missing(self, no_readme_repo: Path) -> None:
        result = check_repo_hygiene(str(no_readme_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_readme")
        assert check["ok"] is False
        assert result["ok"] is False

    def test_has_readme_true_when_present(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_readme")
        assert check["ok"] is True

    def test_has_license_false_when_missing(self, no_license_repo: Path) -> None:
        result = check_repo_hygiene(str(no_license_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_license")
        assert check["ok"] is False
        assert result["ok"] is False

    def test_has_license_true_when_present(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_license")
        assert check["ok"] is True

    def test_has_bug_report_template_true(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_bug_report_template")
        assert check["ok"] is True

    def test_has_bug_report_template_false(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_bug_report_template")
        assert check["ok"] is False

    def test_has_ci_workflows_true(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_ci_workflows")
        assert check["ok"] is True

    def test_has_ci_workflows_false(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_ci_workflows")
        assert check["ok"] is False

    def test_has_v1_contract_true(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_v1_contract")
        assert check["ok"] is True

    def test_has_v1_contract_false(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_v1_contract")
        assert check["ok"] is False

    def test_has_determinism_notes_true(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_determinism_notes")
        assert check["ok"] is True

    def test_has_determinism_notes_false(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_determinism_notes")
        assert check["ok"] is False

    def test_has_package_definition_true(self, minimal_repo: Path) -> None:
        result = check_repo_hygiene(str(minimal_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_package_definition")
        assert check["ok"] is True

    def test_has_package_definition_false(self, no_pyproject_repo: Path) -> None:
        result = check_repo_hygiene(str(no_pyproject_repo))
        check = next(c for c in result["checks"] if c["check_id"] == "has_package_definition")
        assert check["ok"] is False

    # --- serialisability and determinism ---

    def test_json_serializable(self, full_hygiene_repo: Path) -> None:
        result = check_repo_hygiene(str(full_hygiene_repo))
        assert json.loads(json.dumps(result)) == result

    def test_deterministic(self, full_hygiene_repo: Path) -> None:
        r1 = check_repo_hygiene(str(full_hygiene_repo))
        r2 = check_repo_hygiene(str(full_hygiene_repo))
        assert _stable_json(r1) == _stable_json(r2)

    def test_deterministic_on_failing_repo(self, minimal_repo: Path) -> None:
        r1 = check_repo_hygiene(str(minimal_repo))
        r2 = check_repo_hygiene(str(minimal_repo))
        assert _stable_json(r1) == _stable_json(r2)


# ---------------------------------------------------------------------------
# check_version_alignment
# ---------------------------------------------------------------------------


class TestCheckVersionAlignment:

    # --- schema ---

    def test_top_level_keys(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert set(result.keys()) == {
            "tool", "repo_path", "ok", "expected_tag", "detected", "details", "fail_closed",
        }

    def test_tool_field_value(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert result["tool"] == _TOOL_VERSION

    def test_detected_keys(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert set(result["detected"].keys()) == {"version", "source"}

    def test_details_is_non_empty_string(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert isinstance(result["details"], str) and result["details"]

    def test_repo_path_is_resolved_absolute(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert Path(result["repo_path"]).is_absolute()

    # --- ok / fail_closed semantics ---

    def test_matching_tag_ok_true(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert result["ok"] is True
        assert result["fail_closed"] is False

    def test_version_detected_from_pyproject(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert result["detected"]["version"] == "0.1.0"
        assert result["detected"]["source"] == "pyproject.toml"

    def test_leading_v_stripped_before_comparison(self, clean_python_repo: Path) -> None:
        # "v0.1.0" normalises to "0.1.0" which matches pyproject version "0.1.0"
        assert check_version_alignment(str(clean_python_repo), "v0.1.0")["ok"] is True
        # Same result without leading v
        assert check_version_alignment(str(clean_python_repo), "0.1.0")["ok"] is True

    def test_expected_tag_echoed_in_output(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert result["expected_tag"] == "v0.1.0"

    def test_tag_mismatch_ok_false_fail_closed_false(self, clean_python_repo: Path) -> None:
        # Version IS detected; mismatch is not a fail-closed event
        result = check_version_alignment(str(clean_python_repo), "v9.9.9")
        assert result["ok"] is False
        assert result["fail_closed"] is False

    def test_missing_version_ok_false_fail_closed_true(self, no_version_repo: Path) -> None:
        result = check_version_alignment(str(no_version_repo), "v0.1.0")
        assert result["ok"] is False
        assert result["fail_closed"] is True
        assert result["detected"]["version"] is None
        assert result["detected"]["source"] is None

    def test_no_pyproject_ok_false_fail_closed_true(self, no_pyproject_repo: Path) -> None:
        result = check_version_alignment(str(no_pyproject_repo), "v0.1.0")
        assert result["ok"] is False
        assert result["fail_closed"] is True
        assert result["detected"]["version"] is None

    def test_no_expected_tag_ok_true_when_version_present(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo))
        assert result["ok"] is True
        assert result["expected_tag"] is None
        assert result["fail_closed"] is False

    def test_no_expected_tag_fail_closed_when_version_absent(self, no_pyproject_repo: Path) -> None:
        result = check_version_alignment(str(no_pyproject_repo))
        assert result["ok"] is False
        assert result["fail_closed"] is True

    # --- serialisability and determinism ---

    def test_json_serializable(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert json.loads(json.dumps(result)) == result

    def test_deterministic(self, clean_python_repo: Path) -> None:
        r1 = check_version_alignment(str(clean_python_repo), "v0.1.0")
        r2 = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert _stable_json(r1) == _stable_json(r2)

    def test_deterministic_fail_closed(self, no_pyproject_repo: Path) -> None:
        r1 = check_version_alignment(str(no_pyproject_repo), "v0.1.0")
        r2 = check_version_alignment(str(no_pyproject_repo), "v0.1.0")
        assert _stable_json(r1) == _stable_json(r2)


# ---------------------------------------------------------------------------
# generate_release_checklist
# ---------------------------------------------------------------------------


class TestGenerateReleaseChecklist:

    # --- schema ---

    def test_top_level_keys(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert set(result.keys()) == {
            "tool", "repo_path", "target_tag",
            "checklist_markdown", "inputs_used", "fail_closed",
        }

    def test_tool_field_value(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["tool"] == _TOOL_CHECKLIST

    def test_inputs_used_keys(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert set(result["inputs_used"].keys()) == {
            "detected_version", "has_ci_workflows", "has_bug_template",
        }

    def test_inputs_used_boolean_types(self, clean_python_repo: Path) -> None:
        iu = generate_release_checklist(str(clean_python_repo), "v0.1.0")["inputs_used"]
        assert isinstance(iu["has_ci_workflows"], bool)
        assert isinstance(iu["has_bug_template"], bool)

    def test_target_tag_echoed_in_output(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["target_tag"] == "v0.1.0"

    def test_repo_path_is_resolved_absolute(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert Path(result["repo_path"]).is_absolute()

    def test_checklist_markdown_is_non_empty_string(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert isinstance(result["checklist_markdown"], str)
        assert len(result["checklist_markdown"]) > 0

    # --- required checklist content ---

    def test_target_tag_stamped_in_markdown(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.2.0")
        assert "v0.2.0" in result["checklist_markdown"]

    def test_contains_version_alignment_step(self, clean_python_repo: Path) -> None:
        md = generate_release_checklist(str(clean_python_repo), "v0.1.0")["checklist_markdown"]
        assert "version alignment" in md.lower() or "check_version_alignment" in md

    def test_contains_test_run_step(self, clean_python_repo: Path) -> None:
        md = generate_release_checklist(str(clean_python_repo), "v0.1.0")["checklist_markdown"]
        assert "test" in md.lower()

    def test_contains_tag_step(self, clean_python_repo: Path) -> None:
        md = generate_release_checklist(str(clean_python_repo), "v0.1.0")["checklist_markdown"]
        assert "git tag" in md

    def test_contains_release_notes_step(self, clean_python_repo: Path) -> None:
        md = generate_release_checklist(str(clean_python_repo), "v0.1.0")["checklist_markdown"]
        assert "release notes" in md.lower() or "changelog" in md.lower()

    def test_contains_adoption_hooks_step(self, clean_python_repo: Path) -> None:
        md = generate_release_checklist(str(clean_python_repo), "v0.1.0")["checklist_markdown"]
        assert any(kw in md.lower() for kw in ("adoption", "hooks", "bug"))

    # --- fail_closed ---

    def test_fail_closed_false_when_version_detected(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["fail_closed"] is False
        assert result["inputs_used"]["detected_version"] == "0.1.0"

    def test_fail_closed_true_when_version_undetectable(self, no_pyproject_repo: Path) -> None:
        result = generate_release_checklist(str(no_pyproject_repo), "v0.1.0")
        assert result["fail_closed"] is True
        assert result["inputs_used"]["detected_version"] is None

    def test_fail_closed_true_when_no_project_version(self, no_version_repo: Path) -> None:
        result = generate_release_checklist(str(no_version_repo), "v0.1.0")
        assert result["fail_closed"] is True
        assert result["inputs_used"]["detected_version"] is None

    # --- inputs_used booleans reflect local presence ---

    def test_has_ci_workflows_true(self, full_hygiene_repo: Path) -> None:
        result = generate_release_checklist(str(full_hygiene_repo), "v0.1.0")
        assert result["inputs_used"]["has_ci_workflows"] is True

    def test_has_ci_workflows_false(self, minimal_repo: Path) -> None:
        result = generate_release_checklist(str(minimal_repo), "v0.1.0")
        assert result["inputs_used"]["has_ci_workflows"] is False

    def test_has_bug_template_true(self, full_hygiene_repo: Path) -> None:
        result = generate_release_checklist(str(full_hygiene_repo), "v0.1.0")
        assert result["inputs_used"]["has_bug_template"] is True

    def test_has_bug_template_false(self, minimal_repo: Path) -> None:
        result = generate_release_checklist(str(minimal_repo), "v0.1.0")
        assert result["inputs_used"]["has_bug_template"] is False

    # --- serialisability and determinism ---

    def test_json_serializable(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert json.loads(json.dumps(result)) == result

    def test_deterministic_same_inputs(self, clean_python_repo: Path) -> None:
        r1 = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        r2 = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert _stable_json(r1) == _stable_json(r2)

    def test_deterministic_fail_closed(self, no_pyproject_repo: Path) -> None:
        r1 = generate_release_checklist(str(no_pyproject_repo), "v0.1.0")
        r2 = generate_release_checklist(str(no_pyproject_repo), "v0.1.0")
        assert _stable_json(r1) == _stable_json(r2)
