#!/usr/bin/env python3
"""Fetch and normalize recent procurement notices from the official TED Search API.

The script uses only Python's standard library, requires no API key, and writes
new files only after a complete successful fetch and normalization pass.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PRIMARY_API = "https://api.ted.europa.eu/v3/notices/search"
SECONDARY_API = "https://tedweb.api.ted.europa.eu/v3/notices/search"

FIELDS = [
    "publication-number",
    "publication-date",
    "title-proc",
    "description-proc",
    "buyer-country",
    "classification-cpv",
    "deadline-receipt-tender-date-lot",
    "estimated-value-proc",
    "estimated-value-cur-proc",
]

COUNTRIES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DK": "Denmark",
    "EE": "Estonia", "ES": "Spain", "FI": "Finland", "FR": "France",
    "GR": "Greece", "HU": "Hungary", "IE": "Ireland", "IS": "Iceland",
    "IT": "Italy", "LI": "Liechtenstein", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "MT": "Malta", "NL": "Netherlands",
    "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
    "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia",
}

CPV_CATEGORIES = {
    "30": "Office and computing equipment", "31": "Electrical equipment",
    "32": "Telecommunications", "33": "Medical equipment", "34": "Transport equipment",
    "35": "Security equipment", "37": "Musical and sports goods", "38": "Laboratory equipment",
    "39": "Furniture", "41": "Water equipment", "42": "Industrial machinery",
    "43": "Mining and construction machinery", "44": "Construction materials",
    "45": "Construction works", "48": "Software", "50": "Repair and maintenance",
    "51": "Installation services", "55": "Hotel and restaurant services",
    "60": "Transport services", "63": "Travel and logistics", "64": "Postal services",
    "65": "Utilities", "66": "Financial and insurance services", "70": "Real estate",
    "71": "Architecture and engineering", "72": "IT services", "73": "Research and development",
    "75": "Public administration", "76": "Energy services", "77": "Agriculture services",
    "79": "Business services", "80": "Education and training", "85": "Health and social work",
    "90": "Environmental services", "92": "Recreation and culture", "98": "Other services",
}

STOPWORDS = {
    "and", "the", "for", "with", "from", "that", "this", "services", "service",
    "procurement", "contract", "supply", "public", "within", "including", "into",
}


def request_json(url: str, body: dict[str, Any], timeout: int = 45) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TenderSignal/0.2"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("TED response root must be an object")
    return payload


def fetch_payload(days: int, limit: int) -> tuple[dict[str, Any], str, str]:
    since = date.today() - timedelta(days=days)
    query = f"publication-date >= {since:%Y%m%d} sort by publication-date DESC"
    body = {
        "query": query,
        "fields": FIELDS,
        "page": 1,
        "limit": limit,
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER",
    }
    errors: list[str] = []
    for endpoint in (PRIMARY_API, SECONDARY_API):
        try:
            return request_json(endpoint, body), endpoint, query
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            details = f"{endpoint}: {exc}"
            if isinstance(exc, HTTPError):
                try:
                    details += f" — {exc.read().decode('utf-8', errors='replace')[:500]}"
                except Exception:
                    pass
            errors.append(details)
    raise RuntimeError("TED fetch failed on all endpoints:\n" + "\n".join(errors))


def find_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("notices", "results", "items", "noticeList"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    for value in payload.values():
        if isinstance(value, dict):
            nested = find_results(value)
            if nested:
                return nested
    return []


def values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        output: list[Any] = []
        for item in value:
            output.extend(values(item))
        return output
    if isinstance(value, dict):
        for preferred in ("value", "text", "label", "en"):
            if preferred in value:
                return values(value[preferred])
        output = []
        for item in value.values():
            output.extend(values(item))
        return output
    return [value]


def field(notice: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in notice:
            return notice[name]
    fields = notice.get("fields")
    if isinstance(fields, dict):
        for name in names:
            if name in fields:
                return fields[name]
    return None


def first_text(value: Any, default: str = "") -> str:
    for item in values(value):
        text = str(item).strip()
        if text:
            return re.sub(r"\s+", " ", text)
    return default


def all_text(value: Any) -> list[str]:
    output = []
    for item in values(value):
        text = re.sub(r"\s+", " ", str(item)).strip()
        if text and text not in output:
            output.append(text)
    return output


def iso_date(value: Any) -> str | None:
    candidates = []
    for item in values(value):
        text = str(item)
        match = re.search(r"(20\d{2})-?(\d{2})-?(\d{2})", text)
        if not match:
            continue
        candidate = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        try:
            date.fromisoformat(candidate)
            candidates.append(candidate)
        except ValueError:
            continue
    return min(candidates) if candidates else None


def number(value: Any) -> float:
    for item in values(value):
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            return max(0.0, float(item))
        cleaned = re.sub(r"[^0-9.\-]", "", str(item).replace(",", ""))
        try:
            return max(0.0, float(cleaned))
        except ValueError:
            continue
    return 0.0


def category(cpv_value: Any) -> tuple[str, list[str]]:
    cpvs = [re.sub(r"\D", "", item) for item in all_text(cpv_value)]
    cpvs = [item for item in cpvs if len(item) >= 2]
    if not cpvs:
        return "General procurement", []
    return CPV_CATEGORIES.get(cpvs[0][:2], "General procurement"), cpvs[:5]


def keyword_list(title: str, description: str, cpvs: list[str]) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]{3,}", f"{title} {description}".lower())
    ranked: list[str] = []
    for word in words:
        if word not in STOPWORDS and word not in ranked:
            ranked.append(word)
    return (ranked[:8] + [f"CPV {code}" for code in cpvs[:2]]) or ["procurement"]


def source_url(notice: dict[str, Any], publication_number: str) -> str:
    for candidate in values(notice.get("links")) + values(notice.get("urls")):
        text = str(candidate)
        if text.startswith("https://"):
            return text
    return f"https://ted.europa.eu/en/notice/-/detail/{publication_number}"


def normalize_notice(notice: dict[str, Any], retrieved_at: str) -> dict[str, Any] | None:
    publication_number = first_text(field(notice, "publication-number", "publicationNumber", "ND"))
    published_at = iso_date(field(notice, "publication-date", "publicationDate", "PD"))
    deadline = iso_date(field(notice, "deadline-receipt-tender-date-lot", "deadline", "BT-131(d)-Lot"))
    if not publication_number or not published_at or not deadline:
        return None
    if date.fromisoformat(deadline) < date.today():
        return None

    title = first_text(field(notice, "title-proc", "title", "BT-21-Procedure"), "Untitled procurement notice")
    description = first_text(
        field(notice, "description-proc", "description", "BT-24-Procedure"),
        "See the official TED notice for the complete procurement description.",
    )
    country_code = first_text(field(notice, "buyer-country", "buyerCountry", "BT-514-Organization-Country"))[:2].upper()
    category_name, cpvs = category(field(notice, "classification-cpv", "cpv", "BT-262-Procedure"))
    currency = first_text(field(notice, "estimated-value-cur-proc", "currency", "BT-27-Procedure-Currency"), "XXX").upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        currency = "XXX"

    return {
        "id": f"ted-{publication_number}",
        "synthetic": False,
        "title": title[:240],
        "description": description[:1200],
        "country": COUNTRIES.get(country_code, country_code or "European Union"),
        "region": "European Union",
        "category": category_name,
        "keywords": keyword_list(title, description, cpvs),
        "value": round(number(field(notice, "estimated-value-proc", "estimatedValue", "BT-27-Procedure")), 2),
        "currency": currency,
        "published_at": published_at,
        "deadline": deadline,
        "source": "TED",
        "source_url": source_url(notice, publication_number),
        "status": "LIVE",
        "provenance": {
            "publication_number": publication_number,
            "retrieved_at": retrieved_at,
            "generated_fields": ["category", "keywords"],
        },
    }


def normalize_payload(payload: dict[str, Any], retrieved_at: str) -> list[dict[str, Any]]:
    normalized = []
    seen = set()
    for notice in find_results(payload):
        record = normalize_notice(notice, retrieved_at)
        if record and record["id"] not in seen:
            normalized.append(record)
            seen.add(record["id"])
    normalized.sort(key=lambda item: (item["deadline"], item["published_at"]))
    return normalized


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("data/live/opportunities.json"))
    parser.add_argument("--metadata", type=Path, default=Path("data/live/metadata.json"))
    args = parser.parse_args()

    if not 1 <= args.limit <= 250:
        parser.error("--limit must be between 1 and 250")
    if not 1 <= args.days <= 90:
        parser.error("--days must be between 1 and 90")

    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        payload, endpoint, query = fetch_payload(args.days, args.limit)
        records = normalize_payload(payload, retrieved_at)
        if not records:
            raise RuntimeError("TED returned no usable active notices with future deadlines")
        metadata = {
            "status": "live",
            "source": "TED Search API v3",
            "endpoint": endpoint,
            "query": query,
            "retrieved_at": retrieved_at,
            "record_count": len(records),
        }
        write_json(args.output, records)
        write_json(args.metadata, metadata)
        print(f"Wrote {len(records)} live TED records to {args.output}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
