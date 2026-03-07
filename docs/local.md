# Custom Integrations

If you need browser-rendered HTML or a custom local fetch stack, build your own `Integration`.

## Important boundary

`faster-flights` does not ship a built-in local fetch flag or Playwright mode in the current public API.

The optional extra below only installs Playwright so you can use it in your own integration code:

```bash
pip install faster-flights[local]
python -m playwright install chromium
```

## Minimal integration skeleton

```python
from fast_flights import get_flights, get_return_flights
from fast_flights.integrations.base import Integration


class LocalIntegration(Integration):
    def fetch_html(self, q):
        # Return the final Google Flights HTML for q.
        return "...html..."
```

Use it with standard one-way and round-trip flows:

```python
results = get_flights(query, integration=LocalIntegration())
```

```python
returning = get_return_flights(return_query, integration=LocalIntegration())
```

## Example shape for a browser-backed integration

```python
from fast_flights.fetcher import URL
from playwright.sync_api import sync_playwright
from fast_flights.integrations.base import Integration


class PlaywrightIntegration(Integration):
    def fetch_html(self, q):
        url = URL + "?q=" + q if isinstance(q, str) else q.url()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
```

This is user-owned integration code, not a built-in mode of the package.
