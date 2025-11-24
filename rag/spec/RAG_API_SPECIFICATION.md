# RAG Service API Specification

**YARA Lógica RAG (Retrieval-Augmented Generation) API**

**Version:** 1.0
**Date:** 2025-11-24
**Status:** Implementation Specification

---

## Overview

The RAG service is a microservice that provides:
1. **Document ingestion** — Chunking, embedding, and storage of Git-backed documents
2. **Semantic retrieval** — Query-based retrieval of relevant chunks with metadata

**Key Properties:**
- Git SHA provenance for all documents (immutable, tamper-evident)
- Metadata-rich chunks (source file, page, section, classification, domain)
- Integration with GitHub → n8n → LLM pipeline

---

## Architecture

### Technology Stack (Recommended)

**Backend:**
- **Python 3.11+** with FastAPI
- **Pydantic** for request/response validation

**Vector Database:**
- **ChromaDB** (simple, local, good for prototyping)
- **Weaviate** (production-grade, scalable, open-source)
- **Pinecone** (managed, serverless, easy to deploy)

**Embeddings:**
- **Option 1:** OpenAI `text-embedding-3-small` (1536 dimensions, $0.02 per 1M tokens)
- **Option 2:** Open-source `all-MiniLM-L6-v2` (384 dimensions, free, runs locally)

**Document Processing:**
- **PDF:** `pymupdf` or `pdfplumber` for text extraction
- **Markdown:** Custom parser with header-based chunking
- **Text:** Simple token-based chunking

---

## API Endpoints

### 1. POST `/ingest-file`

**Purpose:** Ingest a document from GitHub into the vector database.

**Request:**

```http
POST /ingest-file
Content-Type: application/json
X-API-Key: {api_key}

{
  "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
  "path": "knowledge/methodologies/VM0047_v1.3.pdf",
  "sha": "abc123def456789...",
  "content_url": "https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/knowledge/methodologies/VM0047_v1.3.pdf",
  "metadata": {
    "title": "VM0047 Afforestation, Reforestation and Revegetation v1.3",
    "version": "1.3",
    "published": "2023-06-15",
    "classification": "verra-methodology",
    "domain": "carbon_markets",
    "language": "en"
  }
}
```

**Request Schema:**

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `repo` | string | Yes | GitHub repository (owner/repo) |
| `path` | string | Yes | File path within repo |
| `sha` | string | Yes | Git SHA of file (for provenance) |
| `content_url` | string | Yes | Direct URL to file content |
| `metadata` | object | No | Additional metadata (title, version, etc.) |
| `metadata.title` | string | No | Document title |
| `metadata.version` | string | No | Document version |
| `metadata.published` | string | No | Publication date (ISO-8601) |
| `metadata.classification` | string | No | Document classification |
| `metadata.domain` | string | No | Domain tag (carbon_markets, etc.) |
| `metadata.language` | string | No | Language code (en, pt-BR, etc.) |

**Processing Steps:**

1. **Download file** from `content_url`
2. **Detect file type** (PDF, Markdown, TXT)
3. **Extract text:**
   - PDF: Extract text by page using `pymupdf`
   - Markdown: Parse with headers as section markers
   - TXT: Read as plain text
4. **Chunk text:**
   - **Chunk size:** 512 tokens (configurable)
   - **Overlap:** 128 tokens (configurable)
   - **Strategy:** Sliding window, respecting sentence boundaries
5. **Generate embeddings:**
   - Call embedding model (OpenAI or local)
   - One embedding per chunk
6. **Store in vector DB:**
   - Vector: embedding
   - Metadata: `repo`, `path`, `sha`, `chunk_id`, `page`, `section`, + custom metadata

**Response (Success):**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "file": "knowledge/methodologies/VM0047_v1.3.pdf",
  "sha": "abc123def456789...",
  "chunks_created": 87,
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "timestamp": "2025-11-24T10:35:00Z",
  "ingestion_duration_ms": 3421
}
```

**Response Schema:**

| Field | Type | Description |
|:------|:-----|:------------|
| `status` | string | "success" or "error" |
| `file` | string | File path that was ingested |
| `sha` | string | Git SHA of file |
| `chunks_created` | integer | Number of chunks created |
| `embedding_model` | string | Model used for embeddings |
| `embedding_dimensions` | integer | Dimensionality of embeddings |
| `timestamp` | string | ISO-8601 timestamp |
| `ingestion_duration_ms` | integer | Processing time in milliseconds |

**Response (Error):**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "Missing required field: sha",
  "timestamp": "2025-11-24T10:35:00Z"
}
```

