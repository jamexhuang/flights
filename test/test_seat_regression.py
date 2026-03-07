import unittest
from unittest.mock import patch

from fast_flights import FlightQuery, Passengers, create_query
from fast_flights.fetcher import (
    get_flights,
    get_flights_multicity,
    get_flights_multicity_chained,
)
from fast_flights.parser import MetaList
from fast_flights.querying import SEAT_LOOKUP


class _DummyClient:
    def __init__(self, *args, **kwargs):
        pass


class SeatRegressionTests(unittest.TestCase):
    def setUp(self):
        self.passengers = Passengers(adults=1)
        self.one_way = [
            FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        ]
        self.multi_city = [
            FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
            FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
            FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
        ]

    def test_create_query_maps_seat_to_protobuf_enum(self):
        for seat, expected in SEAT_LOOKUP.items():
            with self.subTest(seat=seat):
                query = create_query(
                    flights=self.one_way,
                    trip="one-way",
                    seat=seat,
                    passengers=self.passengers,
                )
                self.assertEqual(query.seat, expected)

    def test_get_flights_multicity_query_reconstructs_original_seat_string(self):
        def make_fake_fetch(expected_seat):
            def fake_fetch_shopping_results(
                *,
                client,
                legs,
                tokens,
                language,
                currency,
                seat,
                max_retries=2,
            ):
                self.assertEqual(seat, expected_seat)
                self.assertEqual(len(legs), len(self.multi_city))
                return [], None, "", MetaList()

            return fake_fetch_shopping_results

        for seat in SEAT_LOOKUP:
            with self.subTest(seat=seat):
                query = create_query(
                    flights=self.multi_city,
                    trip="multi-city",
                    seat=seat,
                    passengers=self.passengers,
                    language="en-US",
                    currency="USD",
                )
                with patch("fast_flights.fetcher.Client", _DummyClient):
                    with patch(
                        "fast_flights.fetcher.fetch_shopping_results",
                        side_effect=make_fake_fetch(seat),
                    ):
                        results = get_flights(query)
                self.assertEqual(len(results), 0)

    def test_get_flights_multicity_chained_forwards_seat_argument(self):
        def make_fake_fetch(expected_seat):
            def fake_fetch_shopping_results(
                *,
                client,
                legs,
                tokens,
                language,
                currency,
                seat,
                max_retries=2,
            ):
                self.assertEqual(seat, expected_seat)
                self.assertEqual(len(legs), len(self.multi_city))
                return ["token"], 999, "", MetaList()

            return fake_fetch_shopping_results

        for seat in SEAT_LOOKUP:
            with self.subTest(seat=seat):
                with patch("fast_flights.fetcher.Client", _DummyClient):
                    with patch(
                        "fast_flights.fetcher.fetch_shopping_results",
                        side_effect=make_fake_fetch(seat),
                    ):
                        results = get_flights_multicity_chained(
                            self.multi_city,
                            seat=seat,
                            language="en-US",
                            currency="USD",
                        )
                self.assertEqual(len(results), len(self.multi_city))
                self.assertEqual(results[0].tokens, ["token"])
                self.assertEqual(results[0].total_price, 999)

    def test_get_flights_multicity_builds_each_leg_with_same_seat(self):
        for seat, expected in SEAT_LOOKUP.items():
            seen = []

            def fake_get_flights(query, proxy=None, integration=None):
                seen.append(query.seat)
                return MetaList()

            with self.subTest(seat=seat):
                with patch("fast_flights.fetcher.get_flights", side_effect=fake_get_flights):
                    results = get_flights_multicity(
                        self.multi_city,
                        seat=seat,
                        passengers=self.passengers,
                        language="en-US",
                        currency="USD",
                        delay=0,
                    )
                self.assertEqual(len(results), len(self.multi_city))
                self.assertEqual(seen, [expected] * len(self.multi_city))


if __name__ == "__main__":
    unittest.main()
