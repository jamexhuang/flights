# fast-flights v3.1.0 — Migration & Usage Guide

This guide covers how to migrate from the upstream `fast-flights` PyPI package to the fork, and documents all available features including **one-way search**, **max stops**, **round-trip with return flights**, and **integrations**.

---

## Migration

### From PyPI to fork

If you were previously using:

```bash
pip install fast-flights
```

Replace with the fork (pointing to the `dev` branch):

```bash
pip install git+https://github.com/jamexhuang/flights.git@dev
```

#### requirements.txt

```diff
- fast-flights
+ fast-flights @ git+https://github.com/jamexhuang/flights.git@dev
```

#### pyproject.toml

```toml
[project]
dependencies = [
    "fast-flights @ git+https://github.com/jamexhuang/flights.git@dev",
]
```

### What's new in v3.1.0

| Feature | Status |
|---------|--------|
| One-way search | ✅ Unchanged |
| Max stops filter | ✅ Unchanged |
| Airline filter | ✅ Unchanged |
| Integrations (BrightData) | ✅ Unchanged |
| **Round-trip return flights** | 🆕 **New** |

> **Backward compatible** — All existing code works without changes. The new return-flight feature is opt-in.

---

## Usage

### Imports

```python
from fast_flights import (
    FlightQuery,        # define a flight leg
    Passengers,         # passenger counts
    create_query,       # build a Query
    get_flights,        # fetch flight results
    select_flight,      # 🆕 select outbound → build ReturnQuery
    get_return_flights,  # 🆕 fetch return flight results
)
```

---

### 1. One-way search

The simplest use case — search for a single direction.

```python
query = create_query(
    flights=[
        FlightQuery(
            date="2026-03-15",       # YYYY-MM-DD
            from_airport="TPE",      # IATA code
            to_airport="NRT",        # IATA code
        ),
    ],
    seat="economy",                  # economy / premium-economy / business / first
    trip="one-way",
    passengers=Passengers(adults=1),
    language="en-US",                # optional, "" = auto
    currency="USD",                  # optional, "" = auto
)

results = get_flights(query)

for flight in results:
    print(f"{flight.airlines} — ${flight.price}")
    for seg in flight.flights:
        print(f"  {seg.from_airport.code} → {seg.to_airport.code}  ({seg.duration} min)")
```

---

### 2. Max stops filter

Limit the number of stops on any query type.

```python
# Per flight leg
FlightQuery(
    date="2026-03-15",
    from_airport="CDG",
    to_airport="TPE",
    max_stops=1,                     # 0 = nonstop, 1 = max 1 stop, etc.
)

# Or globally for all legs
query = create_query(
    flights=[...],
    trip="one-way",
    max_stops=0,                     # applies to all FlightQuery entries
)
```

---

### 3. Airline filter

Restrict results to specific airlines or alliances.

```python
FlightQuery(
    date="2026-03-15",
    from_airport="CDG",
    to_airport="TPE",
    airlines=["KL", "AF"],           # IATA 2-letter codes
)
```

Alliance codes: `STAR_ALLIANCE`, `SKYTEAM`, `ONEWORLD`.

> **Note:** Google currently only applies the airline filter from the **first** `FlightQuery` to the entire search.

---

### 4. Round-trip with return flights 🆕

Google Flights uses a two-step flow for round-trips:
1. **Step 1** — Show outbound (departing) flights
2. **Step 2** — After selecting one, show return flights

`fast-flights` now supports this:

```python
# Step 1: Create round-trip query and fetch outbound flights
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

outbound = get_flights(query)
print(f"Found {len(outbound)} outbound flights")

for i, f in enumerate(outbound[:5]):
    print(f"  {i}. {f.airlines} — €{f.price}")
```

```python
# Step 2: Pick one outbound flight, then fetch return options
chosen = outbound[0]

return_query = select_flight(query, chosen)
returning = get_return_flights(return_query)

print(f"Found {len(returning)} return flights")
for f in returning[:5]:
    print(f"  ↩ {f.airlines} — €{f.price}")
```

#### How it works

Each outbound result has a hidden `select_token` field (a session token from Google). `select_flight()` wraps it into a `ReturnQuery` that includes the `tfu` URL parameter Google needs to show return options.

#### Error handling

```python
if chosen.select_token is None:
    print("No return options (this is a one-way query)")
else:
    return_query = select_flight(query, chosen)
    returning = get_return_flights(return_query)
```

Calling `select_flight()` on a flight without a token raises `ValueError`.

---

### 5. Integrations

All query types (including return flights) work with integrations.

#### Bright Data

```python
from fast_flights.integrations import BrightData

bd = BrightData(api_key="your-key")  # or set BRIGHT_DATA_API_KEY env var

# One-way / outbound
results = get_flights(query, integration=bd)

# Return flights
rq = select_flight(query, results[0])
returning = get_return_flights(rq, integration=bd)
```

#### Proxy

```python
results = get_flights(query, proxy="http://user:pass@proxy:8080")
```

---

## Data models

### `Flights` (each search result)

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Flight type |
| `price` | `int` | Price in the requested currency |
| `airlines` | `list[str]` | Airline names |
| `flights` | `list[SingleFlight]` | Individual flight segments |
| `carbon` | `CarbonEmission` | CO₂ emission data |
| `select_token` | `str \| None` | 🆕 Session token for return flights |
| `select_data` | `str \| None` | 🆕 Encoded selection data |

### `SingleFlight` (each segment)

| Field | Type | Description |
|-------|------|-------------|
| `from_airport` | `Airport` | Departure airport (`.name`, `.code`) |
| `to_airport` | `Airport` | Arrival airport (`.name`, `.code`) |
| `departure` | `SimpleDatetime` | `.date` (y, m, d) + `.time` (h, m) |
| `arrival` | `SimpleDatetime` | Same as above |
| `duration` | `int` | Flight duration in minutes |
| `plane_type` | `str` | Aircraft type |

---

## Full example

```python
from fast_flights import (
    FlightQuery, Passengers, create_query,
    get_flights, select_flight, get_return_flights,
)

# Round-trip: Paris ↔ Taipei
query = create_query(
    flights=[
        FlightQuery(date="2026-03-15", from_airport="CDG", to_airport="TPE", max_stops=1),
        FlightQuery(date="2026-03-19", from_airport="TPE", to_airport="CDG"),
    ],
    seat="economy",
    trip="round-trip",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    currency="EUR",
    language="en-US",
)

# Outbound
outbound = get_flights(query)
print("=== Outbound ===")
for f in outbound[:3]:
    stops = len(f.flights) - 1
    print(f"  {f.airlines} | {f.flights[0].duration}min | {stops} stop(s) | €{f.price}")

# Return
if outbound and outbound[0].select_token:
    rq = select_flight(query, outbound[0])
    returning = get_return_flights(rq)
    print("=== Return ===")
    for f in returning[:3]:
        stops = len(f.flights) - 1
        print(f"  {f.airlines} | {f.flights[0].duration}min | {stops} stop(s) | €{f.price}")
```
