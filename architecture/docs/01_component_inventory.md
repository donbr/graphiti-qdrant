# Component Inventory

**Project**: graphiti-qdrant
**Description**: Semantic documentation search via Qdrant vector store and FastMCP server
**Generated**: 2025-12-18

## Overview

This codebase implements a custom MCP (Model Context Protocol) server that provides semantic search over 4,969+ documentation pages from 8 sources using Qdrant vector store and OpenAI embeddings.

**Architecture Pattern**: MCP Server with Data Pipeline
**Transport Modes**: stdio (local), HTTP/SSE (cloud)
**Key Technologies**: FastMCP 2.0, LangChain, Qdrant Cloud, OpenAI embeddings

---

## Public API

### MCP Server Interface

#### **mcp_server.py** (Main Public Interface)
*Location*: `mcp_server.py`

**Purpose**: Primary MCP server exposing semantic search tools for Claude Code integration.

**Public Tools** (Lines 73-226):

1. **`search_docs(query: str, k: int = 5, source: Optional[str] = None) -> str`** (Lines 73-166)
   - **Description**: Semantic search over documentation using natural language queries
   - **Parameters**:
     - `query`: Natural language search query (e.g., "How do I build a RAG agent?")
     - `k`: Number of results to return (default: 5, clamped between 1-20)
     - `source`: Optional filter by source name (e.g., "LangChain", "Anthropic")
   - **Returns**: Formatted search results with titles, sources, URLs, content previews
   - **Features**:
     - Automatic k parameter validation (Lines 90)
     - Fallback filtering if payload index missing (Lines 113-125)
     - Content preview truncation (1000 chars) (Lines 156-159)
     - Hierarchy metadata support for multi-level sources (Lines 144-149)
   - **Error Handling**: Returns error message string on failure (Lines 165-166)

2. **`list_sources() -> str`** (Lines 169-226)
   - **Description**: List all available documentation sources with document counts
   - **Parameters**: None
   - **Returns**: Formatted table of sources with document counts
   - **Implementation**: Uses Qdrant scroll API to count documents by source (Lines 188-205)
   - **Features**: Includes usage examples in output (Lines 218-221)
   - **Error Handling**: Returns error message string on failure (Lines 225-226)

**Helper Function**:

3. **`get_vector_store() -> QdrantVectorStore`** (Lines 29-70)
   - **Purpose**: Initialize and return configured Qdrant vector store
   - **Environment Variables Required**:
     - `QDRANT_API_URL` (Line 39)
     - `QDRANT_API_KEY` (Line 40)
     - `OPENAI_API_KEY` (Line 41)
   - **Configuration**:
     - Collection: "llms-full-silver" (Line 25)
     - Embeddings: text-embedding-3-small, 1536 dimensions (Lines 59-63)
     - gRPC preferred for performance (Line 55)
   - **Error Handling**: Raises ValueError if env vars missing (Lines 43-49)

**Constants** (Lines 24-26):
- `COLLECTION_NAME = "llms-full-silver"`
- `DEFAULT_K = 5`

**Entry Point** (Lines 229-231):
- Command: `mcp.run()` - Runs FastMCP server with stdio transport by default

---

### HTTP Server Runner

#### **run_http_server.py** (HTTP Transport Entry Point)
*Location*: `run_http_server.py`

**Purpose**: Run MCP server with HTTP/SSE transport for local testing and cloud deployment.

**Entry Point** (Lines 16-18):
- **Command**: `mcp.run(transport="sse")`
- **URL**: http://localhost:8000/mcp/
- **Use Case**: Local HTTP validation, cloud deployment testing

---

### Simple Entry Point

#### **main.py** (Minimal Example)
*Location*: `main.py`

**Purpose**: Simple hello-world entry point (likely placeholder for future CLI).

**Function** (Lines 1-6):
- `main()`: Prints "Hello from graphiti-qdrant!"
- **Note**: Not actively used in production

---

## Internal Implementation

### Data Pipeline Components

#### **scripts/download_llms_raw.py** (Data Acquisition)
*Location*: `scripts/download_llms_raw.py`

**Purpose**: Download llms.txt and llms-full.txt files from 12 documentation sources.

**Key Functions**:

1. **`download_file(client, url, output_path)`** (Lines 77-118)
   - Downloads single file with error handling
   - Returns status dict with size_bytes, error info

2. **`download_source(client, name, urls)`** (Lines 121-141)
   - Downloads both llms.txt and llms-full.txt concurrently
   - Returns results for both files

3. **`main()`** (Lines 144-216)
   - Orchestrates parallel download of all sources
   - Generates manifest.json with metadata
   - **Exit Code**: 0 if all succeed, 1 if any failures

