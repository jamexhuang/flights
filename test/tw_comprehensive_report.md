# 台灣出發全方位整合測試報告

**執行時間**：2026-03-08 02:45:09

測試涵蓋範圍：
- **目的地**：日本（NRT/KIX）、歐洲（LHR/CDG/FRA）、美洲（JFK/LAX/SFO）
- **艙等**：economy / premium-economy / business / first
- **行程類型**：單程、來回、多腿（3–5 腿）

---

## 摘要

| # | 測試 | 類型 | 狀態 | 說明 |
|---|------|------|------|------|
| 1 | `ow_TPE_NRT_economy` | 單程 (One-way) | ✅ PASS | TPE→NRT economy — 20 筆 |
| 2 | `ow_TPE_NRT_premium_economy` | 單程 (One-way) | ✅ PASS | TPE→NRT premium-economy — 2 筆 |
| 3 | `ow_TPE_NRT_business` | 單程 (One-way) | ✅ PASS | TPE→NRT business — 9 筆 |
| 4 | `ow_TPE_NRT_first` | 單程 (One-way) | ✅ PASS | first class — 找到 3 筆（0 筆為正常） |
| 5 | `ow_TPE_KIX_economy` | 單程 (One-way) | ✅ PASS | TPE→KIX economy — 13 筆 |
| 6 | `ow_TPE_KIX_business` | 單程 (One-way) | ✅ PASS | TPE→KIX business — 8 筆 |
| 7 | `ow_TPE_LHR_economy` | 單程 (One-way) | ✅ PASS | TPE→LHR economy — 7 筆 |
| 8 | `ow_TPE_LHR_premium_economy` | 單程 (One-way) | ✅ PASS | TPE→LHR premium-economy — 4 筆 |
| 9 | `ow_TPE_LHR_business` | 單程 (One-way) | ✅ PASS | TPE→LHR business — 4 筆 |
| 10 | `ow_TPE_LHR_first` | 單程 (One-way) | ✅ PASS | first class — 找到 4 筆（0 筆為正常） |
| 11 | `ow_TPE_CDG_economy` | 單程 (One-way) | ✅ PASS | TPE→CDG economy — 5 筆 |
| 12 | `ow_TPE_CDG_business` | 單程 (One-way) | ✅ PASS | TPE→CDG business — 5 筆 |
| 13 | `ow_TPE_FRA_economy` | 單程 (One-way) | ✅ PASS | TPE→FRA economy — 6 筆 |
| 14 | `ow_TPE_JFK_economy` | 單程 (One-way) | ✅ PASS | TPE→JFK economy — 4 筆 |
| 15 | `ow_TPE_JFK_premium_economy` | 單程 (One-way) | ✅ PASS | TPE→JFK premium-economy — 3 筆 |
| 16 | `ow_TPE_JFK_business` | 單程 (One-way) | ✅ PASS | TPE→JFK business — 4 筆 |
| 17 | `ow_TPE_JFK_first` | 單程 (One-way) | ✅ PASS | first class — 找到 5 筆（0 筆為正常） |
| 18 | `ow_TPE_LAX_economy` | 單程 (One-way) | ✅ PASS | TPE→LAX economy — 7 筆 |
| 19 | `ow_TPE_LAX_business` | 單程 (One-way) | ✅ PASS | TPE→LAX business — 6 筆 |
| 20 | `ow_TPE_SFO_economy` | 單程 (One-way) | ✅ PASS | TPE→SFO economy — 3 筆 |
| 21 | `rt_TPE_NRT_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔NRT economy — 去程 20 筆，回程 20 筆 |
| 22 | `rt_TPE_NRT_business` | 來回 (Round-trip) | ✅ PASS | TPE↔NRT business — 去程 6 筆，回程 6 筆 |
| 23 | `rt_TPE_KIX_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔KIX economy — 去程 15 筆，回程 15 筆 |
| 24 | `rt_TPE_LHR_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔LHR economy — 去程 4 筆，回程 4 筆 |
| 25 | `rt_TPE_LHR_business` | 來回 (Round-trip) | ✅ PASS | TPE↔LHR business — 去程 7 筆，回程 7 筆 |
| 26 | `rt_TPE_CDG_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔CDG economy — 去程 4 筆，回程 4 筆 |
| 27 | `rt_TPE_FRA_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔FRA economy — 去程 4 筆，回程 4 筆 |
| 28 | `rt_TPE_JFK_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔JFK economy — 去程 4 筆，回程 4 筆 |
| 29 | `rt_TPE_JFK_business` | 來回 (Round-trip) | ✅ PASS | TPE↔JFK business — 去程 5 筆，回程 5 筆 |
| 30 | `rt_TPE_LAX_economy` | 來回 (Round-trip) | ✅ PASS | TPE↔LAX economy — 去程 6 筆，回程 6 筆 |
| 31 | `mc_TPE_NRT_KIX_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→NRT→KIX→TPE [economy] — 整趟總價 447 USD |
| 32 | `mc_TPE_NRT_KIX_TPE_business` | 多腿 (Multi-city) | ✅ PASS | TPE→NRT→KIX→TPE [business] — 整趟總價 3524 USD |
| 33 | `mc_TPE_LHR_CDG_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→LHR→CDG→TPE [economy] — 整趟總價 1709 USD |
| 34 | `mc_TPE_LHR_CDG_TPE_business` | 多腿 (Multi-city) | ✅ PASS | TPE→LHR→CDG→TPE [business] — 整趟總價 8410 USD |
| 35 | `mc_TPE_LHR_FRA_CDG_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→LHR→FRA→CDG→TPE [economy] — 整趟總價 1413 USD |
| 36 | `mc_TPE_JFK_LAX_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→JFK→LAX→TPE [economy] — 整趟總價 2059 USD |
| 37 | `mc_TPE_JFK_LAX_TPE_business` | 多腿 (Multi-city) | ❌ FAIL | 斷言失敗 |
| 38 | `mc_TPE_NRT_LAX_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→NRT→LAX→TPE [economy] — 整趟總價 935 USD |
| 39 | `mc_TPE_LHR_JFK_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→LHR→JFK→TPE [economy] — 整趟總價 8025 USD |
| 40 | `mc_TPE_NRT_LAX_LHR_TPE_economy` | 多腿 (Multi-city) | ✅ PASS | TPE→NRT→LAX→LHR→TPE [economy] — 整趟總價 9351 USD |
| 41 | `mc_TPE_NRT_LAX_LHR_TPE_business` | 多腿 (Multi-city) | ❌ FAIL | 斷言失敗 |
| 42 | `mc_TPE_JFK_LHR_CDG_NRT_TPE_economy` | 多腿 (Multi-city) | ❌ FAIL | 斷言失敗 |

