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
        self.base_url = "https://jerechulze.github.io/radaria-licitaciones"
        self.site_manifest = {
            "record_count": 2,
            "pages": [
                {"id": "ted-1", "url": f"{self.base_url}/opportunities/ted-1/"},
                {"id": "ted-2", "url": f"{self.base_url}/opportunities/ted-2/"},
            ],
        }
        self.brief_manifest = {"brief_url": f"{self.base_url}/brief/"}

    def test_collects_unique_canonical_urls(self) -> None:
        urls = indexnow.collect_urls(self.site_manifest, self.brief_manifest, self.base_url)
        self.assertEqual(4, len(urls))
        self.assertEqual(f"{self.base_url}/", urls[0])
        self.assertIn(f"{self.base_url}/brief/", urls)
        self.assertEqual(len(urls), len(set(urls)))

    def test_rejects_external_or_tracking_urls(self) -> None:
        external = dict(self.site_manifest)
        external["pages"] = [{"url": "https://example.com/opportunity/"}]
        with self.assertRaisesRegex(ValueError, "outside the verified"):
            indexnow.collect_urls(external, self.brief_manifest, self.base_url)

        tracking = dict(self.site_manifest)
        tracking["pages"] = [{"url": f"{self.base_url}/opportunities/ted-1/?source=test"}]
        with self.assertRaisesRegex(ValueError, "canonical"):
            indexnow.collect_urls(tracking, self.brief_manifest, self.base_url)

    def test_rejects_invalid_base_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid HTTPS"):
            indexnow.normalize_base_url("http://example.com/project")

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
        urls = indexnow.collect_urls(self.site_manifest, self.brief_manifest, self.base_url)
        payload = indexnow.build_payload(urls, "abcdef1234567890", self.base_url)
        self.assertEqual("jerechulze.github.io", payload["host"])
        self.assertEqual("abcdef1234567890", payload["key"])
        self.assertEqual(
            f"{self.base_url}/abcdef1234567890.txt",
            payload["keyLocation"],
        )
        self.assertEqual(urls, payload["urlList"])


if __name__ == "__main__":
    unittest.main()