# Quick Start: Qdrant MCP Server for Claude Code

## Prerequisites

Before setting up the MCP server, you need:

### 1. Qdrant Cloud Instance

If you don't have a Qdrant instance yet:

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a new cluster (free tier available)
3. Note your cluster URL (e.g., `https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333`)
4. Create an API key from the cluster dashboard

### 2. OpenAI API Key

Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Qdrant Configuration
QDRANT_API_URL=https://your-cluster-id.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
MODEL_NAME=gpt-4.1-mini
```

## Setup (One-Time)

```bash
# 1. Install dependencies
uv sync

# 2. Test the MCP server
uv run python scripts/test_mcp_server.py

# 3. Choose your configuration method:
```

### Option A: Project-Specific (Recommended)

**Best if:** You only want this MCP server available when working in this project.

```bash
./scripts/add_to_claude_code_project.sh
```

The server will ONLY be available when Claude Code is running in this project directory.

### Option B: Global Configuration

**Best if:** You want access to documentation search from any Claude Code session.

```bash
./scripts/add_to_claude_code.sh
```

The server will be available in ALL Claude Code sessions, but depends on this project's files.

## Manual Configuration (Alternative)

If the automatic scripts don't work, manually configure:

```bash
claude mcp add qdrant-docs \
  -e QDRANT_API_URL="your_url" \
  -e QDRANT_API_KEY="your_key" \
  -e OPENAI_API_KEY="your_key" \
  -- uv run --directory /home/donbr/graphiti-qdrant python /home/donbr/graphiti-qdrant/mcp_server.py
```

## Verify Installation

```bash
claude mcp list
```

You should see `qdrant-docs` in the list.

## Usage in Claude Code

Once configured, Claude Code will automatically use the MCP server when you ask questions about documentation.

### Example Queries

**General search:**
> "Show me documentation about building RAG agents"

Claude Code uses: `search_docs("building RAG agents", k=5)`

**Source-specific search:**
> "What does Anthropic say about prompt caching?"

Claude Code uses: `search_docs("prompt caching", source="Anthropic")`

**List available sources:**
> "What documentation sources are available?"

Claude Code uses: `list_sources()`

## What's Available

- **2,670 documentation pages** from 7 sources
- **OpenAI text-embedding-3-small** for semantic search
- **Sources:** Anthropic (932), LangChain (506), Prefect (767), FastMCP (175), McpProtocol (44), PydanticAI (127), Zep (119)

## Troubleshooting

### MCP server not appearing

```bash
# Remove and re-add
claude mcp remove qdrant-docs
./scripts/add_to_claude_code.sh
```

### Search not working

```bash
# Test locally
uv run python scripts/test_mcp_server.py
```

### Environment variables not loading

Verify `.env` file has:
```bash
QDRANT_API_URL=https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_key
OPENAI_API_KEY=sk-proj-...
```

## Performance

- **Search latency:** ~200-500ms (includes embedding generation)
- **Cost per query:** ~$0.0001 (OpenAI embedding API)
- **Results:** Default 5, max 20 per query

## Next Steps

See [MCP_SETUP.md](MCP_SETUP.md) for detailed documentation.