**Configuration** (Lines 22-71):
- `SOURCES`: Dict mapping 12 source names to URL tuples
- `OUTPUT_DIR`: `data/raw/`

**Output Structure**:
```
data/raw/
├── {source}/
│   ├── llms.txt
│   └── llms-full.txt
└── manifest.json
```

---

#### **scripts/split_llms_pages.py** (Document Parsing)
*Location*: `scripts/split_llms_pages.py`

**Purpose**: Split llms-full.txt files into individual page documents using three different strategies.

**Splitting Strategies**:

1. **URL Pattern** (Lines 72-96) - Used by: LangChain, Anthropic, Prefect, FastMCP, McpProtocol
   - **Pattern**: `^# (.+)$\nSource: (https?://[^\n]+)` (Line 46)
   - **Function**: `split_with_url_pattern(content)`
   - **Extracts**: title, source_url, content, content_length

2. **Header-Only Pattern** (Lines 99-133) - Used by: PydanticAI, Zep
   - **Pattern**: `^# (.+)$` (Line 49)
   - **Function**: `split_with_header_pattern(content)`
   - **Feature**: Neutralizes code block headers to avoid false matches (Lines 55-69)
   - **Extracts**: title, content, content_length (no source_url)

3. **Multi-Level Pattern** (Lines 136-207) - Used by: Temporal
   - **Pattern**: `^(#{1,2})\s+(.+)$` (Line 52)
   - **Function**: `split_with_multi_level_pattern(content, levels=(1,2))`
   - **Feature**: Tracks parent-child hierarchy for nested sections (Lines 164-194)
   - **Extracts**: title, header_level, section_path, parent_title, parent_index, content

**Main Processing** (Lines 210-296):
- **`process_source(source_name, use_header_only, use_multi_level)`**
  - Reads llms-full.txt
  - Applies appropriate splitting strategy
  - Writes JSON files: `{index:04d}_{title}.json`
  - Generates per-source manifest.json

**Output Structure**:
```
data/interim/pages/
├── {source}/
│   ├── 0000_Title.json
│   ├── 0001_Title.json
│   └── manifest.json
└── manifest.json (overall)
```

---

#### **scripts/upload_to_qdrant.py** (Vector DB Upload)
*Location*: `scripts/upload_to_qdrant.py`

**Purpose**: Load JSON documents, generate embeddings, and upload to Qdrant Cloud.

**Key Functions**:

1. **`init_qdrant_client() -> QdrantClient`** (Lines 40-63)
   - Initializes Qdrant client with env credentials
   - Enables gRPC for performance

2. **`create_collection(client, collection_name)`** (Lines 66-92)
   - Creates collection if not exists
   - **Configuration**:
     - Vector size: 1536 (Line 82)
     - Distance: COSINE (Line 83)
     - on_disk: True (Lines 84, 89) - saves RAM

3. **`load_documents(pages_dir, source_filter)`** (Lines 94-176)
   - Reads JSON files from `data/interim/pages/{source}/`
   - Reads manifest.json for source-level metadata
   - Converts to LangChain Document objects
   - **Metadata Fields** (Lines 148-165):
     - title, source_url, content_length
     - header_level, section_path, parent_title, parent_index (hierarchy)
     - source_name, total_pages, avg_content_length
     - doc_id, page_number

4. **`upload_batch(batch, vector_store, batch_idx)`** (Lines 179-200)
   - Uploads single batch of documents
   - Returns document IDs

5. **`upload_documents(...)`** (Lines 203-277)
   - Orchestrates parallel batch upload
   - **Configuration**:
     - Batch size: 100 (Line 33)
     - Max workers: 4 (Line 34)
   - Uses ThreadPoolExecutor for parallelism (Lines 250-267)
   - Displays progress with tqdm (Lines 258-267)

6. **`save_upload_manifest(...)`** (Lines 280-311)
   - Saves upload metadata to `data/processed/upload_manifest.json`

**CLI Arguments** (Lines 314-345):
- `--sources`: Filter to specific sources
- `--batch-size`: Documents per batch (default: 100)
- `--workers`: Parallel workers (default: 4)
- `--dry-run`: Validate without uploading
- `--collection`: Collection name (default: "llms-full-silver")

---

#### **scripts/validate_qdrant.py** (Validation)
*Location*: `scripts/validate_qdrant.py`

**Purpose**: Comprehensive validation of Qdrant collection after upload.

**Validation Tests**:

1. **`validate_collection_info(client)`** (Lines 66-117)
   - Verifies collection exists and configuration correct
   - **Checks**: Status=green, dimension=1536, distance=COSINE, count=2670

