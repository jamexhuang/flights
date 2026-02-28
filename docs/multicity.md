# Multi-City Token Chaining

Google Flights calculates prices by making you select an outbound flight first, passing a token (`tfu` / `select`) back to the query, and then fetching the subsequent leg. For multi-city flights, they don't give you the entire trip's price until the final leg is queried.

`fast-flights` provides `get_flights_multicity_chained()` which internally wraps the hidden API (`GetShoppingResults`) to perform token chaining automatically. 

This process guarantees that the prices fetched reflect exact multi-leg combinations as specified by Google.

## Example

```python
from fast_flights import FlightQuery, get_flights_multicity_chained

legs = [
    FlightQuery(date="2026-03-15", from_airport="SIN", to_airport="TPE"),
    FlightQuery(date="2026-03-21", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-03-24", from_airport="NRT", to_airport="TPE"),
    FlightQuery(date="2026-03-27", from_airport="TPE", to_airport="SIN"),
]

# Automatically steps through all legs and calculates total real-time price
result = get_flights_multicity_chained(
    legs,
    language="en-US",
    currency="USD",
    delay=1.0 # Add delay to avoid getting rate-limited
)

for leg in result:
    print(leg.from_airport, "->", leg.to_airport)

if result[-1].total_price:
    print("Final Google Flights ticket price:", result[-1].total_price)
```

## Structure
`get_flights_multicity_chained` returns a list of `MulticityLegChained` objects:
- `leg_index` (int): 0-indexed leg tracker
- `from_airport` (str): Origin
- `to_airport` (str): Destination
- `date` (str): Flight search date
- `tokens` (list[str]): Available Google Flights multi-city continuity tokens fetched
- `total_price` (int | None): Total accumulated price tracked on the current UI state.
- `flights` (MetaList | None): Standard rich flight result set identical to standard `get_flights()` data.

## Technical Details: How the RPC string-extraction works
Google handles multi-city selections in its UI by routing to an internal `/GetShoppingResults` endpoint. The server responds with an incredibly complex undocumented Protobuf structure (often wrapped over 5 layers deep inside `f.req` parameters and nested string-JSON constructs).

Instead of maintaining a fragile Protobuf tree specifically for the `GetShoppingResults` payload (which Google frequently updates with new key IDs), `fast-flights` bypasses strict Protobuf deserialization for this specific functionality. 

Instead, it employs **Heuristic Regex Scanning**. Google's state continuity Tokens (which must be passed as `selected_tokens` parameters) always follow Base64 formats heavily padded with long strings like `AAAA` and specific structural characters (e.g. `---` or `===`). The library rapidly scans the output text for these tokens, ensuring robustness against future UX structural changes.

Similarly, the overall price (`total_price`) is plucked via regex tracking standard currency wrappers (ex. `\"TWD\",42149`).

For the specific `flights` dictionary array, the raw string uses the exact same `[7][1][0]` mapped Javascript indexes that regular Google Flights pages use, allowing us to pipe the hidden data back into the classic `parse_js()` function normally used for the frontend HTML parser!

### Drawbacks
1. **Automated Sub-Selection:** The helper `get_flights_multicity_chained` automatically grabs `tokens[0]` for each subsequent leg. This generally aligns with the cheapest/best flight displayed for that leg, but you aren't manually approving the specific airline.
2. **No Integrations / Fallbacks:** Because this relies heavily on sequential state-keeping via `primp` HTTP cookie-jars, you cannot currently pass `BrightData` or `Playwright` integrations into `get_flights_multicity_chained`.
