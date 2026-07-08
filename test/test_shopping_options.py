import json
import urllib.parse
import unittest
from unittest.mock import patch

from fast_flights import FlightQuery, Passengers, ShoppingOptions, create_query, get_flights
from fast_flights.querying import SelectedSegment
from fast_flights.parser import MetaList
from fast_flights.shopping import _encode_shopping_request


class ShoppingOptionsTests(unittest.TestCase):
    def test_tfu_matches_live_google_mapping(self):
        self.assertEqual(ShoppingOptions().tfu(), "EgoIARAAGAAgASgO")
        self.assertEqual(ShoppingOptions(result_sort="price").tfu(), "EgoIAhAAGAAgASgO")
        self.assertEqual(
            ShoppingOptions(result_sort="departure_time").tfu(),
            "EgoIAxAAGAAgASgO",
        )
        self.assertEqual(
            ShoppingOptions(result_sort="arrival_time").tfu(),
            "EgoIBBAAGAAgASgO",
        )
        self.assertEqual(
            ShoppingOptions(result_sort="duration").tfu(),
            "EgoIBRAAGAAgASgO",
        )
        self.assertEqual(
            ShoppingOptions(result_sort="emissions").tfu(),
            "EgoIBhAAGAAgASgO",
        )
        self.assertEqual(
            ShoppingOptions(ranking_mode="cheapest").tfu(),
            "EgoIARAAGAAgAigP",
        )

    def test_encode_shopping_request_uses_live_sort_tuple(self):
        legs = [
            FlightQuery(date="2026-05-10", from_airport="LHR", to_airport="TPE"),
            FlightQuery(date="2026-05-18", from_airport="TPE", to_airport="LHR"),
        ]

        encoded = _encode_shopping_request(
            legs,
            [],
            shopping=ShoppingOptions(result_sort="duration", ranking_mode="cheapest"),
        )

        req = urllib.parse.parse_qs(encoded.rstrip("&"))
        body = json.loads(urllib.parse.unquote(req["f.req"][0]))
        inner = json.loads(body[1])

        self.assertEqual(inner[-4:], [5, 0, 0, 2])

    def test_encode_shopping_request_uses_live_selected_return_shape(self):
        legs = [
            FlightQuery(date="2026-04-01", from_airport="TPE", to_airport="LHR"),
            FlightQuery(date="2026-04-14", from_airport="LHR", to_airport="TPE"),
        ]
        selected_legs = (
            (
                SelectedSegment("TPE", "2026-04-01", "AUH", "EY", "899"),
                SelectedSegment("AUH", "2026-04-02", "LHR", "EY", "61"),
            ),
        )

        encoded = _encode_shopping_request(
            legs,
            ["TOKEN-1"],
            shopping=ShoppingOptions(result_sort="price", ranking_mode="cheapest"),
            selected_legs=selected_legs,
        )

        req = urllib.parse.parse_qs(encoded.rstrip("&"))
        body = json.loads(urllib.parse.unquote(req["f.req"][0]))
        inner = json.loads(body[1])

        self.assertEqual(inner[0], [None, "TOKEN-1"])
        self.assertEqual(
            inner[1][13][0][8],
            [
                ["TPE", "2026-04-01", "AUH", None, "EY", "899"],
                ["AUH", "2026-04-02", "LHR", None, "EY", "61"],
            ],
        )
        self.assertEqual(inner[-4:], [2, 0, 0, 2])

    def test_get_flights_preserves_html_default_and_uses_rpc_when_shopping_is_set(self):
        query = create_query(
            flights=[FlightQuery(date="2026-05-10", from_airport="LHR", to_airport="TPE")],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en",
            currency="GBP",
        )
        sentinel = MetaList()

        with patch("fast_flights.fetcher.fetch_flights_html", return_value="<html></html>") as html_mock:
            with patch("fast_flights.fetcher.parse", return_value=sentinel) as parse_mock:
                with patch("fast_flights.fetcher.fetch_shopping_results") as rpc_mock:
                    result = get_flights(query)

        self.assertIs(result, sentinel)
        html_mock.assert_called_once()
        parse_mock.assert_called_once()
        rpc_mock.assert_not_called()

        with patch("fast_flights.fetcher.fetch_shopping_results", return_value=([], 100, "", [])) as rpc_mock:
            with patch("fast_flights.fetcher.fetch_flights_html") as html_mock:
                get_flights(query, shopping=ShoppingOptions())

        rpc_mock.assert_called_once()
        html_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
