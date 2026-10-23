# Results on the public GA4 sample

Dataset: `bigquery-public-data.ga4_obfuscated_sample_ecommerce`, the Google Merchandise Store, 2020-11-01 to 2021-01-31. Run on 2026-10-23 from the BigQuery sandbox. Google obfuscates this dataset (some values are replaced with `<Other>` or `(data deleted)`), so the numbers show how the queries work, not the store's real performance.

## 00 · Event counts
4,295,584 events in 17 event types (55.9 MB scanned). The biggest are `page_view` 1,350,428, `user_engagement` 1,058,721 and `scroll` 493,072. Ecommerce: `view_item` 386,068, `add_to_cart` 58,543, `begin_checkout` 38,757, `purchase` 5,692.

## 01 · Funnel by session (995 MB scanned)
| Step | Sessions (open) | Sessions (closed) |
|---|---|---|
| All sessions | 360,129 | |
| view_item | 77,020 | 77,020 |
| add_to_cart | 15,188 | 15,173 |
| begin_checkout | 11,106 | 5,959 |
| purchase | 4,848 | 2,848 |

View to checkout is 14.4% and checkout to purchase 43.7% (open counts). The closed funnel is about half the open one at checkout: many checkout sessions have no `add_to_cart` in the same session, because the cart was filled in an earlier session or the add wasn't tracked. A funnel report that requires every step in one session undercounts buyers.

The month split shows the second reason. In November 2020 there were fewer `add_to_cart` events (7,674) than `begin_checkout` (9,546); from December the order is normal (35,347 vs 18,177). That pattern usually means `add_to_cart` wasn't firing on part of the site, though the obfuscated data can't confirm the cause.

## 02 · Channels (first-user source / medium)
`google / organic` brought the most buyers (1,454 purchases, $95,775), then `(direct)` (1,251, $79,650). `google / cpc` had 15,527 users but 166 purchases. These are first-user sources, not session sources; the 2020 export has no session-level source fields.

## 03 · Revenue by item
Top item: Google Zip Hoodie F/C, 271 units, $13,692. The top 15 are mostly apparel.

## 04 · Duplicate and missing transaction IDs
| | Count |
|---|---|
| purchase events | 5,692 |
| without a usable transaction_id (`(not set)`) | 906 (15.9%) |
| distinct transaction IDs | 4,451 |
| transaction IDs sent more than once | 326 |

Summing `purchase_revenue` over raw events would count those 326 orders more than once. GA4 reports deduplicate on `transaction_id`, so GA4 and a naive SQL total won't match.

## 05 · Days to first purchase (ROW_NUMBER)
2,563 buyers bought on the day of their first visit, 387 the next day, then a long tail.

## 06 · Time between sessions (LAG)
87,854 returning sessions. Median gap 13 hours, 90th percentile 275 hours (about 11 days); 61.6% of returns happen within a day.
