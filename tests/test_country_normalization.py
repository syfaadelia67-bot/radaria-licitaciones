from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "normalize_country_names.py"
spec = importlib.util.spec_from_file_location("normalize_country_names", MODULE_PATH)
country_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(country_module)


class CountryNormalizationTests(unittest.TestCase):
    def test_normalizes_truncated_and_iso3_codes(self) -> None:
        records = [
            {"id": "a", "country": "PO", "provenance": {}},
            {"id": "b", "country": "CHE", "provenance": {}},
            {"id": "c", "country": "FRA", "provenance": {}},
        ]
        normalized = country_module.normalize_records(records)
        self.assertEqual(["Poland", "Switzerland", "France"], [item["country"] for item in normalized])
        for item in normalized:
            self.assertIn("country", item["provenance"]["normalized_fields"])

    def test_preserves_existing_country_names(self) -> None:
        record = {"id": "a", "country": "Germany", "provenance": {"generated_fields": ["category"]}}
        normalized = country_module.normalize_records([record])[0]
        self.assertEqual("Germany", normalized["country"])
        self.assertEqual(record["provenance"], normalized["provenance"])

    def test_rejects_unknown_country_codes(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unrecognized country code"):
            country_module.normalize_records([{"id": "a", "country": "ZZ"}])


if __name__ == "__main__":
    unittest.main()
