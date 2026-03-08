"""
台灣出發全方位整合測試 — 歐洲、美洲、日本 × 單程、來回、多腿 × 全艙等

Live tests calling the Google Flights API.

Usage:
    python test/test_tw_comprehensive.py [--section SECTION]

    SECTION 可選：oneway | roundtrip | multicity | all（預設 all）

Output:
    test/tw_comprehensive_report.md

Routes covered:
    Japan  : TPE → NRT (Tokyo), TPE → KIX (Osaka)
    Europe : TPE → LHR (London), TPE → CDG (Paris), TPE → FRA (Frankfurt)
    Americas: TPE → JFK (New York), TPE → LAX (Los Angeles), TPE → SFO (San Francisco)

Cabin classes:
    economy, premium-economy, business, first
"""

import argparse
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from fast_flights import (
    FlightQuery,
    Passengers,
    create_query,
    get_flights,
    get_flights_multicity,
    get_flights_multicity_chained,
    get_return_flights,
    select_flight,
)
from fast_flights.model import CarbonEmission, Flights

# ── Date constants (current project date: 2026-03-08) ───────────────────────
# One-way / round-trip: April 2026 (spring travel)
DATE_OW          = "2026-04-15"
DATE_RT_OUT      = "2026-04-15"
DATE_RT_RET      = "2026-04-22"

# Multi-city spring (3-leg, gaps of 5-10 days)
DATE_MC3_L1      = "2026-04-20"
DATE_MC3_L2      = "2026-04-27"
DATE_MC3_L3      = "2026-05-04"

# Multi-city summer (4-leg, long haul cross-regional)
DATE_MC4_L1      = "2026-07-20"
DATE_MC4_L2      = "2026-07-25"
DATE_MC4_L3      = "2026-08-05"
DATE_MC4_L4      = "2026-08-12"

REPORT_PATH = Path(__file__).parent / "tw_comprehensive_report.md"

PAX1 = Passengers(adults=1)


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class TestResult:
    name: str
    passed: bool
    section: str = ""
    note: str = ""
    sample_data: list = field(default_factory=list)
    error: str = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt_flight(f: Flights) -> str:
    """Short human-readable summary of a Flights object."""
    seg = f.flights[0] if f.flights else None
    seg_str = (
        f"{seg.from_airport.code}→{seg.to_airport.code} ({seg.airline_code}, {seg.duration}min)"
        if seg else "no-segment"
    )
    return f"${f.price} | {', '.join(f.airlines)} | {seg_str}"


def _assert_flights_list(results, label: str):
    """Common assertions on a MetaList of Flights."""
    assert len(results) > 0, f"{label}: 預期至少 1 筆結果，實際 0 筆"
    f0 = results[0]
    assert f0.price > 0, f"{label}: price 應大於 0，實際 {f0.price}"
    assert isinstance(f0.flights, list) and len(f0.flights) > 0, \
        f"{label}: flights 不應為空"
    seg = f0.flights[0]
    assert seg.from_airport.code != "", f"{label}: from_airport.code 不應為空"
    assert seg.to_airport.code != "", f"{label}: to_airport.code 不應為空"
    assert isinstance(seg.duration, int) and seg.duration > 0, \
        f"{label}: duration 應為正整數（分鐘），實際 {seg.duration}"


def _samples_from_results(results, label: str, n: int = 3) -> list[str]:
    """Extract sample strings from a MetaList of Flights."""
    if len(results) == 0:
        return [f"{label}: 無結果"]
    cheapest = min(results, key=lambda f: f.price)
    rows = [
        f"{label}: 共 {len(results)} 筆，最低票價 {cheapest.price}",
        f"  最低票價選項：{_fmt_flight(cheapest)}",
    ]
    for f in results[1:n]:
        rows.append(f"  {_fmt_flight(f)}")
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: ONE-WAY (單程)
# ═══════════════════════════════════════════════════════════════════════════

