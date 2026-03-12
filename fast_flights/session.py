from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .browser import BrowserCapture, BrowserProvider
from .fetcher import (
    GoogleFlightsDataServiceRequest,
    _build_default_client,
    _get_bundled_leg_results,
    _get_directional_leg_results,
    _get_selected_html_results,
    _query_seat_name,
    _results_match_leg,
    get_flights,
    get_return_flights,
    get_selected_flight_page,
)
from .integrations.base import Integration
from .parser import MetaList
from .querying import (
    Query,
    ReturnQuery,
    build_booking_tfs,
    build_booking_url,
    select_flight,
)
from .shopping_options import ShoppingOptions
from .shopping import _extract_full_flights_list, fetch_shopping_results


SearchMode = Literal["rpc-first", "ssr-first"]


@dataclass(frozen=True)
class ShoppingContext:
    f_sid: str | None = None
    bl: str | None = None
    referer: str | None = None
    data_service_requests: dict[str, GoogleFlightsDataServiceRequest] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class SearchSession:
    """Immutable chained-search session for round-trip and multi-city flows."""

    query: Query
    return_query: ReturnQuery | None = None
    mode: SearchMode = "rpc-first"
    proxy: str | None = None
    integration: Integration | None = None
    browser_provider: BrowserProvider | None = None
    browser_fallback: bool = False
    shopping: ShoppingOptions | None = None
    shopping_context: ShoppingContext = field(default_factory=ShoppingContext)

    def __post_init__(self) -> None:
        if self.mode not in ("rpc-first", "ssr-first"):
            raise ValueError(f"Unsupported search mode: {self.mode}")
        if not self.query._flights or len(self.query._flights) < 2:
            raise ValueError("SearchSession requires a round-trip or multi-city query with at least 2 legs.")

    @property
    def total_legs(self) -> int:
        return len(self.query._flights or [])

    @property
    def current_leg_index(self) -> int:
        if self.return_query is None:
            return 0
        return self.return_query.next_leg_index

    @property
    def selection_tokens(self) -> tuple[str, ...]:
        if self.return_query is None:
            return ()
        return self.return_query.selection_tokens

    @property
    def selected_legs(self) -> tuple[tuple, ...]:
        if self.return_query is None:
            return ()
        return self.return_query.selected_legs

    @property
    def is_complete(self) -> bool:
        return self.current_leg_index >= self.total_legs

    @property
    def current_search_tfs(self) -> str:
        if self.return_query is not None:
            return build_booking_tfs(self.query, self.selected_legs) or self.return_query.selected_tfs or self.query.to_str()
        return self.query.to_str()

    @property
    def final_booking_tfs(self) -> str | None:
        if not self.is_complete:
            return None
        return build_booking_tfs(self.query, self.selected_legs)

    def current_search_url(self) -> str:
        if self.return_query is not None:
            return self.return_query.url()
        return self.query.url()

    def booking_url(self) -> str | None:
        if not self.is_complete:
            return None
        return build_booking_url(self.query, self.selected_legs)

    def results(self) -> MetaList:
        if self.is_complete:
            raise ValueError("All legs have already been selected for this session.")

        if self.mode == "rpc-first":
            rpc_results = self._rpc_results()
            if rpc_results is not None:
                return rpc_results

            html_results = self._html_results()
            if html_results is not None:
                return html_results
        else:
            html_results = self._html_results()
            if html_results is not None:
                return html_results

            rpc_results = self._rpc_results()
            if rpc_results is not None:
                return rpc_results

        browser_results = self._browser_results()
        if browser_results is not None:
            return browser_results

        if self.shopping is not None:
            raise ValueError("Could not fetch exact shopping results for the requested session state.")

        if self.current_leg_index == 0:
            return get_flights(
                self.query,
                proxy=self.proxy,
                integration=self.integration,
                shopping=self.shopping,
            )
        return _get_directional_leg_results(
            self.query,
            self.current_leg_index,
            proxy=self.proxy,
            integration=self.integration,
        )

    def select(self, flight) -> "SearchSession":
        if self.is_complete:
            raise ValueError("All legs have already been selected for this session.")

        source_query: Query | ReturnQuery = self.return_query or self.query
        fallback_return_query = select_flight(source_query, flight)
        selected_page = None
        try:
            selected_page = get_selected_flight_page(
                source_query,
                flight,
                proxy=self.proxy,
                integration=self.integration,
            )
        except Exception:
            pass

        if selected_page is None:
            return SearchSession(
                query=self.query,
                return_query=fallback_return_query,
                mode=self.mode,
                proxy=self.proxy,
                integration=self.integration,
                browser_provider=self.browser_provider,
                browser_fallback=self.browser_fallback,
                shopping=self.shopping,
                shopping_context=self.shopping_context,
            )

        next_context = ShoppingContext(
            f_sid=selected_page.f_sid or self.shopping_context.f_sid,
            bl=selected_page.bl or self.shopping_context.bl,
            referer=selected_page.url,
            data_service_requests=selected_page.data_service_requests or self.shopping_context.data_service_requests,
        )
        return SearchSession(
            query=self.query,
            return_query=selected_page.return_query,
            mode=self.mode,
            proxy=self.proxy,
            integration=self.integration,
            browser_provider=self.browser_provider,
            browser_fallback=self.browser_fallback,
            shopping=self.shopping,
            shopping_context=next_context,
        )

    def _expected_leg(self):
        return self.query._flights[self.current_leg_index]

    def _rpc_results(self) -> MetaList | None:
        try:
            client = _build_default_client(proxy=self.proxy)
            _, _, _, flights_found = fetch_shopping_results(
                client=client,
                legs=self.query._flights or [],
                tokens=list(self.selection_tokens),
                shopping=self.shopping,
                language=self.query.language if self.query.language else "en-US",
                currency=self.query.currency if self.query.currency else "USD",
                seat=_query_seat_name(self.query),
                f_sid=self.shopping_context.f_sid,
                bl=self.shopping_context.bl,
                referer=self.shopping_context.referer or self.current_search_url(),
            )
        except Exception:
            return None
        if flights_found and _results_match_leg(flights_found, self._expected_leg()):
            return flights_found
        return None

    def _browser_results(self) -> MetaList | None:
        if (
            not self.browser_fallback
            or self.browser_provider is None
            or self.current_leg_index == 0
        ):
            return None

        try:
            capture: BrowserCapture | None = self.browser_provider.capture_next_leg(self)
        except Exception:
            return None

        if capture is None or not capture.has_captured_response:
            return None

        response_text = capture.captured_response_text
        if not response_text:
            return None

        flights = _extract_full_flights_list(response_text, shopping=self.shopping, source="browser-capture")
        if flights and _results_match_leg(flights, self._expected_leg()):
            return flights
        return None

    def _html_results(self) -> MetaList | None:
        expected_leg = self._expected_leg()
        if self.current_leg_index == 0:
            try:
                results = get_flights(
                    self.query,
                    proxy=self.proxy,
                    integration=self.integration,
                    shopping=self.shopping,
                )
            except Exception:
                return None
            if _results_match_leg(results, expected_leg):
                return results
            return None

        if self.return_query is None:
            return None

        if self.shopping is not None:
            try:
                return get_return_flights(
                    self.return_query,
                    proxy=self.proxy,
                    integration=self.integration,
                    shopping=self.shopping,
                )
            except Exception:
                return None

        selected_results = _get_selected_html_results(
            self.return_query,
            expected_leg,
            proxy=self.proxy,
            integration=self.integration,
        )
        if selected_results is not None:
            return selected_results

        if self.integration is None:
            bundled_results = _get_bundled_leg_results(self.return_query, proxy=self.proxy)
            if bundled_results is not None and _results_match_leg(bundled_results, expected_leg):
                return bundled_results

        return None
