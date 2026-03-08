import json
import re
import urllib.parse
from typing import TYPE_CHECKING

from primp import Client, ConnectError, Timeout

from .querying import FlightQuery
from .parser import MetaList

DEFAULT_RPC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)

def _encode_shopping_request(legs: list[FlightQuery], tokens: list[str], seat_val: int = 1) -> str:
    flights_array = []
    for leg in legs:
        date_str = leg.date if isinstance(leg.date, str) else leg.date.strftime("%Y-%m-%d")
        flights_array.append([
            [[[leg.from_airport, 0]]],
            [[[leg.to_airport, 0]]],
            None, 0, None, None,
            date_str,
            None, None, None, None, None, None, None, 3
        ])
    
    tokens_arr = []
    if len(tokens) > 0:
        token_entry = [None, None, None, tokens[0]]
        for t in tokens[1:]:
             token_entry.append(t)
        tokens_arr = [token_entry]
        
    inner_json = [
        tokens_arr,
        [None, None, 3, None, [], seat_val, [1, 0, 0, 0], None, None, None, None, None, None, flights_array, None, None, None, 1],
        0, 0, 0, 1
    ]
    
    req_str = json.dumps([None, json.dumps(inner_json, separators=(',', ':'))], separators=(',', ':'))
    return f"f.req={urllib.parse.quote(req_str)}&"

def _extract_flight_tokens(raw_response_text: str) -> list[str]:
    matches = re.findall(r'\\"([^"]*?--+[^"]*?AAAAA[^"]*?)\\"', raw_response_text)
    matches.extend(re.findall(r'"([^"]*?--+[^"]*?AAAAA[^"]*?)"', raw_response_text))
    matches.extend(re.findall(r'\\"([^"]*?==)\\"', raw_response_text))
    matches.extend(re.findall(r'"([^"]*?==)"', raw_response_text))
    matches.extend(re.findall(r'\\"(HczU[^"]*?)\\"', raw_response_text))
    matches.extend(re.findall(r'\\"([a-zA-Z0-9_\-]{80,})\\"', raw_response_text))
    matches.extend(re.findall(r'\\"([a-zA-Z0-9_\-]{60,150})\\"', raw_response_text))

    found_tokens = []
    for m in matches:
        if len(m) > 50 and "http" not in m and "www." not in m:
            found_tokens.append(m)
            
    unique = list(dict.fromkeys(found_tokens))
    unique.sort(key=lambda x: ("----" in x or "AAAA" in x), reverse=True)
    return unique

def _extract_full_flights_list(raw_response_text: str) -> 'MetaList | None':
    """
    Extract flight data from the GetShoppingResults RPC response.
    
    The response format is:
      )]}'\n\nSIZE\n[["wrb.fr",null,"ESCAPED_JSON_STRING"]]\n...
    
    We parse the outer JSON, extract the inner string, decode it,
    then feed the resulting array directly into the flight parser.
    """
    try:
        # Strip the XSSI protection prefix and find the first JSON array
        lines = raw_response_text.split('\n')
        outer_json_str = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('[['):
                outer_json_str = stripped
                break
        
        if not outer_json_str:
            return None
        
        # Parse the outer array: [["wrb.fr", null, "INNER_JSON_STRING"]]
        outer = json.loads(outer_json_str)
        
        # The inner JSON string is at outer[0][2]
        if not outer or not outer[0] or len(outer[0]) < 3 or not isinstance(outer[0][2], str):
            return None
        
        inner_json_str = outer[0][2]
        
        # Parse the inner JSON to get the flight data array
        payload = json.loads(inner_json_str)
        
        # Build flights directly from the payload using the same logic as parse_js
        # but without the HTML script tag format assumption
        from .model import (
            Airline, Airport, Alliance, CarbonEmission,
            Flights, JsMetadata, SimpleDatetime, SingleFlight,
        )
        
        alliances = []
        airlines_meta = []
        try:
            (alliances_data, airlines_data) = (payload[7][1][0], payload[7][1][1])
            for code, name in alliances_data:
                alliances.append(Alliance(code=code, name=name))
            for code, name in airlines_data:
                airlines_meta.append(Airline(code=code, name=name))
        except (IndexError, TypeError, KeyError):
            pass

        meta = JsMetadata(alliances=alliances, airlines=airlines_meta)

        # Build name→code lookup from metadata for airline_code resolution
        _airline_name_to_code: dict[str, str] = {}
        for a in airlines_meta:
            if a.name and a.code:
                _airline_name_to_code[a.name] = a.code

        flights = MetaList()

        flight_list = []
        
        # 1. Grab "Top Flights" (payload[2][0]) if available (often used for highly optimized multi-city bundles)
        if len(payload) > 2 and payload[2] is not None and len(payload[2]) > 0 and payload[2][0] is not None:
            flight_list.extend(payload[2][0])
            
        # 2. Grab standard flights (payload[3][0]) 
        if payload[3] is not None and payload[3][0] is not None:
            flight_list.extend(payload[3][0])
            
        if not flight_list:
            flights.metadata = meta
            return flights

        for k in flight_list:
            try:
                flight = k[0]
                price = k[1][0][1]

                select_token = None
                try:
                    if k[1] and len(k[1]) > 1 and isinstance(k[1][1], str):
                        select_token = k[1][1]
                except (IndexError, TypeError):
                    pass

                select_data = None
                try:
                    if len(k) > 8 and isinstance(k[8], str):
                        select_data = k[8]
                except (IndexError, TypeError):
                    pass

                typ = flight[0]
                flight_airlines = flight[1]

                # Resolve airline IATA code from metadata
                _resolved_code = ""
                if isinstance(flight_airlines, list):
                    for name in flight_airlines:
                        code = _airline_name_to_code.get(name, "")
                        if code:
                            _resolved_code = code
                            break

                sg_flights = []

                for single_flight in flight[2]:
                    from_airport = Airport(code=single_flight[3], name=single_flight[4])
                    to_airport = Airport(code=single_flight[6], name=single_flight[5])
                    departure_time = single_flight[8]
                    departure_date = single_flight[20]
                    departure = SimpleDatetime(date=departure_date, time=departure_time)
                    arrival_time = single_flight[10]
                    arrival_date = single_flight[21]
                    arrival = SimpleDatetime(date=arrival_date, time=arrival_time)
                    plane_type = single_flight[17]
                    duration = single_flight[11]
                    sg_flights.append(SingleFlight(
                        from_airport=from_airport, to_airport=to_airport,
                        departure=departure, arrival=arrival,
                        duration=duration, plane_type=plane_type,
                        airline_code=_resolved_code,
                    ))

                carbon_emission = None
                typical_carbon_emission = None
                try:
                    extras = flight[22]
                    carbon_emission = extras[7]
                    typical_carbon_emission = extras[8]
                except (IndexError, TypeError):
                    pass

                flights.append(Flights(
                    type=typ, price=price, airlines=flight_airlines,
                    flights=sg_flights,
                    carbon=CarbonEmission(typical_on_route=typical_carbon_emission, emission=carbon_emission),
                    select_token=select_token, select_data=select_data,
                ))
            except (IndexError, TypeError, KeyError):
                continue

        flights.metadata = meta
        return flights
    except Exception:
        return None

