#!/usr/bin/env python3
"""
Cloud deployment validation test for qdrant-docs FastMCP server.

This script validates the cloud deployment by:
1. Testing connectivity to the cloud endpoint
2. Running the same tests as local HTTP tests
3. Comparing performance between local and cloud
4. Verifying all tools work identically

Usage:
    uv run python test_cloud_deployment.py

Expected cloud URL: https://qdrant-docs.fastmcp.app/mcp
"""
import asyncio
import time
from typing import List, Tuple

from fastmcp import Client


# ANSI color codes
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


CLOUD_URL = "https://qdrant-docs.fastmcp.app/mcp"


async def test_cloud_connectivity():
    """Test 1: Cloud endpoint connectivity."""
    print_header("Test 1: Cloud Connectivity")

    try:
        async with Client(CLOUD_URL) as client:
            result = await client.ping()
            if result:
                print_success(f"Cloud server ping: {result}")
                return True
            else:
                print_error("Cloud server did not respond to ping")
                return False
    except Exception as e:
        print_error(f"Cloud connectivity failed: {e}")
        return False


async def test_cloud_tools():
    """Test 2: Cloud tools availability."""
    print_header("Test 2: Cloud Tools")

    try:
        async with Client(CLOUD_URL) as client:
            tools = await client.list_tools()
            print_success(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:60]}...")
            return len(tools) == 2
    except Exception as e:
        print_error(f"List tools failed: {e}")
        return False


async def test_cloud_list_sources():
    """Test 3: Cloud list_sources tool."""
    print_header("Test 3: List Sources (Cloud)")

    try:
        async with Client(CLOUD_URL) as client:
            result = await client.call_tool("list_sources", {})
            content = result.content[0].text

            sources = ["Anthropic", "LangChain", "Prefect", "FastMCP", "PydanticAI"]
            found = [s for s in sources if s in content]

            print_success(f"Found {len(found)}/{len(sources)} expected sources")
            print("\nSources preview:")
            print(content[:300])
            return len(found) >= 4
    except Exception as e:
        print_error(f"List sources failed: {e}")
        return False


async def test_cloud_search():
    """Test 4: Cloud semantic search."""
    print_header("Test 4: Semantic Search (Cloud)")

    try:
        async with Client(CLOUD_URL) as client:
            result = await client.call_tool(
                "search_docs",
                {"query": "FastMCP cloud deployment and authentication", "k": 3}
            )
            content = result.content[0].text

            print_info(f"Response length: {len(content)} characters")

            if "Found 3 results" in content:
                print_success("Search returned expected number of results")
            else:
                print_warning(f"Unexpected result count in: {content[:200]}")

            print("\nSearch results preview:")
            lines = content.split("\n")[:15]
            for line in lines:
                print(f"  {line}")

            return "Found" in content
    except Exception as e:
        print_error(f"Search failed: {e}")
        return False


async def test_cloud_performance():
    """Test 5: Cloud performance comparison."""
    print_header("Test 5: Cloud Performance")

    try:
        async with Client(CLOUD_URL) as client:
            # Warm-up
            await client.call_tool("list_sources", {})

            # Timed requests
            times = []
            for i in range(3):
                start = time.time()
                await client.call_tool(
                    "search_docs",
                    {"query": f"FastMCP performance test {i}", "k": 3}
                )
                elapsed = time.time() - start
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print_info(f"Average response time: {avg_time:.3f}s")
            print_info(f"Min: {min_time:.3f}s, Max: {max_time:.3f}s")

            # Compare to local baseline (2.4s from Week 1)
            local_baseline = 2.4
            print_info(f"Local baseline: {local_baseline:.3f}s")

            if avg_time < local_baseline:
                print_success(f"Cloud is faster: {avg_time:.3f}s < {local_baseline:.3f}s")
            elif avg_time < local_baseline * 1.2:
                print_warning(f"Cloud is slightly slower: {avg_time:.3f}s vs {local_baseline:.3f}s")
            else:
                print_error(f"Cloud is significantly slower: {avg_time:.3f}s vs {local_baseline:.3f}s")

            # Target from strategy: < 2s
            target = 2.0
            if avg_time < target:
                print_success(f"Cloud meets target: {avg_time:.3f}s < {target:.3f}s")
            else:
                print_warning(f"Cloud exceeds target: {avg_time:.3f}s > {target:.3f}s")

            return avg_time < 5.0  # Acceptable threshold
    except Exception as e:
        print_error(f"Performance test failed: {e}")
        return False


async def test_cloud_error_handling():
    """Test 6: Cloud error handling."""
    print_header("Test 6: Error Handling (Cloud)")

    try:
        async with Client(CLOUD_URL) as client:
            # Test empty query
            result = await client.call_tool("search_docs", {"query": "", "k": 5})
            print_success("Cloud handled empty query gracefully")

            # Test invalid source
            result = await client.call_tool(
                "search_docs",
                {"query": "test", "source": "NonExistent", "k": 5}
            )
            print_success("Cloud handled invalid source gracefully")

            return True
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False


async def run_all_cloud_tests():
    """Run all cloud deployment validation tests."""
    print_header("🌐 FastMCP Cloud Deployment Validation")
    print_info(f"Testing cloud endpoint: {CLOUD_URL}")
    print_info("This validates Week 2 - Phase 3 (Cloud Preview Deployment)")

    tests = [
        ("Cloud Connectivity", test_cloud_connectivity()),
        ("Cloud Tools", test_cloud_tools()),
        ("List Sources", test_cloud_list_sources()),
        ("Semantic Search", test_cloud_search()),
        ("Performance", test_cloud_performance()),
        ("Error Handling", test_cloud_error_handling()),
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
    print_header("📊 Cloud Deployment Test Summary")

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    if failed == 0:
        print(f"{Colors.BOLD}{Colors.GREEN}✅ All cloud tests passed! ({passed}/{len(results)}){Colors.RESET}")
        print(f"{Colors.GREEN}Cloud deployment validated - ready for production{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.YELLOW}⚠ {passed}/{len(results)} tests passed, {failed} failed{Colors.RESET}")
        print(f"{Colors.YELLOW}Review failures before production promotion{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")

    # Comparison summary
    print_header("📈 Local vs Cloud Comparison")
    print(f"Local HTTP baseline: 2.4s avg (Week 1)")
    print(f"Cloud target: < 2s (Strategy)")
    print(f"Cloud actual: Run performance test to see")
    print("\nBoth servers available:")
    print(f"  - {Colors.GREEN}qdrant-docs{Colors.RESET} (cloud, HTTP)")
    print(f"  - {Colors.BLUE}qdrant-docs-local{Colors.RESET} (local, stdio)")

    return failed == 0


async def main():
    """Main entry point."""
    import sys
    success = await run_all_cloud_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
