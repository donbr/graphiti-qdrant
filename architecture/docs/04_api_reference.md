# API Reference

**Project**: graphiti-qdrant
**Version**: 0.1.0
**Generated**: 2025-12-18
**Python Version**: >=3.11

---

## Overview

This API reference documents all public functions, classes, and interfaces for the graphiti-qdrant MCP server project. The project provides semantic search over documentation sources using Qdrant vector store and OpenAI embeddings.

**Key Components**:
- **MCP Server API**: Public tools for semantic search (`search_docs`, `list_sources`)
- **Configuration API**: Environment variables and embedding configuration
- **Data Pipeline API**: Download, parsing, upload, and validation functions
- **Transport Modes**: stdio (local) and HTTP/SSE (cloud)

**Architecture Pattern**: MCP Server with ETL Data Pipeline
**Main Technologies**: FastMCP 2.0, LangChain, Qdrant Cloud, OpenAI embeddings

---

## MCP Server API

### Module: `mcp_server.py`

Main MCP server exposing semantic search tools for Claude Code integration.

**Location**: `mcp_server.py`

#### Constants

```python
COLLECTION_NAME = "llms-full-silver"  # Qdrant collection name
DEFAULT_K = 5                          # Default number of search results
```

---

### Function: `get_vector_store()`

Initialize and return Qdrant vector store with OpenAI embeddings.

**Signature**:
```python
def get_vector_store() -> QdrantVectorStore
```

**Returns**:
- `QdrantVectorStore`: Configured vector store instance ready for queries

**Raises**:
- `ValueError`: If required environment variables are missing (`QDRANT_API_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY`)

**Environment Variables Required**:
- `QDRANT_API_URL` (str): Qdrant Cloud instance URL
- `QDRANT_API_KEY` (str): Qdrant API key
- `OPENAI_API_KEY` (str): OpenAI API key for embeddings

**Configuration Details**:
- **Collection**: `llms-full-silver`
- **Embedding Model**: `text-embedding-3-small`
- **Embedding Dimensions**: 1536
- **Distance Metric**: COSINE
- **gRPC**: Enabled for performance

**Source**: Lines 29-70

**Example Usage**:
```python
from mcp_server import get_vector_store

# Initialize vector store
vector_store = get_vector_store()

# Perform semantic search
results = vector_store.similarity_search("How do I build a RAG agent?", k=5)
```

**Implementation Notes**:
- Creates new client instances on each call (stateless design)
- Validates all required environment variables before initialization
- Uses gRPC transport for better performance with Qdrant Cloud

---

### Tool: `search_docs`

Search documentation using semantic similarity.

**Signature**:
```python
@mcp.tool()
def search_docs(query: str, k: int = DEFAULT_K, source: Optional[str] = None) -> str
```

**Parameters**:
- `query` (str, required): Natural language search query
  - Example: `"How do I build a RAG agent?"`
  - Example: `"What are Claude's API features?"`
- `k` (int, optional): Number of results to return
  - Default: `5`
  - Range: Automatically clamped between 1 and 20
  - Example: `k=10`
- `source` (str, optional): Filter by source name
  - Default: `None` (search all sources)
  - Valid values: `"LangChain"`, `"Anthropic"`, `"Prefect"`, `"FastMCP"`, `"McpProtocol"`, `"PydanticAI"`, `"Zep"`, `"Temporal"`
  - Example: `source="Anthropic"`

**Returns**:
- `str`: Formatted search results with titles, sources, URLs, and content previews
- Returns error message string if search fails

**Source**: Lines 73-166

**Algorithm**:
1. Validates and clamps `k` parameter to range [1, 20]
2. Initializes vector store with OpenAI embeddings
3. Builds Qdrant filter if `source` parameter specified
4. Performs similarity search via LangChain's `QdrantVectorStore.similarity_search()`
5. Formats results with metadata and content previews (1000 chars)

**Metadata Included in Results**:
- `title`: Document title
- `source_name`: Source name (e.g., "LangChain")
- `source_url`: Original documentation URL
- `doc_id`: Unique document identifier
- `header_level`: Header level (for multi-level sources like Temporal)
- `section_path`: Hierarchical section path
- `parent_title`: Parent section title (if applicable)

**Error Handling**:
- **Payload Index Missing**: Falls back to Python-side filtering if Qdrant payload index not created
  - Fetches `k*3` results and filters manually
  - Returns note about missing index
- **No Results**: Returns descriptive message: `"No results found for query: '{query}'"`
- **Exceptions**: Catches all exceptions and returns error string: `"Error during search: {error}"`

**Example Usage**:

**Basic Search**:
```python
# Via MCP protocol (JSON-RPC)
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

**Filtered Search**:
```python
{
  "method": "call_tool",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "prompt caching",
      "source": "Anthropic",
      "k": 3
    }
  }
}
```

**Direct Python Usage** (for testing):
```python
from mcp_server import search_docs

# Basic search
results = search_docs("authentication methods", k=5)
print(results)

# Filtered search
results = search_docs("workflow orchestration", k=3, source="Prefect")
print(results)
```

**Example Output**:
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

================================================================================
Result 2/5
================================================================================
...
```

**Performance**:
- Target: < 10s (includes network latency)
- Average: ~2.4s for HTTP transport
- Bottlenecks: OpenAI embedding API (~200-500ms) + Qdrant search (~100-300ms)

**Notes**:
- Content preview limited to 1000 chars to keep responses manageable
- Full content available in vector store but truncated in output
- Source filtering requires payload index for optimal performance (optional)

---

### Tool: `list_sources`

List all available documentation sources in the vector store.

**Signature**:
```python
@mcp.tool()
def list_sources() -> str
```

**Parameters**: None

**Returns**:
- `str`: Formatted table of sources with document counts and usage examples
- Returns error message string if operation fails

**Source**: Lines 169-226

**Algorithm**:
1. Initializes vector store
2. Uses Qdrant `scroll()` API to iterate through all documents
3. Counts documents per source by reading `metadata.source_name` field
4. Formats results as a table

**Example Output**:
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

**Example Usage**:

**Via MCP Protocol**:
```python
{
  "method": "call_tool",
  "params": {
    "name": "list_sources",
    "arguments": {}
  }
}
```

**Direct Python Usage**:
```python
from mcp_server import list_sources

# List all sources
sources_table = list_sources()
print(sources_table)
```

**Performance**:
- Requires full collection scroll (100 docs per batch)
- Time: ~1-3s for 4969 documents
- Reads metadata only (no vectors loaded)

**Error Handling**:
- Catches all exceptions and returns error string
- Example: `"Error retrieving source counts: {error}"`

---

## HTTP Server API

### Module: `run_http_server.py`

Run MCP server with HTTP/SSE transport for local testing and cloud deployment.

**Location**: `run_http_server.py`

#### Function: `main`

