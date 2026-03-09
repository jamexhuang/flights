# Multi-City

`faster-flights` supports multi-city itineraries, but there are different workflows depending on whether you want Google's bundled total price or detailed per-leg results.

## Workflow 1: `get_flights_multicity_chained()`

Use this when you want Google's bundled multi-city pricing plus correctly directed parsed options for each requested leg.

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
print(len(result[0].flights))
```

### What you get

- A `list[MulticityLegChained]`
- One entry per requested leg
- Shared `total_price` across all entries
- Directionally correct `flights` results for each leg

### Important limitation

`total_price` comes from Google's bundled multi-city RPC response.

The per-leg `flights` field is populated with independent one-way searches for each leg because Google no longer exposes later-leg bundled directionally correct HTML through the old chaining path.

That means later-leg `Flights.price` values are per-leg one-way prices, while `total_price` is the full bundled itinerary price.

## Workflow 2: `get_flights_multicity()`

Use this when you want detailed options for every leg as independent one-way searches.

```python
from fast_flights import FlightQuery, Passengers, get_flights_multicity

legs = get_flights_multicity(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
        FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
    ],
    seat="business",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
    delay=1.5,
)

for leg in legs:
    print(leg.leg_index, leg.from_airport, leg.to_airport, len(leg.results))
```

### What you get

- A `list[MulticityLeg]`
- Detailed parsed results per leg
- Per-leg one-way pricing
- Support for `integration=` and `proxy=`

### Tradeoff

This does not use Google's bundled multi-city total price. You are looking at independent one-way searches.

## Workflow 3: Hybrid

Use this when you want:

1. Google's bundled total price and first-leg options
2. Detailed leg-by-leg options for legs 2+

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

## Workflow 4: Direct Google Flights selected page

Use this when a user picks a bundled first-leg option and you want the direct Google Flights page for that exact selection.

```python
from fast_flights import get_selected_flight_page

selected = get_selected_flight_page(query, leg1[0])

print(selected.url)
print(selected.f_sid)
print(selected.bl)
print(selected.data_service_requests["ds:1"].rpc_id)
```

This selected page is useful for product handoff flows because it exposes:

- The direct Google Flights URL with the chosen flight encoded in `tfu`
- The frontend `f_sid` and `bl` values from `window.WIZ_global_data`
- The embedded `AF_dataServiceRequests` payloads used by Google's client-side page

It does **not** yet mean later-leg bundled options are available as parsed `Flights` results in this library.

## What not to do

The round-trip return-flight API is not the supported way to fetch legs 2+ of a multi-city itinerary.

The current Google HTML response for that path does not contain the required data for later multi-city legs, so manual `select_flight()` chaining with the round-trip return-flight flow is not a supported multi-city workflow.

## Integration behavior

- `get_flights_multicity()` supports `integration=` and `proxy=`
- `get_flights_multicity_chained()` supports `proxy=` but not `integration=`
- `get_flights(create_query(..., trip="multi-city"))` also uses the RPC path internally, so it supports `proxy=` but not `integration=`
