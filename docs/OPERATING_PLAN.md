# TenderSignal — 30-Day Operating Plan

## Mission

Build a revenue-generating company operated primarily by AI, with zero initial operating capital and no dependence on repetitive manual prospecting.

## Product thesis

Small and medium suppliers do not need another database of procurement notices. They need a fast, explainable answer to a more valuable question:

> Which public-sector opportunities are worth our limited bid effort?

TenderSignal normalizes notices from official procurement sources, matches them to a lightweight supplier profile and explains a relevance score. The acquisition loop is built into the inventory: each newly indexed opportunity can become a searchable page, an email alert and a social post.

## Operating constraints

- Initial cash budget: USD 0.
- No paid ads, domains, hosting, data providers or subscriptions before revenue.
- No fabricated traction, customers or active tender claims.
- No passwords or secrets committed to the repository.
- Human action is reserved for identity verification, legal acceptance, account authorization and high-risk financial decisions.
- Official platform rules, robots directives, rate limits and data licences must be respected.

## Initial customer

A small supplier that:

- sells digital, consulting, training, communications or operational services;
- can bid on public contracts but lacks a dedicated bid-intelligence team;
- currently searches several portals or receives broad alerts;
- loses time reading irrelevant notices;
- can describe its offer using a few categories and keywords.

## MVP scope

Included:

- responsive public landing page;
- normalized opportunity schema;
- country, category, value, deadline and text filters;
- lightweight supplier profile;
- transparent rule-based relevance scoring;
- bilingual English/Spanish interface;
- local validation-list capture for prototype testing;
- automated schema and syntax checks.

Excluded until evidence supports them:

- authentication;
- billing;
- AI chat;
- proposal writing;
- private dashboards;
- paid language-model calls;
- complex historical award analytics.

## Acquisition loop

```text
Official notice
  → normalized record
  → public opportunity page
  → category/country landing page
  → search/social/email discovery
  → supplier profile or alert signup
  → usage signals
  → better ranking and positioning
```

This loop avoids a company that survives only when a human sends direct messages. Selective community participation may accelerate validation, but it cannot become the core distribution system.

## Monetization hypothesis

### Free

- broad weekly digest;
- limited profile;
- basic search and scoring;
- delayed alerts.

### Founder plan

- target test price: USD 10 for 60 days;
- immediate matched alerts;
- multiple categories;
- detailed fit explanation;
- shortlist export.

### Professional plan

- target future price: USD 12–29 monthly, adjusted by market;
- multiple profiles or team members;
- deadline tracking;
- saved searches;
- historical opportunity intelligence.

No payment integration is added until users demonstrate intent by joining a validation list, repeatedly using the ranking tool or explicitly requesting access.

## Thirty-day schedule

### Days 1–3 — Foundation

- Publish the static prototype.
- Validate the global normalized schema.
- Select one official source with a lawful, reliable and free access path.
- Define the first vertical based on notice volume and buyer urgency.

Gate: the prototype loads, filters and scores at least 12 synthetic records; validation passes automatically.

### Days 4–7 — Real data adapter

- Implement one source adapter.
- Preserve source URLs and timestamps.
- Add deduplication and failure logging.
- Generate at least 100 real notice records without paid APIs.

Gate: 95% or more of ingested records pass schema validation; failures are observable and reversible.

### Days 8–12 — Public inventory

- Generate static opportunity detail pages.
- Generate category and market pages.
- Add sitemap and metadata.
- Publish a transparent methodology page.

Gate: at least 100 crawlable, non-duplicate pages with no misleading claims.

### Days 13–17 — Validation capture

- Replace local-only signup storage with a free, permission-based collection method.
- Publish a weekly ranked report.
- Add privacy and unsubscribe language.
- Measure signup conversion and repeat visits.

Gate: 10 qualified signups or strong evidence explaining why the proposition is not converting.

### Days 18–23 — Monetization test

- Offer founder access to users who showed intent.
- Add a payment link only after the offer is requested or accepted.
- Deliver the first premium report manually through the AI workflow if necessary, while documenting every repeated step for automation.

Gate: one paid user, three explicit purchase-intent responses or a documented pivot decision.

### Days 24–30 — Automation or pivot

- Automate the highest-frequency repeated task.
- Remove unused features.
- Compare verticals and acquisition channels.
- Decide to scale, narrow, reposition or discontinue.

Gate: a concrete month-two plan based on measured behaviour rather than optimism.

## Daily CEO metrics

### Product

- valid records ingested;
- duplicate and failed records;
- page-generation success rate;
- ranking interactions;
- saved profiles.

### Acquisition

- unique visitors;
- landing-page conversion;
- traffic by page type and source;
- email signup rate;
- returning visitor rate.

### Revenue evidence

- founder-access requests;
- qualified purchase-intent messages;
- paying users;
- revenue;
- refunds;
- delivery effort per customer.

### Autonomy

- AI decisions completed without human intervention;
- human actions required;
- minutes of human work per day;
- recurring tasks not yet automated;
- errors caught by automated controls.

## Decision rules

- Do not add a feature unless it addresses observed behaviour or a repeated objection.
- Do not pay for traffic before free acquisition produces at least one conversion signal.
- Do not add an LLM dependency when deterministic matching can validate the need.
- Prefer one reliable source and one customer vertical over superficial global coverage.
- Stop or pivot a channel after a defined test produces no meaningful signal.
- Preserve an audit trail for data sources, scoring changes and commercial claims.

## Principal risks

### Distribution risk

Procurement SEO is competitive and slow. Mitigation: create high-intent pages, useful reports and reusable data products rather than relying on generic articles.

### Data-access risk

Portals can change interfaces or access policies. Mitigation: start with documented APIs or licensed open datasets, isolate adapters and monitor failures.

### Trust risk

Suppliers may distrust automated recommendations. Mitigation: expose score factors, link to the official notice and clearly separate facts from inference.

### Legal and compliance risk

Public availability does not automatically grant unrestricted reuse. Mitigation: review each source's licence, terms, rate limits and personal-data implications before ingestion.

### False-urgency risk

Incorrect dates or summaries can waste bid effort. Mitigation: official links remain authoritative; automated checks validate dates and the UI labels unverified or synthetic records.

### Zero-capital infrastructure risk

Free tiers can be suspended or rate-limited. Mitigation: static generation, local caching, low-frequency updates and portable data files.

## Pivot conditions

Pivot the product or target vertical when any of the following occurs:

- fewer than 10 qualified signups after 500 relevant visitors;
- repeated users search but ignore ranking explanations;
- data licensing prevents sustainable indexing;
- suppliers value document preparation substantially more than discovery;
- acquisition requires continuous one-to-one outreach;
- operating cost per active user cannot be covered by the plausible price.

## Immediate next decision

After this static MVP is reviewed, the highest-impact action is to select and implement the first real-data adapter. Selection must be based on documented access, licence clarity, notice volume, customer purchasing power and ability to create indexable pages.
