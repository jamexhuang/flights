# Airports & IATA Codes

The public API expects airport inputs as IATA code strings.

```python
from fast_flights import FlightQuery

leg = FlightQuery(
    date="2026-03-31",
    from_airport="TPE",
    to_airport="NRT",
)
```

## Supported input shape

Use three-letter IATA codes such as:

- `TPE` — Taipei Taoyuan
- `TSA` — Taipei Songshan
- `NRT` — Tokyo Narita
- `HND` — Tokyo Haneda
- `JFK` — New York JFK

## Round-trip and multi-city examples

```python
legs = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="TPE"),
]
```

```python
legs = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]
```

## What is not part of the public API

- There is no exported airport-search helper in `fast_flights`.
- There is no exported airport enum that callers should depend on.
- The internal protobuf `Airport` message is not the input type for end users.

If you need airport search, autocomplete, or city-to-airport expansion, provide that lookup in your own application and pass the final IATA codes into `FlightQuery`.
