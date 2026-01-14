from __future__ import annotations

from typing import Any

from ..errors import ToolError, error_response
from ..openapi.content_type import choose_content_type
from ..openapi.deref import deref_schema
from ..openapi.lookup import find_operation
from ..openapi.store import OpenAPIStore


def _empty_param_object() -> dict[str, Any]:
    return {"type": "object", "properties": {}, "required": []}


def _parameter_schema(spec: dict[str, Any], param: dict[str, Any]) -> Any:
    if isinstance(param.get("schema"), dict):
        return param["schema"]

    content = param.get("content")
    if isinstance(content, dict):
        selected, media = choose_content_type(content)
        if media and isinstance(media.get("schema"), dict):
            return media["schema"]
    raise ToolError(
        code="PARAM_SCHEMA_MISSING",
        message="Parameter schema missing and cannot be inferred",
        details={"name": param.get("name"), "in": param.get("in")},
    )


def get_request_schema(
    *,
    store: OpenAPIStore,
    operationId: str,
    deref_max_depth: int,
    deref_max_nodes: int,
) -> dict[str, Any]:
    try:
        spec, _meta = store.load()
        method, path, op, path_item = find_operation(spec, operationId)

        params = {"path": _empty_param_object(), "query": _empty_param_object(), "header": _empty_param_object(), "cookie": _empty_param_object()}
        required_by_in: dict[str, set[str]] = {k: set() for k in params.keys()}

        combined_params: list[Any] = []
        if isinstance(path_item.get("parameters"), list):
            combined_params.extend(path_item["parameters"])
        if isinstance(op.get("parameters"), list):
            combined_params.extend(op["parameters"])

        kept_ref = False
        for p in combined_params:
            if not isinstance(p, dict):
                continue
            p_in = p.get("in")
            name = p.get("name")
            if p_in not in params or not isinstance(name, str) or not name:
                continue

            schema = _parameter_schema(spec, p)
            res = deref_schema(schema, spec=spec, max_depth=deref_max_depth, max_nodes=deref_max_nodes)
            kept_ref = kept_ref or res.kept_ref

            params[p_in]["properties"][name] = res.schema

            is_required = bool(p.get("required", False)) or p_in == "path"
            if is_required:
                required_by_in[p_in].add(name)

        for loc, req in required_by_in.items():
            params[loc]["required"] = sorted(req)

        body_obj = {"selectedContentType": None, "required": False, "schema": {}}
        request_body = op.get("requestBody")
        if request_body is None:
            pass
        elif isinstance(request_body, dict):
            content = request_body.get("content")
            if not isinstance(content, dict):
                raise ToolError(code="REQUEST_BODY_MISSING", message="requestBody.content missing or invalid")

            selected, media = choose_content_type(content)
            if selected is None or not isinstance(media, dict):
                raise ToolError(code="REQUEST_BODY_MISSING", message="requestBody.content is empty")

            schema = media.get("schema")
            if not isinstance(schema, dict):
                raise ToolError(code="REQUEST_BODY_SCHEMA_MISSING", message="requestBody schema missing and cannot be inferred")

            res = deref_schema(schema, spec=spec, max_depth=deref_max_depth, max_nodes=deref_max_nodes)
            kept_ref = kept_ref or res.kept_ref

            body_obj = {"selectedContentType": selected, "required": bool(request_body.get("required", False)), "schema": res.schema}
        else:
            raise ToolError(code="REQUEST_BODY_INVALID", message="requestBody must be an object when present")

        components = spec.get("components", {}) if kept_ref else {}

        return {
            "operationId": operationId,
            "method": method,
            "path": path,
            "params": params,
            "body": body_obj,
            "components": components if isinstance(components, dict) else {},
        }
    except ToolError as e:
        return error_response(e.code, e.message, e.details)
    except Exception as e:  # pragma: no cover - defensive
        return error_response("INTERNAL_ERROR", str(e), {})

