import unittest
from unittest.mock import patch, MagicMock
from fast_flights.parser import MetaList
from fast_flights.model import ResponseDiagnostics
from fast_flights.shopping import fetch_shopping_results
from fast_flights.querying import FlightQuery


class DiagnosticsShapeTest(unittest.TestCase):
    def test_metalist_defaults_diagnostics_none(self):
        self.assertIsNone(MetaList().diagnostics)

    def test_can_attach_diagnostics(self):
        m = MetaList()
        m.diagnostics = ResponseDiagnostics(status="empty", http_status=200, elapsed_ms=12.5)
        self.assertEqual(m.diagnostics.status, "empty")
        self.assertEqual(m.diagnostics.attempts, 1)  # default


def _resp(status_code, text=""):
    r = MagicMock()
    r.status_code = status_code
    r.text = text
    return r


class ShoppingDiagnosticsTest(unittest.TestCase):
    def _legs(self):
        return [FlightQuery(date="2026-03-15", from_airport="TPE", to_airport="NRT")]

    def _client(self, response):
        c = MagicMock()
        c.post.return_value = response
        c.get.return_value = _resp(200)  # warmup
        return c

    def test_non200_403_is_blocked_and_returns_metalist(self):
        client = self._client(_resp(403))
        *_, flights = fetch_shopping_results(client, self._legs(), tokens=[], max_retries=0)
        from fast_flights.parser import MetaList
        self.assertIsInstance(flights, MetaList)
        self.assertEqual(len(flights), 0)
        self.assertEqual(flights.diagnostics.status, "blocked")
        self.assertEqual(flights.diagnostics.http_status, 403)

    def test_non200_500_is_http_error(self):
        client = self._client(_resp(500))
        *_, flights = fetch_shopping_results(client, self._legs(), tokens=[], max_retries=0)
        self.assertEqual(flights.diagnostics.status, "http_error")
        self.assertEqual(flights.diagnostics.http_status, 500)

    def test_200_empty_is_empty_status(self):
        client = self._client(_resp(200, text=")]}'\n\n5\n[[\"wrb.fr\"]]\n"))
        *_, flights = fetch_shopping_results(client, self._legs(), tokens=[], max_retries=0)
        self.assertEqual(flights.diagnostics.status, "empty")
        self.assertEqual(flights.diagnostics.http_status, 200)


from fast_flights import get_flights
from fast_flights.shopping_options import ShoppingOptions
from fast_flights.querying import create_query


class GetFlightsDiagnosticsPreservedTest(unittest.TestCase):
    def test_blocked_diagnostics_reach_caller(self):
        q = create_query(
            flights=[FlightQuery(date="2026-03-15", from_airport="TPE", to_airport="NRT")],
            trip="one-way",
        )
        blocked = MetaList()
        blocked.diagnostics = ResponseDiagnostics(status="blocked", http_status=429)
        with patch("fast_flights.fetcher.fetch_shopping_results",
                   return_value=([], None, "", blocked)), \
             patch("fast_flights.fetcher._build_default_client", return_value=object()):
            result = get_flights(q, shopping=ShoppingOptions())
        self.assertEqual(len(result), 0)
        self.assertEqual(result.diagnostics.status, "blocked")  # NOT discarded


if __name__ == "__main__":
    unittest.main()
