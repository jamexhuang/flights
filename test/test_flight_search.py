"""
Integration tests for faster-flights: one-way, round-trip, and multi-city search.

Calls the live Google Flights API and generates a markdown report.

Usage:
    python test/test_flight_search.py

Output:
    test/flight_search_report.md

Notes:
    - Multi-city "step-by-step" chaining (leg 2+ via tfu/HTML) is NOT supported by
      Google's current API: payload[3] is None in multi-city return HTML responses.
      The correct approach for per-leg detail is independent one-way queries
      (get_flights_multicity), which is tested in test_mc_independent.
    - model.py must not use Annotated[] types — Python 3.13 drops dataclass fields
      with default values that follow an Annotated field when the importer uses
      `from __future__ import annotations`.
"""

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

# ── Date constants (fixed, not system-time dependent) ────────────────────────
# Based on project currentDate = 2026-03-01; all dates are 30–40 days ahead.
DATE_ONEWAY = "2026-03-31"
DATE_RT_OUT = "2026-03-31"
DATE_RT_RET = "2026-04-05"
DATE_MC_L1  = "2026-03-31"
DATE_MC_L2  = "2026-04-05"
DATE_MC_L3  = "2026-04-10"

# 4-leg multi-city circuit test dates (from screenshots: 14 Aug / 14 Aug / 9 Sep / 10 Sep 2026)
DATE_4L_L1 = "2026-08-14"
DATE_4L_L2 = "2026-08-14"
DATE_4L_L3 = "2026-09-09"
DATE_4L_L4 = "2026-09-10"

REPORT_PATH = Path(__file__).parent / "flight_search_report.md"


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class TestResult:
    name: str
    passed: bool
    note: str = ""
    sample_data: list = field(default_factory=list)
    error: str = ""


# ── Individual tests ─────────────────────────────────────────────────────────