**Signature**:
```python
if __name__ == "__main__":
    mcp.run(transport="sse")
```

**Transport Mode**: HTTP with Server-Sent Events (SSE)

**Server URL**: `http://localhost:8000/mcp/`

**Endpoints**:
- `GET /mcp/` - Establish SSE connection
- `POST /mcp/call_tool` - Invoke MCP tool
- `GET /mcp/list_tools` - List available tools

**Usage**:
```bash
# Start HTTP server
uv run python run_http_server.py

# Server runs on http://localhost:8000/mcp/
```

**Use Cases**:
- Local HTTP validation (Phase 2 testing)
- Cloud deployment testing
- Web-based clients
- Multiple concurrent connections

**Cloud Deployment**:
- Production URL: `https://qdrant-docs.fastmcp.app/mcp`
- Same codebase as local server
- Deployed via FastMCP platform

**Source**: Lines 14-18

---

## Configuration API

### Module: `embedding_config.py`

Centralized embedding model configuration using OpenAI.

**Location**: `scripts/embedding_config.py`

---

### Function: `get_embeddings()`

Initialize OpenAI text-embedding-3-small embeddings.

**Signature**:
```python
def get_embeddings() -> OpenAIEmbeddings
```

**Returns**:
- `OpenAIEmbeddings`: Configured embedding model instance

**Raises**:
- `ValueError`: If `OPENAI_API_KEY` is not set in environment variables

**Configuration**:
- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536
- **API Key**: From `OPENAI_API_KEY` environment variable

**Source**: Lines 15-36

**Example Usage**:
```python
from scripts.embedding_config import get_embeddings

# Initialize embeddings
embeddings = get_embeddings()

# Embed a query
query_vector = embeddings.embed_query("What is a RAG agent?")
print(f"Vector dimension: {len(query_vector)}")  # 1536

# Embed multiple documents
doc_vectors = embeddings.embed_documents([
    "Document 1 text",
    "Document 2 text"
])
```

**Testing**:
```bash
# Test embedding configuration
uv run python scripts/embedding_config.py

# Output:
# Testing embedding configuration...
# Embedding test text: 'This is a test document.'
# ✓ Embedding successful!
#   Vector dimension: 1536
#   First 5 values: [0.123, -0.456, 0.789, ...]
```

**Cost**:
- Model: text-embedding-3-small
- Price: ~$0.02 per 1M tokens
- Monitor at: https://platform.openai.com/usage

---

### Environment Variables

All required environment variables for the MCP server and data pipeline.

**Location**: Define in `.env` file (copy from `.env.example`)

#### Required Variables

**Qdrant Vector Store**:
```bash
QDRANT_API_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here
```
- Get credentials at: https://cloud.qdrant.io/
- Used by: `mcp_server.py`, `upload_to_qdrant.py`, `validate_qdrant.py`

**OpenAI Embeddings**:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```
- Get API key at: https://platform.openai.com/api-keys
- Used by: `mcp_server.py`, `embedding_config.py`, `upload_to_qdrant.py`
- Model: text-embedding-3-small (1536 dimensions)

#### Optional Variables

**OpenAI Model Name** (for other tools):
```bash
MODEL_NAME=gpt-4o-mini
```
- Not used by qdrant-docs MCP server
- For other project components

**Context7 API Key** (optional third-party service):
```bash
CONTEXT7_API_KEY=your-context7-api-key-here
```
- Get API key at: https://context7.com/dashboard
- Not required for qdrant-docs MCP server
- Provides higher rate limits for Context7 MCP server (separate service)

#### Setup Instructions

1. **Copy template**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in values**:
   ```bash
   # Edit .env file with your actual keys
   nano .env
   ```

3. **Add to shell environment** (~/.bashrc or ~/.zshrc):
   ```bash
   export QDRANT_API_URL="your-value"
   export QDRANT_API_KEY="your-value"
   export OPENAI_API_KEY="your-value"
   ```

4. **Reload shell**:
   ```bash
   source ~/.bashrc  # or source ~/.zshrc
   ```

5. **Verify**:
   ```bash
   echo "QDRANT_API_URL: ${QDRANT_API_URL:+SET}"
   echo "QDRANT_API_KEY: ${QDRANT_API_KEY:+SET}"
   echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
   ```

**Security Notes**:
- Never commit `.env` with real keys to version control
- `.env` is in `.gitignore`
- Use environment variables for production deployment
- Keep `.env.example` updated without real values

---

## Data Pipeline API

### Module: `download_llms_raw.py`

Download llms.txt and llms-full.txt files from documentation sources.

**Location**: `scripts/download_llms_raw.py`

---

#### Constants

```python
SOURCES = {
    'LangChain': (
        'https://docs.langchain.com/llms.txt',
        'https://docs.langchain.com/llms-full.txt',
    ),
    'Anthropic': (...),
    'Prefect': (...),
    'FastMCP': (...),
    'McpProtocol': (...),
    'PydanticAI': (...),
    'Zep': (...),
    'Temporal': (...),
    # ... 12 total sources
}

OUTPUT_DIR = Path('data/raw')
```

---

#### Function: `download_file`

Download a single file with error handling.

**Signature**:
```python
async def download_file(
    client: httpx.AsyncClient,
    url: str,
    output_path: Path
) -> dict
```

**Parameters**:
- `client` (httpx.AsyncClient): Async HTTP client
- `url` (str): URL to download
- `output_path` (Path): Local path to save file

**Returns**:
- `dict`: Status dictionary with keys:
  - `status` (str): `"success"` or `"failed"`
  - `size_bytes` (int): File size in bytes
  - `url` (str): Original URL
  - `error` (str, optional): Error message if failed

**Source**: Lines 77-118

**Example Usage**:
```python
import asyncio
import httpx
from pathlib import Path

async def download_example():
    async with httpx.AsyncClient(timeout=60.0) as client:
        result = await download_file(
            client,
            "https://docs.langchain.com/llms-full.txt",
            Path("data/raw/LangChain/llms-full.txt")
        )
        print(result)
        # {'status': 'success', 'size_bytes': 1234567, 'url': '...'}