2. **`validate_document_counts(client)`** (Lines 120-184)
   - Counts documents by source using scroll API
   - **Expected Counts** (Lines 25-33):
     - Anthropic: 932, LangChain: 506, Prefect: 767, FastMCP: 175
     - McpProtocol: 44, PydanticAI: 127, Zep: 119
   - **Total**: 2670 documents

3. **`validate_metadata_structure(client)`** (Lines 191-256)
   - Validates required metadata fields present
   - **Required Fields** (Lines 212-221):
     - title, source_url, content_length, source_name
     - total_pages, avg_content_length, doc_id, page_number

4. **`test_semantic_search(vector_store)`** (Lines 259-330)
   - Tests semantic search with 4 sample queries
   - Validates results are relevant to query
   - **Test Queries** (Lines 263-284):
     - RAG agent (expects: LangChain)
     - Claude API (expects: Anthropic)
     - Prefect workflow (expects: Prefect)
     - MCP server (expects: FastMCP, McpProtocol, Anthropic)

5. **`test_filtered_search(vector_store)`** (Lines 333-427)
   - Tests metadata filtering (requires payload index)
   - Gracefully handles missing index (Lines 410-420)
   - **Note**: Filtered search is optional feature

**Exit Code**: 0 if all pass, 1 if any fail (Lines 467-477)

---

#### **scripts/embedding_config.py** (Shared Configuration)
*Location*: `scripts/embedding_config.py`

**Purpose**: Centralized embedding model configuration.

**Public Function**:

**`get_embeddings() -> OpenAIEmbeddings`** (Lines 15-36)
- **Model**: text-embedding-3-small
- **Dimensions**: 1536
- **API Key**: From `OPENAI_API_KEY` env var
- **Error Handling**: Raises ValueError if key missing

**Test Capability** (Lines 39-56):
- Can be run standalone to test embedding configuration
- Embeds test text and displays vector info

---

#### **scripts/analyze_llms_structure.py** (Analysis Utility)
*Location*: `scripts/analyze_llms_structure.py`

**Purpose**: Analyze llms-full.txt structure to develop splitting strategy (development tool).

**Key Functions**:

1. **`split_into_documents(content)`** (Lines 26-52)
   - Prototype document splitting
   - Returns list of dicts with title, source_url, content, size

2. **`analyze_headers(content)`** (Lines 55-71)
   - Counts markdown headers (h1-h4)

3. **`analyze_jsx_components(content)`** (Lines 74-83)
   - Finds JSX/MDX components in content

4. **`analyze_source(source_name)`** (Lines 86-135)
   - Comprehensive analysis of single source
   - Returns file size, doc count, size stats, header counts, JSX usage

**Output**: Strategy recommendations for document splitting (Lines 186-217)

---

### Testing Components

#### **tests/test_mcp_server.py** (In-Memory Tests)
*Location*: `tests/test_mcp_server.py`

**Purpose**: Comprehensive in-memory testing of MCP server (80% of test coverage).

**Test Suite** (11 tests):

1. **`test_server_ping()`** (Lines 20-30)
   - Validates server responds to ping

2. **`test_list_tools()`** (Lines 33-48)
   - Validates 2 tools registered: search_docs, list_sources

3. **`test_list_sources()`** (Lines 51-86)
   - Validates all 8 sources listed
   - Checks total count: 4000-6000 range
   - Uses regex to extract counts (Lines 77-82)

4. **`test_search_docs_basic()`** (Lines 88-118)
   - Basic semantic search functionality
   - Validates result format

5. **`test_search_docs_with_source_filter()`** (Lines 121-151)
   - Source filtering functionality
   - Handles payload index limitation gracefully

6. **`test_search_docs_k_parameter_validation()`** (Lines 154-183)
   - Tests k clamping (1-20 range)

7. **`test_search_docs_empty_results()`** (Lines 185-202)
   - Graceful handling of no matches

8. **`test_search_docs_various_sources()`** (Lines 205-230)
   - Cross-source search validation

9. **`test_error_handling()`** (Lines 233-259)
   - Edge cases: empty query, invalid source

10. **`test_response_format_consistency()`** (Lines 262-289)
    - Validates consistent output format

11. **`test_search_performance_baseline()`** (Lines 293-318)
    - Performance target: < 10s (includes Qdrant API calls)

**Test Framework**: pytest with pytest-asyncio
**Client**: FastMCP in-memory client for zero-latency testing

---

#### **test_http_local.py** (HTTP Transport Tests)
*Location*: `test_http_local.py`

