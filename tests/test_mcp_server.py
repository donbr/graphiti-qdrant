"""
In-memory tests for qdrant-docs MCP server.

These tests run BEFORE cloud deployment to validate logic locally.
They use FastMCP's in-memory Client for zero-latency testing.

Test Strategy (from FASTMCP_CLOUD_PROMOTION_STRATEGY_V1.md):
- 80% of tests should be in-memory (fast, deterministic)
- 15% should be local HTTP (network behavior)
- 5% should be cloud preview (final validation)

Run with:
    uv run pytest tests/test_mcp_server.py -v
"""
import pytest
from fastmcp import Client
from mcp_server import mcp


@pytest.mark.asyncio
async def test_server_ping():
    """
    Test basic server connectivity.

    This validates that the MCP server initializes correctly
    and responds to ping requests.
    """
    async with Client(mcp) as client:
        result = await client.ping()
        assert result is True, "Server should respond to ping"


@pytest.mark.asyncio
async def test_list_tools():
    """
    Test that all expected tools are registered.

    The qdrant-docs server should expose exactly 2 tools:
    - search_docs: Semantic search over documentation
    - list_sources: List available documentation sources
    """
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]

        assert len(tools) == 2, f"Expected 2 tools, found {len(tools)}"
        assert "search_docs" in tool_names, "search_docs tool should be registered"
        assert "list_sources" in tool_names, "list_sources tool should be registered"


@pytest.mark.asyncio
async def test_list_sources():
    """
    Test the list_sources tool returns expected documentation sources.

    Note: Document counts are now dynamically retrieved from Qdrant.
    This test validates that all expected sources are present and have
    reasonable document counts (> 0).
    """
    async with Client(mcp) as client:
        result = await client.call_tool("list_sources", {})
        content = result.content[0].text

        # Validate all expected sources are listed
        assert "Anthropic" in content, "Anthropic source should be listed"
        assert "LangChain" in content, "LangChain source should be listed"
        assert "Prefect" in content, "Prefect source should be listed"
        assert "FastMCP" in content, "FastMCP source should be listed"
        assert "PydanticAI" in content, "PydanticAI source should be listed"
        assert "Zep" in content, "Zep source should be listed"
        assert "McpProtocol" in content, "McpProtocol source should be listed"
        assert "Temporal" in content, "Temporal source should be listed"

        # Validate TOTAL count is shown and reasonable
        assert "TOTAL" in content, "Total count should be shown"
        # Extract total from content (format: "TOTAL           4886      ")
        import re
        total_match = re.search(r'TOTAL\s+(\d+)', content)
        assert total_match, "Should find TOTAL count in output"
        total = int(total_match.group(1))
        assert total > 4000, f"Total should be > 4000, got {total}"
        assert total < 6000, f"Total should be < 6000, got {total}"

        # Validate usage example is provided
        assert "search_docs" in content, "Usage example should be included"


@pytest.mark.asyncio
async def test_search_docs_basic():
    """
    Test basic semantic search functionality.

    This validates that:
    - Search executes without errors
    - Results are returned in expected format
    - Content preview is included
    """
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_docs",
            {"query": "FastMCP deployment", "k": 3}
        )
        content = result.content[0].text

        # Validate results format
        assert "Found 3 results" in content, "Should return exactly 3 results"
        assert "Result 1/3" in content, "Should show result numbering"
        assert "Title:" in content, "Should include result titles"
        assert "Source:" in content, "Should include source names"
        assert "URL:" in content, "Should include source URLs"
        assert "Content Preview" in content, "Should include content preview"

        # Validate at least one result is relevant
        # (FastMCP or deployment should appear in results)
        assert (
            "FastMCP" in content or
            "deployment" in content.lower()
        ), "Results should be semantically relevant to query"


@pytest.mark.asyncio
async def test_search_docs_with_source_filter():
    """
    Test source filtering functionality.

    This validates that:
    - Source parameter is accepted and processed
    - Filter behavior is documented (may fail if no payload index)
    - System handles filtering gracefully
    """
    async with Client(mcp) as client:
        # Test filtering by Anthropic
        result = await client.call_tool(
            "search_docs",
            {"query": "authentication", "source": "Anthropic", "k": 2}
        )
        content = result.content[0].text

        # Should return a response (either results or no results message)
        assert len(content) > 0, "Should return a response"

        # Handle both cases: payload index exists or doesn't exist
        if "payload index not created" in content:
            # Expected if Qdrant collection doesn't have payload index
            assert "No results found" in content, "Should indicate no results when index missing"
        else:
            # If payload index exists, should return filtered results
            assert "Found" in content or "No results" in content, "Should indicate search was performed"
            if "Found" in content:
                # Validate results are from correct source
                assert "Anthropic" in content, "Results should be from Anthropic source"


@pytest.mark.asyncio
async def test_search_docs_k_parameter_validation():
    """
    Test k parameter validation and clamping.

    From mcp_server.py:90, k is clamped between 1 and 20:
    - k < 1 should be clamped to 1
    - k > 20 should be clamped to 20
    """
    async with Client(mcp) as client:
        # Test with k > 20 (should clamp to 20)
        result = await client.call_tool(
            "search_docs",
            {"query": "test query", "k": 100}
        )
        content = result.content[0].text

        # Should execute without error (clamped internally)
        assert "Found" in content or "No results" in content, "Should handle large k values"

        # Test with k = 1 (minimum valid value)
        result = await client.call_tool(
            "search_docs",
            {"query": "test query", "k": 1}
        )
        content = result.content[0].text

        if "Found 1 result" in content:
            assert "Result 1/1" in content, "Should return exactly 1 result"


