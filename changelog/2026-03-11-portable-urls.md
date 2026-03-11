# v3.5.6 – Portable ReturnQuery URLs

- **Fix URL Portability:** `ReturnQuery.url()` and `SearchSession.current_search_tfs` now prioritize generating a complete, shareable Google Flights booking `tfs` string (via `build_booking_tfs()`) instead of outputting the raw, session-dependent `selected_tfs` fragment. This resolves an issue where URLs generated mid-selection would route to the generic Flights landing page if opened in a new browser session or without the original session cookies.
