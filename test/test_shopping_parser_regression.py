import json
import unittest

from fast_flights.querying import FlightQuery, Passengers, SelectedSegment, build_booking_tfs, build_booking_url, create_query
from fast_flights.shopping import _extract_full_flights_list


def _single_flight(
    frm: str,
    to: str,
    *,
    dep_date: tuple[int, int, int],
    arr_date: tuple[int, int, int],
    dep_time: tuple[int, int],
    arr_time: tuple[int, int],
    airline_code: str,
    flight_number: str,
) -> list:
    single = [None] * 23
    single[3] = frm
    single[4] = f"{frm} Airport"
    single[5] = f"{to} Airport"
    single[6] = to
    single[8] = list(dep_time)
    single[10] = list(arr_time)
    single[11] = 180
    single[17] = "Test Plane"
    single[20] = list(dep_date)
    single[21] = list(arr_date)
    single[22] = [airline_code, flight_number]
    return single


def _flight_entry(
    *,
    price: int,
    airline_name: str,
    airline_code: str,
    select_token: str,
    select_data: str,
    segments: list[list],
) -> list:
    flight = [None] * 23
    flight[0] = "one-way"
    flight[1] = [airline_name]
    flight[2] = segments
    extras = [None] * 9
    extras[7] = 100
    extras[8] = 120
    flight[22] = extras

    entry = [None] * 9
    entry[0] = flight
    entry[1] = [[None, price], select_token]
    entry[8] = select_data
    return entry


class ShoppingParserRegressionTests(unittest.TestCase):
    def test_extract_full_flights_list_keeps_all_segments_and_dedupes_top_results(self):
        outbound = _flight_entry(
            price=347,
            airline_name="China Eastern",
            airline_code="MU",
            select_token="token-1",
            select_data='["selected-tfs-1"]',
            segments=[
                _single_flight(
                    "LHR",
                    "PVG",
                    dep_date=(2026, 5, 3),
                    arr_date=(2026, 5, 4),
                    dep_time=(21, 20),
                    arr_time=(17, 0),
                    airline_code="MU",
                    flight_number="552",
                ),
                _single_flight(
                    "PVG",
                    "TPE",
                    dep_date=(2026, 5, 5),
                    arr_date=(2026, 5, 5),
                    dep_time=(12, 0),
                    arr_time=(14, 25),
                    airline_code="MU",
                    flight_number="5007",
                ),
            ],
        )
        alternate = _flight_entry(
            price=555,
            airline_name="Etihad",
            airline_code="EY",
            select_token="token-2",
            select_data='["selected-tfs-2"]',
            segments=[
                _single_flight(
                    "LHR",
                    "AUH",
                    dep_date=(2026, 5, 3),
                    arr_date=(2026, 5, 4),
                    dep_time=(9, 30),
                    arr_time=(7, 40),
                    airline_code="EY",
                    flight_number="68",
                ),
                _single_flight(
                    "AUH",
                    "TPE",
                    dep_date=(2026, 5, 4),
                    arr_date=(2026, 5, 5),
                    dep_time=(21, 20),
                    arr_time=(9, 35),
                    airline_code="EY",
                    flight_number="898",
                ),
            ],
        )

        payload = [None] * 8
        payload[2] = [[outbound]]
        payload[3] = [[outbound, alternate]]
        payload[7] = [None, [[], [["MU", "China Eastern"], ["EY", "Etihad"]]]]
        raw = ")]}'\n\n1\n" + json.dumps([["wrb.fr", None, json.dumps(payload)]]) + "\n"

        flights = _extract_full_flights_list(raw)

        self.assertIsNotNone(flights)
        self.assertEqual(len(flights), 2)
        self.assertEqual(len(flights[0].flights), 2)
        self.assertEqual(flights[0].flights[0].from_airport.code, "LHR")
        self.assertEqual(flights[0].flights[1].to_airport.code, "TPE")
        self.assertEqual(flights[0].flights[0].airline_code, "MU")
        self.assertEqual(flights[0].flights[1].flight_number, "5007")
        self.assertEqual(flights[0].select_token, "token-1")
        self.assertEqual(flights[0].select_data, '["selected-tfs-1"]')

    def test_build_booking_tfs_recreates_browser_booking_payload(self):
        query = create_query(
            flights=[
                FlightQuery(date="2026-05-03", from_airport="LHR", to_airport="TPE"),
                FlightQuery(date="2026-05-17", from_airport="TPE", to_airport="LHR"),
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en",
            currency="GBP",
        )
        selected_legs = (
            (
                SelectedSegment("LHR", "2026-05-03", "PVG", "MU", "552"),
                SelectedSegment("PVG", "2026-05-05", "TPE", "MU", "5007"),
            ),
            (
                SelectedSegment("TPE", "2026-05-17", "PVG", "MU", "5008"),
                SelectedSegment("PVG", "2026-05-18", "LHR", "MU", "551"),
            ),
        )

        actual = build_booking_tfs(query, selected_legs)

        self.assertEqual(
            actual,
            "CBwQAhphEgoyMDI2LTA1LTAzIh8KA0xIUhIKMjAyNi0wNS0wMxoDUFZHKgJNVTIDNTUyIiAKA1BWRxIKMjAyNi0wNS0wNRoDVFBFKgJNVTIENTAwN2oHCAESA0xIUnIHCAESA1RQRRphEgoyMDI2LTA1LTE3IiAKA1RQRRIKMjAyNi0wNS0xNxoDUFZHKgJNVTIENTAwOCIfCgNQVkcSCjIwMjYtMDUtMTgaA0xIUioCTVUyAzU1MWoHCAESA1RQRXIHCAESA0xIUkABSAFwAYIBCwj___________8BmAEB",
        )
        self.assertEqual(
            build_booking_url(query, selected_legs),
            "https://www.google.com/travel/flights/booking?tfs=CBwQAhphEgoyMDI2LTA1LTAzIh8KA0xIUhIKMjAyNi0wNS0wMxoDUFZHKgJNVTIDNTUyIiAKA1BWRxIKMjAyNi0wNS0wNRoDVFBFKgJNVTIENTAwN2oHCAESA0xIUnIHCAESA1RQRRphEgoyMDI2LTA1LTE3IiAKA1RQRRIKMjAyNi0wNS0xNxoDUFZHKgJNVTIENTAwOCIfCgNQVkcSCjIwMjYtMDUtMTgaA0xIUioCTVUyAzU1MWoHCAESA1RQRXIHCAESA0xIUkABSAFwAYIBCwj___________8BmAEB&hl=en&curr=GBP",
        )


if __name__ == "__main__":
    unittest.main()
