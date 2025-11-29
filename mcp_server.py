#!/usr/bin/env python3
"""
Custom MCP server for Qdrant vector store with OpenAI embeddings.

This MCP server allows Claude Code to semantically search the llms-full-silver
collection using the same OpenAI text-embedding-3-small embeddings used during upload.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("qdrant-docs-search")

# Constants
COLLECTION_NAME = "llms-full-silver"
DEFAULT_K = 5  # Number of results to return


def get_vector_store() -> QdrantVectorStore:
    """
    Initialize and return Qdrant vector store with OpenAI embeddings.

    Returns:
        QdrantVectorStore: Configured vector store instance

    Raises:
        ValueError: If required environment variables are missing
    """
    qdrant_url = os.getenv("QDRANT_API_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not qdrant_url or not qdrant_key:
        raise ValueError(
            "QDRANT_API_URL and QDRANT_API_KEY must be set in environment variables"
        )

    if not openai_key:
        raise ValueError("OPENAI_API_KEY must be set in environment variables")

    # Initialize Qdrant client
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_key,
        prefer_grpc=True,
    )

    # Initialize OpenAI embeddings (same as upload)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_key,
        dimensions=1536,
    )

    # Create vector store
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )


@mcp.tool()
def search_docs(query: str, k: int = DEFAULT_K, source: Optional[str] = None) -> str:
    """
    Search documentation using semantic similarity.

    Use this tool to find relevant documentation pages based on natural language queries.
    Results are ranked by semantic similarity to your query.

    Args:
        query: Natural language search query (e.g., "How do I build a RAG agent?")
        k: Number of results to return (default: 5, max: 20)
        source: Optional filter by source name (e.g., "LangChain", "Anthropic", "Prefect")

    Returns:
        Formatted search results with titles, sources, URLs, and content previews
    """
    # Validate k parameter
    k = max(1, min(k, 20))  # Clamp between 1 and 20

    try:
        vector_store = get_vector_store()

        # Build filter if source specified
        filter_dict = None
        if source:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            filter_dict = Filter(
                must=[
                    FieldCondition(
                        key="metadata.source_name", match=MatchValue(value=source)
                    )
                ]
            )

        # Perform search
        try:
            results = vector_store.similarity_search(query, k=k, filter=filter_dict)
        except Exception as filter_error:
            # If filter fails (e.g., no index), fall back to unfiltered search
            if source and "Index required" in str(filter_error):
                # Perform unfiltered search and manually filter results
                results = vector_store.similarity_search(query, k=k * 3)  # Get more results
                # Filter in Python
                results = [
                    doc for doc in results
                    if doc.metadata.get("source_name") == source
                ][:k]

                if not results:
                    return f"No results found for query '{query}' in source '{source}'. Note: payload index not created for optimal filtering."
            else:
                raise

        if not results:
            return f"No results found for query: '{query}'"

        # Format results
        output = [f"Found {len(results)} results for: '{query}'\n"]

        for i, doc in enumerate(results, 1):
            metadata = doc.metadata
            output.append(f"\n{'='*80}")
            output.append(f"Result {i}/{len(results)}")
            output.append(f"{'='*80}")
            output.append(f"Title: {metadata.get('title', 'Untitled')}")
            output.append(f"Source: {metadata.get('source_name', 'Unknown')}")
            output.append(f"URL: {metadata.get('source_url', 'N/A')}")
            output.append(f"Doc ID: {metadata.get('doc_id', 'N/A')}")
            output.append(f"\nContent Preview ({len(doc.page_content)} chars total):")
            output.append("-" * 80)

            # Include preview (first 1000 chars) to keep responses manageable
            # Claude Code can request full content if needed
            preview_length = 1000
            if len(doc.page_content) > preview_length:
                output.append(doc.page_content[:preview_length] + "...")
                output.append(f"\n[Truncated. Full content: {len(doc.page_content)} chars]")
            else:
                output.append(doc.page_content)

        return "\n".join(output)

    except Exception as e:
        return f"Error during search: {str(e)}"


@mcp.tool()
def list_sources() -> str:
    """
    List all available documentation sources in the vector store.

    Use this tool to see which documentation sources are available for searching.

    Returns:
        List of available sources with document counts
    """
    sources = {
        "Anthropic": 932,
        "LangChain": 506,
        "Prefect": 767,
        "FastMCP": 175,
        "McpProtocol": 44,
        "PydanticAI": 127,
        "Zep": 119,
    }

    output = ["Available Documentation Sources:\n"]
    output.append(f"{'Source':<15} {'Documents':<10}")
    output.append("-" * 30)

    for source, count in sorted(sources.items()):
        output.append(f"{source:<15} {count:<10}")

    output.append("-" * 30)
    output.append(f"{'TOTAL':<15} {sum(sources.values()):<10}")

    output.append(
        "\n\nUse the 'source' parameter in search_docs() to filter by a specific source."
    )
    output.append("Example: search_docs('authentication', source='Anthropic')")

    return "\n".join(output)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
