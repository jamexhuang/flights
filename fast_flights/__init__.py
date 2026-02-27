from . import integrations

from .querying import (
    FlightQuery,
    Query,
    ReturnQuery,
    Passengers,
    create_query,
    create_query as create_filter,  # alias
    select_flight,
)
from .fetcher import (
    get_flights,
    get_return_flights,
    get_flights_multicity,
    fetch_flights_html,
    MulticityLeg,
)

__all__ = [
    "FlightQuery",
    "Query",
    "ReturnQuery",
    "Passengers",
    "create_query",
    "create_filter",
    "select_flight",
    "get_flights",
    "get_return_flights",
    "get_flights_multicity",
    "fetch_flights_html",
    "MulticityLeg",
    "integrations",
]

