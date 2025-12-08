"""Documentation and API reference endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api", tags=["docs"])


@router.get(
    "/docs/swagger",
    response_class=HTMLResponse,
    summary="Swagger UI 文檔",
    include_in_schema=False,
)
async def swagger_ui() -> str:
    """返回 Swagger UI 文檔頁面。"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube 搜尋 API - Swagger UI</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
        <style>
            html {
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }
            *, *:before, *:after {
                box-sizing: inherit;
            }
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({
            url: "/api/openapi.json",
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            deepLinking: true
        })
        window.onload = function() {
            // do nothing
        }
        </script>
    </body>
    </html>
    """


@router.get(
    "/docs/redoc",
    response_class=HTMLResponse,
    summary="ReDoc 文檔",
    include_in_schema=False,
)
async def redoc_ui() -> str:
    """返回 ReDoc 文檔頁面。"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube 搜尋 API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """


@router.get(
    "/docs/openapi.json",
    summary="OpenAPI 規範",
    response_description="OpenAPI 3.1.0 規範 JSON",
)
async def get_openapi_schema() -> dict:
    """返回 OpenAPI 規範 JSON。"""
    from main import app

    return app.openapi()


@router.get(
    "/docs",
    response_class=HTMLResponse,
    summary="API 文檔主頁",
    include_in_schema=False,
)
async def docs_index() -> str:
    """返回文檔導航頁面。"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube 搜尋 API 文檔</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }
            .docs-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 40px;
            }
            @media (max-width: 600px) {
                .docs-grid {
                    grid-template-columns: 1fr;
                }
            }
            .doc-card {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 24px;
                transition: all 0.3s ease;
                text-decoration: none;
                display: block;
            }
            .doc-card:hover {
                border-color: #667eea;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
                transform: translateY(-4px);
            }
            .doc-card h2 {
                color: #667eea;
                margin-bottom: 12px;
                font-size: 1.3em;
            }
            .doc-card p {
                color: #666;
                font-size: 0.95em;
                line-height: 1.6;
            }
            .endpoints {
                background: #f5f5f5;
                border-radius: 8px;
                padding: 24px;
                margin-top: 30px;
            }
            .endpoints h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.3em;
            }
            .endpoint-list {
                list-style: none;
            }
            .endpoint-item {
                padding: 12px;
                border-left: 4px solid #667eea;
                margin-bottom: 10px;
                background: white;
                border-radius: 4px;
            }
            .endpoint-method {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 0.85em;
                margin-right: 10px;
            }
            .method-get {
                background: #61affe;
                color: white;
            }
            .method-post {
                background: #49cc90;
                color: white;
            }
            .endpoint-path {
                color: #333;
                font-family: monospace;
            }
            .version-info {
                color: #999;
                font-size: 0.9em;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 YouTube 搜尋 API</h1>
            <p class="subtitle">REST API 文檔與互動式工具</p>

            <div class="docs-grid">
                <a href="/api/docs/swagger" class="doc-card">
                    <h2>📘 Swagger UI</h2>
                    <p>互動式 API 文檔，可直接在瀏覽器中測試所有端點</p>
                </a>
                <a href="/api/docs/redoc" class="doc-card">
                    <h2>📗 ReDoc</h2>
                    <p>美化版 API 文檔，提供更佳的閱讀體驗</p>
                </a>
                <a href="/api/openapi.json" class="doc-card">
                    <h2>📄 OpenAPI JSON</h2>
                    <p>機器可讀的 OpenAPI 3.1.0 規範檔案</p>
                </a>
                <a href="https://github.com/sacahan/YTSearch" class="doc-card">
                    <h2>💻 GitHub 倉庫</h2>
                    <p>原始碼、Issue 追蹤與貢獻指南</p>
                </a>
            </div>

            <div class="endpoints">
                <h2>🔗 主要端點</h2>
                <ul class="endpoint-list">
                    <li class="endpoint-item">
                        <span class="endpoint-method method-get">GET</span>
                        <span class="endpoint-path">/api/v1/search</span>
                        <p style="color: #666; margin-top: 4px;">搜尋 YouTube 影片</p>
                    </li>
                    <li class="endpoint-item">
                        <span class="endpoint-method method-get">GET</span>
                        <span class="endpoint-path">/api/v1/playlist/metadata</span>
                        <p style="color: #666; margin-top: 4px;">取得播放列表元數據與曲目</p>
                    </li>
                    <li class="endpoint-item">
                        <span class="endpoint-method method-get">GET</span>
                        <span class="endpoint-path">/health</span>
                        <p style="color: #666; margin-top: 4px;">健康檢查端點</p>
                    </li>
                </ul>
            </div>

            <div class="version-info">
                <strong>API 版本：</strong> 1.0.0 | <strong>文檔版本：</strong> 2025-12-08
            </div>
        </div>
    </body>
    </html>
    """
