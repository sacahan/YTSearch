# YouTube Search API

YouTube 搜尋 API - 透過爬蟲實現零成本的影片搜尋服務

## 功能特性

- ✅ 無需 YouTube API 金鑰，完全免費
- ✅ RESTful API 設計
- ✅ Redis 快取優化（1 小時 TTL）
- ✅ 完整影片元數據提取
- ✅ 支援排序與過濾
- ✅ Docker 容器化部署

## 快速開始

### 安裝依賴

```bash
uv sync
```

### 啟動服務

```bash
python main.py
```

服務將於 `http://localhost:8000` 啟動。

### API 文檔

訪問 `http://localhost:8000/docs` 查看互動式 API 文檔。

## API 使用範例

### 基本搜尋

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python教學"
```

### 指定結果數量

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python&limit=5"
```

### 按日期排序

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python&sort_by=date&limit=3"
```

## 環境配置

複製 `.env.example` 為 `.env` 並根據需要修改配置：

```bash
cp .env.example .env
```

## Docker 部署

```bash
docker-compose up -d
```

## 測試

```bash
pytest tests/
```

## 專案結構

```
src/youtube_search/
├── models/          # Pydantic 資料模型
├── services/        # 業務邏輯層
├── api/             # API 路由
└── utils/           # 工具函式
```

## 授權

MIT License
