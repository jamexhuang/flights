<div align="center">

# ✈️ faster-flights

Fast, strongly-typed Google Flights scraping for Python.

[**Documentation**](https://jamexhuang.github.io/flights) • [Issues](https://github.com/jamexhuang/flights/issues) • [PyPI](https://pypi.org/project/faster-flights/)

```bash
pip install faster-flights
```

</div>

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
    seat="economy",  # economy / premium-economy / business / first
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)

results = get_flights(query)

for flight in results[:3]:
    print(f"{flight.airlines} - ${flight.price}")
```

## Current public API

The supported top-level API is the set exported from `fast_flights`:

- `FlightQuery`
- `Passengers`
- `create_query()` and `create_filter()` (`create_filter` is a compatibility alias)
- `get_flights()`
- `select_flight()`
- `get_return_flights()`
- `get_flights_multicity()`
- `get_flights_multicity_chained()`
- `fetch_flights_html()`

Use IATA airport codes like `"TPE"`, `"NRT"`, or `"JFK"` in `FlightQuery`. The repository does not currently export a public airport search helper.

## Round-trip searches

Round-trip search is a two-step flow:

1. Query outbound options with `get_flights()`
2. Select one outbound option and fetch return options with `get_return_flights()`

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
    seat="business",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)

outbound = get_flights(query)
return_query = select_flight(query, outbound[0])
returning = get_return_flights(return_query)
```

Each outbound result carries a hidden `select_token`. `select_flight()` wraps that token into a `ReturnQuery`.

## Multi-city searches

There are three supported multi-city workflows.

### 1. Total trip price + first-leg options

Use `get_flights_multicity_chained()` when you want Google's bundled multi-city pricing in one RPC call.

```python
from fast_flights import FlightQuery, get_flights_multicity_chained

legs = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

result = get_flights_multicity_chained(
    legs,
    seat="economy",
    language="en-US",
    currency="USD",
)

print(result[0].total_price)
print(len(result[0].flights))  # first-leg options only
```

### 2. Per-leg flight details

Use `get_flights_multicity()` when you want each leg as an independent one-way search.

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
    language="en-US",
    currency="USD",
)
```

This returns per-leg one-way pricing, not Google's bundled total trip price.

### 3. Hybrid workflow

Use `get_flights(create_query(..., trip="multi-city"))` for the first-leg bundled options, then `get_flights_multicity()` for detailed options on legs 2+.

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
    language="en-US",
    currency="USD",
)

leg1 = get_flights(query)
remaining = get_flights_multicity(
    flights=legs[1:],
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)
```

The round-trip return-flight API is not the supported way to fetch legs 2+ for multi-city itineraries. Google's HTML response for that path does not provide the required data.

## Integrations and proxies

Fetching customization is done with `integration=` and `proxy=`. The current public API does not expose legacy fetch flags or a packaged local-browser mode.

### Bright Data

```python
from fast_flights import get_flights
from fast_flights.integrations import BrightData

integration = BrightData(api_key="...")
results = get_flights(query, integration=integration)
```

### Custom integrations

Subclass `fast_flights.integrations.base.Integration` and implement `fetch_html(q) -> str`.

```python
from fast_flights.integrations.base import Integration


class MyIntegration(Integration):
    def fetch_html(self, q):
        return "...html..."
```

### Proxy support

```python
results = get_flights(query, proxy="http://user:pass@proxy:8080")
```

`get_flights_multicity()` also forwards `integration=` and `proxy=` to each per-leg one-way search. RPC-based multi-city flows (`get_flights(...trip="multi-city")` and `get_flights_multicity_chained()`) support `proxy=` but not integration overrides.

## Documentation

- [Getting started](https://jamexhuang.github.io/flights/)
- [Query building](https://jamexhuang.github.io/flights/filters/)
- [Return flights](https://jamexhuang.github.io/flights/return-flights/)
- [Multi-city](https://jamexhuang.github.io/flights/multicity/)
- [Integrations and proxies](https://jamexhuang.github.io/flights/fallbacks/)

## Contributing

Contributing is welcomed. A few notes though:

1. please no ai slop. i am not reading all that.
2. one change at a time. what your title says is what you've changed.
3. no new dependencies unless it's related to the core parsing.
4. really, i cant finish reading all of them, i have other projects and life to do. really sorry
