#!/usr/bin/env python3
"""Generate a public market brief and reusable distribution copy from live data."""

from __future__ import annotations

import argparse
import html
import json
import os
import tempfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://syfaadelia67-bot.github.io/radaria-licitaciones"


def clean_text(value: object, fallback: str = "") -> str:
    return " ".join(str(value or fallback).split())


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = handle.name
    os.replace(temporary, path)


def opportunity_url(record: dict, base_url: str) -> str:
    record_id = quote(clean_text(record["id"]).lower())
    return f"{base_url.rstrip('/')}/opportunities/{record_id}/"


def disclosed_value(record: dict) -> float:
    value = record.get("value")
    currency = clean_text(record.get("currency"), "XXX")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 and currency != "XXX":
        return float(value)
    return 0.0


def parse_day(value: object) -> date:
    try:
        return date.fromisoformat(clean_text(value))
    except ValueError:
        return date.max


def notable_records(records: list[dict], limit: int = 8) -> list[dict]:
    """Prioritize disclosed value, then approaching deadlines, without inventing fit."""
    return sorted(
        records,
        key=lambda item: (
            disclosed_value(item) == 0,
            -disclosed_value(item),
            parse_day(item.get("deadline")),
            clean_text(item.get("id")),
        ),
    )[:limit]


def imminent_records(records: list[dict], limit: int = 5) -> list[dict]:
    return sorted(records, key=lambda item: (parse_day(item.get("deadline")), clean_text(item.get("id"))))[:limit]


def top_counts(records: list[dict], field: str, limit: int = 6) -> list[tuple[str, int]]:
    counts = Counter(clean_text(record.get(field), "Unknown") for record in records)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def format_value(record: dict) -> str:
    value = disclosed_value(record)
    currency = clean_text(record.get("currency"), "XXX")
    return f"{value:,.0f} {currency}" if value else "Value not disclosed"


def validate(records: object, metadata: object) -> tuple[list[dict], dict]:
    if not isinstance(records, list) or not records:
        raise ValueError("Live brief requires a non-empty record array")
    if not isinstance(metadata, dict) or metadata.get("status") != "live":
        raise ValueError("Live brief requires metadata status=live")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every brief record must be an object")
        record_id = clean_text(record.get("id"))
        if not record_id or record_id in seen:
            raise ValueError(f"Invalid or duplicate record id: {record_id!r}")
        if record.get("synthetic") is not False or record.get("status") != "LIVE":
            raise ValueError(f"{record_id}: brief only accepts verified LIVE records")
        for field in ("title", "country", "category", "published_at", "deadline", "source_url"):
            if not clean_text(record.get(field)):
                raise ValueError(f"{record_id}: missing {field}")
        seen.add(record_id)
    return records, metadata


def brief_html(records: list[dict], metadata: dict, base_url: str) -> str:
    retrieved = clean_text(metadata.get("retrieved_at"), "Unknown")
    countries = top_counts(records, "country")
    categories = top_counts(records, "category")
    notable = notable_records(records)
    imminent = imminent_records(records)

    country_cards = "".join(
        f"<li><strong>{html.escape(name)}</strong><span>{count} notices</span></li>" for name, count in countries
    )
    category_cards = "".join(
        f"<li><strong>{html.escape(name)}</strong><span>{count} notices</span></li>" for name, count in categories
    )
    notable_cards = "".join(
        f"""<article class="opportunity-card">
          <p class="card-meta">{html.escape(clean_text(record['country']))} · {html.escape(clean_text(record['category']))}</p>
          <h3>{html.escape(clean_text(record['title']))}</h3>
          <p>{html.escape(format_value(record))} · Deadline {html.escape(clean_text(record['deadline']))}</p>
          <a class="source-link" href="{html.escape(opportunity_url(record, base_url), quote=True)}">Review opportunity</a>
        </article>"""
        for record in notable
    )
    imminent_rows = "".join(
        f"<tr><td>{html.escape(clean_text(record['deadline']))}</td><td><a href=\"{html.escape(opportunity_url(record, base_url), quote=True)}\">{html.escape(clean_text(record['title']))}</a></td><td>{html.escape(clean_text(record['country']))}</td></tr>"
        for record in imminent
    )
    canonical = f"{base_url.rstrip('/')}/brief/"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TenderSignal market brief — {len(records)} verified opportunities</title>
  <meta name="description" content="A factual brief of {len(records)} verified public-procurement notices normalized from TED.">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="../"><span class="brand-mark">TS</span><span>TenderSignal</span></a>
    <nav><a href="../#opportunities">All opportunities</a><a href="../founder.html?source=market-brief&amp;offer=founder-validation">Founder validation</a></nav>
  </header>
  <main class="detail-main">
    <article class="detail-card">
      <p class="eyebrow">Verified TED market brief</p>
      <h1 class="detail-title">{len(records)} current public-procurement opportunities</h1>
      <p class="detail-lead">A factual snapshot generated from TenderSignal's latest validated TED dataset. It is not a recommendation, eligibility decision or substitute for the official notice.</p>
      <dl class="detail-facts">
        <div><dt>Verified notices</dt><dd>{len(records)}</dd></div>
        <div><dt>Countries represented</dt><dd>{len(set(clean_text(item.get('country')) for item in records))}</dd></div>
        <div><dt>Categories represented</dt><dd>{len(set(clean_text(item.get('category')) for item in records))}</dd></div>
        <div><dt>Last retrieval</dt><dd>{html.escape(retrieved)}</dd></div>
      </dl>
      <section class="detail-section"><h2>Largest country groups</h2><ul class="keyword-list">{country_cards}</ul></section>
      <section class="detail-section"><h2>Largest category groups</h2><ul class="keyword-list">{category_cards}</ul></section>
      <section class="detail-section"><h2>Notable disclosed-value and near-deadline notices</h2><p>Ordering uses only disclosed value and deadline. TenderSignal does not infer supplier suitability here.</p><div class="opportunity-grid">{notable_cards}</div></section>
      <section class="detail-section"><h2>Deadline watch</h2><div class="table-wrap"><table><thead><tr><th>Deadline</th><th>Notice</th><th>Country</th></tr></thead><tbody>{imminent_rows}</tbody></table></div></section>
      <section class="detail-section"><h2>Need a supplier-specific view?</h2><p>Apply for a ranked fit report that compares selected notices with your services, markets and contract capacity. No payment is collected in the application and applying creates no purchase obligation.</p><a class="button primary" href="../founder.html?source=market-brief&amp;originPage={html.escape(canonical, quote=True)}&amp;offer=founder-validation">Request a ranked fit report</a></section>
    </article>
  </main>
  <footer><p>Official TED notices remain authoritative. Generated from verified live data.</p><a href="../feed.xml">RSS feed</a></footer>