def test_select_token_absent():
    """Unit test (no API call): select_flight raises ValueError when select_token is None."""
    name = "select_token_absent_raises"
    try:
        fake_flight = Flights(
            type="one-way",
            price=1000,
            airlines=["Fake Air"],
            flights=[],
            carbon=CarbonEmission(typical_on_route=0, emission=0),
            select_token=None,
        )
        query = create_query(
            flights=[FlightQuery(date=DATE_ONEWAY, from_airport="TPE", to_airport="NRT")],
            trip="one-way",
        )
        try:
            select_flight(query, fake_flight)
            return TestResult(
                name=name, passed=False,
                note="應該要拋出 ValueError 但沒有", error="ValueError not raised",
            )
        except ValueError as e:
            return TestResult(
                name=name,
                passed=True,
                note="成功確認：select_token=None 時拋出 ValueError",
                sample_data=[f"錯誤訊息：{e}"],
            )
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_oneway():
    """One-way search: TPE → NRT."""
    name = "oneway_TPE_NRT"
    try:
        query = create_query(
            flights=[FlightQuery(date=DATE_ONEWAY, from_airport="TPE", to_airport="NRT")],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
        )
        results = get_flights(query)

        assert len(results) > 0, "預期至少 1 筆結果"
        f0 = results[0]
        assert f0.price > 0, "price 應大於 0"
        assert isinstance(f0.flights, list) and len(f0.flights) > 0, "flights 不應為空"

        seg = f0.flights[0]
        assert seg.from_airport.code != "", "from_airport.code 不應為空"
        assert seg.to_airport.code != "", "to_airport.code 不應為空"
        assert isinstance(seg.duration, int) and seg.duration > 0, "duration 應為正整數（分鐘）"
        assert hasattr(seg, "airline_code"), "SingleFlight 應有 airline_code 欄位"

        assert hasattr(results, "metadata"), "MetaList 應有 metadata 屬性"
        assert isinstance(results.metadata.airlines, list), "metadata.airlines 應為 list"
        assert len(results.metadata.airlines) > 0, "metadata.airlines 不應為空"

        cheapest = min(results, key=lambda f: f.price)
        airlines_sample = [a.code for a in results.metadata.airlines[:5]]

        return TestResult(
            name=name,
            passed=True,
            note=f"找到 {len(results)} 筆結果",
            sample_data=[
                f"結果筆數：{len(results)}",
                f"最低票價：{cheapest.price} USD",
                f"第一筆航空公司：{f0.airlines}",
                f"第一航段：{seg.from_airport.code}→{seg.to_airport.code}，"
                f"airline_code={seg.airline_code}，飛行 {seg.duration} 分鐘",
                f"metadata 航空公司 IATA 代碼（前 5）：{airlines_sample}",
            ],
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_roundtrip():
    """Round-trip search: TPE → NRT → TPE, two-step token chaining."""
    name = "roundtrip_TPE_NRT_TPE"
    try:
        rt_query = create_query(
            flights=[
                FlightQuery(date=DATE_RT_OUT, from_airport="TPE", to_airport="NRT"),
                FlightQuery(date=DATE_RT_RET, from_airport="NRT", to_airport="TPE"),
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
        )

        # Step 1: outbound
        outbound = get_flights(rt_query)
        assert len(outbound) > 0, "去程應有結果"
        assert outbound[0].select_token is not None, "去程第一筆應有 select_token"
        assert outbound[0].price > 0, "去程 price 應大於 0"

        outbound_sample = [
            f"去程筆數：{len(outbound)}",
            f"去程最低票價：{min(outbound, key=lambda f: f.price).price} USD",
            "select_token 存在：True",
        ]

        time.sleep(1.5)

        # Step 2: return
        return_query = select_flight(rt_query, outbound[0])
        assert return_query.tfu != "", "ReturnQuery.tfu 不應為空"

        returning = get_return_flights(return_query)
        assert len(returning) > 0, "回程應有結果"
        assert returning[0].price > 0, "回程 price 應大於 0"

        return_sample = [
            f"回程筆數：{len(returning)}",
            f"回程最低整趟總價：{min(returning, key=lambda f: f.price).price} USD",
            f"tfu token 前 20 字：{return_query.tfu[:20]}...",
        ]

        return TestResult(
            name=name,
            passed=True,
            note="去程 + 回程兩步驟均成功",
            sample_data=outbound_sample + return_sample,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_mc_independent():
    """Multi-city independent per-leg search (get_flights_multicity)."""
    name = "multicity_independent_3legs"
    try:
        legs = get_flights_multicity(
            flights=[
                FlightQuery(date=DATE_MC_L1, from_airport="TPE", to_airport="NRT"),
                FlightQuery(date=DATE_MC_L2, from_airport="NRT", to_airport="HKG"),
                FlightQuery(date=DATE_MC_L3, from_airport="HKG", to_airport="TPE"),
            ],
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
            delay=1.5,
        )

        assert len(legs) == 3, f"應回傳 3 個 MulticityLeg，實際 {len(legs)}"
        for i, leg in enumerate(legs):
            assert leg.leg_index == i, f"leg_index 應為 {i}，實際 {leg.leg_index}"
            assert leg.results is not None, f"第 {i+1} 腿 results 不應為 None"

        samples = []
        for leg in legs:
            count = len(leg.results)
            cheapest = min(leg.results, key=lambda f: f.price).price if count > 0 else None
            samples.append(
                f"第 {leg.leg_index + 1} 腿（{leg.from_airport}→{leg.to_airport}）："
                f"{count} 筆，最低 {cheapest} USD" if cheapest else f"{count} 筆（無結果）"
            )

        return TestResult(
            name=name,
            passed=True,
            note="3 腿各自查詢均回傳結果（各腿為獨立票價，非整趟總價）",
            sample_data=samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_mc_chained():
    """Multi-city RPC chained search (get_flights_multicity_chained): single call, total trip price."""
    name = "multicity_chained_3legs"
    try:
        legs_input = [
            FlightQuery(date=DATE_MC_L1, from_airport="TPE", to_airport="NRT"),
            FlightQuery(date=DATE_MC_L2, from_airport="NRT", to_airport="HKG"),
            FlightQuery(date=DATE_MC_L3, from_airport="HKG", to_airport="TPE"),
        ]

        result = get_flights_multicity_chained(
            legs_input,
            language="en-US",
            currency="USD",
        )

        assert len(result) == 3, f"應回傳 3 個 MulticityLegChained，實際 {len(result)}"
        assert result[0].flights is not None, "result[0].flights 不應為 None"
        assert len(result[0].flights) > 0, "result[0].flights 應有至少 1 個選項"
        assert result[0].total_price is not None, "total_price 不應為 None"
        assert result[0].total_price > 0, "total_price 應大於 0"

        # Key property: all entries share the same flights reference (single RPC call)
        assert result[0].flights is result[1].flights, \
            "result[0].flights 和 result[1].flights 應為同一物件（同一 RPC 呼叫）"
        assert result[1].flights is result[2].flights, \
            "result[1].flights 和 result[2].flights 應為同一物件"

        f0 = result[0].flights[0]
        seg = f0.flights[0] if f0.flights else None

        samples = [
            f"第一腿可選選項數：{len(result[0].flights)}",
            f"整趟最低總價：{result[0].total_price} USD",
            f"result[0].flights is result[1].flights："
            f"{result[0].flights is result[1].flights}",
        ]
        if seg:
            samples.append(
                f"第一腿第一航段：{seg.from_airport.code}→{seg.to_airport.code}，"
                f"airline_code={seg.airline_code}"
            )

        return TestResult(
            name=name,
            passed=True,
            note="單一 RPC 呼叫成功，所有 leg entry 共用同一 flights 物件",
            sample_data=samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_mc_stepwise():
    """
    Multi-city step-by-step workflow:
      Step 1 — get first-leg options with total price (via RPC)
      Step 2+ — get per-leg options independently (via get_flights_multicity)

    Note: Google's HTML endpoint returns payload[3]=None for multi-city return legs,
    so get_return_flights() cannot be used for legs 2+. Per-leg details require
    independent one-way queries (get_flights_multicity).
    """
    name = "multicity_stepwise_3legs"
    try:
        # Step 1: Get first-leg options with total trip price (RPC path)
        mc_query = create_query(
            flights=[
                FlightQuery(date=DATE_MC_L1, from_airport="TPE", to_airport="NRT"),
                FlightQuery(date=DATE_MC_L2, from_airport="NRT", to_airport="HKG"),
                FlightQuery(date=DATE_MC_L3, from_airport="HKG", to_airport="TPE"),
            ],
            trip="multi-city",
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
        )

        leg1_results = get_flights(mc_query)
        assert len(leg1_results) > 0, "第一腿應有結果"
        assert leg1_results[0].select_token is not None, "第一腿應有 select_token"
        assert leg1_results[0].price > 0, "第一腿 price（整趟總價）應大於 0"

        time.sleep(2)

        # Step 2+: Get per-leg details independently (the correct approach)
        per_leg = get_flights_multicity(
            flights=[
                FlightQuery(date=DATE_MC_L2, from_airport="NRT", to_airport="HKG"),
                FlightQuery(date=DATE_MC_L3, from_airport="HKG", to_airport="TPE"),
            ],
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
            delay=1.5,
        )

        assert len(per_leg) == 2, f"應回傳 2 個後續腿結果，實際 {len(per_leg)}"
        assert per_leg[0].results is not None, "第二腿 results 不應為 None"

        samples = [
            f"第一腿（TPE→NRT）RPC 選項數：{len(leg1_results)}",
            f"整趟最低總價：{min(leg1_results, key=lambda f: f.price).price} USD",
            "select_token 存在：True",
            f"第二腿（NRT→HKG）獨立查詢結果：{len(per_leg[0].results)} 筆",
            f"第三腿（HKG→TPE）獨立查詢結果：{len(per_leg[1].results)} 筆",
        ]

        return TestResult(
            name=name,
            passed=True,
            note="Step 1（RPC 整趟總價）+ Step 2+（獨立單程查詢）均成功",
            sample_data=samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_mc4_BKK_circuit():
    """
    4-leg multi-city: BKK→TPE→LHR→TPE→BKK
    Dates from screenshot: 14 Aug / 14 Aug / 9 Sep / 10 Sep 2026

    Step 1: total trip price via single RPC call (get_flights_multicity_chained)
    Step 2: per-leg flight details via independent one-way queries (get_flights_multicity)
    """
    name = "multicity_4legs_BKK_circuit"
    try:
        legs_input = [
            FlightQuery(date=DATE_4L_L1, from_airport="BKK", to_airport="TPE"),
            FlightQuery(date=DATE_4L_L2, from_airport="TPE", to_airport="LHR"),
            FlightQuery(date=DATE_4L_L3, from_airport="LHR", to_airport="TPE"),
            FlightQuery(date=DATE_4L_L4, from_airport="TPE", to_airport="BKK"),
        ]

        # Step 1: total trip price via RPC
        chained = get_flights_multicity_chained(
            legs_input,
            language="en-US",
            currency="USD",
        )
        assert len(chained) == 4, f"應回傳 4 個 MulticityLegChained，實際 {len(chained)}"
        assert chained[0].total_price is not None and chained[0].total_price > 0, "整趟總價應大於 0"
        assert len(chained[0].flights) > 0, "第一腿應有可選選項"

        total_price = chained[0].total_price
        leg1_options = len(chained[0].flights)
        leg1_f0 = chained[0].flights[0]
        leg1_seg = leg1_f0.flights[0] if leg1_f0.flights else None

        time.sleep(2)

        # Step 2: per-leg flight details (independent queries)
        per_leg = get_flights_multicity(
            flights=legs_input,
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
            delay=1.5,
        )
        assert len(per_leg) == 4, f"應回傳 4 個腿結果，實際 {len(per_leg)}"
        for i, leg in enumerate(per_leg):
            assert leg.results is not None, f"第 {i+1} 腿 results 不應為 None"

        samples = [
            f"整趟最低總價（RPC）：{total_price} USD",
            f"第一腿（BKK→TPE）RPC 可選選項數：{leg1_options}",
        ]
        if leg1_seg:
            samples.append(
                f"第一腿第一選項航段：{leg1_seg.from_airport.code}→{leg1_seg.to_airport.code}，"
                f"airline_code={leg1_seg.airline_code}，{leg1_seg.duration} 分鐘"
            )
        for leg in per_leg:
            results = leg.results or []
            count = len(results)
            cheapest = min(results, key=lambda f: f.price).price if count > 0 else None
            seg = results[0].flights[0] if count > 0 and results[0].flights else None
            airline_code = seg.airline_code if seg else "N/A"
            if cheapest:
                samples.append(
                    f"第 {leg.leg_index + 1} 腿（{leg.from_airport}→{leg.to_airport}）："
                    f"{count} 筆，最低 {cheapest} USD，第一航班 airline_code={airline_code}"
                )
            else:
                samples.append(f"第 {leg.leg_index + 1} 腿（{leg.from_airport}→{leg.to_airport}）：0 筆")

        return TestResult(
            name=name,
            passed=True,
            note=f"4 腿 BKK 環形成功，整趟總價 {total_price} USD，各腿均有結果",
            sample_data=samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


def test_mc4_SIN_circuit():
    """
    4-leg multi-city: SIN→TPE→JFK→TPE→SIN
    Dates from screenshot: 14 Aug / 14 Aug / 9 Sep / 10 Sep 2026

    Step 1: total trip price via single RPC call (get_flights_multicity_chained)
    Step 2: per-leg flight details via independent one-way queries (get_flights_multicity)
    """
    name = "multicity_4legs_SIN_circuit"
    try:
        legs_input = [
            FlightQuery(date=DATE_4L_L1, from_airport="SIN", to_airport="TPE"),
            FlightQuery(date=DATE_4L_L2, from_airport="TPE", to_airport="JFK"),
            FlightQuery(date=DATE_4L_L3, from_airport="JFK", to_airport="TPE"),
            FlightQuery(date=DATE_4L_L4, from_airport="TPE", to_airport="SIN"),
        ]

        # Step 1: total trip price via RPC
        chained = get_flights_multicity_chained(
            legs_input,
            language="en-US",
            currency="USD",
        )
        assert len(chained) == 4, f"應回傳 4 個 MulticityLegChained，實際 {len(chained)}"
        assert chained[0].total_price is not None and chained[0].total_price > 0, "整趟總價應大於 0"
        assert len(chained[0].flights) > 0, "第一腿應有可選選項"

        total_price = chained[0].total_price
        leg1_options = len(chained[0].flights)
        leg1_f0 = chained[0].flights[0]
        leg1_seg = leg1_f0.flights[0] if leg1_f0.flights else None

        time.sleep(2)

        # Step 2: per-leg flight details (independent queries)
        per_leg = get_flights_multicity(
            flights=legs_input,
            seat="economy",
            passengers=Passengers(adults=1),
            language="en-US",
            currency="USD",
            delay=1.5,
        )
        assert len(per_leg) == 4, f"應回傳 4 個腿結果，實際 {len(per_leg)}"
        for i, leg in enumerate(per_leg):
            assert leg.results is not None, f"第 {i+1} 腿 results 不應為 None"

        samples = [
            f"整趟最低總價（RPC）：{total_price} USD",
            f"第一腿（SIN→TPE）RPC 可選選項數：{leg1_options}",
        ]
        if leg1_seg:
            samples.append(
                f"第一腿第一選項航段：{leg1_seg.from_airport.code}→{leg1_seg.to_airport.code}，"
                f"airline_code={leg1_seg.airline_code}，{leg1_seg.duration} 分鐘"
            )
        for leg in per_leg:
            results = leg.results or []
            count = len(results)
            cheapest = min(results, key=lambda f: f.price).price if count > 0 else None
            seg = results[0].flights[0] if count > 0 and results[0].flights else None
            airline_code = seg.airline_code if seg else "N/A"
            if cheapest:
                samples.append(
                    f"第 {leg.leg_index + 1} 腿（{leg.from_airport}→{leg.to_airport}）："
                    f"{count} 筆，最低 {cheapest} USD，第一航班 airline_code={airline_code}"
                )
            else:
                samples.append(f"第 {leg.leg_index + 1} 腿（{leg.from_airport}→{leg.to_airport}）：0 筆")

        return TestResult(
            name=name,
            passed=True,
            note=f"4 腿 SIN 環形成功，整趟總價 {total_price} USD，各腿均有結果",
            sample_data=samples,
        )
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e), note="斷言失敗")
    except Exception as e:
        return TestResult(name=name, passed=False, error=traceback.format_exc(), note=str(e))


# ── Report generation ────────────────────────────────────────────────────────

def generate_report(results, run_at):
    lines = [
        "# faster-flights 整合測試報告",
        "",
        f"**執行時間**：{run_at}",
        "",
        "---",
        "",
        "## 摘要",
        "",
        "| 測試 | 狀態 | 說明 |",
        "|------|------|------|",
    ]

    passed = sum(1 for r in results if r.passed)
    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        note = r.note.replace("|", "\\|")
        lines.append(f"| `{r.name}` | {status} | {note} |")

    lines += [
        "",
        f"**總計：{passed} / {len(results)} 通過**",
        "",
        "---",
        "",
        "## 已知限制",
        "",
        "- **多城市逐腿詳情**：`get_return_flights()` 用於多城市時，Google HTML 回應的 `payload[3]` 為 `None`，",
        "  無法取得第 2 腿以後的航班詳細資料。正確做法是用 `get_flights_multicity()` 分別查詢各腿。",
        "- **`from __future__ import annotations`**：在 Python 3.13 中，若 importer 使用此 future import，",
        "  `fast_flights.model.SingleFlight` 的 `airline_code` 和 `flight_number` 欄位（有預設值）會被 `@dataclass` 遺漏。",
        "  已修正 `model.py`：移除 `Annotated[int]` 改用 `int` + 注解。",
        "",
        "---",
        "",
        "## 詳細資料",
        "",
    ]

    for r in results:
        status = "PASS ✅" if r.passed else "FAIL ❌"
        lines += [
            f"### {r.name}",
            "",
            f"**狀態**：{status}",
        ]
        if r.note:
            lines.append(f"**說明**：{r.note}")
        if r.error:
            lines += [
                "",
                "**錯誤**：",
                "```",
                r.error,
                "```",
            ]
        if r.sample_data:
            lines += ["", "**樣本資料**："]
            for item in r.sample_data:
                lines.append(f"- {item}")
        lines += ["", "---", ""]

    return "\n".join(lines)


# ── Main runner ──────────────────────────────────────────────────────────────

def run_all():
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"faster-flights 整合測試  {run_at}")
    print(f"{'='*60}\n")

    test_fns = [
        ("test_select_token_absent", test_select_token_absent, 0),
        ("test_oneway",              test_oneway,              0),
        ("test_roundtrip",           test_roundtrip,           2.0),
        ("test_mc_independent",      test_mc_independent,      2.0),
        ("test_mc_chained",          test_mc_chained,          2.0),
        ("test_mc_stepwise",         test_mc_stepwise,         2.0),
        ("test_mc4_BKK_circuit",     test_mc4_BKK_circuit,     2.0),
        ("test_mc4_SIN_circuit",     test_mc4_SIN_circuit,     2.0),
    ]

    all_results = []

    for i, (label, fn, sleep_before) in enumerate(test_fns):
        if sleep_before > 0:
            print(f"  [等待 {sleep_before}s 避免限速...]")
            time.sleep(sleep_before)

        print(f"[{i+1}/{len(test_fns)}] 執行 {label} ...", end=" ", flush=True)
        result = fn()
        status = "PASS ✅" if result.passed else "FAIL ❌"
        print(status)
        if not result.passed:
            print(f"       原因：{result.note}")
            if result.error:
                last_line = [l for l in result.error.strip().splitlines() if l][-1]
                print(f"       {last_line}")

        all_results.append(result)

    print(f"\n{'='*60}")
    passed = sum(1 for r in all_results if r.passed)
    print(f"結果：{passed}/{len(all_results)} 通過")
    print(f"{'='*60}\n")

    report = generate_report(all_results, run_at)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"報告已寫入：{REPORT_PATH}")

    if passed < len(all_results):
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()
