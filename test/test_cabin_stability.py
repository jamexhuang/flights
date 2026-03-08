"""
API Stability Test: BKK→TPE→LHR→TPE→BKK across all 4 cabin classes.

Verifies get_flights_multicity_chained returns results for:
  economy, premium-economy, business, first

Usage:
    python test/test_cabin_stability.py
"""

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from fast_flights import (
    FlightQuery,
    get_flights_multicity_chained,
)

# ── Route from user screenshot ───────────────────────────────────────────────
# BKK → TPE  June 8
# TPE → LHR  July 4
# LHR → TPE  July 31
# TPE → BKK  August 3
LEGS = [
    FlightQuery(date="2026-06-08", from_airport="BKK", to_airport="TPE"),
    FlightQuery(date="2026-07-04", from_airport="TPE", to_airport="LHR"),
    FlightQuery(date="2026-07-31", from_airport="LHR", to_airport="TPE"),
    FlightQuery(date="2026-08-03", from_airport="TPE", to_airport="BKK"),
]

CABIN_CLASSES = ["economy", "premium-economy", "business", "first"]
CABIN_LABELS = {
    "economy":         "經濟艙 Economy",
    "premium-economy": "豪華經濟艙 Premium Economy",
    "business":        "商務艙 Business",
    "first":           "頭等艙 First",
}

REPORT_PATH = Path(__file__).parent / "cabin_stability_report.md"


@dataclass
class CabinTestResult:
    cabin: str
    label: str
    passed: bool
    flight_count: int = 0
    total_price: int | None = None
    sample_flights: list = field(default_factory=list)
    error: str = ""
    retries_needed: int = 0


def test_cabin(cabin: str, max_attempts: int = 3) -> CabinTestResult:
    label = CABIN_LABELS[cabin]
    for attempt in range(max_attempts):
        try:
            chained = get_flights_multicity_chained(
                LEGS,
                language="zh-TW",
                currency="TWD",
                seat=cabin,
            )

            assert len(chained) == 4, f"Expected 4 legs, got {len(chained)}"

            flights = chained[0].flights
            total_price = chained[0].total_price

            if flights is None or len(flights) == 0:
                if attempt < max_attempts - 1:
                    print(f"    ↻ 重試 ({attempt+1}/{max_attempts})，結果為空...")
                    time.sleep(3)
                    continue
                return CabinTestResult(
                    cabin=cabin,
                    label=label,
                    passed=False,
                    error="API returned empty flights list after retries",
                    retries_needed=attempt,
                )

            samples = []
            for i, f in enumerate(flights[:5]):
                segs = []
                for s in f.flights:
                    segs.append(f"{s.from_airport.code}→{s.to_airport.code}")
                airlines = ", ".join(f.airlines) if f.airlines else "N/A"
                samples.append(f"  #{i+1} {airlines} | {'→'.join([s.from_airport.code for s in f.flights] + [f.flights[-1].to_airport.code])} | TWD {f.price:,}")

            return CabinTestResult(
                cabin=cabin,
                label=label,
                passed=True,
                flight_count=len(flights),
                total_price=total_price,
                sample_flights=samples,
                retries_needed=attempt,
            )
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"    ↻ 重試 ({attempt+1}/{max_attempts})，例外：{e}")
                time.sleep(3)
                continue
            return CabinTestResult(
                cabin=cabin,
                label=label,
                passed=False,
                error=traceback.format_exc(),
                retries_needed=attempt,
            )

    return CabinTestResult(cabin=cabin, label=label, passed=False, error="Max retries exceeded")


def generate_report(results: list[CabinTestResult], run_at: str) -> str:
    lines = [
        "# 四艙等穩定度測試報告",
        "",
        f"**路線**：BKK → TPE → LHR → TPE → BKK（4 腿多城市）",
        f"**日期**：2026-06-08 / 2026-07-04 / 2026-07-31 / 2026-08-03",
        f"**幣別**：TWD｜**語言**：zh-TW",
        f"**執行時間**：{run_at}",
        "",
        "---",
        "",
        "## 摘要",
        "",
        "| 艙等 | 狀態 | 航班數 | 最低整趟總價 | 重試次數 |",
        "|------|------|--------|-------------|---------|",
    ]

    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        count = str(r.flight_count) if r.passed else "—"
        price = f"TWD {r.total_price:,}" if r.total_price else "—"
        retries = str(r.retries_needed) if r.retries_needed > 0 else "0"
        lines.append(f"| {r.label} | {status} | {count} | {price} | {retries} |")

    passed = sum(1 for r in results if r.passed)
    lines += [
        "",
        f"**總計：{passed} / {len(results)} 通過**",
        "",
        "---",
        "",
        "## 詳細結果",
        "",
    ]

    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        lines += [f"### {r.label}", "", f"**狀態**：{status}"]
        if r.passed:
            lines.append(f"**航班選項數**：{r.flight_count}")
            lines.append(f"**最低整趟總價**：TWD {r.total_price:,}" if r.total_price else "**最低整趟總價**：未取得")
            if r.retries_needed > 0:
                lines.append(f"**需重試次數**：{r.retries_needed}")
            if r.sample_flights:
                lines += ["", "**前 5 筆航班**：", "```"]
                lines += r.sample_flights
                lines += ["```"]
        else:
            lines.append(f"**錯誤**：")
            lines += ["```", r.error.strip(), "```"]
        lines += ["", "---", ""]

    return "\n".join(lines)


def main():
    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"四艙等穩定度測試  {run_at}")
    print(f"路線：BKK → TPE → LHR → TPE → BKK")
    print(f"{'='*60}\n")

    results = []
    for i, cabin in enumerate(CABIN_CLASSES):
        if i > 0:
            print(f"  [等待 3s 避免限速...]")
            time.sleep(3)

        label = CABIN_LABELS[cabin]
        print(f"[{i+1}/{len(CABIN_CLASSES)}] 測試 {label} ...", flush=True)
        result = test_cabin(cabin)
        status = "PASS ✅" if result.passed else "FAIL ❌"
        print(f"  → {status}", end="")
        if result.passed:
            print(f" | {result.flight_count} 筆 | TWD {result.total_price:,}" if result.total_price else f" | {result.flight_count} 筆")
        else:
            print(f" | {result.error[:80] if result.error else 'Unknown error'}")
        results.append(result)

    print(f"\n{'='*60}")
    passed = sum(1 for r in results if r.passed)
    print(f"結果：{passed}/{len(results)} 通過")
    print(f"{'='*60}\n")

    report = generate_report(results, run_at)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"報告已寫入：{REPORT_PATH}")

    return results


if __name__ == "__main__":
    main()