**總計：39 / 42 通過**

---

## 單程 (One-way)

通過：20 / 20

### `ow_TPE_NRT_economy`

**狀態**：PASS ✅
**說明**：TPE→NRT economy — 20 筆

**樣本資料**：
- TPE→NRT economy: 共 20 筆，最低票價 145
-   最低票價選項：$145 | T'Way Air | TPE→TAE (TW, 145min)
-   $150 | Hong Kong Express | TPE→HKG (UO, 115min)
-   $154 | Jetstar | TPE→KIX (GK, 160min)

---

### `ow_TPE_NRT_premium_economy`

**狀態**：PASS ✅
**說明**：TPE→NRT premium-economy — 2 筆

**樣本資料**：
- TPE→NRT premium-economy: 共 2 筆，最低票價 1341
-   最低票價選項：$1341 | Shenzhen | TPE→SZX (ZH, 110min)
-   $2324 | EVA Air, Cathay Pacific | TPE→HKG (BR, 120min)

---

### `ow_TPE_NRT_business`

**狀態**：PASS ✅
**說明**：TPE→NRT business — 9 筆

**樣本資料**：
- TPE→NRT business: 共 9 筆，最低票價 628
-   最低票價選項：$628 | Asiana Airlines | TPE→ICN (OZ, 150min)
-   $669 | Asiana Airlines, Korean Air | TPE→ICN (OZ, 150min)
-   $732 | China Airlines | TPE→NRT (CI, 205min)

