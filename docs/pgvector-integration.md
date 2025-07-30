# HACS pgvector Integration

HACS now supports **pgvector** for advanced vector database operations, enabling semantic search, similarity matching, and AI-powered retrieval-augmented generation (RAG) capabilities directly within PostgreSQL.

## Overview

The pgvector integration provides:

- **Vector embeddings storage** in PostgreSQL using the pgvector extension
- **Similarity search** with multiple distance metrics (cosine, L2, inner product)
- **Hybrid search** combining vector similarity with text search and metadata filtering
- **Batch operations** for efficient data processing
- **Complete integration** with HACS tools and MCP server

## Prerequisites

1. **PostgreSQL with pgvector**: The database must have the pgvector extension installed
2. **Python dependencies**: Install pgvector Python package
3. **HACS database migrations**: Run migrations to enable vector support

### Installation

1. Install pgvector Python package:
```bash
pip install pgvector
```

2. Enable pgvector in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Run HACS migrations (automatically includes pgvector setup):
```bash
./scripts/run-migrations.sh
```

## Architecture

### Components

- **`HACSVectorStore`**: Core vector database class in `hacs-persistence`
- **HACS Tools**: High-level functions for vector operations in `hacs-tools`
- **MCP Integration**: Vector tools available via the HACS MCP server
- **Database Schema**: `knowledge_items` table with vector embeddings support

### Database Schema

The `knowledge_items` table includes:

```sql
CREATE TABLE knowledge_items (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- Vector embeddings (default OpenAI dimensions)
    metadata JSONB DEFAULT '{}',
    source TEXT,
    content_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    full_resource JSONB NOT NULL
);

-- Vector similarity index for fast searches
CREATE INDEX idx_knowledge_items_embedding
ON knowledge_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Usage

### 1. Direct Vector Store API

```python
from hacs_persistence import HACSVectorStore

# Initialize vector store
vector_store = HACSVectorStore(
    database_url="postgresql://user:pass@localhost/hacs",
    embedding_dimension=1536  # Match your embedding model
)

# Store an embedding
embedding_id = vector_store.store_embedding(
    content="Patient shows significant improvement after treatment",
    embedding=[0.1, 0.2, 0.3, ...],  # 1536-dimensional vector
    metadata={
        "type": "clinical_note",
        "patient_id": "P12345",
        "date": "2024-01-15"
    },
    source="clinical_notes_2024"
)

# Similarity search
results = vector_store.similarity_search(
    query_embedding=[0.1, 0.2, 0.3, ...],  # Query vector
    top_k=5,
    distance_metric="cosine",
    metadata_filter={"type": "clinical_note"}
)

# Hybrid search (vector + text)
results = vector_store.hybrid_search(
    query_embedding=[0.1, 0.2, 0.3, ...],
    text_query="diabetes treatment",
    top_k=5,
    metadata_filter={"type": "clinical_note"},
    source_filter="medical_literature"
)
```

### 2. HACS Tools Integration

```python
from hacs_tools.tools import (
    store_embedding,
    vector_similarity_search,
    vector_hybrid_search,
    get_vector_collection_stats
)

# Store an embedding
result = store_embedding(
    content="Patient diagnosis and treatment plan",
    embedding=[0.1, 0.2, 0.3, ...],  # Your embedding vector
    metadata={"type": "diagnosis", "patient_id": "P123"},
    source="ehr_system"
)

if result.success:
    print(f"Stored embedding: {result.data['embedding_id']}")

# Search for similar content
search_result = vector_similarity_search(
    query_embedding=[0.1, 0.2, 0.3, ...],
    top_k=3,
    distance_metric="cosine",
    metadata_filter={"type": "diagnosis"}
)

for item in search_result.data["results"]:
    print(f"Similarity: {item['similarity']:.3f}")
    print(f"Content: {item['content'][:100]}...")
```

### 3. MCP Server Usage

The vector tools are available through the HACS MCP server:

```python
import asyncio
from hacs_utils.mcp import HACSmcpClient

async def use_vector_search():
    client = HACSmcpClient("http://localhost:8000")

    # Store embedding via MCP
    result = await client.call_tool("store_embedding", {
        "content": "Medical research on diabetes treatment",
        "embedding": [0.1, 0.2, 0.3] * 512,  # 1536-dim vector
        "metadata": {"type": "research", "topic": "diabetes"},
        "source": "medical_journals"
    })

    # Search via MCP
    search_result = await client.call_tool("vector_similarity_search", {
        "query_embedding": [0.1, 0.2, 0.3] * 512,
        "top_k": 5,
        "distance_metric": "cosine",
        "metadata_filter": {"type": "research"}
    })
