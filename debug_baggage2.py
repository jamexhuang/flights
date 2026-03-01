"""
Targeted diagnostic: focus on k[3], k[4], k[5], k[9] and single_flight subarray.
"""
import json
import urllib.parse
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
    for line in raw.split('\n'):
        s = line.strip()
        if s.startswith('[['):
            outer = json.loads(s)
            return json.loads(outer[0][2])
    return None


def safe(v, n=150):
    s = repr(v)
    return s[:n] + "..." if len(s) > n else s


if __name__ == "__main__":
    raw = fetch_raw()
    payload = parse_payload(raw)

    # payload[11] = airline baggage URL map
    print("=== payload[11] (airline baggage URL map) ===")
    try:
        for entry in payload[11]:
            print(f"  {entry}")
    except Exception as e:
        print(f"  Error: {e}")

    # Build flight list
    flight_list = []
    try:
        if payload[2] and payload[2][0]:
            flight_list.extend(payload[2][0])
    except (IndexError, TypeError):
        pass
    try:
        if payload[3] and payload[3][0]:
            flight_list.extend(payload[3][0])
    except (IndexError, TypeError):
        pass

    print(f"\n=== All {len(flight_list)} flights — k[3], k[4], k[5], k[9] summary ===")
    print(f"{'#':<3} {'Airline':<20} {'Price':<8} {'k[3]':<10} {'k[4]':<30} {'k[5]':<25} {'k[9]':<15}")
    print("-" * 115)
    for i, k in enumerate(flight_list):
        try:
            airline = str(k[0][1])[:18]
            price = k[1][0][1]
            k3 = repr(k[3])[:8]
            k4 = repr(k[4])[:28]
            k5 = repr(k[5])[:23]
            k9 = repr(k[9])[:13]
            print(f"{i:<3} {airline:<20} {price:<8} {k3:<10} {k4:<30} {k5:<25} {k9:<15}")
        except Exception as e:
            print(f"{i:<3} ERROR: {e}")

    # Deep-dive into k[4] and k[5] for each flight
    print("\n=== k[4] full detail per flight ===")
    for i, k in enumerate(flight_list):
        try:
            airline = str(k[0][1])
            price = k[1][0][1]
            print(f"  [{i}] {airline} ${price}: k[4]={safe(k[4])}")
        except Exception as e:
            print(f"  [{i}] ERROR: {e}")

    print("\n=== k[9] full detail per flight ===")
    for i, k in enumerate(flight_list):
        try:
            airline = str(k[0][1])
            price = k[1][0][1]
            print(f"  [{i}] {airline} ${price}: k[9]={safe(k[9])}")
        except Exception as e:
            print(f"  [{i}] ERROR: {e}")

    # Deep dive: single_flight full array for first flight
    print("\n=== single_flight subarray (flight[2][0]) — first flight entry ===")
    if flight_list:
        k = flight_list[0]
        flight = k[0]
        airline = str(flight[1])
        print(f"Airline: {airline}  Price: ${k[1][0][1]}")
        try:
            sf = flight[2][0]  # first leg
            print(f"single_flight has {len(sf)} elements:")
            for j, v in enumerate(sf):
                print(f"  sf[{j}]: {safe(v)}")
        except Exception as e:
            print(f"  Error: {e}")

    # Compare extras[2], extras[3], extras[12] across full-service vs LCC
    print("\n=== flight[22] extras summary per flight ===")
    print(f"{'#':<3} {'Airline':<20} {'Price':<8} {'ex[2]':<8} {'ex[3]':<8} {'ex[9]':<15} {'ex[11]':<8} {'ex[12]':<8}")
    print("-" * 80)
    for i, k in enumerate(flight_list):
        try:
            flight = k[0]
            airline = str(flight[1])[:18]
            price = k[1][0][1]
            extras = flight[22]
            ex2 = repr(extras[2]) if extras and len(extras) > 2 else "?"
            ex3 = repr(extras[3]) if extras and len(extras) > 3 else "?"
            ex9 = repr(extras[9]) if extras and len(extras) > 9 else "?"
            ex11 = repr(extras[11]) if extras and len(extras) > 11 else "?"
            ex12 = repr(extras[12]) if extras and len(extras) > 12 else "?"
            print(f"{i:<3} {airline:<20} {price:<8} {ex2:<8} {ex3:<8} {ex9:<15} {ex11:<8} {ex12:<8}")
        except Exception as e:
            print(f"{i:<3} ERROR: {e}")