---

### `ow_TPE_NRT_first`

**狀態**：PASS ✅
**說明**：first class — 找到 3 筆（0 筆為正常）

**樣本資料**：
- TPE→NRT first: 共 3 筆，最低票價 1354
-   最低票價選項：$1354 | EVA Air, ANA | TPE→OKA (BR, 90min)
-   $2291 | XiamenAir | TPE→FOC (MF, 105min)
-   $5135 | THAI | TPE→BKK (TG, 225min)

---

### `ow_TPE_KIX_economy`

**狀態**：PASS ✅
**說明**：TPE→KIX economy — 13 筆

**樣本資料**：
- TPE→KIX economy: 共 13 筆，最低票價 129
-   最低票價選項：$129 | Tigerair Taiwan | TPE→KIX (IT, 170min)
-   $137 | Jetstar | TPE→KIX (GK, 155min)
-   $204 | Peach Aviation | TPE→KIX (MM, 170min)

---

### `ow_TPE_KIX_business`

**狀態**：PASS ✅
**說明**：TPE→KIX business — 8 筆

**樣本資料**：
- TPE→KIX business: 共 8 筆，最低票價 628
-   最低票價選項：$628 | Asiana Airlines | TPE→ICN (OZ, 150min)
-   $628 | Asiana Airlines | TPE→ICN (OZ, 140min)
-   $678 | Asiana Airlines, Korean Air | TPE→ICN (OZ, 140min)

---

### `ow_TPE_LHR_economy`

**狀態**：PASS ✅
**說明**：TPE→LHR economy — 7 筆

**樣本資料**：
- TPE→LHR economy: 共 7 筆，最低票價 699
-   最低票價選項：$699 | Emirates | TPE→DXB (EK, 570min)
-   $759 | Emirates | TPE→DXB (EK, 570min)
-   $811 | Etihad | TPE→AUH (EY, 530min)

---

### `ow_TPE_LHR_premium_economy`

**狀態**：PASS ✅
**說明**：TPE→LHR premium-economy — 4 筆

**樣本資料**：
- TPE→LHR premium-economy: 共 4 筆，最低票價 1156
-   最低票價選項：$1156 | Emirates | TPE→DXB (EK, 570min)
-   $1771 | China Airlines | TPE→LHR (CI, 910min)
-   $1775 | EVA Air | TPE→BKK (BR, 235min)

---

### `ow_TPE_LHR_business`

**狀態**：PASS ✅
**說明**：TPE→LHR business — 4 筆

**樣本資料**：
- TPE→LHR business: 共 4 筆，最低票價 2509
-   最低票價選項：$2509 | Etihad | TPE→AUH (EY, 530min)
-   $3018 | Emirates | TPE→DXB (EK, 570min)
-   $3808 | THAI | TPE→BKK (TG, 225min)

---

### `ow_TPE_LHR_first`

**狀態**：PASS ✅
**說明**：first class — 找到 4 筆（0 筆為正常）

**樣本資料**：
- TPE→LHR first: 共 4 筆，最低票價 6088
-   最低票價選項：$6088 | China Airlines, Korean Air | TPE→ICN (CI, 155min)
-   $6088 | Korean Air | TPE→ICN (KE, 160min)
-   $10987 | EVA Air, Cathay Pacific | TPE→HKG (BR, 120min)

---

### `ow_TPE_CDG_economy`

**狀態**：PASS ✅
**說明**：TPE→CDG economy — 5 筆

