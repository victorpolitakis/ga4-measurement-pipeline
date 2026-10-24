# Northwind Outdoor: measurement requirements and tracking plan

> **Sample document.** Northwind Outdoor is a fictional retailer created for this project. The structure follows a typical client measurement engagement.

## 1. Client context
- **Business:** Northwind Outdoor sells hiking and camping gear online in Greece and the EU. It also sells to businesses (outdoor clubs, schools) through bulk-order requests on a contact form.
- **Current state:** No tag manager: every tag deployment, update and rollback is a manual change in the site code, done by a developer, with no versioning. Google Tag Manager moves this into one container where Google and third-party tags are deployed, versioned and rolled back across the whole domain. No consent banner means the site does not comply with EU consent rules. There is no link between Google Ads and sales, so the client cannot see which campaigns and ads drive orders, and bidding optimises without real conversion data.
- **Stakeholders:**
  - Head of Marketing: owns the KPIs.
  - Web developer: implements the data layer.
  - DPO / legal: approves consent behaviour.

## 2. Business objectives and KPIs
| # | Business objective | KPI | Why this KPI | Source |
|---|---|---|---|---|
| O1 | Grow online sales | Ecommerce conversion rate, revenue, average order value | Conversion rate shows how well the site turns visits into orders, average order value shows how valuable each order is, and revenue is the end result. | GA4 `purchase` |
| O2 | Generate B2B leads | Leads per week, lead rate per session | Shows which platforms, content, ads or search queries bring in the most leads, so spend can be shifted toward them. | GA4 `generate_lead` |
| O3 | Find where shoppers drop off | Step conversion from product view to cart, checkout and purchase | A funnel exploration shows each step of the journey and where shoppers drop off. | GA4 funnel / BigQuery |
| O4 | Stay privacy-compliant in the EEA | Consent rate (granted / total) | Shows how much traffic can be measured in full. A higher rate means more observed conversions and larger remarketing audiences. A sudden drop usually means a broken banner or consent update, not a change in user behaviour, so it doubles as a health check for the implementation. | BigQuery `privacy_info` |

## 3. Tracking plan
Event names follow GA4 **recommended events** wherever one exists, so GA4's built-in ecommerce reports fill in automatically. `cta_click` is the only custom event.

| Event | Fires when | Parameters | Key event | Recommended / custom | Implemented via |
|---|---|---|---|---|---|
| `page_view` | Every page load | page_location, page_title | No | Automatic | Google tag |
| `view_item` | Product page loads | currency, value, items[], item_count | No | Recommended | dataLayer push, read by GTM |
| `add_to_cart` | "Add to cart" clicked | currency, value, items[], item_count | No | Recommended | dataLayer push, read by GTM |
| `begin_checkout` | Checkout page loads | currency, value, items[], item_count | No | Recommended | dataLayer push, read by GTM |
| `purchase` | Order confirmation shown | **transaction_id**, currency, value, items[], item_count | **Yes** | Recommended | dataLayer push, read by GTM |
| `generate_lead` | B2B contact form submitted successfully | lead_type, value (estimated), currency | **Yes** | Recommended | dataLayer push, read by GTM |
| `cta_click` | A promo banner / hero button is clicked | cta_id, cta_text | No | Custom | dataLayer push, read by GTM |
| `file_download` | Size-guide PDF clicked | file_name, file_extension | No | Automatic (enhanced measurement) | GA4 setting |

**Item fields** (used in `items[]`): item_id, item_name, item_category, price, quantity.

**`item_count`** is the number of units in `items[]`, computed in GTM by a Custom JavaScript variable. It lets reports show units per checkout or order without unnesting items.

**Registered in GA4:** custom dimensions `cta_id` and `lead_type`, and custom metric `item_count` (all event scope). Without registration, a parameter still reaches BigQuery but doesn't appear in GA4 reports.

**Not registered:** `cta_text`. It repeats what `cta_id` already identifies and changes whenever the button copy changes, so it would split one button into several report rows. It stays available in BigQuery for checking copy tests.

## 4. Data quality rules
- `purchase` must always have a unique `transaction_id`. GA4 deduplicates purchases with the same ID, and so do the BigQuery checks.
- `value` must be a number greater than 0 and match the sum of `price × quantity`. `currency` is always `EUR`.
- Each event fires **once** per user action. Reloading the confirmation page must not create a second purchase.

## 5. Privacy and consent
- Consent Mode v2, **advanced** implementation. All four signals default to `denied` until the visitor chooses.
- No personal data (names, emails) is sent in event parameters.
- Why advanced, not basic: with basic consent mode, Google tags send nothing until the visitor consents, so non-consenting traffic disappears from measurement. Advanced mode loads the tags with consent denied and sends cookieless pings (no cookies, no identifiers), which Google uses to model conversions in aggregate. Northwind keeps a more complete picture of campaign performance without tracking anyone who declined.

## 6. Out of scope (phase 1)
- Server-side tagging.
- Paid media activation.
- CRM / offline conversion import.
- Actual spend on Google Ads.
- App data streams.
- A/B testing.
- A commercial consent management platform (CMP); the project uses a demo banner.

## 7. Acceptance criteria
- Every event in section 3 fires once, with all its parameters, in GTM Preview and GA4 DebugView.
- No GA4 cookies are set before consent. Hits carry the correct consent state.
- The daily BigQuery export of GA4 data runs, and the data-quality checks pass.