def _oneway(name: str, frm: str, to: str, seat: str, date: str = DATE_OW) -> TestResult:
    """Generic one-way test from `frm` to `to` with given seat class."""
    section = "oneway"
    try:
        query = create_query(
            flights=[FlightQuery(date=date, from_airport=frm, to_airport=to)],
            trip="one-way",
            seat=seat,
            passengers=PAX1,
            language="en-US",
            currency="USD",
        )
        results = get_flights(query)

        # First class may legitimately return 0 results on some routes.
        if seat == "first":
            note = f"first class — 找到 {len(results)} 筆（0 筆為正常）"
            samples = _samples_from_results(results, f"{frm}→{to} first") if results else [f"{frm}→{to} first: 無結果（正常）"]
            return TestResult(name=name, passed=True, section=section, note=note, sample_data=samples)

        _assert_flights_list(results, f"{frm}→{to} {seat}")
        return TestResult(
            name=name,
            passed=True,
            section=section,
            note=f"{frm}→{to} {seat} — {len(results)} 筆",
            sample_data=_samples_from_results(results, f"{frm}→{to} {seat}"),
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, section=section, error=str(e), note="斷言失敗")
    except Exception:
        return TestResult(name=name, passed=False, section=section, error=traceback.format_exc())


# ── Japan routes ─────────────────────────────────────────────────────────────

def test_ow_TPE_NRT_economy():
    return _oneway("ow_TPE_NRT_economy", "TPE", "NRT", "economy")

def test_ow_TPE_NRT_premium_economy():
    return _oneway("ow_TPE_NRT_premium_economy", "TPE", "NRT", "premium-economy")

def test_ow_TPE_NRT_business():
    return _oneway("ow_TPE_NRT_business", "TPE", "NRT", "business")

def test_ow_TPE_NRT_first():
    return _oneway("ow_TPE_NRT_first", "TPE", "NRT", "first")

def test_ow_TPE_KIX_economy():
    return _oneway("ow_TPE_KIX_economy", "TPE", "KIX", "economy")

def test_ow_TPE_KIX_business():
    return _oneway("ow_TPE_KIX_business", "TPE", "KIX", "business")


# ── Europe routes ─────────────────────────────────────────────────────────────

def test_ow_TPE_LHR_economy():
    return _oneway("ow_TPE_LHR_economy", "TPE", "LHR", "economy")

def test_ow_TPE_LHR_premium_economy():
    return _oneway("ow_TPE_LHR_premium_economy", "TPE", "LHR", "premium-economy")

def test_ow_TPE_LHR_business():
    return _oneway("ow_TPE_LHR_business", "TPE", "LHR", "business")

def test_ow_TPE_LHR_first():
    return _oneway("ow_TPE_LHR_first", "TPE", "LHR", "first")

def test_ow_TPE_CDG_economy():
    return _oneway("ow_TPE_CDG_economy", "TPE", "CDG", "economy")

def test_ow_TPE_CDG_business():
    return _oneway("ow_TPE_CDG_business", "TPE", "CDG", "business")

def test_ow_TPE_FRA_economy():
    return _oneway("ow_TPE_FRA_economy", "TPE", "FRA", "economy")


# ── Americas routes ───────────────────────────────────────────────────────────

def test_ow_TPE_JFK_economy():
    return _oneway("ow_TPE_JFK_economy", "TPE", "JFK", "economy")

def test_ow_TPE_JFK_premium_economy():
    return _oneway("ow_TPE_JFK_premium_economy", "TPE", "JFK", "premium-economy")

def test_ow_TPE_JFK_business():
    return _oneway("ow_TPE_JFK_business", "TPE", "JFK", "business")

def test_ow_TPE_JFK_first():
    return _oneway("ow_TPE_JFK_first", "TPE", "JFK", "first")

def test_ow_TPE_LAX_economy():
    return _oneway("ow_TPE_LAX_economy", "TPE", "LAX", "economy")

def test_ow_TPE_LAX_business():
    return _oneway("ow_TPE_LAX_business", "TPE", "LAX", "business")

def test_ow_TPE_SFO_economy():
    return _oneway("ow_TPE_SFO_economy", "TPE", "SFO", "economy")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: ROUND-TRIP (來回)
# ═══════════════════════════════════════════════════════════════════════════

