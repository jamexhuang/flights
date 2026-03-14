from fast_flights.model import Flights, SingleFlight, Airport, SimpleDatetime, CarbonEmission
from fast_flights.querying import create_query, build_booking_tfs, build_booking_url, FlightQuery, Passengers, SelectedSegment, Trip
import urllib.parse

def make_dummy_flight(code, num):
    return SingleFlight(
        from_airport=Airport("", ""), to_airport=Airport("", ""),
        departure=SimpleDatetime((1,1,1), (1,1)), arrival=SimpleDatetime((1,1,1), (1,1)),
        duration=0, plane_type="", airline_code=code, flight_number=num
    )

def test_tfs_multi_city_parity():
    # Real 3-leg multi-city trip Google Flights captured string
    EXPECTED_TFS = "CAIQAho_EgoyMDI2LTA1LTEyIh8KA1RQRRIKMjAyNi0wNS0xMhoDTlJUKgJCUjIDMTk4agcIARIDVFBFcgcIARIDTlJUGj4SCjIwMjYtMDYtMTEiHgoDTlJUEgoyMDI2LTA2LTExGgNMQVgqAlVBMgIzM2oHCAESA05SVHIHCAESA0xBWBpgEgoyMDI2LTA3LTE1IiAKA0xBWBIKMjAyNi0wNy0xNRoDU0VBKgJETDIEMTA0NSIeCgNTRUESCjIwMjYtMDctMTUaA1RQRSoCREwyAjY5agcIARIDTEFYcgcIARIDVFBFQAFIAXABggELCP___________wGYAQM"
    
    fq_list = [
        FlightQuery("2026-05-12", "TPE", "NRT"),
        FlightQuery("2026-06-11", "NRT", "LAX"),
        FlightQuery("2026-07-15", "LAX", "TPE")
    ]

    q = create_query(
        flights=fq_list, 
        trip="multi-city", 
        seat="economy", 
        passengers=Passengers(adults=1)
    )

    selected_legs = (
        (
            SelectedSegment("TPE", "2026-05-12", "NRT", "BR", "198"),
        ),
        (
            SelectedSegment("NRT", "2026-06-11", "LAX", "UA", "33"),
        ),
        (
            SelectedSegment("LAX", "2026-07-15", "SEA", "DL", "1045"),
            SelectedSegment("SEA", "2026-07-15", "TPE", "DL", "69"),
        )
    )

    tfs = build_booking_tfs(q, selected_legs)
    assert tfs == EXPECTED_TFS, f"Generated TFS {tfs} does not match expected {EXPECTED_TFS}"
    
    url = build_booking_url(q, selected_legs)
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    generated_tfs_from_url = qs.get("tfs", [""])[0]
    assert generated_tfs_from_url == EXPECTED_TFS, "Generated URL TFS mismatch"
