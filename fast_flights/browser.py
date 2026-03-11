"""Experimental browser parity helpers.

The stable scraping path remains HTTP/RPC-first. This module provides an
optional browser-assisted fallback that captures the real shopping RPC response
from a live Chromium page and feeds that payload back into the existing parser.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import SearchSession


@dataclass(frozen=True)
class BrowserCapture:
    """Captured browser-side shopping state for a specific leg."""

    leg_index: int
    selected_url: str
    captured_response_text: str | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    f_sid: str | None = None
    bl: str | None = None
    request_body: bytes | None = None
    cookies: str | None = None
    user_agent: str | None = None
    rpc_url: str | None = None
    rpc_request_headers: dict[str, str] = field(default_factory=dict)

    @property
    def has_captured_response(self) -> bool:
        return bool(self.captured_response_text)

    # Backward-compatible aliases for the earlier BrowserArtifacts prototype.
    @property
    def url(self) -> str:
        return self.selected_url

    @property
    def rpc_response_text(self) -> str | None:
        return self.captured_response_text

    @property
    def has_rpc_response(self) -> bool:
        return self.has_captured_response


BrowserArtifacts = BrowserCapture


class BrowserProvider(ABC):
    """Experimental provider that can capture next-leg shopping responses."""

    @abstractmethod
    def capture_next_leg(self, session: "SearchSession", /) -> BrowserCapture | None:
        """Capture the browser-side shopping response for ``session.current_leg_index``."""


class PlaywrightBrowserProvider(BrowserProvider):
    """Browser provider backed by Playwright's sync Chromium API."""

    def __init__(self, *, headless: bool = True, timeout: float = 30.0) -> None:
        self.headless = headless
        self.timeout = timeout

    def capture_next_leg(self, session: "SearchSession", /) -> BrowserCapture | None:
        return self._capture_url(
            session.current_search_url(),
            leg_index=session.current_leg_index,
            proxy=session.proxy,
        )

    def _capture_url(
        self,
        url: str,
        *,
        leg_index: int,
        proxy: str | None = None,
    ) -> BrowserCapture | None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None

        rpc_path = "/GetShoppingResults"

        try:
            with sync_playwright() as pw:
                launch_kwargs: dict[str, object] = {"headless": self.headless}
                if proxy:
                    launch_kwargs["proxy"] = {"server": proxy}

                browser = pw.chromium.launch(**launch_kwargs)
                context = browser.new_context(
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                page = context.new_page()

                pending_requests: list = []
                pending_responses: list = []

                def on_request(req) -> None:  # type: ignore[no-untyped-def]
                    if rpc_path in req.url and not pending_requests:
                        pending_requests.append(req)

                def on_response(resp) -> None:  # type: ignore[no-untyped-def]
                    if rpc_path in resp.url and not pending_responses:
                        pending_responses.append(resp)

                page.on("request", on_request)
                page.on("response", on_response)

                try:
                    page.goto(
                        url,
                        timeout=int(self.timeout * 1000),
                        wait_until="domcontentloaded",
                    )
                except Exception:
                    # The page can still dispatch the shopping RPC even if
                    # navigation times out on slow or noisy networks.
                    pass

                # Wait for the first shopping RPC response using Playwright's
                # built-in predicate-based wait instead of busy-polling.
                if not pending_responses:
                    try:
                        resp = page.wait_for_event(
                            "response",
                            predicate=lambda r: rpc_path in r.url,
                            timeout=self.timeout * 1000,
                        )
                        pending_responses.append(resp)
                    except Exception:
                        pass

                captured_response: str | None = None
                captured_rpc_url: str | None = None
                captured_request_body: bytes | None = None
                captured_request_headers: dict[str, str] = {}

                if pending_responses:
                    response = pending_responses[0]
                    captured_rpc_url = response.url
                    try:
                        captured_response = response.text()
                    except Exception:
                        pass

                if pending_requests:
                    request = pending_requests[0]
                    try:
                        captured_request_body = request.post_data_buffer
                        captured_request_headers = dict(request.headers)
                    except Exception:
                        pass

                cookie_str: str | None = None
                try:
                    cookies = context.cookies()
                    cookie_str = "; ".join(
                        f"{cookie['name']}={cookie['value']}" for cookie in cookies
                    ) or None
                except Exception:
                    pass

                user_agent: str | None = None
                try:
                    user_agent = page.evaluate("navigator.userAgent")
                except Exception:
                    pass

                f_sid: str | None = None
                try:
                    f_sid = page.evaluate("window.WIZ_global_data?.FdrFJe ?? null")
                except Exception:
                    pass

                bl: str | None = None
                try:
                    bl = page.evaluate("window.WIZ_global_data?.cfb2h ?? null")
                except Exception:
                    pass

                browser.close()

            return BrowserCapture(
                leg_index=leg_index,
                selected_url=url,
                captured_response_text=captured_response,
                captured_at=datetime.now(timezone.utc),
                f_sid=f_sid,
                bl=bl,
                request_body=captured_request_body,
                cookies=cookie_str,
                user_agent=user_agent,
                rpc_url=captured_rpc_url,
                rpc_request_headers=captured_request_headers,
            )
        except Exception:
            return None


def capture_browser_artifacts(
    url: str,
    *,
    leg_index: int = 0,
    headless: bool = True,
    timeout: float = 30.0,
    proxy: str | None = None,
) -> BrowserCapture | None:
    """Compatibility helper for one-off Playwright captures by URL."""

    provider = PlaywrightBrowserProvider(headless=headless, timeout=timeout)
    return provider._capture_url(url, leg_index=leg_index, proxy=proxy)


__all__ = [
    "BrowserArtifacts",
    "BrowserCapture",
    "BrowserProvider",
    "PlaywrightBrowserProvider",
    "capture_browser_artifacts",
]
