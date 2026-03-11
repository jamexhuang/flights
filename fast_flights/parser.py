import json

from selectolax.lexbor import LexborHTMLParser

from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
)


class MetaList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata


def _parse_metadata(payload: list) -> tuple[JsMetadata, dict[str, str]]:
    alliances = []
    airlines = []

    try:
        alliances_data, airlines_data = payload[7][1][0], payload[7][1][1]
        for code, name in alliances_data:
            alliances.append(Alliance(code=code, name=name))
        for code, name in airlines_data:
            airlines.append(Airline(code=code, name=name))
    except (IndexError, TypeError, KeyError):
        pass

    meta = JsMetadata(alliances=alliances, airlines=airlines)
    airline_name_to_code: dict[str, str] = {}
    for airline in airlines:
        if airline.name and airline.code:
            airline_name_to_code[airline.name] = airline.code

    return meta, airline_name_to_code


def _flight_entry_signature(entry: list) -> tuple | None:
    try:
        flight = entry[0]
        price = entry[1][0][1]
        select_token = None
        if entry[1] and len(entry[1]) > 1 and isinstance(entry[1][1], str):
            select_token = entry[1][1]

        segments = []
        for single_flight in flight[2]:
            airline_code = ""
            flight_number = ""
            try:
                if isinstance(single_flight[22], list):
                    if isinstance(single_flight[22][0], str):
                        airline_code = single_flight[22][0]
                    if isinstance(single_flight[22][1], str):
                        flight_number = single_flight[22][1]
            except (IndexError, TypeError):
                pass

            segments.append(
                (
                    single_flight[3],
                    single_flight[6],
                    tuple(single_flight[20]),
                    tuple(single_flight[21]),
                    tuple(single_flight[8]),
                    tuple(single_flight[10]),
                    airline_code,
                    flight_number,
                )
            )

        return (
            select_token,
            price,
            tuple(flight[1]) if isinstance(flight[1], list) else (),
            tuple(segments),
        )
    except (IndexError, TypeError, KeyError):
        return None


def _parse_flight_entry(entry: list, airline_name_to_code: dict[str, str]) -> Flights | None:
    try:
        flight = entry[0]
        price = entry[1][0][1]

        select_token = None
        select_data = None
        try:
            if entry[1] and len(entry[1]) > 1 and isinstance(entry[1][1], str):
                select_token = entry[1][1]
        except (IndexError, TypeError):
            pass
        try:
            if len(entry) > 8 and isinstance(entry[8], str):
                select_data = entry[8]
        except (IndexError, TypeError):
            pass

        typ = flight[0]
        airlines = flight[1]

        resolved_code = ""
        if isinstance(airlines, list):
            for name in airlines:
                code = airline_name_to_code.get(name, "")
                if code:
                    resolved_code = code
                    break

        sg_flights = []
        for single_flight in flight[2]:
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            departure_time = single_flight[8]
            departure_date = single_flight[20]
            departure = SimpleDatetime(date=departure_date, time=departure_time)

            arrival_time = single_flight[10]
            arrival_date = single_flight[21]
            arrival = SimpleDatetime(date=arrival_date, time=arrival_time)

            plane_type = single_flight[17]
            duration = single_flight[11]
            segment_airline_code = resolved_code
            flight_number = ""
            try:
                if isinstance(single_flight[22], list):
                    if isinstance(single_flight[22][0], str):
                        segment_airline_code = single_flight[22][0]
                    if isinstance(single_flight[22][1], str):
                        flight_number = single_flight[22][1]
            except (IndexError, TypeError):
                pass

            sg_flights.append(
                SingleFlight(
                    from_airport=from_airport,
                    to_airport=to_airport,
                    departure=departure,
                    arrival=arrival,
                    duration=duration,
                    plane_type=plane_type,
                    airline_code=segment_airline_code,
                    flight_number=flight_number,
                )
            )

        extras = flight[22]
        carbon_emission = extras[7]
        typical_carbon_emission = extras[8]

        return Flights(
            type=typ,
            price=price,
            airlines=airlines,
            flights=sg_flights,
            carbon=CarbonEmission(
                typical_on_route=typical_carbon_emission, emission=carbon_emission
            ),
            select_token=select_token,
            select_data=select_data,
        )
    except (IndexError, TypeError, KeyError):
        return None


def parse_payload(payload: list, *, include_top_results: bool = False) -> MetaList:
    meta, airline_name_to_code = _parse_metadata(payload)
    flights = MetaList()
    flights.metadata = meta

    candidate_groups: list[list] = []
    if include_top_results:
        try:
            if payload[2] is not None and payload[2][0] is not None:
                candidate_groups.append(payload[2][0])
        except (IndexError, TypeError):
            pass
    try:
        if payload[3] is not None and payload[3][0] is not None:
            candidate_groups.append(payload[3][0])
    except (IndexError, TypeError):
        pass

    seen_signatures: set[tuple] = set()
    for group in candidate_groups:
        for entry in group:
            signature = _flight_entry_signature(entry)
            if signature is not None and signature in seen_signatures:
                continue
            parsed = _parse_flight_entry(entry, airline_name_to_code)
            if parsed is None:
                continue
            flights.append(parsed)
            if signature is not None:
                seen_signatures.add(signature)

    return flights


def parse(html: str) -> MetaList:
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    if script is None:
        raise ValueError(
            "Could not find flight data in the HTML response. "
            "The page may have been blocked by Google, or the HTML structure has changed."
        )
    return parse_js(script.text())


# Data discovery by @kftang, huge shout out!
def parse_js(js: str):
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]
    payload = json.loads(data)
    return parse_payload(payload)
