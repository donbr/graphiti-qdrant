# Qdrant

> [Qdrant](https://qdrant.tech/documentation/) (read: quadrant) is a vector similarity search engine.
> It provides a production-ready service with a convenient API to store, search, and manage
> points - vectors with an additional payload. `Qdrant` is tailored to extended filtering support.

## Installation and Setup

Install the Python partner package:

<CodeGroup>
  ```bash pip theme={null}
  pip install langchain-qdrant
  ```

  ```bash uv theme={null}
  uv add langchain-qdrant
  ```
</CodeGroup>

## Embedding models

### FastEmbedSparse

```python  theme={null}
from langchain_qdrant import FastEmbedSparse
```

### SparseEmbeddings

```python  theme={null}
from langchain_qdrant import SparseEmbeddings
```

## Vector Store

There exists a wrapper around `Qdrant` indexes, allowing you to use it as a vectorstore,
whether for semantic search or example selection.

To import this vectorstore:

```python  theme={null}
from langchain_qdrant import QdrantVectorStore
```

For a more detailed walkthrough of the Qdrant wrapper, see [this notebook](/oss/python/integrations/vectorstores/qdrant)

***

<Callout icon="pen-to-square" iconType="regular">
  [Edit the source of this page on GitHub.](https://github.com/langchain-ai/docs/edit/main/src/oss/python/integrations/providers/qdrant.mdx)
</Callout>

<Tip icon="terminal" iconType="regular">
  [Connect these docs programmatically](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
</Tip>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.langchain.com/llms.txt


```python
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

vector_size = len(embeddings.embed_query("sample text"))

if not client.collection_exists("test"):
    client.create_collection(
        collection_name="test",
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
vector_store = QdrantVectorStore(
    client=client,
    collection_name="test",
    embedding=embeddings,
)
```

