# Qdrant Upload Scripts

This directory contains scripts for uploading documentation pages to Qdrant Cloud.

## Files

- **`upload_to_qdrant.py`** - Main upload script
- **`embedding_config.py`** - OpenAI embedding configuration
- **`langchain-qdrant-notes.md`** - Reference documentation

## Prerequisites

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment variables:**
   Copy `.env.example` to `.env` and add your API keys:
   ```bash
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_API_URL=https://xxxxx.us-west-1-0.aws.cloud.qdrant.io:6333
   OPENAI_API_KEY=sk-proj-your_openai_api_key
   ```

## Usage

### Test Configuration

Test that embeddings are working:
```bash
uv run python scripts/embedding_config.py
```

### Dry Run (Validate Without Uploading)

```bash
uv run python scripts/upload_to_qdrant.py --dry-run
```

### Upload All Documents

Upload all 2,670 documents from all 7 sources:
```bash
uv run python scripts/upload_to_qdrant.py
```

### Upload Specific Sources

Upload only specific documentation sources:
```bash
uv run python scripts/upload_to_qdrant.py --sources LangChain Anthropic
```

### Custom Batch Size and Workers

Adjust batch size and parallel workers:
```bash
uv run python scripts/upload_to_qdrant.py --batch-size 200 --workers 2
```

### Custom Collection Name

Upload to a different collection:
```bash
uv run python scripts/upload_to_qdrant.py --collection my-custom-collection
```

## Command-Line Options

```
usage: upload_to_qdrant.py [-h] [--sources SOURCES [SOURCES ...]]
                           [--batch-size BATCH_SIZE] [--workers WORKERS]
                           [--dry-run] [--collection COLLECTION]

Upload documentation pages to Qdrant Cloud

options:
  -h, --help            show this help message and exit
  --sources SOURCES [SOURCES ...]
                        Filter to specific sources (e.g., --sources LangChain Anthropic)
  --batch-size BATCH_SIZE
                        Number of documents per batch (default: 100)
  --workers WORKERS     Number of parallel workers (default: 4)
  --dry-run             Validate configuration without uploading
  --collection COLLECTION
                        Qdrant collection name (default: llms-full-silver)
```

## Expected Performance

- **Total Documents**: 2,670
- **Embedding Time**: ~2-5 minutes (OpenAI API)
- **Upload Time**: ~10-20 seconds
- **Total Time**: ~5-10 minutes
- **Cost**: ~$0.25-0.50 for initial upload (one-time)

## Output

The script will:
1. Create the collection `llms-full-silver` if it doesn't exist
2. Load all JSON documents from `data/interim/pages/`
3. Add metadata from `data/interim/pages/manifest.json`
4. Upload documents in batches with progress tracking
5. Save upload manifest to `data/processed/upload_manifest.json`

## Metadata Schema

Each document is uploaded with the following metadata:

```python
{
    "page_content": "Full document text...",  # No chunking
    "metadata": {
        "title": "Page Title",
        "source_url": "https://docs.example.com/...",
        "content_length": 4627,
        "source_name": "LangChain",
        "total_pages": 506,
        "avg_content_length": 12683,
        "doc_id": "LangChain_0350",
        "page_number": "0350"
    }
}
```

## Available Sources

- **LangChain** (506 documents)
- **Anthropic** (932 documents)
- **Prefect** (767 documents)
- **FastMCP** (175 documents)
- **McpProtocol** (44 documents)
- **PydanticAI** (127 documents)
- **Zep** (119 documents)

## Troubleshooting

### Connection Errors

If you get connection errors to Qdrant:
- Verify `QDRANT_API_URL` and `QDRANT_API_KEY` in `.env`
- Check that your Qdrant Cloud instance is running
- Try reducing `--workers` to 2

### OpenAI Rate Limits

If you hit OpenAI rate limits:
- Reduce `--batch-size` to 50
- Reduce `--workers` to 2
- Wait a few minutes between retries

### Missing Environment Variables

```
ValueError: OPENAI_API_KEY not found in environment variables
```

Solution: Add `OPENAI_API_KEY` to your `.env` file

## Next Steps

After uploading, you can:

1. **Query the collection** using the Qdrant web UI
2. **Build a RAG application** using the uploaded vectors
3. **Use gpt-4o-mini or gpt-4.1-mini** for semantic search queries

## Example: Semantic Search

```python
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
import os

# Initialize
client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = QdrantVectorStore(
    client=client,
    collection_name="llms-full-silver",
    embedding=embeddings,
)

# Search
results = vector_store.similarity_search(
    "How do I build a RAG agent with LangChain?",
    k=5
)

for doc in results:
    print(f"Title: {doc.metadata['title']}")
    print(f"Source: {doc.metadata['source_url']}")
    print(f"Content: {doc.page_content[:200]}...")
    print("-" * 80)
```
