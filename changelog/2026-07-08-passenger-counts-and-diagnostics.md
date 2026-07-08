# v3.8.0 – Shopping passenger counts & response diagnostics

- **fix(shopping):** the shopping RPC now encodes **real passenger counts**
  instead of a hardcoded single adult. Threaded through `get_flights`,
  `get_return_flights`, and `get_flights_multicity_chained` (which gains a
  `passengers` parameter). `get_flights_multicity` was already correct.
- **feat: `MetaList.diagnostics`** (`ResponseDiagnostics`) exposes per-call
  `status` (`ok` / `empty` / `http_error` / `blocked`), `http_status`,
  `elapsed_ms`, `attempts`, and `used_default_rpc_params`. A shopping non-200
  now returns an empty result carrying `status="blocked"` (403/429) or
  `"http_error"` instead of a silent empty list — callers can tell a soft-block
  apart from a genuine empty result without guessing.
- **feat:** silent `fast_flights` module logging (`NullHandler`) at internal
  exception-swallow sites; enable the `fast_flights` logger at `DEBUG` to see
  the root cause of retries, warmup, and parse failures.
- **ci:** the mocked test suite now runs on every push and pull request.

All changes are additive and non-breaking: new parameters default to the prior
behavior, `MetaList` remains a `list`, and existing raised exceptions are
unchanged.
