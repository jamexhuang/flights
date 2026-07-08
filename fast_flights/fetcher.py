from __future__ import annotations

import json
from dataclasses import dataclass
from typing import overload, TYPE_CHECKING

from primp import Client

from .integrations.base import Integration
from .parser import MetaList, parse
from .querying import Query, ReturnQuery, build_booking_tfs
from .shopping_options import ShoppingOptions
from .shopping import fetch_shopping_results

if TYPE_CHECKING:
    from collections.abc import Callable
    from .model import Flights
    from .querying import FlightQuery, Passengers
    from .types import SeatType

URL = "https://www.google.com/travel/flights"
DEFAULT_IMPERSONATE = "chrome_145"
DEFAULT_IMPERSONATE_OS = "macos"
DEFAULT_CLIENT_TIMEOUT = 15.0


def _build_default_client(*, proxy: str | None = None) -> Client:
    return Client(
        impersonate=DEFAULT_IMPERSONATE,
        impersonate_os=DEFAULT_IMPERSONATE_OS,
        referer=True,
        proxy=proxy,
        cookie_store=True,
        timeout=DEFAULT_CLIENT_TIMEOUT,
    )


@overload
def get_flights(q: str, /, *, proxy: str | None = None, shopping: ShoppingOptions | None = None) -> MetaList:
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: Query, /, *, proxy: str | None = None, shopping: ShoppingOptions | None = None) -> MetaList:
    """Get flights using a structured query.

    Example:
    ```python
    get_flights(
        query(
            flights=[
                FlightQuery(
                    date="2025-12-22",
                    from_airport="TPE",
                    to_airport="MYJ",
                )
            ],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="",
        )
    )
    ```
    """


