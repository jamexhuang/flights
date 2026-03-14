import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fast_flights import (
    BrowserCapture,
    BrowserProvider,
    FlightQuery,
    Passengers,
    SearchSession,
    ShoppingOptions,
    build_booking_tfs,
    create_query,
    select_flight,
)
from fast_flights.fetcher import GoogleFlightsDataServiceRequest, SelectedFlightPage
from fast_flights.model import Airport, CarbonEmission, Flights, SimpleDatetime, SingleFlight
from fast_flights.parser import MetaList


def _segment(
    frm: str,
    to: str,
    *,
    date: tuple[int, int, int] = (2026, 5, 1),
    airline_code: str = "TS",
    flight_number: str = "123",
) -> SingleFlight:
    return SingleFlight(
        from_airport=Airport(name=f"{frm} Airport", code=frm),
        to_airport=Airport(name=f"{to} Airport", code=to),
        departure=SimpleDatetime(date=date, time=(9, 0)),
        arrival=SimpleDatetime(date=date, time=(12, 0)),
        duration=180,
        plane_type="Test Plane",
        airline_code=airline_code,
        flight_number=flight_number,
    )


def _flight(
    frm: str,
    to: str,
    *,
    price: int,
    select_token: str,
    select_data: str,
    segments: list[SingleFlight] | None = None,
) -> Flights:
    return Flights(
        type="one-way",
        price=price,
        airlines=["Test Air"],
        flights=segments or [_segment(frm, to)],
        carbon=CarbonEmission(typical_on_route=0, emission=0),
        select_token=select_token,
        select_data=select_data,
    )


def _results(*flights: Flights) -> MetaList:
    results = MetaList()
    results.extend(flights)
    return results


