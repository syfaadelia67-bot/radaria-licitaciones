from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InteractivityGuardTests(unittest.TestCase):
    def test_controls_bind_before_remote_data_is_awaited(self) -> None:
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        init = app[app.index("async function init()") :]
        self.assertLess(init.index("bindEvents();"), init.index("await loadOpportunityData"))
        self.assertIn("Progressive enhancement", init)
        self.assertIn("AbortController", app)

    def test_data_loader_has_timeout_and_no_mutation_loop(self) -> None:
        loader = (ROOT / "data-loader.js").read_text(encoding="utf-8")
        self.assertIn("DATA_TIMEOUT_MS", loader)
        self.assertIn("AbortController", loader)
        self.assertIn(
            "if (badge.textContent !== presentation.label) badge.textContent = presentation.label;",
            loader,
        )
        self.assertIn('if (badge.textContent !== "DEMO") badge.textContent = "DEMO";', loader)
        self.assertNotIn('badge.textContent = state.mode === "live" ? "LIVE" : "DEMO";', loader)
        self.assertNotIn("badge.textContent = presentation.label;\n", loader.replace(
            "if (badge.textContent !== presentation.label) badge.textContent = presentation.label;\n", ""
        ))

    def test_event_binding_is_idempotent(self) -> None:
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("let eventsBound = false;", app)
        self.assertIn("if (eventsBound) return;", app)


if __name__ == "__main__":
    unittest.main()
