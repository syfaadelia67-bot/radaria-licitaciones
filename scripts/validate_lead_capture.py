#!/usr/bin/env python3
"""Validate that TenderSignal lead capture is honest and contains no secrets."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    founder = (ROOT / "founder.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    config = (ROOT / "lead-config.js").read_text(encoding="utf-8")
    capture = (ROOT / "lead-capture.js").read_text(encoding="utf-8")

    forbidden = ("tendersignal-signups", "emailInput", "Saved locally for prototype validation")
    for token in forbidden:
        if token in index or token in app:
            fail(f"local-only signup behavior remains: {token}")

    required_founder_text = (
        "Payment is not currently collected",
        "does not create a purchase obligation",
        "explicit permission to contact",
        "data-lead-trigger",
        "data-lead-status",
    )
    for token in required_founder_text:
        if token not in founder:
            fail(f"founder page is missing required disclosure: {token}")

    if "https://tally.so/r/" not in capture:
        fail("lead router must use the documented Tally public form route")
    if "originPage" not in capture or "source" not in capture or "offer" not in capture:
        fail("lead router must preserve attribution fields")

    enabled = re.search(r'enabled:\s*(true|false)', config)
    form_id = re.search(r'formId:\s*"([^"]*)"', config)
    if not enabled or not form_id:
        fail("lead-config.js must declare enabled and formId")
    if enabled.group(1) == "true" and not re.fullmatch(r"[A-Za-z0-9_-]{4,32}", form_id.group(1)):
        fail("enabled lead capture requires a valid public Tally form ID")
    if enabled.group(1) == "false" and form_id.group(1):
        fail("disabled lead capture must not publish a form ID")

    secret_patterns = (
        r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]+",
        r"https://tally\.so/r/[^`\"'/{]+",
    )
    combined = config + founder + capture
    for pattern in secret_patterns:
        match = re.search(pattern, combined)
        if match and "${config.formId}" not in match.group(0):
            fail("possible secret or hard-coded form endpoint detected")

    print("Lead capture validation passed: no local fake signup, no secrets, disclosures present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
