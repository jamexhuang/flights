import unittest
from unittest.mock import patch

from fast_flights import FlightQuery, Passengers, create_query, select_flight
from fast_flights.fetcher import MulticityLeg, get_flights_multicity_chained, get_return_flights
from fast_flights.model import CarbonEmission, Flights, Airport, SimpleDatetime, SingleFlight
from fast_flights.parser import MetaList


def _segment(frm: str, to: str) -> SingleFlight:
    return SingleFlight(
        from_airport=Airport(name=f"{frm} Airport", code=frm),
        to_airport=Airport(name=f"{to} Airport", code=to),
        departure=SimpleDatetime(date=(2026, 5, 1), time=(9, 0)),
        arrival=SimpleDatetime(date=(2026, 5, 1), time=(12, 0)),
        duration=180,
        plane_type="Test Plane",
        airline_code="TS",
    )


def _results(frm: str, to: str, price: int = 1000) -> MetaList:
    results = MetaList()
    results.append(
        Flights(
            type="one-way",
            price=price,
            airlines=["Test Air"],
            flights=[_segment(frm, to)],
            carbon=CarbonEmission(typical_on_route=0, emission=0),
            select_token="token",
            select_data='["selected-tfs"]',
        )
    )
    return results


class Issue1RegressionTests(unittest.TestCase):
    def setUp(self):
        self.roundtrip_query = create_query(
            flights=[
                FlightQuery(date="2026-05-01", from_airport="TPE", to_airport="NRT"),
                FlightQuery(date="2026-05-08", from_airport="NRT", to_airport="TPE"),
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
        )
        self.outbound_flight = Flights(
            type="one-way",
            price=1000,
            airlines=["Test Air"],
            flights=[_segment("TPE", "NRT")],
            carbon=CarbonEmission(typical_on_route=0, emission=0),
            select_token="selected-token",
            select_data='["selected-tfs"]',
        )

    def test_select_flight_decodes_selected_tfs_and_tracks_leg_index(self):
        selected = select_flight(self.roundtrip_query, self.outbound_flight)

        self.assertEqual(selected.selected_tfs, "selected-tfs")
        self.assertEqual(selected.next_leg_index, 1)
        self.assertIn("tfs=selected-tfs", selected.url())
        self.assertIn("tfu=", selected.url())

    def test_select_flight_increments_leg_index_when_chaining(self):
        selected = select_flight(self.roundtrip_query, self.outbound_flight)
        chained = select_flight(selected, self.outbound_flight)

        self.assertEqual(chained.next_leg_index, 2)

    def test_get_return_flights_uses_ssr_results_when_direction_matches(self):
        selected = select_flight(self.roundtrip_query, self.outbound_flight)
        correct_results = _results("NRT", "TPE", price=2000)

        with patch("fast_flights.fetcher.fetch_flights_html", return_value="<html/>"):
            with patch("fast_flights.fetcher.parse", return_value=correct_results):
                with patch("fast_flights.fetcher.get_flights") as fallback:
                    actual = get_return_flights(selected)

        self.assertIs(actual, correct_results)
        fallback.assert_not_called()

    def test_get_return_flights_falls_back_to_directional_one_way_results(self):
        selected = select_flight(self.roundtrip_query, self.outbound_flight)
        wrong_results = _results("TPE", "NRT", price=1000)
        fallback_results = _results("NRT", "TPE", price=1200)

        with patch("fast_flights.fetcher.fetch_flights_html", return_value="<html/>"):
            with patch("fast_flights.fetcher.parse", return_value=wrong_results):
                with patch("fast_flights.fetcher.get_flights", return_value=fallback_results) as fallback:
                    actual = get_return_flights(selected)

        self.assertIs(actual, fallback_results)
        fallback_query = fallback.call_args.args[0]
        self.assertEqual(fallback_query._flights[0].from_airport, "NRT")
        self.assertEqual(fallback_query._flights[0].to_airport, "TPE")

    def test_get_flights_multicity_chained_uses_directional_results_per_leg(self):
        legs = [
            FlightQuery(date="2026-05-01", from_airport="TPE", to_airport="NRT"),
            FlightQuery(date="2026-05-08", from_airport="NRT", to_airport="TPE"),
        ]
        directional = [
            MulticityLeg(leg_index=0, from_airport="TPE", to_airport="NRT", date="2026-05-01", results=_results("TPE", "NRT", 500)),
            MulticityLeg(leg_index=1, from_airport="NRT", to_airport="TPE", date="2026-05-08", results=_results("NRT", "TPE", 600)),
        ]

        with patch("fast_flights.fetcher.fetch_shopping_results", return_value=(["token"], 999, "", MetaList())):
            with patch("fast_flights.fetcher.get_flights_multicity", return_value=directional):
                actual = get_flights_multicity_chained(
                    legs,
                    seat="economy",
                    language="en-US",
                    currency="USD",
                    delay=0,
                )

        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0].total_price, 999)
        self.assertEqual(actual[1].total_price, 999)
        self.assertEqual(actual[0].tokens, ["token"])
        self.assertEqual(actual[1].tokens, ["token"])
        self.assertEqual(actual[0].flights[0].flights[0].from_airport.code, "TPE")
        self.assertEqual(actual[0].flights[0].flights[0].to_airport.code, "NRT")
        self.assertEqual(actual[1].flights[0].flights[0].from_airport.code, "NRT")
        self.assertEqual(actual[1].flights[0].flights[0].to_airport.code, "TPE")


if __name__ == "__main__":
    unittest.main()
