from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    base_url: str
    cache_dir: Path = Path(".cache")
    cache_ttl_seconds: int = 0
    request_timeout_seconds: float = 10.0
    deref_max_depth: int = 20
    deref_max_nodes: int = 20_000

    @staticmethod
    def from_env() -> "Config":
        base_url = os.environ.get("OPENAPI_BASE_URL", "").strip()
        if not base_url:
            raise ValueError("Missing required env var: OPENAPI_BASE_URL")

        cache_dir = Path(os.environ.get("OPENAPI_CACHE_DIR", ".cache"))
        cache_ttl_seconds = int(os.environ.get("OPENAPI_CACHE_TTL_SECONDS", "0"))
        request_timeout_seconds = float(os.environ.get("OPENAPI_REQUEST_TIMEOUT_SECONDS", "10"))
        deref_max_depth = int(os.environ.get("OPENAPI_DEREF_MAX_DEPTH", "20"))
        deref_max_nodes = int(os.environ.get("OPENAPI_DEREF_MAX_NODES", "20000"))

        return Config(
            base_url=base_url,
            cache_dir=cache_dir,
            cache_ttl_seconds=cache_ttl_seconds,
            request_timeout_seconds=request_timeout_seconds,
            deref_max_depth=deref_max_depth,
            deref_max_nodes=deref_max_nodes,
        )

