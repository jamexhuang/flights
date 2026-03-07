# Faster Flights

`faster-flights` builds Google Flights queries from typed Python objects, sends the request, and parses the response into Python models.

```bash
pip install faster-flights
```

## Quick start

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

query = create_query(
    flights=[
        FlightQuery(
            date="2026-03-31",
            from_airport="TPE",
            to_airport="NRT",
        ),
    ],
    trip="one-way",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)

results = get_flights(query)

for flight in results[:3]:
    print(f"{flight.airlines} - ${flight.price}")
```

## Core concepts

### `FlightQuery`

One requested leg of travel.

```python
FlightQuery(
    date="2026-03-31",
    from_airport="TPE",
    to_airport="NRT",
    max_stops=1,
    airlines=["BR", "STAR_ALLIANCE"],
)
```

Use IATA airport codes such as `"TPE"`, `"NRT"`, or `"JFK"`.

### `Passengers`

Passenger counts for the whole search.

```python
Passengers(adults=2, children=1, infants_in_seat=0, infants_on_lap=0)
```

### `create_query()`

Builds a typed `Query` object from your legs and search options.

```python
query = create_query(
    flights=[...],
    trip="round-trip",
    seat="business",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)
```

`create_filter()` is still exported as a compatibility alias, but `create_query()` is the primary API.

### `get_flights()`

Fetches and parses flight results.

- `trip="one-way"`: one leg
- `trip="round-trip"`: outbound step of a two-step round-trip flow
- `trip="multi-city"`: first-leg bundled multi-city options with total trip pricing

## Supported values

### Trip types

- `one-way`
- `round-trip`
- `multi-city`

### Seat types

- `economy`
- `premium-economy`
- `business`
- `first`

## What to read next

- [Query building](filters.md)
- [Return flights](return-flights.md)
- [Multi-city](multicity.md)
- [Integrations and proxies](fallbacks.md)
- [Custom integrations](local.md)
