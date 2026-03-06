# faster-flights 整合測試報告

**執行時間**：2026-03-01 20:06:00

---

## 摘要

| 測試 | 狀態 | 說明 |
|------|------|------|
| `select_token_absent_raises` | ✅ PASS | 成功確認：select_token=None 時拋出 ValueError |
| `oneway_TPE_NRT` | ✅ PASS | 找到 18 筆結果 |
| `roundtrip_TPE_NRT_TPE` | ✅ PASS | 去程 + 回程兩步驟均成功 |
| `multicity_independent_3legs` | ✅ PASS | 3 腿各自查詢均回傳結果（各腿為獨立票價，非整趟總價） |
| `multicity_chained_3legs` | ✅ PASS | 單一 RPC 呼叫成功，所有 leg entry 共用同一 flights 物件 |
| `multicity_stepwise_3legs` | ✅ PASS | Step 1（RPC 整趟總價）+ Step 2+（獨立單程查詢）均成功 |
| `multicity_4legs_BKK_circuit` | ✅ PASS | 4 腿 BKK 環形成功，整趟總價 1043 USD，各腿均有結果 |
| `multicity_4legs_SIN_circuit` | ✅ PASS | 4 腿 SIN 環形成功，整趟總價 1302 USD，各腿均有結果 |

**總計：8 / 8 通過**

---

## 已知限制

- **多城市逐腿詳情**：`get_return_flights()` 用於多城市時，Google HTML 回應的 `payload[3]` 為 `None`，
  無法取得第 2 腿以後的航班詳細資料。正確做法是用 `get_flights_multicity()` 分別查詢各腿。
- **`from __future__ import annotations`**：在 Python 3.13 中，若 importer 使用此 future import，
  `fast_flights.model.SingleFlight` 的 `airline_code` 和 `flight_number` 欄位（有預設值）會被 `@dataclass` 遺漏。
  已修正 `model.py`：移除 `Annotated[int]` 改用 `int` + 注解。

---

## 詳細資料

### select_token_absent_raises

**狀態**：PASS ✅
**說明**：成功確認：select_token=None 時拋出 ValueError

**樣本資料**：
- 錯誤訊息：The selected flight has no select_token. Make sure you are using a round-trip or multi-city query and the parser extracted the token correctly.

---

### oneway_TPE_NRT

**狀態**：PASS ✅
**說明**：找到 18 筆結果

**樣本資料**：
- 結果筆數：18
- 最低票價：246 USD
- 第一筆航空公司：['Jin Air']
- 第一航段：TPE→PUS，airline_code=LJ，飛行 155 分鐘
- metadata 航空公司 IATA 代碼（前 5）：['RF', 'BX', 'CA', 'AI', 'NX']

---

### roundtrip_TPE_NRT_TPE

**狀態**：PASS ✅
**說明**：去程 + 回程兩步驟均成功

**樣本資料**：
- 去程筆數：18
- 去程最低票價：465 USD
- select_token 存在：True
- 回程筆數：18
- 回程最低整趟總價：465 USD
- tfu token 前 20 字：CnRDalJJWDB0MmNWTklO...

---

### multicity_independent_3legs

**狀態**：PASS ✅
**說明**：3 腿各自查詢均回傳結果（各腿為獨立票價，非整趟總價）

**樣本資料**：
- 第 1 腿（TPE→NRT）：18 筆，最低 246 USD
- 第 2 腿（NRT→HKG）：13 筆，最低 253 USD
- 第 3 腿（HKG→TPE）：35 筆，最低 84 USD

---

### multicity_chained_3legs

**狀態**：PASS ✅
**說明**：單一 RPC 呼叫成功，所有 leg entry 共用同一 flights 物件

**樣本資料**：
- 第一腿可選選項數：8
- 整趟最低總價：710 USD
- result[0].flights is result[1].flights：True
- 第一腿第一航段：TPE→NRT，airline_code=CX

---

### multicity_stepwise_3legs

**狀態**：PASS ✅
**說明**：Step 1（RPC 整趟總價）+ Step 2+（獨立單程查詢）均成功

**樣本資料**：
- 第一腿（TPE→NRT）RPC 選項數：8
- 整趟最低總價：710 USD
- select_token 存在：True
- 第二腿（NRT→HKG）獨立查詢結果：13 筆
- 第三腿（HKG→TPE）獨立查詢結果：31 筆

---

### multicity_4legs_BKK_circuit

**狀態**：PASS ✅
**說明**：4 腿 BKK 環形成功，整趟總價 1043 USD，各腿均有結果

**樣本資料**：
- 整趟最低總價（RPC）：1043 USD
- 第一腿（BKK→TPE）RPC 可選選項數：7
- 第一腿第一選項航段：BKK→TPE，airline_code=CI，225 分鐘
- 第 1 腿（BKK→TPE）：11 筆，最低 132 USD，第一航班 airline_code=TR
- 第 2 腿（TPE→LHR）：5 筆，最低 655 USD，第一航班 airline_code=OZ
- 第 3 腿（LHR→TPE）：6 筆，最低 633 USD，第一航班 airline_code=LH
- 第 4 腿（TPE→BKK）：13 筆，最低 116 USD，第一航班 airline_code=UO

---

### multicity_4legs_SIN_circuit

**狀態**：PASS ✅
**說明**：4 腿 SIN 環形成功，整趟總價 1302 USD，各腿均有結果

**樣本資料**：
- 整趟最低總價（RPC）：1302 USD
- 第一腿（SIN→TPE）RPC 可選選項數：6
- 第一腿第一選項航段：SIN→TPE，airline_code=BR，275 分鐘
- 第 1 腿（SIN→TPE）：7 筆，最低 121 USD，第一航班 airline_code=TR
- 第 2 腿（TPE→JFK）：5 筆，最低 807 USD，第一航班 airline_code=EY
- 第 3 腿（JFK→TPE）：4 筆，最低 480 USD，第一航班 airline_code=OZ
- 第 4 腿（TPE→SIN）：9 筆，最低 83 USD，第一航班 airline_code=TR

---