def _roundtrip(name: str, frm: str, to: str, seat: str,
               date_out: str = DATE_RT_OUT, date_ret: str = DATE_RT_RET) -> TestResult:
    """Generic round-trip test."""
    section = "roundtrip"
    try:
        query = create_query(
            flights=[
                FlightQuery(date=date_out, from_airport=frm, to_airport=to),
                FlightQuery(date=date_ret, from_airport=to, to_airport=frm),
            ],
            trip="round-trip",
            seat=seat,
            passengers=PAX1,
            language="en-US",
            currency="USD",
        )

        # Step 1: outbound
        outbound = get_flights(query)
        _assert_flights_list(outbound, f"{frm}→{to} outbound")
        assert outbound[0].select_token is not None, \
            f"{frm}→{to} outbound[0].select_token 應存在"

        outbound_samples = _samples_from_results(outbound, f"去程 {frm}→{to}")

        time.sleep(1.5)

        # Step 2: return
        return_query = select_flight(query, outbound[0])
        assert return_query.tfu != "", "ReturnQuery.tfu 不應為空"

        returning = get_return_flights(return_query)
        _assert_flights_list(returning, f"{to}→{frm} return")

        return_samples = _samples_from_results(returning, f"回程 {to}→{frm}")

        return TestResult(
            name=name,
            passed=True,
            section=section,
            note=f"{frm}↔{to} {seat} — 去程 {len(outbound)} 筆，回程 {len(returning)} 筆",
            sample_data=outbound_samples + return_samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, section=section, error=str(e), note="斷言失敗")
    except Exception:
        return TestResult(name=name, passed=False, section=section, error=traceback.format_exc())


# ── Japan round-trips ─────────────────────────────────────────────────────────

def test_rt_TPE_NRT_economy():
    return _roundtrip("rt_TPE_NRT_economy", "TPE", "NRT", "economy")

def test_rt_TPE_NRT_business():
    return _roundtrip("rt_TPE_NRT_business", "TPE", "NRT", "business")

def test_rt_TPE_KIX_economy():
    return _roundtrip("rt_TPE_KIX_economy", "TPE", "KIX", "economy")


# ── Europe round-trips ────────────────────────────────────────────────────────

def test_rt_TPE_LHR_economy():
    return _roundtrip("rt_TPE_LHR_economy", "TPE", "LHR", "economy")

def test_rt_TPE_LHR_business():
    return _roundtrip("rt_TPE_LHR_business", "TPE", "LHR", "business")

def test_rt_TPE_CDG_economy():
    return _roundtrip("rt_TPE_CDG_economy", "TPE", "CDG", "economy")

def test_rt_TPE_FRA_economy():
    return _roundtrip("rt_TPE_FRA_economy", "TPE", "FRA", "economy")


# ── Americas round-trips ──────────────────────────────────────────────────────

def test_rt_TPE_JFK_economy():
    return _roundtrip("rt_TPE_JFK_economy", "TPE", "JFK", "economy")

def test_rt_TPE_JFK_business():
    return _roundtrip("rt_TPE_JFK_business", "TPE", "JFK", "business")

def test_rt_TPE_LAX_economy():
    return _roundtrip("rt_TPE_LAX_economy", "TPE", "LAX", "economy")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: MULTI-CITY (多腿)
# ═══════════════════════════════════════════════════════════════════════════
# Strategy: get_flights_multicity_chained → total trip price (single RPC call)
#           get_flights_multicity → per-leg details (independent queries)

