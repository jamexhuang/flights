# Baggage & Amenities

This page documents what baggage and amenity information is available from the Google Flights data, and what fields to access in the raw response.

---

## What's available

`fast-flights` does **not** expose a dedicated baggage field yet, but the underlying Google Flights payload contains two relevant sources of information:

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

The mapping below was determined by cross-referencing ~23 flights on the TPE↔NRT route (full-service and LCC carriers). **Positions marked ⚠ are inferred, not confirmed by Google.**

| Index | Likely meaning | Confidence |
|-------|---------------|------------|
| `[1]` | In-flight WiFi | ⚠ Medium — present on STARLUX, EVA, Cathay Pacific, some JAL |
| `[3]` | Unknown (observed only on Scoot) | ⚠ Low |
| `[4]` | Unknown (observed on JAL own-operated flights) | ⚠ Low |
| `[5]` | Power/USB outlet or carry-on bag | ⚠ Medium — present on China Airlines, higher-fare Jetstar |
| `[9]` | **Checked bag included** | ✅ High — present on ALL full-service carriers (JAL, EVA, STARLUX, CI, CX); absent on all LCCs (Scoot, Jetstar base, Tigerair, Peach) |

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
    not currently exposed by fast-flights' parsed model.
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

- The `sf[12]` amenity array is **not yet exposed** in the `SingleFlight` dataclass. To access it you would need to work directly with `fetch_shopping_results()` and the raw payload.
- The index mapping is based on empirical observation of ~23 flights on a single regional route (TPE↔NRT). Mapping may differ for long-haul routes or different fare classes.
- Google does not document this internal format; indices could change at any time.
- For authoritative baggage allowance information, always link users to `payload[11]` baggage URLs or the airline's official page.

---

## Related

- [Filters](filters.md) — How to build a search query
- [Multi-City](multicity.md) — `GetShoppingResults` RPC internals
- [Return Flights](return-flights.md) — Round-trip selection flow
