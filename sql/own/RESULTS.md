# Results on the own export

Dataset `northwind-measurement.analytics_559410347` (EU). All traffic is synthetic (`qa/traffic.py`) or from testing.

## Expected vs observed, run 1 (2026-10-23 06:05 UTC, 150 visitors, seed 42)

`qa/reconcile.py` compares what each synthetic visitor did (the CSV) with the events in the export for the same 20 minutes on the live site.

| Event | Consented: expected | observed | Consent denied: expected | observed |
|---|---|---|---|---|
| `cta_click` | 70 | **0** | 26 | **0** |
| `view_item` | 104 | 104 | 37 | 37 |
| `add_to_cart` | 38 | **0** | 20 | **0** |
| `begin_checkout` | 17 | 17 | 14 | 14 |
| `purchase` | 13 | 13 | 11 | 11 |
| `generate_lead` | 4 | 4 | 4 | 4 |

Two findings:

- **Cookieless pings reach the export.** The 11 purchases made after Reject all are in BigQuery with `privacy_info.analytics_storage = 'No'`, although GA4's own reports didn't show them. They have no usable user or session ID, so they can be counted but not attributed.
- **Every `cta_click` and `add_to_cart` was missing.** Both are pushed by a click just before the page changes. GA4 batches events for a few seconds and sends the batch on `pagehide`. In a normal browser the same click sent `cta_click` as the page unloaded; in the Chromium that Playwright drives, `pagehide` doesn't reach the page in time, so the batch was dropped. The site was fine; the test harness wasn't. `qa/browser_fix.py` now fires `pagehide` after each click, and run 2 (2026-10-24 11:09 UTC, seed 43) was made with the fix.

This is why the reconciliation exists: the QA script checked the content of each hit and passed, and only counting what reached the warehouse showed that two event types never arrived.

## Campaign attribution (`02_campaign_attribution.sql`, run 1)

| Source / medium / campaign | Purchases | Revenue (EUR) |
|---|---|---|
| google / cpc / autumn_tents | 11 | 2,377 |
| (consent denied, no source) | 11 | 2,048 |
| newsletter / email / autumn_tents | 2 | 378 |
| tagassistant.google.com / referral | 2 | 1,064 (my Preview tests on 2026-10-18) |

The ground truth agrees: 10 google purchases with Accept all plus 1 with Analytics only, 2 from the newsletter, none from Instagram. Almost half of the campaign's purchases can't be attributed to any source because those visitors declined consent.

## Consent rate (`01_consent_rate.sql`)

| Date | Page views | No consent signal | Analytics consent rate | Ads consent rate |
|---|---|---|---|---|
| 2026-10-18 | 16 | 16 | n/a (before Consent Mode) | n/a |
| 2026-10-23 | 395 | 0 | 68.4% | 59.0% |

The rate is per page view, so it depends on how many pages each group views. On the landing page it is 109 of 151 (72%), close to the share of synthetic visitors who accepted (109 of 150). Over all pages it is lower because, in this run, visitors who rejected happened to reach checkout more often (14 of 41, against 17 of 109). A per-page-view consent rate is fine for spotting a broken banner day to day, but the per-visitor rate is the one to quote.

One `cart` page view of a consented visitor is missing (16 of 17), from the same pre-navigation batching as above.

## Data-quality checks (`qa/bq_checks.py`, 2026-10-24)

7 of 7 passed: no purchase without a transaction ID, no zero or missing values, no duplicate transaction IDs (the refresh guard held), every lead has a `lead_type`, currency is always EUR, no email address in any parameter, and the export is current.
