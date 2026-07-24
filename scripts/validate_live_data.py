#!/usr/bin/env python3
"""Validate normalized live TenderSignal opportunity data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FIELDS = {
    "id", "synthetic", "title", "description", "country", "region", "category",
    "keywords", "value", "currency", "published_at", "deadline", "source",
    "source_url", "status", "provenance",
}


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def valid_date(value: object) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/live/opportunities.json"))
    args = parser.parse_args()

    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {args.path}: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(payload, list) or not payload:
        errors.append("live dataset must be a non-empty array")
        payload = payload if isinstance(payload, list) else []

    seen: set[str] = set()
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            errors.append(f"record[{index}] must be an object")
            continue
        record_id = str(record.get("id", f"record[{index}]"))
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            errors.append(f"{record_id}: missing {', '.join(sorted(missing))}")
        if record_id in seen:
            errors.append(f"{record_id}: duplicate id")
        seen.add(record_id)
        if record.get("synthetic") is not False:
            errors.append(f"{record_id}: live records require synthetic=false")
        if record.get("status") != "LIVE":
            errors.append(f"{record_id}: live records require status=LIVE")
        if record.get("source") != "TED":
            errors.append(f"{record_id}: first live adapter requires source=TED")
        if not valid_url(record.get("source_url")):
            errors.append(f"{record_id}: invalid source_url")
        if not valid_date(record.get("published_at")) or not valid_date(record.get("deadline")):
            errors.append(f"{record_id}: invalid ISO date")
        elif date.fromisoformat(record["deadline"]) < date.fromisoformat(record["published_at"]):
            errors.append(f"{record_id}: deadline precedes publication")
        if not isinstance(record.get("keywords"), list) or not record.get("keywords"):
            errors.append(f"{record_id}: keywords must be non-empty")
        if not isinstance(record.get("value"), (int, float)) or isinstance(record.get("value"), bool) or record.get("value", -1) < 0:
            errors.append(f"{record_id}: value must be a non-negative number")
        if not re.fullmatch(r"[A-Z]{3}", str(record.get("currency", ""))):
            errors.append(f"{record_id}: invalid currency code")
        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("publication_number") or not provenance.get("retrieved_at"):
            errors.append(f"{record_id}: incomplete provenance")

    if errors:
        print("Live data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(payload)} live TED opportunities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