def _single_flight_payload(
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


def _flight_entry_payload(
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


def _shopping_raw_response(*entries: list) -> str:
    payload = [None] * 8
    payload[3] = [list(entries)]
    airlines = []
    seen_codes: set[str] = set()
    for entry in entries:
        segments = entry[0][2] or []
        for segment in segments:
            airline_code = segment[22][0]
            if airline_code not in seen_codes:
                seen_codes.add(airline_code)
                airlines.append([airline_code, f"Airline {airline_code}"])
    payload[7] = [None, [[], airlines]]
    return ")]}'\n\n1\n" + json.dumps([["wrb.fr", None, json.dumps(payload)]]) + "\n"


class StubBrowserProvider(BrowserProvider):
    def __init__(self, capture: BrowserCapture | None) -> None:
        self.capture = capture
        self.calls: list[tuple[int, str]] = []

    def capture_next_leg(self, session, /) -> BrowserCapture | None:
        self.calls.append((session.current_leg_index, session.current_search_url()))
        return self.capture


class SearchSessionTests(unittest.TestCase):
    def test_roundtrip_session_chains_rpc_results_and_builds_booking_link(self):
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
        outbound = _results(
            _flight(
                "LHR",
                "TPE",
                price=347,
                select_token="token-1",
                select_data='["search-tfs-1"]',
                segments=[
                    _segment("LHR", "PVG", date=(2026, 5, 3), airline_code="MU", flight_number="552"),
                    _segment("PVG", "TPE", date=(2026, 5, 5), airline_code="MU", flight_number="5007"),
                ],
            )
        )
        returning = _results(
            _flight(
                "TPE",
                "LHR",
                price=347,
                select_token="token-2",
                select_data='["search-tfs-2"]',
                segments=[
                    _segment("TPE", "PVG", date=(2026, 5, 17), airline_code="MU", flight_number="5008"),
                    _segment("PVG", "LHR", date=(2026, 5, 18), airline_code="MU", flight_number="551"),
                ],
            )
        )

        rpc_calls = []

        def fake_fetch_shopping_results(**kwargs):
            rpc_calls.append(
                {
                    "tokens": tuple(kwargs["tokens"]),
                    "shopping": kwargs.get("shopping"),
                    "f_sid": kwargs.get("f_sid"),
                    "bl": kwargs.get("bl"),
                    "referer": kwargs.get("referer"),
                }
            )
            if not kwargs["tokens"]:
                return [], outbound[0].price, "", outbound
            return [], returning[0].price, "", returning

        selected_after_outbound = select_flight(query, outbound[0])
        selected_after_return = select_flight(selected_after_outbound, returning[0])
        page_one = SelectedFlightPage(
            return_query=selected_after_outbound,
            url="https://example.test/selected/1",
            f_sid="rpc-session-1",
            bl="boq_travel-frontend-flights-ui_test",
            data_service_requests={
                "ds:1": GoogleFlightsDataServiceRequest(key="ds:1", rpc_id="rpc-1", request=[None, 1])
            },
        )
        page_two = SelectedFlightPage(
            return_query=selected_after_return,
            url="https://example.test/selected/2",
            f_sid="rpc-session-2",
            bl="boq_travel-frontend-flights-ui_test",
            data_service_requests={
                "ds:1": GoogleFlightsDataServiceRequest(key="ds:1", rpc_id="rpc-2", request=[None, 2])
            },
        )

        with patch("fast_flights.session._build_default_client", return_value=object()):
            with patch("fast_flights.session.fetch_shopping_results", side_effect=fake_fetch_shopping_results):
                with patch("fast_flights.session.get_selected_flight_page", side_effect=[page_one, page_two]):
                    session = SearchSession(query)
                    first_leg = session.results()
                    next_session = session.select(first_leg[0])
                    second_leg = next_session.results()
                    done_session = next_session.select(second_leg[0])

        self.assertEqual(first_leg[0].price, 347)
        self.assertEqual(second_leg[0].flights[0].from_airport.code, "TPE")
        self.assertEqual(second_leg[0].flights[-1].to_airport.code, "LHR")
        self.assertEqual(rpc_calls[0]["tokens"], ())
        self.assertEqual(rpc_calls[1]["tokens"], ("token-1",))
        self.assertIsNone(rpc_calls[0]["shopping"])
        self.assertEqual(rpc_calls[1]["f_sid"], "rpc-session-1")
        self.assertEqual(rpc_calls[1]["bl"], "boq_travel-frontend-flights-ui_test")
        self.assertEqual(rpc_calls[1]["referer"], "https://example.test/selected/1")
        self.assertEqual(done_session.current_leg_index, 2)
        self.assertTrue(done_session.is_complete)
        self.assertEqual(done_session.final_booking_tfs, build_booking_tfs(query, done_session.selected_legs))
        self.assertIn("/travel/flights/booking?tfs=", done_session.booking_url())

    def test_roundtrip_session_passes_shopping_options_through_rpc(self):
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
        outbound = _results(
            _flight(
                "LHR",
                "TPE",
                price=347,
                select_token="token-1",
                select_data='["search-tfs-1"]',
            )
        )
        returning = _results(
            _flight(
                "TPE",
                "LHR",
                price=347,
                select_token="token-2",
                select_data='["search-tfs-2"]',
            )
        )
        shopping = ShoppingOptions(ranking_mode="cheapest", result_sort="price")
        rpc_calls = []

        def fake_fetch_shopping_results(**kwargs):
            rpc_calls.append(kwargs["shopping"])
            if not kwargs["tokens"]:
                return [], outbound[0].price, "", outbound
            return [], returning[0].price, "", returning

        selected_after_outbound = select_flight(query, outbound[0])
        page_one = SelectedFlightPage(
            return_query=selected_after_outbound,
            url="https://example.test/selected/1",
            f_sid="rpc-session-1",
            bl="boq_travel-frontend-flights-ui_test",
            data_service_requests={
                "ds:1": GoogleFlightsDataServiceRequest(key="ds:1", rpc_id="rpc-1", request=[None, 1])
            },
        )

        with patch("fast_flights.session._build_default_client", return_value=object()):
            with patch("fast_flights.session.fetch_shopping_results", side_effect=fake_fetch_shopping_results):
                with patch("fast_flights.session.get_selected_flight_page", side_effect=[page_one]):
                    session = SearchSession(query, shopping=shopping)
                    first_leg = session.results()
                    next_session = session.select(first_leg[0])
                    next_session.results()

        self.assertEqual(first_leg[0].price, 347)
        self.assertEqual(rpc_calls, [shopping, shopping])

    def test_multicity_session_chains_selection_tokens_across_legs(self):
        query = create_query(
            flights=[
                FlightQuery(date="2026-05-01", from_airport="TPE", to_airport="NRT"),
                FlightQuery(date="2026-05-08", from_airport="NRT", to_airport="HKG"),
                FlightQuery(date="2026-05-12", from_airport="HKG", to_airport="TPE"),
            ],
            trip="multi-city",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
        )
        legs = [
            _results(_flight("TPE", "NRT", price=500, select_token="tok-1", select_data='["search-1"]')),
            _results(_flight("NRT", "HKG", price=700, select_token="tok-2", select_data='["search-2"]')),
            _results(_flight("HKG", "TPE", price=900, select_token="tok-3", select_data='["search-3"]')),
        ]
        pages = []
        current_query = None
        selected = query
        for idx, result in enumerate(legs):
            selected = select_flight(selected, result[0]) if idx > 0 else select_flight(query, result[0])
            pages.append(
                SelectedFlightPage(
                    return_query=selected,
                    url=f"https://example.test/multicity/{idx + 1}",
                    f_sid=f"session-{idx + 1}",
                    bl="boq_travel-frontend-flights-ui_test",
                    data_service_requests={},
                )
            )
            current_query = selected

        observed_tokens = []

        def fake_fetch_shopping_results(**kwargs):
            observed_tokens.append(tuple(kwargs["tokens"]))
            return [], 1000, "", legs[len(kwargs["tokens"])]

        with patch("fast_flights.session._build_default_client", return_value=object()):
            with patch("fast_flights.session.fetch_shopping_results", side_effect=fake_fetch_shopping_results):
                with patch("fast_flights.session.get_selected_flight_page", side_effect=pages):
                    session = SearchSession(query)
                    session = session.select(session.results()[0])
                    session = session.select(session.results()[0])
                    session = session.select(session.results()[0])

        self.assertEqual(observed_tokens, [(), ("tok-1",), ("tok-1", "tok-2")])
        self.assertTrue(session.is_complete)
        self.assertEqual(session.selection_tokens, ("tok-1", "tok-2", "tok-3"))
        self.assertIsNotNone(session.final_booking_tfs)
        self.assertIn("/travel/flights/booking?tfs=", session.booking_url())
        selected_search = session.selected_search_url()
        parsed = urlparse(selected_search)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/travel/flights")
        self.assertEqual(params["tfs"][0], build_booking_tfs(query, session.selected_legs))
        self.assertNotIn("tfu", params)

    def test_browser_fallback_uses_provider_only_when_results_need_it(self):
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
        outbound = _results(
            _flight(
                "LHR",
                "TPE",
                price=347,
                select_token="token-1",
                select_data='["search-tfs-1"]',
                segments=[
                    _segment("LHR", "PVG", date=(2026, 5, 3), airline_code="MU", flight_number="552"),
                    _segment("PVG", "TPE", date=(2026, 5, 5), airline_code="MU", flight_number="5007"),
                ],
            )
        )
        selected_page = SelectedFlightPage(
            return_query=select_flight(query, outbound[0]),
            url="https://example.test/selected/browser",
            f_sid="session-browser",
            bl="boq_travel-frontend-flights-ui_test",
            data_service_requests={},
        )
        browser_capture = BrowserCapture(
            leg_index=1,
            selected_url=selected_page.url,
            captured_response_text=_shopping_raw_response(
                _flight_entry_payload(
                    price=347,
                    airline_name="China Eastern",
                    airline_code="MU",
                    select_token="token-return",
                    select_data='["search-tfs-2"]',
                    segments=[
                        _single_flight_payload(
                            "TPE",
                            "PVG",
                            dep_date=(2026, 5, 17),
                            arr_date=(2026, 5, 17),
                            dep_time=(15, 30),
                            arr_time=(17, 30),
                            airline_code="MU",
                            flight_number="5008",
                        ),
                        _single_flight_payload(
                            "PVG",
                            "LHR",
                            dep_date=(2026, 5, 18),
                            arr_date=(2026, 5, 18),
                            dep_time=(22, 0),
                            arr_time=(18, 40),
                            airline_code="MU",
                            flight_number="551",
                        ),
                    ],
                )
            ),
        )
        provider = StubBrowserProvider(browser_capture)

        with patch("fast_flights.session.get_flights", return_value=outbound):
            with patch("fast_flights.session.get_selected_flight_page", return_value=selected_page):
                session = SearchSession(
                    query,
                    mode="ssr-first",
                    browser_fallback=True,
                    browser_provider=provider,
                )
                first_leg = session.results()
                next_session = session.select(first_leg[0])

        self.assertEqual(provider.calls, [])

        with patch("fast_flights.session._get_selected_html_results", return_value=None):
            with patch("fast_flights.session._get_bundled_leg_results", return_value=None):
                with patch("fast_flights.session._build_default_client", return_value=object()):
                    with patch(
                        "fast_flights.session.fetch_shopping_results",
                        return_value=([], None, "", None),
                    ):
                        with patch(
                            "fast_flights.session._get_directional_leg_results",
                            side_effect=AssertionError("directional fallback should not run"),
                        ):
                            returning = next_session.results()

        self.assertEqual(provider.calls, [(1, next_session.current_search_url())])
        self.assertEqual(returning[0].price, 347)
        self.assertEqual(returning[0].flights[0].from_airport.code, "TPE")
        self.assertEqual(returning[0].flights[-1].to_airport.code, "LHR")

    def test_browser_fallback_without_provider_keeps_existing_fallbacks(self):
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
        outbound = _results(
            _flight(
                "LHR",
                "TPE",
                price=347,
                select_token="token-1",
                select_data='["search-tfs-1"]',
            )
        )
        directional = _results(
            _flight(
                "TPE",
                "LHR",
                price=555,
                select_token="dir-token",
                select_data='["dir-search"]',
            )
        )
        selected_page = SelectedFlightPage(
            return_query=select_flight(query, outbound[0]),
            url="https://example.test/selected/no-provider",
            f_sid="session-browser",
            bl="boq_travel-frontend-flights-ui_test",
            data_service_requests={},
        )

        with patch("fast_flights.session.get_flights", return_value=outbound):
            with patch("fast_flights.session.get_selected_flight_page", return_value=selected_page):
                session = SearchSession(query, mode="ssr-first", browser_fallback=True)
                next_session = session.select(session.results()[0])

        with patch("fast_flights.session._get_selected_html_results", return_value=None):
            with patch("fast_flights.session._get_bundled_leg_results", return_value=None):
                with patch("fast_flights.session._build_default_client", return_value=object()):
                    with patch(
                        "fast_flights.session.fetch_shopping_results",
                        return_value=([], None, "", None),
                    ):
                        with patch(
                            "fast_flights.session._get_directional_leg_results",
                            return_value=directional,
                        ) as directional_fallback:
                            returning = next_session.results()

        directional_fallback.assert_called_once()
        self.assertEqual(returning[0].price, 555)
        self.assertEqual(returning[0].flights[0].from_airport.code, "TPE")


if __name__ == "__main__":
    unittest.main()
