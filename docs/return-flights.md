# Return Flights

For **round-trip** searches, Google Flights uses a two-step selection flow:

1. You see outbound (departing) flight options
2. You pick one → Google shows return flight options with combined prices

`fast-flights` mirrors this flow with `select_flight()` and `get_return_flights()`.

## Quick start

```python
from fast_flights import (
    FlightQuery, Passengers,
    create_query, get_flights,
    select_flight, get_return_flights,
)

# 1️⃣ Create a round-trip query
query = create_query(
    flights=[
        FlightQuery(date="2026-03-15", from_airport="CDG", to_airport="TPE"),
        FlightQuery(date="2026-03-19", from_airport="TPE", to_airport="CDG"),
    ],
    seat="economy",
    trip="round-trip",
    passengers=Passengers(adults=1),
    currency="EUR",
)

# 2️⃣ Fetch outbound flights
outbound = get_flights(query)

for i, flight in enumerate(outbound[:5]):
    print(f"{i}. {flight.airlines} — €{flight.price}")

# 3️⃣ Select an outbound flight and fetch return options
chosen = outbound[0]
return_query = select_flight(query, chosen)
returning = get_return_flights(return_query)

for flight in returning[:5]:
    print(f"  ↩ {flight.airlines} — €{flight.price}")
```

## How it works

Each outbound `Flights` result contains two hidden fields
(set to `repr=False` so they won't clutter your output):

| Field | Type | Description |
|-------|------|-------------|
| `select_token` | `str \| None` | Session token from Google (used for the `tfu` URL parameter) |
| `select_data`  | `str \| None` | Encoded flight selection (used for the `tfs` URL parameter) |

When you call `select_flight(query, flight)`, it:

1. Takes the `select_token` from the chosen flight
2. Wraps it in a Protobuf envelope to build the `tfu` parameter
3. Returns a `ReturnQuery` that includes both the original `tfs` and the new `tfu`

`get_return_flights()` then fetches and parses the return flights page using the exact same parser as outbound flights.

## API reference

### `select_flight(query, flight) → ReturnQuery`

Build a return-flight query from the original query and a selected outbound flight.

**Args:**

- `query` (`Query`) — The original round-trip query from `create_query()`
- `flight` (`Flights`) — A flight result from `get_flights()` that has a valid `select_token`

**Raises:** `ValueError` if the flight has no `select_token`.

---

### `get_return_flights(q, /, *, proxy=None, integration=None) → MetaList`

Fetch return flight options.

**Args:**

- `q` (`ReturnQuery`) — Created by `select_flight()`
- `proxy` (`str`, optional) — HTTP proxy
- `integration` (`Integration`, optional) — e.g. `BrightData()`

**Returns:** A `MetaList` of `Flights` (same type as `get_flights()`).

---

### `ReturnQuery`

A dataclass wrapping the original `Query` with a `tfu` session token.

| Method | Description |
|--------|-------------|
| `.params()` | Returns `dict` with `tfs`, `hl`, `curr`, and `tfu` keys |
| `.url()` | Full Google Flights URL including `tfu` parameter |

## With integrations

Return flights work with all integrations (e.g. Bright Data):

```python
from fast_flights.integrations import BrightData

bd = BrightData(api_key="...")

outbound = get_flights(query, integration=bd)
rq = select_flight(query, outbound[0])
returning = get_return_flights(rq, integration=bd)
```

## One-way flights

For `trip="one-way"` queries, `select_token` will be `None` and you don't need (or can) call `select_flight()`. The API is fully backward-compatible — one-way usage is unchanged.

## Error handling

```python
flight = outbound[0]

if flight.select_token is None:
    print("No return flights available (one-way query?)")
else:
    rq = select_flight(query, flight)
    returning = get_return_flights(rq)
```

If you call `select_flight()` on a flight without a token, it raises `ValueError`:

```
ValueError: The selected flight has no select_token.
Make sure you are using a round-trip query and the
parser extracted the token correctly.
```
