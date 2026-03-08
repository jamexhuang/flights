# 2026-03-07 Multicity RPC Stability

## Changed

- Updated the default primp fingerprint used by `fast_flights.fetcher` from the stale `chrome_127` profile to `chrome_145`.
- Added an explicit `15s` timeout to the default HTTP client used by `get_flights()`, `fetch_flights_html()`, and `get_flights_multicity_chained()`.
- Aligned the shopping RPC `User-Agent` header with the active browser fingerprint.

## Fixed

- `fetch_shopping_results()` now retries retryable transport failures from `client.post(...)` instead of only retrying empty parsed responses.
- `get_flights_multicity_chained()` no longer depends on an unsupported primp impersonation profile during its default request path.

## Verification

- Re-ran deterministic retry checks with mocked timeout failures and confirmed retries now happen before the final exception is raised.
- Re-ran seat propagation checks to confirm the multicity seat parameter still reaches the RPC payload unchanged.
- Planned live validation remains focused on the previously unstable `business` multicity chained flow.

## Project Cleanup

- Moved ad-hoc diagnostic scripts out of the repository root into local `tmp/test/`.
- Left the tracked `test/` directory in place and only redirected temporary, non-project diagnostics into ignored `tmp/` storage.
