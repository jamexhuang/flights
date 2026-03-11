# v3.5.5 – Browser provider improvements

- Replace Playwright busy-loop polling with `page.wait_for_event("response", ...)` for more efficient browser-side response capture
- Expand `test_browser_provider.py` with comprehensive coverage: dataclass validation, backward-compat aliases, ImportError guard, custom provider subclassing, and `capture_browser_artifacts()` compat helper
