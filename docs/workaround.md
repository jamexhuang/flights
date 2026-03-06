# 整合搜尋教學：單程、來回、多城市

本文件以繁體中文撰寫，作為下游專案整合 `faster-flights` API 的完整使用教學。涵蓋實際業務情境、完整可執行範例，以及常見陷阱說明。

---

## 目錄

1. [單程搜尋](#一單程搜尋)
2. [來回搜尋](#二來回搜尋)
3. [多城市搜尋](#三多城市搜尋)
4. [聯盟與航空公司篩選](#四聯盟與航空公司篩選)
5. [多機場範圍（批次查詢）](#五多機場範圍批次查詢)
6. [彈性日期區間 × 多機場（逐腿最便宜搜尋）](#六彈性日期區間--多機場逐腿最便宜搜尋)
7. [其他注意事項](#七其他注意事項)

---

## 一、單程搜尋

### 基本用法

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

query = create_query(
    flights=[
        FlightQuery(
            date="2026-03-31",
            from_airport="TPE",
            to_airport="NRT",
        )
    ],
    seat="economy",       # "economy" | "premium-economy" | "business" | "first"
    trip="one-way",
    passengers=Passengers(adults=1),
    language="zh-TW",     # 回傳的航空公司名稱語言
    currency="TWD",       # 價格幣別
)

results = get_flights(query)
```

### 解析回傳值

`get_flights()` 回傳 `MetaList[Flights]`，是一個有額外屬性的 Python list。

```python
# 遍歷所有選項（通常 8–10 筆）
for f in results:
    print(f"票價：{f.price} TWD")
    print(f"航空公司：{f.airlines}")         # list[str]，航空公司「名稱」
    print(f"共 {len(f.flights)} 個航段")

    for seg in f.flights:
        print(f"  {seg.from_airport.code} → {seg.to_airport.code}")
        print(f"  出發：{seg.departure.date} {seg.departure.time}")
        print(f"  抵達：{seg.arrival.date}   {seg.arrival.time}")
        print(f"  飛行時間：{seg.duration} 分鐘")
        print(f"  機型：{seg.plane_type}")
        print(f"  航空公司代碼：{seg.airline_code}")   # IATA 代碼，如 "BR"
        print(f"  航班號碼：{seg.flight_number}")      # 如 "BR 005"

# 取得航空公司與聯盟清單（metadata）
for airline in results.metadata.airlines:
    print(f"{airline.code}: {airline.name}")
```

#### 資料結構速查

| 屬性 | 型別 | 說明 |
|------|------|------|
| `Flights.price` | `int` | 票價（整數，以 `currency` 幣別計） |
| `Flights.airlines` | `list[str]` | 航空公司**名稱**字串（如 `"長榮航空"`） |
| `Flights.flights` | `list[SingleFlight]` | 各航段詳細資訊 |
| `Flights.select_token` | `str \| None` | 選擇此航班後查詢下一腿所需的 token |
| `SingleFlight.from_airport.code` | `str` | 出發機場 IATA 代碼 |
| `SingleFlight.to_airport.code` | `str` | 抵達機場 IATA 代碼 |
| `SingleFlight.departure` | `SimpleDatetime` | `.date = (year, month, day)`, `.time = (hour, minute)` |
| `SingleFlight.arrival` | `SimpleDatetime` | 同上 |
| `SingleFlight.duration` | `int` | 飛行時間（分鐘） |
| `SingleFlight.airline_code` | `str` | IATA 航空公司代碼（如 `"BR"`） |
| `SingleFlight.flight_number` | `str` | 航班號碼（如 `"BR 005"`） |

> **注意**：`Flights.airlines` 是航空公司**名稱**，不是 IATA 代碼。
> 若需要 IATA 代碼進行聯盟篩選，請使用 `SingleFlight.airline_code`。

### 篩選：最大轉機次數

```python
FlightQuery(
    date="2026-03-31",
    from_airport="TPE",
    to_airport="LHR",
    max_stops=1,  # 最多 1 次轉機（0 = 直飛）
)
```

---

## 二、來回搜尋

Google Flights 的來回搜尋是兩步驟設計：先查去程，再用選擇的去程 token 查回程。

### Step 1：查詢去程

```python
from fast_flights import FlightQuery, Passengers, create_query, get_flights

rt_query = create_query(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="TPE"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    language="zh-TW",
    currency="TWD",
)

outbound = get_flights(rt_query)

# 顯示去程選項
for i, f in enumerate(outbound):
    print(f"[{i}] {f.airlines} — {f.price} TWD")
    seg = f.flights[0]
    print(f"     {seg.from_airport.code}→{seg.to_airport.code} "
          f"{seg.departure.time[0]:02d}:{seg.departure.time[1]:02d} → "
          f"{seg.arrival.time[0]:02d}:{seg.arrival.time[1]:02d}")
```

> **重要**：來回搜尋的 `price` 是去程的單程票價或部分總價，**回程後才會顯示整趟總價**。

### Step 2：選擇去程，查詢回程

```python
from fast_flights import select_flight, get_return_flights

# 確認 select_token 存在（必要條件）
if not outbound or outbound[0].select_token is None:
    raise RuntimeError("無法取得去程 token，請確認 trip='round-trip' 且查詢成功")

# 讓使用者選擇去程（範例：選第 0 筆）
chosen_outbound = outbound[0]

# 建立回程查詢（內部會把 token 包成 tfu 參數）
return_query = select_flight(rt_query, chosen_outbound)

# 查詢回程
returning = get_return_flights(return_query)

for f in returning:
    print(f"回程：{f.airlines} — {f.price} TWD（整趟總價）")
    seg = f.flights[0]
    print(f"  {seg.from_airport.code}→{seg.to_airport.code} "
          f"{seg.departure.time[0]:02d}:{seg.departure.time[1]:02d}")
```

### 為何要保留原始 query？

`select_flight()` 建立的 `ReturnQuery` 內部包含：
- `base`：原始 `Query`（含 `tfs` 參數，代表整個行程設定）
- `tfu`：選擇的去程 token

兩者都會傳給 Google，缺一不可。因此**請保留 `rt_query` 物件**，不要在呼叫 `select_flight` 前丟棄它。

### 完整流程圖

```
create_query(trip="round-trip")
        ↓
get_flights(rt_query)
  → outbound: MetaList[Flights]（每筆有 select_token）
        ↓
使用者選擇去程 → chosen = outbound[i]
        ↓
select_flight(rt_query, chosen)
  → return_query: ReturnQuery
        ↓
get_return_flights(return_query)
  → returning: MetaList[Flights]（整趟總價）
```

---

## 三、多城市搜尋

多城市搜尋有三種做法，依使用情境選擇：

| 做法 | 函式 | 票價類型 | 適用情境 |
|------|------|----------|----------|
| A. 獨立單程 | `get_flights_multicity()` | 各腿單程票價（非整趟總價） | 只比較各腿最低價，或取得各腿詳細航班 |
| B. RPC 一次查 | `get_flights_multicity_chained()` | 整趟總價 | 需要 Google 整趟定價，快速取得第一腿選項 |
| C. 逐腿互動選擇 | `get_flights` + `get_flights_multicity` | Step 1 整趟總價 + Step 2+ 各腿單程 | 產品功能逐腿選航班（**推薦**） |

---

### 做法 A：獨立單程（`get_flights_multicity`）

每一腿各自獨立查詢，價格為各腿的單程票價，**加總不等於 Google 整趟多城市票價**。

```python
from fast_flights import FlightQuery, get_flights_multicity

legs = get_flights_multicity(
    flights=[
        FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
        FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
        FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
    ],
    seat="economy",
    language="zh-TW",
    currency="TWD",
    delay=1.5,  # 每腿之間等待秒數，避免被限速
)

for leg in legs:
    print(f"第 {leg.leg_index + 1} 腿：{leg.from_airport} → {leg.to_airport} ({leg.date})")
    if leg.results:
        cheapest = min(leg.results, key=lambda f: f.price)
        print(f"  最低票價：{cheapest.price} TWD")
    else:
        print("  無結果")
```

---

### 做法 B：RPC 整趟總價（`get_flights_multicity_chained`）

單一 API 呼叫，回傳第一腿的可用航班選項，每個選項的 `price` 已是**整趟多城市總價**。

```python
from fast_flights import FlightQuery, get_flights_multicity_chained

legs_input = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

result = get_flights_multicity_chained(
    legs_input,
    language="zh-TW",
    currency="TWD",
)

# ⚠️ 重要：result[0].flights、result[1].flights、result[2].flights
#    都是同一個物件（同一次 RPC 回傳），都是「第一腿的選項」
#    不要誤以為 result[1].flights 是第二腿的資料

print(f"整趟最低總價：{result[0].total_price} TWD")

for f in result[0].flights:
    print(f"  {f.airlines} — {f.price} TWD（整趟）")
    seg = f.flights[0]
    print(f"  第一腿：{seg.from_airport.code}→{seg.to_airport.code} "
          f"airline={seg.airline_code}")
```

---

### 做法 C：逐腿互動選擇（推薦用於產品功能）

> **已知限制**：`get_return_flights()` 用於多城市時，Google HTML 回應的 `payload[3]` 為 `None`，
> 因此**無法取得第 2 腿以後的逐腿詳細航班資料**。
>
> 正確做法是兩步驟分離：
> - **Step 1**：用 RPC（`get_flights(mc_query)`）取得第一腿選項 + **整趟總價**
> - **Step 2+**：用獨立單程查詢（`get_flights_multicity`）取得各腿詳細航班選項

#### 完整逐腿互動範例

```python
import time
from fast_flights import (
    FlightQuery, Passengers, create_query,
    get_flights, get_flights_multicity,
)

legs_def = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

# Step 1：取得第一腿選項 + 整趟總價（RPC）
mc_query = create_query(
    flights=legs_def, trip="multi-city",
    seat="economy", passengers=Passengers(adults=1),
    language="zh-TW", currency="TWD",
)
leg1_results = get_flights(mc_query)

print("=== 第一腿選項（含整趟總價）===")
for i, f in enumerate(leg1_results):
    seg = f.flights[0]
    print(f"[{i}] {seg.airline_code} {seg.from_airport.code}→{seg.to_airport.code}"
          f"  整趟總價 {f.price} TWD")

total_price = leg1_results[0].price   # 保留整趟總價

time.sleep(2)

# Step 2+：各腿獨立查詢（⚠️ 不知道 Step 1 選了哪班，結果與去程選擇無關）
remaining_legs = get_flights_multicity(
    flights=legs_def[1:],
    seat="economy", passengers=Passengers(adults=1),
    language="zh-TW", currency="TWD", delay=1.5,
)

for leg in remaining_legs:
    print(f"\n=== 第 {leg.leg_index + 2} 腿：{leg.from_airport}→{leg.to_airport} ===")
    for i, f in enumerate((leg.results or [])[:5]):
        seg = f.flights[0]
        print(f"[{i}] {seg.airline_code}"
              f"  {seg.departure.time[0]:02d}:{seg.departure.time[1]:02d}"
              f"→{seg.arrival.time[0]:02d}:{seg.arrival.time[1]:02d}"
              f"  {seg.duration}分鐘  {f.price} TWD（單腿）")
```

若腿與腿之間**日期不同**（最常見情況），Step 2+ 的獨立查詢不會出現時序衝突，上方範例即可直接使用。
若有**同日轉機**需求，可加上 `filter_by_connection` 過濾掉接不上的班次（見下方）。

#### 讓下游應用記住上一腿的選擇（同日轉機適用）

`get_flights_multicity` 是無狀態的獨立查詢，本身不知道前一腿選了什麼。
若兩腿在同一天，可在 client 端用前一腿的**抵達時間**過濾下一腿選項，
實現「只顯示銜接得上的航班」：

```python
from datetime import datetime, timedelta

def filter_by_connection(leg_results, prev_last_seg, min_layover_min: int = 90):
    """
    只保留出發時間 ≥ 前腿抵達 + min_layover_min 的航班選項。

    Args:
        leg_results:      get_flights_multicity 某腿的 results（MetaList[Flights]）
        prev_last_seg:    前一腿選定班機的最後一個 SingleFlight（含 .arrival）
        min_layover_min:  最短轉機時間（分鐘），預設 90 分鐘
    """
    arr = prev_last_seg.arrival
    prev_dt = datetime(*arr.date, *arr.time)
    earliest = prev_dt + timedelta(minutes=min_layover_min)

    return [
        f for f in (leg_results or [])
        if f.flights and datetime(*f.flights[0].departure.date,
                                   *f.flights[0].departure.time) >= earliest
    ]
```

```python
import time
from datetime import datetime, timedelta
from fast_flights import (
    FlightQuery, Passengers, create_query,
    get_flights, get_flights_multicity,
)

legs_def = [
    FlightQuery(date="2026-03-31", from_airport="TPE", to_airport="NRT"),
    FlightQuery(date="2026-04-05", from_airport="NRT", to_airport="HKG"),
    FlightQuery(date="2026-04-10", from_airport="HKG", to_airport="TPE"),
]

# ── Step 1：取得第一腿選項 + 整趟總價（RPC）────────────────
mc_query = create_query(
    flights=legs_def, trip="multi-city",
    seat="economy", passengers=Passengers(adults=1),
    language="zh-TW", currency="TWD",
)
leg1_results = get_flights(mc_query)

print("=== 第一腿選項（含整趟總價）===")
for i, f in enumerate(leg1_results):
    seg = f.flights[0]
    arr = f.flights[-1].arrival   # 最後一航段的抵達時間
    print(f"[{i}] {seg.airline_code} {seg.from_airport.code}→{f.flights[-1].to_airport.code}"
          f"  抵達 {arr.date[1]:02d}/{arr.date[2]:02d} {arr.time[0]:02d}:{arr.time[1]:02d}"
          f"  整趟總價 {f.price} TWD")

chosen1 = leg1_results[0]   # 使用者選第一腿
prev_seg = chosen1.flights[-1]   # 記住最後一航段（含抵達時間）

time.sleep(2)

# ── Step 2+：查詢剩餘各腿，並過濾銜接不上的班次────────────
remaining_legs = get_flights_multicity(
    flights=legs_def[1:],
    seat="economy", passengers=Passengers(adults=1),
    language="zh-TW", currency="TWD", delay=1.5,
)

for leg in remaining_legs:
    # 過濾：只保留出發時間 ≥ 前腿抵達 + 90 分鐘
    feasible = filter_by_connection(leg.results, prev_seg, min_layover_min=90)

    print(f"\n=== 第 {leg.leg_index + 2} 腿：{leg.from_airport}→{leg.to_airport}"
          f"（可銜接 {len(feasible)} / {len(leg.results or [])} 筆）===")

    for i, f in enumerate(feasible[:5]):
        seg = f.flights[0]
        dep = seg.departure
        print(f"[{i}] {seg.airline_code}"
              f"  出發 {dep.time[0]:02d}:{dep.time[1]:02d}"
              f"  {seg.duration}分鐘  {f.price} TWD（單腿）")

    if feasible:
        chosen_next = feasible[0]   # 使用者選下一腿
        prev_seg = chosen_next.flights[-1]   # 更新記憶
```

#### 流程圖

```
create_query(trip="multi-city", flights=[leg1, leg2, ..., legN])
        ↓
get_flights(mc_query)  ← RPC 路徑
  → leg1_results（第一腿選項 + 整趟總價 + select_token）
        ↓
使用者選擇第一腿 → chosen1
prev_seg = chosen1.flights[-1]   ← 記住抵達時間
        ↓
get_flights_multicity(flights=[leg2, leg3, ..., legN])
  → 每腿獨立單程結果（未過濾，不知道前一腿選了什麼）
        ↓
filter_by_connection(leg.results, prev_seg)
  → 只保留出發時間 ≥ prev_seg.arrival + 最短轉機時間的選項
        ↓
使用者選擇下一腿 → prev_seg 更新 → 重複直到最後一腿

總費用 = 整趟總價（來自 Step 1，Google 正式報價）
各腿詳情 = 獨立單程查詢 + client 端銜接過濾
```

> **注意**：銜接過濾是 client 端行為，不影響 Google 回傳的票價。
> Step 2+ 顯示的各腿票價仍是獨立單程價，Step 1 的整趟總價才是 Google 正式報價。

---

## 四、聯盟與航空公司篩選

### 伺服器端篩選（速度快，但只有第一腿有效）

在 `FlightQuery` 的 `airlines` 參數填入聯盟或 IATA 代碼：

```python
FlightQuery(
    date="2026-03-31",
    from_airport="TPE",
    to_airport="NRT",
    airlines=["STAR_ALLIANCE"],  # 或 "ONEWORLD"、"SKYTEAM"、"BR"、"CI" 等
)
```

> **限制**：`airlines` 只有套用到第一個 `FlightQuery` 時才有效。
> 若有多個 FlightQuery（來回、多城市），後面的 FlightQuery 中的 `airlines` 設定會被 Google 忽略。

### 用戶端篩選（所有腿均適用）

因為 `Flights.airlines` 是**航空公司名稱字串**（如 `"長榮航空"`），不是 IATA 代碼，
聯盟篩選必須透過 `SingleFlight.airline_code` 進行比對。

```python
def filter_by_iata_codes(results, iata_codes: set[str]):
    """
    篩選由指定航空公司（IATA 代碼）運營第一航段的航班。

    Args:
        results: get_flights() 或 get_return_flights() 的回傳值
        iata_codes: IATA 代碼集合（如 {"BR", "CI", "AE"}）

    Returns:
        篩選後的 list[Flights]
    """
    return [
        f for f in results
        if f.flights and f.flights[0].airline_code in iata_codes
    ]
```

#### 三大聯盟主要成員代碼參考

```python
ALLIANCE_MEMBERS = {
    "STAR_ALLIANCE": {
        "NH",   # 全日空 ANA
        "UA",   # 聯合航空 United
        "LH",   # 漢莎航空 Lufthansa
        "SQ",   # 新加坡航空 Singapore Airlines
        "TG",   # 泰國航空 Thai Airways
        "TK",   # 土耳其航空 Turkish Airlines
        "CA",   # 中國國際航空 Air China
        "OS",   # 奧地利航空 Austrian
        "LO",   # 波蘭航空 LOT
        "SK",   # 北歐航空 SAS
        "TP",   # 葡萄牙航空 TAP
        "ET",   # 衣索比亞航空 Ethiopian
        "MS",   # 埃及航空 EgyptAir
        # ... 以官方名單為準
    },
    "ONEWORLD": {
        "AA",   # 美國航空 American
        "BA",   # 英國航空 British Airways
        "CX",   # 國泰航空 Cathay Pacific
        "QF",   # 澳洲航空 Qantas
        "JL",   # 日本航空 Japan Airlines
        "MH",   # 馬來西亞航空 Malaysia Airlines
        "IB",   # 西班牙國際航空 Iberia
        "QR",   # 卡達航空 Qatar Airways
        "RJ",   # 約旦皇家航空 Royal Jordanian
        "UL",   # 斯里蘭卡航空 SriLankan
        "AY",   # 芬蘭航空 Finnair
        # ... 以官方名單為準
    },
    "SKYTEAM": {
        "DL",   # 達美航空 Delta
        "AF",   # 法國航空 Air France
        "KL",   # 荷蘭皇家航空 KLM
        "KE",   # 大韓航空 Korean Air
        "CZ",   # 中國南方航空
        "MU",   # 中國東方航空
        "CI",   # 中華航空 China Airlines
        "AZ",   # 義大利航空 ITA Airways
        "AM",   # 墨西哥航空 Aeromexico
        "SU",   # 俄羅斯航空 Aeroflot
        "VN",   # 越南航空 Vietnam Airlines
        # ... 以官方名單為準
    },
}
```

> **注意**：聯盟成員會隨時間變動，請以各聯盟官方網站的最新名單為準。

#### 使用範例

```python
# 來回搜尋後，只顯示 Star Alliance 去程選項
outbound = get_flights(rt_query)
star_outbound = filter_by_iata_codes(outbound, ALLIANCE_MEMBERS["STAR_ALLIANCE"])

if not star_outbound:
    print("無 Star Alliance 去程班次")
else:
    print(f"找到 {len(star_outbound)} 個 Star Alliance 去程選項")
    chosen = star_outbound[0]
    return_query = select_flight(rt_query, chosen)
    returning = get_return_flights(return_query)
```

---

## 五、多機場範圍（批次查詢）

`FlightQuery` 的 `from_airport` 和 `to_airport` 只接受**單一 IATA 機場代碼**。
若需搜尋「TPE 或 TSA 出發 → NRT 或 HND 抵達」，需要拆成多個查詢再合併。

### 做法：批次查詢後合併排序

```python
import time
from fast_flights import FlightQuery, Passengers, create_query, get_flights

airports_from = ["TPE", "TSA"]
airports_to   = ["NRT", "HND"]
date = "2026-03-31"

all_flights = []

for i, from_ in enumerate(airports_from):
    for j, to_ in enumerate(airports_to):
        if i > 0 or j > 0:
            time.sleep(1.5)  # 避免過快請求

        q = create_query(
            flights=[FlightQuery(date=date, from_airport=from_, to_airport=to_)],
            trip="one-way",
            passengers=Passengers(adults=1),
            language="zh-TW",
            currency="TWD",
        )
        results = get_flights(q)

        # 標記此批結果的出發/抵達機場（方便後續顯示）
        for f in results:
            f._from = from_
            f._to = to_

        all_flights.extend(results)
        print(f"{from_}→{to_}：找到 {len(results)} 筆")

# 依票價排序，顯示最便宜的 10 筆
all_flights.sort(key=lambda f: f.price)
for f in all_flights[:10]:
    seg = f.flights[0]
    print(f"{getattr(f, '_from', seg.from_airport.code)}→{getattr(f, '_to', seg.to_airport.code)}"
          f" {f.price} TWD  {f.airlines}")
```

### 並行查詢（速度較快，注意限速風險）

```python
import concurrent.futures
import time

def fetch_one(from_: str, to_: str, date: str):
    q = create_query(
        flights=[FlightQuery(date=date, from_airport=from_, to_airport=to_)],
        trip="one-way",
        passengers=Passengers(adults=1),
        language="zh-TW",
        currency="TWD",
    )
    return from_, to_, get_flights(q)

combos = [(f, t) for f in airports_from for t in airports_to]

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    futures = [ex.submit(fetch_one, f, t, date) for f, t in combos]
    results_map = {}
    for future in concurrent.futures.as_completed(futures):
        from_, to_, flights = future.result()
        results_map[(from_, to_)] = flights
```

> **建議**：並行數量不超過 2，避免觸發 Google 的速率限制（HTTP 429）。

---

## 六、彈性日期區間 × 多機場（逐腿最便宜搜尋）

有時使用者不確定要從哪個機場出發、或哪天飛最划算，希望給定**日期區間** + **多個候選機場**，
自動找出最便宜的組合。

本節提供 `find_cheapest_leg()` helper，讓每一腿都能在指定的日期區間與機場範圍中，
找出 `(出發機場, 抵達機場, 日期, Flights)` 的最低票價組合，再逐腿銜接。

> **API 呼叫次數警告**
>
> 每呼叫一次 `find_cheapest_leg()` 會發出：
> `len(from_airports) × len(to_airports) × (date_end - date_start + 1 天)` 次 API 請求。
>
> 例如：2 出發機場 × 2 抵達機場 × 3 天 = **12 次請求**，延遲 1.5 秒 × 12 = 約 18 秒。
> 3 腿共需 ~36 次請求，搜尋時間約 60 秒。請視需求控制機場數量與日期範圍。

---

### `find_cheapest_leg()` 輔助函式

```python
import time
from datetime import date as _Date, timedelta
from fast_flights import FlightQuery, Passengers, create_query, get_flights


def find_cheapest_leg(
    from_airports: list[str],
    to_airports: list[str],
    date_start: str,
    date_end: str,
    *,
    seat: str = "economy",
    passengers: Passengers = Passengers(adults=1),
    language: str = "zh-TW",
    currency: str = "TWD",
    delay: float = 1.5,
) -> tuple[str, str, str, object] | None:
    """
    在 from_airports × to_airports × [date_start, date_end] 所有組合中，
    找出票價最低的選項。

    Returns:
        (from_airport, to_airport, date_str, Flights)，若完全無結果則 None。
    """
    best_price = None
    best = None  # (from_, to_, date_str, Flights)

    d = _Date.fromisoformat(date_start)
    d_end = _Date.fromisoformat(date_end)

    while d <= d_end:
        for from_ in from_airports:
            for to_ in to_airports:
                query = create_query(
                    flights=[FlightQuery(
                        date=d.isoformat(),
                        from_airport=from_,
                        to_airport=to_,
                    )],
                    trip="one-way",
                    seat=seat,
                    passengers=passengers,
                    language=language,
                    currency=currency,
                )
                results = get_flights(query)
                if results:
                    cheapest = min(results, key=lambda f: f.price)
                    if best_price is None or cheapest.price < best_price:
                        best_price = cheapest.price
                        best = (from_, to_, d.isoformat(), cheapest)

                time.sleep(delay)

        d += timedelta(days=1)

    return best
```

---

### 完整範例：三腿多城市，每腿有多機場候選 + 日期區間

```python
import time
from fast_flights import get_flights_multicity_chained, FlightQuery

# ── 定義每一腿的搜尋範圍 ─────────────────────────────────────────────
# 腿 1：從 TPE 或 TSA 出發 → NRT 或 HND，日期任選 5/4–5/6
leg1_from = ["TPE", "TSA"]
leg1_to   = ["NRT", "HND"]
leg1_dates = ("2026-05-04", "2026-05-06")

# 腿 2：從腿 1 所選的抵達機場出發（動態決定） → SIN，日期任選 5/6–5/8
leg2_to   = ["SIN"]
leg2_dates = ("2026-05-06", "2026-05-08")

# 腿 3：從 SIN 回 TPE 或 TSA，日期任選 5/10–5/12
leg3_from = ["SIN"]
leg3_to   = ["TPE", "TSA"]
leg3_dates = ("2026-05-10", "2026-05-12")

# ── 逐腿找最便宜組合 ─────────────────────────────────────────────────
print("搜尋第一腿...")
result1 = find_cheapest_leg(leg1_from, leg1_to, *leg1_dates)
if result1 is None:
    raise RuntimeError("第一腿無結果")
from1, to1, date1, flight1 = result1
print(f"第一腿最便宜：{from1}→{to1} on {date1}，{flight1.price} TWD（單腿）")

time.sleep(2)

# 腿 2 的出發機場 = 腿 1 選定的抵達機場（銜接）
print("搜尋第二腿...")
result2 = find_cheapest_leg([to1], leg2_to, *leg2_dates)
if result2 is None:
    raise RuntimeError("第二腿無結果")
from2, to2, date2, flight2 = result2
print(f"第二腿最便宜：{from2}→{to2} on {date2}，{flight2.price} TWD（單腿）")

time.sleep(2)

print("搜尋第三腿...")
result3 = find_cheapest_leg(leg3_from, leg3_to, *leg3_dates)
if result3 is None:
    raise RuntimeError("第三腿無結果")
from3, to3, date3, flight3 = result3
print(f"第三腿最便宜：{from3}→{to3} on {date3}，{flight3.price} TWD（單腿）")

time.sleep(2)

# ── 取得 Google 整趟正式總價 ─────────────────────────────────────────
print("\n取得整趟多城市總價...")
mc_result = get_flights_multicity_chained(
    [
        FlightQuery(date=date1, from_airport=from1, to_airport=to1),
        FlightQuery(date=date2, from_airport=from2, to_airport=to2),
        FlightQuery(date=date3, from_airport=from3, to_airport=to3),
    ],
    language="zh-TW",
    currency="TWD",
)

if mc_result and mc_result[0].flights:
    total = mc_result[0].flights[0].price
    print(f"\n整趟最低總價（Google 報價）：{total} TWD")
    print(f"最佳行程：")
    print(f"  腿 1：{from1}→{to1}  {date1}")
    print(f"  腿 2：{from2}→{to2}  {date2}")
    print(f"  腿 3：{from3}→{to3}  {date3}")
```

---

### 說明：腿 2 的出發機場為何是 `[to1]`？

因為旅客在腿 1 選定了目的地（`to1`），腿 2 必須從同一城市出發。
因此腿 2 的 `from_airports` 固定為 `[to1]`（上一腿的抵達機場）：

```
腿 1：TPE/TSA → NRT/HND  →  選定 NRT
腿 2：[NRT]   → SIN       →  固定從 NRT 出發
腿 3：SIN     → TPE/TSA
```

若每腿的出發地和上一腿抵達地完全無關（例如中途在不同城市開始新旅程），
才需要在腿 2 指定全新的 `from_airports`。

---

### 小結

| 需求 | 做法 |
|------|------|
| 固定日期 + 多機場 | 第五節的批次查詢 |
| 固定機場 + 日期區間 | `find_cheapest_leg` 只傳一個 from/to，給出多個日期 |
| 多機場 + 日期區間（最一般化） | 本節 `find_cheapest_leg`，完整組合枚舉 |
| 取得 Google 正式整趟總價 | 找到最佳組合後，再呼叫 `get_flights_multicity_chained` |

---

## 七、其他注意事項

### Proxy 使用

```python
get_flights(query, proxy="http://user:pass@host:port")
get_return_flights(return_query, proxy="http://user:pass@host:port")
```

適用於：規避地區限制、降低被限速風險。

### 貨幣與語言設定

```python
create_query(
    ...,
    language="zh-TW",  # 影響回傳的航空公司名稱語言
    currency="TWD",     # 影響 price 的幣別
)
```

- 支援的語言代碼：見 `fast_flights.types.Language`（73 種）
- 支援的幣別代碼：見 `fast_flights.types.Currency`（160 種以上）

### 常見錯誤對照表

| 錯誤 / 現象 | 可能原因 | 解決方式 |
|------------|----------|----------|
| `RuntimeError: HTTP 429` | 請求過快 | 在呼叫之間加入 `time.sleep(2)`，或使用 proxy |
| `MetaList` 為空（`len(results) == 0`）| 查詢日期無航班，或被 Google 封鎖 | 換日期或換熱門航線（如 TPE→NRT），再試一次 |
| `select_token is None` | 使用了 `one-way` query 卻呼叫 `select_flight` | 確認 `create_query(trip="round-trip")` 或 `"multi-city"` |
| `ValueError: The selected flight has no select_token` | 同上，或 parser 未能解析 token | 同上；也可改用其他航班（`results[1]` 等） |
| 多城市做法 C：Step 2+ 結果與去程選擇無關 | `get_flights_multicity` 是獨立查詢，不受 Step 1 的去程選擇影響 | 這是已知架構限制；整趟總價以 Step 1 的 RPC 為準 |
| `get_flights_multicity_chained` 回傳 `flights=None` | Google RPC 暫時回傳 session-init 資料 | 自動重試機制已內建（最多 2 次），通常無需手動處理 |

### 多城市：result[i].flights 都一樣？

這是正常行為。`get_flights_multicity_chained()` 只發出**一次** RPC，
Google 的回應只包含第一腿的航班選項（含整趟總價），
因此所有 `result[i].flights` 都指向同一個物件。

若需要逐腿選航班，請改用[做法 C（逐腿互動選擇）](#做法-c逐腿互動選擇推薦用於產品功能)。
