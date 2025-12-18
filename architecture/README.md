# Repository Architecture Documentation

**Project**: graphiti-qdrant
**Description**: Semantic documentation search via Qdrant vector store and FastMCP server
**Generated**: 2025-12-18
**Version**: 0.1.0

---

## Overview

This project implements a custom **MCP (Model Context Protocol) server** that provides semantic search over **4,969+ documentation pages** from **8 sources** using **Qdrant Cloud** vector database and **OpenAI embeddings**. It enables Claude Code (and other MCP clients) to search technical documentation using natural language queries.

### What Does This Do?

The MCP server exposes two primary tools:
1. **`search_docs`**: Semantic search across documentation using natural language queries
2. **`list_sources`**: List all available documentation sources with document counts

### Key Technologies

- **FastMCP 2.0**: MCP server framework with dual transport support (stdio, HTTP/SSE)
- **LangChain**: Document processing and vector store abstraction
- **Qdrant Cloud**: Managed vector database with 1536-dimensional embeddings
- **OpenAI**: text-embedding-3-small model for semantic embeddings
- **Python 3.11+**: Core implementation language

### Documentation Sources (8 Total)

| Source | Pages | Description |
|--------|-------|-------------|
| Anthropic | 932 | Claude API, MCP protocol, prompt engineering |
| Temporal | 2,299 | Workflow orchestration framework |
| Prefect | 767 | Modern workflow orchestration |
| LangChain | 506 | LLM application framework |
| FastMCP | 175 | FastMCP server framework |
| PydanticAI | 127 | Pydantic-based AI framework |
| Zep | 119 | Memory layer for LLM apps |
| McpProtocol | 44 | MCP protocol specification |
| **TOTAL** | **4,969** | |

---

## Quick Start

### For Readers

If you're **new to this project**, read in this order:

1. **Start here** (this README) - Get the big picture
2. [Component Inventory](docs/01_component_inventory.md) - Understand what each file does
3. [Architecture Diagrams](diagrams/02_architecture_diagrams.md) - See how components connect
4. [Data Flows](docs/03_data_flows.md) - Follow the request/response lifecycle
5. [API Reference](docs/04_api_reference.md) - Detailed function/class documentation

### For Developers

**Using the MCP Server**:
```bash
# Start stdio server (for Claude Code)
uv run python mcp_server.py

# Start HTTP server (for local testing/cloud deployment)
uv run python run_http_server.py
# Server available at: http://localhost:8000/mcp/

# Cloud production: https://qdrant-docs.fastmcp.app/mcp
```

**Testing**:
```bash
# In-memory tests (fastest, 80% coverage)
uv run pytest tests/test_mcp_server.py -v

# HTTP tests (requires server running, 15% coverage)
uv run python run_http_server.py  # Terminal 1
uv run python test_http_local.py  # Terminal 2

# Cloud tests (5% coverage)
uv run python test_cloud_deployment.py
```

**Data Pipeline** (refreshing documentation):
```bash
# 1. Download raw documentation
uv run python scripts/download_llms_raw.py

# 2. Parse into individual pages
uv run python scripts/split_llms_pages.py

# 3. Upload to Qdrant (with embeddings)
uv run python scripts/upload_to_qdrant.py

# 4. Validate collection
uv run python scripts/validate_qdrant.py
```

---

## Architecture Summary

### Layered Architecture

This system follows a **5-layer architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENT LAYER                                                 │
│ - Claude Code Desktop (stdio transport)                     │
│ - HTTP/Web Clients (SSE transport)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ MCP SERVER LAYER                                            │
│ - FastMCP Server (mcp_server.py)                            │
│ - Tools: search_docs(), list_sources()                      │
│ - Dual Transport: stdio (local) + HTTP/SSE (cloud)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ SEARCH & RETRIEVAL LAYER                                    │
│ - QdrantVectorStore (LangChain wrapper)                     │
│ - OpenAI Embeddings (text-embedding-3-small, 1536 dims)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                  │
│ - Qdrant Cloud (managed vector database)                   │
│ - Collection: llms-full-silver (4,969+ documents)           │
│ - Distance: COSINE, on_disk storage                         │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│ DATA PIPELINE LAYER (Offline ETL)                           │
│ 1. Download → 2. Parse → 3. Embed & Upload → 4. Validate   │
│ - 12 documentation sources → 4,969+ JSON docs → Vectors     │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Transport Agnostic**: Single server codebase supports both stdio (local Claude Code) and HTTP/SSE (web/cloud)
2. **No Chunking**: Full pages preserved for better context (avg 2,000 chars per page)
3. **Strategy Pattern**: 3 different document parsing strategies for different formats
4. **Batch Processing**: Parallel upload with 100 docs/batch, 4 workers
5. **Cost Optimization**: on_disk storage in Qdrant saves ~60% RAM costs
6. **Embedding Consistency**: Same OpenAI model (text-embedding-3-small) for upload and queries
7. **Read-Only Tools**: All MCP tools are read-only (search, list) for safety

### Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Factory** | `get_embeddings()`, `get_vector_store()` | Centralized configuration, dependency injection |
| **Strategy** | `split_llms_pages.py` | Different parsing strategies for different doc formats |
| **Pipeline** | Data pipeline scripts | Clear sequential ETL stages (download → parse → upload) |
| **Wrapper** | `QdrantVectorStore` | LangChain provides unified interface over Qdrant SDK |
| **Decorator** | `@mcp.tool()` | FastMCP auto-discovers and registers tools |

---

## Component Overview

### Public API Components

| Component | Purpose | Entry Point |
|-----------|---------|-------------|
| **MCP Server** | Main semantic search server | `mcp_server.py` (stdio) |
| **HTTP Server** | HTTP/SSE transport wrapper | `run_http_server.py` |
| **search_docs** | Semantic search tool | `mcp_server.py:73-166` |
| **list_sources** | List documentation sources | `mcp_server.py:169-226` |

### Data Pipeline Components

| Component | Purpose | Input → Output |
|-----------|---------|----------------|
| **download_llms_raw.py** | Download raw docs | 12 URLs → `data/raw/*.txt` |
| **split_llms_pages.py** | Parse into pages | `.txt` → `data/interim/pages/*.json` |
| **upload_to_qdrant.py** | Generate embeddings & upload | `.json` → Qdrant Cloud |
| **validate_qdrant.py** | Comprehensive validation | Qdrant → validation report |
| **embedding_config.py** | Shared embedding config | - → OpenAI embeddings |

### Test Components

| Component | Coverage | Test Count | Purpose |
|-----------|----------|------------|---------|
| **test_mcp_server.py** | 80% | 11 tests | In-memory server testing (Phase 1) |
| **test_http_local.py** | 15% | 7 tests | HTTP transport validation (Phase 2) |
| **test_cloud_deployment.py** | 5% | 6 tests | Production cloud validation (Phase 3) |

**Test Strategy**: Following FastMCP's 80/15/5 pyramid - most tests in-memory for speed, fewer integration tests, minimal cloud tests.

### Configuration Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `.env` | API keys & credentials | Root (not in git) |
| `.env.example` | Template for environment vars | Root |
| `pyproject.toml` | Python dependencies | Root |
| `uv.lock` | Locked dependency versions | Root |

---

## Data Flows

### Query Flow (Runtime)

The **search_docs** tool follows this flow:

```
1. Client Request
   ↓ (JSON-RPC: {"method": "call_tool", "params": {"name": "search_docs", ...}})
2. MCP Server (mcp_server.py)
   - Validates k parameter (clamp 1-20)
   - Initializes vector store
   ↓
3. Query Embedding
   - OpenAI API: text → 1536-dim vector (~200-500ms)
   ↓
4. Vector Search
   - Qdrant Cloud: COSINE similarity search (~100-300ms)
   - Returns top-k Document objects
   ↓
5. Result Formatting
   - Extracts metadata (title, source, URL)
   - Truncates content to 1000 chars
   - Formats as readable string
   ↓
6. Client Response
   - Returns formatted results string
```

**Performance**: Target < 10s, Avg HTTP: ~2.4s

See [Data Flows Documentation](docs/03_data_flows.md) for detailed sequence diagrams.

### Data Pipeline Flow (Offline ETL)

The **data pipeline** transforms raw documentation into searchable vectors:

```
Phase 1: Download (download_llms_raw.py)
  12 documentation sites
  ↓ (Async HTTP, parallel downloads)
  data/raw/{source}/llms-full.txt (12 files)

Phase 2: Parse (split_llms_pages.py)
  llms-full.txt files
  ↓ (3 parsing strategies: URL pattern, header-only, multi-level)
  data/interim/pages/{source}/XXXX_Title.json (4,969 files)

Phase 3: Embed & Upload (upload_to_qdrant.py)
  JSON documents
  ↓ (OpenAI embeddings, batch processing, 4 workers)
  Qdrant Cloud: llms-full-silver collection (4,969 vectors)
  data/processed/upload_manifest.json

Phase 4: Validate (validate_qdrant.py)
  Qdrant collection
  ↓ (4 validation categories, semantic search tests)
  Validation report (stdout, exit code 0/1)
```