asyncio.run(download_example())
```

---

#### Function: `download_source`

Download both llms.txt and llms-full.txt for a single source.

**Signature**:
```python
async def download_source(
    client: httpx.AsyncClient,
    name: str,
    urls: tuple[str, str]
) -> dict
```

**Parameters**:
- `client` (httpx.AsyncClient): Async HTTP client
- `name` (str): Source name (e.g., "LangChain")
- `urls` (tuple[str, str]): Tuple of (llms.txt URL, llms-full.txt URL)

**Returns**:
- `dict`: Results dictionary with keys:
  - `llms.txt` (dict): Result from downloading llms.txt
  - `llms-full.txt` (dict): Result from downloading llms-full.txt

**Source**: Lines 121-141

**Algorithm**:
1. Downloads both files concurrently using `asyncio.gather()`
2. Saves to `data/raw/{name}/llms.txt` and `data/raw/{name}/llms-full.txt`
3. Returns status for both files

---

#### Function: `main` (download)

Orchestrate parallel download of all sources.

**Signature**:
```python
async def main() -> int
```

**Returns**:
- `int`: Exit code (0 if all succeed, 1 if any failures)

**Source**: Lines 144-216

**Output Structure**:
```
data/raw/
├── LangChain/
│   ├── llms.txt
│   └── llms-full.txt
├── Anthropic/
│   ├── llms.txt
│   └── llms-full.txt
├── ...
└── manifest.json
```

**Manifest Format** (`data/raw/manifest.json`):
```json
{
  "created_at": "2025-12-18T14:33:41Z",
  "duration_seconds": 12.5,
  "sources": {
    "LangChain": {
      "llms.txt": {"status": "success", "size_bytes": 12345, "url": "..."},
      "llms-full.txt": {"status": "success", "size_bytes": 123456, "url": "..."}
    }
  },
  "summary": {
    "total_sources": 12,
    "llms_txt": {"success": 12, "failed": 0},
    "llms_full_txt": {"success": 12, "failed": 0}
  }
}
```

**Usage**:
```bash
# Download all sources
uv run python scripts/download_llms_raw.py

# Output:
# Downloading from 12 sources to data/raw
#
#   LangChain:
#     ✓ llms.txt: 12.3 KB
#     ✓ llms-full.txt: 456.7 KB
#   ...
#
#   Summary:
#     llms.txt: 12 succeeded, 0 failed
#     llms-full.txt: 12 succeeded, 0 failed
#     Duration: 12.5s
#     Manifest: data/raw/manifest.json
```

**Performance**:
- Downloads all 12 sources concurrently
- Typical duration: 10-20 seconds
- Total downloaded: ~15-20 MB

---

### Module: `split_llms_pages.py`

Split llms-full.txt files into individual page documents using three different strategies.

**Location**: `scripts/split_llms_pages.py`

---

#### Constants

```python
# Sources with URL pattern (5 sources)
SOURCES_WITH_URL = ['LangChain', 'Anthropic', 'Prefect', 'FastMCP', 'McpProtocol']

# Sources with header-only pattern (2 sources)
SOURCES_HEADER_ONLY = ['PydanticAI', 'Zep']

# Sources with multi-level pattern (1 source)
SOURCES_MULTI_LEVEL = ['Temporal']

# Regex patterns
PAGE_PATTERN_WITH_URL = re.compile(r'^# (.+)$\nSource: (https?://[^\n]+)', re.MULTILINE)
PAGE_PATTERN_HEADER_ONLY = re.compile(r'^# (.+)$', re.MULTILINE)
PAGE_PATTERN_MULTI_LEVEL = re.compile(r'^(#{1,2})\s+(.+)$', re.MULTILINE)
```

---

#### Function: `neutralize_code_block_headers`

Convert # headers inside code blocks to ### to avoid false positive matches.

**Signature**:
```python
def neutralize_code_block_headers(content: str) -> str
```

**Parameters**:
- `content` (str): Markdown content with code blocks

**Returns**:
- `str`: Content with headers inside code blocks neutralized

**Purpose**: Prevents Python comments (`# comment`) inside code blocks from being detected as markdown headers.

**Source**: Lines 55-69

**Algorithm**:
1. Find all code blocks using regex: `` ```[\s\S]*?``` ``
2. Replace `^# ` with `^### ` inside each code block
3. Preserves code block content while preventing header matches

**Example**:
```python
content = """
# Real Header
Source: https://example.com

```python
# This is a comment, not a header
x = 1
```
"""

neutralized = neutralize_code_block_headers(content)
# Code block comment now: ### This is a comment, not a header
```

---

#### Function: `split_with_url_pattern`

Split content using `# Title + Source: URL` pattern.

**Signature**:
```python
def split_with_url_pattern(content: str) -> list[dict]
```

**Parameters**:
- `content` (str): Full text content of llms-full.txt

**Returns**:
- `list[dict]`: List of page dictionaries with keys:
  - `title` (str): Page title
  - `source_url` (str): Original documentation URL
  - `content` (str): Page content (markdown)
  - `content_length` (int): Character count

**Source**: Lines 72-96

**Pattern**:
```
# Page Title
Source: https://example.com/page-url

Page content goes here...
```

**Used By**: LangChain, Anthropic, Prefect, FastMCP, McpProtocol (5 sources)

**Example**:
```python
content = """
# Getting Started
Source: https://docs.langchain.com/getting-started

Welcome to LangChain...

# Build a RAG Agent
Source: https://docs.langchain.com/rag-agent

In this tutorial...
"""

pages = split_with_url_pattern(content)
# [
#   {
#     'title': 'Getting Started',
#     'source_url': 'https://docs.langchain.com/getting-started',
#     'content': 'Welcome to LangChain...',
#     'content_length': 123
#   },
#   {
#     'title': 'Build a RAG Agent',
#     'source_url': 'https://docs.langchain.com/rag-agent',
#     'content': 'In this tutorial...',
#     'content_length': 456
#   }
# ]
```

---

#### Function: `split_with_header_pattern`

Split content using `^# Title` pattern, filtering out code block headers.

**Signature**:
```python
def split_with_header_pattern(content: str) -> list[dict]
```

**Parameters**:
- `content` (str): Full text content of llms-full.txt

**Returns**:
- `list[dict]`: List of page dictionaries with keys:
  - `title` (str): Page title
  - `source_url` (None): No URL in this format
  - `content` (str): Page content (markdown)
  - `content_length` (int): Character count

**Source**: Lines 99-133

**Pattern**:
```
# Page Title

Page content goes here...
```

**Used By**: PydanticAI, Zep (2 sources)

**Algorithm**:
1. Neutralizes code block headers to avoid false matches
2. Finds `^# Title` patterns in neutralized content
3. Extracts content between headers
4. Code blocks in output show `###` for comments (neutralized)

**Example**:
```python
content = """
# Introduction

Welcome to the docs...

```python
# This comment won't be detected as a header
def hello():
    pass
