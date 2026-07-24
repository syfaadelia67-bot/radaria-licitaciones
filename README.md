# TenderSignal

**AI-ranked public procurement opportunities for suppliers that cannot afford to read every notice.**

TenderSignal is a zero-capital company experiment. It converts public procurement notices into a normalized opportunity feed, compares each record with a lightweight supplier profile and explains why an opportunity may or may not be worth pursuing.

> The current dataset contains synthetic demonstration records only. It must not be used to make real bidding decisions.

## MVP capabilities

- responsive static interface;
- English and Spanish UI;
- supplier keyword, category, market and capacity profile;
- transparent rule-based relevance scoring;
- full-text, country, category, deadline and minimum-value filters;
- 12 synthetic records spanning multiple markets;
- zero-dependency Python data validation;
- automated validation through GitHub Actions;
- 30-day operating, acquisition and monetization plan.

## Run locally

Python 3 is sufficient:

```bash
python -m http.server 8000
```

Open `http://localhost:8000`.

Opening `index.html` directly may prevent the browser from loading the JSON dataset, so use a local web server.

## Validate

```bash
python scripts/validate_data.py
node --check app.js
```

No package installation or paid service is required.

## Deploy for free with GitHub Pages

1. Merge the MVP pull request into `main`.
2. Open repository **Settings → Pages**.
3. Under **Build and deployment**, select **Deploy from a branch**.
4. Select the `main` branch and `/ (root)` folder.
5. Save and wait for the published URL.

## Repository structure

```text
.
├── .github/workflows/validate.yml
├── data/opportunities.json
├── docs/OPERATING_PLAN.md
├── scripts/validate_data.py
├── app.js
├── index.html
└── styles.css
```

## Scoring model

The prototype uses an intentionally auditable deterministic score. Points are added for:

- matching supplier keywords;
- matching preferred category;
- matching preferred market;
- fitting within the supplier's stated contract capacity;
- having an actionable deadline window.

This model validates user demand before adding paid model inference. Official source pages remain authoritative.

## Commercial hypothesis

TenderSignal will not compete as a generic tender database. Its value proposition is decision support:

> **Find the opportunities worth spending bid effort on.**

The intended distribution loop turns each official notice into structured inventory, a public page, an alert and reusable market content. See [`docs/OPERATING_PLAN.md`](docs/OPERATING_PLAN.md) for metrics, risks and pivot criteria.

## Data policy

Before adding any live source adapter:

- confirm API or dataset access rules;
- review licensing and reuse rights;
- respect rate limits and robots directives;
- retain official source URLs and timestamps;
- label facts, generated summaries and inference separately;
- avoid personal data that is unnecessary for procurement discovery.

## Status

Day 1 foundation: MVP implementation and automated schema validation.
