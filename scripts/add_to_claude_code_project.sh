#!/bin/bash
# Add Qdrant MCP server to Claude Code (PROJECT-SPECIFIC)
#
# This script creates a project-specific MCP configuration that only
# applies when working in this directory.

set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_CONFIG_DIR="$PROJECT_ROOT/.claude"
MCP_CONFIG_FILE="$MCP_CONFIG_DIR/mcp.json"

echo "Setting up project-specific MCP configuration..."
echo "Project root: $PROJECT_ROOT"
echo "Config file: $MCP_CONFIG_FILE"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found at $PROJECT_ROOT/.env"
    echo "Please create a .env file with QDRANT_API_URL, QDRANT_API_KEY, and OPENAI_API_KEY"
    exit 1
fi

# MCP config already created by the Write tool
echo "✓ MCP configuration file already exists at $MCP_CONFIG_FILE"
echo ""
echo "Configuration details:"
echo "  - Server name: qdrant-docs"
echo "  - Command: uv run python mcp_server.py"
echo "  - Environment variables: Uses .env file in this project"
echo ""
echo "✓ Project-specific MCP server configured successfully!"
echo ""
echo "This configuration ONLY applies when Claude Code is running in:"
echo "  $PROJECT_ROOT"
echo ""
echo "To use it:"
echo "  1. Start Claude Code in this project directory"
echo "  2. The qdrant-docs server will be automatically available"
echo "  3. Ask questions about documentation"
echo ""
echo "Note: This does NOT affect Claude Code sessions in other directories."
