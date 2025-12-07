# YouTube Search API

Zero-cost YouTube video search service powered by web scraping

## Features

- ✅ No YouTube API key required - completely free
- ✅ RESTful API design with Swagger documentation
- ✅ MCP (Model Context Protocol) support - integrate with AI assistants
- ✅ Redis caching optimization (1 hour TTL)
- ✅ Complete video metadata extraction
- ✅ Sorting and filtering capabilities
- ✅ Docker containerization support

## Quick Start

### Install Dependencies

```bash
uv sync
```

### Start the Service

```bash
python main.py
```

The service will start at `http://localhost:8000`.

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Usage Examples

### Basic Search

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python tutorial"
```

### Specify Result Count

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python&limit=5"
```

### Sort by Date

```bash
curl "http://localhost:8000/api/v1/search?keyword=Python&sort_by=date&limit=3"
```

## MCP Integration (Model Context Protocol)

This service provides MCP server functionality, allowing AI assistants (such as Claude Desktop) to directly invoke YouTube search tools via the MCP protocol.

### MCP Service Types

- **HTTP Service**: Provided via StreamableHTTPSessionManager, integrated with existing FastAPI application
- **Supported Transport Modes**: HTTP (MVP)
- **Future Iterations**: Consider supporting stdio and SSE modes

### REST API and MCP Coexistence

- **REST API Preservation**: Existing REST API endpoints (`/api/v1/search`, etc.) remain fully functional
- **Flexible Deployment**: Choose between integrated (same FastAPI app) or separate (independent process) deployment
- **Backward Compatibility**: MCP additions do not modify any existing REST API signatures or behaviors

### MCP Configuration

#### Claude Desktop Setup

Add the following to Claude Desktop's configuration file (`~/.config/claude/settings.json` or `%APPDATA%\Claude\settings.json`):

```json
{
  "servers": {
    "youtube-search-mcp": {
      "command": "uv",
      "args": ["run", "python", "mcp_stdio.py"],
      "env": {
        "MCP_SEARCH_TIMEOUT": "15",
        "MCP_SEARCH_RETRIES": "3",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

#### Environment Variables

- `MCP_SEARCH_TIMEOUT` (default: 15 seconds): Search operation timeout
- `MCP_SEARCH_RETRIES` (default: 3 times): Retry attempts on search failure
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`: Redis cache configuration (optional)

### Starting the MCP Server

```bash
# Start MCP server (stdio mode)
python mcp_stdio.py

# Or using uv
uv run python mcp_stdio.py
```

### MCP Tool: youtube_search

**Tool Name**: `youtube_search`

**Description**: Search YouTube videos and return complete metadata

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyword` | string | ✅ | - | Search keyword (1-200 characters) |
| `limit` | integer | ❌ | 1 | Number of results to return (1-100) |
| `sort_by` | string | ❌ | relevance | Sort order: `relevance` or `date` |

**Response Format**:

```json
{
  "videos": [
    {
      "video_id": "mIF-nn_y2_8",
      "title": "Jackie Cheung - Farewell Kiss",
      "channel": "Music Without Boundaries",
      "url": "https://www.youtube.com/watch?v=mIF-nn_y2_8",
      "channel_url": "https://www.youtube.com/@channel_name",
      "publish_date": "2020-01-15",
      "view_count": "1500000",
      "description": "Classic Cantonese song..."
    }
  ],
  "message": "Successfully returned 1 result"
}
```

**Error Handling**:

- Empty keyword: Returns `{"error": "INVALID_KEYWORD", "message": "Search keyword cannot be empty..."}`
- Invalid limit: Returns `{"error": "INVALID_LIMIT", "message": "limit must be between 1-100..."}`
- YouTube service unavailable: Returns `{"error": "SERVICE_UNAVAILABLE", "message": "YouTube service is temporarily unavailable..."}`
- Cache service failure: Gracefully degrades to direct search and returns normal results

## Environment Configuration

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

## Docker Deployment

```bash
docker-compose up -d
```

## Testing

```bash
pytest tests/
```

## Project Structure

```
src/youtube_search/
├── models/          # Pydantic data models
├── services/        # Business logic layer
├── api/             # API routes
└── utils/           # Utility functions
```

## License

MIT License
