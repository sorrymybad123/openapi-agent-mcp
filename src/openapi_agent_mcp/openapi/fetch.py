from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from .cache import ensure_dir, read_json, write_bytes_atomic, write_json_atomic


def _openapi_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/openapi.json"


def fetch_openapi_spec(
    *,
    base_url: str,
    cache_dir: Path,
    cache_ttl_seconds: int,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Hash-based caching:
    - Always fetch unless TTL is enabled and still valid.
    - Store raw JSON and metadata (sha256, fetched_at, size_bytes).
    """

    ensure_dir(cache_dir)
    spec_path = cache_dir / "openapi.json"
    meta_path = cache_dir / "openapi.meta.json"

    if cache_ttl_seconds > 0 and spec_path.exists() and meta_path.exists():
        meta = read_json(meta_path)
        fetched_at = int(meta.get("fetched_at", 0))
        if fetched_at and (int(time.time()) - fetched_at) < cache_ttl_seconds:
            return read_json(spec_path), meta

    url = _openapi_url(base_url)
    req = urllib.request.Request(url, method="GET")

    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        hasher = hashlib.sha256()
        chunks: list[bytes] = []
        size_bytes = 0
        while True:
            chunk = resp.read(1024 * 64)
            if not chunk:
                break
            hasher.update(chunk)
            chunks.append(chunk)
            size_bytes += len(chunk)

    raw = b"".join(chunks)
    sha256 = hasher.hexdigest()
    fetched_at = int(time.time())

    write_bytes_atomic(spec_path, raw)
    meta = {"sha256": sha256, "fetched_at": fetched_at, "size_bytes": size_bytes, "url": url}
    write_json_atomic(meta_path, meta)

    return json.loads(raw.decode("utf-8")), meta

