from pprint import pprint

from fast_flights import FlightQuery, Passengers, create_query, get_flights

# v3.1.0 – Added return-flight support for round-trip queries

# --- One-way example (unchanged) ---
query = create_query(
    flights=[
        FlightQuery(
            date="2026-03-15",
            from_airport="MYJ",
            to_airport="TPE",
        ),
    ],
    seat="economy",
    trip="one-way",
    passengers=Passengers(adults=1),
    language="zh-TW",
)
res = get_flights(query)
pprint(res)


# --- Round-trip example (NEW) ---
# Step 1: query outbound flights
from fast_flights import select_flight, get_return_flights

rt_query = create_query(
    flights=[
        FlightQuery(date="2026-03-15", from_airport="CDG", to_airport="TPE"),
        FlightQuery(date="2026-03-19", from_airport="TPE", to_airport="CDG"),
    ],
    seat="economy",
    trip="round-trip",
    passengers=Passengers(adults=1),
    language="zh-TW",
    currency="EUR",
)
outbound = get_flights(rt_query)
print(f"Outbound flights: {len(outbound)}")

# Step 2: select an outbound flight and fetch return options
if outbound and outbound[0].select_token:
    return_query = select_flight(rt_query, outbound[0])
    returning = get_return_flights(return_query)
    print(f"Return flights: {len(returning)}")
    pprint(returning)
