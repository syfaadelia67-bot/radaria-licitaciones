#!/usr/bin/env python3
"""Submit current canonical TenderSignal URLs to IndexNow without private credentials."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = os.environ.get(
    "TENDERSIGNAL_BASE_URL",
    "https://syfaadelia67-bot.github.io/radaria-licitaciones",
)
ENDPOINT = "https://api.indexnow.org/indexnow"
MAX_URLS = 10_000


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def normalize_base_url(value: str) -> str:
    base_url = clean_text(value).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError(f"Invalid HTTPS publication base URL: {value}")
    return base_url


def load_key(path: Path) -> str:
    key = clean_text(path.read_text(encoding="utf-8"))
    if not 8 <= len(key) <= 128 or not key.isalnum():
        raise ValueError("IndexNow key must be 8–128 alphanumeric characters")
    if path.stem != key:
        raise ValueError("IndexNow key filename must match its contents")
    return key


def collect_urls(site_manifest: object, brief_manifest: object, base_url: str = DEFAULT_BASE_URL) -> list[str]:
    if not isinstance(site_manifest, dict):
        raise ValueError("Site manifest must be an object")
    if not isinstance(brief_manifest, dict):
        raise ValueError("Brief manifest must be an object")

    base_url = normalize_base_url(base_url)
    parsed_base = urlparse(base_url)
    candidates = [f"{base_url}/", f"{base_url}/brief/"]
    for item in site_manifest.get("pages", []):
        if not isinstance(item, dict):
            raise ValueError("Every site-manifest page must be an object")
        candidates.append(clean_text(item.get("url")))
    brief_url = clean_text(brief_manifest.get("brief_url"))
    if brief_url:
        candidates.append(brief_url)

    expected_prefix = f"{base_url}/"
    urls: list[str] = []
    for candidate in candidates:
        if not candidate or candidate in urls:
            continue
        parsed = urlparse(candidate)
        if parsed.scheme != "https" or parsed.netloc != parsed_base.netloc:
            raise ValueError(f"URL is outside the verified IndexNow host: {candidate}")
        if not candidate.startswith(expected_prefix):
            raise ValueError(f"URL is outside the TenderSignal publication path: {candidate}")
        if parsed.query or parsed.fragment:
            raise ValueError(f"Only canonical URLs may be submitted: {candidate}")
        urls.append(candidate)

    if not urls:
        raise ValueError("No canonical URLs found for IndexNow")
    if len(urls) > MAX_URLS:
        raise ValueError(f"IndexNow batch exceeds {MAX_URLS} URLs")
    return urls


def build_payload(urls: list[str], key: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    base_url = normalize_base_url(base_url)
    return {
        "host": urlparse(base_url).netloc,
        "key": key,
        "keyLocation": f"{base_url}/{key}.txt",
        "urlList": urls,
    }


def submit(payload: dict[str, Any], attempts: int = 6, delay_seconds: int = 60) -> int:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    for attempt in range(1, attempts + 1):
        request = Request(
            ENDPOINT,
            data=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "TenderSignal-IndexNow/1.1",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
            if status in (200, 202):
                return status
            if status not in (403, 429) and status < 500:
                raise RuntimeError(f"IndexNow rejected the batch with HTTP {status}")
        except HTTPError as exc:
            if exc.code not in (403, 429) and exc.code < 500:
                details = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"IndexNow rejected the batch with HTTP {exc.code}: {details}") from exc
            status = exc.code
        except (URLError, TimeoutError) as exc:
            status = 0
            last_network_error = exc

        if attempt == attempts:
            if status == 0:
                raise RuntimeError(f"IndexNow could not be reached after {attempts} attempts: {last_network_error}")
            raise RuntimeError(f"IndexNow did not accept the batch after {attempts} attempts; last HTTP status {status}")
        time.sleep(delay_seconds)
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-manifest", type=Path, default=Path("data/live/generated-manifest.json"))
    parser.add_argument("--brief-manifest", type=Path, default=Path("data/live/brief-manifest.json"))
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--delay-seconds", type=int, default=60)
    args = parser.parse_args()

    if not 1 <= args.attempts <= 10:
        parser.error("--attempts must be between 1 and 10")
    if not 0 <= args.delay_seconds <= 300:
        parser.error("--delay-seconds must be between 0 and 300")

    base_url = normalize_base_url(args.base_url)
    site_manifest = json.loads(args.site_manifest.read_text(encoding="utf-8"))
    brief_manifest = json.loads(args.brief_manifest.read_text(encoding="utf-8"))
    key = load_key(args.key_file)
    urls = collect_urls(site_manifest, brief_manifest, base_url)
    payload = build_payload(urls, key, base_url)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    status = submit(payload, attempts=args.attempts, delay_seconds=args.delay_seconds)
    print(f"IndexNow accepted {len(urls)} canonical URLs with HTTP {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())