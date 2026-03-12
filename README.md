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
from fast_flights import FlightQuery, Passengers, ShoppingOptions, create_query, get_flights

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

results = get_flights(
    query,
    shopping=ShoppingOptions(
        ranking_mode="best",
        result_sort="top_flights",
    ),
)

for flight in results[:3]:
    print(f"{flight.airlines} - ${flight.price}")
    print(flight.rank, flight.group_key)

print(results.metadata.shopping.cheapest_price)
```

## Current public API

The supported top-level API is the set exported from `fast_flights`:

- `FlightQuery`
- `Passengers`
- `create_query()` and `create_filter()` (`create_filter` is a compatibility alias)
- `SearchSession`
- `ShoppingOptions`
- `build_booking_tfs()` / `build_booking_url()`
- `get_flights()`
- `select_flight()`
- `get_return_flights()`
- `get_flights_multicity()`
- `get_flights_multicity_chained()`
- `get_selected_flight_page()`
- `PlaywrightBrowserProvider` (experimental)
- `fetch_flights_html()`

Use IATA airport codes like `"TPE"`, `"NRT"`, or `"JFK"` in `FlightQuery`. The repository does not currently export a public airport search helper.

## Google shopping ranking and sorting

Use `ShoppingOptions` when you want the same server-side ranking and ordering that Google Flights uses in its shopping RPC:

```python
from fast_flights import ShoppingOptions, get_flights

results = get_flights(
    query,
    shopping=ShoppingOptions(
        ranking_mode="cheapest",
        result_sort="price",
    ),
)
```

Supported values:

- `ranking_mode`: `best`, `cheapest`
- `result_sort`: `top_flights`, `price`, `departure_time`, `arrival_time`, `duration`, `emissions`

When `shopping` is provided:

- `get_flights()` and `get_return_flights()` use the shopping RPC instead of HTML parsing
- result order matches Google’s RPC order
- `results.metadata.shopping` includes ranking metadata such as `ranking_mode`, `result_sort`, `cheapest_price`, `ranking_token`, `source`, and Google group boundaries
- each `Flights` item carries additive `rank`, `group_key`, and `group_title` metadata

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

`get_return_flights()` first tries Google's selected-flight HTML and verifies that the returned itinerary direction matches the requested return leg. If Google still serves the wrong payload there, the library rebuilds the browser-style selected `tfs` state from the chosen outbound segments and fetches the bundled return page again.

Only if both HTML paths fail does the library fall back to an independent one-way query for the requested return leg. In that last-resort mode, the returned `Flights.price` values are per-leg one-way prices rather than Google's selected round-trip total.

### Session workflow

Use `SearchSession` when you want one API for chained search state, current search links, the final booking link, and optional Google shopping ranking:

```python
from fast_flights import FlightQuery, Passengers, SearchSession, ShoppingOptions, create_query

query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)

session = SearchSession(
    query,
    mode="rpc-first",
    shopping=ShoppingOptions(ranking_mode="best", result_sort="top_flights"),
)
outbound = session.results()
session = session.select(outbound[0])
returning = session.results()
session = session.select(returning[0])

print(session.current_search_tfs)   # selected-page / search-state tfs
print(session.final_booking_tfs)    # final booking itinerary tfs
print(session.booking_url())        # https://www.google.com/travel/flights/booking?...
```

`build_booking_tfs()` and `build_booking_url()` expose the same final booking-state builder directly if you already have `selected_legs`.

### Experimental browser parity

If later-leg results do not match what Google shows in a real browser, you can let `SearchSession` fall back to a browser-captured shopping response:

```python
from fast_flights import (
    FlightQuery,
    Passengers,
    PlaywrightBrowserProvider,
    SearchSession,
    create_query,
)

query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="LHR"),
        FlightQuery(date="2026-04-14", from_airport="LHR", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-GB",
    currency="GBP",
)

session = SearchSession(
    query,
    mode="rpc-first",
    browser_fallback=True,
    browser_provider=PlaywrightBrowserProvider(),
)
```

This path is experimental and only applies to later legs. The normal order stays:

- `rpc-first`: shopping RPC -> selected/bundled HTML -> browser capture -> directional fallback
- `ssr-first`: selected/bundled HTML -> shopping RPC -> browser capture -> directional fallback

The browser provider captures the real `GetShoppingResults` response and feeds that response into the existing parser. It does not replay the request body in v1.

## Multi-city searches

There are three supported multi-city workflows.

### 1. Total trip price + directional per-leg options

Use `get_flights_multicity_chained()` when you want Google's bundled multi-city pricing plus correctly directed parsed options for each leg.

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
print(result[1].flights[0].flights[-1].to_airport.code)  # per-leg directional results
```

`total_price` is Google's bundled multi-city price from the RPC response. The per-leg `flights` lists are populated with independent one-way searches for each leg so the parsed routes always match the requested leg direction. That means later-leg `Flights.price` values are per-leg one-way prices, not re-priced bundled totals.

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

Use `get_flights(create_query(..., trip="multi-city"))` for Google's bundled first-leg options, then `get_flights_multicity()` for detailed options on legs 2+.

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

### 4. Direct Google Flights selected page

Use `get_selected_flight_page()` when a user picks an option and you want the direct Google Flights page for that selection.

```python
from fast_flights import get_selected_flight_page

selected = get_selected_flight_page(query, leg1[0])

print(selected.url)
print(selected.f_sid)
print(selected.bl)
print(selected.data_service_requests["ds:1"].rpc_id)
```

For multi-city searches, this gives you the real Google Flights selected page plus the client-side data-service requests embedded in that page. Google still does not expose later-leg bundled options as parsed `Flights` objects through this library's public API.

The round-trip return-flight API is not the supported way to fetch legs 2+ for multi-city itineraries. Google's HTML response for that path does not provide the required data.

## Integrations and proxies

Fetching customization is split between `integration=` for HTML fetches and `browser_provider=` for experimental browser-assisted parity in `SearchSession`.

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

### Browser providers

Browser providers are separate from integrations. They do not replace `fetch_html()`. They only provide an optional network-capture fallback for chained `SearchSession` searches.

```python
from fast_flights import PlaywrightBrowserProvider, SearchSession

session = SearchSession(
    query,
    browser_fallback=True,
    browser_provider=PlaywrightBrowserProvider(),
)
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