**Purpose**: Local HTTP transport validation (15% of test coverage) - Phase 2 testing.

**Test Suite** (7 tests):

1. **`test_http_connectivity()`** (Lines 81-96)
   - Basic HTTP ping test

2. **`test_list_tools()`** (Lines 99-112)
   - List tools via HTTP

3. **`test_list_sources()`** (Lines 115-135)
   - List sources via HTTP, validates 4+ sources found

4. **`test_search_basic()`** (Lines 138-166)
   - Basic search via HTTP

5. **`test_search_with_filter()`** (Lines 169-195)
   - Filtered search via HTTP

6. **`test_performance()`** (Lines 198-236)
   - HTTP performance baseline: < 5s target
   - **Actual**: ~2.4s avg (from testing)

7. **`test_error_handling()`** (Lines 239-262)
   - Error handling via HTTP

**Server Requirement**: Server must be running on http://localhost:8000/sse
**Usage**:
```bash
# Terminal 1
uv run python run_http_server.py

# Terminal 2
uv run python test_http_local.py
```

**Exit Code**: 0 if all pass, 1 if any fail (Line 329)

---

#### **test_cloud_deployment.py** (Cloud Validation)
*Location*: `test_cloud_deployment.py`

**Purpose**: Cloud deployment validation (5% of test coverage) - Phase 3 testing.

**Test Suite** (6 tests):

1. **`test_cloud_connectivity()`** (Lines 63-78)
   - Cloud endpoint ping

2. **`test_cloud_tools()`** (Lines 81-94)
   - List tools from cloud

3. **`test_cloud_list_sources()`** (Lines 97-115)
   - List sources from cloud

4. **`test_cloud_search()`** (Lines 118-145)
   - Semantic search from cloud

5. **`test_cloud_performance()`** (Lines 148-196)
   - Cloud performance comparison
   - **Target**: < 2s (Line 187)
   - **Baseline**: 2.4s local (Line 176)

6. **`test_cloud_error_handling()`** (Lines 199-219)
   - Cloud error handling

**Cloud URL**: https://qdrant-docs.fastmcp.app/mcp (Line 60)
**Exit Code**: 0 if all pass, 1 if any fail (Line 283)

---

## Entry Points

### Primary Entry Points

1. **MCP Server (stdio transport)**
   - **File**: `mcp_server.py`
   - **Command**: `uv run python mcp_server.py`
   - **Use Case**: Local development, Claude Code integration (stdio)
   - **Transport**: stdio (default)
   - **Port**: N/A (stdio uses stdin/stdout)

2. **HTTP Server (SSE transport)**
   - **File**: `run_http_server.py`
   - **Command**: `uv run python run_http_server.py`
   - **Use Case**: Local HTTP testing, cloud deployment
   - **Transport**: HTTP/SSE
   - **URL**: http://localhost:8000/mcp/

3. **Cloud Deployment**
   - **URL**: https://qdrant-docs.fastmcp.app/mcp
   - **Transport**: HTTP/SSE
   - **Status**: Production (based on test_cloud_deployment.py)

### Data Pipeline Entry Points

4. **Download Documentation**
   - **File**: `scripts/download_llms_raw.py`
   - **Command**: `uv run python scripts/download_llms_raw.py`
   - **Output**: `data/raw/{source}/llms-full.txt`

5. **Split into Pages**
   - **File**: `scripts/split_llms_pages.py`
   - **Command**: `uv run python scripts/split_llms_pages.py`
   - **Output**: `data/interim/pages/{source}/{index}_Title.json`

6. **Upload to Qdrant**
   - **File**: `scripts/upload_to_qdrant.py`
   - **Command**: `uv run python scripts/upload_to_qdrant.py [--sources SOURCE...] [--dry-run]`
   - **Output**: Qdrant collection "llms-full-silver"

7. **Validate Collection**
   - **File**: `scripts/validate_qdrant.py`
   - **Command**: `uv run python scripts/validate_qdrant.py`
   - **Output**: Validation report (stdout), exit code 0/1

### Testing Entry Points

8. **In-Memory Tests**
   - **File**: `tests/test_mcp_server.py`
   - **Command**: `uv run pytest tests/test_mcp_server.py -v`
   - **Coverage**: 80% (11 tests)

9. **HTTP Tests**
   - **File**: `test_http_local.py`
   - **Command**: `uv run python test_http_local.py`
   - **Prerequisite**: HTTP server running
   - **Coverage**: 15% (7 tests)

10. **Cloud Tests**
    - **File**: `test_cloud_deployment.py`
    - **Command**: `uv run python test_cloud_deployment.py`
    - **Prerequisite**: Cloud deployment active
    - **Coverage**: 5% (6 tests)

