from dataclasses import dataclass, field
from typing import Annotated, Literal, Optional, Union


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
    duration: Annotated[int, "(minutes)"]
    plane_type: str
    airline_code: str = ""
    flight_number: str = ""


@dataclass
class CarbonEmission:
    typical_on_route: Annotated[int, "(grams)"]
    emission: Annotated[int, "(grams)"]


@dataclass
class Flights:
    type: str | Literal["multi"]
    price: int
    airlines: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission
    select_token: Optional[str] = field(default=None, repr=False)
    """Session token from ds:1 data (f[1][1]) used for the ``tfu`` URL
    parameter when querying return flights in a round-trip search."""
    select_data: Optional[str] = field(default=None, repr=False)
    """Encoded selected-flight data from ds:1 (f[8]) used for the ``tfs``
    URL parameter when querying return flights."""