def get_flights(
    q: Query | ReturnQuery | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
    shopping: ShoppingOptions | None = None,
) -> MetaList:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
        integration (Integration | None, optional): You can use Playwright or your own fetching config.
    """
    if isinstance(q, str):
        q = Query.from_url(q)

    # For multi-city and explicit shopping sort requests, the initial HTML
    # does not preserve the RPC ordering/metadata we want to expose.
    # q.trip == 3 corresponds to multi-city in TRIP_LOOKUP
    if isinstance(q, Query) and (q.trip == 3 or shopping is not None):
        client = _build_default_client(proxy=proxy)
        if not q._flights:
            raise ValueError("Multi-city search requires flight models. Pass FlightQuery legs into create_query.")

        # Reverse-lookup seat string from protobuf enum value
        from .querying import SEAT_LOOKUP
        seat_str = "economy"
        for name, val in SEAT_LOOKUP.items():
            if val == q.seat:
                seat_str = name
                break

        p = _query_passengers(q)
        _, _, _, flights_found = fetch_shopping_results(
            client=client,
            legs=q._flights,
            tokens=[],
            shopping=shopping,
            language=q.language if q.language else "en-US",
            currency=q.currency if q.currency else "USD",
            seat=seat_str,
            passenger_counts=(p.adults, p.children, p.infants_in_seat, p.infants_on_lap),
        )
        # return empty list if none to maintain compatibility
        return flights_found if flights_found is not None else MetaList()

    from time import perf_counter as _pc
    from .model import ResponseDiagnostics
    _t0 = _pc()
    html = fetch_flights_html(q, proxy=proxy, integration=integration)
    result = parse(html)
    result.diagnostics = ResponseDiagnostics(
        status="ok" if len(result) > 0 else "empty",
        http_status=200,
        elapsed_ms=round((_pc() - _t0) * 1000, 1),
    )
    return result


def get_return_flights(
    q: ReturnQuery,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
    shopping: ShoppingOptions | None = None,
) -> MetaList:
    """Get return flights after selecting an outbound flight.

    Use :func:`~fast_flights.querying.select_flight` to build a
    :class:`ReturnQuery` from the original query and a chosen outbound
    flight, then pass it here to retrieve the available return options.

    Args:
        q: A :class:`ReturnQuery` created by :func:`select_flight`.
        proxy (str, optional): Proxy.
    """
    expected_leg = _get_expected_return_leg(q)
    if expected_leg is None:
        return parse(fetch_flights_html(q, proxy=proxy, integration=integration))

    selected_results = _get_selected_html_results(
        q,
        expected_leg,
        proxy=proxy,
        integration=integration,
    )
    if selected_results is not None:
        return selected_results

    bundled_results = None
    if integration is None and shopping is None:
        bundled_results = _get_bundled_leg_results(q, proxy=proxy)
        if bundled_results is not None:
            return bundled_results

    if shopping is not None:
        expected_leg = _get_expected_return_leg(q)
        if expected_leg is None:
            raise ValueError("ReturnQuery is missing the expected next leg.")
        if not q.base._flights:
            raise ValueError("ReturnQuery base query is missing flight models.")
        client = _build_default_client(proxy=proxy)
        p = _query_passengers(q.base)
        _, _, _, flights_found = fetch_shopping_results(
            client=client,
            legs=q.base._flights,
            tokens=list(q.selection_tokens),
            shopping=shopping,
            selected_legs=q.selected_legs,
            language=q.base.language if q.base.language else "en-US",
            currency=q.base.currency if q.base.currency else "USD",
            seat=_query_seat_name(q.base),
            passenger_counts=(p.adults, p.children, p.infants_in_seat, p.infants_on_lap),
            referer=q.url(),
        )
        if flights_found and _results_match_leg(flights_found, expected_leg):
            return flights_found
        raise ValueError("Could not fetch exact shopping results for the requested return leg.")

    # Google's selected-flight HTML no longer reliably SSRs the reverse leg,
    # but replaying the browser-style selected ``tfs`` can also fail if the
    # selected itinerary metadata is incomplete. Fall back to an independent
    # one-way query so the returned segment data still matches the requested
    # direction.
    return _get_directional_leg_results(
        q.base,
        q.next_leg_index,
        proxy=proxy,
        integration=integration,
    )


def _get_selected_html_results(
    q: ReturnQuery,
    expected_leg: "FlightQuery",
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> MetaList | None:
    try:
        parsed = parse(fetch_flights_html(q, proxy=proxy, integration=integration))
    except Exception:
        return None

    if _results_match_leg(parsed, expected_leg):
        return parsed
    return None


def _get_bundled_leg_results(
    q: ReturnQuery,
    *,
    proxy: str | None = None,
) -> MetaList | None:
    expected_leg = _get_expected_return_leg(q)
    if expected_leg is None:
        return None
    if q.next_leg_index != 1:
        return None
    if not q.base._flights or not q.selection_tokens or not q.selected_legs:
        return None
    selected_segments = q.selected_legs[0]
    if not selected_segments:
        return None

    selected_tfs = build_booking_tfs(q.base, q.selected_legs)
    if not selected_tfs:
        return None

    try:
        client = _build_default_client(proxy=proxy)
        res = client.get(
            URL,
            params={
                "tfs": selected_tfs,
                "hl": q.base.language,
                "curr": q.base.currency,
            },
            headers={
                "cookie": "CONSENT=YES+cb.20230810-00-p0.en+FX+874; SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg"
            },
        )
        if res.status_code != 200:
            return None
        flights_found = parse(res.text)
    except Exception:
        return None

    if flights_found and _results_match_leg(flights_found, expected_leg):
        return flights_found

    return None


def fetch_flights_html(
    q: Query | ReturnQuery | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> str:
    """Fetch flights and get the **HTML**.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    if integration is None:
        client = _build_default_client(proxy=proxy)

        if isinstance(q, (Query, ReturnQuery)):
            params = q.params()

        else:
            params = {"q": q}

        res = client.get(
            URL,
            params=params,
            headers={
                "cookie": "CONSENT=YES+cb.20230810-00-p0.en+FX+874; SOCS=CAISHAgCEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LyaBg"
            }
        )
        if res.status_code != 200:
            raise RuntimeError(
                f"Google Flights returned HTTP {res.status_code}. "
                "The request may have been blocked or rate-limited."
            )
        return res.text

    else:
        return integration.fetch_html(q)


