from __future__ import annotations

from typing import Any

from ..errors import ToolError, error_response
from ..openapi.content_type import choose_content_type
from ..openapi.deref import deref_schema
from ..openapi.lookup import find_operation
from ..openapi.store import OpenAPIStore


def get_response_schema(
    *,
    store: OpenAPIStore,
    operationId: str,
    deref_max_depth: int,
    deref_max_nodes: int,
) -> dict[str, Any]:
    try:
        spec, _meta = store.load()
        method, path, op, _path_item = find_operation(spec, operationId)

        responses = op.get("responses")
        if not isinstance(responses, dict):
            raise ToolError(code="RESPONSES_MISSING", message="responses missing or invalid")

        out: dict[str, Any] = {}
        kept_ref = False

        for status_code, resp in responses.items():
            key = str(status_code)
            if not isinstance(resp, dict):
                out[key] = {"selectedContentType": None, "schema": {}}
                continue

            content = resp.get("content")
            selected, media = choose_content_type(content if isinstance(content, dict) else None)
            if selected is None or not isinstance(media, dict):
                out[key] = {"selectedContentType": None, "schema": {}}
                continue

            schema = media.get("schema")
            if not isinstance(schema, dict):
                raise ToolError(
                    code="RESPONSE_SCHEMA_MISSING",
                    message="response schema missing and cannot be inferred",
                    details={"statusCode": key},
                )

            res = deref_schema(schema, spec=spec, max_depth=deref_max_depth, max_nodes=deref_max_nodes)
            kept_ref = kept_ref or res.kept_ref
            out[key] = {"selectedContentType": selected, "schema": res.schema}

        components = spec.get("components", {}) if kept_ref else {}

        return {
            "operationId": operationId,
            "method": method,
            "path": path,
            "responses": out,
            "components": components if isinstance(components, dict) else {},
        }
    except ToolError as e:
        return error_response(e.code, e.message, e.details)
    except Exception as e:  # pragma: no cover - defensive
        return error_response("INTERNAL_ERROR", str(e), {})

