from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "submit_indexnow.py"
spec = importlib.util.spec_from_file_location("submit_indexnow", MODULE_PATH)
indexnow = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(indexnow)


class IndexNowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.site_manifest = {
            "record_count": 2,
            "pages": [
                {"id": "ted-1", "url": "https://syfaadelia67-bot.github.io/radaria-licitaciones/opportunities/ted-1/"},
                {"id": "ted-2", "url": "https://syfaadelia67-bot.github.io/radaria-licitaciones/opportunities/ted-2/"},
            ],
        }
        self.brief_manifest = {
            "brief_url": "https://syfaadelia67-bot.github.io/radaria-licitaciones/brief/"
        }

    def test_collects_unique_canonical_urls(self) -> None:
        urls = indexnow.collect_urls(self.site_manifest, self.brief_manifest)
        self.assertEqual(4, len(urls))
        self.assertEqual("https://syfaadelia67-bot.github.io/radaria-licitaciones/", urls[0])
        self.assertIn("https://syfaadelia67-bot.github.io/radaria-licitaciones/brief/", urls)
        self.assertEqual(len(urls), len(set(urls)))

    def test_rejects_external_or_tracking_urls(self) -> None:
        external = dict(self.site_manifest)
        external["pages"] = [{"url": "https://example.com/opportunity/"}]
        with self.assertRaisesRegex(ValueError, "outside the verified"):
            indexnow.collect_urls(external, self.brief_manifest)

        tracking = dict(self.site_manifest)
        tracking["pages"] = [{"url": "https://syfaadelia67-bot.github.io/radaria-licitaciones/opportunities/ted-1/?source=test"}]
        with self.assertRaisesRegex(ValueError, "canonical"):
            indexnow.collect_urls(tracking, self.brief_manifest)

    def test_key_file_name_must_match_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid = Path(directory) / "abcdef1234567890.txt"
            valid.write_text("abcdef1234567890\n", encoding="utf-8")
            self.assertEqual("abcdef1234567890", indexnow.load_key(valid))

            invalid = Path(directory) / "different.txt"
            invalid.write_text("abcdef1234567890\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "filename"):
                indexnow.load_key(invalid)

    def test_payload_uses_public_key_location(self) -> None:
        urls = indexnow.collect_urls(self.site_manifest, self.brief_manifest)
        payload = indexnow.build_payload(urls, "abcdef1234567890")
        self.assertEqual("syfaadelia67-bot.github.io", payload["host"])
        self.assertEqual("abcdef1234567890", payload["key"])
        self.assertEqual(
            "https://syfaadelia67-bot.github.io/radaria-licitaciones/abcdef1234567890.txt",
            payload["keyLocation"],
        )
        self.assertEqual(urls, payload["urlList"])


if __name__ == "__main__":
    unittest.main()
