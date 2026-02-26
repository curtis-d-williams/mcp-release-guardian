# Determinism Notes

This document explains the design constraints that make `mcp-release-guardian`
deterministic, provider-free, and fail-closed.

---

## Design boundary

`mcp-release-guardian` operates exclusively inside a single well-defined
boundary:

```
[ local filesystem ] + [ local git index ] → deterministic JSON
```

Nothing crosses that boundary:

- **No network calls.** The server never opens a TCP socket, resolves a DNS
  name, or contacts any external API (GitHub, PyPI, npm, etc.).
- **No provider SDKs.** There is no dependency on any LLM provider, cloud
  service SDK, or telemetry library.
- **Read-only against target repos.** Tools inspect files and run `git` in
  read-only mode (`git status`, `git tag --list`). No `git fetch`, `git push`,
  `git commit`, or any mutating command is ever issued.

---

## Sources of non-determinism eliminated

| Potential source                  | Mitigation                                                   |
|-----------------------------------|--------------------------------------------------------------|
| Network latency / availability    | No network access at all                                     |
| External API rate limits          | No external API calls                                        |
| LLM sampling / temperature        | No LLM calls; logic is pure Python                           |
| System clock / timestamps         | No timestamp reads in tool logic                             |
| Random number generation          | No random calls                                              |
| Python dict ordering (< 3.7)      | Python ≥ 3.11 required; dict insertion order is guaranteed   |
| Environment variables             | Tools do not read `os.environ` during check execution        |

---

## Fail-closed semantics

Every tool follows the same fail-closed contract:

> **When a check cannot be completed, the check is marked as failed — never
> as passed.**

Specific rules:

1. `check_repo_hygiene` — if `repo_path` is not a git repository, only the
   `is_git_repo` check is returned (marked `false`). Subsequent checks that
   would require a valid git repo are not run, not omitted silently, and not
   assumed to pass.

2. `check_version_alignment` — if `repo_path` does not exist, `sources` is
   `[]` and `all_aligned` is `false`. A parse error in any source file sets
   that source's `aligned` to `false` and `version` to `null`. If `sources`
   is empty, `all_aligned` is `false` (empty-is-failing, not empty-is-ok).

3. `generate_release_checklist` — purely deterministic; the path is resolved
   but not required to exist at call time. No fail-closed concern applies
   because no runtime state is read.

---

## Subprocess isolation

Git is invoked via `subprocess.run` with:

- `capture_output=True` — stdout and stderr are never written to the console
- `timeout=10` — a hung git process is killed and the relevant check is failed
- `cwd=<repo_path>` — git operations are scoped to the target repository
- **No shell=True** — arguments are passed as a list; no shell injection possible

---

## Reproducibility for issue reports

Because all checks are local and read-only, any failing result can be
reproduced exactly by re-running the same tool call against the same local
repo state. This is why the bug report issue template requires:

- Exact input JSON
- Full output JSON
- Confirmation that the repo was not modified by the tool
- Confirmation that the issue reproduces on a second run
