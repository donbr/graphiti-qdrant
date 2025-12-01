#!/usr/bin/env python3
"""
Run qdrant-docs MCP server with HTTP transport for local testing.

This script starts the MCP server on http://localhost:8000/mcp/
for Phase 2 testing (local HTTP validation).

Usage:
    uv run python run_http_server.py

The server will be accessible at:
    http://localhost:8000/mcp/
"""
from mcp_server import mcp

if __name__ == "__main__":
    # Run with HTTP transport for local testing
    mcp.run(transport="sse")