**樣本資料**：
- TPE→CDG economy: 共 5 筆，最低票價 739
-   最低票價選項：$739 | Emirates | TPE→DXB (EK, 570min)
-   $799 | Emirates | TPE→DXB (EK, 570min)
-   $828 | Turkish Airlines | TPE→IST (TK, 745min)

---

### `ow_TPE_CDG_business`

**狀態**：PASS ✅
**說明**：TPE→CDG business — 5 筆

**樣本資料**：
- TPE→CDG business: 共 5 筆，最低票價 2657
-   最低票價選項：$2657 | Emirates | TPE→DXB (EK, 570min)
-   $3003 | THAI | TPE→BKK (TG, 225min)
-   $3380 | Emirates | TPE→DXB (EK, 570min)

---

### `ow_TPE_FRA_economy`

**狀態**：PASS ✅
**說明**：TPE→FRA economy — 6 筆

**樣本資料**：
- TPE→FRA economy: 共 6 筆，最低票價 675
-   最低票價選項：$675 | Cathay Pacific, Qatar Airways | TPE→HKG (CX, 120min)
-   $689 | Emirates | TPE→DXB (EK, 570min)
-   $1335 | China Airlines | TPE→FRA (CI, 870min)

---

### `ow_TPE_JFK_economy`

**狀態**：PASS ✅
**說明**：TPE→JFK economy — 4 筆

**樣本資料**：
- TPE→JFK economy: 共 4 筆，最低票價 640
-   最低票價選項：$640 | Asiana Airlines, Delta | TPE→ICN (OZ, 150min)
-   $698 | Etihad | TPE→AUH (EY, 530min)
-   $885 | Korean Air | TPE→ICN (KE, 150min)

---

### `ow_TPE_JFK_premium_economy`

**狀態**：PASS ✅
**說明**：TPE→JFK premium-economy — 3 筆

**樣本資料**：
- TPE→JFK premium-economy: 共 3 筆，最低票價 1334
-   最低票價選項：$1334 | Cathay Pacific | TPE→HKG (CX, 125min)
-   $1351 | Asiana Airlines, Delta | TPE→ICN (OZ, 150min)
-   $2262 | United, Alaska | TPE→SFO (UA, 700min)

---

### `ow_TPE_JFK_business`

**狀態**：PASS ✅
**說明**：TPE→JFK business — 4 筆

**樣本資料**：
- TPE→JFK business: 共 4 筆，最低票價 2732
-   最低票價選項：$2732 | Korean Air, Asiana Airlines | TPE→ICN (KE, 150min)
-   $3477 | Cathay Pacific | TPE→HKG (CX, 125min)
-   $4838 | Cathay Pacific | TPE→HKG (CX, 130min)

---

### `ow_TPE_JFK_first`

**狀態**：PASS ✅
**說明**：first class — 找到 5 筆（0 筆為正常）

**樣本資料**：
- TPE→JFK first: 共 5 筆，最低票價 6627
-   最低票價選項：$6627 | Emirates | TPE→DXB (EK, 570min)
-   $6746 | EVA Air, ANA | TPE→NRT (BR, 205min)
-   $6749 | EVA Air, ANA | TPE→FUK (BR, 130min)

---

### `ow_TPE_LAX_economy`

**狀態**：PASS ✅
**說明**：TPE→LAX economy — 7 筆

**樣本資料**：
- TPE→LAX economy: 共 7 筆，最低票價 486
-   最低票價選項：$486 | Cathay Pacific | TPE→HKG (CX, 125min)
-   $561 | United | TPE→SFO (UA, 700min)
-   $561 | United | TPE→SFO (UA, 695min)

---

### `ow_TPE_LAX_business`

**狀態**：PASS ✅
**說明**：TPE→LAX business — 6 筆

**樣本資料**：
- TPE→LAX business: 共 6 筆，最低票價 1987
-   最低票價選項：$1987 | China Airlines, Philippine Airlines | TPE→MNL (CI, 140min)
-   $2619 | United | TPE→SFO (UA, 700min)
-   $2619 | United | TPE→SFO (UA, 695min)