---

## Configuration Files

### Environment Configuration

**`.env`** (not in repo, created from .env.example)
- **Required Variables**:
  - `QDRANT_API_URL`: Qdrant Cloud instance URL
  - `QDRANT_API_KEY`: Qdrant API key
  - `OPENAI_API_KEY`: OpenAI API key for embeddings

**`.env.example`** (template)
- Located at: `.env.example`
- Contains documentation for all required environment variables

### Project Configuration

**`pyproject.toml`**
- **Location**: `pyproject.toml`
- **Project Name**: graphiti-qdrant
- **Version**: 0.1.0
- **Python Version**: >=3.11
- **Dependencies** (Lines 7-18):
  - datasets>=4.4.1
  - langchain-community>=0.4.1
  - ipywidgets>=8.1.8
  - langchain>=1.1.0
  - langchain-qdrant>=1.1.0
  - langchain-openai>=1.1.0
  - python-dotenv>=1.0.0
  - tqdm>=4.67.1
  - fastmcp>=0.7.0
  - claude-agent-sdk>=0.1.18
- **Dev Dependencies** (Lines 21-24):
  - pytest>=9.0.1
  - pytest-asyncio>=1.3.0

**`uv.lock`**
- Dependency lockfile for reproducible builds
- Located at: `uv.lock`

---

## Data Flow Architecture

```
1. ACQUISITION
   download_llms_raw.py
   ↓
   data/raw/{source}/llms-full.txt

2. PARSING
   split_llms_pages.py
   ↓
   data/interim/pages/{source}/XXXX_Title.json

3. EMBEDDING & UPLOAD
   upload_to_qdrant.py + embedding_config.py
   ↓
   Qdrant Cloud (llms-full-silver collection)

4. VALIDATION
   validate_qdrant.py
   ↓
   Validation report

5. SERVING
   mcp_server.py (stdio/HTTP)
   ↓
   Claude Code / HTTP Clients
```

---

## Component Summary

### Public API Surface
- **MCP Tools**: 2 tools (search_docs, list_sources)
- **Entry Points**: 3 (stdio, HTTP local, HTTP cloud)
- **Configuration**: Environment variables only (.env)

### Internal Implementation
- **Data Pipeline**: 4 stages (download → split → upload → validate)
- **Scripts**: 5 pipeline scripts + 1 analysis utility
- **Tests**: 24 total tests (11 in-memory + 7 HTTP + 6 cloud)
- **Documentation**: 13+ markdown files in docs/

### External Dependencies
- **Vector DB**: Qdrant Cloud (managed service)
- **Embeddings**: OpenAI text-embedding-3-small API
- **Framework**: FastMCP 2.0, LangChain

### Key Design Patterns
1. **Strategy Pattern**: Multiple splitting strategies for different documentation formats
2. **Factory Pattern**: get_embeddings(), get_vector_store() for dependency injection
3. **Pipeline Pattern**: Sequential data processing (download → split → upload → validate)
4. **Test Pyramid**: 80% in-memory, 15% HTTP, 5% cloud (per FastMCP strategy)

---

## Notes

1. **Excluded from Analysis**: All `ra_*` directories are analysis framework code, not part of the main project.

2. **Test Coverage Strategy**: Following FastMCP Cloud Promotion Strategy V1:
   - Phase 1: In-memory tests (80%) - Fast, deterministic
   - Phase 2: Local HTTP tests (15%) - Network behavior validation
   - Phase 3: Cloud preview (5%) - Final production validation

3. **Vector DB**: Uses Qdrant Cloud with on-disk storage for cost optimization (saves RAM).

4. **Metadata Hierarchy**: Temporal source uses multi-level hierarchy tracking (parent-child relationships) for better context in search results.

5. **Performance Targets**:
   - In-memory: < 10s (includes Qdrant API calls)
   - Local HTTP: ~2.4s avg
   - Cloud: < 2s target

6. **Collection Stats** (as of validation):
   - Total documents: 2,670
   - Sources: 7 (Anthropic, LangChain, Prefect, FastMCP, McpProtocol, PydanticAI, Zep)
   - Note: README mentions 8 sources and 4,969 pages, suggesting Temporal was added later

7. **Transport Modes**:
   - **stdio**: For Claude Code desktop integration (local)
   - **HTTP/SSE**: For web clients and cloud deployment
   - Same server code supports both via FastMCP 2.0

---

**Document Version**: 1.0
**Last Updated**: 2025-12-18
**Analyzer**: Claude Opus 4.5
