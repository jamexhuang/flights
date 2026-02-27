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
from .fetcher import get_flights, get_return_flights, fetch_flights_html

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
    "fetch_flights_html",
    "integrations",
]
