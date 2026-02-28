import urllib.parse
import json
import re
from typing import TYPE_CHECKING
from primp import Client
from .querying import FlightQuery
from .parser import parse_js

if TYPE_CHECKING:
    from .parser import MetaList

def _encode_shopping_request(legs: list[FlightQuery], tokens: list[str]) -> str:
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
        [None, None, 3, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None, flights_array, None, None, None, 1],
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
    chunks = raw_response_text.split('wrb.fr",null,"')
    if len(chunks) < 2:
        return None
        
    main_chunk = chunks[1].split('"]')[0]
    # Re-wrap in quotes and use json.loads to resolve inner escaped quotes
    try:
        unquoted = json.loads('"' + main_chunk + '"')
        # We simulate the \"data: {json}\" format parser_js expects
        simulated_js_str = "data:" + unquoted
        flights = parse_js(simulated_js_str)
        return flights
    except Exception:
        return None

def fetch_shopping_results(
    client: Client,
    legs: list[FlightQuery],
    tokens: list[str],
    language: str = "en-US",
    currency: str = "USD"
) -> tuple[list[str], int | None, str, 'MetaList | None']:
    """
    Submits a chained multicity booking selection request to GetShoppingResults.
    Returns: (list of available selection tokens, price_if_found, raw_response_text, detailed_flights_if_found)
    """
    url = f"https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetShoppingResults?f.sid=-5642963406499784770&bl=boq_travel-frontend-flights-ui_20260225.02_p0&hl={language}&gl=US&curr={currency}&soc-app=162&soc-platform=1&soc-device=1&rt=c"
    headers = {
        "accept": "*/*",
        "accept-language": language,
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    
    res = client.post(url, headers=headers, content=_encode_shopping_request(legs, tokens).encode('utf-8'))
    if res.status_code != 200:
        return [], None, "", None
        
    content = res.text
    tokens_found = _extract_flight_tokens(content)
    flights_found = _extract_full_flights_list(content)
    
    price_found = None
    if flights_found and len(flights_found) > 0:
        price_found = flights_found[0].price
    
    return tokens_found, price_found, content, flights_found
