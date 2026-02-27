V1 Tool Contract (Authoritative, Frozen)

Tool 1: check_repo_hygiene
Purpose: Validate that a repo contains the minimum "release hygiene" artifacts.

Input schema (frozen):
{
  "repo_path": "string"
}

Output schema (frozen):
{
  "tool": "check_repo_hygiene",
  "repo_path": "string",
  "ok": "boolean",
  "checks": [
    {
      "check_id": "string",
      "ok": "boolean",
      "details": "string"
    }
  ],
  "fail_closed": "boolean"
}

Checks to include (V1):
* pyproject.toml present OR setup.cfg present OR setup.py present
* LICENSE present
* README present
* .github/ISSUE_TEMPLATE/bug_report.yml present
* .github/workflows/ exists (presence only, no CI API calls)
* docs/V1_CONTRACT.md present (in this repo) — for self-hygiene
* docs/DETERMINISM_NOTES.md present (in this repo) — for self-hygiene

Tool 2: check_version_alignment
Purpose: Check that local version metadata matches a git tag (when provided) or provide version metadata deterministically.

Input schema (frozen):
{
  "repo_path": "string",
  "expected_tag": "string (optional, e.g. v0.2.2)"
}

Output schema (frozen):
{
  "tool": "check_version_alignment",
  "repo_path": "string",
  "ok": "boolean",
  "expected_tag": "string|null",
  "detected": {
    "version": "string|null",
    "source": "string|null"
  },
  "details": "string",
  "fail_closed": "boolean"
}

Rules (V1):
* Read version from pyproject.toml [project].version if present.
* If absent, set detected.version=null and fail-closed.
* If expected_tag provided, normalize by stripping leading v for comparison.

Tool 3: generate_release_checklist
Purpose: Deterministically generate a release checklist for a repo, based on local state.

Input schema (frozen):
{
  "repo_path": "string",
  "target_tag": "string"
}

Output schema (frozen):
{
  "tool": "generate_release_checklist",
  "repo_path": "string",
  "target_tag": "string",
  "checklist_markdown": "string",
  "inputs_used": {
    "detected_version": "string|null",
    "has_ci_workflows": "boolean",
    "has_bug_template": "boolean"
  },
  "fail_closed": "boolean"
}

Checklist content must include:
* version alignment step
* test run step (pytest -q if present, else "run repo tests")
* tag step (manual instruction)
* release notes step
* verify adoption hooks step (pinned issues + bug form)
No network calls.
