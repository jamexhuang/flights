from __future__ import annotations

from dataclasses import dataclass
from typing import overload, TYPE_CHECKING

from primp import Client

from .integrations.base import Integration
from .parser import MetaList, parse
from .querying import Query, ReturnQuery

if TYPE_CHECKING:
    from collections.abc import Callable
    from .model import Flights
    from .querying import FlightQuery, Passengers
    from .types import SeatType

URL = "https://www.google.com/travel/flights"


@overload
def get_flights(q: str, /, *, proxy: str | None = None) -> MetaList:
    """Get flights using a str query.

    Examples:
    - *Flights from TPE to MYJ on 2025-12-22 one way economy class*
    """


@overload
def get_flights(q: Query, /, *, proxy: str | None = None) -> MetaList:
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
    q: Query | str,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> MetaList:
    """Get flights.

    Args:
        q: The query.
        proxy (str, optional): Proxy.
    """
    html = fetch_flights_html(q, proxy=proxy, integration=integration)
    return parse(html)


def get_return_flights(
    q: ReturnQuery,
    /,
    *,
    proxy: str | None = None,
    integration: Integration | None = None,
) -> MetaList:
    """Get return flights after selecting an outbound flight.

    Use :func:`~fast_flights.querying.select_flight` to build a
    :class:`ReturnQuery` from the original query and a chosen outbound
    flight, then pass it here to retrieve the available return options.

    Args:
        q: A :class:`ReturnQuery` created by :func:`select_flight`.
        proxy (str, optional): Proxy.
    """
    html = fetch_flights_html(q, proxy=proxy, integration=integration)
    return parse(html)


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
        client = Client(
            impersonate="chrome_127",
            impersonate_os="macos",
            referer=True,
            proxy=proxy,
            cookie_store=True,
        )

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
    selector: "Callable[[MulticityLeg], Flights] | None" = None,
    delay: float = 1.0,
) -> list[MulticityLeg]:
    """Search a multi-city itinerary by chaining round-trip queries.

    Google Flights does not server-side render multi-city results, so the
    standard ``get_flights()`` returns empty data for ``trip="multi-city"``
    when using the default primp (HTTP-only) client.

    This function works around the limitation by running sequential
    round-trip / return queries, chaining each leg via
    :func:`select_flight`.

    Args:
        flights: List of :class:`FlightQuery`, one per leg (2–10 legs).
        seat: Seat class.
        passengers: Passenger counts. Defaults to 1 adult.
        language: Language code (e.g. ``"en"``).
        currency: Currency code (e.g. ``"EUR"``).
        proxy: Optional proxy string.
        integration: Optional :class:`Integration` for the HTTP fetch.
        selector: A callable that receives a :class:`MulticityLeg` and
            returns the :class:`Flights` to select for that leg.
            If ``None``, the first result is selected automatically.
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
        FlightQuery as _FQ,
        Passengers as _P,
        create_query as _cq,
        select_flight as _sel,
    )

    if passengers is None:
        passengers = _P(adults=1)

    if len(flights) < 2:
        raise ValueError("Multi-city requires at least 2 legs")

    all_legs: list[MulticityLeg] = []

    # ── Leg 0 (first leg): use round-trip with legs[0] and legs[1] ──
    query = _cq(
        flights=[flights[0], flights[1]],
        trip="round-trip",
        seat=seat,
        passengers=passengers,
        language=language,
        currency=currency,
    )
    results = get_flights(query, proxy=proxy, integration=integration)
    leg0 = MulticityLeg(
        leg_index=0,
        from_airport=flights[0].from_airport,
        to_airport=flights[0].to_airport,
        date=flights[0].date if isinstance(flights[0].date, str) else flights[0].date.strftime("%Y-%m-%d"),
        results=results,
    )
    all_legs.append(leg0)

    if not results:
        return all_legs  # no results for leg 0

    # Select flight for leg 0
    pick = selector(leg0) if selector else results[0]
    current_q = _sel(query, pick)

    # ── Legs 1..N-1: chain via select_flight + get_return_flights ──
    for i in range(1, len(flights)):
        if delay > 0:
            _time.sleep(delay)

        results = get_return_flights(current_q, proxy=proxy, integration=integration)
        leg = MulticityLeg(
            leg_index=i,
            from_airport=flights[i].from_airport,
            to_airport=flights[i].to_airport,
            date=flights[i].date if isinstance(flights[i].date, str) else flights[i].date.strftime("%Y-%m-%d"),
            results=results,
        )
        all_legs.append(leg)

        if not results:
            break  # no results for this leg

        # Select flight for this leg (needed for subsequent legs)
        if i < len(flights) - 1:
            pick = selector(leg) if selector else results[0]
            current_q = _sel(current_q, pick)

    return all_legs

