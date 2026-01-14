# Repository Guidelines

This repository currently contains a single source of truth: the specification for an “OpenAPI Agent” MCP server that inspects a FastAPI `/openapi.json` and produces request/response schemas for downstream callers.

## Project Structure & Module Organization

- `openapi_agent_mcp_spec.md`: Protocol/specification (tools, inputs/outputs, schema conventions). Treat this as the canonical reference.
- (When implementation is added) prefer a conventional layout:
  - `src/` (or `openapi_mcp/`) for runtime code
  - `tests/` for automated tests
  - `examples/` for sample OpenAPI payloads and expected tool outputs

## Build, Test, and Development Commands

There is no build/test harness in the current repo state (spec-only).

If you add an implementation, include a minimal, copy/paste-friendly command set in `README.md`, for example:

- `make lint` / `make test` / `make run` (preferred), or
- `python -m pytest` (Python) / `npm test` (Node), matching the chosen stack.

## Coding Style & Naming Conventions

- Markdown: use clear headings, short paragraphs, and fenced code blocks with language tags (e.g. ```json).
- JSON in docs/examples: 2-space indentation; keep keys stable to minimize diffs.
- Naming: use `snake_case` for markdown filenames and example fixtures; use explicit names (avoid `tmp`, `test1`).

If introducing code, add a formatter/linter config in the same PR and keep CI/tooling commands documented.

## Testing Guidelines

No test framework is configured yet. New code should include unit tests for:

- operation search/filtering behavior
- `$ref` dereferencing rules (including cycles)
- content-type selection (`application/json` preference)

Name tests `test_*.py` (Python) or `*.test.ts` (TypeScript), consistent with the chosen stack.

## Commit & Pull Request Guidelines

- Commits: use a conventional, descriptive prefix (e.g. `spec:`, `feat:`, `fix:`, `chore:`).
- PRs: include purpose, spec impact, and any backward-compat notes; update examples when changing outputs.

## Security & Configuration Tips

- Do not commit secrets or environment-specific base URLs.
- Treat fetched OpenAPI specs as untrusted input; validate and cap recursion/depth when dereferencing schemas.
