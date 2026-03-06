# faster-flights — Documentation Index

> A fast, robust Google Flights scraper for Python.
>
> ```sh
> pip install faster-flights
> ```

This directory contains all documentation for `faster-flights`. The full rendered site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) from these Markdown files.

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
| [workaround.md](workaround.md) | 整合搜尋教學（zh-TW） | 單程、來回、多城市的完整使用範例、聯盟篩選、多機場批次查詢 |

---

## Quick links

- **Source code** — [`fast_flights/`](../fast_flights/)
- **Usage example** — [`example.py`](../example.py)
- **Package config** — [`pyproject.toml`](../pyproject.toml)
- **MkDocs config** — [`mkdocs.yml`](../mkdocs.yml)
- **Research Report** — [`test/baggage_research_report.md`](../test/baggage_research_report.md)
- **GitHub** — [jamexhuang/flights](https://github.com/jamexhuang/flights)

---

## CI/CD：保持使用最新版本

在下游專案的 CI/CD 中，可透過以下方式確保每次建置都拉取 `faster-flights` 的最新 `dev` 分支。

### requirements.txt

```
faster-flights @ git+https://github.com/jamexhuang/flights.git@dev
```

> `pip install -r requirements.txt` 時加上 `--upgrade` 確保更新：
>
> ```bash
> pip install --upgrade -r requirements.txt
> ```

### pyproject.toml（使用 pip 安裝）

```toml
[project]
dependencies = [
    "faster-flights @ git+https://github.com/jamexhuang/flights.git@dev",
]
```

### GitHub Actions 範例

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies (always fetch latest faster-flights)
        run: |
          pip install --no-cache-dir \
            "faster-flights @ git+https://github.com/jamexhuang/flights.git@dev"
          pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

> **提示**：`--no-cache-dir` 可避免 pip 使用快取中的舊版本，確保每次都從 Git 拉取最新程式碼。