**Error Codes:**

| Code | HTTP Status | Description |
|:-----|:------------|:------------|
| `INVALID_REQUEST` | 400 | Missing or invalid request fields |
| `FILE_NOT_FOUND` | 404 | File not found at `content_url` |
| `ALREADY_INGESTED` | 409 | File with same SHA already ingested (idempotent) |
| `DOWNLOAD_FAILED` | 502 | Failed to download file from GitHub |
| `EMBEDDING_FAILED` | 500 | Embedding generation failed |
| `STORAGE_FAILED` | 500 | Vector DB storage failed |

---

### 2. POST `/query`

**Purpose:** Retrieve relevant document chunks for a query.

**Request:**

```http
POST /query
Content-Type: application/json
X-API-Key: {api_key}

{
  "query": "What are the eligibility criteria for VM0047 ARR projects in the Cerrado biome?",
  "top_k": 8,
  "filters": {
    "domain": "carbon_markets",
    "classification": "verra-methodology"
  },
  "min_score": 0.7
}
```

**Request Schema:**

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `query` | string | Yes | User query (natural language) |
| `top_k` | integer | No | Number of chunks to return (default: 8) |
| `filters` | object | No | Metadata filters |
| `filters.domain` | string | No | Filter by domain (carbon_markets, etc.) |
| `filters.classification` | string | No | Filter by classification |
| `filters.repo` | string | No | Filter by repo |
| `filters.path` | string | No | Filter by file path (glob pattern) |
| `min_score` | float | No | Minimum similarity score (0.0-1.0, default: 0.0) |

**Processing Steps:**

1. **Generate query embedding**
2. **Perform semantic search:**
   - Cosine similarity or dot product (depending on embedding model)
   - Apply metadata filters
   - Return top K results
3. **Sort by score** (descending)
4. **Return chunks with metadata**

**Response (Success):**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "query": "What are the eligibility criteria for VM0047 ARR projects in the Cerrado biome?",
  "chunks": [
    {
      "chunk_id": "abc123-chunk-012",
      "text": "Section 4.1: Eligibility Criteria. For ARR projects under VM0047, the project area must meet the following: (1) not classified as forest for at least 10 years prior to project start date; (2) no displacement of existing agriculture or communities...",
      "source": "knowledge/methodologies/VM0047_v1.3.pdf",
      "sha": "abc123def456789...",
      "metadata": {
        "page": 12,
        "section": "4.1",
        "title": "VM0047 Afforestation, Reforestation and Revegetation v1.3",
        "version": "1.3",
        "methodology": "VM0047",
        "classification": "verra-methodology",
        "domain": "carbon_markets",
        "published": "2023-06-15"
      },
      "score": 0.89
    },
    {
      "chunk_id": "def456-chunk-008",
      "text": "The Cerrado biome is subject to Brazilian Forest Code Article 12, which requires Legal Reserve (RL) of 35% for rural properties. Restoration of RL is a legal obligation and therefore not additional under carbon credit additionality requirements...",
      "source": "knowledge/regulations/forest-code-lei-12651-2012.pdf",
      "sha": "def456ghi789abc...",
      "metadata": {
        "page": 8,
        "section": "Article 12",
        "title": "Lei 12.651/2012 - Código Florestal Brasileiro",
        "classification": "regulation-brazil",
        "domain": "compliance_legal",
        "published": "2012-05-25"
      },
      "score": 0.82
    }
    // ... 6 more chunks
  ],
  "total_results": 8,
  "query_embedding_model": "text-embedding-3-small",
  "timestamp": "2025-11-24T10:40:00Z",
  "query_duration_ms": 142
}
```

**Response Schema:**

| Field | Type | Description |
|:------|:-----|:------------|
| `query` | string | Original query |
| `chunks` | array | List of retrieved chunks |
| `chunks[].chunk_id` | string | Unique chunk identifier |
| `chunks[].text` | string | Chunk text content |
| `chunks[].source` | string | Source file path |
| `chunks[].sha` | string | Git SHA of source file |
| `chunks[].metadata` | object | Chunk metadata |
| `chunks[].score` | float | Similarity score (0.0-1.0) |
| `total_results` | integer | Number of chunks returned |
| `query_embedding_model` | string | Model used for query embedding |
| `timestamp` | string | ISO-8601 timestamp |
| `query_duration_ms` | integer | Query processing time |

**Response (Error):**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "error",
  "error_code": "INVALID_QUERY",
  "message": "Query text is required",
  "timestamp": "2025-11-24T10:40:00Z"
}
```