```

## Distance Metrics

pgvector supports three distance metrics:

1. **Cosine Distance** (`cosine`): Best for normalized embeddings
   - Operator: `<=>`
   - Range: 0-2 (lower = more similar)
   - Use case: Text embeddings, semantic similarity

2. **L2 Distance** (`l2`): Euclidean distance
   - Operator: `<->`
   - Range: 0-∞ (lower = more similar)
   - Use case: When absolute magnitude matters

3. **Inner Product** (`inner_product`): Dot product (negative)
   - Operator: `<#>`
   - Range: -∞ to ∞ (higher = more similar)
   - Use case: When embeddings include magnitude information

## Performance Optimization

### Indexing

pgvector provides two index types:

1. **IVFFlat** (default): Good for most use cases
```sql
CREATE INDEX ON knowledge_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

2. **HNSW**: Better for high-dimensional data and real-time queries
```sql
CREATE INDEX ON knowledge_items USING hnsw (embedding vector_cosine_ops);
```

### Best Practices

1. **Choose the right embedding dimension**: Match your model (1536 for OpenAI text-embedding-3-small)
2. **Use appropriate index parameters**:
   - IVFFlat: `lists` should be roughly `rows/1000`
   - HNSW: Generally works well with defaults
3. **Batch operations**: Use `store_embeddings_batch()` for multiple embeddings
4. **Metadata filtering**: Use JSONB indexes for frequently filtered metadata fields

## Advanced Features

### Hybrid Search

Combine vector similarity with PostgreSQL's full-text search:

```python
results = vector_store.hybrid_search(
    query_embedding=query_vector,
    text_query="diabetes insulin treatment",  # Full-text search
    metadata_filter={"category": "medical"},
    date_range=(start_date, end_date),
    top_k=10
)
```

### Metadata Filtering

Filter results using JSONB operations:

```python
results = vector_store.similarity_search(
    query_embedding=query_vector,
    metadata_filter={
        "patient_age": "65",
        "condition": "diabetes",
        "treatment_type": "medication"
    }
)
```

### Collection Statistics

Monitor your vector collection:

```python
stats = vector_store.get_collection_stats()
print(f"Total embeddings: {stats['total_embeddings']}")
print(f"Unique sources: {stats['unique_sources']}")
print(f"Average content length: {stats['avg_content_length']}")
```

## Integration with AI/ML Workflows

### RAG (Retrieval-Augmented Generation)

```python
def rag_query(question: str, embedding_model, llm_model):
    # Generate query embedding
    query_embedding = embedding_model.encode(question)

    # Retrieve relevant context
    results = vector_similarity_search(
        query_embedding=query_embedding,
        top_k=5,
        distance_metric="cosine"
    )

    # Build context for LLM
    context = "\n\n".join([item["content"] for item in results.data["results"]])

    # Generate response with context
    prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    response = llm_model.generate(prompt)

    return response, results.data["results"]
```

### Document Embedding Pipeline

```python
def embed_documents(documents: List[str], embedding_model):
    """Embed and store a collection of documents."""
    embeddings = embedding_model.encode(documents)

    # Batch store embeddings
    items = []
    for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
        items.append({
            "content": doc,
            "embedding": embedding.tolist(),
            "metadata": {"doc_index": i, "source": "document_batch"},
            "content_hash": hashlib.md5(doc.encode()).hexdigest()
        })

    vector_store = HACSVectorStore(database_url=DATABASE_URL)
    stored_ids = vector_store.store_embeddings_batch(items)

    return stored_ids
```

## Testing

Use the provided test script to validate your pgvector integration:

```bash
python test_pgvector.py
```

This will test:
- pgvector dependencies
- HACS integration
- Database connectivity
- Basic vector operations
- HACS tools integration

## Troubleshooting

### Common Issues

1. **pgvector extension not found**
   ```
   ERROR: extension "vector" is not available
   ```
   **Solution**: Install pgvector extension in PostgreSQL

2. **Dimension mismatch**
   ```
   ERROR: Embedding dimension 768 does not match expected 1536
   ```
   **Solution**: Ensure embedding dimensions match your model and table schema

3. **Index creation fails**
   ```
   ERROR: operator class "vector_cosine_ops" does not exist
   ```
   **Solution**: Make sure pgvector extension is properly installed

4. **Memory issues with large collections**
   **Solution**: Use IVFFlat index with appropriate `lists` parameter

### Performance Issues

1. **Slow queries**: Create appropriate vector indexes
2. **High memory usage**: Reduce index parameters or use IVFFlat instead of HNSW
3. **Connection issues**: Check PostgreSQL configuration and connection limits

## Resources

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [HACS Documentation](../readme.md)

## Examples

See the `test_pgvector.py` script for complete working examples of:
- Vector store initialization
- Embedding storage and retrieval
- Similarity and hybrid search
- Collection management
- Integration with HACS tools