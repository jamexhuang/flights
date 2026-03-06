# Baggage & Amenities

This page documents what baggage and amenity information is available from the Google Flights data, and what fields to access in the raw response.

---

## What's available

`faster-flights` does **not** expose a dedicated baggage field yet, but the underlying Google Flights payload contains two relevant sources of information:

| Source | What it contains | Where |
|--------|-----------------|-------|
| `payload[11]` | Per-airline baggage policy URLs | Top-level payload field |
| `single_flight[12]` | Per-flight amenity flags (bag inclusion, WiFi, IFE, …) | Inside each flight segment |

---

## Airline baggage URLs (`payload[11]`)

At the top level of the `GetShoppingResults` response, index `[11]` contains a list of `[airline_code, airline_name, baggage_url]` entries for every airline appearing in the results:

```python
# Example entries from payload[11]
['CX', 'Cathay Pacific',    'https://www.cathaypacific.com/cx/.../baggage.html']
['GK', 'Jetstar',           'https://www.jetstar.com/.../baggage/checked-baggage']
['TR', 'Scoot',             'https://www.flyscoot.com/.../baggage']
['BR', 'EVA Air',           'https://www.evaair.com/en-us/fly-prepare/baggage/']
['JL', 'JAL',               'https://www.jal.co.jp/jp/en/inter/baggage/']
```

These are **airline-level** links, not per-flight allowances. Useful for pointing users to the airline's baggage policy page.

---

## Per-flight amenity flags (`single_flight[12]`)

Each flight segment (a `SingleFlight` in the parsed model) has a raw amenity array at position `[12]` in the underlying data. It is a sparse list where `True` at a given index indicates that amenity is available.

### Observed index mapping

This mapping has been extensively verified across multiple regional and long-haul routes via the `test/test_baggage.py` test suite and detailed in [`test/baggage_research_report.md`](../test/baggage_research_report.md).

| Index | Type | Confidence | Likely meaning |
|-------|------|------------|---------------|
| `[1]` | bool | ✅ High     | In-flight WiFi |
| `[5]` | bool | ✅ High     | Power/USB outlet or carry-on bag (common on both LCC and Full Service) |
| `[9]` | bool | ✅ High     | **Checked bag included** (Present on nearly all full-service carriers) |
| `[10]`| bool | ⚠ Low      | Unknown (Observed on Malaysia Airlines) |
| `[11]`| int  | ⚠ Med      | Seat Pitch / Legroom category (e.g., 2 or 3) |

### Examples from reverse-engineering session

```
Carrier             Price   sf[12]
──────────────────────────────────────────────────────────────────────
Jetstar (base)      $250    []                                  ← no bags
Scoot               $262    [None, None, None, True, …]         ← [3]=True
Tigerair Taiwan     $271    None                                ← no info
Peach Aviation      $289    None                                ← no info
China Airlines      $328    [None, None, None, None, None, True, …, True, …]   ← [5] & [9]
STARLUX Airlines    $334    [None, True, …, True, …]            ← [1] & [9]
JAL (codeshare)     $337    [None, True, …, True, …]            ← [1] & [9]
EVA Air             $348    [None, True, …, True, …]            ← [1] & [9]
Cathay Pacific      $405    [None, True, …, True, …]            ← [1] & [9]
JAL (own-op)        $414    [None, None, None, None, True, …, True]  ← [4] & [9]
Jetstar (higher)    $457    [None, None, None, None, None, True]     ← [5] only
```

### Practical heuristic

```python
def checked_bag_included(single_flight_raw_sf12) -> bool | None:
    """
    Returns True if a checked bag is likely included, False if likely not,
    or None if the data is absent (no amenity info from Google).

    single_flight_raw_sf12 is the raw sf[12] list from the payload;
    not currently exposed by faster-flights' parsed model.
    """
    if single_flight_raw_sf12 is None:
        return None
    if not single_flight_raw_sf12:  # empty list []
        return False
    try:
        return single_flight_raw_sf12[9] is True
    except IndexError:
        return False
```

---

## Notes & caveats

- The `sf[12]` amenity array is **not yet exposed** in the `SingleFlight` dataclass (see `test/baggage_research_report.md` for a potential implementation plan).
- The index mapping is based on extensive empirical observation across various global routes.
- Google does not document this internal format; indices could change at any time.
- For authoritative baggage allowance information, always link users to `payload[11]` baggage URLs or the airline's official page.

---

## Related

- [Filters](filters.md) — How to build a search query
- [Multi-City](multicity.md) — `GetShoppingResults` RPC internals
- [Return Flights](return-flights.md) — Round-trip selection flow
