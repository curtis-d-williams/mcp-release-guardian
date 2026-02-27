# Adopting the mcp-release-guardian Governance Template

This template is a proven “minimum viable governance” scaffold for deterministic MCP servers.

## What you get
- Deterministic + network-free posture
- Fail-closed semantics documented
- Frozen V1 contract doc pattern
- Canonical example outputs workflow
- CI + PyPI install smoke workflow
- README badges + release discipline section

## How to use
1. Copy `template/` contents into a new repo root.
2. Rename:
   - package/module name in `pyproject_TEMPLATE.toml`
   - console script entrypoint
   - README title + badges URLs (repo path)
3. Replace `docs/*_TEMPLATE.md` content with your server’s contract and examples.
4. Run:
   - `pytest`
   - `python -m build`
   - `python -m twine check dist/*`
5. Publish to PyPI, then verify install in a fresh venv.

## Guardrails
- Do not change schema/JSON structure after V1 freeze without explicit reopening.
- Keep examples in `docs/EXAMPLE_OUTPUTS.md` aligned with README and behavior.
