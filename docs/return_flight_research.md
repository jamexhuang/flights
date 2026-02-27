# Return Flight Support — Research & Verification

## Verified Findings

### Google Flights Two-Step Flow
Both **round-trip** AND **multi-city** modes use a two-step flow:
1. First page shows outbound (Leg 1) options only
2. User selects one → second page shows return (Leg 2) options

**There is no way to get both legs in a single request.**

### Data Structure (from `ds:1` JavaScript)

Each flight result `f` in `data[3][0]` has:

| Index | Type | Content |
|-------|------|---------|
| `f[0]` | object | Flight info (airlines, segments, carbon, etc.) |
| `f[0][1]` | string[] | Airline names |
| `f[0][2]` | array | Individual flight segments |
| `f[0][2][n][3]` | string | From airport code |
| `f[0][2][n][6]` | string | To airport code |
| `f[0][2][n][15]` | array | Airline info `[code, flightNum, null, name]` |
| `f[1][0][1]` | int | Price (already parsed) |
| **`f[1][1]`** | **string** | **Session token for `tfu` param (NEW)** |
| **`f[8]`** | **string** | **Encoded flight selection for `tfs` param (NEW)** |

### URL Parameter Changes After Selection

**Before (outbound):**
```
tfs=<original protobuf with 2 FlightData entries>
tfu=EgYIABABGAA  (short, generic)
```

**After selecting outbound flight (return page):**
```
tfs=<expanded: outbound FlightData gets Field 4 submessages with leg details>
tfu=<long token from f[1][1], wrapped in protobuf>
```

### `tfu` Token Structure (Protobuf)
```
Field 1 (string): inner token from f[1][1]
Field 2 (submsg): { Field 1 (varint): 0 }
Field 4 (string): ""
```

Inner token contains: session hash, flight numbers (`KL1404|KL807`), price, currency.

### `tfs` Expansion (Protobuf Field 4)
The outbound `FlightData` gains Field 4 submessages per leg:
```
Field 4: { from_airport, date, to_airport, airline_code, flight_number }
```

### Return Page Parser Compatibility
✅ Return flights page uses the **same `ds:1` structure** → existing `parse()` works as-is.

## Implementation Approach
1. Modify `parser.py`: extract `f[1][1]` (token) and `f[8]` (selection data)  
2. Modify `model.py`: add `select_token` and `select_data` fields to `Flights`
3. Modify `querying.py`: add function to build return-flight query with token
4. Modify `fetcher.py`: add `get_return_flights()` convenience function
