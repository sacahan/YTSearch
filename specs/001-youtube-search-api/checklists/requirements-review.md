# 需求品質檢查清單：YouTube 搜尋 API

**功能**：`001-youtube-search-api` | **建立日期**：2025-12-07 | **深度**：輕量級 | **受眾**：作者自檢
**規範文件**：`spec.md` + `plan.md` + `data-model.md` + `contracts/openapi.yaml`

**用途**：此檢查清單驗證需求文件的品質（完整性、明確性、一致性），而非驗證實作。每個項目測試需求本身是否寫得清楚，而非系統是否正確運作。

---

## 需求完整性

- [ ] **CHK001** - 功能需求是否覆蓋所有核心流程（搜尋、metadata 提取、快取、錯誤處理）？ [Completeness, Spec §FR]
- [ ] **CHK002** - 是否定義了所有查詢參數的預設值和約束（keyword 必須、limit 1-100、sort_by 選項）？ [Completeness, Spec §FR-001]
- [ ] **CHK003** - 所有 HTTP 錯誤情境是否都明確定義回應格式（400、503 等）？ [Completeness, Spec §FR-007]
- [ ] **CHK004** - Redis 快取策略是否完整定義（TTL、鍵格式、失敗降級）？ [Completeness, Plan §Phase 1]
- [ ] **CHK005** - metadata 欄位的可選策略是否明確（video_id 必須，其他最佳努力 + null 容錯）？ [Completeness, Spec §FR-003]

---

## API 合約品質

- [ ] **CHK006** - OpenAPI 規格是否定義所有查詢參數的類型、範圍、驗證規則？ [Clarity, Contracts]
- [ ] **CHK007** - 成功和失敗回應的 JSON 結構是否明確一致？ [Clarity, Contracts §responses]
- [ ] **CHK008** - 是否定義了 `error_code` 的完整列表（e.g., INVALID_KEYWORD_LENGTH、YOUTUBE_UNAVAILABLE）？ [Clarity, Spec §FR-007]
- [ ] **CHK009** - API 版本策略是否定義（/api/v1/ 路由如何支援後續升級）？ [Clarity, Plan §API 層]

---

## 資料模型完整性

- [ ] **CHK010** - Video 模型的所有欄位是否有清晰的型別、可選性、驗證規則文檔？ [Clarity, Data-Model]
- [ ] **CHK011** - SearchResult 模型的 `timestamp` 格式是否明確（ISO 8601 UTC）？ [Clarity, Plan §SearchResult]
- [ ] **CHK012** - 是否定義了 metadata 部分缺失時的 JSON 序列化行為（null vs 省略）？ [Clarity, Data-Model]
- [ ] **CHK013** - keyword 參數的驗證規則是否清楚（1-200 字元、Unicode 支援、特殊字符編碼）？ [Clarity, Spec §FR-001]

---

## 邊界情況與恢復

- [ ] **CHK014** - YouTube 連線失敗時的行為是否定義（HTTP 503、不重試）？ [Coverage, Spec §FR-008]
- [ ] **CHK015** - limit 超過 100 或小於 1 時是否定義錯誤回應？ [Coverage, Spec §FR-002]
- [ ] **CHK016** - Redis 快取不可用時的降級策略是否定義（繞過快取或返回快取失敗錯誤）？ [Coverage, Gap]
- [ ] **CHK017** - 搜尋返回 0 結果時是否定義正確回應（empty array vs 錯誤）？ [Coverage, Gap]

---

## 非功能需求明確性

- [ ] **CHK018** - 效能需求（3 秒內返回）是否可測量和驗證？ [Measurability, Plan §效能目標]
- [ ] **CHK019** - Redis TTL（3600 秒）是否在需求中明確記錄？ [Clarity, Plan §快取策略]
- [ ] **CHK020** - Python 3.12+ 版本要求是否明確（與依賴版本一致）？ [Clarity, Plan §技術背景]

---

## 一致性檢查

- [ ] **CHK021** - 規範、計劃、資料模型中對 metadata 欄位的定義是否一致？ [Consistency, Spec §FR-003 vs Data-Model]
- [ ] **CHK022** - API 回應格式在規範和 OpenAPI 中是否一致（成功 HTTP 200、錯誤 status + error_code）？ [Consistency, Spec §FR-007 vs Contracts]

---

## 歧義與假設

- [ ] **CHK023** - 「最佳努力」metadata 提取失敗時，是否明確允許 null？ [Ambiguity, Spec §FR-003]
- [ ] **CHK024** - 快取鍵的 SHA256 生成是否明確記錄實現細節（e.g., 如何處理 keyword 編碼）？ [Ambiguity, Plan §快取策略]
- [ ] **CHK025** - sort_by 參數值（relevance、date）是否對應 YouTube 實際排序選項？ [Assumption, Spec §FR-002]

---

**完成指引**：

1. 逐項檢查，遇到「否」時在相應規範文件中補充定義
2. 項目編號 CHK001-CHK025 供追蹤使用
3. 檢查完成後建議執行 `/speckit.tasks` 進入任務規劃階段

**檢查完成日期**：________ | **檢查者**：________ | **發現問題數**：________