**Error Codes:**

| Code | HTTP Status | Description |
|:-----|:------------|:------------|
| `INVALID_QUERY` | 400 | Missing or invalid query |
| `EMBEDDING_FAILED` | 500 | Query embedding generation failed |
| `SEARCH_FAILED` | 500 | Vector search failed |

---

### 3. GET `/health`

**Purpose:** Health check endpoint.

**Request:**

```http
GET /health
```

**Response (Success):**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "services": {
    "vector_db": "connected",
    "embedding_service": "operational"
  },
  "stats": {
    "total_documents": 42,
    "total_chunks": 3847,
    "embedding_model": "text-embedding-3-small",
    "embedding_dimensions": 1536
  },
  "timestamp": "2025-11-24T10:45:00Z",
  "version": "1.0.0"
}
```

**Response (Unhealthy):**

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "status": "unhealthy",
  "services": {
    "vector_db": "disconnected",
    "embedding_service": "operational"
  },
  "error": "Vector database connection failed",
  "timestamp": "2025-11-24T10:45:00Z",
  "version": "1.0.0"
}
```

---

## Data Models

### Chunk Metadata Schema

Every chunk in the vector database has this metadata structure:

```python
{
  # Core identification
  "chunk_id": str,           # Unique ID: "{file_sha}-chunk-{index}"
  "repo": str,               # GitHub repo (owner/repo)
  "path": str,               # File path in repo
  "sha": str,                # Git SHA of source file

  # Location within document
  "page": int,               # Page number (PDF) or null
  "section": str,            # Section/header (Markdown) or null
  "chunk_index": int,        # Sequential index within file (0, 1, 2, ...)

  # Document metadata
  "title": str,              # Document title
  "version": str,            # Document version
  "published": str,          # Publication date (ISO-8601)
  "classification": str,     # Document type (verra-methodology, regulation-brazil, etc.)
  "domain": str,             # Domain tag (carbon_markets, regenerative_agriculture, etc.)
  "language": str,           # Language code (en, pt-BR, es, etc.)

  # Processing metadata
  "ingested_at": str,        # ISO-8601 timestamp of ingestion
  "embedding_model": str,    # Model used for this chunk
  "chunk_tokens": int        # Token count for this chunk
}
```

---

## Implementation Details

### Chunking Strategy

**PDF Documents:**

1. Extract text page-by-page
2. For each page:
   - Split text into sentences
   - Group sentences into ~512 token chunks
   - Overlap: last 128 tokens of chunk N = first 128 tokens of chunk N+1
3. Store page number in metadata

**Markdown Documents:**

