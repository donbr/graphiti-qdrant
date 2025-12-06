# Vector Database Refresh Guide

Best practices for dropping and replacing llms-full.txt content in Qdrant.

## Table of Contents
1. [When to Refresh](#when-to-refresh)
2. [Refresh Strategies](#refresh-strategies)
3. [Safe Refresh Procedures](#safe-refresh-procedures)
4. [Rollback Strategies](#rollback-strategies)
5. [Testing & Validation](#testing--validation)
6. [Common Pitfalls](#common-pitfalls)

---

## When to Refresh

### Full Collection Drop & Replace
Use when:
- ✅ Major documentation version updates (e.g., API v1 → v2)
- ✅ Changing embedding model (e.g., text-embedding-3-small → text-embedding-3-large)
- ✅ Changing vector dimensions or distance metrics
- ✅ Schema changes (adding/removing metadata fields for all sources)
- ✅ Collection becomes corrupted or inconsistent

### Incremental Updates (Source-Level)
Use when:
- ✅ Adding a new documentation source (e.g., adding Temporal)
- ✅ Updating a single source's documentation
- ✅ Fixing data quality issues in one source
- ✅ Testing new splitting strategies on one source

**Example**: Temporal hierarchy metadata update (this session)
```bash
# Delete only Temporal documents
uv run python -c "..." # scroll + delete by source_name

# Re-upload only Temporal
uv run python scripts/upload_to_qdrant.py --sources Temporal
```

---

## Refresh Strategies

### Strategy 1: Drop Entire Collection
**Use**: When changing embedding model or vector dimensions

```python
#!/usr/bin/env python3
"""Drop entire collection and recreate from scratch."""
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True,
)

# 1. Drop collection
if client.collection_exists("llms-full-silver"):
    client.delete_collection("llms-full-silver")
    print("✓ Collection dropped")

# 2. Upload will auto-create collection
# Run: uv run python scripts/upload_to_qdrant.py
```

**Pros**: Clean slate, no residual data
**Cons**: Downtime, must re-upload everything

---

### Strategy 2: Delete by Source Filter
**Use**: When updating specific documentation sources

```python
#!/usr/bin/env python3
"""Delete documents for specific source(s)."""
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True,
)

# Scroll and collect IDs (required if no payload index on source_name)
source_to_delete = "Temporal"
ids_to_delete = []
offset = None

while True:
    result = client.scroll(
        collection_name="llms-full-silver",
        limit=100,
        offset=offset,
        with_payload=["metadata.source_name"],
        with_vectors=False,
    )

    points, next_offset = result

    for point in points:
        if point.payload.get("metadata", {}).get("source_name") == source_to_delete:
            ids_to_delete.append(point.id)

    if next_offset is None:
        break
    offset = next_offset

# Delete by IDs
if ids_to_delete:
    client.delete(
        collection_name="llms-full-silver",
        points_selector=ids_to_delete,
    )
    print(f"✓ Deleted {len(ids_to_delete)} documents from {source_to_delete}")

# Then re-upload
# Run: uv run python scripts/upload_to_qdrant.py --sources Temporal
```

**Pros**: No downtime for other sources, surgical updates
**Cons**: Requires scroll if no payload index

---

### Strategy 3: Blue-Green Deployment
**Use**: Production systems requiring zero downtime

```python
#!/usr/bin/env python3
"""Blue-green deployment with collection swap."""
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True,
)

# 1. Create new collection with timestamp
new_collection = "llms-full-silver-20251205"

# 2. Upload to new collection
# Run: uv run python scripts/upload_to_qdrant.py --collection llms-full-silver-20251205

# 3. Test new collection
# Run tests against new_collection

# 4. Swap collections (update MCP server config)
# Update mcp_server.py: COLLECTION_NAME = "llms-full-silver-20251205"

# 5. Drop old collection after verification
# client.delete_collection("llms-full-silver")
```

**Pros**: Zero downtime, easy rollback
**Cons**: Requires 2x storage temporarily, config changes

---

### Strategy 4: Snapshot Collections
**Use**: For rollback capability

```python
#!/usr/bin/env python3
"""Create snapshot before major changes."""
from qdrant_client import QdrantClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True,
)

# Create collection alias for snapshots
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
snapshot_name = f"llms-full-silver-snapshot-{timestamp}"

# Qdrant Cloud: Use collection snapshots API
# https://qdrant.tech/documentation/concepts/snapshots/

# Local alternative: Create collection alias
# client.create_alias(
#     collection_name="llms-full-silver",
#     alias_name=snapshot_name,
# )
```

**Note**: Qdrant Cloud offers [snapshot capabilities](https://qdrant.tech/documentation/cloud/backups/)

---

## Safe Refresh Procedures

### Pre-Refresh Checklist
- [ ] **Backup**: Create snapshot or note collection state
- [ ] **Test locally**: Run pipeline on test collection first
- [ ] **Verify data**: Check split output in `data/interim/pages/`
- [ ] **Document counts**: Record current counts for validation
- [ ] **Embedding model**: Confirm same model/dimensions
- [ ] **API keys**: Verify QDRANT_API_KEY and OPENAI_API_KEY in .env

### Post-Refresh Validation
```bash
# 1. Verify document counts
uv run python -c "
from mcp_server import list_sources
result = list_sources.fn()
print(result)
"

# 2. Test semantic search
uv run python -c "
from mcp_server import get_vector_store
vs = get_vector_store()
results = vs.similarity_search('test query', k=3)
print(f'Found {len(results)} results')
for doc in results:
    print(f\"  - {doc.metadata.get('source_name')}: {doc.metadata.get('title')}\")
"

# 3. Run full test suite
uv run pytest tests/test_mcp_server.py -v

# 4. Test MCP server via Claude Code
# > Search qdrant-docs for "test query"
# > List sources from qdrant-docs
```

---

## Rollback Strategies

### Rollback from Blue-Green Deployment
```python
# Simply switch back to old collection
# Update mcp_server.py: COLLECTION_NAME = "llms-full-silver-OLD"
# Restart MCP server
```

### Rollback from Full Drop
```bash
# No automatic rollback - must re-upload from data/interim/pages/

# If you have backup manifests:
uv run python scripts/upload_to_qdrant.py
```

**💡 Tip**: Always keep `data/interim/pages/` intact as your source of truth for fast re-uploads

---

## Testing & Validation

### Test Pipeline Before Production

1. **Use a test collection**:
```bash
# Upload to test collection
uv run python scripts/upload_to_qdrant.py \
  --collection llms-full-test

# Test against test collection
# Update mcp_server.py temporarily: COLLECTION_NAME = "llms-full-test"
uv run pytest tests/test_mcp_server.py -v
```

2. **Validate data quality**:
```bash
# Check split output before uploading
ls data/interim/pages/Temporal/ | wc -l  # Should be 2217 (2216 + manifest)
cat data/interim/pages/Temporal/manifest.json | jq '.page_count'

# Verify hierarchy metadata in sample pages
cat data/interim/pages/Temporal/0001_*.json | jq '{title, header_level, section_path, parent_title}'
```

3. **Compare before/after**:
```python
# Before refresh
old_counts = {"Temporal": 2216, "LangChain": 506, ...}

# After refresh
from mcp_server import list_sources
new_result = list_sources.fn()
# Compare counts
```

---

## Common Pitfalls

### ❌ Pitfall 1: Deleting with Filter (No Payload Index)
**Error**: `Index required but not found for "metadata.source_name"`

**Solution**: Use scroll + delete by IDs (see Strategy 2 above)

---

### ❌ Pitfall 2: Changing Embedding Model Mid-Stream
**Problem**: Mixing vectors from different embedding models breaks semantic search

**Solution**: Always drop entire collection when changing embedding model

---

### ❌ Pitfall 3: Not Updating Hard-Coded Counts
**Problem**: Stale document counts in MCP server

**Solution**: ✅ **FIXED** - Now uses dynamic count retrieval

---

### ❌ Pitfall 4: Forgetting to Re-Split After Code Changes
**Problem**: Upload script reads old JSON files, doesn't reflect code changes

**Solution**: Always re-run split script after modifying splitting logic
```bash
# After changing split_llms_pages.py
uv run python scripts/split_llms_pages.py  # Re-generate JSON files
uv run python scripts/upload_to_qdrant.py --sources Temporal  # Upload
```

---

### ❌ Pitfall 5: No Backup Before Major Changes
**Problem**: Cannot rollback if something goes wrong

**Solution**: Use blue-green deployment or create snapshots

---

## Quick Reference

### Full Refresh (Drop & Replace All)
```bash
# 1. Drop collection (via Python script or Qdrant UI)
# 2. Re-download documentation
uv run python scripts/download_llms_raw.py

# 3. Re-split into pages
uv run python scripts/split_llms_pages.py

# 4. Upload (will auto-create collection)
uv run python scripts/upload_to_qdrant.py

# 5. Validate
uv run pytest tests/test_mcp_server.py -v
```

### Incremental Refresh (Single Source)
```bash
# 1. Re-download single source
# (Modify download script or manually update data/raw/Source/)

# 2. Re-split single source
uv run python scripts/split_llms_pages.py
# (Processes all sources, but only changed source will differ)

# 3. Delete old source documents from Qdrant
# (Use scroll + delete script - see Strategy 2)

# 4. Upload single source
uv run python scripts/upload_to_qdrant.py --sources Temporal

# 5. Validate
uv run pytest tests/test_mcp_server.py::test_search_docs_various_sources -v
```

### Emergency Rollback
```bash
# If using blue-green:
# 1. Update COLLECTION_NAME in mcp_server.py to old collection
# 2. Restart MCP server

# If dropped collection:
# 1. Re-run upload script from data/interim/pages/
uv run python scripts/upload_to_qdrant.py
```

---

## Best Practices Summary

1. ✅ **Always test on a separate collection first**
2. ✅ **Keep `data/interim/pages/` as source of truth**
3. ✅ **Use incremental updates for single sources**
4. ✅ **Use blue-green for zero-downtime production updates**
5. ✅ **Validate counts and search quality after refresh**
6. ✅ **Run full test suite after major changes**
7. ✅ **Document what changed in git commit messages**
8. ✅ **Monitor MCP server performance after refresh**

---

## Related Documentation

- [upload_to_qdrant.py](../scripts/upload_to_qdrant.py) - Upload script with `--sources` filter
- [split_llms_pages.py](../scripts/split_llms_pages.py) - Splitting strategies
- [mcp_server.py](../mcp_server.py) - MCP server with dynamic count retrieval
- [Qdrant Documentation](https://qdrant.tech/documentation/) - Official Qdrant docs
- [Qdrant Snapshots](https://qdrant.tech/documentation/concepts/snapshots/) - Backup strategies
