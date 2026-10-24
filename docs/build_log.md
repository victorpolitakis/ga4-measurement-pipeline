# Build log

One entry per work session: what was done, what broke, how it was fixed.

## Phase 2 — Demo shop and data layer (JavaScript)

- Date: 2026-10-17
- Done:
  - Six static pages plus `site/js/shop.js`. The site only pushes to `window.dataLayer`; it never calls GA4 itself.
  - `window.dataLayer = window.dataLayer || []` keeps the array GTM already hooked into. Replacing it with a new array would disconnect GTM without any error.
  - Every ecommerce push is preceded by `{ ecommerce: null }`. GTM merges each push into one data model, so without the reset, fields from a `view_item` could carry over into the next `add_to_cart`.
  - Prices and names come from the product catalog in code, the stand-in for the backend, not from the text on the page. Page text breaks on formatting, redesigns and discounts.
  - `add_to_cart` sends the value of what was just added, not the whole cart. GA4 sums event values, so sending the cart total would count the same item more than once.
  - Cart values are rounded to cents, so floating-point results like 19.990000000000002 never reach GA4.
  - `purchase` fires once per order: confirmed orders are remembered, so a refresh of the confirmation page sends nothing. On a real site this check belongs on the server.
  - `generate_lead` fires only after the (simulated) server accepts the form, never on the click, and a flag stops double-clicks from creating two leads. No email or name goes into the event. An organisation name containing "fail" simulates a server error, to test that no lead is sent.
  - `cta_click` uses one click listener on the document and `closest("[data-cta-id]")`, so a new tracked button only needs an HTML attribute, and clicks on an icon inside the button still count.
- Found in review on 2026-10-18 and fixed on 2026-10-23: the cart in `localStorage` is parsed with a try/catch, which catches broken JSON but not valid JSON with a missing `quantity`, which would have sent `value: NaN`. `cartItems()` now drops lines with an unknown product or a quantity that is not a positive whole number.

## Phase 3 — GTM and GA4

- Date: 2026-10-18
- Done:
  - GTM: six Data Layer Variables (`cta_id`, `cta_text`, `lead_type`, `value`, `currency`, `ecommerce.items`) and three Custom Event triggers.
  - One GA4 event tag sends all four ecommerce events, using `{{Event}}` as the event name and the ecommerce object from the data layer. `generate_lead` and `cta_click` have their own tags with parameters.
  - Custom JavaScript variable `CJS - item_count`: sums `quantity` over `ecommerce.items` and returns 0 when there are no items. It's sent as `item_count` on the ecommerce events. In Preview it returned 3 on a purchase of two tents and a backpack, and 0 on a link click.
  - Checked every event in Preview, Tag Assistant and DebugView, then published. Versions: "v1 - GA4 base, ecommerce, lead, cta", "v2 - disable automatic user-provided data detection", "v3 - item_count parameter on ecommerce events".
  - GA4: `generate_lead` marked as a key event with no default value, so it keeps the 50 EUR sent with the event. Custom dimensions `cta_id` and `lead_type` (event scope). The internal-traffic filter stays in Testing, because all traffic on the demo is mine.
  - BigQuery daily export linked to project `northwind-measurement`, location EU. Sandbox tables expire after 60 days.
- Broke / surprised me:
  - GTM's regex matching is partial. `view_item|add_to_cart|begin_checkout|purchase` would also match an event such as `purchase_refund_request`.
  - DebugView stayed empty although Tag Assistant showed the hits. In the Network tab the `/g/collect` requests were blocked by an ad blocker (AdGuard), while the GTM requests went through, so GTM itself looked healthy. Firefox also lists `google-analytics.com` as a known tracker, so strict tracking protection would block it too.
  - The Google tag is now called the "Google Analytics" tag in GTM. Publishing failed with "Missing required settings" until the container had a user-provided data setting, and GTM's suggested fix turned on automatic detection of email, phone and address. The contact form has an email field. No data was sent, because the user-provided data terms were never accepted.
  - In the item count variable, checking `items === undefined` was not enough: the reset push sets `ecommerce` to `null`, and `null.reduce` throws. `!items` covers both.
  - `DLV - value` is `undefined` on ecommerce events. That's expected: it reads a top-level `value`, which only `generate_lead` has. Ecommerce events carry `ecommerce.value`, sent through "Send Ecommerce data".
- Fix:
  - Anchored the trigger regex: `^(view_item|add_to_cart|begin_checkout|purchase)$`.
  - Allowed the demo site in the ad blocker for testing. For a client, the data lost to blockers is a reason to look at server-side tagging on a first-party subdomain, which still has to respect the user's consent choice.
  - Turned automatic user-provided data detection off and published v2, so the container matches the "no personal data" rule in the tracking plan.

## Phase 4 — Consent Mode v2 (advanced)

- Date: 2026-10-23
- Done:
  - `site/js/consent.js`, loaded synchronously in every page's `<head>` before the GTM snippet. It sets all four signals (`ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`) to `denied` by default, turns on `ads_data_redaction`, and re-applies a saved choice before GTM loads.
  - A demo banner with Accept all, Analytics only and Reject all, plus a "Cookie settings" link in every footer to change the choice later. A real site would use a certified CMP.
  - Advanced mode, not basic: Google tags still load with consent denied and send cookieless pings, so GA4 sees that visits and conversions happened without being able to tie them to a person.