1. Parse headers (# H1, ## H2, etc.)
2. Chunk by section:
   - If section < 512 tokens: one chunk
   - If section > 512 tokens: split with overlap
3. Store section header in metadata

**Plain Text:**

1. Split into sentences
2. Group into ~512 token chunks with 128 token overlap

### Embedding Model Selection

| Model | Dimensions | Cost | Pros | Cons |
|:------|:-----------|:-----|:-----|:-----|
| OpenAI `text-embedding-3-small` | 1536 | $0.02/1M tokens | High quality, multilingual | API cost, internet required |
| OpenAI `text-embedding-3-large` | 3072 | $0.13/1M tokens | Highest quality | Higher cost, larger storage |
| `all-MiniLM-L6-v2` | 384 | Free | Fast, runs locally | Lower quality than OpenAI |
| `multilingual-e5-large` | 1024 | Free | Good multilingual support | Slower than MiniLM |

**Recommendation:** Start with `text-embedding-3-small` for production, `all-MiniLM-L6-v2` for development/testing.

### Vector Database Comparison

| Database | Pros | Cons |
|:---------|:-----|:-----|
| **ChromaDB** | Easy setup, local, SQLite-backed | Not scalable beyond ~1M chunks |
| **Weaviate** | Production-grade, scalable, GraphQL API | More complex setup |
| **Pinecone** | Managed, serverless, auto-scaling | Vendor lock-in, cost |
| **Qdrant** | Fast, Rust-based, self-hosted | Newer, smaller ecosystem |

**Recommendation:** ChromaDB for MVP, Weaviate for production.

---

## Authentication

### API Key Authentication

**Header:**

```
X-API-Key: {api_key}
```

**Implementation:**

- API keys stored in environment variable or secrets manager
- Validate on every request
- Return 401 if missing/invalid

**Example:**

```bash
curl -X POST https://rag.alter-agro.com/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ak_live_abc123..." \
  -d '{"query": "VM0047 eligibility", "top_k": 8}'
```

---

## Rate Limiting

**Limits (Suggested):**

- `/ingest-file`: 60 requests/minute per API key
- `/query`: 600 requests/minute per API key
- `/health`: unlimited

**Implementation:**

- Use Redis or in-memory store for rate limit tracking
- Return 429 (Too Many Requests) if exceeded

**Response (Rate Limited):**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Retry after 60 seconds.",
  "limit": 600,
  "reset_at": "2025-11-24T10:46:00Z"
}
```

---

## Monitoring & Observability

### Metrics (Prometheus Format)

**Ingestion:**
- `rag_ingest_requests_total{status}` — Counter
- `rag_ingest_duration_seconds` — Histogram
- `rag_chunks_created_total` — Counter

**Query:**
- `rag_query_requests_total{status}` — Counter
- `rag_query_duration_seconds` — Histogram
- `rag_chunks_returned` — Histogram

**System:**
- `rag_vector_db_connected` — Gauge (1=connected, 0=disconnected)
- `rag_embedding_service_available` — Gauge

### Logging

**Log Format (JSON):**

```json
{
  "timestamp": "2025-11-24T10:40:15.123Z",
  "level": "INFO",
  "service": "rag-api",
  "endpoint": "POST /query",
  "request_id": "req-abc123",
  "query": "VM0047 eligibility",
  "top_k": 8,
  "filters": {"domain": "carbon_markets"},
  "results": 8,
  "duration_ms": 142,
  "status": "success"
}
```

---

## Security

### Input Validation

- Validate all inputs (query length, top_k range, etc.)
- Sanitize file paths (prevent directory traversal)
- Limit file size for ingestion (e.g., max 50 MB)

### No Secrets in Logs

- Never log API keys
- Redact sensitive metadata if present

### HTTPS Required

- All endpoints must use HTTPS in production
- Redirect HTTP to HTTPS

---

## Deployment

### Docker Compose Example

```yaml
version: '3.8'
services:
  rag-api:
    image: alter-agro/rag-api:1.0
    ports:
      - "8000:8000"
    environment:
      - VECTOR_DB_URL=http://chromadb:8000
      - EMBEDDING_MODEL=text-embedding-3-small
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RAG_API_KEY=${RAG_API_KEY}
    depends_on:
      - chromadb

  chromadb:
    image: chromadb/chroma:0.4.15
    ports:
      - "8001:8000"
    volumes:
      - chromadb-data:/chroma/chroma

volumes:
  chromadb-data:
```

**Start:**

```bash
docker-compose up -d
```

**Health check:**

```bash
curl http://localhost:8000/health
```

---

## Testing

### Unit Tests

```python
# Test chunking
def test_chunk_pdf():
    chunks = chunk_pdf("sample.pdf", chunk_size=512, overlap=128)
    assert len(chunks) > 0
    assert all(chunk["tokens"] <= 512 for chunk in chunks)

# Test embedding
def test_embed_text():
    embedding = embed_text("Sample text", model="text-embedding-3-small")
    assert len(embedding) == 1536
```

### Integration Tests

```python
# Test ingestion
def test_ingest_file():
    response = client.post("/ingest-file", json={
        "repo": "test/repo",
        "path": "test.pdf",
        "sha": "abc123",
        "content_url": "https://example.com/test.pdf"
    })
    assert response.status_code == 200
    assert response.json()["chunks_created"] > 0

# Test query
def test_query():
    response = client.post("/query", json={
        "query": "test query",
        "top_k": 5
    })
    assert response.status_code == 200
    assert len(response.json()["chunks"]) <= 5
```

---

## Documentation

- **OpenAPI Spec:** `/docs` (FastAPI auto-generated Swagger UI)
- **Redoc:** `/redoc` (alternative documentation UI)

---

**Version:** 1.0
**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
