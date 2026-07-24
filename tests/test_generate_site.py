from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_site.py"
spec = importlib.util.spec_from_file_location("generate_site", MODULE_PATH)
generate_site = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate_site)


class GenerateSiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = {
            "id": "ted-123456-2026",
            "synthetic": False,
            "title": "Cloud & security services",
            "description": "Managed cloud monitoring and incident response for a public authority.",
            "country": "Belgium",
            "region": "European Union",
            "category": "IT services",
            "keywords": ["cloud", "security", "CPV 72200000"],
            "value": 125000,
            "currency": "EUR",
            "published_at": "2026-07-24",
            "deadline": "2026-08-30",
            "source": "TED",
            "source_url": "https://ted.europa.eu/en/notice/123456-2026/xml",
            "status": "LIVE",
            "provenance": {
                "publication_number": "123456-2026",
                "retrieved_at": "2026-07-24T01:35:48+00:00",
                "generated_fields": ["category", "keywords"],
            },
        }
        self.metadata = {
            "status": "live",
            "source": "TED Search API v3",
            "retrieved_at": "2026-07-24T01:35:48+00:00",
            "record_count": 1,
        }

    def test_generates_page_sitemap_feed_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = generate_site.generate([self.record], self.metadata, root, "https://example.test/product")

            page = root / "opportunities" / "ted-123456-2026" / "index.html"
            self.assertTrue(page.exists())
            page_text = page.read_text(encoding="utf-8")
            self.assertIn("Cloud &amp; security services", page_text)
            self.assertIn('rel="canonical" href="https://example.test/product/opportunities/ted-123456-2026/"', page_text)
            self.assertIn("TenderSignal-generated classification", page_text)
            self.assertIn(self.record["source_url"], page_text)
            self.assertIn("Get a ranked fit report", page_text)
            self.assertIn("source=opportunity-page", page_text)
            self.assertIn("opportunityId=ted-123456-2026", page_text)
            self.assertIn(
                "originPage=https%3A%2F%2Fexample.test%2Fproduct%2Fopportunities%2Fted-123456-2026%2F",
                page_text,
            )

            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.test/product/opportunities/ted-123456-2026/", sitemap)
            self.assertNotIn("demo-", sitemap)

            feed = (root / "feed.xml").read_text(encoding="utf-8")
            self.assertIn("TenderSignal live opportunities", feed)
            self.assertIn("Cloud &amp; security services", feed)

            stored_manifest = json.loads((root / "data/live/generated-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest, stored_manifest)
            self.assertEqual(1, manifest["record_count"])

    def test_generation_is_deterministic_for_fixed_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            generate_site.generate([self.record], self.metadata, Path(first), "https://example.test")
            generate_site.generate([self.record], self.metadata, Path(second), "https://example.test")
            paths = [
                Path("opportunities/ted-123456-2026/index.html"),
                Path("sitemap.xml"),
                Path("feed.xml"),
                Path("data/live/generated-manifest.json"),
            ]
            for path in paths:
                self.assertEqual((Path(first) / path).read_bytes(), (Path(second) / path).read_bytes())

    def test_rejects_demo_or_unverified_records(self) -> None:
        invalid = dict(self.record)
        invalid["synthetic"] = True
        invalid["status"] = "DEMO"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "only verified LIVE"):
                generate_site.generate([invalid], self.metadata, Path(directory), "https://example.test")

    def test_does_not_delete_preexisting_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_page = root / "opportunities" / "ted-old" / "index.html"
            old_page.parent.mkdir(parents=True)
            old_page.write_text("last known valid page", encoding="utf-8")
            generate_site.generate([self.record], self.metadata, root, "https://example.test")
            self.assertEqual("last known valid page", old_page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
