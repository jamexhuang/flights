# test/test_passenger_counts.py
import unittest
from unittest.mock import patch
from urllib.parse import unquote
from fast_flights.shopping import _encode_shopping_request
from fast_flights.querying import FlightQuery
from fast_flights import get_flights
from fast_flights.querying import create_query, Passengers


class PassengerCountsTest(unittest.TestCase):
    def _legs(self):
        return [FlightQuery(date="2026-03-15", from_airport="TPE", to_airport="NRT")]

    def test_default_is_single_adult(self):
        body = unquote(_encode_shopping_request(self._legs(), tokens=[]))
        self.assertIn("[1,0,0,0]", body)

    def test_multi_passenger_vector_is_encoded(self):
        body = unquote(
            _encode_shopping_request(self._legs(), tokens=[], passenger_counts=(2, 1, 0, 0))
        )
        self.assertIn("[2,1,0,0]", body)
        self.assertNotIn("[1,0,0,0]", body)


class GetFlightsPassengerThreadingTest(unittest.TestCase):
    def test_get_flights_shopping_passes_passenger_counts(self):
        q = create_query(
            flights=[FlightQuery(date="2026-03-15", from_airport="TPE", to_airport="NRT")],
            trip="one-way",
            passengers=Passengers(adults=2, children=1),
        )
        captured = {}

        def fake_fetch(*args, **kwargs):
            captured["pc"] = kwargs.get("passenger_counts")
            return [], None, "", None

        # shopping is not None forces the shopping branch
        with patch("fast_flights.fetcher.fetch_shopping_results", side_effect=fake_fetch), \
             patch("fast_flights.fetcher._build_default_client", return_value=object()):
            from fast_flights.shopping_options import ShoppingOptions
            get_flights(q, shopping=ShoppingOptions())

        self.assertEqual(captured["pc"], (2, 1, 0, 0))


if __name__ == "__main__":
    unittest.main()
