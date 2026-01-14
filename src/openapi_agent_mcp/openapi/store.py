from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ToolError
from .fetch import fetch_openapi_spec
from .index import Operation, build_operations


@dataclass
class OpenAPIStore:
    base_url: str
    cache_dir: Path
    cache_ttl_seconds: int
    timeout_seconds: float

    _spec: dict[str, Any] | None = None
    _meta: dict[str, Any] | None = None
    _operations: list[Operation] | None = None
    _operation_by_id: dict[str, Operation] | None = None

    def load(self) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            spec, meta = fetch_openapi_spec(
                base_url=self.base_url,
                cache_dir=self.cache_dir,
                cache_ttl_seconds=self.cache_ttl_seconds,
                timeout_seconds=self.timeout_seconds,
            )
        except Exception as e:  # pragma: no cover - defensive
            raise ToolError(code="OPENAPI_FETCH_FAILED", message=str(e), details={"baseUrl": self.base_url})

        if self._meta is None or self._meta.get("sha256") != meta.get("sha256"):
            ops, by_id = build_operations(spec)
            self._spec = spec
            self._meta = meta
            self._operations = ops
            self._operation_by_id = by_id

        return self._spec or spec, self._meta or meta

    def operations(self) -> list[Operation]:
        self.load()
        return list(self._operations or [])

    def operation_by_id(self, operation_id: str) -> Operation | None:
        self.load()
        return (self._operation_by_id or {}).get(operation_id)

    def spec(self) -> dict[str, Any]:
        self.load()
        return self._spec or {}

