#!/usr/bin/env python3
"""Validate TenderSignal's normalized opportunity dataset using only stdlib."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "opportunities.json"
REQUIRED_FIELDS = {
    "id",
    "synthetic",
    "title",
    "description",
    "country",
    "region",
    "category",
    "keywords",
    "value",
    "currency",
    "published_at",
    "deadline",
    "source",
    "source_url",
    "status",
}
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


def fail(errors: list[str], record_id: str, message: str) -> None:
    errors.append(f"{record_id}: {message}")


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_record(record: object, index: int, seen_ids: set[str], errors: list[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f"record[{index}]: expected object")
        return

    record_id = str(record.get("id", f"record[{index}]"))
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        fail(errors, record_id, f"missing fields: {', '.join(missing)}")

    if record_id in seen_ids:
        fail(errors, record_id, "duplicate id")
    seen_ids.add(record_id)

    for field in ("id", "title", "description", "country", "region", "category", "source", "status"):
        if not isinstance(record.get(field), str) or not record.get(field, "").strip():
            fail(errors, record_id, f"{field} must be a non-empty string")

    if record.get("synthetic") is not True:
        fail(errors, record_id, "prototype records must explicitly set synthetic=true")
    if record.get("status") != "DEMO":
        fail(errors, record_id, "prototype records must use status=DEMO")

    keywords = record.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item.strip() for item in keywords):
        fail(errors, record_id, "keywords must be a non-empty list of strings")

    value = record.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        fail(errors, record_id, "value must be a non-negative number")

    currency = record.get("currency")
    if not isinstance(currency, str) or not CURRENCY_PATTERN.fullmatch(currency):
        fail(errors, record_id, "currency must be a three-letter uppercase code")

    published = parse_iso_date(record.get("published_at"))
    deadline = parse_iso_date(record.get("deadline"))
    if published is None:
        fail(errors, record_id, "published_at must be an ISO date (YYYY-MM-DD)")
    if deadline is None:
        fail(errors, record_id, "deadline must be an ISO date (YYYY-MM-DD)")
    if published and deadline and deadline < published:
        fail(errors, record_id, "deadline cannot be earlier than published_at")

    if not valid_url(record.get("source_url")):
        fail(errors, record_id, "source_url must be a valid HTTPS URL")


def main() -> int:
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: missing dataset at {DATA_PATH}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, list):
        print("ERROR: root JSON value must be an array", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(payload):
        validate_record(record, index, seen_ids, errors)

    if len(payload) < 12:
        errors.append("dataset must contain at least 12 demonstration records")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    countries = len({record["country"] for record in payload})
    categories = len({record["category"] for record in payload})
    print(f"Validated {len(payload)} records across {countries} countries and {categories} categories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
