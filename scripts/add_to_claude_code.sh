#!/bin/bash
# Add Qdrant MCP server to Claude Code
#
# This script reads environment variables from .env and configures
# Claude Code to use the custom Qdrant MCP server.

set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please create a .env file with QDRANT_API_URL, QDRANT_API_KEY, and OPENAI_API_KEY"
    exit 1
fi

# Load environment variables
source .env

# Verify required variables
if [ -z "$QDRANT_API_URL" ]; then
    echo "Error: QDRANT_API_URL not set in .env"
    exit 1
fi

if [ -z "$QDRANT_API_KEY" ]; then
    echo "Error: QDRANT_API_KEY not set in .env"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set in .env"
    exit 1
fi

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Adding Qdrant MCP server to Claude Code..."
echo "Project root: $PROJECT_ROOT"
echo ""

# Add MCP server to Claude Code
claude mcp add qdrant-docs \
  -e QDRANT_API_URL="$QDRANT_API_URL" \
  -e QDRANT_API_KEY="$QDRANT_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -- uv run --directory "$PROJECT_ROOT" python "$PROJECT_ROOT/mcp_server.py"

echo ""
echo "✓ MCP server added successfully!"
echo ""
echo "Verify with: claude mcp list"
echo ""
echo "You can now use semantic search in Claude Code:"
echo "  - Ask questions about documentation"
echo "  - Claude Code will automatically use the search_docs tool"
echo "  - Searches across 2,670 documentation pages from 7 sources"
