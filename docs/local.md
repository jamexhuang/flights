# Browser Providers and Custom Integrations

`faster-flights` now has two separate extension points:

- `integration=`: custom HTML fetching
- `browser_provider=`: experimental browser-side network capture for `SearchSession`

They solve different problems and are not interchangeable.

## Install Playwright

The optional extra installs Playwright so you can use the built-in experimental browser provider:

```bash
pip install faster-flights[local]
python -m playwright install chromium
```

## Experimental browser provider

Use `PlaywrightBrowserProvider` when you want `SearchSession` to fall back to a real browser response for later legs.

```python
from fast_flights import (
    FlightQuery,
    Passengers,
    PlaywrightBrowserProvider,
    SearchSession,
    create_query,
)

query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="LHR"),
        FlightQuery(date="2026-04-14", from_airport="LHR", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    language="en-GB",
    currency="GBP",
)

session = SearchSession(
    query,
    mode="rpc-first",
    browser_fallback=True,
    browser_provider=PlaywrightBrowserProvider(),
)
```

The current MVP is response-first:

- it captures the real `GetShoppingResults` response from Chromium
- it parses that response directly
- it does not replay the captured request body yet
- it does not inject captured cookies back into the HTTP client yet

The browser provider is only used for later legs after the normal HTTP/RPC paths fail to return a matching result.

## Custom integrations

Custom integrations still implement HTML fetching only.

```python
from fast_flights import get_flights, get_return_flights
from fast_flights.integrations.base import Integration


class LocalIntegration(Integration):
    def fetch_html(self, q):
        return "...html..."
```

Use it with standard one-way and round-trip flows:

```python
results = get_flights(query, integration=LocalIntegration())
```

```python
returning = get_return_flights(return_query, integration=LocalIntegration())
```

## Custom browser providers

If you want your own browser runtime, implement `BrowserProvider` instead of `Integration`.

```python
from fast_flights import BrowserCapture, BrowserProvider


class MyBrowserProvider(BrowserProvider):
    def capture_next_leg(self, session):
        return BrowserCapture(
            leg_index=session.current_leg_index,
            selected_url=session.current_search_url(),
            captured_response_text="...raw shopping RPC response...",
        )
```
