from __future__ import annotations

from typing import Any

from ..errors import ToolError
from .index import HTTP_METHODS


def find_operation(spec: dict[str, Any], operation_id: str) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise ToolError(code="OPENAPI_INVALID", message="OpenAPI document missing 'paths' or has invalid structure")

    found: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            method_up = str(method).upper()
            if method_up not in HTTP_METHODS:
                continue
            if not isinstance(op, dict):
                continue
            if op.get("operationId") == operation_id:
                found.append((method_up, str(path), op, path_item))

    if not found:
        raise ToolError(
            code="OPERATION_NOT_FOUND",
            message=f"operationId not found: {operation_id}",
            details={"operationId": operation_id},
        )
    if len(found) > 1:
        raise ToolError(
            code="OPERATION_NOT_UNIQUE",
            message=f"operationId is not unique: {operation_id}",
            details={"operationId": operation_id, "matches": [{"method": m, "path": p} for m, p, _, _ in found]},
        )
    return found[0]

