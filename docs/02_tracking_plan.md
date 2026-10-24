# Northwind Outdoor: tracking plan

> **Sample document** for a fictional retailer. Companion to the [BRD](01_BRD.md): the BRD says what the business needs measured and why; this document says exactly what is sent. Requirement IDs (MR-…) refer to the BRD.

Version 2.0, 2026-10-24.

## 1. Events

Event names follow GA4 recommended events wherever one exists, so GA4's ecommerce reports fill in without extra setup. `cta_click` is the only custom event.

| Event | Fires when | Parameters | Key event | Type | Source | Requirement |
|---|---|---|---|---|---|---|
| `page_view` | Every page load | page_location, page_title | No | Automatic | Google Analytics tag | MR-1 |
| `view_item` | Product page loads | currency, value, items, item_count | No | Recommended | data layer | MR-2 |
| `add_to_cart` | "Add to cart" clicked | currency, value (added item only), items, item_count | No | Recommended | data layer | MR-2 |
| `begin_checkout` | Checkout page loads with a non-empty cart | currency, value, items, item_count | No | Recommended | data layer | MR-2 |
| `purchase` | Order confirmation shown, once per order | **transaction_id**, currency, value, items, item_count | **Yes** | Recommended | data layer | MR-2, MR-3 |
| `generate_lead` | B2B form accepted by the server | lead_type, value (estimated), currency | **Yes** | Recommended | data layer | MR-4 |
| `cta_click` | A hero or promo button is clicked | cta_id, cta_text | No | Custom | data layer | MR-5 |
| `file_download` | Size-guide PDF clicked | file_name, file_extension | No | Automatic | enhanced measurement | MR-6 |

## 2. Data dictionary

| Parameter | Type | Example | Sent on | Comes from | In GA4 reports |
|---|---|---|---|---|---|
| `currency` | string, ISO 4217 | `EUR` | ecommerce events, `generate_lead` | site constant | built in |
| `value` | number, 2 decimals | `378.00` | ecommerce events, `generate_lead` | catalog prices × quantity, rounded to cents; leads: fixed estimate of 50 | built in |
| `items` | array | see item fields | ecommerce events | catalog (backend stand-in) | built in (item reports) |
| `transaction_id` | string, unique per order | `NW-1792751565245-352` | `purchase` | order created at checkout | built in |
| `item_count` | integer ≥ 1 | `2` | ecommerce events | GTM Custom JavaScript variable (sum of `quantity`) | custom metric |
| `lead_type` | string: `club`, `school`, `other` | `club` | `generate_lead` | form select | custom dimension |
| `cta_id` | string, snake_case | `hero_tent` | `cta_click` | `data-cta-id` attribute | custom dimension |
| `cta_text` | string | `Shop the Ridgeline tent` | `cta_click` | button text | not registered (see below) |

**Item fields:** `item_id` (e.g. `NW-TENT-2P`), `item_name`, `item_category`, `price` (number), `quantity` (integer ≥ 1).

**Not sent anywhere:** names, email addresses, phone numbers, free-text form fields. GTM's automatic detection of user-provided data is off.

**Why `cta_text` isn't registered:** it repeats what `cta_id` identifies and changes whenever the copy changes, which would split one button into several report rows. It stays in BigQuery for checking copy changes.

## 3. Campaign tagging

All paid and owned links carry UTMs in lower case, with the campaign name in snake_case.

| Channel | utm_source | utm_medium | utm_campaign |
|---|---|---|---|
| Google Ads (until auto-tagging is linked) | `google` | `cpc` | `autumn_tents` |
| Newsletter | `newsletter` | `email` | `autumn_tents` |
| Instagram | `instagram` | `social` | `autumn_tents` |

Tag Assistant must be excluded as a referral (`tagassistant.google.com`), or test sessions show up as a traffic source.

## 4. Data quality rules

Checked automatically by `qa/tag_qa.py` (hits) and `qa/bq_checks.py` (export).

- `purchase` always has a unique `transaction_id`; a reload of the confirmation page sends nothing.
- `value` is a number greater than 0 and equals the sum of `price × quantity`; `currency` is always `EUR`.
- Each event fires once per user action. `generate_lead` never fires for a form the server rejected.
- No parameter contains an email address.
