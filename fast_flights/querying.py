from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime as Datetime
from typing import Literal, Optional, Union

from .pb.flights_pb2 import Airport, FlightData, Info, Passenger, Seat, Trip
from .types import Currency, Language, SeatType, TripType


@dataclass
class Query:
    """A query containing `?tfs` data."""

    flight_data: list[FlightData]
    seat: Seat
    trip: Trip
    passengers: list[Passenger]
    language: str
    currency: str

    def pb(self) -> Info:
        """(internal) Protobuf data. (`Info`)"""
        return Info(
            data=self.flight_data,
            seat=self.seat,
            trip=self.trip,
            passengers=self.passengers,
        )

    def to_bytes(self) -> bytes:
        """Convert this query to bytes."""
        return self.pb().SerializeToString()

    def to_str(self) -> str:
        """Convert this query to a string."""
        return b64encode(self.to_bytes()).decode("utf-8")

    def url(self) -> str:
        """Get the URL for this query.

        This is generally used for debugging purposes.
        """
        return (
            "https://www.google.com/travel/flights/search?tfs="
            + self.to_str()
            + "&hl="
            + self.language
            + "&curr="
            + self.currency
        )

    def params(self) -> dict[str, str]:
        """Create `params` in dictionary form."""
        return {"tfs": self.to_str(), "hl": self.language, "curr": self.currency}

    def __repr__(self) -> str:
        return "Query(...)"


@dataclass
class FlightQuery:
    date: str | Datetime
    from_airport: str
    to_airport: str
    max_stops: int | None = None
    airlines: list[str] | None = None

    def pb(self) -> FlightData:
        if isinstance(self.date, str):
            date = self.date
        else:
            date = self.date.strftime("%Y-%m-%d")

        return FlightData(
            date=date,
            from_airport=Airport(airport=self.from_airport),
            to_airport=Airport(airport=self.to_airport),
            max_stops=self.max_stops,
            airlines=self.airlines,
        )

    def _setmaxstops(self, m: int | None = None) -> "FlightQuery":
        if m is not None:
            self.max_stops = m

        return self


class Passengers:
    def __init__(
        self,
        *,
        adults: int = 0,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        assert sum((adults, children, infants_in_seat, infants_on_lap)) <= 9, (
            "Too many passengers (> 9)"
        )
        assert infants_on_lap <= adults, (
            "Must have at least one adult per infant on lap"
        )

        self.adults = adults
        self.children = children
        self.infants_in_seat = infants_in_seat
        self.infants_on_lap = infants_on_lap

    def pb(self) -> list[Passenger]:
        return [
            *(Passenger.ADULT for _ in range(self.adults)),
            *(Passenger.CHILD for _ in range(self.children)),
            *(Passenger.INFANT_IN_SEAT for _ in range(self.infants_in_seat)),
            *(Passenger.INFANT_ON_LAP for _ in range(self.infants_on_lap)),
        ]


DEFAULT_PASSENGERS = Passengers(adults=1)
SEAT_LOOKUP = {
    "economy": Seat.ECONOMY,
    "premium-economy": Seat.PREMIUM_ECONOMY,
    "business": Seat.BUSINESS,
    "first": Seat.FIRST,
}
TRIP_LOOKUP = {
    "round-trip": Trip.ROUND_TRIP,
    "one-way": Trip.ONE_WAY,
    "multi-city": Trip.MULTI_CITY,
}


def create_query(
    *,
    flights: list[FlightQuery],
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    passengers: Passengers = DEFAULT_PASSENGERS,
    language: str | Literal[""] | Language = "",
    currency: str | Literal[""] | Currency = "",
    max_stops: int | None = None,
) -> Query:
    """Create a query.

    Args:
        flights: The flight queries.
        seat: Desired seat type.
        trip: Trip type.
        passengers: Passengers.
        language: Set the language. Use `""` (blank str) to let Google decide.
        currency: Set the currency. Use `""` (blank str) to let Google decide.
        max_stops (optional): Set the maximum stops for every flight query, if present.
    """
    return Query(
        flight_data=[flight._setmaxstops(max_stops).pb() for flight in flights],
        seat=SEAT_LOOKUP[seat],
        trip=TRIP_LOOKUP[trip],
        passengers=passengers.pb(),
        language=language,
        currency=currency,
    )


@dataclass
class ReturnQuery:
    """A query for fetching return flights after selecting an outbound flight.

    Wraps the original :class:`Query` with the ``tfu`` session token
    extracted from a selected :class:`~fast_flights.model.Flights` result.
    """

    base: Query
    tfu: str

    def params(self) -> dict[str, str]:
        """Create `params` in dictionary form, including the ``tfu`` key."""
        p = self.base.params()
        p["tfu"] = self.tfu
        return p

    def url(self) -> str:
        """Get the URL for this return-flight query."""
        return self.base.url() + "&tfu=" + self.tfu

    def __repr__(self) -> str:
        return "ReturnQuery(...)"


def _build_tfu(token: str) -> str:
    """Wrap a session token in the protobuf envelope expected by the ``tfu``
    URL parameter and return it as a Base64 string.

    Wire format::

        Field 1 (LEN): <token>
        Field 2 (LEN): { Field 1 (VARINT): 0 }
        Field 4 (LEN): ""
    """
    import struct

    def _encode_varint(value: int) -> bytes:
        parts = []
        while value > 0x7F:
            parts.append((value & 0x7F) | 0x80)
            value >>= 7
        parts.append(value & 0x7F)
        return bytes(parts)

    def _encode_len(field_number: int, data: bytes) -> bytes:
        tag = _encode_varint((field_number << 3) | 2)
        length = _encode_varint(len(data))
        return tag + length + data

    token_bytes = token.encode("utf-8")
    field2_inner = _encode_varint((1 << 3) | 0) + _encode_varint(0)  # Field 1 varint 0
    payload = (
        _encode_len(1, token_bytes)
        + _encode_len(2, field2_inner)
        + _encode_len(4, b"")
    )
    return b64encode(payload).decode("utf-8")


def select_flight(query: Query, flight: "Flights") -> ReturnQuery:
    """Build a :class:`ReturnQuery` for fetching return-flight options.

    After calling :func:`get_flights` on a round-trip query you receive a
    list of outbound flights, each carrying a ``select_token``.  Pass the
    original *query* together with the chosen *flight* to this function to
    obtain a :class:`ReturnQuery` that can be fed to
    :func:`~fast_flights.fetcher.get_return_flights`.

    Args:
        query: The original round-trip query.
        flight: A :class:`~fast_flights.model.Flights` result with a valid
            ``select_token``.

    Raises:
        ValueError: If the flight has no ``select_token``.
    """
    from .model import Flights  # avoid circular import at module level

    if not flight.select_token:
        raise ValueError(
            "The selected flight has no select_token. "
            "Make sure you are using a round-trip query and the "
            "parser extracted the token correctly."
        )

    tfu = _build_tfu(flight.select_token)
    return ReturnQuery(base=query, tfu=tfu)