- Checked:
  - Locally, from the `/g/collect` requests: before any choice `gcs=G100` and no `_ga` cookie; after Accept all `gcs=G111` and `_ga` / `_ga_<id>` cookies appear.
  - On the live site in Tag Assistant's Consent tab, all three buttons (screenshots in `docs/img/`). The on-page default is always Denied; the update matches the button.
  - Reject all keeps `gcs=G100`, the same as no choice. The difference is in `gcd`, which records the default and the update separately, so an explicit refusal can be told apart from no answer.
- Broke / surprised me:
  - Hits were blocked again, this time by the browser itself: Firefox-based browsers block `google-analytics.com` in private windows, and Midori blocked it even with a tracking-protection exception. The `gcs` value can still be read from the blocked request's URL, and `_ga` is written by JavaScript in the page, so the consent check doesn't depend on the hit arriving.
  - GTM's Consent Overview listed every tag as "Consent Not Configured" although each Google tag has built-in consent checks. It only means the "additional consent" setting was never chosen. For Google tags the right answer is "No additional consent required"; requiring it would stop them firing without consent, which is basic mode. Set on all four tags and published as "v4 - consent settings for Google tags".

## Phase 5 and 6 — Synthetic traffic, QA and SQL

- Date: 2026-10-23
- Done:
  - `qa/traffic.py` (Playwright): 150 synthetic visitors of the mock `autumn_tents` campaign at 06:05 UTC, with a seed so the run can be repeated. Ground truth: 24 purchases, 8 accepted leads, 1 failed lead, 1 confirmation refresh; consent all 94, analytics only 15, reject 41.
  - GA4 Realtime right after the run matched the consented part exactly: 110 users (109 synthetic plus my own session), 104 `view_item`, 17 `begin_checkout`, 13 `purchase` (12 with Accept all, 1 with Analytics only), 4 `generate_lead`. The 11 purchases made after Reject all aren't there: they arrived as cookieless pings, and the demo has far too little traffic for GA4's modeling.
  - `qa/tag_qa.py`: 22 checks on the hits the browser sends, blocked before they reach GA4. 21 pass, 1 known issue.
  - `qa/mp_validate.py`: a valid Measurement Protocol purchase passes the debug endpoint; an event named `add-to-cart` is rejected with `NAME_INVALID`.
  - Seven queries on the public GA4 sample (`sql/public/`, results in `RESULTS.md`); the event total is 4,295,584, the same as the baseline. Consent rate, attribution and events-by-consent queries for the own export (`sql/own/`), `qa/bq_checks.py` and `qa/reconcile.py`.
  - GA4: custom metric `item_count` registered.
- Broke / surprised me:
  - The first QA run failed 11 checks that were fine. `time.sleep` in the polling loop blocked Playwright's sync API, so the request handler never ran while the script waited. Waiting with `page.wait_for_timeout` fixed it.
  - `cta_click` reaches the data layer and the tag fires, but GA4 holds the hit for a few seconds to batch it, and the hero link navigates at once. In headless Chromium the hit never leaves. My own click on 2026-10-18 did arrive in BigQuery, but that was in Preview (debug mode). Resolved on 2026-10-24, see below.
  - Public sample: in November 2020 `add_to_cart` (7,674) is lower than `begin_checkout` (9,546), the opposite of December. It looks like `add_to_cart` wasn't firing everywhere that month.
  - The `.env` with the Measurement Protocol secret had been saved in `site/`, the folder GitHub Pages publishes. It was git-ignored and never committed, so it was never deployed; it now sits at the repo root.
  - The `bq` CLI read the SQL files' leading `--` comment as a flag. The SQL now goes in on stdin.
  - The consent-rate query first counted events with no consent signal (before Consent Mode existed) as "not granted", which showed a 0% rate. NULL is now left out of the rate.
  - Preview sessions are attributed to `tagassistant.google.com / referral`.

### 2026-10-24 — Reconciliation and the missing click events

- The 23 Oct export arrived. `qa/reconcile.py` matched `view_item`, `begin_checkout`, `purchase` and `generate_lead` exactly, consented and cookieless, but found **0 of 96** `cta_click` and **0 of 58** `add_to_cart`. `qa/bq_checks.py`: 7 of 7 passed.
- Narrowing it down, one variable at a time:
  - headless shell and Chromium's new headless mode: both lost them;
  - a visible Playwright window: lost them too, so not a headless issue;
  - waiting 6 s before navigating: `add_to_cart` arrived, so GA4 sends the batch late, not never;
  - GTM `eventCallback` before navigating: fired after 0.29 s, when the tag ran, not when the hit left, so it doesn't help;
  - the same click in a normal browser (not driven by Playwright), with `fetch` and `sendBeacon` logged to localStorage: `cta_click` was sent as the page unloaded;
  - a synthetic `pagehide` under Playwright: `cta_click` sent; a synthetic `visibilitychange`: not sent.
- Cause: gtag sends its batch on `pagehide`, and Playwright-driven Chromium doesn't deliver it in time. Real visitors don't lose these events; the test harness did. Fix in `qa/browser_fix.py` (fire `pagehide` after each click and before closing a context). `tag_qa.py` now passes 21 of 21 with the navigation included, and run 2 (150 visitors, seed 43, 11:09 UTC) was made with the fix.
- Attribution of run 1: google / cpc 11 purchases, newsletter / email 2, instagram 0, and 11 with consent denied and no source, which matches the ground truth.
- I first explained the lower per-page-view consent rate (68.4% vs 72.7% of visitors) by "rejecters view fewer pages". A breakdown by page showed the opposite: in this run they reached checkout more often. Checked before writing it down.