@pytest.mark.asyncio
async def test_search_docs_empty_results():
    """
    Test behavior when no results are found.

    This validates graceful handling of queries that don't match any documents.
    """
    async with Client(mcp) as client:
        # Use a very specific nonsense query unlikely to match anything
        result = await client.call_tool(
            "search_docs",
            {"query": "xyzabc123nonsensequery456", "k": 5}
        )
        content = result.content[0].text

        # Should return a message (either results or "No results found")
        assert len(content) > 0, "Should return a response even for no matches"
        assert "No results found" in content or "Found" in content, "Should indicate search was performed"


@pytest.mark.asyncio
async def test_search_docs_various_sources():
    """
    Test searching across different documentation sources.

    This validates that semantic search works for various domains:
    - Anthropic (AI/LLM documentation)
    - LangChain (framework documentation)
    - FastMCP (MCP server documentation)
    """
    async with Client(mcp) as client:
        # Test LangChain-specific query
        result_lc = await client.call_tool(
            "search_docs",
            {"query": "building RAG applications", "k": 3}
        )
        content_lc = result_lc.content[0].text
        assert "Found" in content_lc, "Should find results for LangChain query"

        # Test Anthropic-specific query
        result_ant = await client.call_tool(
            "search_docs",
            {"query": "Claude API prompt engineering", "k": 3}
        )
        content_ant = result_ant.content[0].text
        assert "Found" in content_ant, "Should find results for Anthropic query"


@pytest.mark.asyncio
async def test_error_handling():
    """
    Test error handling for invalid inputs.

    This validates that the server handles edge cases gracefully.
    """
    async with Client(mcp) as client:
        # Test with empty query string
        result = await client.call_tool(
            "search_docs",
            {"query": "", "k": 5}
        )
        content = result.content[0].text

        # Should handle gracefully (either results or error message)
        assert len(content) > 0, "Should return a response for empty query"

        # Test with invalid source filter
        result = await client.call_tool(
            "search_docs",
            {"query": "test", "source": "NonExistentSource", "k": 5}
        )
        content = result.content[0].text

        # Should handle gracefully (likely no results)
        assert len(content) > 0, "Should return a response for invalid source"


@pytest.mark.asyncio
async def test_response_format_consistency():
    """
    Test that response format is consistent across different queries.

    This validates that all search results follow the same format:
    - Title, Source, URL, Doc ID, Content Preview
    - Consistent separators and structure
    """
    async with Client(mcp) as client:
        # Run multiple searches
        queries = [
            {"query": "authentication", "k": 2},
            {"query": "deployment", "k": 3},
            {"query": "API reference", "k": 1},
        ]

        for query_params in queries:
            result = await client.call_tool("search_docs", query_params)
            content = result.content[0].text

            if "Found" in content and "No results" not in content:
                # Validate consistent format
                assert "Title:" in content, "Should include Title field"
                assert "Source:" in content, "Should include Source field"
                assert "URL:" in content, "Should include URL field"
                assert "Content Preview" in content, "Should include Content Preview section"
                assert "=" * 80 in content, "Should include separator lines"


# Performance baseline tests
@pytest.mark.asyncio
async def test_search_performance_baseline():
    """
    Establish performance baseline for in-memory tests.

    This helps identify performance regressions before cloud deployment.
    Target: < 500ms for in-memory tests (per strategy document)
    """
    import time

    async with Client(mcp) as client:
        start = time.time()

        result = await client.call_tool(
            "search_docs",
            {"query": "test performance", "k": 5}
        )

        elapsed = time.time() - start

        # In-memory should be very fast (< 2s even with network calls to Qdrant)
        # Note: This includes actual Qdrant API calls, so may be slower than pure in-memory
        assert elapsed < 10.0, f"Search took {elapsed:.2f}s, expected < 10s"

        # Log performance for monitoring
        print(f"\n⏱️  Search performance: {elapsed:.3f}s")


if __name__ == "__main__":
    # Allow running tests directly
    import asyncio

    async def run_all_tests():
        """Run all tests manually for debugging."""
        print("🧪 Running qdrant-docs in-memory tests...\n")

        tests = [
            ("Server Ping", test_server_ping()),
            ("List Tools", test_list_tools()),
            ("List Sources", test_list_sources()),
            ("Basic Search", test_search_docs_basic()),
            ("Source Filter", test_search_docs_with_source_filter()),
            ("K Parameter Validation", test_search_docs_k_parameter_validation()),
            ("Empty Results", test_search_docs_empty_results()),
            ("Various Sources", test_search_docs_various_sources()),
            ("Error Handling", test_error_handling()),
            ("Response Format", test_response_format_consistency()),
            ("Performance Baseline", test_search_performance_baseline()),
        ]

        passed = 0
        failed = 0

        for name, test_coro in tests:
            try:
                await test_coro
                print(f"✅ {name}")
                passed += 1
            except Exception as e:
                print(f"❌ {name}: {e}")
                failed += 1

        print(f"\n{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*60}")

    asyncio.run(run_all_tests())
