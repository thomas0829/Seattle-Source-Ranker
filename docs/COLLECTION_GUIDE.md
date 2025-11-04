# 🚀 快速收集指南

## 即時顯示版本 (推薦)

使用 `collect_now.sh` 或 `collect.sh` 獲得最佳即時輸出體驗:

```bash
# 快速測試 - 100 個專案
./collect_now.sh --target 100 --min-stars 5

# 中型收集 - 1,000 個專案 (~2 分鐘)
./collect_now.sh --target 1000 --min-stars 5

# 大型收集 - 10,000 個專案 (~20 分鐘)
./collect_now.sh --target 10000 --min-stars 5

# 超大型收集 - 100,000 個專案 (需分批或多 token)
./collect_now.sh --target 100000 --min-stars 10
```

## 參數說明

- `--target`: 目標專案數量
- `--min-stars`: 最低 star 數篩選 (預設 0)
- `--min-followers`: 最低用戶 follower 數 (預設 0)
- `--location`: 搜尋地區 (預設 seattle)
- `--tokens`: 多個 token (逗號分隔) 用於加速
- `--output`: 輸出檔案路徑

## 多 Token 加速

如果您有多個 GitHub 帳號:

```bash
./collect_now.sh --target 100000 --min-stars 5 \
  --tokens "token1,token2,token3,token4"
```

## 斷點續傳

程式會自動儲存進度到 `data/checkpoint.json`。如果中斷,再次執行時會詢問是否從斷點繼續。

## 即時進度顯示

程式會顯示:
- ✅ 當前處理的用戶名
- 📊 已收集的專案數
- ⏱️ 預估剩餘時間
- 🔄 每個用戶新增的專案數

## 常見問題

### Q: 為什麼輸出有延遲?

A: 使用 `./collect_now.sh` 而不是 `conda run`,可以避免輸出緩衝。

### Q: 如何收集 100,000 個專案?

A: 三種方法:
1. **分批**: 每次 25,000,等待 1 小時後繼續
2. **多 token**: 使用 4-5 個 tokens 並行
3. **提高門檻**: 使用 `--min-stars 10` 只收集優質專案

### Q: API 限制問題?

A: 程式會自動檢測並等待 rate limit 重置。使用多 token 可避免等待。

## 效能參考

| 專案數 | 預估時間 | API 使用 |
|--------|----------|----------|
| 100 | 5-10 秒 | ~20 requests |
| 1,000 | 1-2 分鐘 | ~200 requests |
| 10,000 | 15-20 分鐘 | ~2,000 requests |
| 100,000 | 2-3 小時 | ~20,000 requests |

*使用單 token,實際時間取決於網路速度和 GitHub API 響應*
