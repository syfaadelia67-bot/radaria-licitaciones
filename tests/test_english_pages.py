import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "generate_site.py"
spec = importlib.util.spec_from_file_location("generate_site", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class EnglishPageTests(unittest.TestCase):
    def base_record(self):
        return {
            "id": "ted-test-1",
            "synthetic": False,
            "title": "Supply of medical equipment",
            "description": "Supply of 12 medical devices for the regional hospital.",
            "country": "Poland",
            "category": "Medical equipment",
            "keywords": ["medical", "equipment"],
            "value": 250000,
            "currency": "PLN",
            "published_at": "2026-07-24",
            "deadline": "2026-08-31",
            "source": "TED",
            "source_url": "https://ted.europa.eu/en/notice/test/xml",
            "status": "LIVE",
            "provenance": {
                "publication_number": "test",
                "retrieved_at": "2026-07-24T00:00:00+00:00",
                "generated_fields": ["category", "keywords"],
            },
        }

    def test_machine_translation_exposes_original(self):
        record = self.base_record()
        record.update({
            "original_title": "Dostawa sprzętu medycznego",
            "original_description": "Dostawa 12 urządzeń medycznych dla szpitala regionalnego.",
            "translation": {
                "status": "machine_translated",
                "display_language": "en",
                "source_language": "Polish",
                "provider": "GitHub Models",
                "model": "openai/gpt-4.1-mini",
                "source_hash": "a" * 64,
                "translated_at": "2026-07-24T00:00:00+00:00",
            },
        })
        output = module.page_html(record, {"retrieved_at": "2026-07-24T00:00:00+00:00"}, module.BASE_URL)
        self.assertIn('lang="en"', output)
        self.assertIn("MACHINE-TRANSLATED ENGLISH", output)
        self.assertIn("Dostawa sprzętu medycznego", output)
        self.assertIn("official TED notice remains authoritative", output)

    def test_original_only_page_is_not_mislabeled_english(self):
        record = self.base_record()
        record["title"] = "Dostawa sprzętu medycznego"
        record["description"] = "Dostawa urządzeń medycznych dla szpitala regionalnego."
        record["translation"] = {
            "status": "original_only",
            "display_language": "original",
            "source_language": "undetermined",
            "source_hash": "b" * 64,
        }
        output = module.page_html(record, {"retrieved_at": "2026-07-24T00:00:00+00:00"}, module.BASE_URL)
        self.assertIn('lang="und"', output)
        self.assertIn("ORIGINAL LANGUAGE", output)
        self.assertNotIn("View authoritative original text", output)


if __name__ == "__main__":
    unittest.main()
