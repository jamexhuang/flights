import json
import logging
import re
import urllib.parse
from typing import TYPE_CHECKING

from primp import Client

from .querying import FlightQuery, SelectedSegment
from .parser import MetaList, parse_payload
from .shopping_options import ShoppingOptions
from .model import ResponseDiagnostics

logger = logging.getLogger("fast_flights")

DEFAULT_RPC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)
DEFAULT_RPC_F_SID = "6697578230526900010"
DEFAULT_RPC_BL = "boq_travel-frontend-flights-ui_20260303.06_p0"

def _encode_shopping_request(
    legs: list[FlightQuery],
    tokens: list[str],
    seat_val: int = 1,
    shopping: ShoppingOptions | None = None,
    selected_legs: tuple[tuple[SelectedSegment, ...], ...] | None = None,
    passenger_counts: tuple[int, int, int, int] = (1, 0, 0, 0),
) -> str:
    exact_selection = bool(selected_legs and any(selected_legs))
    flights_array = []
    for idx, leg in enumerate(legs):
        date_str = leg.date if isinstance(leg.date, str) else leg.date.strftime("%Y-%m-%d")
        selected_segments = None
        if selected_legs and idx < len(selected_legs) and selected_legs[idx]:
            selected_segments = [
                [
                    segment.from_airport,
                    segment.departure_date,
                    segment.to_airport,
                    None,
                    segment.airline_code,
                    segment.flight_number,
                ]
                for segment in selected_legs[idx]
            ]
        flights_array.append([
            [[[leg.from_airport, 0]]],
            [[[leg.to_airport, 0]]],
            None, 0, None, None,
            date_str,
            None,
            selected_segments,
            None,
            None,
            None,
            None,
            None,
            3,
        ])

    tokens_arr: list | list[list] = []
    if exact_selection and len(tokens) > 0:
        tokens_arr = [None, *tokens]
    elif len(tokens) > 0:
        token_entry = [None, None, None, tokens[0]]
        for t in tokens[1:]:
             token_entry.append(t)
        tokens_arr = [token_entry]
        
    shopping = shopping or ShoppingOptions()

    inner_json = [
        tokens_arr,
        [None, None, 3, None, [], seat_val, list(passenger_counts), None, None, None, None, None, None, flights_array, None, None, None, 1],
        shopping.sort_id, 0, 0, shopping.ranking_id
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

def _extract_full_flights_list(
    raw_response_text: str,
    *,
    shopping: ShoppingOptions | None = None,
    source: str | None = None,
) -> 'MetaList | None':
    """
    Extract flight data from the GetShoppingResults RPC response.
    
    The response format is:
      )]}'\n\nSIZE\n[["wrb.fr",null,"ESCAPED_JSON_STRING"]]\n...
    
    We parse the outer JSON, extract the inner string, decode it,
    then feed the resulting array directly into the flight parser.
    """
    try:
        lines = raw_response_text.split('\n')
        outer_json_str = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('[['):
                outer_json_str = stripped
                break

        if not outer_json_str:
            return None

        outer = json.loads(outer_json_str)
        if not outer or not outer[0] or len(outer[0]) < 3 or not isinstance(outer[0][2], str):
            return None

        payload = json.loads(outer[0][2])
        return parse_payload(payload, include_top_results=True, shopping=shopping, source=source)
    except Exception:
        logger.debug("shopping: extract_full_flights_list failed", exc_info=True)
        return None


def _shopping_rpc_url(
    *,
    language: str,
    currency: str,
    f_sid: str | None = None,
    bl: str | None = None,
) -> str:
    return (
        "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights"
        ".FlightsFrontendService/GetShoppingResults"
        f"?f.sid={f_sid or DEFAULT_RPC_F_SID}"
        f"&bl={bl or DEFAULT_RPC_BL}"
        f"&hl={language}&gl=US&curr={currency}&soc-app=162&soc-platform=1&soc-device=1&rt=c"
    )


def _shopping_rpc_headers(*, language: str, currency: str, referer: str = "https://www.google.com/travel/flights") -> dict[str, str]:
    return {
        "accept": "*/*",
        "accept-language": language,
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": DEFAULT_RPC_USER_AGENT,
        "origin": "https://www.google.com",
        "referer": referer,
        "x-goog-ext-259736195-jspb": f'["{language}","IE","{currency}",1,null,[0],null,null,1,[]]',
        "cookie": (
            "CONSENT=YES+cb.20230810-00-p0.en+FX+874; "
            "SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg"
        ),
    }


def _warmup_shopping_session(client: Client, *, language: str, cookie_header: str) -> None:
    try:
        client.get(
            "https://www.google.com/travel/flights",
            headers={
                "user-agent": DEFAULT_RPC_USER_AGENT,
                "accept-language": language,
                "cookie": cookie_header,
            },
        )
    except Exception:
        logger.debug("shopping: warmup GET failed", exc_info=True)

def fetch_shopping_results(
    client: Client,
    legs: list[FlightQuery],
    tokens: list[str],
    shopping: ShoppingOptions | None = None,
    selected_legs: tuple[tuple[SelectedSegment, ...], ...] | None = None,
    language: str = "en-US",
    currency: str = "USD",
    seat: str = "economy",
    passenger_counts: tuple[int, int, int, int] = (1, 0, 0, 0),
    max_retries: int = 3,
    f_sid: str | None = None,
    bl: str | None = None,
    referer: str = "https://www.google.com/travel/flights",
) -> tuple[list[str], int | None, str, 'MetaList']:
    """
    Submits a multicity booking selection request to GetShoppingResults.
    Returns: (list of available selection tokens, price_if_found, raw_response_text, flights_found)
    ``flights_found`` is always a MetaList (empty or populated), carrying a
    ``.diagnostics`` (ResponseDiagnostics) describing the outcome of the call.

    Retries up to ``max_retries`` times when the request times out or flight
    parsing returns no results (Google occasionally returns a session-init
    response instead of flight data).

    On the first attempt, a lightweight GET warmup is sent to
    ``/travel/flights`` to establish cookies that Google expects before
    serving RPC data (especially for premium cabin classes).
    """
    import time as _time
    from time import perf_counter as _pc
    _t0 = _pc()
    _lang_code = language if language else "en-US"
    _curr_code = currency if currency else "USD"
    url = _shopping_rpc_url(language=_lang_code, currency=_curr_code, f_sid=f_sid, bl=bl)
    headers = _shopping_rpc_headers(language=_lang_code, currency=_curr_code, referer=referer)
    
    from .querying import SEAT_LOOKUP
    try:
        seat_val = SEAT_LOOKUP.get(seat.lower(), 1)
    except AttributeError:
        seat_val = 1

    _warmup_shopping_session(client, language=_lang_code, cookie_header=headers["cookie"])

    body = _encode_shopping_request(
        legs,
        tokens,
        seat_val,
        shopping=shopping,
        selected_legs=selected_legs,
        passenger_counts=passenger_counts,
    ).encode("utf-8")
    tokens_found: list[str] = []
    content = ""
    flights_found: "MetaList | None" = None
    used_defaults = f_sid is None and bl is None
    http_status: int | None = None
    attempts_made = 0

    def _empty(status: str) -> MetaList:
        m = MetaList()
        m.diagnostics = ResponseDiagnostics(
            status=status, http_status=http_status,
            elapsed_ms=round((_pc() - _t0) * 1000, 1),
            attempts=attempts_made, used_default_rpc_params=used_defaults,
        )
        return m

    for attempt in range(1 + max_retries):
        if attempt > 0:
            # Progressive backoff: 2s, 3s, 4.5s, ...
            _time.sleep(2.0 * (1.5 ** (attempt - 1)))
        attempts_made = attempt + 1

        try:
            res = client.post(url, headers=headers, content=body)
        except Exception:
            logger.debug("shopping: RPC POST attempt failed", exc_info=True)
            if attempt >= max_retries:
                raise
            continue

        http_status = res.status_code
        if res.status_code != 200:
            status = "blocked" if res.status_code in (403, 429) else "http_error"
            return [], None, "", _empty(status)

        content = res.text
        tokens_found = _extract_flight_tokens(content)
        flights_found = _extract_full_flights_list(content, shopping=shopping, source="rpc")

        if flights_found is not None and len(flights_found) > 0:
            flights_found.diagnostics = ResponseDiagnostics(
                status="ok", http_status=200,
                elapsed_ms=round((_pc() - _t0) * 1000, 1),
                attempts=attempts_made, used_default_rpc_params=used_defaults,
            )
            price_found = flights_found[0].price
            return tokens_found, price_found, content, flights_found

    # Exhausted with 200s but no results → empty (soft-block-shaped)
    return tokens_found, None, content, _empty("empty")
