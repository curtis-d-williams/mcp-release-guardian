# mcp-release-guardian

Deterministic MCP server for validating release hygiene in local repositories. Network-free, read-only, governance-grade outputs.

---

## Overview

`mcp-release-guardian` exposes three tools via the [Model Context Protocol](https://modelcontextprotocol.io/):

| Tool | What it does |
|------|-------------|
| `check_repo_hygiene` | Seven file/directory presence checks: package definition, LICENSE, README, bug report template, CI workflows, V1 contract doc, determinism notes doc |
| `check_version_alignment` | Reads `pyproject.toml [project].version` and compares it to an optional expected tag |
| `generate_release_checklist` | Generates a deterministic markdown checklist based on local repo state |

All tools are:
- **Network-free** — no external API calls, ever
- **Read-only** — no writes to the target repository
- **Fail-closed** — unresolvable state marks that result as failed, not passed

---

## Quickstart

### Install

```bash
pip install mcp-release-guardian
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install mcp-release-guardian
```

### Run the server manually

```bash
mcp-release-guardian
```

The server starts on **stdio** and waits for MCP messages.

---

## Claude Desktop configuration

Add the following block to your `claude_desktop_config.json`
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "mcp-release-guardian": {
      "command": "mcp-release-guardian",
      "args": []
    }
  }
}
```

If you installed with `uv tool`:

```json
{
  "mcpServers": {
    "mcp-release-guardian": {
      "command": "uvx",
      "args": ["mcp-release-guardian"]
    }
  }
}
```

Restart Claude Desktop after editing the config.

---

## Tool usage examples

### check_repo_hygiene

Input:

```json
{
  "repo_path": "/ABS/PATH/TO/REPO"
}
```

Example response:

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

`ok` is `true` only when all seven checks pass. `fail_closed` equals `not ok`.

---

### check_version_alignment

Input:

```json
{
  "repo_path": "/path/to/my-project",
  "expected_tag": "v1.2.0"
}
```

`expected_tag` is optional. When omitted, the tool returns version metadata without performing a comparison.

Example response (match):

```json
{
  "tool": "check_version_alignment",
  "repo_path": "/path/to/my-project",
  "ok": true,
  "expected_tag": "v1.2.0",
  "detected": {
    "version": "1.2.0",
    "source": "pyproject.toml"
  },
  "details": "Version 1.2.0 matches expected tag v1.2.0",
  "fail_closed": false
}
```

Example response (version absent — fail-closed):

```json
{
  "tool": "check_version_alignment",
  "repo_path": "/path/to/my-project",
  "ok": false,
  "expected_tag": "v1.2.0",
  "detected": {
    "version": null,
    "source": null
  },
  "details": "Could not detect version: pyproject.toml missing or [project].version absent",
  "fail_closed": true
}
```

Version is read exclusively from `pyproject.toml [project].version`. The leading `v` in `expected_tag` is stripped before comparison.

---

### generate_release_checklist

Input:

```json
{
  "repo_path": "/path/to/my-project",
  "target_tag": "v1.2.0"
}
```

Example response:

```json
{
  "tool": "generate_release_checklist",
  "repo_path": "/path/to/my-project",
  "target_tag": "v1.2.0",
  "checklist_markdown": "# Release Checklist — v1.2.0\n\n## Version alignment\n...",
  "inputs_used": {
    "detected_version": "1.2.0",
    "has_ci_workflows": true,
    "has_bug_template": true
  },
  "fail_closed": false
}
```

`fail_closed` is `true` when `detected_version` is `null` (version undetectable). The checklist covers: version alignment, test run, tag creation, release notes, and adoption hooks verification.

---

## Development

```bash
git clone https://github.com/YOUR_ORG/mcp-release-guardian.git
cd mcp-release-guardian
pip install -e .
pytest -q
```

See [`docs/V1_CONTRACT.md`](docs/V1_CONTRACT.md) for the frozen tool contracts
and [`docs/DETERMINISM_NOTES.md`](docs/DETERMINISM_NOTES.md) for the
determinism and fail-closed design rationale.

See [docs/EXAMPLE_OUTPUTS.md](docs/EXAMPLE_OUTPUTS.md) for canonical example outputs.

---

## License

MIT — see [LICENSE](LICENSE).
