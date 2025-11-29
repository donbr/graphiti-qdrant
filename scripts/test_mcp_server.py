#!/usr/bin/env python3
"""
Test the MCP server locally before adding to Claude Code.

This script tests the MCP server's search functionality without using the MCP protocol,
allowing you to verify that search is working correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import mcp_server
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_vector_store():
    """Test that we can initialize the vector store."""
    print("=" * 70)
    print("Testing Vector Store Initialization")
    print("=" * 70)

    try:
        from mcp_server import get_vector_store

        vector_store = get_vector_store()
        print("✓ Vector store initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize vector store: {e}")
        return False


def test_basic_search():
    """Test basic semantic search."""
    print("\n" + "=" * 70)
    print("Testing Basic Search")
    print("=" * 70)

    try:
        from mcp_server import search_docs

        query = "How do I build a RAG agent?"
        print(f"\nQuery: '{query}'")
        print("-" * 70)

        # Call the underlying function (search_docs is a FunctionTool)
        result = search_docs.fn(query, k=3)
        print(result)

        if "Error" in result:
            print("\n✗ Search returned an error")
            return False

        print("\n✓ Basic search completed successfully")
        return True
    except Exception as e:
        print(f"\n✗ Basic search failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_filtered_search():
    """Test search with source filtering."""
    print("\n" + "=" * 70)
    print("Testing Filtered Search")
    print("=" * 70)

    try:
        from mcp_server import search_docs

        query = "API authentication"
        source = "Anthropic"
        print(f"\nQuery: '{query}' (source: {source})")
        print("-" * 70)

        # Call the underlying function (search_docs is a FunctionTool)
        result = search_docs.fn(query, k=3, source=source)
        print(result)

        if "Error" in result:
            print("\n✗ Filtered search returned an error")
            return False

        # Verify all results are from the specified source
        if source in result:
            print(f"\n✓ Filtered search completed successfully (found {source} docs)")
            return True
        else:
            print(f"\n⚠ Results may not be filtered correctly")
            return False

    except Exception as e:
        print(f"\n✗ Filtered search failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_list_sources():
    """Test listing available sources."""
    print("\n" + "=" * 70)
    print("Testing List Sources")
    print("=" * 70)

    try:
        from mcp_server import list_sources

        # Call the underlying function (list_sources is a FunctionTool)
        result = list_sources.fn()
        print(result)

        if "Available Documentation Sources" in result:
            print("\n✓ List sources completed successfully")
            return True
        else:
            print("\n✗ List sources returned unexpected format")
            return False

    except Exception as e:
        print(f"\n✗ List sources failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("MCP Server Test Suite")
    print("=" * 70)

    # Check environment variables
    print("\nEnvironment Variables:")
    print(f"  QDRANT_API_URL: {os.getenv('QDRANT_API_URL', 'NOT SET')}")
    print(
        f"  QDRANT_API_KEY: {'SET' if os.getenv('QDRANT_API_KEY') else 'NOT SET'}"
    )
    print(
        f"  OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}"
    )
    print()

    # Run tests
    tests = [
        ("Vector Store Initialization", test_vector_store),
        ("Basic Search", test_basic_search),
        ("Filtered Search", test_filtered_search),
        ("List Sources", test_list_sources),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:<40} {status}")
        all_passed = all_passed and passed

    print("=" * 70)

    if all_passed:
        print("\n✓ All tests passed! MCP server is ready to use with Claude Code.")
        print("\nNext steps:")
        print("1. Add the server to Claude Code:")
        print('   claude mcp add qdrant-docs -e QDRANT_API_URL="..." -e QDRANT_API_KEY="..." -e OPENAI_API_KEY="..." -- uv run python mcp_server.py')
        print("2. Verify with: claude mcp list")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues before using with Claude Code.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
