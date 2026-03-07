# Return Flights

`get_return_flights()` is the second step of a round-trip search.

## Supported flow

1. Query outbound options with `get_flights()`
2. Choose one outbound option
3. Build a `ReturnQuery` with `select_flight()`
4. Fetch return options with `get_return_flights()`

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

## API pieces

### `select_flight(query, flight) -> ReturnQuery`

- `query`: the original round-trip `Query`
- `flight`: one outbound `Flights` result with a `select_token`

Raises `ValueError` if the chosen result has no `select_token`.

### `get_return_flights(q, /, *, proxy=None, integration=None) -> MetaList`

- `q`: a `ReturnQuery`
- `proxy`: optional proxy string
- `integration`: optional custom `Integration`

Returns the same parsed `Flights` model as `get_flights()`.

## Integrations

Round-trip return searches work with integrations:

```python
from fast_flights.integrations import BrightData

integration = BrightData(api_key="...")
outbound = get_flights(query, integration=integration)
return_query = select_flight(query, outbound[0])
returning = get_return_flights(return_query, integration=integration)
```

## Boundary with multi-city

`get_return_flights()` is a round-trip API.

Although the first leg of a `trip="multi-city"` query may expose a `select_token`, Google's HTML response for later multi-city legs does not provide the data required for this round-trip return-flight workflow. For multi-city itineraries, use the flows documented in [Multi-city](multicity.md) instead.

## One-way behavior

For `trip="one-way"`, results do not carry usable return-flight tokens. Calling `select_flight()` on such a result raises `ValueError`.
