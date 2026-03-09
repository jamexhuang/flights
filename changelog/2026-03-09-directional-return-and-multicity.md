# 2026-03-09 Directional Return And Multicity Fixes

## Fixed

- `select_flight()` now decodes the selected-flight `tfs` payload from `Flights.select_data` and carries it inside `ReturnQuery`.
- `get_return_flights()` now verifies that the parsed itinerary matches the requested return-leg direction and falls back to an independent one-way query when Google still serves outbound-direction HTML.
- `get_flights_multicity_chained()` no longer repeats outbound-direction segment data on later legs. It now combines:
  - Google's bundled multi-city `total_price` from the RPC path
  - correctly directed per-leg `flights` results from independent one-way searches

## Behavioral Notes

- In `get_return_flights()` fallback mode, `Flights.price` is the one-way price for the requested return leg.
- In `get_flights_multicity_chained()`, `total_price` remains the bundled itinerary price, while per-leg `flights[*].price` values are per-leg one-way prices.

## Verification

- Added unit regressions in `test/test_issue_1_regression.py`.
- Re-ran:
  - `python -m unittest discover -s test -p 'test_issue_1_regression.py'`
  - `python -m unittest discover -s test -p 'test_selected_page_context.py'`
  - `python -m unittest discover -s test -p 'test_seat_regression.py'`
- Added and ran `tmp/release_validate_issue_1.py`, which produced a passing live validation report for:
  - round-trip: `TPE↔LHR`, `MAN↔JFK`, `TPE↔NRT`
  - multi-city chained: `TPE→NRT→TPE`, `TPE→LHR→TPE`, `MAN→JFK→MAN`
