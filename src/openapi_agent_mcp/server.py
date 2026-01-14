from __future__ import annotations

from .config import Config
from .openapi.store import OpenAPIStore
from .tools.get_request_schema import get_request_schema
from .tools.get_response_schema import get_response_schema
from .tools.search_operations import search_operations


def create_server():
    from mcp.server.fastmcp import FastMCP

    cfg = Config.from_env()
    store = OpenAPIStore(
        base_url=cfg.base_url,
        cache_dir=cfg.cache_dir,
        cache_ttl_seconds=cfg.cache_ttl_seconds,
        timeout_seconds=cfg.request_timeout_seconds,
    )

    mcp = FastMCP("openapi-agent-mcp")

    @mcp.tool()
    def search_operations_tool(
        query: str = "",
        match: dict[str, bool] | None = None,
        method: str | None = None,
        limit: int = 50,
    ):
        return search_operations(store=store, query=query, match=match, method=method, limit=limit)

    @mcp.tool()
    def get_request_schema_tool(operationId: str):
        return get_request_schema(
            store=store,
            operationId=operationId,
            deref_max_depth=cfg.deref_max_depth,
            deref_max_nodes=cfg.deref_max_nodes,
        )

    @mcp.tool()
    def get_response_schema_tool(operationId: str):
        return get_response_schema(
            store=store,
            operationId=operationId,
            deref_max_depth=cfg.deref_max_depth,
            deref_max_nodes=cfg.deref_max_nodes,
        )

    return mcp


def main() -> None:
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    main()
