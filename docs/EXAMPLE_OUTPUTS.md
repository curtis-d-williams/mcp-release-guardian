# Canonical Example Outputs

> **Note:** All `repo_path` values use the placeholder `/ABS/PATH/TO/REPO`.
> Resolved absolute paths vary by machine.

JSON keys appear in the same order as the V1 contract schemas in
[`docs/V1_CONTRACT.md`](V1_CONTRACT.md).

---

## Tool 1: `check_repo_hygiene`

### Pass — all seven hygiene checks present

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO"
}
```

**Output:**

```json
{
  "tool": "check_repo_hygiene",
  "repo_path": "/ABS/PATH/TO/REPO",
  "ok": true,
  "checks": [
    { "check_id": "has_package_definition",  "ok": true,  "details": "Found pyproject.toml" },
    { "check_id": "has_license",             "ok": true,  "details": "Found LICENSE" },
    { "check_id": "has_readme",              "ok": true,  "details": "Found README.md" },
    { "check_id": "has_bug_report_template", "ok": true,  "details": "Found .github/ISSUE_TEMPLATE/bug_report.yml" },
    { "check_id": "has_ci_workflows",        "ok": true,  "details": "Found .github/workflows/" },
    { "check_id": "has_v1_contract",         "ok": true,  "details": "Found docs/V1_CONTRACT.md" },
    { "check_id": "has_determinism_notes",   "ok": true,  "details": "Found docs/DETERMINISM_NOTES.md" }
  ],
  "fail_closed": false
}
```

### Fail — four artifacts missing

Repo contains `pyproject.toml`, `README.md`, and `LICENSE`, but lacks
`.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/workflows/`,
`docs/V1_CONTRACT.md`, and `docs/DETERMINISM_NOTES.md`.

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO"
}
```

**Output:**

```json
{
  "tool": "check_repo_hygiene",
  "repo_path": "/ABS/PATH/TO/REPO",
  "ok": false,
  "checks": [
    { "check_id": "has_package_definition",  "ok": true,  "details": "Found pyproject.toml" },
    { "check_id": "has_license",             "ok": true,  "details": "Found LICENSE" },
    { "check_id": "has_readme",              "ok": true,  "details": "Found README.md" },
    { "check_id": "has_bug_report_template", "ok": false, "details": "Not found: .github/ISSUE_TEMPLATE/bug_report.yml" },
    { "check_id": "has_ci_workflows",        "ok": false, "details": "Not found: .github/workflows/" },
    { "check_id": "has_v1_contract",         "ok": false, "details": "Not found: docs/V1_CONTRACT.md" },
    { "check_id": "has_determinism_notes",   "ok": false, "details": "Not found: docs/DETERMINISM_NOTES.md" }
  ],
  "fail_closed": true
}
```

`ok` is `true` only when all seven checks pass. `fail_closed` equals `not ok`.

---

## Tool 2: `check_version_alignment`

### Pass — version matches expected tag

Repo has `pyproject.toml` with `[project].version = "0.1.0"`.

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO",
  "expected_tag": "v0.1.0"
}
```

**Output:**

```json
{
  "tool": "check_version_alignment",
  "repo_path": "/ABS/PATH/TO/REPO",
  "ok": true,
  "expected_tag": "v0.1.0",
  "detected": {
    "version": "0.1.0",
    "source": "pyproject.toml"
  },
  "details": "Version 0.1.0 matches expected tag v0.1.0",
  "fail_closed": false
}
```

The leading `v` in `expected_tag` is stripped before comparison.

### Fail — version undetectable (fail-closed)

Repo has no `pyproject.toml`, or `pyproject.toml` lacks a `[project].version`
field. `fail_closed` is `true` because the tool cannot determine version state.

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO",
  "expected_tag": "v0.1.0"
}
```

**Output:**

```json
{
  "tool": "check_version_alignment",
  "repo_path": "/ABS/PATH/TO/REPO",
  "ok": false,
  "expected_tag": "v0.1.0",
  "detected": {
    "version": null,
    "source": null
  },
  "details": "Could not detect version: pyproject.toml missing or [project].version absent",
  "fail_closed": true
}
```

---

## Tool 3: `generate_release_checklist`

### Pass — version detected, all hooks present

