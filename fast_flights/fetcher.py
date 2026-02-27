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


