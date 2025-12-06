# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python project providing semantic documentation search via a custom FastMCP server (`qdrant-docs`). The server enables semantic search over 4,969+ pre-indexed documentation pages from 8 sources (Anthropic, LangChain, Prefect, FastMCP, PydanticAI, Zep, McpProtocol, Temporal) using OpenAI embeddings and Qdrant vector store.

**Key Components**:
- **MCP Server** (`mcp_server.py`) - FastMCP 2.0 server exposing `search_docs` and `list_sources` tools
- **Data Pipeline** (`scripts/`) - ETL pipeline for documentation processing
- **Test Suite** - 18 tests (11 in-memory, 7 HTTP) with 100% pass rate
- **Cloud Deployment** - FastMCP Cloud endpoint at https://qdrant-docs.fastmcp.app/mcp

## Environment Setup

This project uses `uv` for dependency management and Python 3.11+.

### Initial Setup
```bash
# Install dependencies
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env with your QDRANT_API_KEY and QDRANT_API_URL
```

### Required Environment Variables
- `QDRANT_API_KEY`: Your Qdrant API key
- `QDRANT_API_URL`: Your Qdrant instance URL (e.g., https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333)
- `OPENAI_API_KEY`: OpenAI API key (for text-embedding-3-small)

## Common Commands

### MCP Server
```bash
# Run MCP server (stdio transport, default)
uv run python mcp_server.py

# Run HTTP server for local testing (requires separate terminal)
uv run python run_http_server.py

# Test suite - in-memory validation (fast, no network required for FastMCP tests)
uv run pytest tests/test_mcp_server.py -v

# Test suite - HTTP transport validation (requires run_http_server.py running)
uv run python test_http_local.py

# Run single test
uv run pytest tests/test_mcp_server.py::test_search_docs_basic -v
```

### Data Pipeline Scripts
```bash
# Download llms.txt and llms-full.txt from all configured sources
uv run scripts/download_llms_raw.py

# Analyze structure of downloaded documentation
uv run scripts/analyze_llms_structure.py

# Split llms-full.txt files into individual pages/documents
uv run scripts/split_llms_pages.py

# Upload split pages to Qdrant vector store
uv run scripts/upload_to_qdrant.py
```

## Data Pipeline Architecture

### Directory Structure
```
data/
├── raw/                    # Downloaded llms.txt and llms-full.txt files
│   ├── {Source}/          # One directory per source (Cursor, LangChain, etc.)
│   │   ├── llms.txt
│   │   ├── llms-full.txt
│   └── manifest.json      # Download metadata and status
├── interim/               # Intermediate processing results
│   └── pages/            # Individual pages split from llms-full.txt
│       ├── {Source}/     # One directory per source
│       │   ├── 0000_Page_Title.json
│       │   ├── manifest.json
│       └── manifest.json  # Overall processing metadata
└── processed/            # Final processed data ready for vector DB
```

### Processing Pipeline

1. **Download Stage** (`download_llms_raw.py`)
   - Async download of llms.txt and llms-full.txt from 12 documentation sources
   - Sources: Cursor, PydanticAI, McpProtocol, FastMCP, LangChain, Prefect, Anthropic, OpenAI, Vue, Supabase, Zep, Temporal
   - Outputs to `data/raw/{Source}/`
   - Generates `data/raw/manifest.json` with download status and metrics

2. **Analysis Stage** (`analyze_llms_structure.py`)
   - Analyzes top 4 largest sources (Cursor, LangChain, Anthropic, Prefect)
   - Examines document delimiters, header structure, JSX components
   - Provides splitting strategy recommendations
   - Used for understanding documentation structure before processing

3. **Splitting Stage** (`split_llms_pages.py`)
   - Three splitting strategies based on source format:
     - **URL Pattern**: Sources with `# Title\nSource: URL` format (LangChain, Anthropic, Prefect, FastMCP, McpProtocol)
     - **Header-Only Pattern**: Sources with just `# Title` (PydanticAI, Zep)
     - **Multi-Level Pattern**: Sources split on both `# ` and `## ` headers (Temporal)
   - Handles code block neutralization to prevent false header matches
   - Outputs individual JSON files per page to `data/interim/pages/{Source}/`
   - Each page includes: title, source_url (if available), content, content_length, header_level (if multi-level)

### Document Splitting Patterns

**URL Pattern** (most sources):
```
# Page Title
Source: https://example.com/page

[page content]
```

**Header-Only Pattern** (PydanticAI, Zep):
```
# Page Title

[page content]
```

The header-only pattern uses code block neutralization: converts `# ` inside code blocks to `### ` to prevent Python comments from being treated as page delimiters.

**Multi-Level Pattern** (Temporal):
```
# Level 1 Title

[content]

## Level 2 Title

[content]
```

The multi-level pattern splits on both `# ` (level 1) AND `## ` (level 2) headers, with code block neutralization applied. Each page includes a `header_level` field (1 or 2) for future filtering/ranking.