```

# API Reference

The API provides...
"""

pages = split_with_header_pattern(content)
# [
#   {
#     'title': 'Introduction',
#     'source_url': None,
#     'content': 'Welcome...\n\n```python\n### This comment...',
#     'content_length': 123
#   },
#   {
#     'title': 'API Reference',
#     'source_url': None,
#     'content': 'The API provides...',
#     'content_length': 456
#   }
# ]
```

---

#### Function: `split_with_multi_level_pattern`

Split content using multiple header levels (# and ##), tracking parent-child hierarchy.

**Signature**:
```python
def split_with_multi_level_pattern(
    content: str,
    levels: tuple = (1, 2)
) -> list[dict]
```

**Parameters**:
- `content` (str): Full text content of llms-full.txt
- `levels` (tuple): Header levels to split on (default: (1, 2) for # and ##)

**Returns**:
- `list[dict]`: List of page dictionaries with keys:
  - `title` (str): Page title
  - `header_level` (int): Header level (1 or 2)
  - `section_path` (str): Hierarchical path (e.g., "Parent > Child")
  - `parent_title` (str or None): Parent section title
  - `parent_index` (int or None): Parent section index
  - `source_url` (None): No URL in this format
  - `content` (str): Page content (markdown)
  - `content_length` (int): Character count

**Source**: Lines 136-207

**Pattern**:
```
# Level 1 Section

Level 1 content...

## Level 2 Subsection

Level 2 content...
```

**Used By**: Temporal (1 source)

**Hierarchy Tracking**:
- Level 1 headers (`#`) are top-level sections (no parent)
- Level 2 headers (`##`) are children of the most recent Level 1
- `section_path` shows full hierarchy (e.g., "Getting Started > Installation")

**Example**:
```python
content = """
# Getting Started

Welcome to Temporal...

## Installation

To install Temporal...

## Configuration

Configure your settings...

# Advanced Topics

Deep dive into...
"""

pages = split_with_multi_level_pattern(content)
# [
#   {
#     'title': 'Getting Started',
#     'header_level': 1,
#     'section_path': 'Getting Started',
#     'parent_title': None,
#     'parent_index': None,
#     'source_url': None,
#     'content': 'Welcome to Temporal...',
#     'content_length': 123
#   },
#   {
#     'title': 'Installation',
#     'header_level': 2,
#     'section_path': 'Getting Started > Installation',
#     'parent_title': 'Getting Started',
#     'parent_index': 0,
#     'source_url': None,
#     'content': 'To install Temporal...',
#     'content_length': 456
#   },
#   ...
# ]
```

---

#### Function: `process_source`

Process a single source's llms-full.txt file.

**Signature**:
```python
def process_source(
    source_name: str,
    use_header_only: bool = False,
    use_multi_level: bool = False
) -> dict
```

**Parameters**:
- `source_name` (str): Source directory name (e.g., "LangChain")
- `use_header_only` (bool): If True, use header-only pattern
- `use_multi_level` (bool): If True, use multi-level header pattern

**Returns**:
- `dict`: Processing result with keys:
  - `status` (str): `"success"`, `"failed"`, or `"skipped"`
  - `page_count` (int): Number of pages extracted
  - `avg_size_chars` (float): Average page size in characters
  - `output_dir` (str): Output directory path
  - `error` (str, optional): Error message if failed

**Source**: Lines 210-296

**Output Structure**:
```
data/interim/pages/{source}/
├── 0000_Page_Title.json
├── 0001_Another_Page.json
├── ...
└── manifest.json
```

**Page JSON Format**:
```json
{
  "title": "Getting Started",
  "source_url": "https://docs.example.com/getting-started",
  "content": "Full markdown content...",
  "content_length": 1234,
  "header_level": 1,
  "section_path": "Getting Started",
  "parent_title": null,
  "parent_index": null
}
```

**Manifest JSON Format** (`{source}/manifest.json`):
```json
{
  "source": "LangChain",
  "input_file": "data/raw/LangChain/llms-full.txt",
  "pattern_type": "with_url",
  "page_count": 506,
  "total_content_chars": 1234567,
  "avg_page_size": 2441.0,
  "pages": [
    {
      "index": 0,
      "title": "Getting Started",
      "header_level": null,
      "section_path": null,
      "parent_title": null,
      "parent_index": null,
      "source_url": "https://docs.langchain.com/getting-started",
      "content_length": 1234
    }
  ]
}
```

---

#### Function: `main` (split)

Process all sources and split into pages.

**Signature**:
```python
def main() -> None
```

**Source**: Lines 299-369

**Usage**:
```bash
# Split all sources into pages
uv run python scripts/split_llms_pages.py

# Output:
# Splitting llms-full.txt files into pages
# Raw directory: data/raw
# Output directory: data/interim/pages
#
# === Sources with Source: URL pattern ===
# Processing LangChain... ✓ 506 pages (2441 chars avg)
# Processing Anthropic... ✓ 932 pages (1876 chars avg)
# ...
#
# === Sources with header-only pattern ===
# Processing PydanticAI... ✓ 127 pages (3210 chars avg)
# Processing Zep... ✓ 119 pages (2987 chars avg)
#
# === Sources with multi-level header pattern (# and ##) ===
# Processing Temporal... ✓ 2299 pages (1543 chars avg)
#
# Summary: 4969 total pages from 8 sources
# Manifest: data/interim/pages/manifest.json
```

**Overall Manifest** (`data/interim/pages/manifest.json`):
```json
{
  "sources_processed": 8,
  "total_pages": 4969,
  "results": {
    "LangChain": {
      "status": "success",
      "page_count": 506,
      "avg_size_chars": 2441.0,
      "output_dir": "data/interim/pages/LangChain"
    }
  }
}
```

---

### Module: `upload_to_qdrant.py`

Load JSON documents, generate embeddings, and upload to Qdrant Cloud.

**Location**: `scripts/upload_to_qdrant.py`

---

#### Constants

```python
COLLECTION_NAME = "llms-full-silver"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100        # Documents per batch
MAX_WORKERS = 4         # Parallel workers
DATA_DIR = Path("data")
PAGES_DIR = DATA_DIR / "interim" / "pages"
PROCESSED_DIR = DATA_DIR / "processed"
```

---

#### Function: `init_qdrant_client`

Initialize Qdrant client with credentials from environment.

**Signature**:
```python
def init_qdrant_client() -> QdrantClient
```

**Returns**:
- `QdrantClient`: Configured Qdrant client with gRPC enabled

**Raises**:
- `ValueError`: If `QDRANT_API_URL` or `QDRANT_API_KEY` not set

**Configuration**:
- gRPC: Enabled for better performance
- Timeout: Default (60s)

**Source**: Lines 40-63

**Example Usage**:
```python
from scripts.upload_to_qdrant import init_qdrant_client

client = init_qdrant_client()
collection_info = client.get_collection("llms-full-silver")
print(f"Points: {collection_info.points_count}")
```

---

#### Function: `create_collection`

Create Qdrant collection if it doesn't exist.

**Signature**:
```python
def create_collection(client: QdrantClient, collection_name: str) -> None
```

**Parameters**:
- `client` (QdrantClient): Qdrant client instance
- `collection_name` (str): Name of collection to create

**Configuration**:
- **Vector Size**: 1536 (matches text-embedding-3-small)
- **Distance Metric**: COSINE
- **On-Disk Storage**: Enabled (saves RAM)
- **Payload On-Disk**: Enabled (saves RAM)
- **Indexing Threshold**: 10,000 points