def _multicity(
    name: str,
    legs_input: list[FlightQuery],
    seat: str = "economy",
    label: str = "",
) -> TestResult:
    """
    Generic multi-city test.
    Step 1: get total trip price via get_flights_multicity_chained (single RPC).
    Step 2: get per-leg flight details via get_flights_multicity (independent).
    """
    section = "multicity"
    n = len(legs_input)
    route_label = label or " → ".join(
        f"{l.from_airport}" for l in legs_input
    ) + f" → {legs_input[-1].to_airport}"

    try:
        # ── Step 1: total trip price via RPC ───────────────────────────────
        chained = get_flights_multicity_chained(
            legs_input,
            seat=seat,
            language="en-US",
            currency="USD",
        )
        assert len(chained) == n, \
            f"chained 應回傳 {n} 個 leg，實際 {len(chained)}"
        assert chained[0].total_price is not None and chained[0].total_price > 0, \
            f"total_price 應大於 0，實際 {chained[0].total_price}"
        assert len(chained[0].flights) > 0, "chained[0].flights 應有至少 1 個選項"

        # Shared flights reference (single RPC call guarantee)
        for i in range(1, n):
            assert chained[0].flights is chained[i].flights, \
                f"chained[0].flights 應與 chained[{i}].flights 為同一物件"

        total_price = chained[0].total_price
        first_leg_options = len(chained[0].flights)
        chained_samples = [
            f"[RPC] 整趟最低總價：{total_price} USD",
            f"[RPC] 第一腿可選選項數：{first_leg_options}",
        ]
        best_f = chained[0].flights[0]
        if best_f.flights:
            seg = best_f.flights[0]
            chained_samples.append(
                f"[RPC] 第一選項第一航段：{seg.from_airport.code}→{seg.to_airport.code} "
                f"({seg.airline_code}, {seg.duration}min)"
            )

        time.sleep(2)

        # ── Step 2: per-leg details via independent queries ────────────────
        per_leg = get_flights_multicity(
            flights=legs_input,
            seat=seat,
            passengers=PAX1,
            language="en-US",
            currency="USD",
            delay=1.5,
        )
        assert len(per_leg) == n, \
            f"per_leg 應回傳 {n} 個 leg，實際 {len(per_leg)}"
        for i, leg in enumerate(per_leg):
            assert leg.results is not None, f"第 {i+1} 腿 results 不應為 None"

        per_leg_samples = []
        for leg in per_leg:
            results = leg.results or []
            if results:
                cheapest = min(results, key=lambda f: f.price)
                seg = results[0].flights[0] if results[0].flights else None
                ac = seg.airline_code if seg else "N/A"
                per_leg_samples.append(
                    f"[獨立] 第 {leg.leg_index+1} 腿 {leg.from_airport}→{leg.to_airport}: "
                    f"{len(results)} 筆，最低 {cheapest.price} USD，airline={ac}"
                )
            else:
                per_leg_samples.append(
                    f"[獨立] 第 {leg.leg_index+1} 腿 {leg.from_airport}→{leg.to_airport}: 0 筆"
                )

        return TestResult(
            name=name,
            passed=True,
            section=section,
            note=f"{route_label} [{seat}] — 整趟總價 {total_price} USD",
            sample_data=chained_samples + per_leg_samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, section=section, error=str(e), note="斷言失敗")
    except Exception:
        return TestResult(name=name, passed=False, section=section, error=traceback.format_exc())


# ── Japan multi-city (日本多腿) ───────────────────────────────────────────────

def test_mc_TPE_NRT_KIX_TPE_economy():
    """3 legs: TPE→NRT→KIX→TPE, economy（日本境內多點）"""
    return _multicity(
        "mc_TPE_NRT_KIX_TPE_economy",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC3_L2, from_airport="NRT", to_airport="KIX"),
            FlightQuery(date=DATE_MC3_L3, from_airport="KIX", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→NRT→KIX→TPE",
    )

def test_mc_TPE_NRT_KIX_TPE_business():
    """3 legs: TPE→NRT→KIX→TPE, business class"""
    return _multicity(
        "mc_TPE_NRT_KIX_TPE_business",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC3_L2, from_airport="NRT", to_airport="KIX"),
            FlightQuery(date=DATE_MC3_L3, from_airport="KIX", to_airport="TPE"),
        ],
        seat="business",
        label="TPE→NRT→KIX→TPE",
    )


# ── Europe multi-city (歐洲多腿) ──────────────────────────────────────────────

def test_mc_TPE_LHR_CDG_TPE_economy():
    """3 legs: TPE→LHR→CDG→TPE, economy（英法雙城）"""
    return _multicity(
        "mc_TPE_LHR_CDG_TPE_economy",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="LHR"),
            FlightQuery(date=DATE_MC3_L2, from_airport="LHR", to_airport="CDG"),
            FlightQuery(date=DATE_MC3_L3, from_airport="CDG", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→LHR→CDG→TPE",
    )

