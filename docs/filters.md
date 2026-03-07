# Query Building

Use `FlightQuery`, `Passengers`, and `create_query()` to build searches.

## `FlightQuery`

Each `FlightQuery` describes one requested leg.

```python
from fast_flights import FlightQuery

leg = FlightQuery(
    date="2026-03-31",
    from_airport="TPE",
    to_airport="NRT",
    max_stops=1,
    airlines=["BR", "STAR_ALLIANCE"],
)
```

### Fields

- `date`: `YYYY-MM-DD` string or `datetime`
- `from_airport`: origin IATA code
- `to_airport`: destination IATA code
- `max_stops`: optional maximum number of stops for this leg
- `airlines`: optional airline or alliance filters

Google currently applies the airline filter from the first leg to the whole search more reliably than per-leg filters on later legs.

## `Passengers`

```python
from fast_flights import Passengers

passengers = Passengers(
    adults=2,
    children=1,
    infants_in_seat=0,
    infants_on_lap=0,
)
```

Constraints enforced by `Passengers`:

- Total passengers must be `<= 9`
- `infants_on_lap <= adults`

## `create_query()`

```python
from fast_flights import Passengers, create_query

query = create_query(
    flights=[leg],
    trip="one-way",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)
```

### Main arguments

- `flights`: list of `FlightQuery`
- `trip`: `one-way`, `round-trip`, or `multi-city`
- `seat`: `economy`, `premium-economy`, `business`, or `first`
- `passengers`: `Passengers`
- `language`: response language passed to Google
- `currency`: pricing currency passed to Google
- `max_stops`: optional global override applied to every `FlightQuery`

`create_filter()` is still available as a compatibility alias:

```python
from fast_flights import create_filter

query = create_filter(
    flights=[leg],
    trip="one-way",
    seat="economy",
)
```

## Query shapes by trip type

### One-way

```python
query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    ],
    trip="one-way",
    seat="economy",
    passengers=Passengers(adults=1),
)
```

### Round-trip

```python
query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="business",
    passengers=Passengers(adults=1),
)
```

### Multi-city

```python
query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
        FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
    ],
    trip="multi-city",
    seat="premium-economy",
    passengers=Passengers(adults=1),
)
```

See [Return flights](return-flights.md) for round-trip step 2, and [Multi-city](multicity.md) for the supported multi-city workflows.
