# Integrations & Proxies

The current API customizes fetching with:

- `integration=` for HTML fetching
- `proxy=` for the built-in HTTP client
- `browser_provider=` for experimental browser-assisted parity in `SearchSession`

## Built-in HTTP fetching

By default, `faster-flights` uses its internal HTTP client:

```python
results = get_flights(query)
```

## Proxy support

Pass `proxy=` when you want the built-in client to route through a proxy.

```python
results = get_flights(query, proxy="http://user:pass@proxy:8080")
```

The same pattern works with:

- `get_flights()`
- `get_return_flights()`
- `get_flights_multicity()`
- `get_flights_multicity_chained()`

## Bright Data integration

```python
from fast_flights import get_flights, get_return_flights, select_flight
from fast_flights.integrations import BrightData

integration = BrightData(api_key="...")

outbound = get_flights(query, integration=integration)
return_query = select_flight(query, outbound[0])
returning = get_return_flights(return_query, integration=integration)
```

`get_flights_multicity()` also supports `integration=` because it runs one-way searches per leg.

## Custom integrations

Implement `Integration.fetch_html()` when you want to bring your own fetching stack.

```python
from fast_flights.integrations.base import Integration


class MyIntegration(Integration):
    def fetch_html(self, q):
        return "...html from your own client..."
```

Then pass it into `get_flights()` or `get_return_flights()`:

```python
results = get_flights(query, integration=MyIntegration())
```

## Experimental browser providers

Browser providers are separate from integrations. They do not replace `fetch_html()`. They provide an optional later-leg fallback for `SearchSession` by capturing the real browser `GetShoppingResults` response.

```python
from fast_flights import PlaywrightBrowserProvider, SearchSession

session = SearchSession(
    query,
    browser_fallback=True,
    browser_provider=PlaywrightBrowserProvider(),
)
```

## Multi-city RPC limitation

Two multi-city flows use Google's RPC endpoint internally:

- `get_flights(create_query(..., trip="multi-city"))`
- `get_flights_multicity_chained()`

Those flows support `proxy=` but do not currently support custom `integration=` overrides.