## Architecture

### MCP Server Design (`mcp_server.py`)

The server uses a **lazy initialization pattern** for the vector store:
- `get_vector_store()` creates new `QdrantVectorStore` instance on each call
- `QdrantClient` initialized with `prefer_grpc=True` for performance
- OpenAI embeddings configured to match upload settings (1536 dimensions)

**Two MCP Tools**:
1. `search_docs(query, k, source)` - Semantic search with optional source filtering
   - Falls back to client-side filtering when Qdrant payload index missing
   - Results truncated to 1000 chars preview (full content available on request)
   - Clamps `k` parameter between 1-20 to prevent excessive API costs

2. `list_sources()` - Returns hardcoded source counts (static data)
   - No Qdrant API calls required
   - Document counts: Anthropic (932), LangChain (571), Prefect (767), FastMCP (189), McpProtocol (44), PydanticAI (127), Zep (123), Temporal (2216)

### Data Pipeline Architecture

**Four-stage ETL pipeline** (`scripts/` directory):

1. **Download** (`download_llms_raw.py`)
   - Async downloads using `httpx.AsyncClient`
   - Fetches both `llms.txt` (URLs only) and `llms-full.txt` (full content)
   - Outputs to `data/raw/{Source}/`
   - Generates `manifest.json` with download metadata

2. **Analyze** (`analyze_llms_structure.py`)
   - Examines document structure and delimiters
   - Used for debugging and validating splitting strategies
   - Not required for normal pipeline operation

3. **Split** (`split_llms_pages.py`)
   - Parses `llms-full.txt` using regex patterns
   - Two strategies: URL Pattern (most sources) vs Header-Only Pattern (PydanticAI, Zep)
   - Handles code block neutralization to prevent false header matches
   - Outputs individual JSON files to `data/interim/pages/{Source}/`

4. **Upload** (`upload_to_qdrant.py`)
   - Creates embeddings using OpenAI text-embedding-3-small (1536d)
   - Uploads to Qdrant collection `llms-full-silver`
   - Uses `QdrantVectorStore.from_documents()` with metadata

### Key Dependencies

**MCP Server**:
- `fastmcp` - FastMCP 2.0 framework (declarative tool definitions via decorators)
- `langchain-qdrant` - Qdrant vector store wrapper with LangChain interface
- `langchain-openai` - OpenAI embeddings integration
- `qdrant-client` - Direct Qdrant API client (used for gRPC and filtering)

**Data Pipeline**:
- `httpx` - Async HTTP client for parallel source downloads
- `python-dotenv` - Environment variable management

**Testing**:
- `pytest` + `pytest-asyncio` - Test framework with async support

## Development Notes

### MCP Server Configuration
- **User scope deployment** in `~/.claude.json` (NOT project scope in `claude_mcp.json`)
- Two server endpoints available:
  - `qdrant-docs` - Cloud endpoint at https://qdrant-docs.fastmcp.app/mcp
  - `qdrant-docs-local` - Local stdio endpoint (`uv run python mcp_server.py`)
- Uses `llms-full-silver` Qdrant collection (shared across both endpoints)
- Environment variables must be accessible globally (set in `~/.bashrc` or `~/.zshrc`)
- Performance baseline: 2.4s avg response time (local HTTP), varies on cloud

### Data Pipeline
- Never commit `.env` files with real API keys - only commit `.env.example` with placeholders
- The `data/` directory structure supports a clear ETL pipeline: raw → interim → processed
- Async operations are used for efficient parallel downloads across multiple sources
- All scripts generate manifest.json files for tracking processing metadata and debugging

### Testing Strategy

**Two-layer testing approach**:

1. **In-memory tests** (`tests/test_mcp_server.py`)
   - Uses FastMCP's built-in test client (no network server required)
   - Validates tool logic, parameter handling, error cases
   - Makes real Qdrant API calls (requires valid credentials in .env)
   - 11 tests covering: connectivity, tools, search, filtering, performance
   - Run time: ~24s (includes real vector search operations)

2. **HTTP transport tests** (`test_http_local.py`)
   - Validates actual HTTP/SSE transport layer
   - Requires `run_http_server.py` running in separate terminal
   - 7 tests covering: connectivity, tools, search, performance, errors
   - Performance target: < 5.0s response time

**Important**: Run tests before making changes to MCP server code. See `docs/fastmcp-promotion/WEEK1_TESTING_SUMMARY.md` for baseline metrics.

## Related Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[MCP-SETUP.md](MCP-SETUP.md)** - Comprehensive MCP server reference
- **[docs/VECTOR_DB_REFRESH_GUIDE.md](docs/VECTOR_DB_REFRESH_GUIDE.md)** - Best practices for dropping/replacing vector database content
- **[docs/fastmcp-promotion/](docs/fastmcp-promotion/)** - FastMCP Cloud promotion strategy
- **[.env.example](.env.example)** - Environment variable template with security guidance
