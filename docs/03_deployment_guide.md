# Deployment guide

How to deploy this measurement setup on a site, in the order that keeps data clean. Written for the next implementation, not only for Northwind: the steps hold for any GA4 and GTM deployment with a data layer.

## 1. Before anything is tagged

- Agree the tracking plan with the client ([BRD](01_BRD.md), [tracking plan](02_tracking_plan.md)). Every event needs a trigger condition, its parameters and an owner on the client side.
- Agree consent with the DPO: which signals, the default state, and basic or advanced mode. This project uses advanced mode with everything denied by default.
- Create the GA4 property and web stream, and the GTM web container. Set GA4 data retention to 14 months; the default of 2 months cuts explorations short.

## 2. Site code (developer)

1. **Consent default**, as the first script in `<head>`, before GTM. See `site/js/consent.js`. If it loads after GTM, Google tags run before any consent state exists, treat consent as granted and set cookies.
2. **GTM snippet** right after it, plus the `<noscript>` iframe after `<body>`.
3. **Data layer pushes** for each event in the tracking plan (`site/js/shop.js`, page scripts):
   - push `{ ecommerce: null }` before every ecommerce event;
   - take prices and IDs from the backend, never from page text;
   - send `purchase` once per order, and `generate_lead` only after the server accepts the form;
   - never put names, emails or phone numbers in event parameters.

## 3. GTM container

| Item | Setting |
|---|---|
| Google Analytics tag | Measurement ID, trigger Initialization – All Pages |
| Data Layer Variables | one per parameter, Version 2 |
| Custom Event triggers | anchored regex for grouped events, e.g. `^(view_item\|add_to_cart\|begin_checkout\|purchase)$` |
| GA4 event tag, ecommerce | event name `{{Event}}`, "Send Ecommerce data" from the data layer |
| GA4 event tags, others | one per custom event, parameters from the variables |
| Consent | Google tags: built-in checks, "No additional consent required". Non-Google tags: require the consent they need |
| User-provided data | automatic detection off unless the client has approved sending hashed personal data |

Test in Preview first, then publish as a named version with a description of what changed and why. Rollback is publishing the previous version from Versions.

## 4. GA4 property

- Key events: `purchase` (default), `generate_lead` with no default value, so the value sent with the event is kept.
- Custom dimensions and metrics for custom parameters (`cta_id`, `lead_type`, `item_count`). Parameters can't be changed after registration, only archived.
- Internal-traffic filter: define the client's IP ranges, leave the filter in **Testing** for a few days, check the "Test data filter name" dimension, then set it to Active. Active filtering deletes data permanently.
- BigQuery link: daily export to an EU dataset. In a sandbox project, tables expire after 60 days.

## 5. QA before and after go-live

```bash
python3 -m venv .venv && .venv/bin/pip install -r qa/requirements.txt && .venv/bin/python -m playwright install chromium
.venv/bin/python qa/tag_qa.py --base-url <site URL>
.venv/bin/python qa/mp_validate.py
```

- `tag_qa.py` checks the hits the browser sends: consent states, every funnel event and its parameters, the refresh guard, failed leads, and that no email leaks into a hit. It blocks the hits it captures, so it adds no data to GA4.
- `mp_validate.py` checks server-side Measurement Protocol payloads against the debug endpoint, which records nothing.
- Manually: Tag Assistant (Tags, Consent tabs) and GA4 DebugView, with ad blockers off.
- The day after go-live: the BigQuery export has a new `events_YYYYMMDD` table, and the data-quality queries in `sql/` return no duplicates or missing transaction IDs.

## 6. Handover

Give the client the tracking plan, the GTM version history, this guide and the [troubleshooting runbook](04_troubleshooting_runbook.md). Any later site release should be followed by a `tag_qa.py` run, because a template change can break a tag without any visible error.