---

### `ow_TPE_SFO_economy`

**狀態**：PASS ✅
**說明**：TPE→SFO economy — 3 筆

**樣本資料**：
- TPE→SFO economy: 共 3 筆，最低票價 517
-   最低票價選項：$517 | Delta | TPE→SEA (DL, 685min)
-   $742 | EVA Air | TPE→SFO (BR, 680min)
-   $1221 | EVA Air | TPE→SFO (BR, 680min)

---

## 來回 (Round-trip)

通過：10 / 10

### `rt_TPE_NRT_economy`

**狀態**：PASS ✅
**說明**：TPE↔NRT economy — 去程 20 筆，回程 20 筆

**樣本資料**：
- 去程 TPE→NRT: 共 20 筆，最低票價 230
-   最低票價選項：$230 | T'Way Air | TPE→TAE (TW, 145min)
-   $252 | Tigerair Taiwan | TPE→NRT (IT, 190min)
-   $260 | Thai Lion Air | TPE→NRT (SL, 200min)
- 回程 NRT→TPE: 共 20 筆，最低票價 230
-   最低票價選項：$230 | T'Way Air | TPE→TAE (TW, 145min)
-   $252 | Tigerair Taiwan | TPE→NRT (IT, 190min)
-   $260 | Thai Lion Air | TPE→NRT (SL, 200min)

---

### `rt_TPE_NRT_business`

**狀態**：PASS ✅
**說明**：TPE↔NRT business — 去程 6 筆，回程 6 筆

**樣本資料**：
- 去程 TPE→NRT: 共 6 筆，最低票價 1139
-   最低票價選項：$1139 | China Airlines | TPE→NRT (CI, 205min)
-   $1139 | China Airlines | TPE→NRT (CI, 205min)
-   $1215 | China Airlines | TPE→NRT (CI, 200min)
- 回程 NRT→TPE: 共 6 筆，最低票價 1139
-   最低票價選項：$1139 | China Airlines | TPE→NRT (CI, 205min)
-   $1139 | China Airlines | TPE→NRT (CI, 205min)
-   $1215 | China Airlines | TPE→NRT (CI, 200min)

---

### `rt_TPE_KIX_economy`

**狀態**：PASS ✅
**說明**：TPE↔KIX economy — 去程 15 筆，回程 15 筆

**樣本資料**：
- 去程 TPE→KIX: 共 15 筆，最低票價 232
-   最低票價選項：$232 | Tigerair Taiwan | TPE→KIX (IT, 170min)
-   $240 | Jetstar | TPE→KIX (GK, 155min)
-   $274 | T'Way Air | TPE→TAE (TW, 145min)
- 回程 KIX→TPE: 共 15 筆，最低票價 232
-   最低票價選項：$232 | Tigerair Taiwan | TPE→KIX (IT, 170min)
-   $240 | Jetstar | TPE→KIX (GK, 155min)
-   $274 | T'Way Air | TPE→TAE (TW, 145min)

---

### `rt_TPE_LHR_economy`

**狀態**：PASS ✅
**說明**：TPE↔LHR economy — 去程 4 筆，回程 4 筆

**樣本資料**：
- 去程 TPE→LHR: 共 4 筆，最低票價 1177
-   最低票價選項：$1177 | Emirates | TPE→DXB (EK, 570min)
-   $1184 | Asiana Airlines | TPE→ICN (OZ, 140min)
-   $1212 | Etihad | TPE→AUH (EY, 530min)
- 回程 LHR→TPE: 共 4 筆，最低票價 1177
-   最低票價選項：$1177 | Emirates | TPE→DXB (EK, 570min)
-   $1184 | Asiana Airlines | TPE→ICN (OZ, 140min)
-   $1212 | Etihad | TPE→AUH (EY, 530min)

---

