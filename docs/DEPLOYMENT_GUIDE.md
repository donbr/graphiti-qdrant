# Platform Docs Deployment Guide

## Overview

This project provides two parallel MCP server deployments for semantic documentation search:

| Endpoint | Collection | Embedding Model | API Key Required |
|----------|------------|-----------------|------------------|
| `platform-docs` | `platform-docs` | OpenAI text-embedding-3-small (1536d) | Yes (OpenAI) |
| `platform-docs-free` | `platform-docs-fastembed` | BAAI/bge-small-en-v1.5 (384d) | No |

Both contain 7,423 documents from 8 sources: Anthropic, LangChain, Prefect, FastMCP, McpProtocol, PydanticAI, Temporal, Zep.

---

## Deployment Configurations

### platform-docs (OpenAI Embeddings)

**FastMCP Cloud Settings:**
- **Name**: `platform-docs`
- **Entry Point**: `platform_docs_server.py:mcp`
- **Config File**: `fastmcp.json`

**Environment Variables Required:**
```
QDRANT_API_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
OPENAI_API_KEY=sk-proj-your-openai-key
```

**Add to Claude Code:**
```bash
claude mcp add --scope user --transport http platform-docs https://platform-docs.fastmcp.app/mcp
```

---

### platform-docs-free (FastEmbed - No API Key)

**FastMCP Cloud Settings:**
- **Name**: `platform-docs-free`
- **Entry Point**: `platform_docs_fastembed_server.py:mcp`
- **Config File**: `fastmcp-fastembed.json`

**Environment Variables Required:**
```
QDRANT_API_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
```
*No OpenAI API key needed!*

**Add to Claude Code:**
```bash
claude mcp add --scope user --transport http platform-docs-free https://platform-docs-free.fastmcp.app/mcp
```

---

## Data Refresh Process

### Step 1: Download Fresh Documentation
```bash
uv run scripts/download_llms_raw.py
```
Downloads `llms.txt` and `llms-full.txt` from 12 sources to `data/raw/`.

### Step 2: Split into Pages
```bash
uv run scripts/split_llms_pages.py
```
Parses documentation into individual JSON files in `data/interim/pages/`.

### Step 3: Upload to Collections

**For OpenAI collection (platform-docs):**
```bash
uv run scripts/upload_to_qdrant.py --collection platform-docs
```

**For FastEmbed collection (platform-docs-fastembed):**
```bash
uv run scripts/upload_to_qdrant_fastembed.py --collection platform-docs-fastembed
```

### Step 4: Verify Upload
Use the validation queries below to confirm both collections are working.

---

## Validation Test Queries

Use these queries to test the MCP servers in Claude Code:

### Test 1: List Sources
```
Use platform-docs to list all available documentation sources.
```
**Expected**: 8 sources, 7,423 total documents

### Test 2: Basic Search
```
Search platform-docs for "how to create a FastMCP server"
```
**Expected**: FastMCP documentation results with code examples

### Test 3: Source Filtering
```
Search platform-docs for "API authentication" filtering to Anthropic only
```
**Expected**: Anthropic-specific results about API keys and headers

### Test 4: Cross-Source Query
```
Using platform-docs, find documentation about durable execution and workflows
```
**Expected**: Results from Temporal and possibly LangChain

### Test 5: Free Server Comparison
```
Use platform-docs-free to search for "RAG agent implementation"
```
**Expected**: Similar results to platform-docs (may differ in ranking)

### Test 6: Large Document Search
```
Search platform-docs for "Claude extended thinking" with k=10
```
**Expected**: Multiple Anthropic docs about thinking and reasoning features

---

## Troubleshooting

### "No results found for source filter"
The payload index might not be created. Run:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
client.create_payload_index(
    collection_name="platform-docs",
    field_name="metadata.source_name",
    field_schema=PayloadSchemaType.KEYWORD,
)
```

### First query is slow on platform-docs-free
FastEmbed downloads the model on first use (~50MB). Subsequent queries are fast.

### OpenAI rate limit errors during upload
Use smaller batches and add delays:
```bash
uv run scripts/upload_to_qdrant.py --batch-size 25 --workers 2
```

---

## Architecture Summary

```
GitHub Repo (donbr/graphiti-qdrant)
    │
    ├── data/
    │   ├── raw/           ← Downloaded llms.txt files
    │   ├── interim/pages/ ← Split JSON documents
    │   └── processed/     ← Upload manifests
    │
    ├── Scripts
    │   ├── download_llms_raw.py
    │   ├── split_llms_pages.py
    │   ├── upload_to_qdrant.py (OpenAI)
    │   └── upload_to_qdrant_fastembed.py (Free)
    │
    └── MCP Servers
        ├── platform_docs_server.py → platform-docs.fastmcp.app
        └── platform_docs_fastembed_server.py → platform-docs-free.fastmcp.app
```

Both servers connect to Qdrant Cloud where the vector collections are stored.
