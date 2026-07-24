import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "translate_to_english.py"
spec = importlib.util.spec_from_file_location("translate_to_english", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def record(title="Dostawa urządzeń", description="Dostawa 12 urządzeń za 250 000 PLN do dnia 2026-08-31."):
    return {
        "id": "ted-test-1",
        "title": title,
        "description": description,
        "source_url": "https://ted.europa.eu/en/notice/test/xml",
    }


class EnglishLayerTests(unittest.TestCase):
    def test_conservative_english_detection(self):
        self.assertTrue(module.likely_english(
            "Supply of network equipment",
            "The contract is for the supply and maintenance of network equipment with support services.",
        ))
        self.assertFalse(module.likely_english(
            "Dostawa urządzeń sieciowych",
            "Przedmiotem zamówienia jest dostawa urządzeń i świadczenie usług serwisowych.",
        ))

    def test_translation_must_preserve_numbers(self):
        source = record()
        good = {
            "id": "ted-test-1",
            "source_language": "Polish",
            "title_en": "Supply of equipment",
            "description_en": "Supply of 12 devices for 250 000 PLN by 2026-08-31.",
        }
        validated = module.validate_translation(source, good)
        self.assertEqual(validated["source_language"], "Polish")

        bad = dict(good)
        bad["description_en"] = "Supply of devices by the stated deadline."
        with self.assertRaises(ValueError):
            module.validate_translation(source, bad)

    def test_cached_translation_preserves_original(self):
        source = record()
        source_hash = module.content_hash(source)
        cache = {
            "ted-test-1": {
                "id": "ted-test-1",
                "source_hash": source_hash,
                "source_language": "Polish",
                "title_en": "Supply of equipment",
                "description_en": "Supply of 12 devices for 250 000 PLN by 2026-08-31.",
                "model": "test/model",
                "translated_at": "2026-07-24T00:00:00+00:00",
            }
        }
        translated, _, stats = module.translate_records([source], cache, None, "test/model", 6)
        item = translated[0]
        self.assertEqual(item["title"], "Supply of equipment")
        self.assertEqual(item["original_title"], "Dostawa urządzeń")
        self.assertEqual(item["translation"]["status"], "machine_translated")
        self.assertEqual(stats["cached"], 1)

    def test_missing_model_is_non_blocking(self):
        source = record()
        translated, _, stats = module.translate_records([source], {}, None, "test/model", 6)
        item = translated[0]
        self.assertEqual(item["title"], source["title"])
        self.assertEqual(item["translation"]["status"], "original_only")
        self.assertEqual(stats["original_only"], 1)

    def test_source_english_avoids_unnecessary_translation(self):
        source = record(
            "Supply of network equipment",
            "The contract is for the supply and maintenance of 12 network devices with support services.",
        )
        translated, _, stats = module.translate_records([source], {}, None, "test/model", 6)
        item = translated[0]
        self.assertEqual(item["translation"]["status"], "source_english")
        self.assertNotIn("original_title", item)
        self.assertEqual(stats["source_english"], 1)


if __name__ == "__main__":
    unittest.main()
