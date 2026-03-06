import json
import urllib.parse
from primp import Client

def _encode_shopping_request(legs):
    flights_array = []
    for leg in legs:
        flights_array.append([
            [[[leg["from"], 0]]],
            [[[leg["to"], 0]]],
            None, 0, None, None,
            leg["date"],
            None, None, None, None, None, None, None, 3
        ])

    inner_json = [
        [],
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
        )
    }
    body = _encode_shopping_request(legs).encode("utf-8")
    res = client.post(url, headers=headers, content=body)
    return res.text

def parse_payload(raw):
    for line in raw.split('\n'):
        if line.strip().startswith('[['):
            outer = json.loads(line.strip())
            return json.loads(outer[0][2])
    return None

def main():
    routes = [
        ("TPE -> NRT", [{"from": "TPE", "to": "NRT", "date": "2026-08-15"}]),
        ("TPE -> LHR", [{"from": "TPE", "to": "LHR", "date": "2026-08-15"}]),
        ("MAN -> JFK", [{"from": "MAN", "to": "JFK", "date": "2026-08-15"}]),
    ]

    for name, legs in routes:
        print(f"\n================ {name} ================")
        raw = fetch_raw(legs)
        payload = parse_payload(raw)
        if not payload:
            print("Failed to parse.")
            continue
            
        flight_list = []
        if payload[2] and payload[2][0]: flight_list.extend(payload[2][0])
        if payload[3] and payload[3][0]: flight_list.extend(payload[3][0])

        count = 0
        for k in flight_list:
            if count >= 3: break # just print top 3 to keep it concise
            try:
                flight = k[0]
                price = k[1][0][1]
                airlines = flight[1]
                sg_flights = flight[2]
                
                print(f"\nPrice: ${price}")
                for idx, sgf in enumerate(sg_flights):
                    carrier = airlines[0] if airlines else "Unknown"
                    dep_time = sgf[8]
                    arr_time = sgf[10]
                    flight_num = sgf[1] if len(sgf)>1 else 'N/A'
                    sf12 = sgf[12] if len(sgf) > 12 else None
                    print(f" Leg {idx+1}: {carrier} {flight_num} | Dep: {dep_time} | Arr: {arr_time}")
                    print(f"     -> sf[12]: {sf12}")
                count += 1
            except Exception as e:
                pass

if __name__ == "__main__":
    main()
