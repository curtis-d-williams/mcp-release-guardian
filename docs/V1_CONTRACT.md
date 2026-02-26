# V1 Tool Contracts

This document is the authoritative, frozen specification for the three tools
shipped in V1 of `mcp-release-guardian`. All inputs, outputs, and behaviour
described here are normative.

---

## 1. `check_repo_hygiene`

### Purpose

Check a local git repository for release-readiness by running six deterministic,
read-only checks against the filesystem and `git status`.

### Input

| Field       | Type   | Required | Description                                      |
|-------------|--------|----------|--------------------------------------------------|
| `repo_path` | string | yes      | Absolute or relative path to the repository root |

### Output

```json
{
  "repo_path": "<resolved absolute path>",
  "checks": [
    {
      "name":   "<check identifier>",
      "passed": true,
      "detail": "<human-readable explanation>"
    }
  ],
  "all_passed": true
}
```

### Checks (fixed order, always present when the path is a git repo)

| # | `name`                | What is tested                                                    |
|---|-----------------------|-------------------------------------------------------------------|
| 1 | `is_git_repo`         | A `.git` directory exists at `repo_path`                          |
| 2 | `clean_working_tree`  | `git status --porcelain` has no staged or modified tracked files  |
| 3 | `no_untracked_files`  | `git status --porcelain` has no lines starting with `??`          |
| 4 | `has_readme`          | `README.md`, `README.rst`, `README.txt`, or `README` exists       |
| 5 | `has_license`         | `LICENSE`, `LICENSE.txt`, `LICENSE.md`, or `LICENSE.rst` exists   |
| 6 | `has_changelog`       | `CHANGELOG.md`, `CHANGELOG.rst`, `CHANGELOG.txt`, `CHANGELOG`, or `HISTORY.md` exists |

**Fail-closed rules:**

- If `repo_path` is not a git repository, only check 1 is present and
  `all_passed` is `false`.
- If `git status` returns a non-zero exit code, checks 2 and 3 are marked
  `passed: false`.
- `all_passed` is `true` if and only if every check in the list has `passed: true`.

---

## 2. `check_version_alignment`

### Purpose

Verify that version strings across source files and the local git tag list
agree with the given expected release tag.

### Input

| Field          | Type   | Required | Description                                                          |
|----------------|--------|----------|----------------------------------------------------------------------|
| `repo_path`    | string | yes      | Absolute or relative path to the repository root                     |
| `expected_tag` | string | yes      | The target tag, e.g. `"v0.1.0"`. Leading `v` is stripped when comparing to file-level version strings. |

### Output

```json
{
  "repo_path":    "<resolved absolute path>",
  "expected_tag": "v0.1.0",
  "sources": [
    {
      "source":  "pyproject.toml",
      "version": "0.1.0",
      "aligned": true
    },
    {
      "source":  "git_tag",
      "version": "v0.1.0",
      "aligned": true
    }
  ],
  "all_aligned": true
}
```

### Sources inspected (only when present)

| `source`        | File / command                         | `version` value                     |
|-----------------|----------------------------------------|-------------------------------------|
| `pyproject.toml`| PEP 621 `[project] version` or Poetry `[tool.poetry] version` | bare semver, e.g. `"0.1.0"` |
| `package.json`  | `version` field                        | bare semver, e.g. `"0.1.0"`        |
| `git_tag`       | `git tag --list <expected_tag>`        | the full tag string if found, else `null` |

**Fail-closed rules:**

- If `repo_path` does not exist, `sources` is `[]` and `all_aligned` is `false`.
- If `sources` is empty (no recognised version files and no `.git`), `all_aligned` is `false`.
- A parse error in any file sets that source's `version` to `null` and `aligned` to `false`.
- `all_aligned` is `true` if and only if `sources` is non-empty and every source has `aligned: true`.

---

## 3. `generate_release_checklist`

### Purpose

Return a deterministic, ordered list of release checklist items for the given
version. No filesystem reads occur beyond resolving `repo_path`. No network access.

### Input

| Field       | Type   | Required | Description                                                    |
|-------------|--------|----------|----------------------------------------------------------------|
| `repo_path` | string | yes      | Absolute or relative path to the repository root               |
| `version`   | string | yes      | Target release version string, e.g. `"v0.1.0"`               |

### Output

```json
{
  "repo_path":      "<resolved absolute path>",
  "version":        "v0.1.0",
  "checklist": [
    {
      "item":     "<action description>",
      "category": "<category>",
      "required": true
    }
  ],
  "total":          10,
  "required_count": 7
}
```

### Fixed checklist items (ordered)

| # | `category`      | `required` | `item`                                                              |
|---|-----------------|------------|---------------------------------------------------------------------|
| 1 | `hygiene`       | `true`     | Repository working tree is clean (no uncommitted or untracked changes) |
| 2 | `versioning`    | `true`     | Version string updated in pyproject.toml or package.json           |
| 3 | `documentation` | `true`     | CHANGELOG updated with entries for this release                    |
| 4 | `quality`       | `true`     | All tests pass locally                                             |
| 5 | `versioning`    | `true`     | Git tag `<version>` created and pushed to remote *(version-stamped)* |
| 6 | `documentation` | `false`    | README reflects current feature set and usage                      |
| 7 | `hygiene`       | `true`     | LICENSE file present in repository root                            |
| 8 | `hygiene`       | `true`     | No debug or temporary code committed                               |
| 9 | `quality`       | `false`    | Dependencies pinned or bounded appropriately in lock file          |
| 10 | `release`      | `false`    | Release artifacts built, tested, and verified                      |

Row 5 has its `item` string stamped with the `version` parameter at call time,
making output deterministic per `(repo_path, version)` pair.

**Determinism guarantee:** Given identical `repo_path` and `version` inputs,
`generate_release_checklist` always returns byte-for-byte identical JSON output.
