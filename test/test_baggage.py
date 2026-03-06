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


def fetch_raw(legs):
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

def investigate_route(route_name, legs):
    print(f"\n{'='*70}")
    print(f"Investigating Route: {route_name}")
    raw = fetch_raw(legs)
    payload = parse_payload(raw)
    if not payload:
        print("Failed to parse payload")
        return

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
    
    # We also check payload[11] which according to docs has baggage URLs
    try:
        if len(payload) > 11 and payload[11]:
            print("\nBaggage URLs from payload[11]:")
            for entry in payload[11]:
                print(f"  {entry[0]} - {entry[1]}: {entry[2]}")
    except (IndexError, TypeError):
        pass

    print("\nFormat: Price | Carrier -> Amenity array sf[12]")
    
    unique_amenities = set()

    for k in flight_list:
        try:
            flight = k[0]
            price = k[1][0][1]
            airlines = flight[1]
            # Print only first leg for simplicity
            sg_flights = flight[2]
            for sgf in sg_flights:
                sf12 = sgf[12] if len(sgf) > 12 else None
                carrier = airlines[0] if airlines else "Unknown"
                print(f"${price:<5} | {carrier:<20} -> {sf12}")
                if sf12:
                    unique_amenities.add(tuple(sf12))
        except (IndexError, TypeError, KeyError) as e:
            continue

    print("\nUnique amenity array patterns found on this route:")
    for pat in unique_amenities:
        print(pat)


if __name__ == "__main__":
    routes = [
        ("TPE -> NRT", [{"from": "TPE", "to": "NRT", "date": "2026-04-10"}]),
        ("LHR -> JFK", [{"from": "LHR", "to": "JFK", "date": "2026-05-15"}]),
        ("SIN -> KUL", [{"from": "SIN", "to": "KUL", "date": "2026-06-01"}]),
    ]

    for name, legs in routes:
        investigate_route(name, legs)