### `rt_TPE_LHR_business`

**狀態**：PASS ✅
**說明**：TPE↔LHR business — 去程 7 筆，回程 7 筆

**樣本資料**：
- 去程 TPE→LHR: 共 7 筆，最低票價 5058
-   最低票價選項：$5058 | Emirates | TPE→DXB (EK, 570min)
-   $5071 | Cathay Pacific | TPE→HKG (CX, 120min)
-   $5254 | Emirates | TPE→DXB (EK, 570min)
- 回程 LHR→TPE: 共 7 筆，最低票價 5058
-   最低票價選項：$5058 | Emirates | TPE→DXB (EK, 570min)
-   $5071 | Cathay Pacific | TPE→HKG (CX, 120min)
-   $5254 | Emirates | TPE→DXB (EK, 570min)

---

### `rt_TPE_CDG_economy`

**狀態**：PASS ✅
**說明**：TPE↔CDG economy — 去程 4 筆，回程 4 筆

**樣本資料**：
- 去程 TPE→CDG: 共 4 筆，最低票價 1143
-   最低票價選項：$1143 | Emirates | TPE→DXB (EK, 570min)
-   $1186 | Emirates | TPE→DXB (EK, 570min)
-   $1555 | Cathay Pacific | TPE→HKG (CX, 120min)
- 回程 CDG→TPE: 共 4 筆，最低票價 1143
-   最低票價選項：$1143 | Emirates | TPE→DXB (EK, 570min)
-   $1186 | Emirates | TPE→DXB (EK, 570min)
-   $1555 | Cathay Pacific | TPE→HKG (CX, 120min)

---

### `rt_TPE_FRA_economy`

**狀態**：PASS ✅
**說明**：TPE↔FRA economy — 去程 4 筆，回程 4 筆

**樣本資料**：
- 去程 TPE→FRA: 共 4 筆，最低票價 1115
-   最低票價選項：$1115 | Emirates | TPE→DXB (EK, 570min)
-   $1627 | China Airlines, Condor | TPE→BKK (CI, 225min)
-   $1685 | China Airlines, Condor | TPE→BKK (CI, 225min)
- 回程 FRA→TPE: 共 4 筆，最低票價 1115
-   最低票價選項：$1115 | Emirates | TPE→DXB (EK, 570min)
-   $1627 | China Airlines, Condor | TPE→BKK (CI, 225min)
-   $1685 | China Airlines, Condor | TPE→BKK (CI, 225min)

---

### `rt_TPE_JFK_economy`

**狀態**：PASS ✅
**說明**：TPE↔JFK economy — 去程 4 筆，回程 4 筆

**樣本資料**：
- 去程 TPE→JFK: 共 4 筆，最低票價 889
-   最低票價選項：$889 | Delta | TPE→SEA (DL, 685min)
-   $956 | Etihad | TPE→AUH (EY, 530min)
-   $1114 | Asiana Airlines | TPE→ICN (OZ, 140min)
- 回程 JFK→TPE: 共 4 筆，最低票價 889
-   最低票價選項：$889 | Delta | TPE→SEA (DL, 685min)
-   $956 | Etihad | TPE→AUH (EY, 530min)
-   $1114 | Asiana Airlines | TPE→ICN (OZ, 140min)

---

### `rt_TPE_JFK_business`

**狀態**：PASS ✅
**說明**：TPE↔JFK business — 去程 5 筆，回程 5 筆

**樣本資料**：
- 去程 TPE→JFK: 共 5 筆，最低票價 3530
-   最低票價選項：$3530 | Korean Air, Asiana Airlines | TPE→ICN (KE, 150min)
-   $4503 | Delta | TPE→SEA (DL, 685min)
-   $6023 | Cathay Pacific | TPE→HKG (CX, 120min)
- 回程 JFK→TPE: 共 5 筆，最低票價 3530
-   最低票價選項：$3530 | Korean Air, Asiana Airlines | TPE→ICN (KE, 150min)
-   $4503 | Delta | TPE→SEA (DL, 685min)
-   $6023 | Cathay Pacific | TPE→HKG (CX, 120min)

