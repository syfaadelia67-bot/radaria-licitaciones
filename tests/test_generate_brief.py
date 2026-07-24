from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_brief.py"
spec = importlib.util.spec_from_file_location("generate_brief", MODULE_PATH)
generate_brief = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate_brief)


class GenerateBriefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            {
                "id": "ted-123456-2026",
                "synthetic": False,
                "title": "Cloud & security services",
                "description": "Managed cloud monitoring and incident response.",
                "country": "Belgium",
                "region": "European Union",
                "category": "IT services",
                "keywords": ["cloud", "security"],
                "value": 125000,
                "currency": "EUR",
                "published_at": "2026-07-24",
                "deadline": "2026-08-30",
                "source": "TED",
                "source_url": "https://ted.europa.eu/en/notice/123456-2026/xml",
                "status": "LIVE",
            },
            {
                "id": "ted-654321-2026",
                "synthetic": False,
                "title": "Data platform support",
                "description": "Support for a public data platform.",
                "country": "France",
                "region": "European Union",
                "category": "IT services",
                "keywords": ["data", "support"],
                "value": 0,
                "currency": "XXX",
                "published_at": "2026-07-25",
                "deadline": "2026-08-15",
                "source": "TED",
                "source_url": "https://ted.europa.eu/en/notice/654321-2026/xml",
                "status": "LIVE",
            },
        ]
        self.metadata = {
            "status": "live",
            "source": "TED Search API v3",
            "retrieved_at": "2026-07-25T06:17:00+00:00",
            "record_count": 2,
        }

    def test_generates_public_brief_posts_sitemap_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = generate_brief.generate(self.records, self.metadata, root, "https://example.test/product")

            page = (root / "brief/index.html").read_text(encoding="utf-8")
            self.assertIn("2 current public-procurement opportunities", page)
            self.assertIn("Cloud &amp; security services", page)
            self.assertIn("not a recommendation", page)
            self.assertIn("No payment is collected", page)

            markdown = (root / "brief/latest.md").read_text(encoding="utf-8")
            self.assertIn("Verified notices: **2**", markdown)
            self.assertIn("Value not disclosed", markdown)

            posts = (root / "distribution/latest-posts.md").read_text(encoding="utf-8")
            self.assertIn("Review each community's rules", posts)
            self.assertNotIn("limited spots", posts.lower())
            self.assertNotIn("customers", posts.lower())

            sitemap = (root / "brief-sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.test/product/brief/", sitemap)

            stored = json.loads((root / "data/live/brief-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest, stored)
            self.assertEqual(2, manifest["record_count"])

    def test_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            generate_brief.generate(self.records, self.metadata, Path(first), "https://example.test")
            generate_brief.generate(self.records, self.metadata, Path(second), "https://example.test")
            for relative in (
                "brief/index.html",
                "brief/latest.md",
                "distribution/latest-posts.md",
                "brief-sitemap.xml",
                "data/live/brief-manifest.json",
            ):
                self.assertEqual((Path(first) / relative).read_bytes(), (Path(second) / relative).read_bytes())

    def test_rejects_demo_records(self) -> None:
        invalid = dict(self.records[0])
        invalid["synthetic"] = True
        invalid["status"] = "DEMO"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "verified LIVE"):
                generate_brief.generate([invalid], self.metadata, Path(directory), "https://example.test")


if __name__ == "__main__":
    unittest.main()
