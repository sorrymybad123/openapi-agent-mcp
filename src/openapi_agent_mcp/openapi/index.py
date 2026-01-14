from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Operation:
    operationId: str
    method: str
    path: str
    tags: list[str]
    summary: str | None
    description: str | None


HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


def build_operations(spec: dict[str, Any]) -> tuple[list[Operation], dict[str, Operation]]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI document missing 'paths' or has invalid structure")

    operations: list[Operation] = []
    by_id: dict[str, Operation] = {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            method_up = str(method).upper()
            if method_up not in HTTP_METHODS:
                continue
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if not op_id or not isinstance(op_id, str):
                continue
            if op_id in by_id:
                raise ValueError(f"Duplicate operationId: {op_id}")

            tags = op.get("tags") if isinstance(op.get("tags"), list) else []
            tags_out = [str(t) for t in tags if isinstance(t, (str, int, float))]

            operation = Operation(
                operationId=op_id,
                method=method_up,
                path=str(path),
                tags=tags_out,
                summary=op.get("summary") if isinstance(op.get("summary"), str) else None,
                description=op.get("description") if isinstance(op.get("description"), str) else None,
            )
            operations.append(operation)
            by_id[op_id] = operation

    return operations, by_id


def _maybe_match(value: str | None, query: str) -> bool:
    if not value:
        return False
    return query in value.lower()


def search_operations(
    *,
    operations: Iterable[Operation],
    query: str,
    match: dict[str, bool],
    method: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    q = query.strip().lower()
    method_up = method.upper() if method else None
    out: list[dict[str, Any]] = []

    for op in operations:
        if method_up and op.method != method_up:
            continue

        if q:
            ok = False
            if match.get("operationId", True) and _maybe_match(op.operationId, q):
                ok = True
            if not ok and match.get("path", True) and _maybe_match(op.path, q):
                ok = True
            if not ok and match.get("tag", True) and any(q in t.lower() for t in op.tags):
                ok = True
            if not ok and match.get("summary", True) and _maybe_match(op.summary, q):
                ok = True
            if not ok and match.get("description", True) and _maybe_match(op.description, q):
                ok = True
            if not ok:
                continue

        out.append(
            {
                "operationId": op.operationId,
                "method": op.method,
                "path": op.path,
                "tags": op.tags,
                "summary": op.summary,
                "description": op.description,
            }
        )
        if len(out) >= limit:
            break

    return out

