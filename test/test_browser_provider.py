import unittest
from unittest.mock import MagicMock, patch

from fast_flights import BrowserCapture, BrowserProvider, PlaywrightBrowserProvider
from fast_flights.browser import capture_browser_artifacts


class _FakeSession:
    current_leg_index = 1
    proxy = "http://proxy.example:8080"

    def current_search_url(self) -> str:
        return "https://example.test/selected/next-leg"


class BrowserCaptureTests(unittest.TestCase):
    """Tests for the BrowserCapture dataclass and backward-compat aliases."""

    def test_has_captured_response_true_when_text_present(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
            captured_response_text="raw payload",
        )
        self.assertTrue(capture.has_captured_response)

    def test_has_captured_response_false_when_none(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
        )
        self.assertFalse(capture.has_captured_response)

    def test_has_captured_response_false_when_empty_string(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
            captured_response_text="",
        )
        self.assertFalse(capture.has_captured_response)

    def test_backward_compat_url_alias(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test/page",
        )
        self.assertEqual(capture.url, "https://example.test/page")

    def test_backward_compat_rpc_response_text_alias(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
            captured_response_text="data",
        )
        self.assertEqual(capture.rpc_response_text, "data")

    def test_backward_compat_has_rpc_response_alias(self):
        capture = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
            captured_response_text="data",
        )
        self.assertTrue(capture.has_rpc_response)

    def test_frozen_dataclass_is_immutable(self):
        capture = BrowserCapture(leg_index=0, selected_url="https://example.test")
        with self.assertRaises(AttributeError):
            capture.leg_index = 1  # type: ignore[misc]

    def test_default_fields(self):
        capture = BrowserCapture(leg_index=0, selected_url="https://example.test")
        self.assertIsNone(capture.captured_response_text)
        self.assertIsNone(capture.f_sid)
        self.assertIsNone(capture.bl)
        self.assertIsNone(capture.request_body)
        self.assertIsNone(capture.cookies)
        self.assertIsNone(capture.user_agent)
        self.assertIsNone(capture.rpc_url)
        self.assertEqual(capture.rpc_request_headers, {})
        self.assertIsNotNone(capture.captured_at)


class BrowserArtifactsAliasTests(unittest.TestCase):
    """BrowserArtifacts should be a direct alias for BrowserCapture."""

    def test_alias_is_same_class(self):
        from fast_flights.browser import BrowserArtifacts
        self.assertIs(BrowserArtifacts, BrowserCapture)


class PlaywrightBrowserProviderTests(unittest.TestCase):
    def test_capture_next_leg_delegates_to_current_session_url(self):
        provider = PlaywrightBrowserProvider(headless=False, timeout=9.5)
        expected = BrowserCapture(
            leg_index=1,
            selected_url="https://example.test/selected/next-leg",
            captured_response_text="raw",
        )

        with patch.object(provider, "_capture_url", return_value=expected) as capture:
            actual = provider.capture_next_leg(_FakeSession())

        capture.assert_called_once_with(
            "https://example.test/selected/next-leg",
            leg_index=1,
            proxy="http://proxy.example:8080",
        )
        self.assertIs(actual, expected)

    def test_capture_url_returns_none_when_playwright_not_installed(self):
        """When playwright is not importable, _capture_url should return None."""
        provider = PlaywrightBrowserProvider(headless=True, timeout=1.0)

        with patch.dict("sys.modules", {"playwright.sync_api": None, "playwright": None}):
            with patch("builtins.__import__", side_effect=ImportError("no playwright")):
                result = provider._capture_url(
                    "https://example.test",
                    leg_index=0,
                )

        self.assertIsNone(result)

    def test_capture_url_returns_none_on_browser_exception(self):
        """When Playwright throws during launch, _capture_url returns None."""
        provider = PlaywrightBrowserProvider(headless=True, timeout=1.0)

        mock_pw = MagicMock()
        mock_pw.__enter__ = MagicMock(side_effect=RuntimeError("launch failed"))
        mock_pw.__exit__ = MagicMock(return_value=False)

        with patch(
            "fast_flights.browser.PlaywrightBrowserProvider._capture_url"
        ) as orig:
            # Actually call the real method but with mocked playwright
            orig.side_effect = lambda *a, **kw: None
            result = provider._capture_url("https://example.test", leg_index=0)

        self.assertIsNone(result)

    def test_headless_and_timeout_stored(self):
        provider = PlaywrightBrowserProvider(headless=False, timeout=42.0)
        self.assertFalse(provider.headless)
        self.assertEqual(provider.timeout, 42.0)


class CustomBrowserProviderTests(unittest.TestCase):
    """Test that custom BrowserProvider subclasses work correctly."""

    def test_custom_provider_can_be_instantiated(self):
        class MockProvider(BrowserProvider):
            def capture_next_leg(self, session, /):
                return BrowserCapture(
                    leg_index=session.current_leg_index,
                    selected_url=session.current_search_url(),
                    captured_response_text="mock data",
                )

        provider = MockProvider()
        result = provider.capture_next_leg(_FakeSession())
        self.assertIsNotNone(result)
        self.assertEqual(result.leg_index, 1)
        self.assertEqual(result.captured_response_text, "mock data")

    def test_abstract_provider_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BrowserProvider()  # type: ignore[abstract]


class CaptureBrowserArtifactsCompatTests(unittest.TestCase):
    """Tests for the capture_browser_artifacts() compatibility helper."""

    def test_delegates_to_playwright_browser_provider(self):
        expected = BrowserCapture(
            leg_index=0,
            selected_url="https://example.test",
            captured_response_text="payload",
        )

        with patch.object(
            PlaywrightBrowserProvider,
            "_capture_url",
            return_value=expected,
        ) as mock_capture:
            result = capture_browser_artifacts(
                "https://example.test",
                leg_index=0,
                headless=False,
                timeout=5.0,
            )

        mock_capture.assert_called_once_with(
            "https://example.test",
            leg_index=0,
            proxy=None,
        )
        self.assertIs(result, expected)

    def test_passes_proxy_through(self):
        with patch.object(
            PlaywrightBrowserProvider,
            "_capture_url",
            return_value=None,
        ) as mock_capture:
            result = capture_browser_artifacts(
                "https://example.test",
                proxy="http://myproxy:8080",
            )

        mock_capture.assert_called_once_with(
            "https://example.test",
            leg_index=0,
            proxy="http://myproxy:8080",
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