</body>
</html>
"""


def brief_markdown(records: list[dict], metadata: dict, base_url: str) -> str:
    retrieved = clean_text(metadata.get("retrieved_at"), "Unknown")
    lines = [
        "# TenderSignal market brief",
        "",
        f"Verified notices: **{len(records)}**  ",
        f"Last retrieval: **{retrieved}**  ",
        "Source: TED Search API v3; official notices remain authoritative.",
        "",
        "## Notable notices",
        "",
    ]
    for record in notable_records(records):
        lines.append(
            f"- [{clean_text(record['title'])}]({opportunity_url(record, base_url)}) — "
            f"{clean_text(record['country'])}; {clean_text(record['category'])}; "
            f"{format_value(record)}; deadline {clean_text(record['deadline'])}."
        )
    lines.extend(
        [
            "",
            "## Supplier-specific validation",
            "",
            f"Request a ranked fit report: {base_url.rstrip('/')}/founder.html?source=market-brief&offer=founder-validation",
            "",
            "No payment is collected in the application and applying creates no purchase obligation.",
            "",
        ]
    )
    return "\n".join(lines)


def distribution_posts(records: list[dict], metadata: dict, base_url: str) -> str:
    retrieved = clean_text(metadata.get("retrieved_at"), "Unknown")
    brief_url = f"{base_url.rstrip('/')}/brief/"
    countries = top_counts(records, "country", 3)
    categories = top_counts(records, "category", 3)
    first = notable_records(records, 1)[0]
    country_summary = ", ".join(f"{name} ({count})" for name, count in countries)
    category_summary = ", ".join(f"{name} ({count})" for name, count in categories)
    return f"""# TenderSignal reusable distribution copy

Generated from verified live data retrieved at {retrieved}. Review each community's rules and adapt the introduction before posting. Do not mass-post identical copy.

## Professional network post

TenderSignal's latest public-procurement brief covers {len(records)} verified TED notices. The largest current country groups are {country_summary}, while the largest normalized categories are {category_summary}.

The brief links every summary back to the TenderSignal detail page and the authoritative TED notice. No login or payment is required to review the data.

{brief_url}

## Supplier community post

I built a free, factual view of {len(records)} current TED opportunities to reduce the time small suppliers spend opening irrelevant notices. It includes a deadline watch, disclosed-value ordering and links to every official source.

This is not bid advice and does not claim eligibility. Feedback from software, consulting and specialist suppliers is useful:

{brief_url}

## Single-opportunity post

New verified public-procurement notice in {clean_text(first['country'])}: {clean_text(first['title'])}.

Normalized category: {clean_text(first['category'])}  
Disclosed value: {format_value(first)}  
Deadline: {clean_text(first['deadline'])}

TenderSignal summary: {opportunity_url(first, base_url)}
Official TED source remains authoritative.

## Editorial checklist

- Add one sentence explaining why the specific community may find the brief useful.
- Remove any section that is not relevant to that audience.
- Never imply endorsement, guaranteed eligibility, customers, revenue or artificial scarcity.
- Answer comments with source links and factual limitations rather than sales pressure.
"""


def brief_sitemap(metadata: dict, base_url: str) -> str:
    lastmod = html.escape(clean_text(metadata.get("retrieved_at"), "")[:10])
    lastmod_tag = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    location = html.escape(f"{base_url.rstrip('/')}/brief/")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{location}</loc>{lastmod_tag}</url>
</urlset>
"""


def generate(records: list[dict], metadata: dict, output_root: Path, base_url: str) -> dict:
    records, metadata = validate(records, metadata)
    atomic_write(output_root / "brief/index.html", brief_html(records, metadata, base_url))
    atomic_write(output_root / "brief/latest.md", brief_markdown(records, metadata, base_url))
    atomic_write(output_root / "distribution/latest-posts.md", distribution_posts(records, metadata, base_url))
    atomic_write(output_root / "brief-sitemap.xml", brief_sitemap(metadata, base_url))
    manifest = {
        "generated_at": clean_text(metadata.get("retrieved_at"), datetime.now(timezone.utc).isoformat()),
        "record_count": len(records),
        "brief_url": f"{base_url.rstrip('/')}/brief/",
        "files": ["brief/index.html", "brief/latest.md", "distribution/latest-posts.md", "brief-sitemap.xml"],
    }
    atomic_write(output_root / "data/live/brief-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/live/opportunities.json"))
    parser.add_argument("--metadata", type=Path, default=Path("data/live/metadata.json"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    records = json.loads(args.data.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    manifest = generate(records, metadata, args.output_root, args.base_url)
    print(f"Generated market brief and distribution copy from {manifest['record_count']} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
