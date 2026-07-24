#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fetch_ted", ROOT / "scripts" / "fetch_ted.py")
assert SPEC and SPEC.loader
fetch_ted = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_ted)


class TedNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads((ROOT / "tests" / "fixtures" / "ted_search_response.json").read_text(encoding="utf-8"))
        self.retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def test_normalizes_fixture(self) -> None:
        records = fetch_ted.normalize_payload(self.payload, self.retrieved_at)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["source"], "TED")
        self.assertFalse(records[0]["synthetic"])
        self.assertEqual(records[0]["status"], "LIVE")
        self.assertTrue(records[0]["source_url"].startswith("https://ted.europa.eu/"))
        self.assertIn(records[0]["country"], {"Belgium", "Germany"})
        self.assertTrue(records[0]["keywords"])

    def test_finds_nested_results(self) -> None:
        nested = {"response": self.payload}
        self.assertEqual(len(fetch_ted.find_results(nested)), 2)

    def test_rejects_notice_without_deadline(self) -> None:
        notice = dict(self.payload["notices"][0])
        notice.pop("deadline-receipt-tender-date-lot")
        self.assertIsNone(fetch_ted.normalize_notice(notice, self.retrieved_at))


if __name__ == "__main__":
    unittest.main()
