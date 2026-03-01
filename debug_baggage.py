"""
Diagnostic script: dump raw Google Flights payload to find baggage fields.
"""
import json
import urllib.parse
import re
from primp import Client


def _encode_shopping_request(legs, tokens):
    flights_array = []
    for leg in legs:
        flights_array.append([
            [[[leg["from"], 0]]],
            [[[leg["to"], 0]]],
            None, 0, None, None,
            leg["date"],
            None, None, None, None, None, None, None, 3
        ])

    tokens_arr = []
    if tokens:
        token_entry = [None, None, None, tokens[0]]
        for t in tokens[1:]:
            token_entry.append(t)
        tokens_arr = [token_entry]

    inner_json = [
        tokens_arr,
        [None, None, 3, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None, flights_array, None, None, None, 1],
        0, 0, 0, 1
    ]
    req_str = json.dumps([None, json.dumps(inner_json, separators=(',', ':'))], separators=(',', ':'))
    return f"f.req={urllib.parse.quote(req_str)}&"


def fetch_raw():
    legs = [
        {"from": "TPE", "to": "NRT", "date": "2026-04-10"},
        {"from": "NRT", "to": "TPE", "date": "2026-04-17"},
    ]

    client = Client(impersonate="chrome_127", impersonate_os="macos", referer=True, cookie_store=True)
    url = (
        "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
        ".FlightsFrontendService/GetShoppingResults"
        "?f.sid=-5642963406499784770&bl=boq_travel-frontend-flights-ui_20260225.02_p0"
        "&hl=en-US&gl=US&curr=USD&soc-app=162&soc-platform=1&soc-device=1&rt=c"
    )
    headers = {
        "accept": "*/*",
        "accept-language": "en-US",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "cookie": (
            "CONSENT=YES+cb.20230810-00-p0.en+FX+874; "
            "SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg"
        ),
    }
    body = _encode_shopping_request(legs, []).encode("utf-8")
    res = client.post(url, headers=headers, content=body)
    print(f"HTTP {res.status_code}")
    return res.text


def parse_payload(raw):
    lines = raw.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[['):
            outer = json.loads(stripped)
            inner_str = outer[0][2]
            return json.loads(inner_str)
    return None


def safe_repr(v, max_len=120):
    s = repr(v)
    return s[:max_len] + "..." if len(s) > max_len else s


def dump_structure(obj, path="", depth=0, max_depth=6):
    indent = "  " * depth
    if depth > max_depth:
        print(f"{indent}{path}: [MAX DEPTH]")
        return
    if isinstance(obj, list):
        print(f"{indent}{path}: list[{len(obj)}]")
        for i, v in enumerate(obj):
            dump_structure(v, f"[{i}]", depth + 1, max_depth)
    elif isinstance(obj, dict):
        print(f"{indent}{path}: dict{{{list(obj.keys())}}}")
        for k, v in obj.items():
            dump_structure(v, f".{k}", depth + 1, max_depth)
    else:
        print(f"{indent}{path}: {safe_repr(obj)}")


def search_for_baggage_keywords(obj, path="", found=None):
    """Recursively search for strings containing baggage-related keywords."""
    if found is None:
        found = []
    keywords = ["bag", "luggage", "carry", "checked", "allowance", "cabin", "kilo", "kg", "lb", "piece"]
    if isinstance(obj, str):
        low = obj.lower()
        if any(kw in low for kw in keywords):
            found.append((path, obj[:200]))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            search_for_baggage_keywords(v, f"{path}[{i}]", found)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            search_for_baggage_keywords(v, f"{path}.{k}", found)
    return found


def dump_flight_entry(k, index):
    """Dump a single flight entry (k) with all its fields."""
    print(f"\n{'='*60}")
    print(f"Flight entry [{index}] — top-level keys (list of {len(k)} elements):")
    for i, v in enumerate(k):
        print(f"  k[{i}]: {safe_repr(v)}")

    flight = k[0]
    print(f"\n  flight (k[0]) — list of {len(flight)} elements:")
    for i, v in enumerate(flight):
        print(f"    flight[{i}]: {safe_repr(v)}")

    print(f"\n  k[1] (price/token area): {safe_repr(k[1])}")


if __name__ == "__main__":
    print("Fetching raw payload...")
    raw = fetch_raw()

    print("Parsing payload...")
    payload = parse_payload(raw)
    if payload is None:
        print("Failed to parse payload!")
        exit(1)

    print(f"Payload has {len(payload)} top-level elements")
    print("\n--- Top-level payload structure ---")
    for i, v in enumerate(payload):
        print(f"payload[{i}]: {safe_repr(v)}")

    # Build flight list from payload[2][0] and payload[3][0]
    flight_list = []
    try:
        if payload[2] and payload[2][0]:
            flight_list.extend(payload[2][0])
            print(f"\npayload[2][0] (Top Flights): {len(payload[2][0])} entries")
    except (IndexError, TypeError):
        pass
    try:
        if payload[3] and payload[3][0]:
            flight_list.extend(payload[3][0])
            print(f"payload[3][0] (Standard Flights): {len(payload[3][0])} entries")
    except (IndexError, TypeError):
        pass

    print(f"\nTotal flight entries: {len(flight_list)}")

    # Dump first 2 entries in detail
    for i, k in enumerate(flight_list[:2]):
        dump_flight_entry(k, i)

    # Search for baggage-related strings in the entire payload
    print("\n\n--- Searching for baggage/bag keywords in entire payload ---")
    hits = search_for_baggage_keywords(payload)
    if hits:
        for path, val in hits:
            print(f"  {path}: {val!r}")
    else:
        print("  (none found)")

    # Also dump flight[22] extras for first flight entry in detail
    if flight_list:
        k = flight_list[0]
        flight = k[0]
        print(f"\n--- flight[0][22] extras (first entry) ---")
        try:
            extras = flight[22]
            print(f"extras: {safe_repr(extras, 500)}")
            if isinstance(extras, list):
                for i, v in enumerate(extras):
                    print(f"  extras[{i}]: {safe_repr(v)}")
        except IndexError:
            print("  flight[22] does not exist")

        # Also check k[1] in full detail
        print(f"\n--- k[1] full detail (first entry) ---")
        try:
            k1 = k[1]
            print(f"k[1] has {len(k1)} elements")
            for i, v in enumerate(k1):
                print(f"  k[1][{i}]: {safe_repr(v, 300)}")
        except (IndexError, TypeError):
            pass
