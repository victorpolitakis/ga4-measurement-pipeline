"""Automated tag QA for the Northwind Outdoor demo shop.

Drives the site with Playwright and checks the GA4 hits the browser actually
sends, not the dataLayer: a tag that is misconfigured in GTM still pushes to the
dataLayer, so only the outgoing /g/collect requests prove what GA4 receives.

Every GA4 request is captured and then aborted, so a QA run sends no data to the
GA4 property.

Usage:
    .venv/bin/python qa/tag_qa.py                       # live site
    .venv/bin/python qa/tag_qa.py --base-url http://localhost:8000/
Exit code is 1 if any check fails.
"""

import argparse
import sys
import time
from urllib.parse import parse_qsl, urlparse

from playwright.sync_api import sync_playwright

BASE_URL = "https://victorpolitakis.github.io/ga4-measurement-pipeline/"
MEASUREMENT_ID = "G-03MNY8H5GR"
TEST_EMAIL = "qa-check@example.com"


class Hits:
    """Collects GA4 hits. A request can carry several events: shared parameters
    sit in the URL and each event's own parameters are one line of the body."""

    def __init__(self):
        self.events = []
        self.raw = []

    def capture(self, route):
        request = route.request
        self.raw.append(request.url + "\n" + (request.post_data or ""))
        shared = dict(parse_qsl(urlparse(request.url).query))
        lines = [l for l in (request.post_data or "").splitlines() if l.strip()]
        for line in lines or [""]:
            self.events.append({**shared, **dict(parse_qsl(line))})
        route.abort()

    def named(self, name):
        return [e for e in self.events if e.get("en") == name]

    def wait_for(self, page, name, timeout=8.0):
        # page.wait_for_timeout, not time.sleep: the sync API only runs the route
        # handler (and so captures hits) while Playwright itself is waiting.
        end = time.time() + timeout
        while time.time() < end:
            if self.named(name):
                return self.named(name)[-1]
            page.wait_for_timeout(200)
        return None


class Report:
    def __init__(self):
        self.rows = []

    def check(self, scenario, what, ok, detail="", known_issue=False):
        status = "PASS" if ok else ("WARN" if known_issue else "FAIL")
        self.rows.append((scenario, what, status, detail))

    def print(self):
        width = max(len(r[1]) for r in self.rows)
        for scenario, what, status, detail in self.rows:
            print(f"{status}  {scenario:<14} {what:<{width}}  {detail}")
        counts = {k: sum(1 for r in self.rows if r[2] == k) for k in ("PASS", "WARN", "FAIL")}
        print(f"\n{counts['PASS']} passed, {counts['WARN']} known issues, {counts['FAIL']} failed")
        return counts["FAIL"]


def new_page(browser, hits):
    context = browser.new_context()
    context.route("**/g/collect**", hits.capture)
    page = context.new_page()
    return context, page


def has_ga_cookie(context):
    return any(c["name"] == "_ga" for c in context.cookies())


def settle(page, ms=1500):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def scenario_rejected(browser, base, r):
    s = "consent denied"
    hits = Hits()
    context, page = new_page(browser, hits)
    page.goto(base)
    first = hits.wait_for(page, "page_view")
    r.check(s, "page_view sent before any choice", first)
    r.check(s, "first hit has gcs=G100", first and first.get("gcs") == "G100", first and first.get("gcs"))
    r.check(s, "no _ga cookie before a choice", not has_ga_cookie(context))
    page.click('[data-consent="none"]')
    page.click('a[href="product.html?id=NW-PACK-45"]')
    view = hits.wait_for(page, "view_item")
    r.check(s, "view_item still sent (cookieless)", view)
    r.check(s, "view_item has gcs=G100", view and view.get("gcs") == "G100", view and view.get("gcs"))
    settle(page)
    r.check(s, "no _ga cookie after Reject all", not has_ga_cookie(context))
    context.close()