# ── Multi-city convenience ──────────────────────────────────────────────


@dataclass
class MulticityLeg:
    """Results for one leg of a multi-city search.

    Attributes:
        leg_index: 0-based leg index.
        from_airport: IATA code of origin airport for this leg.
        to_airport: IATA code of destination airport for this leg.
        date: Departure date string.
        results: The parsed flight results for this leg.
    """

    leg_index: int
    from_airport: str
    to_airport: str
    date: str
    results: MetaList


def get_flights_multicity(
    flights: "list[FlightQuery]",
    *,
    seat: "SeatType" = "economy",
    passengers: "Passengers" = None,
    language: str = "",
    currency: str = "",
    proxy: str | None = None,
    integration: Integration | None = None,
    delay: float = 1.0,
) -> list[MulticityLeg]:
    """Search a multi-city itinerary using independent one-way queries.

    Google Flights does not server-side render multi-city or return-flight
    results, so neither ``trip="multi-city"`` nor the ``tfu``-based
    chaining approach works via the default primp (HTTP-only) client.

    This function works around the limitation by running **one independent
    one-way query per leg**, which Google *does* server-side render.

    .. note::

       Because each leg is an independent one-way query, the prices shown
       are **per-leg one-way prices**, not the bundled "entire trip" price
       that Google shows in a multi-city search.  Sum the per-leg cheapest
       prices for an approximate total.

    Args:
        flights: List of :class:`FlightQuery`, one per leg (2–10 legs).
        seat: Seat class.
        passengers: Passenger counts.  Defaults to 1 adult.
        language: Language code (e.g. ``"en"``).
        currency: Currency code (e.g. ``"EUR"``).
        proxy: Optional proxy string.
        integration: Optional :class:`Integration` for the HTTP fetch.
        delay: Seconds to wait between fetches (default 1.0).

    Returns:
        A list of :class:`MulticityLeg`, one per leg.
        Each contains the available flights for that leg.

    Example::

        legs = get_flights_multicity(
            flights=[
                FlightQuery(date="2026-03-15", from_airport="SIN", to_airport="TPE"),
                FlightQuery(date="2026-03-21", from_airport="TPE", to_airport="NRT"),
                FlightQuery(date="2026-03-24", from_airport="NRT", to_airport="TPE"),
                FlightQuery(date="2026-03-27", from_airport="TPE", to_airport="SIN"),
            ],
            seat="economy",
            language="en",
            currency="EUR",
        )
        for leg in legs:
            print(f"Leg {leg.leg_index}: {leg.from_airport}→{leg.to_airport}")
            for f in leg.results[:3]:
                print(f"  €{f.price}")
    """
    import time as _time

    from .querying import (
        Passengers as _P,
        create_query as _cq,
    )

    if passengers is None:
        passengers = _P(adults=1)

    if len(flights) < 2:
        raise ValueError("Multi-city requires at least 2 legs")

    all_legs: list[MulticityLeg] = []

    for i, fq in enumerate(flights):
        if i > 0 and delay > 0:
            _time.sleep(delay)

        query = _cq(
            flights=[fq],
            trip="one-way",
            seat=seat,
            passengers=passengers,
            language=language,
            currency=currency,
        )
        results = get_flights(query, proxy=proxy, integration=integration)
        leg = MulticityLeg(
            leg_index=i,
            from_airport=fq.from_airport,
            to_airport=fq.to_airport,
            date=fq.date if isinstance(fq.date, str) else fq.date.strftime("%Y-%m-%d"),
            results=results,
        )
        all_legs.append(leg)

    return all_legs


@dataclass
class MulticityLegChained:
    """Results for one leg of a multi-city chained search.
    
    Attributes:
        leg_index: 0-based leg index.
        from_airport: IATA code of origin airport for this leg.
        to_airport: IATA code of destination airport for this leg.
        date: Departure date string.
        tokens: The available flight selection tokens found.
        total_price: The accumulated ticket overall price found on this leg (usually on the final leg).
    """

    leg_index: int
    from_airport: str
    to_airport: str
    date: str
    tokens: list[str]
    total_price: int | None
    flights: MetaList | None


