"""Tests for the three V1 MCP tools.

Each tool is called directly (not through the MCP protocol) so pytest can
exercise inputs / outputs without running the full server.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_release_guardian.server import (
    check_repo_hygiene,
    check_version_alignment,
    generate_release_checklist,
)

# ---------------------------------------------------------------------------
# check_repo_hygiene
# ---------------------------------------------------------------------------


class TestCheckRepoHygiene:
    EXPECTED_CHECK_NAMES = {
        "is_git_repo",
        "clean_working_tree",
        "no_untracked_files",
        "has_readme",
        "has_license",
        "has_changelog",
    }

    def test_clean_repo_all_passed(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        assert result["all_passed"] is True
        assert result["repo_path"] == str(clean_python_repo)

    def test_returns_exactly_six_checks(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        assert len(result["checks"]) == 6

    def test_check_names_are_present(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        names = {c["name"] for c in result["checks"]}
        assert names == self.EXPECTED_CHECK_NAMES

    def test_each_check_has_required_fields(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        for check in result["checks"]:
            assert "name" in check
            assert "passed" in check
            assert "detail" in check
            assert isinstance(check["passed"], bool)
            assert isinstance(check["detail"], str)

    def test_non_git_dir_fails_closed(self, non_git_dir: Path) -> None:
        result = check_repo_hygiene(str(non_git_dir))
        assert result["all_passed"] is False
        is_git = next(c for c in result["checks"] if c["name"] == "is_git_repo")
        assert is_git["passed"] is False
        # Only the is_git_repo check is present when path is not a git repo
        assert len(result["checks"]) == 1

    def test_missing_readme_fails(self, no_readme_repo: Path) -> None:
        result = check_repo_hygiene(str(no_readme_repo))
        readme_check = next(c for c in result["checks"] if c["name"] == "has_readme")
        assert readme_check["passed"] is False
        assert result["all_passed"] is False

    def test_missing_license_fails(self, no_license_repo: Path) -> None:
        result = check_repo_hygiene(str(no_license_repo))
        lic_check = next(c for c in result["checks"] if c["name"] == "has_license")
        assert lic_check["passed"] is False
        assert result["all_passed"] is False

    def test_dirty_repo_untracked_check_fails(self, dirty_repo: Path) -> None:
        result = check_repo_hygiene(str(dirty_repo))
        untracked = next(c for c in result["checks"] if c["name"] == "no_untracked_files")
        assert untracked["passed"] is False
        assert result["all_passed"] is False

    def test_modified_repo_clean_working_tree_fails(self, modified_repo: Path) -> None:
        result = check_repo_hygiene(str(modified_repo))
        clean = next(c for c in result["checks"] if c["name"] == "clean_working_tree")
        assert clean["passed"] is False
        assert result["all_passed"] is False

    def test_result_is_json_serializable(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        loaded = json.loads(json.dumps(result))
        assert loaded == result

    def test_nonexistent_path_fails_closed(self, tmp_path: Path) -> None:
        result = check_repo_hygiene(str(tmp_path / "nonexistent"))
        assert result["all_passed"] is False

    def test_repo_path_is_resolved_absolute(self, clean_python_repo: Path) -> None:
        result = check_repo_hygiene(str(clean_python_repo))
        assert Path(result["repo_path"]).is_absolute()


# ---------------------------------------------------------------------------
# check_version_alignment
# ---------------------------------------------------------------------------


class TestCheckVersionAlignment:
    def test_aligned_repo_all_aligned(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert result["all_aligned"] is True
        assert result["expected_tag"] == "v0.1.0"

    def test_result_schema_fields_present(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert "repo_path" in result
        assert "expected_tag" in result
        assert "sources" in result
        assert "all_aligned" in result

    def test_each_source_has_required_fields(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        for source in result["sources"]:
            assert "source" in source
            assert "version" in source
            assert "aligned" in source
            assert isinstance(source["aligned"], bool)

    def test_pyproject_version_found_and_aligned(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        src = next(s for s in result["sources"] if s["source"] == "pyproject.toml")
        assert src["version"] == "0.1.0"
        assert src["aligned"] is True

    def test_git_tag_aligned(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        src = next(s for s in result["sources"] if s["source"] == "git_tag")
        assert src["aligned"] is True
        assert src["version"] == "v0.1.0"

    def test_missing_tag_reports_unaligned(self, misaligned_repo: Path) -> None:
        result = check_version_alignment(str(misaligned_repo), "v0.1.0")
        git_src = next(s for s in result["sources"] if s["source"] == "git_tag")
        assert git_src["aligned"] is False
        assert git_src["version"] is None

    def test_wrong_expected_tag_fails(self, misaligned_repo: Path) -> None:
        result = check_version_alignment(str(misaligned_repo), "v0.2.0")
        assert result["all_aligned"] is False

    def test_nonexistent_path_fails_closed(self, tmp_path: Path) -> None:
        result = check_version_alignment(str(tmp_path / "nonexistent"), "v0.1.0")
        assert result["all_aligned"] is False
        assert "error" in result

    def test_result_is_json_serializable(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        loaded = json.loads(json.dumps(result))
        assert loaded == result

    def test_repo_path_is_resolved_absolute(self, clean_python_repo: Path) -> None:
        result = check_version_alignment(str(clean_python_repo), "v0.1.0")
        assert Path(result["repo_path"]).is_absolute()

    def test_all_aligned_false_when_sources_empty(self, non_git_dir: Path) -> None:
        # non_git_dir has no pyproject.toml and no .git → sources will be empty
        result = check_version_alignment(str(non_git_dir), "v0.1.0")
        assert result["all_aligned"] is False


# ---------------------------------------------------------------------------
# generate_release_checklist
# ---------------------------------------------------------------------------


class TestGenerateReleaseChecklist:
    def test_returns_correct_top_level_keys(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert "repo_path" in result
        assert "version" in result
        assert "checklist" in result
        assert "total" in result
        assert "required_count" in result

    def test_total_matches_checklist_length(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["total"] == len(result["checklist"])

    def test_required_count_matches(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        expected = sum(1 for it in result["checklist"] if it["required"])
        assert result["required_count"] == expected

    def test_each_item_has_required_fields(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        for item in result["checklist"]:
            assert "item" in item
            assert "category" in item
            assert "required" in item
            assert isinstance(item["item"], str)
            assert isinstance(item["category"], str)
            assert isinstance(item["required"], bool)

    def test_version_reflected_in_output(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["version"] == "v0.1.0"

    def test_version_stamp_in_checklist_item(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.2.0")
        items = [it["item"] for it in result["checklist"]]
        assert any("v0.2.0" in item for item in items)

    def test_deterministic_same_inputs(self, clean_python_repo: Path) -> None:
        r1 = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        r2 = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert r1 == r2

    def test_result_is_json_serializable(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        loaded = json.loads(json.dumps(result))
        assert loaded == result

    def test_repo_path_is_resolved_absolute(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert Path(result["repo_path"]).is_absolute()

    def test_at_least_one_required_item(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        assert result["required_count"] > 0

    def test_works_with_nonexistent_path(self, tmp_path: Path) -> None:
        """Checklist generation is purely deterministic; path need not exist."""
        result = generate_release_checklist(str(tmp_path / "anywhere"), "v1.0.0")
        assert result["version"] == "v1.0.0"
        assert result["total"] > 0

    def test_known_categories_present(self, clean_python_repo: Path) -> None:
        result = generate_release_checklist(str(clean_python_repo), "v0.1.0")
        categories = {it["category"] for it in result["checklist"]}
        assert "hygiene" in categories
        assert "versioning" in categories
        assert "documentation" in categories
        assert "quality" in categories
