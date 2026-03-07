# Migration Guide

This guide maps older `faster-flights` usage and outdated docs examples to the current public API.

## Install

```bash
pip install faster-flights
```

If you pin directly to this repository:

```bash
pip install git+https://github.com/jamexhuang/flights.git@dev
```

## Old names vs current API

| Older docs / examples | Current API |
|-----------------------|-------------|
| `FlightData(...)` | `FlightQuery(...)` |
| `create_filter(...)` | `create_query(...)` (`create_filter` still works as an alias) |
| `fetch_mode="fallback"` | `proxy=` or `integration=` |
| `fetch_mode="local"` | build your own `Integration` |
| `get_return_flights()` for multi-city leg 2+ | `get_flights_multicity()` or a hybrid flow |
| `search_airports()` | provide your own IATA lookup and pass strings into `FlightQuery` |

## Basic query shape

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    ],
    trip="one-way",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)

results = get_flights(query)
```

## Round-trip

Round-trip is a two-step flow.

```python
from fast_flights import (
    FlightQuery,
    Passengers,
    create_query,
    get_flights,
    get_return_flights,
    select_flight,
)

query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    currency="USD",
)

outbound = get_flights(query)
return_query = select_flight(query, outbound[0])
returning = get_return_flights(return_query)
```

## Multi-city

There are two helper flows plus one hybrid flow.

### Bundled total price

```python
from fast_flights import FlightQuery, get_flights_multicity_chained

legs = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

result = get_flights_multicity_chained(legs, seat="economy")
```

### Per-leg detail

```python
from fast_flights import FlightQuery, Passengers, get_flights_multicity

legs = get_flights_multicity(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
        FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
    ],
    seat="economy",
    passengers=Passengers(adults=1),
)
```

### Hybrid

```python
from fast_flights import (
    FlightQuery,
    Passengers,
    create_query,
    get_flights,
    get_flights_multicity,
)

legs = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

query = create_query(
    flights=legs,
    trip="multi-city",
    seat="economy",
    passengers=Passengers(adults=1),
)

leg1 = get_flights(query)
remaining = get_flights_multicity(
    flights=legs[1:],
    seat="economy",
    passengers=Passengers(adults=1),
)
```

## Integrations and proxies

If older code used fallback or local fetch modes, replace that with:

- `proxy="http://user:pass@proxy:8080"`
- `integration=BrightData(...)`
- your own subclass of `Integration`

Example:

```python
from fast_flights.integrations import BrightData

integration = BrightData(api_key="...")
results = get_flights(query, integration=integration)
```

## Current behavior to rely on

- `seat` is supported for `one-way`, `round-trip`, and the current multi-city entry points
- `multi-city` is supported
- `create_filter()` is an alias, not a separate query model
- there is no public airport search helper or local fetch mode in the current API
