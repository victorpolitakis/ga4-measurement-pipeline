# Northwind Outdoor: measurement requirements and tracking plan

> **Sample document.** Northwind Outdoor is a fictional retailer created for this project. The structure follows a typical client measurement engagement.

## 1. Client context
- **Business:** Northwind Outdoor sells hiking and camping gear online in Greece and the EU. It also sells to businesses (outdoor clubs, schools) through bulk-order requests on a contact form.
- **Current state:** _TODO (Victor): describe what the client has today and why it's a problem. Example: no tag manager, a hard-coded analytics snippet, no consent banner, no link between ads and sales._
- **Stakeholders:**
  - Head of Marketing: owns the KPIs.
  - Web developer: implements the data layer.
  - DPO / legal: approves consent behaviour.

## 2. Business objectives → KPIs
| # | Business objective | KPI | Why this KPI | Source |
|---|---|---|---|---|
| O1 | Grow online sales | Ecommerce conversion rate, revenue, average order value | _TODO (Victor)_ | GA4 `purchase` |
| O2 | Generate B2B leads | Leads per week, lead rate per session | _TODO (Victor)_ | GA4 `generate_lead` |
| O3 | Find where shoppers drop off | Step conversion: view → cart → checkout → purchase | _TODO (Victor)_ | GA4 funnel / BigQuery |
| O4 | Stay privacy-compliant in the EEA | Consent rate (granted / total) | _TODO (Victor)_ | BigQuery `privacy_info` |

## 3. Tracking plan
Event names follow GA4 **recommended events** wherever one exists, so GA4's built-in ecommerce reports fill in automatically. `cta_click` is the only custom event.

| Event | Fires when | Parameters | Key event | Recommended / custom | Implemented via |
|---|---|---|---|---|---|
| `page_view` | Every page load | page_location, page_title | No | Automatic | Google tag |
| `view_item` | Product page loads | currency, value, items[] | No | Recommended | dataLayer → GTM |
| `add_to_cart` | "Add to cart" clicked | currency, value, items[] | No | Recommended | dataLayer → GTM |
| `begin_checkout` | Checkout page loads | currency, value, items[] | No | Recommended | dataLayer → GTM |
| `purchase` | Order confirmation shown | **transaction_id**, currency, value, items[] | **Yes** | Recommended | dataLayer → GTM |
| `generate_lead` | B2B contact form submitted successfully | lead_type, value (estimated), currency | **Yes** | Recommended | dataLayer → GTM |
| `cta_click` | A promo banner / hero button is clicked | cta_id, cta_text | No | Custom | dataLayer → GTM |
| `file_download` | Size-guide PDF clicked | file_name, file_extension | No | Automatic (enhanced measurement) | GA4 setting |

**Item fields** (used in `items[]`): item_id, item_name, item_category, price, quantity.

**Custom dimensions to register in GA4:** `cta_id` (event scope), `lead_type` (event scope). Without registering them, they still reach BigQuery but don't appear in GA4 reports.

## 4. Data quality rules
- `purchase` must always have a unique `transaction_id`. GA4 deduplicates purchases with the same ID, and so do the BigQuery checks.
- `value` must be a number greater than 0 and match the sum of `price × quantity`. `currency` is always `EUR`.
- Each event fires **once** per user action. Reloading the confirmation page must not create a second purchase.

## 5. Privacy and consent
- Consent Mode v2, **advanced** implementation. All four signals default to `denied` until the visitor chooses.
- No personal data (names, emails) is sent in event parameters.
- _TODO (Victor): one sentence on why "advanced" rather than "basic" for this client._

## 6. Out of scope (phase 1)
- Server-side tagging.
- Paid media activation.
- CRM / offline conversion import.
- _TODO (Victor): add anything else you'd push back on._

## 7. Acceptance criteria
- Every event in section 3 fires once, with all its parameters, in GTM Preview and GA4 DebugView.
- No GA4 cookies are set before consent. Hits carry the correct consent state.
- The GA4 → BigQuery export runs daily, and the data-quality checks pass.
