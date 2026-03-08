import unittest
from unittest.mock import patch

from fast_flights import FlightQuery, create_query
from fast_flights.fetcher import get_selected_flight_page
from fast_flights.model import CarbonEmission, Flights


FIXTURE_HTML = """
<html>
  <head>
    <script>
      window.WIZ_global_data = {"FdrFJe":"123456789","cfb2h":"boq_travel-frontend-flights-ui_20260303.06_p0"};
    </script>
    <script>
      var AF_dataServiceRequests = {
        'ds:1' : {id:'LqxFAb',request:[[null,"TOKEN-1"],[null,null,3,null,[],1,[1,0,0,0],null,null,null,null,null,null,[],null,null,null,1],0]},
        'ds:2' : {id:'j0jL5',request:[]}
      };
    </script>
  </head>
</html>
"""


class SelectedFlightPageTests(unittest.TestCase):
    def test_get_selected_flight_page_extracts_context(self):
        query = create_query(
            flights=[FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT")],
            trip="one-way",
            seat="economy",
        )
        flight = Flights(
            type="one-way",
            price=1000,
            airlines=["Test Air"],
            flights=[],
            carbon=CarbonEmission(typical_on_route=0, emission=0),
            select_token="dummy-select-token",
        )

        with patch("fast_flights.fetcher.fetch_flights_html", return_value=FIXTURE_HTML):
            page = get_selected_flight_page(query, flight)

        self.assertIn("tfu=", page.url)
        self.assertEqual(page.f_sid, "123456789")
        self.assertEqual(page.bl, "boq_travel-frontend-flights-ui_20260303.06_p0")
        self.assertIn("ds:1", page.data_service_requests)
        self.assertEqual(page.data_service_requests["ds:1"].rpc_id, "LqxFAb")
        self.assertEqual(page.data_service_requests["ds:1"].request[0][1], "TOKEN-1")
        self.assertIn("ds:2", page.data_service_requests)
        self.assertEqual(page.data_service_requests["ds:2"].request, [])


if __name__ == "__main__":
    unittest.main()
