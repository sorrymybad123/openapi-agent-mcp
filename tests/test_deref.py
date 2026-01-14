import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openapi_agent_mcp.openapi.deref import deref_schema


class DerefTests(unittest.TestCase):
    def test_cycle_ref_keeps_ref(self):
        spec = json.loads(Path("tests/fixtures/openapi_cycle_ref.json").read_text(encoding="utf-8"))
        schema = {"$ref": "#/components/schemas/User"}
        res = deref_schema(schema, spec=spec, max_depth=20, max_nodes=20000)

        self.assertTrue(res.kept_ref, "cycle should keep $ref somewhere")
        self.assertIsInstance(res.schema, dict)
        self.assertIn("properties", res.schema)
        self.assertEqual(res.schema["properties"]["manager"]["$ref"], "#/components/schemas/User")


if __name__ == "__main__":
    unittest.main()
