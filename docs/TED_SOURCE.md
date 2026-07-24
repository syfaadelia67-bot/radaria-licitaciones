# TED live source

TenderSignal's first live adapter uses the official European Union TED Search API v3.

## Endpoint

- Primary: `https://api.ted.europa.eu/v3/notices/search`
- Secondary: `https://tedweb.api.ted.europa.eu/v3/notices/search`
- Authentication: none for published-notice search
- Method: `POST`
- Pagination: page-number mode, up to 250 notices per page

## Current query

The scheduled job requests notices published during the previous 14 days, sorted by publication date descending. It requests no more than 100 records per run and retains only normalized notices with a future tender deadline.

## Provenance model

Facts copied from TED include publication number, title, description, buyer country, CPV classification, estimated value, currency, publication date and tender deadline. TenderSignal-generated fields are explicitly recorded under `provenance.generated_fields`; the initial generated fields are category and keywords.

Every normalized record retains:

- the TED publication number;
- an official source URL;
- the UTC retrieval timestamp;
- `synthetic=false` and `status=LIVE`.

## Safe failure policy

The scheduled workflow fetches into temporary files, validates the complete candidate dataset and only then replaces `data/live/`. A failed request, empty normalization result or schema error leaves the last known good dataset untouched. The browser uses demonstration data unless live metadata reports `status=live` and the live dataset is non-empty.

## Limits

TenderSignal is a discovery and prioritization layer, not the authoritative procurement record. Users must verify every opportunity on TED before making a bid decision.
