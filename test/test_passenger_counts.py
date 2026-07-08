# test/test_passenger_counts.py
import unittest
from urllib.parse import unquote
from fast_flights.shopping import _encode_shopping_request
from fast_flights.querying import FlightQuery


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


if __name__ == "__main__":
    unittest.main()