**Total Pipeline Time**: ~25-35 minutes (10-15 min embedding, rest I/O)

### Session Flow (Interactive)

For **Claude Code** integration:

```
1. Claude Code launches MCP server as subprocess
   ↓
2. MCP Handshake (ping/pong)
   ↓
3. Tool Discovery (list_tools → 2 tools: search_docs, list_sources)
   ↓
4. User Interaction Loop
   - User asks question in Claude Code
   - Claude Code calls search_docs tool
   - Results displayed in conversation
   ↓ (Repeats)
5. Session End (stdin closes, server exits)
```

See [Data Flows Documentation](docs/03_data_flows.md) for complete sequence diagrams.

---

## Key Technologies & Design

### Vector Search Architecture

**Why Qdrant Cloud?**
- Managed service (no infrastructure management)
- gRPC support for performance
- On-disk storage saves RAM costs (~60% reduction)
- COSINE distance metric for semantic similarity

**Why OpenAI text-embedding-3-small?**
- Cost-effective: ~$0.02 per 1M tokens
- 1536 dimensions (good balance of quality vs size)
- Fast inference (~200-500ms per query)
- Widely used, well-tested model

### Document Parsing Strategies

Different documentation sites use different formats, requiring **3 parsing strategies**:

#### Strategy 1: URL Pattern (5 sources)
```markdown
# Page Title
Source: https://example.com/page-url

Page content...
```
**Used by**: LangChain, Anthropic, Prefect, FastMCP, McpProtocol

#### Strategy 2: Header-Only (2 sources)
```markdown
# Page Title

Page content...
```
**Challenge**: Python code blocks contain `# comments` that look like headers
**Solution**: Neutralize code block headers (`^#` → `^###` inside code blocks)
**Used by**: PydanticAI, Zep

#### Strategy 3: Multi-Level Hierarchy (1 source)
```markdown
# Level 1 Section

Content...

## Level 2 Subsection

Content...
```
**Features**: Tracks parent-child relationships, builds section_path breadcrumbs
**Used by**: Temporal (complex hierarchical docs)

See [Architecture Diagrams](diagrams/02_architecture_diagrams.md) for visual flow.

### Metadata Schema

Every document in Qdrant includes rich metadata:

**Core Fields** (all documents):
- `title`: Page title
- `source_name`: Documentation source (e.g., "LangChain")
- `source_url`: Original URL (null for header-only sources)
- `content_length`: Character count
- `doc_id`: Unique ID format `{source}_{page_num}`
- `page_number`: Zero-padded index (e.g., "0042")

**Manifest Fields** (from source-level metadata):
- `total_pages`: Total pages in source
- `avg_content_length`: Average page size in source

