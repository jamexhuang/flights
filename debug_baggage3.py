"""
Deep dive: compare full-service vs LCC single_flight subarrays.
Focus on sf[12], sf[13], sf[16], sf[25], sf[31], sf[32].
"""
import json
import urllib.parse
from primp import Client


def _encode(legs):
    flights_array = []
    for leg in legs:
        flights_array.append([
            [[[leg["from"], 0]]],
            [[[leg["to"], 0]]],
            None, 0, None, None, leg["date"],
            None, None, None, None, None, None, None, 3
        ])
    inner_json = [
        [],
        [None, None, 3, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None, flights_array, None, None, None, 1],
        0, 0, 0, 1
    ]
    req_str = json.dumps([None, json.dumps(inner_json, separators=(',', ':'))], separators=(',', ':'))
    return f"f.req={urllib.parse.quote(req_str)}&"


def fetch(legs):
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
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "cookie": "CONSENT=YES+cb.20230810-00-p0.en+FX+874; SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg",
    }
    body = _encode(legs).encode("utf-8")
    res = client.post(url, headers=headers, content=body)
    print(f"HTTP {res.status_code}")
    for line in res.text.split('\n'):
        s = line.strip()
        if s.startswith('[['):
            outer = json.loads(s)
            return json.loads(outer[0][2])
    return None


def safe(v, n=200):
    s = repr(v)
    return s[:n] + "..." if len(s) > n else s


if __name__ == "__main__":
    legs = [
        {"from": "TPE", "to": "NRT", "date": "2026-04-10"},
        {"from": "NRT", "to": "TPE", "date": "2026-04-17"},
    ]
    payload = fetch(legs)
    if not payload:
        print("Failed"); exit(1)

    flight_list = []
    try:
        if payload[2] and payload[2][0]:
            flight_list.extend(payload[2][0])
    except (IndexError, TypeError): pass
    try:
        if payload[3] and payload[3][0]:
            flight_list.extend(payload[3][0])
    except (IndexError, TypeError): pass

    print(f"Total: {len(flight_list)} flights\n")

    # For each flight: show sf[12] (amenities?), sf[13], sf[16], sf[25..32]
    print("=== single_flight key fields per flight ===")
    for i, k in enumerate(flight_list):
        try:
            flight = k[0]
            airline = str(flight[1])
            price = k[1][0][1]
            sf_list = flight[2]
            for leg_idx, sf in enumerate(sf_list):
                # Interesting fields to examine
                sf12 = sf[12] if len(sf) > 12 else "?"
                sf13 = sf[13] if len(sf) > 13 else "?"
                sf16 = sf[16] if len(sf) > 16 else "?"
                sf22 = sf[22] if len(sf) > 22 else "?"
                sf25 = sf[25] if len(sf) > 25 else "?"
                sf31 = sf[31] if len(sf) > 31 else "?"
                sf32 = sf[32] if len(sf) > 32 else "?"
                print(f"[{i}] {airline} ${price} leg{leg_idx}:")
                print(f"     sf[12]={safe(sf12)}  sf[13]={sf13}  sf[16]={sf16}")
                print(f"     sf[22]={safe(sf22)}")
                print(f"     sf[25]={sf25}  sf[31]={sf31}  sf[32]={sf32}")
        except Exception as e:
            print(f"[{i}] ERROR: {e}")

    # Also look at k[8] JSON decoded content for first few flights
    print("\n=== k[8] JSON content (first 5 flights) ===")
    for i, k in enumerate(flight_list[:5]):
        try:
            airline = str(k[0][1])
            price = k[1][0][1]
            k8 = k[8]
            if isinstance(k8, str):
                parsed = json.loads(k8)
                print(f"[{i}] {airline} ${price}: k[8] is JSON list with {len(parsed)} elements")
                for j, item in enumerate(parsed):
                    print(f"  k8[{j}]: {safe(item)}")
            else:
                print(f"[{i}] {airline} ${price}: k[8]={safe(k8)}")
        except Exception as e:
            print(f"[{i}] ERROR parsing k[8]: {e}")