---

### `rt_TPE_LAX_economy`

**狀態**：PASS ✅
**說明**：TPE↔LAX economy — 去程 6 筆，回程 6 筆

**樣本資料**：
- 去程 TPE→LAX: 共 6 筆，最低票價 686
-   最低票價選項：$686 | United | TPE→SFO (UA, 700min)
-   $686 | United | TPE→SFO (UA, 695min)
-   $763 | Korean Air | TPE→ICN (KE, 150min)
- 回程 LAX→TPE: 共 6 筆，最低票價 686
-   最低票價選項：$686 | United | TPE→SFO (UA, 700min)
-   $686 | United | TPE→SFO (UA, 695min)
-   $763 | Korean Air | TPE→ICN (KE, 150min)

---

## 多腿 (Multi-city)

通過：9 / 12

### `mc_TPE_NRT_KIX_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→NRT→KIX→TPE [economy] — 整趟總價 447 USD

**樣本資料**：
- [RPC] 整趟最低總價：447 USD
- [RPC] 第一腿可選選項數：7
- [RPC] 第一選項第一航段：TPE→NRT (GK, 200min)
- [獨立] 第 1 腿 TPE→NRT: 21 筆，最低 136 USD，airline=GK
- [獨立] 第 2 腿 NRT→KIX: 6 筆，最低 36 USD，airline=GK
- [獨立] 第 3 腿 KIX→TPE: 11 筆，最低 157 USD，airline=MM

---

### `mc_TPE_NRT_KIX_TPE_business`

**狀態**：PASS ✅
**說明**：TPE→NRT→KIX→TPE [business] — 整趟總價 3524 USD

**樣本資料**：
- [RPC] 整趟最低總價：3524 USD
- [RPC] 第一腿可選選項數：4
- [RPC] 第一選項第一航段：TPE→NRT (BR, 200min)
- [獨立] 第 1 腿 TPE→NRT: 8 筆，最低 628 USD，airline=OZ
- [獨立] 第 2 腿 NRT→KIX: 6 筆，最低 567 USD，airline=KE
- [獨立] 第 3 腿 KIX→TPE: 5 筆，最低 590 USD，airline=CI

---

### `mc_TPE_LHR_CDG_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→LHR→CDG→TPE [economy] — 整趟總價 1709 USD

**樣本資料**：
- [RPC] 整趟最低總價：1709 USD
- [RPC] 第一腿可選選項數：6
- [RPC] 第一選項第一航段：TPE→HKG (CX, 130min)
- [獨立] 第 1 腿 TPE→LHR: 4 筆，最低 614 USD，airline=EK
- [獨立] 第 2 腿 LHR→CDG: 13 筆，最低 99 USD，airline=AF
- [獨立] 第 3 腿 CDG→TPE: 7 筆，最低 495 USD，airline=EY

---

### `mc_TPE_LHR_CDG_TPE_business`

**狀態**：PASS ✅
**說明**：TPE→LHR→CDG→TPE [business] — 整趟總價 8410 USD

**樣本資料**：
- [RPC] 整趟最低總價：8410 USD
- [RPC] 第一腿可選選項數：5
- [RPC] 第一選項第一航段：TPE→DXB (EK, 570min)
- [獨立] 第 1 腿 TPE→LHR: 4 筆，最低 3072 USD，airline=TG
- [獨立] 第 2 腿 LHR→CDG: 13 筆，最低 268 USD，airline=AF
- [獨立] 第 3 腿 CDG→TPE: 7 筆，最低 2216 USD，airline=MF

---

### `mc_TPE_LHR_FRA_CDG_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→LHR→FRA→CDG→TPE [economy] — 整趟總價 1413 USD

