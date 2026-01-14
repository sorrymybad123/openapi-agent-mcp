# OpenAPI Agent MCP

An MCP server + CLI that consumes a FastAPI OpenAPI spec from `{baseUrl}/openapi.json` and exposes tools to:

- search operations (`search_operations`)
- get request schema (`get_request_schema`)
- get response schema (`get_response_schema`)

See `openapi_agent_mcp_spec.md` for the protocol and output conventions.
Community-friendly overview: `docs/README.md`.

## Development Setup

### Option A: Poetry (recommended)

```bash
# Install Poetry (one-time)
pipx install poetry  # or: pip install --user poetry

# From repo root
poetry install

# Run CLI
poetry run openapi-agent-mcp fetch --base-url http://localhost:8000
poetry run openapi-agent-mcp index --base-url http://localhost:8000 --out .cache/index.json
poetry run openapi-agent-mcp search --base-url http://localhost:8000 --query purchase --limit 5

# Run tests
poetry run python -m unittest
```

### Option B: Conda + Poetry

```bash
conda env create -f environment.yml
conda activate openapi-agent-mcp
poetry install
poetry run python -m unittest
```

## Quickstart (CLI)

```bash
openapi-agent-mcp fetch --base-url http://localhost:8000
openapi-agent-mcp index --base-url http://localhost:8000 --out .cache/index.json
openapi-agent-mcp search --base-url http://localhost:8000 --query purchase --limit 5
```

## MCP Server

The server is intended to be run by an MCP host. Configure `OPENAPI_BASE_URL` to point at the target service.

### Codex CLI MCP config

Add a server entry to your Codex config (typically `~/.codex/config.toml`):

```toml
[mcp_servers.openapi-agent-mcp]
command = "/root/miniconda3/bin/conda"
args = [
  "run", "--no-capture-output",
  "--cwd", "/home/mcp/openapi_mcp",
  "-n", "openapi-agent-mcp",
  "env",
  "OPENAPI_BASE_URL=http://localhost:5052",
  "OPENAPI_CACHE_DIR=.cache",
  "poetry", "run", "openapi-agent-mcp-server"
]
startup_timeout_sec = 60.0
```
