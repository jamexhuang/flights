# faster-flights — Documentation Index

> A fast, typed Google Flights scraper for Python.
>
> ```sh
> pip install faster-flights
> ```

This directory contains the Markdown source for the public documentation site.

## Pages

| File | Title | Description |
|------|-------|-------------|
| [index.md](index.md) | Getting started | Install, quick start, and the current public API surface |
| [filters.md](filters.md) | Query building | `FlightQuery`, `Passengers`, `create_query()`, seat types, trip types, and filters |
| [airports.md](airports.md) | Airports & IATA codes | How airport inputs work in the public API |
| [return-flights.md](return-flights.md) | Return flights | Round-trip two-step selection with `select_flight()` and `get_return_flights()` |
| [multicity.md](multicity.md) | Multi-city | Supported multi-city workflows and their tradeoffs |
| [baggage.md](baggage.md) | Baggage & amenities | Reverse-engineered payload fields for baggage and amenities |
| [fallbacks.md](fallbacks.md) | Integrations & proxies | `integration=` and `proxy=` in the current API |
| [local.md](local.md) | Custom integrations | Building your own local or browser-backed integration |
| [migration-guide.md](migration-guide.md) | Migration guide | Updating older code and docs to the current API |
| [workaround.md](workaround.md) | 整合搜尋教學（zh-TW） | 單程、來回、多城市、聯盟篩選、多機場批次查詢 |

## Quick links

- **Source code** — [`fast_flights/`](../fast_flights/)
- **Usage example** — [`example.py`](../example.py)
- **Package config** — [`pyproject.toml`](../pyproject.toml)
- **MkDocs config** — [`mkdocs.yml`](../mkdocs.yml)
- **Research report** — [`test/baggage_research_report.md`](../test/baggage_research_report.md)
- **GitHub** — [jamexhuang/flights](https://github.com/jamexhuang/flights)

## CI/CD：保持使用最新版本

在下游專案的 CI/CD 中，可透過以下方式確保每次建置都拉取 `faster-flights` 的最新 `dev` 分支。

### requirements.txt

```text
faster-flights @ git+https://github.com/jamexhuang/flights.git@dev
```

```bash
pip install --upgrade -r requirements.txt
```

### pyproject.toml

```toml
[project]
dependencies = [
    "faster-flights @ git+https://github.com/jamexhuang/flights.git@dev",
]
```

### GitHub Actions

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install --no-cache-dir \
            "faster-flights @ git+https://github.com/jamexhuang/flights.git@dev"
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```
