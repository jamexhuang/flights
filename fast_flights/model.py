from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class Airline:
    code: str
    name: str


@dataclass
class Alliance:
    code: str
    name: str


@dataclass
class JsMetadata:
    airlines: list[Airline]
    alliances: list[Alliance]
    shopping: Optional["ShoppingMetadata"] = None


@dataclass
class Airport:
    name: str
    code: str


@dataclass
class SimpleDatetime:
    date: tuple[int, int, int]
    time: tuple[int, int]


@dataclass
class SingleFlight:
    from_airport: Airport
    to_airport: Airport
    departure: SimpleDatetime
    arrival: SimpleDatetime
    duration: int  # minutes
    plane_type: str
    airline_code: str = ""
    flight_number: str = ""


@dataclass
class CarbonEmission:
    typical_on_route: int  # grams
    emission: int  # grams


@dataclass
class ShoppingGroup:
    key: str
    title: str
    flight_indices: list[int]


@dataclass
class ShoppingMetadata:
    ranking_mode: str | None = None
    result_sort: str | None = None
    source: str | None = None
    cheapest_price: int | None = None
    ranking_token: str | None = None
    groups: list[ShoppingGroup] = field(default_factory=list)


@dataclass
class Flights:
    type: str | Literal["multi"]
    price: int
    airlines: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission
    rank: Optional[int] = None
    group_key: Optional[str] = None
    group_title: Optional[str] = None
    select_token: Optional[str] = field(default=None, repr=False)
    """Session token from ds:1 data (f[1][1]) used for the ``tfu`` URL
    parameter when querying return flights in a round-trip search."""
    select_data: Optional[str] = field(default=None, repr=False)
    """Encoded selected-flight data from ds:1 (f[8]) used for the ``tfs``
    URL parameter when querying return flights."""