**Source**: Lines 66-92

**Example Usage**:
```python
from scripts.upload_to_qdrant import init_qdrant_client, create_collection

client = init_qdrant_client()
create_collection(client, "llms-full-silver")
# ✓ Collection 'llms-full-silver' created successfully
```

**Cost Optimization**:
- `on_disk=True`: Stores vectors on disk instead of RAM
- `on_disk_payload=True`: Stores metadata on disk
- Reduces RAM costs by ~60% on Qdrant Cloud

---

#### Function: `load_documents`

Load all JSON files and convert to LangChain Documents with manifest metadata.

**Signature**:
```python
def load_documents(
    pages_dir: Path,
    source_filter: Optional[List[str]] = None,
) -> List[Document]
```

**Parameters**:
- `pages_dir` (Path): Path to `data/interim/pages/` directory
- `source_filter` (list[str], optional): Filter to specific sources
  - Example: `["LangChain", "Anthropic"]`
  - Default: `None` (load all sources)

**Returns**:
- `list[Document]`: LangChain Document objects with rich metadata

**Metadata Fields** (from JSON files):
- `title` (str): Page title
- `source_url` (str or None): Original documentation URL
- `content_length` (int): Character count
- `header_level` (int or None): Header level (1 or 2) for multi-level sources
- `section_path` (str or None): Hierarchical path (e.g., "Parent > Child")
- `parent_title` (str or None): Parent section title
- `parent_index` (int or None): Parent section index

**Metadata Fields** (from manifest):
- `source_name` (str): Source name (e.g., "LangChain")
- `total_pages` (int): Total pages in source
- `avg_content_length` (float): Average page size in source

**Generated Metadata**:
- `doc_id` (str): Unique ID in format `{source}_{page_num}` (e.g., "LangChain_0042")
- `page_number` (str): Page number extracted from filename

**Source**: Lines 94-176

**Example Usage**:
```python
from pathlib import Path
from scripts.upload_to_qdrant import load_documents

# Load all sources
docs = load_documents(Path("data/interim/pages"))
print(f"Loaded {len(docs)} documents")

# Load specific sources only
docs = load_documents(
    Path("data/interim/pages"),
    source_filter=["LangChain", "Anthropic"]
)
print(f"Loaded {len(docs)} documents from 2 sources")

# Inspect document
doc = docs[0]
print(f"Title: {doc.metadata['title']}")
print(f"Source: {doc.metadata['source_name']}")
print(f"URL: {doc.metadata['source_url']}")
print(f"Content: {doc.page_content[:200]}...")
```

---

#### Function: `upload_batch`

Upload a single batch of documents to Qdrant.

**Signature**:
```python
def upload_batch(
    batch: List[Document],
    vector_store: QdrantVectorStore,
    batch_idx: int,
) -> List[str]
```

**Parameters**:
- `batch` (list[Document]): List of documents to upload
- `vector_store` (QdrantVectorStore): Vector store instance
- `batch_idx` (int): Batch index (for logging)

**Returns**:
- `list[str]`: List of document IDs that were uploaded

**Raises**:
- Exceptions are propagated to caller for error handling

**Source**: Lines 179-200

**Algorithm**:
1. Calls `vector_store.add_documents()`
2. LangChain internally:
   - Generates embeddings via OpenAI API
   - Uploads vectors + metadata to Qdrant
3. Returns list of assigned document IDs

---

#### Function: `upload_documents`

Upload documents in batches with parallel processing.

**Signature**:
```python
def upload_documents(
    documents: List[Document],
    embeddings,
    client: QdrantClient,
    collection_name: str,
    batch_size: int = BATCH_SIZE,
    max_workers: int = MAX_WORKERS,
    dry_run: bool = False,
) -> List[str]
```

**Parameters**:
- `documents` (list[Document]): Documents to upload
- `embeddings` (OpenAIEmbeddings): Embedding model instance
- `client` (QdrantClient): Qdrant client instance
- `collection_name` (str): Collection name
- `batch_size` (int): Documents per batch (default: 100)
- `max_workers` (int): Parallel workers (default: 4)
- `dry_run` (bool): If True, skip actual upload (default: False)

**Returns**:
- `list[str]`: List of uploaded document IDs (empty if dry_run)

**Source**: Lines 203-277

**Algorithm**:
1. Splits documents into batches of size `batch_size`
2. Creates `ThreadPoolExecutor` with `max_workers` threads
3. Submits all batches for parallel upload
4. Displays progress with `tqdm` progress bar
5. Collects results and reports failures

**Performance**:
- **Batch Size**: 100 docs balances throughput and error recovery
- **Workers**: 4 parallel threads maximize throughput without overwhelming APIs
- **Throughput**: ~400 docs/minute (rate limited by OpenAI)
- **Total Time**: 12-15 minutes for 4,969 documents

**Example Usage**:
```python
from scripts.upload_to_qdrant import (
    init_qdrant_client,
    load_documents,
    upload_documents
)
from scripts.embedding_config import get_embeddings
from pathlib import Path

# Initialize
client = init_qdrant_client()
embeddings = get_embeddings()
docs = load_documents(Path("data/interim/pages"))

# Upload with custom settings
uploaded_ids = upload_documents(
    documents=docs,
    embeddings=embeddings,
    client=client,
    collection_name="llms-full-silver",
    batch_size=50,   # Smaller batches
    max_workers=2,   # Fewer workers
    dry_run=False
)

print(f"Uploaded {len(uploaded_ids)} documents")
```

**Dry Run Mode**:
```python
# Validate without uploading
upload_documents(
    documents=docs,
    embeddings=embeddings,
    client=client,
    collection_name="llms-full-silver",
    dry_run=True
)
# [DRY RUN] Would upload 4969 documents to 'llms-full-silver'
# [DRY RUN] Batch size: 100, Workers: 4
```

---

#### Function: `save_upload_manifest`

Save upload metadata for tracking.

**Signature**:
```python
def save_upload_manifest(
    output_path: Path,
    uploaded_count: int,
    total_count: int,
    collection_name: str,
    sources: List[str],
) -> None
```

**Parameters**:
- `output_path` (Path): Path to save manifest JSON
- `uploaded_count` (int): Number of documents successfully uploaded
- `total_count` (int): Total number of documents attempted
- `collection_name` (str): Qdrant collection name
- `sources` (list[str]): Source names that were uploaded

**Output**: JSON file at `output_path`

**Source**: Lines 280-311

**Manifest Format**:
```json
{
  "upload_timestamp": "2025-12-18T14:33:41.123456",
  "collection_name": "llms-full-silver",
  "documents_uploaded": 4969,
  "documents_total": 4969,
  "sources": ["LangChain", "Anthropic", "Prefect", ...],
  "embedding_model": "text-embedding-3-small",
  "embedding_dimension": 1536
}
```

