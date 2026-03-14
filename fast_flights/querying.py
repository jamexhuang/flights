from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import datetime as Datetime
import re
from typing import Literal, Optional, Union
from urllib.parse import urlencode

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
    _flights: list['FlightQuery'] | None = None

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


@dataclass(frozen=True)
class SelectedSegment:
    from_airport: str
    departure_date: str
    to_airport: str
    airline_code: str
    flight_number: str


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
        _flights=flights,
    )


@dataclass
class ReturnQuery:
    """A query for fetching return flights after selecting an outbound flight.

    Wraps the original :class:`Query` with the ``tfu`` session token
    extracted from a selected :class:`~fast_flights.model.Flights` result.
    The raw selection context is also retained so return searches can
    rebuild Google's bundled selected-itinerary state when needed.
    """

    base: Query
    tfu: str
    selected_tfs: str | None = None
    next_leg_index: int = 1
    selection_tokens: tuple[str, ...] = ()
    selected_legs: tuple[tuple[SelectedSegment, ...], ...] = ()

    def params(self) -> dict[str, str]:
        """Create `params` in dictionary form, including the ``tfu`` key."""
        p = self.base.params()
        # Use a fully rebuilt booking tfs string only when every selected leg can
        # be reconstructed. Synthetic selector flows can carry a valid
        # ``selected_tfs`` even when ``selected_legs`` was initially empty.
        tfs = _effective_return_tfs(self.base, self.selected_legs, self.selected_tfs)
        if tfs:
            p["tfs"] = tfs
        p["tfu"] = self.tfu
        return p

    def url(self) -> str:
        """Get the URL for this return-flight query."""
        tfs = _effective_return_tfs(self.base, self.selected_legs, self.selected_tfs) or self.base.to_str()
        return (
            "https://www.google.com/travel/flights/search?tfs="
            + tfs
            + "&hl="
            + self.base.language
            + "&curr="
            + self.base.currency
            + "&tfu="
            + self.tfu
        )

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


def _extract_selected_tfs(select_data: str | None) -> str | None:
    """Decode the selected-flight ``tfs`` payload from ``Flights.select_data``."""
    import json

    if not select_data:
        return None

    try:
        decoded = json.loads(select_data)
    except json.JSONDecodeError:
        return select_data

    if isinstance(decoded, list) and decoded and isinstance(decoded[0], str):
        return decoded[0]

    if isinstance(decoded, str):
        return decoded

    return None


_SELECT_DATA_SEGMENT_PATTERN = re.compile(
    rb'\n[\x00-\xff]\n\x03(?P<from>[A-Z0-9]{3})'
    rb'\x12\x19(?P<departure>[0-9T:+-]{25})'
    rb'\x1a\x03(?P<to>[A-Z0-9]{3})'
    rb'"\x19(?P<arrival>[0-9T:+-]{25})'
    rb'\*\x02(?P<airline>[A-Z0-9]{2,3})'
    rb'2[\x01-\x08](?P<flight>[0-9A-Z]{1,8})'
)


def _extract_selected_leg_from_select_data(select_data: str | None) -> tuple[SelectedSegment, ...]:
    """Best-effort segment reconstruction from ``Flights.select_data``.

    Google's selected-flight payload contains a compact protobuf-like blob with
    all chosen segment details. Synthetic ``Flights`` objects created from a
    token + ``select_data`` pair do not carry ``flight.flights``, so we decode
    the raw blob and recover the selected legs directly.
    """
    selected_tfs = _extract_selected_tfs(select_data)
    if not selected_tfs:
        return ()

    try:
        padded = selected_tfs + ("=" * (-len(selected_tfs) % 4))
        payload = b64decode(padded, altchars=b"-_")
    except Exception:
        return ()

    segments: list[SelectedSegment] = []
    for match in _SELECT_DATA_SEGMENT_PATTERN.finditer(payload):
        try:
            departure = match.group("departure").decode("utf-8")
            segments.append(
                SelectedSegment(
                    from_airport=match.group("from").decode("utf-8"),
                    departure_date=departure[:10],
                    to_airport=match.group("to").decode("utf-8"),
                    airline_code=match.group("airline").decode("utf-8"),
                    flight_number=match.group("flight").decode("utf-8"),
                )
            )
        except Exception:
            return ()

    return tuple(segments)


