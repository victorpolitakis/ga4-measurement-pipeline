"""Data-quality checks on the project's own GA4 BigQuery export.

Each check is a query that should return 0. Run after each daily export.

Usage:
    .venv/bin/python qa/bq_checks.py
Exit code is 1 if any check fails.
"""

import sys

import bq

CHECKS = [
    ("purchase without a transaction_id", """
        SELECT COUNT(*) AS n FROM `{d}.events_*`
        WHERE event_name = 'purchase'
          AND IFNULL(ecommerce.transaction_id, '') IN ('', '(not set)')"""),
    ("purchase with value missing or <= 0", """
        SELECT COUNT(*) AS n FROM `{d}.events_*`
        WHERE event_name = 'purchase' AND IFNULL(ecommerce.purchase_revenue, 0) <= 0"""),
    ("transaction_id sent more than once", """
        SELECT COUNT(*) AS n FROM (
          SELECT ecommerce.transaction_id FROM `{d}.events_*`
          WHERE event_name = 'purchase' AND ecommerce.transaction_id IS NOT NULL
          GROUP BY 1 HAVING COUNT(*) > 1)"""),
    ("generate_lead without lead_type", """
        SELECT COUNT(*) AS n FROM `{d}.events_*`
        WHERE event_name = 'generate_lead'
          AND NOT EXISTS (SELECT 1 FROM UNNEST(event_params) WHERE key = 'lead_type' AND value.string_value IS NOT NULL)"""),
    ("currency other than EUR", """
        SELECT COUNT(*) AS n FROM `{d}.events_*`, UNNEST(event_params) p
        WHERE p.key = 'currency' AND p.value.string_value != 'EUR'"""),
    ("email address in any event parameter", """
        SELECT COUNT(*) AS n FROM `{d}.events_*`, UNNEST(event_params) p
        WHERE REGEXP_CONTAINS(IFNULL(p.value.string_value, ''), r'[^@\\s]+@[^@\\s]+\\.[a-z]{{2,}}')"""),
    ("days since the latest export table (should be <= 2)", """
        SELECT GREATEST(DATE_DIFF(CURRENT_DATE(), PARSE_DATE('%Y%m%d', MAX(event_date)), DAY) - 2, 0) AS n
        FROM `{d}.events_*`"""),
]


def main():
    dataset = bq.export_dataset()
    print(f"Dataset {dataset}\n")
    failed = 0
    for name, sql in CHECKS:
        n = int(bq.run(sql.format(d=dataset))[0]["n"])
        ok = n == 0
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  ({n})"))
    print(f"\n{len(CHECKS) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
