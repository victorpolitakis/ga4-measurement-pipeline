"""Synthetic traffic for the "autumn_tents" mock campaign.

Each simulated visitor gets a fresh browser context (a new user), lands on the
home page with campaign UTMs, makes a consent choice and walks some way down
the funnel. The script writes what every visitor actually did to a CSV, the
ground truth that the BigQuery export is later checked against.

All traffic this script sends is synthetic: the shop is a demo and no real
person is behind any of these visits.

Usage:
    .venv/bin/python qa/traffic.py --visitors 150 --seed 42
"""

import argparse
import asyncio
import csv
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

BASE_URL = "https://victorpolitakis.github.io/ga4-measurement-pipeline/"
CAMPAIGN = "autumn_tents"

# Headless Chromium announces itself as "HeadlessChrome", which GA4's bot
# filtering drops. A normal desktop Chrome string keeps the synthetic visits.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
)

# Each source has its own intent, so attribution by source shows a difference.
# Probabilities are per step, given the visitor reached the previous step.
SOURCES = [
    # (source, medium, share, add_to_cart, begin_checkout, purchase)
    ("google", "cpc", 0.50, 0.55, 0.65, 0.70),
    ("newsletter", "email", 0.30, 0.45, 0.55, 0.60),
    ("instagram", "social", 0.20, 0.25, 0.40, 0.45),
]
CONSENT = [("all", 0.60), ("analytics", 0.15), ("none", 0.25)]
PRODUCTS = ["NW-TENT-2P", "NW-PACK-45", "NW-BOOT-GTX"]
LEAD_SHARE = 0.08          # visitors who go to the B2B form instead of shopping
REFRESH_CONFIRMATION = 0.15  # purchasers who reload the confirmation page


def pick(rng, weighted):
    return rng.choices([w[0] for w in weighted], weights=[w[-1] for w in weighted])[0]


def plan_visitor(rng, n):
    """Decide up front what visitor n will do, so the run is reproducible."""
    source = rng.choices(SOURCES, weights=[s[2] for s in SOURCES])[0]
    name, medium, _, p_add, p_checkout, p_buy = source
    v = {
        "visitor": n,
        "source": name,
        "medium": medium,
        "consent": pick(rng, CONSENT),
        "entry": "hero_cta" if rng.random() < 0.7 else "product_grid",
        "product": None,
        "quantity": rng.choice([1, 1, 1, 2]),
        "add_to_cart": False,
        "begin_checkout": False,
        "purchase": False,
        "refreshed_confirmation": False,
        "lead_type": None,
    }
    if rng.random() < LEAD_SHARE:
        v["entry"] = "lead_form"
        v["lead_type"] = rng.choice(["club", "school", "other"])
        return v
    v["product"] = "NW-TENT-2P" if v["entry"] == "hero_cta" else rng.choice(PRODUCTS)
    v["add_to_cart"] = rng.random() < p_add
    v["begin_checkout"] = v["add_to_cart"] and rng.random() < p_checkout
    v["purchase"] = v["begin_checkout"] and rng.random() < p_buy
    v["refreshed_confirmation"] = v["purchase"] and rng.random() < REFRESH_CONFIRMATION
    return v


async def settle(page):
    # Give GA4 hits time to leave before the next navigation or the context closes.
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(800)


async def run_visitor(browser, base_url, v, send_hits=True):
    utm = f"utm_source={v['source']}&utm_medium={v['medium']}&utm_campaign={CAMPAIGN}"
    context = await browser.new_context(user_agent=USER_AGENT, locale="en-GB")
    if not send_hits:
        # Dry run: the pages and the data layer work as usual, but nothing reaches GA4.
        await context.route("**/g/collect**", lambda route: route.abort())
    page = await context.new_page()
    v["transaction_id"] = None
    v["lead_ok"] = None
    try:
        await page.goto(f"{base_url}?{utm}")
        await page.click(f'[data-consent="{v["consent"]}"]')
        await settle(page)

        if v["entry"] == "lead_form":
            await page.click('a[href="contact.html"]')
            # "fail" in the organisation name makes the demo server reject the form.
            company = "Synthetic fail test" if v.get("force_fail") else f"Synthetic {v['lead_type']} {v['visitor']}"
            await page.fill("#company", company)
            await page.fill("#email", f"visitor{v['visitor']}@example.com")
            await page.select_option("#lead_type", v["lead_type"])
            await page.click('button[type="submit"]')
            await page.wait_for_selector("#status:not([hidden])")
            v["lead_ok"] = "Thanks" in await page.inner_text("#status")
            await settle(page)
            return v

        if v["entry"] == "hero_cta":
            await page.click('[data-cta-id="hero_tent"]')
        else:
            await page.click(f'a[href="product.html?id={v["product"]}"]')
        await page.wait_for_selector("#add")
        await settle(page)

        if not v["add_to_cart"]:
            return v
        await page.fill("#qty", str(v["quantity"]))
        await page.click("#add")
        await settle(page)

        if not v["begin_checkout"]:
            return v
        await page.click('a.btn[href="cart.html"]')
        await page.click('a[href="checkout.html"]')
        await page.wait_for_selector("#place")
        await settle(page)

        if not v["purchase"]:
            return v
        await page.click("#place")
        await page.wait_for_url("**/confirmation.html*")
        await settle(page)
        v["transaction_id"] = parse_qs(urlparse(page.url).query)["order"][0]
        if v["refreshed_confirmation"]:
            await page.reload()
            await settle(page)
        return v
    finally:
        await context.close()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--visitors", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--dry-run", action="store_true", help="block GA4 hits, for testing the script")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    plans = [plan_visitor(rng, n) for n in range(1, args.visitors + 1)]
    # One lead is forced to fail, to show the server-error path sends no generate_lead.
    leads = [v for v in plans if v["entry"] == "lead_form"]
    if leads:
        leads[0]["lead_type"] = "other"
        leads[0]["force_fail"] = True

    started = datetime.now(timezone.utc)
    sem = asyncio.Semaphore(args.concurrency)
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        async def one(v):
            async with sem:
                try:
                    return await run_visitor(browser, args.base_url, v, send_hits=not args.dry_run)
                except Exception as e:  # keep the run going; record the failure
                    v["error"] = f"{type(e).__name__}: {e}".splitlines()[0]
                    return v

        results = await asyncio.gather(*(one(v) for v in plans))
        await browser.close()

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"traffic_{started:%Y%m%dT%H%M%SZ}_seed{args.seed}.csv"
    fields = ["visitor", "source", "medium", "consent", "entry", "product", "quantity",
              "add_to_cart", "begin_checkout", "purchase", "transaction_id",
              "refreshed_confirmation", "lead_type", "lead_ok", "error"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    def count(key):
        return sum(1 for r in results if r.get(key))

    print(f"Run started {started:%Y-%m-%d %H:%M:%S} UTC, {len(results)} visitors, seed {args.seed}")
    print(f"add_to_cart {count('add_to_cart')}, begin_checkout {count('begin_checkout')}, "
          f"purchase {count('transaction_id')}, confirmation refreshes {count('refreshed_confirmation')}")
    print(f"leads accepted {sum(1 for r in results if r.get('lead_ok') is True)}, "
          f"leads failed {sum(1 for r in results if r.get('lead_ok') is False)}, errors {count('error')}")
    print(f"Ground truth written to {out}")


if __name__ == "__main__":
    asyncio.run(main())
