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

When Google serves the selected page with the correct reverse-direction SSR payload, those parsed results are returned directly.

When Google still responds with the wrong selected-flight HTML payload, `get_return_flights()` next rebuilds the browser-style selected `tfs` state from the chosen outbound segments and fetches that bundled return page directly.

Only if both HTML paths fail does it fall back to an independent one-way search for the requested return leg so the returned route direction is still correct.

In that last-resort mode, `Flights.price` is the one-way price for the return leg rather than Google's selected round-trip total.

## Experimental browser parity

`get_return_flights()` keeps the stable built-in HTTP/HTML fallback chain above.

If you need an additional browser-assisted fallback for later legs, use `SearchSession` with `browser_fallback=True` and a `browser_provider`:

```python
from fast_flights import (
    PlaywrightBrowserProvider,
    SearchSession,
)

session = SearchSession(
    query,
    mode="rpc-first",
    browser_fallback=True,
    browser_provider=PlaywrightBrowserProvider(),
)

outbound = session.results()
session = session.select(outbound[0])
returning = session.results()
```

That browser path is experimental. It captures the real browser `GetShoppingResults` response for the next leg and parses that response directly.

## Search state vs booking state

`select_flight()` and the selected-page flow expose Google's search-state `tfs` for the next leg.

If you need the final selected-itinerary payload for a Google Flights booking URL, use `build_booking_tfs()` / `build_booking_url()` or `SearchSession.final_booking_tfs` / `SearchSession.booking_url()` after all legs are selected.

## Integrations

Round-trip return searches work with integrations:

```python
from fast_flights.integrations import BrightData

integration = BrightData(api_key="...")
outbound = get_flights(query, integration=integration)
return_query = select_flight(query, outbound[0])
returning = get_return_flights(return_query, integration=integration)
```

Custom integrations are used for the primary HTML fetch path. The rebuilt selected-`tfs` fallback currently uses the built-in client, so if your integration is required to reach Google at all, the final fallback may still be the directional one-way search.

## Boundary with multi-city

`get_return_flights()` is a round-trip API.

Although the first leg of a `trip="multi-city"` query may expose a `select_token`, Google's HTML response for later multi-city legs does not provide the data required for this round-trip return-flight workflow. For multi-city itineraries, use the flows documented in [Multi-city](multicity.md) instead.

## One-way behavior

For `trip="one-way"`, results do not carry usable return-flight tokens. Calling `select_flight()` on such a result raises `ValueError`.
