# mcp-release-guardian

Deterministic MCP server for validating release hygiene in local repositories. Network-free, read-only, governance-grade outputs.

---

## Overview

`mcp-release-guardian` exposes three tools via the [Model Context Protocol](https://modelcontextprotocol.io/):

| Tool | What it does |
|------|-------------|
| `check_repo_hygiene` | Six read-only checks: git repo state, README, LICENSE, CHANGELOG |
| `check_version_alignment` | Compares `pyproject.toml` / `package.json` / git tag versions |
| `generate_release_checklist` | Returns a deterministic ordered checklist for a release |

All tools are:
- **Network-free** — no external API calls, ever
- **Read-only** — no writes to the target repository
- **Fail-closed** — errors mark checks as failed, not as passed

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

```json
{
  "tool": "check_repo_hygiene",
  "arguments": { "repo_path": "/path/to/my-project" }
}
```

Example response:

```json
{
  "repo_path": "/path/to/my-project",
  "checks": [
    { "name": "is_git_repo",        "passed": true, "detail": "..." },
    { "name": "clean_working_tree", "passed": true, "detail": "Working tree is clean" },
    { "name": "no_untracked_files", "passed": true, "detail": "No untracked files" },
    { "name": "has_readme",         "passed": true, "detail": "Found README.md" },
    { "name": "has_license",        "passed": true, "detail": "Found LICENSE" },
    { "name": "has_changelog",      "passed": true, "detail": "Found CHANGELOG.md" }
  ],
  "all_passed": true
}
```

### check_version_alignment

```json
{
  "tool": "check_version_alignment",
  "arguments": {
    "repo_path": "/path/to/my-project",
    "expected_tag": "v1.2.0"
  }
}
```

### generate_release_checklist

```json
{
  "tool": "generate_release_checklist",
  "arguments": {
    "repo_path": "/path/to/my-project",
    "version": "v1.2.0"
  }
}
```

---

## Development

```bash
git clone https://github.com/YOUR_ORG/mcp-release-guardian.git
cd mcp-release-guardian
pip install -e ".[dev]"
pytest -q
```

See [`docs/V1_CONTRACT.md`](docs/V1_CONTRACT.md) for the frozen tool contracts
and [`docs/DETERMINISM_NOTES.md`](docs/DETERMINISM_NOTES.md) for the
determinism and fail-closed design rationale.

---

## License

MIT — see [LICENSE](LICENSE).