def fetch_shopping_results(
    client: Client,
    legs: list[FlightQuery],
    tokens: list[str],
    language: str = "en-US",
    currency: str = "USD",
    seat: str = "economy",
    max_retries: int = 3,
) -> tuple[list[str], int | None, str, 'MetaList | None']:
    """
    Submits a multicity booking selection request to GetShoppingResults.
    Returns: (list of available selection tokens, price_if_found, raw_response_text, flights_if_found)

    Retries up to ``max_retries`` times when the request times out or flight
    parsing returns no results (Google occasionally returns a session-init
    response instead of flight data).

    On the first attempt, a lightweight GET warmup is sent to
    ``/travel/flights`` to establish cookies that Google expects before
    serving RPC data (especially for premium cabin classes).
    """
    import time as _time

    url = (
        "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
        f".FlightsFrontendService/GetShoppingResults"
        f"?f.sid=6697578230526900010&bl=boq_travel-frontend-flights-ui_20260303.06_p0"
        f"&hl={language}&gl=US&curr={currency}&soc-app=162&soc-platform=1&soc-device=1&rt=c"
    )
    # Build the language/currency metadata header that Google's frontend sends
    _lang_code = language if language else "en-US"
    _curr_code = currency if currency else "USD"
    headers = {
        "accept": "*/*",
        "accept-language": _lang_code,
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": DEFAULT_RPC_USER_AGENT,
        "origin": "https://www.google.com",
        "referer": "https://www.google.com/travel/flights",
        "x-goog-ext-259736195-jspb": f'["{_lang_code}","IE","{_curr_code}",1,null,[0],null,null,1,[]]',
        "cookie": (
            "CONSENT=YES+cb.20230810-00-p0.en+FX+874; "
            "SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg"
        ),
    }
    
    from .querying import SEAT_LOOKUP
    try:
        seat_val = SEAT_LOOKUP.get(seat.lower(), 1)
    except AttributeError:
        seat_val = 1

    # Session warmup: visit Google Flights to set cookies before the RPC call
    try:
        client.get(
            "https://www.google.com/travel/flights",
            headers={
                "user-agent": DEFAULT_RPC_USER_AGENT,
                "accept-language": _lang_code,
                "cookie": headers["cookie"],
            },
        )
    except Exception:
        pass  # Warmup failure is non-fatal

    body = _encode_shopping_request(legs, tokens, seat_val).encode("utf-8")
    tokens_found: list[str] = []
    content = ""
    flights_found = None

    for attempt in range(1 + max_retries):
        if attempt > 0:
            # Progressive backoff: 2s, 3s, 4.5s, ...
            _time.sleep(2.0 * (1.5 ** (attempt - 1)))

        try:
            res = client.post(url, headers=headers, content=body)
        except (Timeout, ConnectError):
            if attempt >= max_retries:
                raise
            continue

        if res.status_code != 200:
            return [], None, "", None

        content = res.text
        tokens_found = _extract_flight_tokens(content)
        flights_found = _extract_full_flights_list(content)

        if flights_found is not None and len(flights_found) > 0:
            price_found = flights_found[0].price
            return tokens_found, price_found, content, flights_found

    # All attempts exhausted — return whatever we have (tokens still useful for chaining)
    return tokens_found, None, content, flights_found
