#!/usr/bin/env python3
"""Normalize TED country labels and reject unresolved truncated codes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

COUNTRY_NAMES = {
    "AT": "Austria", "AUT": "Austria",
    "BE": "Belgium", "BEL": "Belgium",
    "BG": "Bulgaria", "BGR": "Bulgaria",
    "CH": "Switzerland", "CHE": "Switzerland",
    "CY": "Cyprus", "CYP": "Cyprus",
    "CZ": "Czechia", "CZE": "Czechia",
    "DE": "Germany", "DEU": "Germany",
    "DK": "Denmark", "DNK": "Denmark",
    "EE": "Estonia", "EST": "Estonia",
    "ES": "Spain", "ESP": "Spain",
    "FI": "Finland", "FIN": "Finland",
    "FR": "France", "FRA": "France",
    "GB": "United Kingdom", "GBR": "United Kingdom", "UK": "United Kingdom",
    "GR": "Greece", "GRC": "Greece", "EL": "Greece",
    "HR": "Croatia", "HRV": "Croatia",
    "HU": "Hungary", "HUN": "Hungary",
    "IE": "Ireland", "IRL": "Ireland",
    "IS": "Iceland", "ISL": "Iceland",
    "IT": "Italy", "ITA": "Italy",
    "LI": "Liechtenstein", "LIE": "Liechtenstein",
    "LT": "Lithuania", "LTU": "Lithuania",
    "LU": "Luxembourg", "LUX": "Luxembourg",
    "LV": "Latvia", "LVA": "Latvia",
    "MT": "Malta", "MLT": "Malta",
    "NL": "Netherlands", "NLD": "Netherlands",
    "NO": "Norway", "NOR": "Norway",
    "PL": "Poland", "POL": "Poland", "PO": "Poland",
    "PT": "Portugal", "PRT": "Portugal",
    "RO": "Romania", "ROU": "Romania",
    "SE": "Sweden", "SWE": "Sweden",
    "SI": "Slovenia", "SVN": "Slovenia",
    "SK": "Slovakia", "SVK": "Slovakia",
}

KNOWN_NAMES = set(COUNTRY_NAMES.values()) | {"European Union"}
CODE_PATTERN = re.compile(r"^[A-Z]{2,3}$")


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def normalize_country(value: object) -> tuple[str, bool]:
    text = clean_text(value)
    if text in KNOWN_NAMES:
        return text, False
    code = re.sub(r"[^A-Za-z]", "", text).upper()
    if code in COUNTRY_NAMES:
        return COUNTRY_NAMES[code], True
    if CODE_PATTERN.fullmatch(code):
        raise ValueError(f"Unrecognized country code: {text!r}")
    if text:
        return text, False
    raise ValueError("Country is empty")


def normalize_records(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("Country normalization requires a non-empty record array")
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Every record must be an object")
        record = dict(item)
        country, changed = normalize_country(record.get("country"))
        record["country"] = country
        if changed:
            provenance = dict(record.get("provenance") or {})
            normalized_fields = list(provenance.get("normalized_fields") or [])
            if "country" not in normalized_fields:
                normalized_fields.append("country")
            provenance["normalized_fields"] = normalized_fields
            record["provenance"] = provenance
        normalized.append(record)
    return normalized


def write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    records = json.loads(args.path.read_text(encoding="utf-8"))
    normalized = normalize_records(records)
    write_json(args.path, normalized)
    changed = sum(1 for before, after in zip(records, normalized) if before.get("country") != after.get("country"))
    print(f"Normalized {changed} country labels across {len(normalized)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
