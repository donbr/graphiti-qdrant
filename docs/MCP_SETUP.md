# MCP Server Setup for Claude Code

This guide shows how to configure Claude Code to use the custom Qdrant MCP server for semantic documentation search.

## Overview

The custom MCP server (`mcp_server.py`) provides Claude Code with semantic search capabilities over your 2,670 documentation pages stored in Qdrant Cloud. This enables:

- **Semantic search** instead of loading massive llms-full.txt files
- **Source-filtered search** (e.g., search only Anthropic docs)
- **Full document retrieval** with metadata (titles, URLs, source names)
- **Same embeddings** as your upload (OpenAI text-embedding-3-small)

## Prerequisites

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Verify environment variables in `.env`:**
   ```bash
   # Qdrant Configuration
   QDRANT_API_KEY=your_api_key_here
   QDRANT_API_URL=https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333

   # OpenAI Configuration
   OPENAI_API_KEY=sk-proj-...
   MODEL_NAME=gpt-4.1-mini
   ```

## Option 1: Add to Claude Code (Recommended)

Add the MCP server to Claude Code using the CLI:

```bash
# Navigate to project directory
cd /home/donbr/graphiti-qdrant

# Add the MCP server to Claude Code
claude mcp add qdrant-docs \
  -e QDRANT_API_URL="$(grep QDRANT_API_URL .env | cut -d= -f2)" \
  -e QDRANT_API_KEY="$(grep QDRANT_API_KEY .env | cut -d= -f2)" \
  -e OPENAI_API_KEY="$(grep OPENAI_API_KEY .env | cut -d= -f2)" \
  -- uv run python mcp_server.py
```

Verify the server was added:

```bash
claude mcp list
```

## Option 2: Manual Configuration

If you prefer manual configuration, add this to your Claude Code MCP configuration file (usually `~/.claude/mcp.json`):

```json
{
  "qdrant-docs": {
    "command": "uv",
    "args": ["run", "python", "/home/donbr/graphiti-qdrant/mcp_server.py"],
    "cwd": "/home/donbr/graphiti-qdrant",
    "env": {
      "QDRANT_API_URL": "your_qdrant_url",
      "QDRANT_API_KEY": "your_qdrant_key",
      "OPENAI_API_KEY": "your_openai_key"
    }
  }
}
```

## Available MCP Tools

Once configured, Claude Code will have access to these tools:

### 1. `search_docs`

Search documentation using semantic similarity.

**Parameters:**
- `query` (string, required): Natural language search query
- `k` (int, optional): Number of results (default: 5, max: 20)
- `source` (string, optional): Filter by source name

**Examples:**
```python
# Basic search
search_docs("How do I build a RAG agent with LangChain?")

# Search with more results
search_docs("authentication methods", k=10)

# Search only Anthropic docs
search_docs("Claude API features", source="Anthropic")

# Search only Prefect docs
search_docs("workflow orchestration", source="Prefect")
```

### 2. `list_sources`

List all available documentation sources with document counts.

**Example:**
```python
list_sources()
```

**Output:**
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
Zep             119
------------------------------
TOTAL           2670
```

## Usage in Claude Code

Once the MCP server is configured, Claude Code will automatically use it when you ask questions about the documentation:

**Example conversations:**

> "Search for documentation about building RAG agents"

Claude Code will use `search_docs("building RAG agents")` and return relevant documentation.

> "Show me Anthropic's documentation about prompt caching"

Claude Code will use `search_docs("prompt caching", source="Anthropic")` to filter results.

> "What documentation sources are available?"

Claude Code will use `list_sources()` to show all available sources.

## Testing the MCP Server

Test the server manually before adding to Claude Code:

```bash
# Test in development mode with MCP inspector
uv run fastmcp dev mcp_server.py
```

This will:
1. Start the MCP server
2. Open the MCP inspector in your browser (default: http://localhost:5173)
3. Allow you to test tools interactively

## Troubleshooting

### Server fails to start

Check that all environment variables are set:
```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('QDRANT_API_URL:', os.getenv('QDRANT_API_URL'))
print('QDRANT_API_KEY:', 'Set' if os.getenv('QDRANT_API_KEY') else 'Not set')
print('OPENAI_API_KEY:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Not set')
"
```

### No search results

Verify the collection exists and has documents:
```bash
uv run python scripts/validate_qdrant.py
```

### Slow searches

- Each search generates an embedding via OpenAI API (~100-200ms)
- Qdrant search is fast (~10-50ms)
- Total latency: ~200-500ms per query

### Filter errors

If you get filter errors when using `source` parameter, the collection may need a payload index:

```python
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# Create index for source_name filtering
client.create_payload_index(
    collection_name="llms-full-silver",
    field_name="metadata.source_name",
)
```

## Performance Characteristics

- **Search latency**: ~200-500ms (includes embedding generation)
- **Results per query**: Configurable (default: 5, max: 20)
- **Cost**: ~$0.0001 per search (OpenAI embedding API)
- **Full content**: Each result includes the complete document text

## Next Steps

After setting up the MCP server:

1. **Test basic search**: Ask Claude Code to search for documentation
2. **Try filtered search**: Use source filtering for specific documentation sets
3. **Compare with direct file access**: Notice improved speed vs loading llms-full.txt
4. **Adjust result count**: Tune `k` parameter based on your needs

## Architecture

```
Claude Code
    ↓ (MCP Protocol)
mcp_server.py
    ↓ (LangChain + OpenAI API)
OpenAI Embeddings (text-embedding-3-small)
    ↓ (Vector search)
Qdrant Cloud (llms-full-silver collection)
    ↓ (Return documents)
Claude Code (receives formatted results)
```

## Benefits Over Direct File Access

| Aspect | llms-full.txt Files | MCP + Qdrant |
|--------|---------------------|--------------|
| **Load time** | Minutes (large files) | <1 second |
| **Search** | Keyword only | Semantic similarity |
| **Context size** | Limited by file size | Top-k most relevant |
| **Filtering** | Manual | Automatic by source |
| **Updates** | Replace entire file | Update specific docs |
| **Cost** | Free | ~$0.0001/query |

## Additional Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LangChain Qdrant Integration](https://python.langchain.com/docs/integrations/vectorstores/qdrant)