def test_mc_TPE_LHR_CDG_TPE_business():
    """3 legs: TPE→LHR→CDG→TPE, business class"""
    return _multicity(
        "mc_TPE_LHR_CDG_TPE_business",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="LHR"),
            FlightQuery(date=DATE_MC3_L2, from_airport="LHR", to_airport="CDG"),
            FlightQuery(date=DATE_MC3_L3, from_airport="CDG", to_airport="TPE"),
        ],
        seat="business",
        label="TPE→LHR→CDG→TPE",
    )

def test_mc_TPE_LHR_FRA_CDG_TPE_economy():
    """4 legs: TPE→LHR→FRA→CDG→TPE, economy（歐洲三城）"""
    return _multicity(
        "mc_TPE_LHR_FRA_CDG_TPE_economy",
        [
            FlightQuery(date=DATE_MC4_L1, from_airport="TPE", to_airport="LHR"),
            FlightQuery(date=DATE_MC4_L2, from_airport="LHR", to_airport="FRA"),
            FlightQuery(date=DATE_MC4_L3, from_airport="FRA", to_airport="CDG"),
            FlightQuery(date=DATE_MC4_L4, from_airport="CDG", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→LHR→FRA→CDG→TPE",
    )


# ── Americas multi-city (美洲多腿) ────────────────────────────────────────────

def test_mc_TPE_JFK_LAX_TPE_economy():
    """3 legs: TPE→JFK→LAX→TPE, economy（美國東西岸）"""
    return _multicity(
        "mc_TPE_JFK_LAX_TPE_economy",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="JFK"),
            FlightQuery(date=DATE_MC3_L2, from_airport="JFK", to_airport="LAX"),
            FlightQuery(date=DATE_MC3_L3, from_airport="LAX", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→JFK→LAX→TPE",
    )

def test_mc_TPE_JFK_LAX_TPE_business():
    """3 legs: TPE→JFK→LAX→TPE, business class"""
    return _multicity(
        "mc_TPE_JFK_LAX_TPE_business",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="JFK"),
            FlightQuery(date=DATE_MC3_L2, from_airport="JFK", to_airport="LAX"),
            FlightQuery(date=DATE_MC3_L3, from_airport="LAX", to_airport="TPE"),
        ],
        seat="business",
        label="TPE→JFK→LAX→TPE",
    )


# ── Cross-regional multi-city (跨區域多腿) ────────────────────────────────────

def test_mc_TPE_NRT_LAX_TPE_economy():
    """3 legs: TPE→NRT→LAX→TPE, economy（亞太→美洲）"""
    return _multicity(
        "mc_TPE_NRT_LAX_TPE_economy",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC3_L2, from_airport="NRT", to_airport="LAX"),
            FlightQuery(date=DATE_MC3_L3, from_airport="LAX", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→NRT→LAX→TPE",
    )