**Hierarchy Fields** (optional, Temporal only):
- `header_level`: 1 or 2 (# or ##)
- `section_path`: Breadcrumb path (e.g., "Getting Started > Installation")
- `parent_title`: Parent section title
- `parent_index`: Parent page index

This enables:
- **Filtering**: Search within specific sources
- **Context**: Display hierarchy in results
- **Analytics**: Page size, source statistics

---

## Project Statistics

### Codebase Metrics

| Category | Count | Details |
|----------|-------|---------|
| **Total Components** | 13 | 3 servers, 5 pipeline scripts, 3 test suites, 2 config |
| **Public API Tools** | 2 | search_docs, list_sources |
| **Documentation Sources** | 8 | Anthropic, Temporal, Prefect, LangChain, FastMCP, PydanticAI, Zep, McpProtocol |
| **Total Documents** | 4,969 | Individual documentation pages |
| **Test Coverage** | 24 tests | 11 in-memory + 7 HTTP + 6 cloud |

### Data Pipeline Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Raw Downloads** | 12 sources | ~15-20 MB total |
| **JSON Documents** | 4,969 files | Avg ~2,000 chars/page |
| **Vector Dimension** | 1,536 | OpenAI text-embedding-3-small |
| **Collection Size** | ~30 MB | Vectors + metadata |
| **Upload Time** | 12-15 min | Rate limited by OpenAI |
| **Validation Time** | 5-10 sec | 4 test categories |

### Performance Metrics

| Operation | Latency | Notes |
|-----------|---------|-------|
| **Search Query** | ~2.4s avg | HTTP transport, includes embedding + search |
| **List Sources** | ~1-3s | Full collection scroll |
| **Batch Upload** | ~400 docs/min | 4 workers, 100/batch |
| **OpenAI Embedding** | ~200-500ms | Per query |
| **Qdrant Search** | ~100-300ms | COSINE similarity |

---

## References

### Detailed Documentation

| Document | Description | Key Topics |
|----------|-------------|------------|
| [**01_component_inventory.md**](docs/01_component_inventory.md) | Complete component catalog | Public API, data pipeline, tests, configuration |
| [**02_architecture_diagrams.md**](diagrams/02_architecture_diagrams.md) | Visual architecture diagrams | System architecture, class hierarchies, module dependencies |
| [**03_data_flows.md**](docs/03_data_flows.md) | Detailed sequence diagrams | Query flow, session lifecycle, pipeline flow, message routing |
| [**04_api_reference.md**](docs/04_api_reference.md) | Complete API documentation | Function signatures, parameters, examples, best practices |

### Quick Reference

**Component Inventory** contains:
- Public API surface (MCP tools, HTTP endpoints)
- Internal implementation details
- Data pipeline components (download → parse → upload → validate)
- Test suite breakdown (80/15/5 coverage strategy)
- Configuration files and environment variables
- Entry points and usage examples

**Architecture Diagrams** contains:
- System architecture (5-layer view)
- Component relationships and dependencies
- Class hierarchies (FastMCP, LangChain, Qdrant)
- Module dependency graph
- Data flow diagram (end-to-end pipeline)
- Testing architecture (3-phase pyramid)
- Metadata schema (ER diagram)
- Document parsing strategies (flowchart)

**Data Flows** contains:
- Query flow (user request → search results)
- Interactive session flow (Claude Code integration)
- Tool permission/exposure flow (decorator-based registration)
- MCP server communication flow (stdio vs HTTP)
- Message parsing and routing (JSON-RPC handling)
- Data pipeline flow (complete ETL process)
- Performance characteristics
- Error handling patterns

**API Reference** contains:
- MCP Server API (`search_docs`, `list_sources`)
- HTTP Server API (transport modes)
- Configuration API (embeddings, environment variables)
- Data Pipeline API (download, parse, upload, validate)
- Usage patterns and examples
- Best practices
- Error handling
- Performance metrics
- Dependencies

---

## Environment Setup

### Prerequisites

- **Python**: 3.11 or higher
- **uv**: Package manager (https://github.com/astral-sh/uv)
- **API Keys**: Qdrant Cloud, OpenAI

### Installation

```bash
# Clone repository
git clone <repo-url>
cd graphiti-qdrant

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### Required Environment Variables

Create a `.env` file with:

```bash
# Qdrant Cloud credentials
QDRANT_API_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here

# OpenAI credentials
OPENAI_API_KEY=your-openai-api-key-here
```

Get credentials:
- **Qdrant**: https://cloud.qdrant.io/ (free tier available)
- **OpenAI**: https://platform.openai.com/api-keys

---

## Usage Examples

### Example 1: Basic Search

**Query**: "How do I build a RAG agent?"

**Python** (for testing):
```python
from mcp_server import search_docs

results = search_docs("How do I build a RAG agent?", k=5)
print(results)
```

**MCP Protocol** (Claude Code):
```json
{
  "method": "call_tool",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "How do I build a RAG agent?",
      "k": 5
    }
  }
}
```

**Response**:
```
Found 5 results for: 'How do I build a RAG agent?'

================================================================================
Result 1/5
================================================================================
Title: Build a Retrieval Agent
Source: LangChain
URL: https://python.langchain.com/docs/tutorials/agents
Doc ID: LangChain_0042

Content Preview (3245 chars total):
--------------------------------------------------------------------------------
In this tutorial we will build an agent that can answer questions using
a retrieval-augmented generation (RAG) approach...
[Truncated. Full content: 3245 chars]
...
```

### Example 2: Filtered Search

**Query**: "prompt caching" in Anthropic docs only

**Python**:
```python
from mcp_server import search_docs

results = search_docs(
    query="prompt caching strategies",
    k=3,
    source="Anthropic"
)
print(results)
```

**MCP Protocol**:
```json
{
  "method": "call_tool",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "prompt caching strategies",
      "source": "Anthropic",
      "k": 3
    }
  }
}
```

### Example 3: List Available Sources

**Python**:
```python
from mcp_server import list_sources

sources = list_sources()
print(sources)
```

**MCP Protocol**:
```json
{
  "method": "call_tool",
  "params": {
    "name": "list_sources",
    "arguments": {}
  }
}
```

**Response**:
```
Available Documentation Sources:

Source          Documents
------------------------------
Anthropic       932
FastMCP         175
LangChain       506
McpProtocol     44
Prefect         767
PydanticAI      127
Temporal        2299
Zep             119
------------------------------
TOTAL           4969

