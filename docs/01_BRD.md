# Northwind Outdoor: measurement requirements (BRD)

> **Sample document.** Northwind Outdoor is a fictional retailer created for this project; the people are roles, not real contacts. The structure follows a client measurement engagement: what the business needs, how each need is checked, and what was decided along the way. The event-level detail is in the [tracking plan](02_tracking_plan.md).

| | |
|---|---|
| Version | 2.0 |
| Date | 2026-10-24 |
| Author | Victor Politakis (implementation) |
| Status | Delivered; one acceptance check awaiting re-run results (section 10) |

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-17 | Context, objectives, tracking plan, privacy approach |
| 2.0 | 2026-10-24 | Requirements with IDs and tests, maturity assessment, risks, decisions; tracking plan moved to its own document |

## 1. Summary

Northwind can't say which campaigns sell, because nothing on the site measures sales and nothing links Google Ads to orders. Phase 1 puts a tag manager, a consent banner and a GA4 setup on the site, exports the raw events to BigQuery, and adds automated checks so a site release can't break measurement unnoticed.

## 2. Client context

- **Business:** Northwind Outdoor sells hiking and camping gear online in Greece and the EU. It also sells to businesses (outdoor clubs, schools) through bulk-order requests on a contact form.
- **Current state:** No tag manager: every tag deployment, update and rollback is a manual change in the site code, done by a developer, with no versioning. No consent banner, so the site does not comply with EU consent rules. No link between Google Ads and sales, so the client can't see which campaigns and ads drive orders, and bidding optimises without real conversion data.

### Technical maturity assessment

Scored 1 to 4 (1: missing, 2: ad hoc, 3: in place and documented, 4: in place, tested automatically and monitored).

| Area | Before | Score | After phase 1 | Score | Next step |
|---|---|---|---|---|---|
| Tag management | Tags hard-coded, no versions | 1 | GTM container, named versions, Preview before publish | 3 | Approval workflow in GTM for releases |
| Data layer | None | 1 | Ecommerce and lead events from the site code, prices from the catalog | 3 | Prices and order IDs from the backend |
| Consent | No banner | 1 | Consent Mode v2 advanced, default denied, demo banner | 3 | Certified CMP, consent rate monitored |
| First-party data | Form data unused for measurement | 1 | Leads measured without personal data | 2 | Enhanced conversions after DPO approval |
| Ads to sales link | None | 1 | UTM conventions, campaign attribution in BigQuery | 2 | Google Ads link, auto-tagging, imported conversions |
| Warehouse | None | 1 | Daily GA4 export to BigQuery (EU) | 3 | Billing enabled for streaming and retention |
| QA | Manual, after complaints | 1 | Automated hit checks, payload validation, export checks, reconciliation | 4 | Run on every site release |

## 3. Stakeholders

| Role | Responsible for | Signs off |
|---|---|---|
| Head of Marketing | KPIs, campaign naming, what reports must show | Sections 4, 5 |
| Web developer | Data layer, consent script, site releases | Section 6 |
| DPO / legal | Consent behaviour, what personal data may leave the site | Section 6, decision D-3 |
| Implementation lead (author) | GTM, GA4, BigQuery, QA, this document | Sections 7 to 10 |

## 4. Business objectives and KPIs

No baseline exists, because nothing is measured today; the first four weeks after go-live become the baseline.

| # | Business objective | KPI | Why this KPI | Source |
|---|---|---|---|---|
| O1 | Grow online sales | Ecommerce conversion rate, revenue, average order value | Conversion rate shows how well the site turns visits into orders, average order value shows how valuable each order is, and revenue is the end result. | GA4 `purchase` |
| O2 | Generate B2B leads | Leads per week, lead rate per session | Shows which platforms, content, ads or search queries bring in the most leads, so spend can be shifted toward them. | GA4 `generate_lead` |
| O3 | Find where shoppers drop off | Step conversion from product view to cart, checkout and purchase | A funnel shows each step of the journey and where shoppers drop off. | GA4 funnel / BigQuery |
| O4 | Stay privacy-compliant in the EEA | Consent rate (granted / total) | Shows how much traffic can be measured in full. A sudden drop usually means a broken banner or consent update, not a change in user behaviour, so it doubles as a health check for the implementation. | BigQuery `privacy_info` |

## 5. Measurement requirements

Priority: M must, S should, C could.