Repo has `pyproject.toml` with `[project].version = "0.1.0"` and a
`[tool.pytest.ini_options]` section (so `pytest -q` is used as the test
command), `.github/workflows/`, and `.github/ISSUE_TEMPLATE/bug_report.yml`.

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO",
  "target_tag": "v0.1.0"
}
```

**Output:**

```json
{
  "tool": "generate_release_checklist",
  "repo_path": "/ABS/PATH/TO/REPO",
  "target_tag": "v0.1.0",
  "checklist_markdown": "# Release Checklist — v0.1.0\n\n## Version alignment\n- [ ] Confirm version alignment: run `check_version_alignment` with `expected_tag=v0.1.0`\n\n## Tests\n- [ ] Run tests: `pytest -q` — all must pass before tagging\n\n## Tag\n- [ ] Create and push git tag:\n      `git tag v0.1.0 && git push origin v0.1.0`\n\n## Release notes\n- [ ] Update CHANGELOG / release notes with entries for v0.1.0\n\n## Adoption hooks\n- [ ] Verify adoption hooks are in place:\n  - Bug report template (.github/ISSUE_TEMPLATE/bug_report.yml): ✓ present\n  - CI workflows (.github/workflows/): ✓ present\n  - Confirm pinned issues are set if applicable",
  "inputs_used": {
    "detected_version": "0.1.0",
    "has_ci_workflows": true,
    "has_bug_template": true
  },
  "fail_closed": false
}
```

**Rendered `checklist_markdown`:**

```markdown
# Release Checklist — v0.1.0

## Version alignment
- [ ] Confirm version alignment: run `check_version_alignment` with `expected_tag=v0.1.0`

## Tests
- [ ] Run tests: `pytest -q` — all must pass before tagging

## Tag
- [ ] Create and push git tag:
      `git tag v0.1.0 && git push origin v0.1.0`

## Release notes
- [ ] Update CHANGELOG / release notes with entries for v0.1.0

## Adoption hooks
- [ ] Verify adoption hooks are in place:
  - Bug report template (.github/ISSUE_TEMPLATE/bug_report.yml): ✓ present
  - CI workflows (.github/workflows/): ✓ present
  - Confirm pinned issues are set if applicable
```

### Fail — version undetectable (fail-closed)

Repo has no `pyproject.toml` (no version, no pytest detection), no
`.github/workflows/`, and no `.github/ISSUE_TEMPLATE/bug_report.yml`.
`fail_closed` is `true` because version state cannot be determined.

**Input:**

```json
{
  "repo_path": "/ABS/PATH/TO/REPO",
  "target_tag": "v0.1.0"
}
```

**Output:**

```json
{
  "tool": "generate_release_checklist",
  "repo_path": "/ABS/PATH/TO/REPO",
  "target_tag": "v0.1.0",
  "checklist_markdown": "# Release Checklist — v0.1.0\n\n## Version alignment\n- [ ] Confirm version alignment: run `check_version_alignment` with `expected_tag=v0.1.0`\n\n## Tests\n- [ ] Run tests: `run repo tests` — all must pass before tagging\n\n## Tag\n- [ ] Create and push git tag:\n      `git tag v0.1.0 && git push origin v0.1.0`\n\n## Release notes\n- [ ] Update CHANGELOG / release notes with entries for v0.1.0\n\n## Adoption hooks\n- [ ] Verify adoption hooks are in place:\n  - Bug report template (.github/ISSUE_TEMPLATE/bug_report.yml): ✗ missing\n  - CI workflows (.github/workflows/): ✗ missing\n  - Confirm pinned issues are set if applicable",
  "inputs_used": {
    "detected_version": null,
    "has_ci_workflows": false,
    "has_bug_template": false
  },
  "fail_closed": true
}
```

**Rendered `checklist_markdown`:**

```markdown
# Release Checklist — v0.1.0

## Version alignment
- [ ] Confirm version alignment: run `check_version_alignment` with `expected_tag=v0.1.0`

## Tests
- [ ] Run tests: `run repo tests` — all must pass before tagging

## Tag
- [ ] Create and push git tag:
      `git tag v0.1.0 && git push origin v0.1.0`

## Release notes
- [ ] Update CHANGELOG / release notes with entries for v0.1.0

## Adoption hooks
- [ ] Verify adoption hooks are in place:
  - Bug report template (.github/ISSUE_TEMPLATE/bug_report.yml): ✗ missing
  - CI workflows (.github/workflows/): ✗ missing
  - Confirm pinned issues are set if applicable
```

`fail_closed` is `true` whenever `detected_version` is `null`. The checklist is
still generated so callers receive actionable output even in fail-closed state.