Use the 'source' parameter in search_docs() to filter by a specific source.
Example: search_docs('authentication', source='Anthropic')
```

---

## Contributing

### Extending Documentation Sources

To add a new documentation source:

1. **Add URL to download script**:
   ```python
   # scripts/download_llms_raw.py
   SOURCES = {
       'NewSource': (
           'https://docs.newsource.com/llms.txt',
           'https://docs.newsource.com/llms-full.txt',
       ),
       # ... existing sources
   }
   ```

2. **Choose parsing strategy** (analyze format first):
   ```bash
   # Run analysis utility
   uv run python scripts/analyze_llms_structure.py
   ```

3. **Add to appropriate strategy list**:
   ```python
   # scripts/split_llms_pages.py
   SOURCES_WITH_URL = ['LangChain', 'Anthropic', ..., 'NewSource']
   # OR
   SOURCES_HEADER_ONLY = ['PydanticAI', 'Zep', 'NewSource']
   # OR
   SOURCES_MULTI_LEVEL = ['Temporal', 'NewSource']
   ```

4. **Update expected counts**:
   ```python
   # scripts/validate_qdrant.py
   EXPECTED_SOURCES = {
       "NewSource": 999,  # Expected page count
       # ... existing sources
   }
   ```

5. **Run pipeline**:
   ```bash
   # Download
   uv run python scripts/download_llms_raw.py

   # Parse
   uv run python scripts/split_llms_pages.py

   # Upload (incremental - only new source)
   uv run python scripts/upload_to_qdrant.py --sources NewSource

   # Validate
   uv run python scripts/validate_qdrant.py
   ```

### Adding Tests

Follow the **80/15/5 test pyramid**:

1. **In-memory tests** (80%): Add to `tests/test_mcp_server.py`
   - Fast, deterministic
   - Test tool logic without network calls

2. **HTTP tests** (15%): Add to `test_http_local.py`
   - Validate transport layer
   - Test network behavior

3. **Cloud tests** (5%): Add to `test_cloud_deployment.py`
   - Verify production deployment
   - Final integration tests

### Updating Documentation

When making changes:

1. Update **component inventory** if adding/removing files
2. Update **architecture diagrams** if changing structure
3. Update **data flows** if changing request/response logic
4. Update **API reference** if changing function signatures
5. Update **this README** for high-level changes

---

## Troubleshooting

### Common Issues

**Issue**: `ValueError: QDRANT_API_KEY not set`
**Solution**: Check `.env` file exists and contains valid credentials

**Issue**: `No results found for query: 'xyz'`
**Solution**: Try broader query, check source filter, verify collection has data

**Issue**: Search returns "Index required for filtering" note
**Solution**: Optional feature - creates payload index for better performance:
```python
from qdrant_client import QdrantClient
client = QdrantClient(url=..., api_key=...)
client.create_payload_index(
    collection_name="llms-full-silver",
    field_name="metadata.source_name"
)
```

**Issue**: Upload fails with rate limit error
**Solution**: Reduce workers or batch size:
```bash
uv run python scripts/upload_to_qdrant.py --workers 2 --batch-size 50
```

**Issue**: Validation fails with document count mismatch
**Solution**: Update expected counts in `validate_qdrant.py` or re-upload failed sources

### Debug Mode

Enable verbose logging:
```bash
# Set environment variable
export FASTMCP_DEBUG=1

# Run server
uv run python mcp_server.py
```

### Health Checks

**Test MCP Server**:
```bash
# In-memory test (fastest)
uv run pytest tests/test_mcp_server.py::test_server_ping -v

# HTTP test (requires server running)
# Terminal 1:
uv run python run_http_server.py
# Terminal 2:
uv run python test_http_local.py
```

**Test Qdrant Connection**:
```python
from scripts.upload_to_qdrant import init_qdrant_client

client = init_qdrant_client()
info = client.get_collection("llms-full-silver")
print(f"Collection status: {info.status}")
print(f"Points: {info.points_count}")
```

**Test OpenAI Embeddings**:
```bash
uv run python scripts/embedding_config.py

# Should output:
# Testing embedding configuration...
# ✓ Embedding successful!
#   Vector dimension: 1536
```

---

## License

[Specify license here - commonly MIT]

---

## Acknowledgments

- **FastMCP**: MCP server framework (https://github.com/jlowin/fastmcp)
- **LangChain**: Document processing framework
- **Qdrant**: Vector database platform
- **OpenAI**: Embedding models

---

## Contact & Support

For issues or questions:
- **Repository Issues**: [GitHub Issues URL]
- **Documentation**: See reference docs in this directory
- **API Reference**: [04_api_reference.md](docs/04_api_reference.md)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-18
**Generated By**: Claude Opus 4.5 (Technical Documentation Expert)
