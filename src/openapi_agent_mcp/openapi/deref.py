from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DerefResult:
    schema: Any
    kept_ref: bool


def schema_contains_ref(schema: Any) -> bool:
    if isinstance(schema, dict):
        if "$ref" in schema:
            return True
        return any(schema_contains_ref(v) for v in schema.values())
    if isinstance(schema, list):
        return any(schema_contains_ref(v) for v in schema)
    return False


def _resolve_local_ref(spec: dict[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs are supported, got: {ref}")
    parts = ref[2:].split("/")
    current: Any = spec
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Unresolvable ref: {ref}")
        current = current[part]
    return current


def deref_schema(
    schema: Any,
    *,
    spec: dict[str, Any],
    max_depth: int,
    max_nodes: int,
) -> DerefResult:
    node_budget = {"count": 0}

    def walk(value: Any, *, depth: int, ref_stack: tuple[str, ...]) -> DerefResult:
        node_budget["count"] += 1
        if node_budget["count"] > max_nodes or depth > max_depth:
            return DerefResult(schema=value, kept_ref=schema_contains_ref(value))

        if isinstance(value, list):
            kept = False
            out: list[Any] = []
            for item in value:
                res = walk(item, depth=depth + 1, ref_stack=ref_stack)
                kept = kept or res.kept_ref
                out.append(res.schema)
            return DerefResult(schema=out, kept_ref=kept)

        if isinstance(value, dict):
            if "$ref" in value and isinstance(value.get("$ref"), str):
                ref = value["$ref"]
                if ref in ref_stack:
                    return DerefResult(schema={"$ref": ref}, kept_ref=True)

                target = _resolve_local_ref(spec, ref)
                resolved = walk(target, depth=depth + 1, ref_stack=ref_stack + (ref,))
                if not isinstance(resolved.schema, dict):
                    return DerefResult(schema=resolved.schema, kept_ref=resolved.kept_ref)

                merged: dict[str, Any] = dict(resolved.schema)
                kept = resolved.kept_ref
                for k, v in value.items():
                    if k == "$ref":
                        continue
                    sub = walk(v, depth=depth + 1, ref_stack=ref_stack)
                    merged[k] = sub.schema
                    kept = kept or sub.kept_ref
                return DerefResult(schema=merged, kept_ref=kept)

            kept = False
            out: dict[str, Any] = {}
            for k, v in value.items():
                res = walk(v, depth=depth + 1, ref_stack=ref_stack)
                kept = kept or res.kept_ref
                out[k] = res.schema
            return DerefResult(schema=out, kept_ref=kept)

        return DerefResult(schema=value, kept_ref=False)

    return walk(schema, depth=0, ref_stack=())

