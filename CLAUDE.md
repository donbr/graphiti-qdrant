# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python project providing semantic documentation search via a custom FastMCP server (`qdrant-docs`). The server enables semantic search over 2,670+ pre-indexed documentation pages from 7 sources (Anthropic, LangChain, Prefect, FastMCP, PydanticAI, Zep, McpProtocol) using OpenAI embeddings and Qdrant vector store.

**Key Components**:
- **MCP Server** (`mcp_server.py`) - FastMCP 2.0 server with `search_docs` and `list_sources` tools
- **Data Pipeline** - Downloads, splits, and uploads documentation to Qdrant
- **Test Suite** - 18 tests (11 in-memory, 7 HTTP) with 100% pass rate

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
# Run MCP server (stdio transport)
uv run python mcp_server.py

# Run HTTP server for testing
uv run python run_http_server.py

# Run in-memory tests
uv run pytest tests/test_mcp_server.py -v

# Run HTTP transport tests
uv run python test_http_local.py
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
   - Async download of llms.txt and llms-full.txt from 11 documentation sources
   - Sources: Cursor, PydanticAI, McpProtocol, FastMCP, LangChain, Prefect, Anthropic, OpenAI, Vue, Supabase, Zep
   - Outputs to `data/raw/{Source}/`
   - Generates `data/raw/manifest.json` with download status and metrics

2. **Analysis Stage** (`analyze_llms_structure.py`)
   - Analyzes top 4 largest sources (Cursor, LangChain, Anthropic, Prefect)
   - Examines document delimiters, header structure, JSX components
   - Provides splitting strategy recommendations
   - Used for understanding documentation structure before processing

3. **Splitting Stage** (`split_llms_pages.py`)
   - Two splitting strategies based on source format:
     - **URL Pattern**: Sources with `# Title\nSource: URL` format (LangChain, Anthropic, Prefect, FastMCP, McpProtocol)
     - **Header-Only Pattern**: Sources with just `# Title` (PydanticAI, Zep)
   - Handles code block neutralization to prevent false header matches
   - Outputs individual JSON files per page to `data/interim/pages/{Source}/`
   - Each page includes: title, source_url (if available), content, content_length

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

## Key Dependencies

**MCP Server**:
- **fastmcp**: FastMCP 2.0 server framework
- **langchain-qdrant**: Qdrant vector store integration
- **langchain-openai**: OpenAI embeddings (text-embedding-3-small)
- **qdrant-client**: Qdrant Cloud client

**Data Pipeline**:
- **httpx**: Async HTTP client for downloading documentation
- **langchain**: Framework for LLM applications

**Testing**:
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support

## Development Notes

### MCP Server
- Server configured at **user scope** in `~/.claude.json` (not project scope)
- Uses `llms-full-silver` Qdrant collection with 2,670 pre-indexed pages
- Two tools: `search_docs(query, k, source)` and `list_sources()`
- Comprehensive test coverage: 18 tests (11 in-memory, 7 HTTP) all passing
- Performance baseline: 2.4s avg response time (local HTTP)

### Data Pipeline
- Never commit `.env` files with real API keys - only commit `.env.example` with placeholders
- The `data/` directory structure supports a clear ETL pipeline: raw → interim → processed
- Async operations are used for efficient parallel downloads across multiple sources
- All scripts generate manifest.json files for tracking processing metadata and debugging

### Testing
- **In-memory tests** (`tests/test_mcp_server.py`) - Fast, zero-deployment validation
- **HTTP tests** (`test_http_local.py`) - Network transport validation
- Run tests before making changes to MCP server code
- See `docs/fastmcp-promotion/WEEK1_TESTING_SUMMARY.md` for detailed results

## Related Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[MCP-SETUP.md](MCP-SETUP.md)** - Comprehensive MCP server reference
- **[docs/fastmcp-promotion/](docs/fastmcp-promotion/)** - FastMCP Cloud promotion strategy
- **[.env.example](.env.example)** - Environment variable template with security guidance