@dataclass
class GoogleFlightsDataServiceRequest:
    """Client-side data service request embedded in a selected Google Flights page."""

    key: str
    rpc_id: str
    request: list


@dataclass
class SelectedFlightPage:
    """Google Flights page state after selecting a flight.

    Attributes:
        return_query: Query wrapper containing the selected-flight ``tfu`` token.
        url: Direct Google Flights URL for the selected page.
        f_sid: Request session identifier extracted from ``window.WIZ_global_data``.
        bl: Frontend build label extracted from ``window.WIZ_global_data``.
        data_service_requests: Client-side RPC requests keyed by ``ds:*`` name.
    """

    return_query: ReturnQuery
    url: str
    f_sid: str | None
    bl: str | None
    data_service_requests: dict[str, GoogleFlightsDataServiceRequest]


def _extract_wiz_global_value(html: str, key: str) -> str | None:
    marker = f'"{key}":"'
    start = html.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = start
    while end < len(html):
        ch = html[end]
        if ch == '"' and html[end - 1] != "\\":
            break
        end += 1
    if end >= len(html):
        return None
    return json.loads(f'"{html[start:end]}"')


def _extract_balanced_list(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "[":
        raise ValueError("Expected list start '['")

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1], idx + 1

    raise ValueError("Unterminated list in data service request")


def _extract_data_service_requests(html: str) -> dict[str, GoogleFlightsDataServiceRequest]:
    """Extract client-side AF_dataService request payloads from a Google Flights page."""
    marker = "var AF_dataServiceRequests = {"
    start = html.find(marker)
    if start == -1:
        return {}

    requests_block = html[start + len(marker) :]
    requests: dict[str, GoogleFlightsDataServiceRequest] = {}
    cursor = 0
    while True:
        key_start = requests_block.find("'ds:", cursor)
        if key_start == -1:
            break

        key_end = requests_block.find("'", key_start + 1)
        if key_end == -1:
            break
        key = requests_block[key_start + 1 : key_end]

        id_marker = "{id:'"
        id_start = requests_block.find(id_marker, key_end)
        if id_start == -1:
            break
        id_start += len(id_marker)
        id_end = requests_block.find("'", id_start)
        if id_end == -1:
            break
        rpc_id = requests_block[id_start:id_end]

        request_marker = "request:"
        request_start = requests_block.find(request_marker, id_end)
        if request_start == -1:
            break
        request_start += len(request_marker)

        try:
            request_json, cursor = _extract_balanced_list(requests_block, request_start)
        except ValueError:
            break

        requests[key] = GoogleFlightsDataServiceRequest(
            key=key,
            rpc_id=rpc_id,
            request=json.loads(request_json),
        )

    return requests


