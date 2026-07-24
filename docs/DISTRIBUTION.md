# Automated distribution assets

TenderSignal turns every verified live TED notice into reusable public infrastructure after each successful refresh.

## Generated outputs

- `opportunities/<stable-id>/index.html` — one canonical detail page per verified notice;
- `sitemap.xml` — the home page and current live detail pages only;
- `feed.xml` — RSS 2.0 feed ordered by publication date;
- `data/live/generated-manifest.json` — generated page count, stable paths and canonical URLs.

Demo records are never included in generated production pages, the sitemap or the feed.

## Reliability policy

The workflow fetches and validates into temporary files first. It publishes data and generated pages only after validation succeeds. The generator writes files atomically and does not delete previously valid detail pages, so a truncated source response cannot erase the last known published pages.

The sitemap and feed contain only the latest verified live set. Older retained pages may remain accessible by their stable TED publication URL but are removed from active discovery when they no longer appear in the current dataset.

## Provenance

Each page separates:

- official source facts, including title, description, country, publication date, deadline and source link;
- TenderSignal-generated category and keyword classification;
- retrieval timestamp and TED publication identifier.

The official TED notice remains authoritative.

## Stable URL rule

The normalized record ID becomes the path:

```text
https://syfaadelia67-bot.github.io/radaria-licitaciones/opportunities/ted-<publication-number>/
```

The same TED publication number always resolves to the same TenderSignal URL.

## Metrics for the distribution experiment

- live pages generated;
- search impressions and visits per page;
- RSS subscribers or feed fetches;
- clicks to official notices;
- clicks back to the supplier-profile tool;
- validation-list conversions.

No fabricated traffic or customer metrics should be added. Measurement integrations remain out of scope until they can be introduced at zero cost and with an explicit privacy policy.
