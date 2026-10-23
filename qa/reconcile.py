"""Expected vs observed: compare a traffic.py run with what reached BigQuery.

The CSV says what each synthetic visitor did. This script counts the business
events those visitors should have produced, split by consent, and puts them next
to what the GA4 export holds for the same time window on the live site.

Usage:
    .venv/bin/python qa/reconcile.py qa/output/traffic_20261023T060554Z_seed42.csv
"""

import csv
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bq

EVENTS = ["cta_click", "view_item", "add_to_cart", "begin_checkout", "purchase", "generate_lead"]


def expected(rows):
    out = {}
    for group, consents in (("consented", {"all", "analytics"}), ("cookieless", {"none"})):
        g = [r for r in rows if r["consent"] in consents]
        out[group] = {
            "cta_click": sum(r["entry"] == "hero_cta" for r in g),
            "view_item": sum(r["entry"] != "lead_form" for r in g),
            "add_to_cart": sum(r["add_to_cart"] == "True" for r in g),
            "begin_checkout": sum(r["begin_checkout"] == "True" for r in g),
            "purchase": sum(bool(r["transaction_id"]) for r in g),
            "generate_lead": sum(r["lead_ok"] == "True" for r in g),
        }
    return out


def observed(dataset, start, end):
    sql = f"""
        SELECT event_name,
          COUNTIF(privacy_info.analytics_storage = 'Yes') AS consented,
          COUNTIF(privacy_info.analytics_storage = 'No') AS cookieless
        FROM `{dataset}.events_*`
        WHERE _TABLE_SUFFIX BETWEEN '{start:%Y%m%d}' AND '{(end + timedelta(days=1)):%Y%m%d}'
          AND event_timestamp BETWEEN {int(start.timestamp() * 1e6)} AND {int(end.timestamp() * 1e6)}
          AND device.web_info.hostname = 'victorpolitakis.github.io'
          AND event_name IN ({", ".join(f"'{e}'" for e in EVENTS)})
        GROUP BY event_name"""
    rows = bq.run(sql)
    return {group: {r["event_name"]: int(r[group]) for r in rows} for group in ("consented", "cookieless")}


def main():
    path = Path(sys.argv[1])
    stamp = re.search(r"traffic_(\d{8}T\d{6}Z)", path.name).group(1)
    start = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=20)
    rows = list(csv.DictReader(path.open()))

    exp = expected(rows)
    obs = observed(bq.export_dataset(), start, end)
    print(f"Run {start:%Y-%m-%d %H:%M} UTC, {len(rows)} visitors\n")
    print(f"{'event':<15} {'expected':>9} {'observed':>9} {'diff':>6}   {'expected':>9} {'observed':>9} {'diff':>6}")
    print(f"{'':<15} {'consented':^26}   {'cookieless (consent denied)':^26}")
    for e in EVENTS:
        cells = []
        for group in ("consented", "cookieless"):
            x, o = exp[group][e], obs[group].get(e, 0)
            cells.append(f"{x:>9} {o:>9} {o - x:>+6}")
        print(f"{e:<15} " + "   ".join(cells))


if __name__ == "__main__":
    main()
