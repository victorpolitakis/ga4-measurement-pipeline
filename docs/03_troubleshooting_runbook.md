# Troubleshooting runbook

Symptoms seen or tested in this project, how to check them, and the fix. Work down the data path in order: the page pushes to the data layer, GTM fires a tag, the browser sends `/g/collect`, GA4 receives and processes it, BigQuery exports it. Find the first step where it breaks before changing anything.

| Symptom | Check | Likely cause | Fix |
|---|---|---|---|
| DebugView empty, Tag Assistant shows tags firing | DevTools Network, filter `collect`: are requests "Blocked"? | Ad blocker or browser tracking protection (seen with AdGuard and Firefox-based browsers) | Test with blockers off. For real users this is data loss, not a bug; server-side tagging on a first-party subdomain reduces it and must still respect consent |
| GA4 shows fewer purchases than the backend | Compare with the share of visitors who rejected consent; in BigQuery, `privacy_info.analytics_storage` | Consent denied: cookieless pings can't be tied to users, and modeling needs more volume | Expected under advanced consent mode. Report the gap with the consent rate next to it |
| Purchase counted twice | BigQuery: `transaction_id` seen more than once (`sql/public/04_duplicate_transactions.sql`) | Confirmation page reloaded or revisited, no guard | Send `purchase` once per order; on a real site the backend should remember which orders were reported |
| Conversions dropped right after a consent banner went live | Consent rate by day; first hit's `gcs` before any choice; `_ga` cookie | Expected drop in observed conversions, or a banner that never sends the update | If `gcs` stays `G100` after Accept, the update call is broken. Otherwise explain modeling and the consent rate |
| `_ga` cookie set before the visitor chooses | First `/g/collect` hit has no `gcs`, or `G111` | Consent default loads after GTM | Move the default above the GTM snippet |
| An event fires for the wrong event name | Trigger condition | GTM regex matching is partial | Anchor it: `^(...)$` |
| `value` is `NaN` or a long decimal | Data layer push in Preview | Bad cart data, or floating-point sums | Validate inputs; round to cents |
| A Data Layer Variable is `undefined` | Data Layer tab in Tag Assistant | The key sits at another level (`value` vs `ecommerce.value`), or a typo | Point the variable at the right path |
| Events from clicks just before a page change are missing, but only in automated runs | Count them in BigQuery against the script's ground truth (`qa/reconcile.py`) | GA4 batches events and sends them on `pagehide`; Playwright-driven Chromium doesn't fire it in time. Real browsers do | Fire `pagehide` in the test harness (`qa/browser_fix.py`); don't change the site for it |
| GTM publish fails with "Missing required settings" | Workspace Settings | The new Google Analytics tag expects a user-provided data setting | Add it with automatic detection **off** unless the client approved hashed personal data |
| Consent Overview lists Google tags as "not configured" | Tag consent settings | Additional consent never chosen | "No additional consent required" for Google tags; requiring it turns advanced mode into basic |
| A day is missing in BigQuery | Dataset tables, GA4 BigQuery link status | Export not linked yet, daily limit, or (sandbox) table older than 60 days expired | Re-link or upgrade; the export does not backfill |
| Measurement Protocol events never appear | `qa/mp_validate.py` | Invalid event name or parameters; the live endpoint returns 204 even for bad payloads | Validate against `/debug/mp/collect` first |
| Test purchases show `tagassistant.google.com / referral` as their source | BigQuery `collected_traffic_source` on Preview sessions | Tag Assistant opens the site from its own domain, so Preview sessions count as referrals | Add `tagassistant.google.com` to unwanted referrals (GA4 Admin, Data streams, Configure tag settings) |
