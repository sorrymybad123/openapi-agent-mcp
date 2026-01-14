import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openapi_agent_mcp.openapi.index import build_operations
from openapi_agent_mcp.tools.get_response_schema import get_response_schema
from openapi_agent_mcp.tools.search_operations import search_operations


class FakeStore:
    def __init__(self, spec):
        self._spec = spec
        self._ops, self._by_id = build_operations(spec)

    def load(self):
        return self._spec, {"sha256": "test", "url": "http://example/openapi.json"}

    def operations(self):
        return self._ops


class ToolTests(unittest.TestCase):
    def test_search_operations_basic(self):
        spec = json.loads(Path("tests/fixtures/openapi_minimal.json").read_text(encoding="utf-8"))
        store = FakeStore(spec)
        res = search_operations(store=store, query="ping", match=None, method="GET", limit=10)
        self.assertIsInstance(res, list)
        self.assertEqual(res[0]["operationId"], "ping")

    def test_get_response_schema_returns_components_when_ref_kept(self):
        spec = json.loads(Path("tests/fixtures/openapi_cycle_ref.json").read_text(encoding="utf-8"))
        store = FakeStore(spec)
        res = get_response_schema(store=store, operationId="get_user", deref_max_depth=20, deref_max_nodes=20000)
        self.assertIn("responses", res)
        self.assertIn("components", res)
        self.assertIn("schemas", res["components"])
        self.assertIn("User", res["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
