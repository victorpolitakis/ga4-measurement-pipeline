"""Validate Measurement Protocol payloads against GA4's debug endpoint.

The Measurement Protocol sends events server to server (for example a purchase
confirmed by the backend, or an offline conversion). The /debug/mp/collect
endpoint checks a payload and returns validation messages without recording
anything, so this script never adds data to the property.

One payload is valid; the other is broken on purpose, to show the check catches it.

Needs GA4_API_SECRET in the git-ignored .env file at the repo root
(GA4 Admin > Data streams > web stream > Measurement Protocol API secrets).

Usage:
    .venv/bin/python qa/mp_validate.py
Exit code is 1 if the valid payload fails or the broken one passes.
"""

import json
import sys
import urllib.request
from pathlib import Path

MEASUREMENT_ID = "G-03MNY8H5GR"
DEBUG_ENDPOINT = "https://www.google-analytics.com/debug/mp/collect"


def read_secret():
    env = Path(__file__).resolve().parent.parent / ".env"
    for line in env.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "GA4_API_SECRET" and value.strip():
            return value.strip().strip('"').strip("'")
    sys.exit("GA4_API_SECRET is missing from .env")


def validate(secret, payload):
    url = f"{DEBUG_ENDPOINT}?measurement_id={MEASUREMENT_ID}&api_secret={secret}"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response).get("validationMessages", [])


VALID_PURCHASE = {
    "client_id": "123456789.1700000000",
    "events": [{
        "name": "purchase",
        "params": {
            "transaction_id": "NW-MP-TEST-0001",
            "currency": "EUR",
            "value": 189.0,
            "items": [{"item_id": "NW-TENT-2P", "item_name": "Ridgeline 2-Person Tent",
                       "item_category": "Tents", "price": 189.0, "quantity": 1}],
        },
    }],
}

# A mistake a backend developer could make: a hyphen in the event name. GA4 accepts
# only letters, digits and underscores, so the event would be dropped.
BROKEN_EVENT = {
    "client_id": "123456789.1700000000",
    "events": [{"name": "add-to-cart", "params": {"currency": "EUR", "value": 189.0}}],
}


def main():
    secret = read_secret()
    failed = False

    messages = validate(secret, VALID_PURCHASE)
    if messages:
        failed = True
        print("FAIL  valid purchase was rejected:")
    else:
        print("PASS  valid purchase: no validation messages")
    for m in messages:
        print(f"      {m.get('validationCode')}: {m.get('description')}")

    messages = validate(secret, BROKEN_EVENT)
    if messages:
        print(f"PASS  broken event caught ({len(messages)} message(s)):")
    else:
        failed = True
        print("FAIL  broken event was accepted")
    for m in messages:
        print(f"      {m.get('validationCode')} on {m.get('fieldPath')}: {m.get('description')}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