def scenario_purchase(browser, base, r):
    s = "consent granted"
    hits = Hits()
    context, page = new_page(browser, hits)
    page.goto(base)
    page.click('[data-consent="all"]')
    # GA4 batches events for a few seconds before sending. The hero link navigates at
    # once, so first click it with navigation blocked to check the hit's content...
    page.evaluate("document.addEventListener('click', e => e.preventDefault(), { once: true })")
    page.click('[data-cta-id="hero_tent"]')
    cta = hits.wait_for(page, "cta_click", timeout=20)
    r.check(s, "cta_click with cta_id=hero_tent", cta and cta.get("ep.cta_id") == "hero_tent", cta and cta.get("ep.cta_id"))
    # ...then click it for real and see whether the hit survives the navigation.
    page.click('[data-cta-id="hero_tent"]')
    view = hits.wait_for(page, "view_item")
    r.check(s, "view_item has gcs=G111", view and view.get("gcs") == "G111", view and view.get("gcs"))
    r.check(s, "_ga cookie after Accept all", has_ga_cookie(context))
    settle(page)
    r.check(s, "cta_click survives the navigation it starts", len(hits.named("cta_click")) == 2,
            f"{len(hits.named('cta_click'))} of 2 cta_click hits sent", known_issue=True)

    page.fill("#qty", "2")
    page.click("#add")
    add = hits.wait_for(page, "add_to_cart")
    r.check(s, "add_to_cart value=378 EUR", add and add.get("epn.value") == "378" and add.get("cu") == "EUR",
            add and f"{add.get('epn.value')} {add.get('cu')}")
    r.check(s, "add_to_cart item line pr1", add and "NW-TENT-2P" in add.get("pr1", ""), add and add.get("pr1", "")[:40])

    page.click('a.btn[href="cart.html"]')
    page.click('a[href="checkout.html"]')
    checkout = hits.wait_for(page, "begin_checkout")
    r.check(s, "begin_checkout sent", checkout)

    page.click("#place")
    page.wait_for_url("**/confirmation.html*")
    purchase = hits.wait_for(page, "purchase")
    order_id = urlparse(page.url).query.split("order=")[-1]
    r.check(s, "purchase transaction_id matches order", purchase and purchase.get("ep.transaction_id") == order_id,
            purchase and purchase.get("ep.transaction_id"))
    r.check(s, "purchase value=378", purchase and purchase.get("epn.value") == "378", purchase and purchase.get("epn.value"))
    r.check(s, "purchase item_count=2", purchase and purchase.get("epn.item_count") == "2",
            purchase and purchase.get("epn.item_count"))

    page.reload()
    settle(page, 2500)
    r.check(s, "refresh sends no second purchase", len(hits.named("purchase")) == 1, f"{len(hits.named('purchase'))} purchase hit(s)")
    r.check(s, "every hit goes to the right property", all(e.get("tid") == MEASUREMENT_ID for e in hits.events))
    context.close()


def scenario_leads(browser, base, r):
    s = "lead form"
    hits = Hits()
    context, page = new_page(browser, hits)
    page.goto(base + "contact.html")
    page.click('[data-consent="all"]')

    page.fill("#company", "QA fail check")
    page.fill("#email", TEST_EMAIL)
    page.click('button[type="submit"]')
    page.wait_for_selector("#status:not([hidden])")
    settle(page)
    r.check(s, "server error sends no generate_lead", not hits.named("generate_lead"))

    page.fill("#company", "QA outdoor club")
    page.fill("#email", TEST_EMAIL)
    page.select_option("#lead_type", "club")
    page.click('button[type="submit"]')
    lead = hits.wait_for(page, "generate_lead")
    r.check(s, "generate_lead after success", lead)
    r.check(s, "lead_type=club, value=50 EUR",
            lead and lead.get("ep.lead_type") == "club" and lead.get("epn.value") == "50" and lead.get("cu") == "EUR",
            lead and f"{lead.get('ep.lead_type')} {lead.get('epn.value')} {lead.get('cu')}")
    settle(page)
    leaked = [h for h in hits.raw if TEST_EMAIL in h or TEST_EMAIL.replace("@", "%40") in h]
    r.check(s, "email never appears in any hit", not leaked, f"{len(leaked)} hit(s) contain it")
    context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    base = args.base_url if args.base_url.endswith("/") else args.base_url + "/"

    r = Report()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scenario in (scenario_rejected, scenario_purchase, scenario_leads):
            try:
                scenario(browser, base, r)
            except Exception as e:  # a crash in one scenario is a failure, not the end of the run
                r.check(scenario.__name__, "scenario ran to the end", False, f"{type(e).__name__}: {e}".splitlines()[0])
        browser.close()
    sys.exit(1 if r.print() else 0)


if __name__ == "__main__":
    main()
