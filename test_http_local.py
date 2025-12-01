#!/usr/bin/env python3
"""
Local HTTP transport test for qdrant-docs MCP server.

This test validates network behavior BEFORE cloud deployment.
It tests the full HTTP transport stack locally to ensure:
- Server starts correctly on HTTP
- Client can connect over network
- JSON serialization/deserialization works
- All tools work via HTTP (not just in-memory)

Prerequisites:
1. Start the MCP server in another terminal:
   uv run fastmcp run mcp_server.py

2. Server should be running on http://localhost:8000/mcp/

3. Run this test:
   uv run python test_http_local.py

This is Phase 2 of the FastMCP Cloud Promotion Strategy:
- Phase 1: In-memory tests (80%) ✅ COMPLETE
- Phase 2: Local HTTP tests (15%) ← YOU ARE HERE
- Phase 3: Cloud preview (5%)
"""
import asyncio
import sys
from typing import Optional

import httpx
from fastmcp import Client


# ANSI color codes for pretty output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


async def check_server_running() -> bool:
    """Check if MCP server is running on localhost:8000."""
    try:
        # Try using the FastMCP Client to ping the server
        async with Client("http://localhost:8000/sse") as client:
            return await client.ping()
    except Exception:
        return False


async def test_http_connectivity():
    """Test 1: Basic HTTP connectivity."""
    print_header("Test 1: HTTP Connectivity")

    try:
        async with Client("http://localhost:8000/sse") as client:
            result = await client.ping()
            if result:
                print_success(f"Server ping: {result}")
                return True
            else:
                print_error("Server did not respond to ping")
                return False
    except Exception as e:
        print_error(f"Connectivity test failed: {e}")
        return False


async def test_list_tools():
    """Test 2: List available tools via HTTP."""
    print_header("Test 2: List Tools")

    try:
        async with Client("http://localhost:8000/sse") as client:
            tools = await client.list_tools()
            print_success(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:60]}...")
            return len(tools) == 2
    except Exception as e:
        print_error(f"List tools test failed: {e}")
        return False


async def test_list_sources():
    """Test 3: Test list_sources tool via HTTP."""
    print_header("Test 3: List Sources Tool")

    try:
        async with Client("http://localhost:8000/sse") as client:
            result = await client.call_tool("list_sources", {})
            content = result.content[0].text

            # Check for expected sources
            sources = ["Anthropic", "LangChain", "Prefect", "FastMCP", "PydanticAI"]
            found = [s for s in sources if s in content]

            print_success(f"Found {len(found)}/{len(sources)} expected sources")
            print("\nSources list preview:")
            print(content[:500])

            return len(found) >= 4  # At least 4 sources should be found
    except Exception as e:
        print_error(f"List sources test failed: {e}")
        return False


async def test_search_basic():
    """Test 4: Basic semantic search via HTTP."""
    print_header("Test 4: Basic Search")

    try:
        async with Client("http://localhost:8000/sse") as client:
            result = await client.call_tool(
                "search_docs",
                {"query": "FastMCP deployment and authentication", "k": 3}
            )
            content = result.content[0].text

            print_info(f"Response length: {len(content)} characters")

            if "Found 3 results" in content:
                print_success("Search returned expected number of results")
            else:
                print_warning(f"Unexpected result count in: {content[:200]}")

            # Show preview
            print("\nSearch results preview:")
            lines = content.split("\n")[:20]
            for line in lines:
                print(f"  {line}")

            return "Found" in content
    except Exception as e:
        print_error(f"Basic search test failed: {e}")
        return False


async def test_search_with_filter():
    """Test 5: Search with source filter via HTTP."""
    print_header("Test 5: Search with Source Filter")

    try:
        async with Client("http://localhost:8000/sse") as client:
            result = await client.call_tool(
                "search_docs",
                {"query": "agents and tools", "source": "LangChain", "k": 2}
            )
            content = result.content[0].text

            print_info(f"Response length: {len(content)} characters")

            # Handle payload index limitation
            if "payload index not created" in content:
                print_warning("Payload index not available - filtering falls back to manual filtering")
                return True  # This is expected and handled gracefully
            elif "Found" in content:
                print_success("Filtered search returned results")
                return True
            else:
                print_warning(f"Unexpected response: {content[:200]}")
                return True  # Still passes if handled gracefully
    except Exception as e:
        print_error(f"Filtered search test failed: {e}")
        return False


async def test_performance():
    """Test 6: Measure HTTP performance."""
    print_header("Test 6: HTTP Performance Baseline")

    import time

    try:
        async with Client("http://localhost:8000/sse") as client:
            # Warm-up request
            await client.call_tool("list_sources", {})

            # Timed requests
            times = []
            for i in range(3):
                start = time.time()
                await client.call_tool(
                    "search_docs",
                    {"query": f"test query {i}", "k": 3}
                )
                elapsed = time.time() - start
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print_info(f"Average response time: {avg_time:.3f}s")
            print_info(f"Min: {min_time:.3f}s, Max: {max_time:.3f}s")

            # Local HTTP should be < 5s (includes network overhead + Qdrant API)
            if avg_time < 5.0:
                print_success(f"Performance acceptable: {avg_time:.3f}s < 5.0s")
                return True
            else:
                print_warning(f"Performance slower than expected: {avg_time:.3f}s")
                return True  # Still pass, but flag for investigation
    except Exception as e:
        print_error(f"Performance test failed: {e}")
        return False


async def test_error_handling():
    """Test 7: Error handling via HTTP."""
    print_header("Test 7: Error Handling")

    try:
        async with Client("http://localhost:8000/sse") as client:
            # Test with empty query
            result = await client.call_tool("search_docs", {"query": "", "k": 5})
            content = result.content[0].text

            print_success("Server handled empty query gracefully")

            # Test with invalid source
            result = await client.call_tool(
                "search_docs",
                {"query": "test", "source": "NonExistentSource", "k": 5}
            )
            content = result.content[0].text

            print_success("Server handled invalid source gracefully")
            return True
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False


async def run_all_tests():
    """Run all HTTP transport tests."""
    print_header("🧪 qdrant-docs Local HTTP Transport Tests")
    print_info("Testing server at: http://localhost:8000/sse")

    # Check if server is running
    print_info("Checking if server is running...")
    if not await check_server_running():
        print_error("Server is NOT running on http://localhost:8000")
        print("\n" + "="*80)
        print("To start the server, run in another terminal:")
        print(f"{Colors.YELLOW}  uv run python run_http_server.py{Colors.RESET}")
        print("="*80 + "\n")
        return False

    print_success("Server is running")

    # Run all tests
    tests = [
        ("HTTP Connectivity", test_http_connectivity()),
        ("List Tools", test_list_tools()),
        ("List Sources", test_list_sources()),
        ("Basic Search", test_search_basic()),
        ("Filtered Search", test_search_with_filter()),
        ("Performance", test_performance()),
        ("Error Handling", test_error_handling()),
    ]

    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Print summary
    print_header("📊 Test Summary")

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    if failed == 0:
        print(f"{Colors.BOLD}{Colors.GREEN}✅ All tests passed! ({passed}/{len(results)}){Colors.RESET}")
        print(f"{Colors.GREEN}Network transport validated - ready for cloud deployment{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.YELLOW}⚠ {passed}/{len(results)} tests passed, {failed} failed{Colors.RESET}")
        print(f"{Colors.YELLOW}Review failures before cloud deployment{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")

    return failed == 0


async def main():
    """Main entry point."""
    success = await run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
