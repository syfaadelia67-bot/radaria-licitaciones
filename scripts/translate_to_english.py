#!/usr/bin/env python3
"""Add a non-blocking English display layer to normalized TED opportunities.

The original title and description remain preserved. New or changed non-English
records can be translated through GitHub Models using the workflow-scoped
GITHUB_TOKEN. Cached translations are reused and model failures never prevent
publication of the original verified TED data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://models.github.ai/inference/chat/completions"
DEFAULT_MODEL = "openai/gpt-4.1-mini"
DEFAULT_REQUEST_TIMEOUT = 45
DEFAULT_MAX_NEW_TRANSLATIONS = 8
CACHE_VERSION = 1
COMMON_ENGLISH = {
    "the", "and", "for", "of", "to", "in", "with", "from", "services",
    "service", "supply", "contract", "procurement", "works", "maintenance",
    "construction", "framework", "system", "equipment", "management",
}


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def original_text(record: dict[str, Any]) -> tuple[str, str]:
    return (
        clean_text(record.get("original_title") or record.get("title")),
        clean_text(record.get("original_description") or record.get("description")),
    )


def content_hash(record: dict[str, Any]) -> str:
    title, description = original_text(record)
    return hashlib.sha256(f"{title}\0{description}".encode("utf-8")).hexdigest()


def likely_english(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    words = re.findall(r"[a-z]+", text)
    if len(words) < 4:
        return False
    common_hits = sum(1 for word in words[:120] if word in COMMON_ENGLISH)
    latin_chars = [character for character in text if character.isalpha()]
    ascii_ratio = (
        sum(1 for character in latin_chars if "a" <= character <= "z") / len(latin_chars)
        if latin_chars else 0
    )
    return common_hits >= 3 and ascii_ratio >= 0.92


def numeric_tokens(text: str) -> set[str]:
    return set(re.findall(r"\b\d[\d.,/%-]*\b", text))


def validate_translation(record: dict[str, Any], translated: dict[str, Any]) -> dict[str, str]:
    record_id = clean_text(record.get("id"))
    if clean_text(translated.get("id")) != record_id:
        raise ValueError(f"translation id mismatch for {record_id}")
    title_en = clean_text(translated.get("title_en"))
    description_en = clean_text(translated.get("description_en"))
    source_language = clean_text(translated.get("source_language")) or "undetermined"
    if not title_en or not description_en:
        raise ValueError(f"empty English translation for {record_id}")

    original_title, original_description = original_text(record)
    original_numbers = numeric_tokens(f"{original_title} {original_description}")
    translated_numbers = numeric_tokens(f"{title_en} {description_en}")
    missing_numbers = sorted(original_numbers - translated_numbers)
    if missing_numbers:
        raise ValueError(f"translation for {record_id} lost numeric tokens: {missing_numbers[:8]}")
    if len(description_en) < min(80, max(20, len(original_description) // 4)):
        raise ValueError(f"translation for {record_id} appears summarized or truncated")
    if len(description_en) > max(300, len(original_description) * 3):
        raise ValueError(f"translation for {record_id} expanded implausibly")
    return {
        "id": record_id,
        "title_en": title_en,
        "description_en": description_en,
        "source_language": source_language,
    }


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("entries"), dict):
        return {str(key): value for key, value in payload["entries"].items() if isinstance(value, dict)}
    return {}


def error_summary(exc: BaseException) -> str:
    if isinstance(exc, HTTPError):
        detail = ""
        try:
            detail = clean_text(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            detail = ""
        message = f"HTTP {exc.code}"
        if detail:
            message += f": {detail[:240]}"
        return message
    return clean_text(str(exc))[:300] or exc.__class__.__name__


def request_translations(
    records: list[dict[str, Any]],
    token: str,
    model: str,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> list[dict[str, Any]]:
    compact = []
    source_characters = 0
    for record in records:
        title, description = original_text(record)
        compact.append({"id": record["id"], "title": title, "description": description})
        source_characters += len(title) + len(description)
    prompt = (
        "Translate every procurement notice into faithful, plain English. Do not summarize, omit, "
        "interpret or add facts. Preserve all personal and organisation names, product names, legal "
        "references, identifiers, dates, quantities, percentages, currencies and monetary values "
        "with exactly the same numeric formatting. Return one JSON object only with this exact shape: "
        "{\"translations\":[{\"id\":\"...\",\"source_language\":\"English language name\","
        "\"title_en\":\"...\",\"description_en\":\"...\"}]}. "
        "Return exactly one item for every input id in the same order. Input: "
        + json.dumps(compact, ensure_ascii=False)
    )
    max_tokens = min(6000, max(1200, source_characters // 2 + 800))
    body = {
        "model": model,
        "temperature": 0,
        "seed": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a literal public-procurement translator. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    request = Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "TenderSignal-English-Layer/1.1",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    decoded = json.loads(content)
    translations = decoded.get("translations")
    if not isinstance(translations, list):
        raise ValueError("model response did not contain a translations array")
    return translations


def apply_entry(record: dict[str, Any], entry: dict[str, Any], model: str) -> None:
    original_title, original_description = original_text(record)
    record["original_title"] = original_title
    record["original_description"] = original_description
    record["title"] = clean_text(entry["title_en"])
    record["description"] = clean_text(entry["description_en"])
    record["translation"] = {
        "status": "machine_translated",
        "display_language": "en",
        "source_language": clean_text(entry.get("source_language")) or "undetermined",
        "provider": "GitHub Models",
        "model": clean_text(entry.get("model")) or model,
        "source_hash": content_hash(record),
        "translated_at": clean_text(entry.get("translated_at")) or utc_now(),
    }


def mark_source_english(record: dict[str, Any]) -> None:
    title, description = original_text(record)
    record["title"] = title
    record["description"] = description
    record.pop("original_title", None)
    record.pop("original_description", None)
    record["translation"] = {
        "status": "source_english",
        "display_language": "en",
        "source_language": "English",
        "source_hash": content_hash(record),
    }


def mark_original_only(record: dict[str, Any], reason: str = "unavailable") -> None:
    title, description = original_text(record)
    record["title"] = title
    record["description"] = description
    record.pop("original_title", None)
    record.pop("original_description", None)
    record["translation"] = {
        "status": "original_only",
        "display_language": "original",
        "source_language": "undetermined",
        "source_hash": content_hash(record),
        "reason": reason,
    }


def translate_records(
    records: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    token: str | None,
    model: str,
    batch_size: int,
    max_new_translations: int | None = None,
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    prepared = [dict(record) for record in records]
    pending: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "source_english": 0,
        "cached": 0,
        "translated": 0,
        "original_only": 0,
        "deferred": 0,
        "request_failures": 0,
        "rejected": 0,
        "errors": [],
    }

    for record in prepared:
        title, description = original_text(record)
        record_hash = content_hash(record)
        entry = cache.get(str(record.get("id")))
        if likely_english(title, description):
            mark_source_english(record)
            stats["source_english"] += 1
        elif entry and entry.get("source_hash") == record_hash:
            apply_entry(record, entry, model)
            stats["cached"] += 1
        else:
            pending.append(record)

    limit = len(pending) if max_new_translations is None else max(0, max_new_translations)
    candidates = pending[:limit]
    deferred = pending[limit:]
    for record in deferred:
        mark_original_only(record, "translation_budget")
        stats["original_only"] += 1
        stats["deferred"] += 1

    if token:
        for start in range(0, len(candidates), batch_size):
            batch = candidates[start : start + batch_size]
            try:
                raw_translations = request_translations(batch, token, model, timeout=request_timeout)
                by_id = {clean_text(item.get("id")): item for item in raw_translations if isinstance(item, dict)}
            except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
                summary = error_summary(exc)
                print(f"WARNING: English translation request failed; preserving batch originals: {summary}", file=sys.stderr)
                stats["request_failures"] += 1
                stats["errors"].append(summary)
                for record in batch:
                    mark_original_only(record, "request_failed")
                    stats["original_only"] += 1
                continue

            for record in batch:
                try:
                    validated = validate_translation(record, by_id.get(str(record.get("id")), {}))
                    now = utc_now()
                    entry = {
                        **validated,
                        "source_hash": content_hash(record),
                        "model": model,
                        "translated_at": now,
                    }
                    cache[str(record["id"])] = entry
                    apply_entry(record, entry, model)
                    stats["translated"] += 1
                except (KeyError, ValueError) as exc:
                    summary = error_summary(exc)
                    print(f"WARNING: rejected English translation for {record.get('id')}: {summary}", file=sys.stderr)
                    stats["rejected"] += 1
                    stats["errors"].append(summary)
                    mark_original_only(record, "validation_rejected")
                    stats["original_only"] += 1
    else:
        for record in candidates:
            mark_original_only(record, "model_token_unavailable")
            stats["original_only"] += 1
        if candidates:
            stats["errors"].append("GITHUB_TOKEN was unavailable to the translation process")

    stats["errors"] = stats["errors"][:12]
    return prepared, cache, stats


def translation_status(
    records: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    stats: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    counts = {key: value for key, value in stats.items() if key != "errors"}
    translated_or_english = counts.get("source_english", 0) + counts.get("cached", 0) + counts.get("translated", 0)
    return {
        "generated_at": utc_now(),
        "state": "complete" if translated_or_english == len(records) else "partial",
        "model": model,
        "record_count": len(records),
        "english_display_count": translated_or_english,
        "cache_entries": len(cache),
        "counts": counts,
        "errors": list(stats.get("errors", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/live/opportunities.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path, default=Path("data/live/translation-cache.json"))
    parser.add_argument("--status", type=Path, default=Path("data/live/translation-status.json"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-new-translations", type=int, default=DEFAULT_MAX_NEW_TRANSLATIONS)
    parser.add_argument("--request-timeout", type=int, default=DEFAULT_REQUEST_TIMEOUT)
    parser.add_argument("--offline", action="store_true", help="Use source-English detection and cache only")
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 20:
        parser.error("--batch-size must be between 1 and 20")
    if not 0 <= args.max_new_translations <= 100:
        parser.error("--max-new-translations must be between 0 and 100")
    if not 5 <= args.request_timeout <= 120:
        parser.error("--request-timeout must be between 5 and 120 seconds")

    records = json.loads(args.path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise SystemExit("translation input must be a non-empty JSON array")
    cache = load_cache(args.cache)
    token = None if args.offline else os.environ.get("GITHUB_TOKEN")
    translated, cache, stats = translate_records(
        records,
        cache,
        token,
        args.model,
        args.batch_size,
        max_new_translations=args.max_new_translations,
        request_timeout=args.request_timeout,
    )
    output = args.output or args.path
    atomic_json(output, translated)
    atomic_json(args.cache, {"version": CACHE_VERSION, "entries": cache})
    atomic_json(args.status, translation_status(translated, cache, stats, args.model))
    printable = {key: value for key, value in stats.items() if key != "errors"}
    print("English layer: " + ", ".join(f"{key}={value}" for key, value in printable.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
