#!/usr/bin/env python3
"""Generate stable, indexable TenderSignal pages from validated live data."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote, urlencode

BASE_URL = "https://syfaadelia67-bot.github.io/radaria-licitaciones"
ID_PATTERN = re.compile(r"[^a-z0-9-]+")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temp_name = handle.name
    os.replace(temp_name, path)


def slug_for(record_id: str) -> str:
    slug = ID_PATTERN.sub("-", record_id.lower()).strip("-")
    if not slug:
        raise ValueError(f"Cannot derive URL slug from id={record_id!r}")
    return slug


def clean_text(value: object, fallback: str = "") -> str:
    return " ".join(str(value or fallback).split())


def short_description(text: str, limit: int = 180) -> str:
    text = clean_text(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def format_value(record: dict) -> str:
    value = record.get("value")
    currency = clean_text(record.get("currency"), "XXX")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 and currency != "XXX":
        return f"{value:,.0f} {currency}"
    return "Not disclosed in the normalized notice"


def canonical_url(record: dict, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/opportunities/{quote(slug_for(record['id']))}/"


def founder_application_url(record: dict, base_url: str) -> str:
    """Build a local founder-page route that preserves acquisition attribution."""
    params = urlencode(
        {
            "source": "opportunity-page",
            "originPage": canonical_url(record, base_url),
            "offer": "founder-validation",
            "opportunityId": clean_text(record["id"]),
        }
    )
    return f"../../founder.html?{params}"


def language_context(record: dict) -> tuple[str, str, str]:
    translation = record.get("translation") if isinstance(record.get("translation"), dict) else {}
    status = translation.get("status", "original_only")
    source_language = clean_text(translation.get("source_language"), "undetermined")
    if status == "machine_translated":
        model = clean_text(translation.get("model"), "GitHub Models")
        return "en", "MACHINE-TRANSLATED ENGLISH", (
            f"English translation generated through GitHub Models ({model}). "
            f"Source language: {source_language}. The original text is preserved below."
        )
    if status == "source_english":
        return "en", "ORIGINAL ENGLISH", "TED supplied this notice text in English; no machine translation was needed."
    return "und", "ORIGINAL LANGUAGE", "An English translation is not available yet. The original TED text is shown without alteration."


def original_text_section(record: dict) -> str:
    translation = record.get("translation") if isinstance(record.get("translation"), dict) else {}
    if translation.get("status") != "machine_translated":
        return ""
    original_title = clean_text(record.get("original_title"))
    original_description = clean_text(record.get("original_description"))
    source_language = clean_text(translation.get("source_language"), "Original language")
    return f"""
      <section class="detail-section original-text">
        <details>
          <summary>View authoritative original text ({html.escape(source_language)})</summary>
          <h2>{html.escape(original_title)}</h2>
          <p>{html.escape(original_description)}</p>
        </details>
      </section>"""


def page_html(record: dict, metadata: dict, base_url: str) -> str:
    canonical = canonical_url(record, base_url)
    application_url = founder_application_url(record, base_url)
    title = clean_text(record["title"])
    description = clean_text(record["description"])
    meta_description = short_description(description)
    retrieved_at = clean_text(metadata.get("retrieved_at"), "Unknown")
    keywords = [clean_text(item) for item in record.get("keywords", []) if clean_text(item)]
    generated_fields = set(record.get("provenance", {}).get("generated_fields", []))
    classification_note = "TenderSignal-generated classification" if generated_fields else "source classification"
    page_language, language_badge, language_note = language_context(record)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": canonical,
        "url": canonical,
        "name": title,
        "description": meta_description,
        "inLanguage": page_language,
        "datePublished": record.get("published_at"),
        "dateModified": retrieved_at,
        "isBasedOn": record.get("source_url"),
        "keywords": keywords,
    }
    safe_json_ld = json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")
    keyword_html = "".join(f"<li>{html.escape(item)}</li>" for item in keywords[:12]) or "<li>Not classified</li>"
    return f"""<!doctype html>