def get_selected_flight_page(
    query: Query | ReturnQuery,
    flight: "Flights",
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> SelectedFlightPage:
    """Build the selected Google Flights page for a chosen flight.

    This is useful for product flows that want a direct Google Flights URL after
    a user picks an option.  The returned page metadata also exposes the
    client-side data service requests that Google's frontend embeds in the page.
    """
    from .querying import select_flight

    selected_query = select_flight(query, flight)
    html = fetch_flights_html(selected_query, proxy=proxy, integration=integration)
    return SelectedFlightPage(
        return_query=selected_query,
        url=selected_query.url(),
        f_sid=_extract_wiz_global_value(html, "FdrFJe"),
        bl=_extract_wiz_global_value(html, "cfb2h"),
        data_service_requests=_extract_data_service_requests(html),
    )


def _query_seat_name(query: Query) -> str:
    from .querying import SEAT_LOOKUP

    for name, value in SEAT_LOOKUP.items():
        if value == query.seat:
            return name
    return "economy"


def _query_passengers(query: Query) -> "Passengers":
    from .pb.flights_pb2 import Passenger
    from .querying import Passengers

    counts = {
        Passenger.ADULT: 0,
        Passenger.CHILD: 0,
        Passenger.INFANT_IN_SEAT: 0,
        Passenger.INFANT_ON_LAP: 0,
    }
    for passenger in query.passengers:
        counts[passenger] = counts.get(passenger, 0) + 1

    return Passengers(
        adults=counts.get(Passenger.ADULT, 0),
        children=counts.get(Passenger.CHILD, 0),
        infants_in_seat=counts.get(Passenger.INFANT_IN_SEAT, 0),
        infants_on_lap=counts.get(Passenger.INFANT_ON_LAP, 0),
    )


def _get_expected_return_leg(q: ReturnQuery) -> "FlightQuery | None":
    if not q.base._flights:
        return None
    if q.next_leg_index >= len(q.base._flights):
        return None
    return q.base._flights[q.next_leg_index]


def _results_match_leg(results: MetaList, leg: "FlightQuery") -> bool:
    if not results:
        return False
    first = results[0]
    if not first.flights:
        return False
    first_segment = first.flights[0]
    last_segment = first.flights[-1]
    return (
        first_segment.from_airport.code == leg.from_airport
        and last_segment.to_airport.code == leg.to_airport
    )


def _get_directional_leg_results(
    base: Query,
    leg_index: int,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> MetaList:
    from .querying import create_query

    if not base._flights:
        raise ValueError("Directional fallback requires original flight legs on the base query.")
    if leg_index >= len(base._flights):
        raise ValueError(f"Leg index {leg_index} is out of range for this query.")

    one_way_query = create_query(
        flights=[base._flights[leg_index]],
        trip="one-way",
        seat=_query_seat_name(base),
        passengers=_query_passengers(base),
        language=base.language,
        currency=base.currency,
    )
    return get_flights(one_way_query, proxy=proxy, integration=integration)


def get_flights_multicity_chained(
    flights: "list[FlightQuery]",
    *,
    language: str = "en-US",
    currency: str = "USD",
    seat: str = "economy",
    passengers: "Passengers | None" = None,
    proxy: str | None = None,
    delay: float = 1.0,
) -> list[MulticityLegChained]:
    """Search a multi-city itinerary and return available options with total trip prices.

    Google still exposes bundled total itinerary pricing via the multi-city RPC,
    but later-leg HTML chaining no longer yields correctly directed segment data.
    This function therefore combines:

    * one multi-city RPC call for the bundled ``total_price``
    * one independent one-way search per leg for correctly directed ``flights``

    Returns:
        A list of :class:`MulticityLegChained`, one per input leg.
        All entries share the same bundled ``total_price``.
        Each entry's ``flights`` contains the correctly directed options for that leg.
    """
    if len(flights) < 2:
        raise ValueError("Multi-city chaining requires at least 2 flight legs")

    from .querying import Passengers as _P
    if passengers is None:
        passengers = _P(adults=1)
    _pc = (passengers.adults, passengers.children, passengers.infants_in_seat, passengers.infants_on_lap)

    client = _build_default_client(proxy=proxy)

    tokens, price, _, _ = fetch_shopping_results(
        client=client,
        legs=flights,
        tokens=[],
        language=language,
        currency=currency,
        seat=seat,
        passenger_counts=_pc,
    )

    directional_legs = get_flights_multicity(
        flights,
        seat=seat,
        passengers=passengers,
        language=language,
        currency=currency,
        proxy=proxy,
        delay=delay,
    )

    all_legs: list[MulticityLegChained] = []
    for i, leg in enumerate(flights):
        leg_results = directional_legs[i].results if i < len(directional_legs) else None
        all_legs.append(MulticityLegChained(
            leg_index=i,
            from_airport=leg.from_airport,
            to_airport=leg.to_airport,
            date=leg.date if isinstance(leg.date, str) else leg.date.strftime("%Y-%m-%d"),
            tokens=tokens,
            total_price=price,
            flights=leg_results,
        ))

    return all_legs