def test_mc_TPE_LHR_JFK_TPE_economy():
    """3 legs: TPE→LHR→JFK→TPE, economy（歐洲→美洲）"""
    return _multicity(
        "mc_TPE_LHR_JFK_TPE_economy",
        [
            FlightQuery(date=DATE_MC3_L1, from_airport="TPE", to_airport="LHR"),
            FlightQuery(date=DATE_MC3_L2, from_airport="LHR", to_airport="JFK"),
            FlightQuery(date=DATE_MC3_L3, from_airport="JFK", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→LHR→JFK→TPE",
    )

def test_mc_TPE_NRT_LAX_LHR_TPE_economy():
    """4 legs: TPE→NRT→LAX→LHR→TPE, economy（亞洲→美洲→歐洲環球）"""
    return _multicity(
        "mc_TPE_NRT_LAX_LHR_TPE_economy",
        [
            FlightQuery(date=DATE_MC4_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC4_L2, from_airport="NRT", to_airport="LAX"),
            FlightQuery(date=DATE_MC4_L3, from_airport="LAX", to_airport="LHR"),
            FlightQuery(date=DATE_MC4_L4, from_airport="LHR", to_airport="TPE"),
        ],
        seat="economy",
        label="TPE→NRT→LAX→LHR→TPE",
    )

def test_mc_TPE_NRT_LAX_LHR_TPE_business():
    """4 legs: TPE→NRT→LAX→LHR→TPE, business class（環球商務艙）"""
    return _multicity(
        "mc_TPE_NRT_LAX_LHR_TPE_business",
        [
            FlightQuery(date=DATE_MC4_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC4_L2, from_airport="NRT", to_airport="LAX"),
            FlightQuery(date=DATE_MC4_L3, from_airport="LAX", to_airport="LHR"),
            FlightQuery(date=DATE_MC4_L4, from_airport="LHR", to_airport="TPE"),
        ],
        seat="business",
        label="TPE→NRT→LAX→LHR→TPE",
    )

def test_mc_TPE_JFK_LHR_CDG_NRT_TPE_economy():
    """
    5 legs: TPE→JFK→LHR→CDG→NRT→TPE (美洲+歐洲+日本環球大行程)
    Tests the upper end of supported multi-city legs.
    """
    section = "multicity"
    name = "mc_TPE_JFK_LHR_CDG_NRT_TPE_economy"
    legs_input = [
        FlightQuery(date="2026-07-15", from_airport="TPE", to_airport="JFK"),
        FlightQuery(date="2026-07-22", from_airport="JFK", to_airport="LHR"),
        FlightQuery(date="2026-07-29", from_airport="LHR", to_airport="CDG"),
        FlightQuery(date="2026-08-05", from_airport="CDG", to_airport="NRT"),
        FlightQuery(date="2026-08-10", from_airport="NRT", to_airport="TPE"),
    ]
    try:
        # Only RPC chained (total price) — per-leg independent queries add too much delay
        chained = get_flights_multicity_chained(
            legs_input,
            seat="economy",
            language="en-US",
            currency="USD",
        )
        assert len(chained) == 5, f"應回傳 5 個 leg，實際 {len(chained)}"
        assert chained[0].total_price is not None and chained[0].total_price > 0
        assert len(chained[0].flights) > 0

        total_price = chained[0].total_price
        return TestResult(
            name=name,
            passed=True,
            section=section,
            note=f"5 腿環球行程，整趟總價 {total_price} USD",
            sample_data=[
                f"[RPC] 5 腿整趟最低總價：{total_price} USD",
                f"[RPC] 第一腿可選選項數：{len(chained[0].flights)}",
                f"[RPC] shared flights reference: chained[0] is chained[4]: "
                f"{chained[0].flights is chained[4].flights}",
            ],
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, section=section, error=str(e), note="斷言失敗")
    except Exception:
        return TestResult(name=name, passed=False, section=section, error=traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════════════════════════════════════

SECTION_LABELS = {
    "oneway":    "單程 (One-way)",
    "roundtrip": "來回 (Round-trip)",
    "multicity": "多腿 (Multi-city)",
}


def generate_report(results: list[TestResult], run_at: str) -> str:
    lines = [
        "# 台灣出發全方位整合測試報告",
        "",
        f"**執行時間**：{run_at}",
        "",
        "測試涵蓋範圍：",
        "- **目的地**：日本（NRT/KIX）、歐洲（LHR/CDG/FRA）、美洲（JFK/LAX/SFO）",
        "- **艙等**：economy / premium-economy / business / first",
        "- **行程類型**：單程、來回、多腿（3–5 腿）",
        "",
        "---",
        "",
    ]

    # Summary table
    passed_total = sum(1 for r in results if r.passed)
    lines += [
        "## 摘要",
        "",
        "| # | 測試 | 類型 | 狀態 | 說明 |",
        "|---|------|------|------|------|",
    ]
    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r.passed else "❌ FAIL"
        sec = SECTION_LABELS.get(r.section, r.section)
        note = r.note.replace("|", "\\|")
        lines.append(f"| {i} | `{r.name}` | {sec} | {status} | {note} |")

    lines += [
        "",
        f"**總計：{passed_total} / {len(results)} 通過**",
        "",
        "---",
        "",
    ]

    # Per-section breakdown
    for section_key, section_label in SECTION_LABELS.items():
        section_results = [r for r in results if r.section == section_key]
        if not section_results:
            continue
        sec_pass = sum(1 for r in section_results if r.passed)
        lines += [
            f"## {section_label}",
            "",
            f"通過：{sec_pass} / {len(section_results)}",
            "",
        ]
        for r in section_results:
            status = "PASS ✅" if r.passed else "FAIL ❌"
            lines += [f"### `{r.name}`", "", f"**狀態**：{status}"]
            if r.note:
                lines.append(f"**說明**：{r.note}")
            if r.error:
                lines += ["", "**錯誤**：", "```", r.error, "```"]
            if r.sample_data:
                lines += ["", "**樣本資料**："]
                for item in r.sample_data:
                    lines.append(f"- {item}")
            lines += ["", "---", ""]

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Test registry
# ═══════════════════════════════════════════════════════════════════════════

# (label, function, pre-sleep seconds)
# Pre-sleep avoids rate limiting between consecutive live API calls.
ONEWAY_TESTS = [
    # Japan
    ("test_ow_TPE_NRT_economy",          test_ow_TPE_NRT_economy,          0),
    ("test_ow_TPE_NRT_premium_economy",  test_ow_TPE_NRT_premium_economy,  1.5),
    ("test_ow_TPE_NRT_business",         test_ow_TPE_NRT_business,         1.5),
    ("test_ow_TPE_NRT_first",            test_ow_TPE_NRT_first,            1.5),
    ("test_ow_TPE_KIX_economy",          test_ow_TPE_KIX_economy,          1.5),
    ("test_ow_TPE_KIX_business",         test_ow_TPE_KIX_business,         1.5),
    # Europe
    ("test_ow_TPE_LHR_economy",          test_ow_TPE_LHR_economy,          2.0),
    ("test_ow_TPE_LHR_premium_economy",  test_ow_TPE_LHR_premium_economy,  1.5),
    ("test_ow_TPE_LHR_business",         test_ow_TPE_LHR_business,         1.5),
    ("test_ow_TPE_LHR_first",            test_ow_TPE_LHR_first,            1.5),
    ("test_ow_TPE_CDG_economy",          test_ow_TPE_CDG_economy,          1.5),
    ("test_ow_TPE_CDG_business",         test_ow_TPE_CDG_business,         1.5),
    ("test_ow_TPE_FRA_economy",          test_ow_TPE_FRA_economy,          1.5),
    # Americas
    ("test_ow_TPE_JFK_economy",          test_ow_TPE_JFK_economy,          2.0),
    ("test_ow_TPE_JFK_premium_economy",  test_ow_TPE_JFK_premium_economy,  1.5),
    ("test_ow_TPE_JFK_business",         test_ow_TPE_JFK_business,         1.5),
    ("test_ow_TPE_JFK_first",            test_ow_TPE_JFK_first,            1.5),
    ("test_ow_TPE_LAX_economy",          test_ow_TPE_LAX_economy,          1.5),
    ("test_ow_TPE_LAX_business",         test_ow_TPE_LAX_business,         1.5),
    ("test_ow_TPE_SFO_economy",          test_ow_TPE_SFO_economy,          1.5),
]

ROUNDTRIP_TESTS = [
    # Japan
    ("test_rt_TPE_NRT_economy",  test_rt_TPE_NRT_economy,  2.0),
    ("test_rt_TPE_NRT_business", test_rt_TPE_NRT_business, 2.0),
    ("test_rt_TPE_KIX_economy",  test_rt_TPE_KIX_economy,  2.0),
    # Europe
    ("test_rt_TPE_LHR_economy",  test_rt_TPE_LHR_economy,  2.0),
    ("test_rt_TPE_LHR_business", test_rt_TPE_LHR_business, 2.0),
    ("test_rt_TPE_CDG_economy",  test_rt_TPE_CDG_economy,  2.0),
    ("test_rt_TPE_FRA_economy",  test_rt_TPE_FRA_economy,  2.0),
    # Americas
    ("test_rt_TPE_JFK_economy",  test_rt_TPE_JFK_economy,  2.0),
    ("test_rt_TPE_JFK_business", test_rt_TPE_JFK_business, 2.0),
    ("test_rt_TPE_LAX_economy",  test_rt_TPE_LAX_economy,  2.0),
]

MULTICITY_TESTS = [
    # Japan
    ("test_mc_TPE_NRT_KIX_TPE_economy",          test_mc_TPE_NRT_KIX_TPE_economy,          2.0),
    ("test_mc_TPE_NRT_KIX_TPE_business",         test_mc_TPE_NRT_KIX_TPE_business,         3.0),
    # Europe
    ("test_mc_TPE_LHR_CDG_TPE_economy",          test_mc_TPE_LHR_CDG_TPE_economy,          2.0),
    ("test_mc_TPE_LHR_CDG_TPE_business",         test_mc_TPE_LHR_CDG_TPE_business,         3.0),
    ("test_mc_TPE_LHR_FRA_CDG_TPE_economy",      test_mc_TPE_LHR_FRA_CDG_TPE_economy,      3.0),
    # Americas
    ("test_mc_TPE_JFK_LAX_TPE_economy",          test_mc_TPE_JFK_LAX_TPE_economy,          2.0),
    ("test_mc_TPE_JFK_LAX_TPE_business",         test_mc_TPE_JFK_LAX_TPE_business,         3.0),
    # Cross-regional
    ("test_mc_TPE_NRT_LAX_TPE_economy",          test_mc_TPE_NRT_LAX_TPE_economy,          2.0),
    ("test_mc_TPE_LHR_JFK_TPE_economy",          test_mc_TPE_LHR_JFK_TPE_economy,          3.0),
    ("test_mc_TPE_NRT_LAX_LHR_TPE_economy",      test_mc_TPE_NRT_LAX_LHR_TPE_economy,      3.0),
    ("test_mc_TPE_NRT_LAX_LHR_TPE_business",     test_mc_TPE_NRT_LAX_LHR_TPE_business,     3.0),
    ("test_mc_TPE_JFK_LHR_CDG_NRT_TPE_economy",  test_mc_TPE_JFK_LHR_CDG_NRT_TPE_economy,  3.0),
]

ALL_TESTS = ONEWAY_TESTS + ROUNDTRIP_TESTS + MULTICITY_TESTS


# ═══════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════

def run_section(test_list, section_name: str) -> list[TestResult]:
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n = len(test_list)
    print(f"\n{'='*70}")
    print(f"  {section_name}  ({n} 個測試)  —  {run_at}")
    print(f"{'='*70}\n")

    results = []
    for i, (label, fn, sleep_before) in enumerate(test_list):
        if sleep_before > 0:
            print(f"  [等待 {sleep_before:.1f}s 避免限速...]")
            time.sleep(sleep_before)

        print(f"  [{i+1:>2}/{n}] {label} ...", end=" ", flush=True)
        result = fn()
        status = "PASS ✅" if result.passed else "FAIL ❌"
        print(status)
        if not result.passed:
            print(f"         原因：{result.note or '(無說明)'}")
            if result.error:
                last = [l for l in result.error.strip().splitlines() if l]
                if last:
                    print(f"         {last[-1]}")
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    print(f"\n  ── {section_name} 結果：{passed}/{n} 通過\n")
    return results


def main():
    parser = argparse.ArgumentParser(description="台灣出發全方位整合測試")
    parser.add_argument(
        "--section",
        choices=["oneway", "roundtrip", "multicity", "all"],
        default="all",
        help="執行哪個測試區塊（預設 all）",
    )
    args = parser.parse_args()

    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    section_map = {
        "oneway":    ("單程測試",   ONEWAY_TESTS),
        "roundtrip": ("來回測試",   ROUNDTRIP_TESTS),
        "multicity": ("多腿測試",   MULTICITY_TESTS),
    }

    if args.section == "all":
        sections = list(section_map.items())
    else:
        sections = [(args.section, section_map[args.section])]

    all_results: list[TestResult] = []
    for _key, (section_name, test_list) in sections:
        results = run_section(test_list, section_name)
        all_results.extend(results)

    print(f"\n{'='*70}")
    passed_total = sum(1 for r in all_results if r.passed)
    print(f"  總結果：{passed_total} / {len(all_results)} 通過")
    print(f"{'='*70}\n")

    report = generate_report(all_results, run_at)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"報告已寫入：{REPORT_PATH}\n")

    if passed_total < len(all_results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