<html lang="{html.escape(page_language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} — TenderSignal</title>
  <meta name="description" content="{html.escape(meta_description, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="stylesheet" href="../../styles.css">
  <script type="application/ld+json">{safe_json_ld}</script>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="../../"><span class="brand-mark">TS</span><span>TenderSignal</span></a>
    <nav><a href="../../#opportunities">All opportunities</a><a href="../../#profile">Build supplier profile</a></nav>
  </header>
  <main class="detail-main">
    <article class="detail-card">
      <p class="eyebrow">Verified public procurement notice</p>
      <p class="translation-badge">{html.escape(language_badge)}</p>
      <h1 class="detail-title">{html.escape(title)}</h1>
      <p class="detail-lead">{html.escape(description)}</p>
      <section class="detail-section translation-note">
        <h2>Language and provenance</h2>
        <p>{html.escape(language_note)}</p>
        <p>The official TED notice remains authoritative for all legal, technical and eligibility decisions.</p>
      </section>
      {original_text_section(record)}
      <dl class="detail-facts">
        <div><dt>Country</dt><dd>{html.escape(clean_text(record.get('country'), 'Unknown'))}</dd></div>
        <div><dt>Category</dt><dd>{html.escape(clean_text(record.get('category'), 'Unclassified'))}</dd></div>
        <div><dt>Published</dt><dd>{html.escape(clean_text(record.get('published_at'), 'Unknown'))}</dd></div>
        <div><dt>Deadline</dt><dd>{html.escape(clean_text(record.get('deadline'), 'Unknown'))}</dd></div>
        <div><dt>Value</dt><dd>{html.escape(format_value(record))}</dd></div>
        <div><dt>Source</dt><dd>{html.escape(clean_text(record.get('source'), 'TED'))}</dd></div>
      </dl>
      <section class="detail-section">
        <h2>Provenance</h2>
        <p>This page preserves source facts from the official notice. Category and keywords are displayed as {html.escape(classification_note)}.</p>
        <p><strong>Publication ID:</strong> {html.escape(clean_text(record.get('provenance', {}).get('publication_number'), record['id']))}</p>
        <p><strong>Last verified retrieval:</strong> {html.escape(retrieved_at)}</p>
      </section>
      <section class="detail-section">
        <h2>Keywords</h2>
        <ul class="keyword-list">{keyword_html}</ul>
      </section>
      <section class="detail-section">
        <h2>Should your company pursue this opportunity?</h2>
        <p>Apply for a founder validation report to compare this notice with your services, markets and contract capacity. Payment is not currently collected, and applying creates no purchase obligation.</p>
      </section>
      <div class="detail-actions">
        <a class="button primary" href="{html.escape(application_url, quote=True)}">Get a ranked fit report</a>
        <a class="button secondary" href="{html.escape(record['source_url'], quote=True)}" target="_blank" rel="noopener noreferrer">Open official TED notice</a>
        <a class="button secondary" href="../../#profile">Rank locally first</a>
      </div>
    </article>
  </main>
  <footer><p>Official source remains authoritative. TenderSignal does not submit bids or guarantee eligibility.</p><a href="../../feed.xml">RSS feed</a></footer>
</body>
</html>
"""


def sitemap_xml(records: list[dict], metadata: dict, base_url: str) -> str:
    lastmod = clean_text(metadata.get("retrieved_at"), "")[:10]
    urls = [f"{base_url.rstrip('/')}/"] + [canonical_url(record, base_url) for record in records]
    entries = []
    for url in urls:
        lastmod_tag = f"<lastmod>{html.escape(lastmod)}</lastmod>" if lastmod else ""
        entries.append(f"  <url><loc>{html.escape(url)}</loc>{lastmod_tag}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def rss_xml(records: list[dict], metadata: dict, base_url: str) -> str:
    items = []
    for record in sorted(records, key=lambda item: (item.get("published_at", ""), item["id"]), reverse=True):
        link = canonical_url(record, base_url)
        try:
            published = datetime.fromisoformat(record["published_at"]).replace(tzinfo=timezone.utc)
            pub_date = format_datetime(published)
        except (KeyError, ValueError):
            pub_date = format_datetime(datetime.now(timezone.utc))
        items.append(
            "    <item>"
            f"<title>{html.escape(clean_text(record['title']))}</title>"
            f"<link>{html.escape(link)}</link>"
            f"<guid isPermaLink=\"true\">{html.escape(link)}</guid>"
            f"<pubDate>{html.escape(pub_date)}</pubDate>"
            f"<description>{html.escape(short_description(record.get('description', ''), 500))}</description>"
            "</item>"
        )
    retrieved = html.escape(clean_text(metadata.get("retrieved_at"), "unknown"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>TenderSignal live opportunities</title>
    <link>{html.escape(base_url.rstrip('/') + '/')}</link>
    <description>Verified public procurement notices with an English-first display layer. Last retrieval: {retrieved}</description>
    <language>en</language>
{chr(10).join(items)}
  </channel>
</rss>
"""


def validate_records(records: object) -> list[dict]:
    if not isinstance(records, list) or not records:
        raise ValueError("Live dataset must be a non-empty array")
    validated = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every live record must be an object")
        record_id = clean_text(record.get("id"))
        if not record_id or record_id in seen:
            raise ValueError(f"Invalid or duplicate record id: {record_id!r}")
        if record.get("synthetic") is not False or record.get("status") != "LIVE":
            raise ValueError(f"{record_id}: only verified LIVE non-synthetic records may be generated")
        source_url = clean_text(record.get("source_url"))
        if not source_url.startswith("https://"):
            raise ValueError(f"{record_id}: source_url must use HTTPS")
        for field in ("title", "description", "country", "category", "published_at", "deadline"):
            if not clean_text(record.get(field)):
                raise ValueError(f"{record_id}: missing {field}")
        seen.add(record_id)
        validated.append(record)
    return validated


def generate(records: list[dict], metadata: dict, output_root: Path, base_url: str) -> dict:
    records = validate_records(records)
    if metadata.get("status") != "live":
        raise ValueError("Metadata must report status=live")
    manifest = {
        "generated_at": clean_text(metadata.get("retrieved_at"), datetime.now(timezone.utc).isoformat()),
        "record_count": len(records),
        "pages": [],
    }
    for record in records:
        slug = slug_for(record["id"])
        relative = Path("opportunities") / slug / "index.html"
        atomic_write(output_root / relative, page_html(record, metadata, base_url))
        manifest["pages"].append({"id": record["id"], "url": canonical_url(record, base_url), "path": str(relative)})
    atomic_write(output_root / "sitemap.xml", sitemap_xml(records, metadata, base_url))
    atomic_write(output_root / "feed.xml", rss_xml(records, metadata, base_url))
    atomic_write(output_root / "data/live/generated-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
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
    print(f"Generated {manifest['record_count']} opportunity pages, sitemap.xml and feed.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
