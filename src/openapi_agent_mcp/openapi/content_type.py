from __future__ import annotations

from typing import Any


def choose_content_type(content: dict[str, Any] | None) -> tuple[str | None, dict[str, Any] | None]:
    if not content:
        return None, None

    if "application/json" in content:
        return "application/json", content.get("application/json")

    first_key = next(iter(content.keys()), None)
    if first_key is None:
        return None, None
    return first_key, content.get(first_key)