**樣本資料**：
- [RPC] 整趟最低總價：1413 USD
- [RPC] 第一腿可選選項數：8
- [RPC] 第一選項第一航段：TPE→HKG (CX, 130min)
- [獨立] 第 1 腿 TPE→LHR: 7 筆，最低 554 USD，airline=CX
- [獨立] 第 2 腿 LHR→FRA: 10 筆，最低 169 USD，airline=VL
- [獨立] 第 3 腿 FRA→CDG: 9 筆，最低 100 USD，airline=LH
- [獨立] 第 4 腿 CDG→TPE: 10 筆，最低 617 USD，airline=EY

---

### `mc_TPE_JFK_LAX_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→JFK→LAX→TPE [economy] — 整趟總價 2059 USD

**樣本資料**：
- [RPC] 整趟最低總價：2059 USD
- [RPC] 第一腿可選選項數：4
- [RPC] 第一選項第一航段：TPE→SEA (DL, 685min)
- [獨立] 第 1 腿 TPE→JFK: 5 筆，最低 602 USD，airline=DL
- [獨立] 第 2 腿 JFK→LAX: 27 筆，最低 149 USD，airline=B6
- [獨立] 第 3 腿 LAX→TPE: 5 筆，最低 393 USD，airline=UA

---

### `mc_TPE_JFK_LAX_TPE_business`

**狀態**：FAIL ❌
**說明**：斷言失敗

**錯誤**：
```
total_price 應大於 0，實際 None
```

---

### `mc_TPE_NRT_LAX_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→NRT→LAX→TPE [economy] — 整趟總價 935 USD

**樣本資料**：
- [RPC] 整趟最低總價：935 USD
- [RPC] 第一腿可選選項數：12
- [RPC] 第一選項第一航段：TPE→NRT (BR, 210min)
- [獨立] 第 1 腿 TPE→NRT: 21 筆，最低 136 USD，airline=GK
- [獨立] 第 2 腿 NRT→LAX: 7 筆，最低 523 USD，airline=BR
- [獨立] 第 3 腿 LAX→TPE: 5 筆，最低 393 USD，airline=UA

---

### `mc_TPE_LHR_JFK_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→LHR→JFK→TPE [economy] — 整趟總價 8025 USD

**樣本資料**：
- [RPC] 整趟最低總價：8025 USD
- [RPC] 第一腿可選選項數：6
- [RPC] 第一選項第一航段：TPE→BKK (BR, 235min)
- [獨立] 第 1 腿 TPE→LHR: 4 筆，最低 614 USD，airline=EK
- [獨立] 第 2 腿 LHR→JFK: 23 筆，最低 396 USD，airline=FI
- [獨立] 第 3 腿 JFK→TPE: 8 筆，最低 486 USD，airline=OZ

---

### `mc_TPE_NRT_LAX_LHR_TPE_economy`

**狀態**：PASS ✅
**說明**：TPE→NRT→LAX→LHR→TPE [economy] — 整趟總價 9351 USD

**樣本資料**：
- [RPC] 整趟最低總價：9351 USD
- [RPC] 第一腿可選選項數：12
- [RPC] 第一選項第一航段：TPE→NRT (BR, 210min)
- [獨立] 第 1 腿 TPE→NRT: 15 筆，最低 156 USD，airline=UO
- [獨立] 第 2 腿 NRT→LAX: 6 筆，最低 696 USD，airline=CI
- [獨立] 第 3 腿 LAX→LHR: 18 筆，最低 434 USD，airline=AC
- [獨立] 第 4 腿 LHR→TPE: 5 筆，最低 648 USD，airline=OS

---

### `mc_TPE_NRT_LAX_LHR_TPE_business`

**狀態**：FAIL ❌
**說明**：斷言失敗

**錯誤**：
```
total_price 應大於 0，實際 None
```

---

### `mc_TPE_JFK_LHR_CDG_NRT_TPE_economy`

**狀態**：FAIL ❌
**說明**：斷言失敗

---