| ID | Requirement | Pri. | Owner | How it is checked |
|---|---|---|---|---|
| MR-1 | Every page view is measured, with consent state | M | Implementation | `tag_qa.py`: first hit `gcs=G100` before a choice |
| MR-2 | The four funnel steps are measured with items and value | M | Developer | `tag_qa.py`: `add_to_cart` value and items, `begin_checkout`, `purchase`; `reconcile.py` counts |
| MR-3 | Each order is counted once, with a unique ID | M | Developer | `tag_qa.py`: refresh sends nothing; `bq_checks.py`: no duplicate or missing IDs |
| MR-4 | A lead counts only when the server accepts the form, with its type | M | Developer | `tag_qa.py`: failed form sends nothing; `bq_checks.py`: every lead has `lead_type` |
| MR-5 | Promo clicks are measured per button | S | Marketing | `tag_qa.py`: `cta_click` with `cta_id`; `reconcile.py` |
| MR-6 | Size-guide downloads are measured | C | Implementation | Enhanced measurement, DebugView |
| MR-7 | Purchases and leads can be attributed to campaigns | M | Marketing | UTM conventions (tracking plan §3); `sql/own/02_campaign_attribution.sql` |
| MR-8 | Raw events are available in BigQuery daily | M | Implementation | `bq_checks.py`: export no older than 2 days |
| MR-9 | Measurement keeps working after site releases | S | Developer | `tag_qa.py` run on each release (deployment guide §6) |

## 6. Privacy and consent requirements

| ID | Requirement | How it is checked |
|---|---|---|
| PR-1 | Consent Mode v2, advanced. All four signals default to denied until the visitor chooses | Tag Assistant Consent tab; `tag_qa.py` |
| PR-2 | No analytics cookie before consent, and none after Reject all | `tag_qa.py`: no `_ga` cookie |
| PR-3 | No personal data (names, emails, phone numbers) in any event | `tag_qa.py` and `bq_checks.py`: no email in any hit or parameter |
| PR-4 | The visitor can change the choice at any time | "Cookie settings" link on every page |

Why advanced, not basic: with basic consent mode, Google tags send nothing until the visitor consents, so non-consenting traffic disappears from measurement. Advanced mode loads the tags with consent denied and sends cookieless pings (no cookies, no identifiers), which Google uses to model conversions in aggregate. Northwind keeps a more complete picture of campaign performance without tracking anyone who declined.

## 7. Assumptions, open questions and risks

| Type | Item | Impact | Handling |
|---|---|---|---|
| Assumption | The backend will later expose prices and order IDs to the data layer | Today the site computes them in the browser | Documented in the deployment guide; dedup belongs on the server |
| Assumption | Lead value is a flat 50 EUR estimate | Lead value in reports is indicative | Marketing to replace it with an average deal value |
| Open question | Which CMP will replace the demo banner? | Banner text and logging of consent records | DPO decision; the consent script is built to be swapped |
| Open question | When will the Google Ads account be linked? | No imported conversions or auto-tagging yet | UTMs until then (tracking plan §3) |
| Risk | Ad blockers and tracking protection drop hits | GA4 under-counts against the backend | Explain the gap with the consent rate; consider server-side tagging later |
| Risk | Visitors who decline consent can't be attributed | Up to half of purchases have no source (seen in testing) | Report attributed and unattributed side by side |
| Risk | BigQuery sandbox deletes tables after 60 days | History is lost | Enable billing before the first 60 days end |
| Risk | A site release breaks a tag silently | Missing data found weeks later | `tag_qa.py` in the release checklist |

## 8. Decisions

| # | Decision | Alternatives considered | Why |
|---|---|---|---|
| D-1 | Consent Mode advanced | Basic | Keeps cookieless pings for modeling without identifying anyone |
| D-2 | One GA4 tag for the four ecommerce events, with an anchored regex trigger | One tag per event | Fewer tags to keep in sync; anchoring stops partial matches such as `purchase_refund` |
| D-3 | No user-provided data; GTM's automatic detection off | Enhanced conversions now | Needs DPO approval and hashing rules first; the form has an email field that automatic detection would pick up |
| D-4 | `cta_text` stays unregistered | Register it as a dimension | Duplicates `cta_id` and splits rows when copy changes |
| D-5 | Purchase dedup in the browser for the demo | Server-side flag | No backend in the demo; on the real site the order record should hold it |
| D-6 | Daily export only | Streaming | Streaming needs billing; daily is enough for the KPIs |
| D-7 | Test with synthetic, labelled traffic | Wait for real traffic | Gives a known ground truth to reconcile the export against |

## 9. Out of scope (phase 1)

- Server-side tagging.
- Paid media activation and spend on Google Ads.
- CRM and offline conversion import.
- App data streams.
- A/B testing.
- A commercial CMP; phase 1 uses a demo banner.

## 10. Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Every event fires once with its parameters in Preview and DebugView | Met | Build log, phase 3 |
| No GA4 cookies before consent; hits carry the consent state | Met | `docs/img/` screenshots; `tag_qa.py` 21 of 21 |
| The daily BigQuery export runs and data-quality checks pass | Met | `bq_checks.py` 7 of 7 |
| What the site sent matches what reached BigQuery | 4 of 6 event types matched exactly; the other 2 were lost by the test harness, fixed, and re-run on 2026-10-24 (result pending the next export) | `sql/own/RESULTS.md` |
