# fast-flights — Documentation Index

> A fast, robust Google Flights scraper for Python.
>
> ```sh
> pip install fast-flights
> ```

This directory contains all documentation for `fast-flights`. The full rendered site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) from these Markdown files.

---

## Pages

| File | Title | Description |
|------|-------|-------------|
| [index.md](index.md) | Get started | Installation, quick-start, and the story behind the project |
| [filters.md](filters.md) | Filters | `FlightData`, `Passengers`, seat types, and trip types |
| [airports.md](airports.md) | Airports | Using `search_airports()` and the `Airport` enum |
| [return-flights.md](return-flights.md) | Return Flights | Round-trip two-step selection with `select_flight()` / `get_return_flights()` |
| [multicity.md](multicity.md) | Multi-City Flights | `get_flights_multicity_chained()` and manual N-leg chaining |
| [baggage.md](baggage.md) | Baggage & Amenities | Reverse-engineered payload fields for bag inclusion and airline amenities |
| [fallbacks.md](fallbacks.md) | Fallbacks | Playwright serverless fallback modes |
| [local.md](local.md) | Local Playwright | Running Playwright locally as an integration |
| [migration-guide.md](migration-guide.md) | Migration Guide | Upgrading from older API versions |

---

## Quick links

- **Source code** — [`fast_flights/`](../fast_flights/)
- **Usage example** — [`example.py`](../example.py)
- **Package config** — [`pyproject.toml`](../pyproject.toml)
- **MkDocs config** — [`mkdocs.yml`](../mkdocs.yml)
- **GitHub** — [AWeirdDev/flights](https://github.com/AWeirdDev/flights)