---

#### CLI Usage

**Command**:
```bash
uv run python scripts/upload_to_qdrant.py [OPTIONS]
```

**Options**:
- `--sources SOURCE [SOURCE ...]`: Filter to specific sources
  - Example: `--sources LangChain Anthropic`
- `--batch-size INT`: Documents per batch (default: 100)
- `--workers INT`: Parallel workers (default: 4)
- `--dry-run`: Validate configuration without uploading
- `--collection STR`: Collection name (default: "llms-full-silver")

**Source**: Lines 314-345

**Examples**:

**Upload all sources**:
```bash
uv run python scripts/upload_to_qdrant.py
```

**Upload specific sources only**:
```bash
uv run python scripts/upload_to_qdrant.py --sources LangChain Anthropic
```

**Dry run (validate without uploading)**:
```bash
uv run python scripts/upload_to_qdrant.py --dry-run
```

**Custom batch size and workers**:
```bash
uv run python scripts/upload_to_qdrant.py --batch-size 50 --workers 2
```

**Custom collection name**:
```bash
uv run python scripts/upload_to_qdrant.py --collection my-custom-collection
```

**Output Example**:
```
======================================================================
Qdrant Documentation Upload
======================================================================

Initializing clients...
✓ Clients initialized
✓ Collection 'llms-full-silver' already exists

Loading documents from data/interim/pages...
  Loading 506 documents from LangChain...
  Loading 932 documents from Anthropic...
  ...

✓ Loaded 4969 documents from 8 sources:
  - Anthropic: 932 documents
  - FastMCP: 175 documents
  - LangChain: 506 documents
  ...

Uploading 4969 documents in 50 batches...
Batch size: 100, Parallel workers: 4
Uploading: 100%|████████████████████████| 4969/4969 [12:34<00:00, 6.59docs/s]

✓ Upload complete!
  Successful: 4969 documents

✓ Upload manifest saved to data/processed/upload_manifest.json

======================================================================
Upload Complete!
======================================================================
```

---

### Module: `validate_qdrant.py`

Comprehensive validation of Qdrant collection after upload.

**Location**: `scripts/validate_qdrant.py`

---

#### Constants

```python
COLLECTION_NAME = "llms-full-silver"
EXPECTED_TOTAL = 2670  # Update based on actual upload
EXPECTED_SOURCES = {
    "Anthropic": 932,
    "LangChain": 506,
    "Prefect": 767,
    "FastMCP": 175,
    "McpProtocol": 44,
    "PydanticAI": 127,
    "Zep": 119,
    # Add "Temporal": 2299 if included
}
```

Note: Constants may need updating based on actual sources uploaded.

---

#### Function: `init_clients`

Initialize Qdrant client, embeddings, and vector store.

**Signature**:
```python
def init_clients() -> tuple[QdrantClient, OpenAIEmbeddings, QdrantVectorStore]
```

**Returns**:
- `tuple`: (client, embeddings, vector_store)

**Source**: Lines 43-63

---

#### Function: `validate_collection_info`

Validate collection configuration and basic info.

**Signature**:
```python
def validate_collection_info(client: QdrantClient) -> bool
```

**Parameters**:
- `client` (QdrantClient): Qdrant client instance

**Returns**:
- `bool`: True if all checks pass, False otherwise

**Checks**:
- Collection status is "green"
- Vector dimension is 1536
- Distance metric is COSINE
- Total point count matches expected

**Source**: Lines 66-117

**Example Output**:
```
======================================================================
1. Collection Configuration
======================================================================
Collection name: llms-full-silver
Status: green
Vector dimension: 1536
Distance metric: COSINE
Total points: 2,670

Configuration checks:
  ✓ Status is green
  ✓ Vector dimension is 1536
  ✓ Distance metric is COSINE
  ✓ Total points is 2670
```

---

#### Function: `validate_document_counts`

Validate document counts by source.

**Signature**:
```python
def validate_document_counts(client: QdrantClient) -> bool
```

**Parameters**:
- `client` (QdrantClient): Qdrant client instance

**Returns**:
- `bool`: True if all counts match expected, False otherwise

**Algorithm**:
1. Uses `scroll()` API to iterate through all documents
2. Counts documents per source by reading `metadata.source_name`
3. Compares against expected counts

**Source**: Lines 120-184

**Example Output**:
```
======================================================================
2. Document Counts by Source
======================================================================
Scanning all documents...

Total documents scanned: 2,670

Source          Expected   Actual     Status
--------------------------------------------------
Anthropic       932        932        ✓
FastMCP         175        175        ✓
LangChain       506        506        ✓
McpProtocol     44         44         ✓
Prefect         767        767        ✓
PydanticAI      127        127        ✓
Zep             119        119        ✓
--------------------------------------------------
TOTAL           2670       2670       ✓
```

---

#### Function: `validate_metadata_structure`

Validate metadata structure of sample documents.

**Signature**:
```python
def validate_metadata_structure(client: QdrantClient) -> bool
```

**Parameters**:
- `client` (QdrantClient): Qdrant client instance

**Returns**:
- `bool`: True if all required fields present, False otherwise

**Required Metadata Fields**:
- `title`
- `source_url`
- `content_length`
- `source_name`
- `total_pages`
- `avg_content_length`
- `doc_id`
- `page_number`

**Source**: Lines 191-256

**Example Output**:
```
======================================================================
3. Metadata Structure Validation
======================================================================
Checking metadata structure of 5 sample documents...

Document 1 (ID: abc123):
  Source: LangChain
  Title: Build a RAG Agent
  Doc ID: LangChain_0042
  ✓ All required metadata fields present
  ✓ Has page_content (3245 chars)

...
```

---

#### Function: `test_semantic_search`

Test semantic search with sample queries.

**Signature**:
```python
def test_semantic_search(vector_store: QdrantVectorStore) -> bool
```

**Parameters**:
- `vector_store` (QdrantVectorStore): Vector store instance

**Returns**:
- `bool`: True if all test queries return expected sources, False otherwise

**Test Queries**:
1. "How do I build a RAG agent with LangChain?" → expects LangChain
2. "What are Claude's API features and capabilities?" → expects Anthropic
3. "How does Prefect handle workflow orchestration?" → expects Prefect
4. "Explain MCP server implementation" → expects FastMCP, McpProtocol, or Anthropic

**Source**: Lines 259-330

**Example Output**:
```
======================================================================
4. Semantic Search Tests
======================================================================

Test 1: How do I build a RAG agent with LangChain?
----------------------------------------------------------------------
✓ Retrieved 3 results

✓ Found expected source(s): ['LangChain']

  Result 1:
    Title: Build a Retrieval Agent
    Source: LangChain
    URL: https://python.langchain.com/docs/tutorials/agents
    Preview: In this tutorial we will build an agent that can answer...

...
```

