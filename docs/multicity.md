# Multi-City Flights

`fast-flights` provides two approaches for multi-city (N-leg) itineraries.

---

## Option A: `get_flights_multicity_chained` (Recommended)

Makes a **single call** to Google's internal `GetShoppingResults` RPC. The response already contains all available first-leg flight options, each priced as the **total cost of the entire multi-city trip**.

```python
from fast_flights import FlightQuery, get_flights_multicity_chained

legs = [
    FlightQuery(date="2026-03-15", from_airport="SIN", to_airport="TPE"),
    FlightQuery(date="2026-03-21", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-03-24", from_airport="NRT", to_airport="TPE"),
    FlightQuery(date="2026-03-27", from_airport="TPE", to_airport="SIN"),
]

result = get_flights_multicity_chained(
    legs,
    language="en-US",
    currency="USD",
)

# All legs share the same flights list and total_price
for flight in result[0].flights:
    print(f"{flight.airlines} — total trip: ${flight.price}")

# Or access summary via any leg entry
print(f"Cheapest total price: ${result[0].total_price}")
```

### Return value: `list[MulticityLegChained]`

One entry per input leg. All entries share the same `flights` and `total_price` from the single API response.

| Field | Type | Description |
|-------|------|-------------|
| `leg_index` | `int` | 0-based leg index |
| `from_airport` | `str` | Origin IATA code |
| `to_airport` | `str` | Destination IATA code |
| `date` | `str` | Departure date (`YYYY-MM-DD`) |
| `tokens` | `list[str]` | Available selection tokens from the response |
| `total_price` | `int \| None` | Cheapest total trip price found |
| `flights` | `MetaList \| None` | First-leg flight options (same as `get_flights()`) |

### How it works

`fast_flights` sends a single POST to Google's `GetShoppingResults` endpoint with all legs encoded in the `f.req` payload. The response is a nested JSON structure; the inner payload at `[2][0]` (Top Flights) and `[3][0]` (All Flights) contains first-leg options where each option's `price` already reflects the **entire multi-city trip cost** — Google bundles the pricing from the start.

### Limitations

- **First-leg flights only**: The `flights` field contains segments for the first leg only (e.g. SIN→TPE). Specific flight options for subsequent legs are encoded in each result's `select_token` for further chaining.
- **No integrations**: Uses a `primp` HTTP session internally; BrightData and Playwright integrations are not supported.

---

## Option B: Manual Chaining with `select_flight()`

For full control over which specific flight is selected on each leg, use `trip="multi-city"` with `get_flights()` and manually chain `select_flight()` calls:

```python
from fast_flights import (
    FlightQuery, Passengers, create_query,
    get_flights, select_flight, get_return_flights,
)

query = create_query(
    flights=[
        FlightQuery(date="2026-03-15", from_airport="SIN", to_airport="TPE"),
        FlightQuery(date="2026-03-21", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-03-24", from_airport="NRT", to_airport="TPE"),
        FlightQuery(date="2026-03-27", from_airport="TPE", to_airport="SIN"),
    ],
    seat="economy",
    trip="multi-city",
    passengers=Passengers(adults=1),
    currency="EUR",
)

# Leg 1: SIN → TPE
leg1 = get_flights(query)
rq = select_flight(query, leg1[0])

# Leg 2: TPE → NRT
leg2 = get_return_flights(rq)
rq = select_flight(rq, leg2[0])

# Leg 3: NRT → TPE
leg3 = get_return_flights(rq)
rq = select_flight(rq, leg3[0])

# Leg 4: TPE → SIN (final)
leg4 = get_return_flights(rq)
print(f"Final leg options: {len(leg4)}, best: €{leg4[0].price}")
```

This approach supports all integrations (BrightData, Playwright) and lets you pick specific flights at each step. The `price` on the final leg reflects the total trip cost as confirmed by Google.
