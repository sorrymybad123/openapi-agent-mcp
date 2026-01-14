from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from .openapi.cache import ensure_dir, write_json_atomic
from .openapi.store import OpenAPIStore
from .tools.get_request_schema import get_request_schema
from .tools.get_response_schema import get_response_schema
from .tools.search_operations import search_operations


def _store_from_args(args: argparse.Namespace) -> OpenAPIStore:
    return OpenAPIStore(
        base_url=args.base_url,
        cache_dir=Path(args.cache_dir),
        cache_ttl_seconds=int(args.cache_ttl_seconds),
        timeout_seconds=float(args.timeout_seconds),
    )


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2, sort_keys=False)
    sys.stdout.write("\n")


def cmd_fetch(args: argparse.Namespace) -> int:
    store = _store_from_args(args)
    _spec, meta = store.load()
    _print_json(meta)
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    store = _store_from_args(args)
    _spec, meta = store.load()
    operations = search_operations(store=store, query="", match=None, method=None, limit=10_000)
    payload = {
        "generated_at": int(time.time()),
        "source": {"baseUrl": args.base_url, "url": meta.get("url"), "sha256": meta.get("sha256")},
        "operations": operations if isinstance(operations, list) else [],
    }

    if args.out:
        out_path = Path(args.out)
        ensure_dir(out_path.parent)
        write_json_atomic(out_path, payload)
    else:
        _print_json(payload)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    store = _store_from_args(args)
    result = search_operations(
        store=store,
        query=args.query or "",
        match=None,
        method=args.method,
        limit=int(args.limit),
    )
    _print_json(result)
    return 0


def cmd_schema_request(args: argparse.Namespace) -> int:
    store = _store_from_args(args)
    result = get_request_schema(
        store=store,
        operationId=args.operation_id,
        deref_max_depth=int(args.deref_max_depth),
        deref_max_nodes=int(args.deref_max_nodes),
    )
    _print_json(result)
    return 0


def cmd_schema_response(args: argparse.Namespace) -> int:
    store = _store_from_args(args)
    result = get_response_schema(
        store=store,
        operationId=args.operation_id,
        deref_max_depth=int(args.deref_max_depth),
        deref_max_nodes=int(args.deref_max_nodes),
    )
    _print_json(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="openapi-agent-mcp")
    p.add_argument("--base-url", required=True, help="Service base URL (e.g. http://localhost:8000)")
    p.add_argument("--cache-dir", default=".cache", help="Cache directory (default: .cache)")
    p.add_argument("--cache-ttl-seconds", default="0", help="Optional TTL to skip refetching (default: 0)")
    p.add_argument("--timeout-seconds", default="10", help="HTTP timeout seconds (default: 10)")
    p.add_argument("--deref-max-depth", default="20", help="Max deref depth (default: 20)")
    p.add_argument("--deref-max-nodes", default="20000", help="Max deref nodes (default: 20000)")

    sub = p.add_subparsers(dest="cmd", required=True)

    fetch = sub.add_parser("fetch", help="Fetch /openapi.json and print cache metadata")
    fetch.set_defaults(func=cmd_fetch)

    index = sub.add_parser("index", help="Build operation index and write to file/stdout")
    index.add_argument("--out", help="Output file path (e.g. .cache/index.json)")
    index.set_defaults(func=cmd_index)

    search = sub.add_parser("search", help="Search operations")
    search.add_argument("--query", default="", help="Search query (substring match)")
    search.add_argument("--method", default=None, help="HTTP method filter (GET/POST/...)")
    search.add_argument("--limit", default="50", help="Max results (default: 50)")
    search.set_defaults(func=cmd_search)

    schema = sub.add_parser("schema", help="Print request/response schema for an operationId")
    schema_sub = schema.add_subparsers(dest="schema_cmd", required=True)

    req = schema_sub.add_parser("request", help="Get request schema by operationId")
    req.add_argument("--operation-id", required=True)
    req.set_defaults(func=cmd_schema_request)

    resp = schema_sub.add_parser("response", help="Get response schema by operationId")
    resp.add_argument("--operation-id", required=True)
    resp.set_defaults(func=cmd_schema_response)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    rc = args.func(args)
    raise SystemExit(rc)