def _format_segment_date(date: tuple[int, int, int] | list[int]) -> str:
    year, month, day = date
    return f"{year:04d}-{month:02d}-{day:02d}"


def _encode_varint(value: int) -> bytes:
    parts = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value & 0x7F)
    return bytes(parts)


def _encode_len(field_number: int, data: bytes) -> bytes:
    return _encode_varint((field_number << 3) | 2) + _encode_varint(len(data)) + data


def _encode_field_varint(field_number: int, value: int) -> bytes:
    return _encode_varint((field_number << 3) | 0) + _encode_varint(value)


def _encode_selected_airport(code: str) -> bytes:
    return _encode_field_varint(1, 1) + _encode_len(2, code.encode("utf-8"))


def _encode_selected_segment(segment: SelectedSegment) -> bytes:
    return b"".join(
        (
            _encode_len(1, segment.from_airport.encode("utf-8")),
            _encode_len(2, segment.departure_date.encode("utf-8")),
            _encode_len(3, segment.to_airport.encode("utf-8")),
            _encode_len(5, segment.airline_code.encode("utf-8")),
            _encode_len(6, segment.flight_number.encode("utf-8")),
        )
    )


def _encode_selected_leg(
    flight: FlightQuery,
    selected_segments: tuple[SelectedSegment, ...] = (),
) -> bytes:
    date = flight.date if isinstance(flight.date, str) else flight.date.strftime("%Y-%m-%d")
    leg = _encode_len(2, date.encode("utf-8"))
    for segment in selected_segments:
        leg += _encode_len(4, _encode_selected_segment(segment))
    leg += _encode_len(13, _encode_selected_airport(flight.from_airport))
    leg += _encode_len(14, _encode_selected_airport(flight.to_airport))
    return leg


def _selected_tfs_max_stops(base: Query) -> int:
    if not base._flights:
        return (1 << 64) - 1
    stops = [flight.max_stops for flight in base._flights if flight.max_stops is not None]
    if not stops:
        return (1 << 64) - 1
    return max(stops)


def _booking_trip_code(query: Query) -> int:
    """Map query trip type to the selected-itinerary booking payload code.

    Google's booking ``tfs`` field 2 uses a separate code from the trip type
    in field 19.  Multi-city uses the same F2 value (2) as round-trip.
    """
    if query.trip == Trip.ONE_WAY:
        return 1
    return 2


def build_booking_tfs(query: Query, selected_legs: tuple[tuple[SelectedSegment, ...], ...]) -> str | None:
    flights_list = getattr(query, "flights", getattr(query, "_flights", None))
    if not flights_list:
        return None
    if not selected_legs:
        return None

    payload = b"".join(
        (
            _encode_field_varint(1, 2 if getattr(query, "trip", None) == 3 else 28),
            _encode_field_varint(2, _booking_trip_code(query)),
            *(
                _encode_len(
                    3,
                    _encode_selected_leg(
                        flight,
                        selected_legs[idx] if idx < len(selected_legs) else (),
                    ),
                )
                for idx, flight in enumerate(flights_list)
            ),
            _encode_field_varint(8, 1),
            _encode_field_varint(9, 1),
            _encode_field_varint(14, 1),
            _encode_len(16, _encode_field_varint(1, _selected_tfs_max_stops(query))),
            _encode_field_varint(19, query.trip),
        )
    )
    return b64encode(payload, altchars=b"-_").decode("utf-8").rstrip("=")


def _effective_return_tfs(
    query: Query,
    selected_legs: tuple[tuple[SelectedSegment, ...], ...],
    selected_tfs: str | None,
) -> str | None:
    if selected_legs and all(selected_legs):
        rebuilt = build_booking_tfs(query, selected_legs)
        if rebuilt:
            return rebuilt
    return selected_tfs


def build_selected_tfs(query: Query, selected_legs: tuple[tuple[SelectedSegment, ...], ...]) -> str | None:
    """Backward-compatible alias for :func:`build_booking_tfs`."""
    return build_booking_tfs(query, selected_legs)


def build_booking_url(
    query: Query,
    selected_legs: tuple[tuple[SelectedSegment, ...], ...],
    *,
    language: str | None = None,
    currency: str | None = None,
    tfu: str | None = None,
) -> str | None:
    booking_tfs = build_booking_tfs(query, selected_legs)
    if not booking_tfs:
        return None
    params: dict[str, str] = {
        "tfs": booking_tfs,
        "hl": query.language if language is None else language,
        "curr": query.currency if currency is None else currency,
    }
    if tfu:
        params["tfu"] = tfu
    return f"https://www.google.com/travel/flights/booking?{urlencode(params)}"


