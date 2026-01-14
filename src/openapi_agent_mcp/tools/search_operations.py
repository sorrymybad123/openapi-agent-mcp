from __future__ import annotations

from typing import Any

from ..errors import ToolError, error_response
from ..openapi.index import search_operations as search_impl
from ..openapi.store import OpenAPIStore


def search_operations(
    *,
    store: OpenAPIStore,
    query: str = "",
    match: dict[str, bool] | None = None,
    method: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        if limit <= 0:
            raise ToolError(code="BAD_INPUT", message="limit must be > 0", details={"limit": limit})

        match_map = match or {"tag": True, "operationId": True, "path": True, "summary": True, "description": True}
        ops = store.operations()
        return search_impl(operations=ops, query=query or "", match=match_map, method=method, limit=int(limit))
    except ToolError as e:
        return error_response(e.code, e.message, e.details)