---

#### Function: `test_filtered_search`

Test semantic search with metadata filtering (optional feature).

**Signature**:
```python
def test_filtered_search(vector_store: QdrantVectorStore) -> bool
```

**Parameters**:
- `vector_store` (QdrantVectorStore): Vector store instance

**Returns**:
- `bool`: Always returns True (optional feature, doesn't fail validation)

**Note**: Requires creating a payload index on `metadata.source_name` field for optimal performance. Falls back to Python-side filtering if index doesn't exist.

**Source**: Lines 333-427

**Example Output (with index)**:
```
======================================================================
5. Filtered Search Tests (Optional Feature)
======================================================================

Test 1: Search only Anthropic docs
Query: 'API authentication'
Expected source: Anthropic
----------------------------------------------------------------------
✓ Retrieved 3 results
✓ All results are from Anthropic

...
```

**Example Output (without index)**:
```
Test 1: Search only Anthropic docs
Query: 'API authentication'
Expected source: Anthropic
----------------------------------------------------------------------
ℹ  Filtered search requires creating an index on metadata fields
   This is optional. To enable, create a payload index:
   client.create_payload_index('llms-full-silver', 'metadata.source_name')

Note: Filtered search is optional. Basic semantic search is fully functional.
```

---

#### CLI Usage

**Command**:
```bash
uv run python scripts/validate_qdrant.py
```

**Exit Codes**:
- `0`: All validation tests passed
- `1`: Some validation tests failed or fatal error

**Source**: Lines 430-481

**Example Output**:
```
======================================================================
Qdrant Collection Validation
======================================================================
Collection: llms-full-silver
Expected documents: 2,670

Initializing clients...
✓ Clients initialized

[Run all validation tests...]

======================================================================
Validation Summary
======================================================================
Collection Info           ✓ PASSED
Document Counts           ✓ PASSED
Metadata Structure        ✓ PASSED
Semantic Search           ✓ PASSED
Filtered Search           ✓ PASSED
======================================================================

✓ All validation tests passed!

Your Qdrant collection 'llms-full-silver' is ready for production use.
```

---

## Usage Patterns

### Basic Search

Search documentation with natural language queries.

**Via Python** (for testing):
```python
from mcp_server import search_docs

# Simple search
results = search_docs("How do I authenticate with the API?")
print(results)

# Search with more results
results = search_docs("RAG agent tutorial", k=10)

# Filtered search
results = search_docs("prompt caching", source="Anthropic")
```

**Via MCP Protocol** (Claude Code):
```json
{
  "jsonrpc": "2.0",
  "method": "call_tool",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "How do I authenticate with the API?",
      "k": 5
    }
  },
  "id": 1
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": "Found 5 results for: 'How do I authenticate with the API?'\n\n...",
  "id": 1
}
```

---

### Filtered Search

Search within a specific documentation source.

**Python**:
```python
from mcp_server import search_docs

# Search only Anthropic docs
results = search_docs(
    query="prompt caching strategies",
    k=5,
    source="Anthropic"
)

# Search only LangChain docs
results = search_docs(
    query="build a RAG agent",
    k=3,
    source="LangChain"
)
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
      "k": 5
    }
  }
}
```

---

### List Available Sources

Discover which documentation sources are available for search.

**Python**:
```python
from mcp_server import list_sources

# Get list of all sources with counts
sources_table = list_sources()
print(sources_table)
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
...
------------------------------
TOTAL           4969

Use the 'source' parameter in search_docs() to filter by a specific source.
Example: search_docs('authentication', source='Anthropic')
```

---

### Running the Server

**stdio Transport** (for Claude Code desktop):
```bash
# Start MCP server with stdio transport
uv run python mcp_server.py

# Server listens on stdin/stdout for JSON-RPC messages
# Configure in Claude Code's MCP settings
```

**HTTP/SSE Transport** (for local testing or cloud deployment):
```bash
# Start HTTP server
uv run python run_http_server.py

# Server runs on http://localhost:8000/mcp/
# Connect via HTTP POST to /mcp/call_tool
```

**Cloud Deployment**:
- Production URL: `https://qdrant-docs.fastmcp.app/mcp`
- Same codebase as local server
- Deployed via FastMCP platform

---

### Data Pipeline Workflow

Complete workflow to refresh documentation data.

**Step 1: Download Raw Documentation**:
```bash
uv run python scripts/download_llms_raw.py

# Downloads to data/raw/{source}/llms-full.txt
```

**Step 2: Parse into Pages**:
```bash
uv run python scripts/split_llms_pages.py

# Splits to data/interim/pages/{source}/XXXX_Title.json
```

**Step 3: Upload to Qdrant**:
```bash
# Upload all sources
uv run python scripts/upload_to_qdrant.py

# Or upload specific sources only
uv run python scripts/upload_to_qdrant.py --sources LangChain Anthropic

# Or dry run to validate
uv run python scripts/upload_to_qdrant.py --dry-run
```

**Step 4: Validate Collection**:
```bash
uv run python scripts/validate_qdrant.py

# Exit code 0 if all tests pass
# Exit code 1 if any tests fail
```

---

### Testing

**In-Memory Tests** (80% coverage, fastest):
```bash
# Run all in-memory tests
uv run pytest tests/test_mcp_server.py -v

# Run specific test
uv run pytest tests/test_mcp_server.py::test_search_docs_basic -v
```

**HTTP Tests** (15% coverage, requires server running):
```bash
# Terminal 1: Start HTTP server
uv run python run_http_server.py

# Terminal 2: Run HTTP tests
uv run python test_http_local.py
```

**Cloud Tests** (5% coverage, requires cloud deployment):
```bash
# Test cloud deployment
uv run python test_cloud_deployment.py
```

---

## Best Practices

### Query Design

**Good Queries**:
- Natural language: `"How do I build a RAG agent?"`
- Specific questions: `"What are Claude's prompt caching strategies?"`
- Technical terms: `"Prefect workflow scheduling"`

**Avoid**:
- Single words: `"authentication"` (too broad)
- Overly long queries (>100 words)
- Non-English queries (embeddings trained on English)

### Source Filtering

**When to Use**:
- You know which documentation to search
- Narrowing results for specific framework
- Reducing response time

**Example**:
```python
# Good: Specific source
search_docs("API authentication", source="Anthropic")

# Good: Broader search across all sources
search_docs("API authentication")  # No source filter
```

### K Parameter

**Guidelines**:
- Default `k=5`: Good balance for most queries
- `k=3`: When you want concise results
- `k=10-20`: When exploring a topic broadly
- Automatically clamped to range [1, 20]

**Example**:
```python
# Concise results
search_docs("quick start guide", k=3)

# Comprehensive exploration
search_docs("agent architecture patterns", k=15)
```

### Error Handling

**Always handle potential errors**:

```python
try:
    results = search_docs("my query")
    if results.startswith("Error during search:"):
        print("Search failed, check logs")
    elif results.startswith("No results found"):
        print("Try a different query")
    else:
        print(results)
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Performance Optimization

**Tips**:
- **Batch Queries**: If possible, group related queries
- **Cache Results**: Common queries can be cached client-side
- **Filter Early**: Use `source` parameter to reduce search space
- **Appropriate K**: Don't request more results than needed

### Data Pipeline

**Best Practices**:
- **Validate First**: Run with `--dry-run` before actual upload
- **Incremental Updates**: Use `--sources` to update specific sources
- **Monitor Costs**: Check OpenAI usage after uploads
- **Test After Upload**: Always run `validate_qdrant.py`

**Example Workflow**:
```bash
# 1. Dry run first
uv run python scripts/upload_to_qdrant.py --dry-run

# 2. Upload incrementally
uv run python scripts/upload_to_qdrant.py --sources Temporal

# 3. Validate
uv run python scripts/validate_qdrant.py

# 4. Check costs
# Visit https://platform.openai.com/usage
```

---

## Error Handling

### MCP Server Errors

**Connection Errors**:
```python
# Error: QDRANT_API_URL or QDRANT_API_KEY not set
# Solution: Check .env file and environment variables
```

**Search Errors**:
```python
# Error: "Index required for filtering"
# Reason: Payload index not created for source_name field
# Solution: Falls back to Python-side filtering automatically
# Optional: Create index for better performance
```

**Empty Results**:
```python
# Response: "No results found for query: 'xyz'"
# Reason: Query didn't match any documents
# Solution: Try broader query or different keywords
```

### Data Pipeline Errors

**Download Errors**:
```python
# Error: HTTP 404 or connection timeout
# Reason: Source URL changed or site down
# Solution: Update SOURCES dict with new URL or skip source
```

**Parsing Errors**:
```python
# Error: "No pages found - check regex pattern"
# Reason: Document format changed
# Solution: Update regex pattern or add new splitting strategy
```

**Upload Errors**:
```python
# Error: "Rate limit exceeded"
# Reason: OpenAI API rate limits
# Solution: Reduce --workers or --batch-size
```

**Validation Errors**:
```python
# Error: Document count mismatch
# Reason: Upload partially failed or data changed
# Solution: Re-run upload or update EXPECTED_SOURCES
```

### Common Error Types

**ValueError**:
- Missing environment variables
- Invalid configuration parameters

**HTTPStatusError**:
- Failed HTTP requests (download)
- Qdrant API errors

**ConnectionError**:
- Cannot connect to Qdrant Cloud
- Network issues

**AuthenticationError**:
- Invalid API keys
- Expired credentials

---

## Performance Characteristics

### Query Performance

**Latency Breakdown**:
- OpenAI embedding: ~200-500ms
- Qdrant search: ~100-300ms
- Network latency: ~50-200ms (local) or ~100-500ms (cloud)
- Result formatting: ~1ms

**Total Latency**:
- Target: < 10s (includes all network calls)
- Average HTTP: ~2.4s
- In-memory tests: ~1-3s (mock network)

**Throughput**:
- Sequential queries: ~2-5 queries/second
- Concurrent queries (HTTP): Limited by OpenAI rate limits

### Upload Performance

**Batch Upload**:
- Batch size: 100 documents
- Parallel workers: 4
- Throughput: ~400 docs/minute (rate limited by OpenAI)

**Total Upload Time**:
- 4,969 documents: 12-15 minutes
- Bottleneck: OpenAI embedding API (~10 min)
- Qdrant upload: ~2-3 minutes (batched, parallel)

**Cost Optimization**:
- On-disk storage: Reduces Qdrant RAM costs by ~60%
- Batch embeddings: Reduces API overhead

### Validation Performance

**Collection Info**: ~100-200ms
**Document Counts**: ~1-3s (4,969 documents)
**Metadata Structure**: ~100-200ms
**Semantic Search Tests**: ~2-5s (4 queries)
**Total Validation**: ~5-10s

---

## Dependencies

### Core Dependencies

```toml
[dependencies]
datasets = ">=4.4.1"
langchain = ">=1.1.0"
langchain-community = ">=0.4.1"
langchain-qdrant = ">=1.1.0"
langchain-openai = ">=1.1.0"
python-dotenv = ">=1.0.0"
tqdm = ">=4.67.1"
fastmcp = ">=0.7.0"
```

### Development Dependencies

```toml
[dev-dependencies]
pytest = ">=9.0.1"
pytest-asyncio = ">=1.3.0"
```

### External Services

**Qdrant Cloud**:
- Vector database service
- Free tier available
- Monitor at: https://cloud.qdrant.io/

**OpenAI API**:
- Embedding model: text-embedding-3-small
- Cost: ~$0.02 per 1M tokens
- Monitor at: https://platform.openai.com/usage

---

## Changelog

### Version 0.1.0 (Current)

**Features**:
- MCP server with 2 tools: `search_docs`, `list_sources`
- Support for 8 documentation sources (4,969+ pages)
- Semantic search via Qdrant + OpenAI embeddings
- Multi-level hierarchy support (Temporal)
- stdio and HTTP/SSE transport modes
- Complete data pipeline (download → parse → upload → validate)

**Data Pipeline**:
- 3 parsing strategies for different documentation formats
- Batch upload with parallel processing
- Comprehensive validation suite

**Testing**:
- 24 total tests (11 in-memory + 7 HTTP + 6 cloud)
- 80% in-memory, 15% HTTP, 5% cloud coverage

---

## Notes

### Design Decisions

**Why No Chunking?**:
- Full page content preserved for better context
- Embeddings capture entire page semantics
- Users get complete, coherent pages in results

**Why 3 Parsing Strategies?**:
- Different documentation sites use different formats
- URL pattern for sites with source URLs
- Header-only for sites without URLs
- Multi-level for hierarchical documentation (Temporal)

**Why Batch Upload?**:
- Balances throughput and error recovery
- 100 docs/batch is optimal for rate limits
- Parallel workers maximize throughput

**Why On-Disk Storage?**:
- Reduces Qdrant Cloud RAM costs by ~60%
- Acceptable performance trade-off for this use case
- Collection size manageable (~30MB vectors)

### Limitations

**Current Limitations**:
- **No Streaming**: Results returned all at once (not streamed)
- **No Caching**: Repeated queries always hit vector store
- **No Connection Pooling**: New clients created per request
- **No Authentication**: MCP server assumes trusted clients
- **English Only**: Embeddings optimized for English text

**Future Enhancements**:
- Add more documentation sources
- Implement result streaming
- Add query result caching
- Connection pooling for better performance
- Multi-language support

---

**Document Version**: 1.0
**Last Updated**: 2025-12-18
**Author**: Technical Documentation Expert (Claude Opus 4.5)