def build_selected_search_url(
    query_or_return_query: Query | ReturnQuery,
    *,
    language: str | None = None,
    currency: str | None = None,
) -> str:
    """Build a Google Flights URL that preserves the available selected-flight context.

    This is primarily useful for multi-city sessions where Google may reject a
    portable finalized booking payload but will still open the matching search
    page when given the selected-session ``tfs``. Round-trip selectors continue
    to carry ``tfu`` so Google can open the selected return flow.
    """
    if isinstance(query_or_return_query, ReturnQuery):
        tfs = _effective_return_tfs(
            query_or_return_query.base,
            query_or_return_query.selected_legs,
            query_or_return_query.selected_tfs,
        ) or query_or_return_query.base.to_str()
        if query_or_return_query.base.trip == Trip.MULTI_CITY:
            params = urlencode(
                {
                    "tfs": tfs,
                    "hl": query_or_return_query.base.language if language is None else language,
                    "curr": query_or_return_query.base.currency if currency is None else currency,
                }
            )
            return f"https://www.google.com/travel/flights?{params}"
        params = urlencode(
            {
                "tfs": tfs,
                "hl": query_or_return_query.base.language if language is None else language,
                "curr": query_or_return_query.base.currency if currency is None else currency,
                "tfu": query_or_return_query.tfu,
            }
        )
        return f"https://www.google.com/travel/flights?{params}"

    params = urlencode(
        {
            "tfs": query_or_return_query.to_str(),
            "hl": query_or_return_query.language if language is None else language,
            "curr": query_or_return_query.currency if currency is None else currency,
        }
    )
    return f"https://www.google.com/travel/flights?{params}"


def _extract_selected_leg(flight: "Flights") -> tuple[SelectedSegment, ...]:
    segments: list[SelectedSegment] = []
    for segment in flight.flights:
        if not segment.airline_code or not segment.flight_number:
            return ()
        segments.append(
            SelectedSegment(
                from_airport=segment.from_airport.code,
                departure_date=_format_segment_date(segment.departure.date),
                to_airport=segment.to_airport.code,
                airline_code=segment.airline_code,
                flight_number=segment.flight_number,
            )
        )
    return tuple(segments)


def select_flight(query: "Query | ReturnQuery", flight: "Flights") -> ReturnQuery:
    """Build a :class:`ReturnQuery` for fetching the next leg's options.

    Works for both **round-trip** (2 legs) and **multi-city** (N legs).

    * For the first selection, pass the original :class:`Query`.
    * For subsequent legs, pass the :class:`ReturnQuery` from the
      previous step — this chains the selections together.

    Args:
        query: The original query (:class:`Query`) or the result of a
            previous ``select_flight()`` call (:class:`ReturnQuery`).
        flight: A :class:`~fast_flights.model.Flights` result with a valid
            ``select_token``.

    Raises:
        ValueError: If the flight has no ``select_token``.
    """
    from .model import Flights  # avoid circular import at module level

    if not flight.select_token:
        raise ValueError(
            "The selected flight has no select_token. "
            "Make sure you are using a round-trip or multi-city query and "
            "the parser extracted the token correctly."
        )

    tfu = _build_tfu(flight.select_token)
    selected_tfs = _extract_selected_tfs(flight.select_data)
    selected_leg = _extract_selected_leg(flight) or _extract_selected_leg_from_select_data(flight.select_data)

    if isinstance(query, ReturnQuery):
        selection_tokens = (*query.selection_tokens, flight.select_token)
        selected_legs = (*query.selected_legs, selected_leg)
        # Chain: keep the same base Query, just update the tfu token
        return ReturnQuery(
            base=query.base,
            tfu=tfu,
            selected_tfs=selected_tfs,
            next_leg_index=query.next_leg_index + 1,
            selection_tokens=selection_tokens,
            selected_legs=selected_legs,
        )
    else:
        return ReturnQuery(
            base=query,
            tfu=tfu,
            selected_tfs=selected_tfs,
            next_leg_index=1,
            selection_tokens=(flight.select_token,),
            selected_legs=(selected_leg,),
        )
