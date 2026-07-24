from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "score_founder_application.py"
spec = importlib.util.spec_from_file_location("score_founder_application", MODULE_PATH)
report_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(report_module)


class FounderReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qualified = {
            "company": "Example Cloud Studio",
            "markets": ["Belgium", "France"],
            "products_services": "Cloud migration, managed infrastructure, security monitoring and incident response for public-sector organizations.",
            "contract_capacity": "USD 50k–250k",
            "discovery_process": "We monitor public procurement portals and manually review tender documents before deciding whether to bid.",
            "useful_features": ["Ranked alerts", "Bid-or-skip brief", "Deadline monitoring"],
            "founder_interest": "Provisional USD 10 for 60 days",
            "opportunity_id": "ted-123456-2026",
        }

    def test_scores_qualified_application_and_renders_boundaries(self) -> None:
        result = report_module.score_application(self.qualified)
        self.assertGreaterEqual(result["score"], 70)
        self.assertEqual("Qualified founder candidate", result["band"])
        report = report_module.render_markdown(result)
        self.assertIn("not procurement, legal or eligibility advice", report)
        self.assertIn("No payment should be requested until", report)
        self.assertIn("ted-123456-2026", report)

    def test_rejects_personal_contact_fields(self) -> None:
        payload = dict(self.qualified)
        payload["email"] = "person@example.com"
        with self.assertRaisesRegex(ValueError, "Personal contact fields"):
            report_module.score_application(payload)

    def test_low_information_application_is_not_sold_to(self) -> None:
        payload = dict(self.qualified)
        payload.update({
            "markets": ["France"],
            "products_services": "Consulting",
            "contract_capacity": "Under USD 50k",
            "discovery_process": "Referral",
            "useful_features": [],
            "founder_interest": "Research only",
        })
        result = report_module.score_application(payload)
        self.assertLess(result["score"], 45)
        self.assertEqual("Research signal", result["band"])
        self.assertIn("avoid a payment request", result["recommended_next_step"])

    def test_score_never_exceeds_100(self) -> None:
        result = report_module.score_application(self.qualified)
        self.assertLessEqual(result["score"], result["maximum"])
        self.assertEqual(100, result["maximum"])


if __name__ == "__main__":
    unittest.main()
