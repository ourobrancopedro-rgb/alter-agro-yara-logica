# Wiring Diagram: GitHub → n8n → RAG

**Complete Integration Flow for YARA Lógica Three-Layer Architecture**

**Version:** 1.0
**Date:** 2025-11-24

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                             GITHUB                                    │
│                        (Source of Truth)                              │
│  ┌────────────────┬──────────────────┬──────────────────┐           │
│  │  /knowledge/   │   /config/       │  /audit-trail/   │           │
│  │  - PDFs        │   - YAML configs │  - Decision JSONs│           │
│  │  - Markdown    │   - Prompts      │  - Review logs   │           │
│  │  - Text docs   │   - Domain rules │  - Falsifier     │           │
│  │                │                  │    validations   │           │
│  └────────┬───────┴────────┬─────────┴──────────┬───────┘           │
│           │                 │                    │                   │
│           │ Git SHA         │ Git SHA            │ Git Commit        │
│           │ provenance      │ versioning         │ immutable log     │
└───────────┼─────────────────┼────────────────────┼───────────────────┘
            │                 │                    │
            ↓                 ↓                    ↑
┌──────────────────────────────────────────────────────────────────────┐
│                              n8n                                      │
│                      (Orchestration Layer)                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Workflow 1: Index GitHub Updates                            │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐                    │   │
│  │  │ GitHub  │──→│ Filter  │──→│  HTTP   │──→ RAG /ingest-file│   │
│  │  │ Webhook │   │knowledge│   │ Fetch   │                    │   │
│  │  │         │   │  files  │   │  File   │                    │   │
│  │  └─────────┘   └─────────┘   └─────────┘                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Workflow 2: YARA Lógica (RAG-enabled)                       │   │
│  │  ┌────────┐   ┌────────┐   ┌─────────┐   ┌──────────┐      │   │
│  │  │ Chat/  │──→│ Norm.  │──→│   RAG   │──→│  Build   │      │   │
│  │  │Webhook │   │ Query  │   │  /query │   │  Prompt  │      │   │
│  │  └────────┘   └────────┘   └─────────┘   └────┬─────┘      │   │
│  │                                                 │            │   │
│  │  ┌────────────────────────────────────────────┘            │   │
│  │  ↓                                                          │   │
│  │  ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐ │   │
│  │  │   LLM    │──→│ Extract │──→│  Risk   │──→│  GitHub  │ │   │
│  │  │  Call    │   │Decision │   │ Assess  │   │  Commit  │ │   │
│  │  └──────────┘   └─────────┘   └─────────┘   └──────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────┬─────────────────────────────────────────┬─────────────┘
              │                                         │
              ↓                                         ↑
┌──────────────────────────────────────────────────────────────────────┐
│                         RAG SERVICE                                   │
│                    (Embeddings + Retrieval)                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  POST /ingest-file                                             │ │
│  │  • Download file from GitHub                                   │ │
│  │  • Chunk text (512 tokens, 128 overlap)                        │ │
│  │  • Generate embeddings (text-embedding-3-small)                │ │
│  │  • Store in vector DB with metadata (source, SHA, page)        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  POST /query                                                   │ │
│  │  • Generate query embedding                                    │ │
│  │  • Semantic search (cosine similarity)                         │ │
│  │  • Apply filters (domain, classification)                      │ │
│  │  • Return top K chunks with metadata                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Vector Database (ChromaDB / Weaviate)                         │ │
│  │  • Vectors: embeddings (1536 dimensions)                       │ │
│  │  • Metadata: {repo, path, sha, page, section, domain, ...}    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Sequences

### Flow 1: Document Ingestion (GitHub → RAG)

```
┌──────┐                 ┌──────┐                 ┌──────┐
│ Dev  │                 │ n8n  │                 │ RAG  │
└──┬───┘                 └──┬───┘                 └──┬───┘
   │                        │                        │
   │ 1. git push            │                        │
   │   knowledge/VM0047.pdf │                        │
   ├───────────────────────→│                        │
   │                        │                        │
   │ 2. GitHub webhook      │                        │
   │    (push event)        │                        │
   ├───────────────────────→│                        │
   │                        │                        │
   │                        │ 3. Filter: knowledge/** │
   │                        │                        │
   │                        │ 4. Fetch file from     │
   │                        │    GitHub (with SHA)   │
   │                        ├───────────────────────→│
   │                        │                        │
   │                        │ 5. Download + chunk    │
   │                        │    + embed + store     │
   │                        │                        │
   │                        │←───────────────────────┤
   │                        │ 6. chunks_created: 87  │
   │                        │                        │
   │                        │ 7. Create GitHub issue │
   │                        │    (ingestion log)     │
   │                        │                        │
   │←───────────────────────┤                        │
   │ 8. Issue #123 created  │                        │
   │                        │                        │
   │                        │ 9. Slack notification  │
   │                        │                        │
   └────────────────────────┴────────────────────────┘
```

**Key Properties:**
- **Idempotent:** Same SHA ingested twice = no-op (409 response)
- **Traceable:** GitHub issue log shows what was ingested when
- **Provenance:** Each chunk links to source file + Git SHA

---

### Flow 2: User Query → Decision (RAG-enabled Reasoning)

```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ User │  │ n8n  │  │ RAG  │  │ LLM  │  │GitHub│
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │         │
   │ 1. POST │         │         │         │
   │ /webhook│         │         │         │
   │ "Should │         │         │         │
   │  I use  │         │         │         │
   │  VM0047?"│         │         │         │
   ├─────────→         │         │         │
   │         │         │         │         │
   │         │ 2. Normalize query │         │
   │         │    domain=carbon_markets   │
   │         │         │         │         │
   │         │ 3. POST /query    │         │
   │         │    top_k=8        │         │
   │         ├─────────→         │         │
   │         │         │         │         │
   │         │         │ 4. Semantic search │
   │         │         │    8 chunks       │
   │         │←─────────         │         │
   │         │         │         │         │
   │         │ 5. Fetch configs from GitHub │
   │         │    - lsa-config.yaml        │
   │         │    - domain-carbon-markets.yaml │
   │         │    - yara-logica-system.md  │
   │         │         │         │         │
   │         │ 6. Build prompt   │         │
   │         │    = LARA + RTOA + │         │
   │         │      domain rules + │        │
   │         │      RAG chunks     │        │
   │         │         │         │         │
   │         │ 7. LLM call       │         │
   │         ├───────────────────→         │
   │         │         │         │         │
   │         │         │ 8. Generate JSON  │
   │         │         │    decision record │
   │         │←───────────────────         │
   │         │         │         │         │
   │         │ 9. Extract + validate JSON  │
   │         │    - P→I→C→C̄ structure     │
   │         │    - Falsifier present      │
   │         │         │         │         │
   │         │ 10. Risk assessment         │
   │         │     confidence=MEDIUM       │
   │         │     → risk=medium           │
   │         │     → needs review          │
   │         │         │         │         │
   │         │ 11. Commit decision record  │
   │         │     audit-trail/DEC-xxx.json │
   │         ├─────────────────────────────→
   │         │         │         │         │
   │         │         │         │ 12. Git commit │
   │         │         │         │     sha: ef23dbf │
   │         │←─────────────────────────────
   │         │         │         │         │
   │         │ 13. Create GitHub issue     │
   │         │     [LSA Review] DEC-xxx    │
   │         ├─────────────────────────────→
   │         │         │         │         │
   │         │ 14. Response to user        │
   │←─────────         │         │         │
   │ {        │         │         │         │
   │   decision_id,    │         │         │
   │   confidence,     │         │         │
   │   review_required │         │         │
   │ }        │         │         │         │
   │         │         │         │         │
   └─────────┴─────────┴─────────┴─────────┘
```

**Key Properties:**
- **Evidence-based:** Every premise cites RAG chunk (with SHA + page)
- **Auditable:** Decision record committed to Git (immutable)
- **Human-in-loop:** Medium/high risk → GitHub issue for review
- **Falsifiable:** Every decision has measurable validation criteria

---

## Component Responsibilities

### GitHub

**What it owns:**
- **Knowledge base** — All documents for RAG (`/knowledge/`)
- **Configuration** — LSA + domain configs, prompts (`/config/`)
- **Audit trail** — Decision records, review logs (`/audit-trail/`)

**What it provides:**
- **Version control** — Git SHA for every file
- **Immutability** — Tamper-evident commit history
- **Access control** — GitHub permissions
- **Webhook triggers** — Push events notify n8n

**What it does NOT do:**
- Embeddings or vector search (RAG does this)
- Reasoning or decision-making (LLM does this)
- Orchestration (n8n does this)

---

### n8n

**What it owns:**
- **Workflows** — Orchestration logic
- **Triggers** — Webhooks, cron jobs, chat events

**What it provides:**
- **Glue code** — Connects GitHub ↔ RAG ↔ LLM
- **State management** — Tracks execution state (per workflow run)
- **Error handling** — Retries, notifications, logging

**What it does NOT do:**
- Store documents (GitHub does this)
- Generate embeddings (RAG does this)
- Make decisions (LLM does this)

**Critical principle:** n8n is **stateless** — all state lives in GitHub or RAG, not n8n.

---

### RAG Service

**What it owns:**
- **Vector database** — Embeddings + metadata
- **Embedding model** — text-embedding-3-small (or similar)

**What it provides:**
- **Ingestion API** — POST /ingest-file
- **Query API** — POST /query
- **Semantic search** — Find relevant chunks for user query

**What it does NOT do:**
- Store original files (GitHub does this)
- Make decisions (LLM does this)
- Commit to Git (n8n does this via GitHub API)

**Critical property:** Every chunk has **Git SHA provenance** — you can always trace back to exact source version.

---

## Integration Points

### 1. GitHub → n8n (Push Events)

**Mechanism:** GitHub webhook

**Setup:**
1. GitHub repo settings → Webhooks → Add webhook
2. Payload URL: `https://n8n.alter-agro.com/webhook/github-push`
3. Content type: `application/json`
4. Events: "Just the push event"
5. Active: ✅

**Payload Example:**

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "ourobrancopedro-rgb/alter-agro-yara-logica"
  },
  "commits": [
    {
      "id": "abc123",
      "added": ["knowledge/methodologies/VM0047_v1.3.pdf"],
      "modified": [],
      "removed": []
    }
  ]
}
```

---

### 2. n8n → GitHub (Fetch Configs)

**Mechanism:** HTTP GET to raw.githubusercontent.com

**Example:**

```
GET https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/config/lsa-config.yaml
```

**Alternative:** Use GitHub API with authentication for private repos.

---

### 3. n8n → GitHub (Commit Decision Records)

**Mechanism:** GitHub API PUT (create/update file)

**Example:**

```bash
PUT https://api.github.com/repos/ourobrancopedro-rgb/alter-agro-yara-logica/contents/audit-trail/decisions/2025-11/DEC-20251124-001.json

Headers:
  Authorization: token ghp_abc123...

Body:
{
  "message": "LSA: DEC-20251124-001 - Recommend VM0047",
  "content": "<base64 encoded JSON>",
  "branch": "main"
}
```

**Response:** GitHub commit SHA (for audit trail metadata)

---

### 4. n8n → RAG (Ingest File)

**Mechanism:** HTTP POST to RAG API

**Example:**

```bash
POST https://rag.alter-agro.com/ingest-file

Headers:
  X-API-Key: ak_live_abc123...

Body:
{
  "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
  "path": "knowledge/methodologies/VM0047_v1.3.pdf",
  "sha": "abc123def456",
  "content_url": "https://raw.githubusercontent.com/.../VM0047_v1.3.pdf",
  "metadata": {
    "classification": "verra-methodology",
    "domain": "carbon_markets"
  }
}
```

**Response:**

```json
{
  "status": "success",
  "chunks_created": 87,
  "sha": "abc123def456"
}
```

---

### 5. n8n → RAG (Query)

**Mechanism:** HTTP POST to RAG API

**Example:**

```bash
POST https://rag.alter-agro.com/query

Headers:
  X-API-Key: ak_live_abc123...

Body:
{
  "query": "What are VM0047 eligibility criteria?",
  "top_k": 8,
  "filters": {
    "domain": "carbon_markets"
  }
}
```

**Response:**

```json
{
  "chunks": [
    {
      "text": "Section 4.1: Eligibility...",
      "source": "knowledge/methodologies/VM0047_v1.3.pdf",
      "sha": "abc123def456",
      "metadata": {"page": 12, "domain": "carbon_markets"},
      "score": 0.89
    },
    ...
  ]
}
```

---

### 6. n8n → LLM (Generate Decision)

**Mechanism:** LangChain node or direct API call

**Example (OpenAI):**

```bash
POST https://api.openai.com/v1/chat/completions

Headers:
  Authorization: Bearer sk-proj-abc123...

Body:
{
  "model": "gpt-4-turbo-preview",
  "messages": [
    {
      "role": "system",
      "content": "<LARA + RTOA + RAG chunks + domain rules>"
    },
    {
      "role": "user",
      "content": "Should I use VM0047 for this project?"
    }
  ],
  "temperature": 0.1,
  "max_tokens": 4096
}
```

**Response:**

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<<<BEGIN_DECISION_RECORD>>>\n{...}\n<<<END_DECISION_RECORD>>>"
      }
    }
  ]
}
```

---

## Authentication & Security

### GitHub

- **Public repos:** No auth needed for reads
- **Private repos:** GitHub PAT (Personal Access Token)
  - Scope: `repo` (full access) or `contents:write` (for commits)

### RAG API

- **API Key Authentication**
  - Header: `X-API-Key: ak_live_abc123...`
  - Stored in n8n environment variable: `RAG_API_KEY`

### n8n Webhooks

- **HMAC Signature Verification** (optional but recommended)
  - GitHub webhook secret → HMAC-SHA256
  - Verify `X-Hub-Signature-256` header

### LLM API

- **API Key Authentication**
  - OpenAI: `Authorization: Bearer sk-proj-...`
  - Anthropic: `x-api-key: sk-ant-...`
  - Stored in n8n credentials store

---

## Deployment Checklist

### Prerequisites

- [ ] GitHub repo created: `ourobrancopedro-rgb/alter-agro-yara-logica`
- [ ] Directory structure set up: `/knowledge/`, `/config/`, `/audit-trail/`
- [ ] n8n instance deployed: `https://n8n.alter-agro.com`
- [ ] RAG service deployed: `https://rag.alter-agro.com`
- [ ] Vector database (ChromaDB/Weaviate) running

### Step 1: Configure GitHub

1. Add webhook:
   - URL: `https://n8n.alter-agro.com/webhook/github-push`
   - Events: Push
   - Active: ✅

2. Generate PAT (Personal Access Token):
   - Scope: `repo`
   - Save to n8n: `GITHUB_TOKEN`

### Step 2: Deploy RAG Service

1. Set up vector database (ChromaDB)
2. Deploy RAG API (Python + FastAPI)
3. Generate API key:
   - Save to n8n: `RAG_API_KEY`

### Step 3: Import n8n Workflows

1. Import Workflow 1 (Index GitHub Updates)
   - Enable webhook trigger
   - Test with manual payload

2. Import Workflow 2 (YARA Lógica RAG-enabled)
   - Configure LLM credentials (OpenAI/Anthropic)
   - Test with sample query

### Step 4: Populate Knowledge Base

1. Add sample documents to `/knowledge/methodologies/`
   - Example: VM0047 v1.3 PDF
   - Commit and push → triggers Workflow 1

2. Verify ingestion:
   - Check n8n execution log
   - Check RAG health endpoint: `GET /health`
   - Verify chunks created

### Step 5: Test End-to-End

1. Submit test query via webhook:

```bash
curl -X POST https://n8n.alter-agro.com/webhook/yara-logica-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I use VM0047 for ARR in Cerrado?", "domain": "carbon_markets"}'
```

2. Verify:
   - n8n workflow executes
   - RAG returns chunks
   - LLM generates decision record
   - Decision committed to GitHub (`audit-trail/decisions/...`)
   - GitHub issue created (if review needed)

### Step 6: Monitor & Iterate

- Set up Prometheus metrics (optional)
- Configure Slack/email notifications
- Review first 10 decisions manually
- Adjust risk thresholds if needed

---

## Troubleshooting

### Issue: Webhook not triggering

**Symptoms:** Push to GitHub, but n8n workflow doesn't run

**Diagnosis:**
1. Check GitHub webhook delivery logs (repo settings)
2. Verify n8n webhook URL is accessible
3. Test with "Redeliver" in GitHub

**Solution:**
- Ensure n8n is publicly accessible (or use ngrok for testing)
- Verify webhook path matches n8n trigger node

---

### Issue: RAG returns no results

**Symptoms:** Query succeeds, but `chunks: []`

**Diagnosis:**
1. Check if documents were ingested: `GET /health` (total_documents)
2. Verify query filters match document metadata
3. Lower `min_score` threshold

**Solution:**
- Re-ingest documents if needed
- Broaden filters (remove domain/classification filters)
- Check embedding model consistency

---

### Issue: LLM JSON parsing fails

**Symptoms:** n8n node "Extract Decision Record" errors

**Diagnosis:**
1. Check LLM response in n8n execution log
2. Verify delimiters present: `<<<BEGIN_DECISION_RECORD>>>`
3. Validate JSON syntax

**Solution:**
- Improve system prompt with JSON examples
- Increase LLM temperature slightly (0.1 → 0.2)
- Use structured output API (GPT-4 JSON mode)

---

### Issue: GitHub commit fails (403/404)

**Symptoms:** n8n GitHub API call returns error

**Diagnosis:**
1. Check GitHub token permissions
2. Verify file path doesn't exist (409 if exists)
3. Check branch name

**Solution:**
- Regenerate GitHub PAT with correct scopes
- Use unique decision IDs
- Ensure branch exists (create if needed)

---

## Performance Optimization

### RAG Query Latency

**Current:** ~100-200ms
**Optimization:**
- Use faster embedding model (all-MiniLM-L6-v2)
- Enable vector DB caching
- Pre-filter by domain before semantic search

### LLM Latency

**Current:** ~5-10 seconds (gpt-4-turbo)
**Optimization:**
- Use faster model (gpt-3.5-turbo for simple queries)
- Stream responses (if UI supports)
- Cache common queries (with TTL)

### End-to-End Latency

**Target:** <15 seconds from query to response

**Bottlenecks:**
1. LLM call (~5-10s) — unavoidable
2. RAG query (~0.2s) — optimizable
3. Config fetch (~0.5s) — cache in n8n
4. GitHub commit (~1s) — acceptable

---

## Cost Estimation

### RAG Service

**Embedding costs (OpenAI text-embedding-3-small):**
- $0.02 per 1M tokens
- Average document: 10,000 tokens
- 100 documents = 1M tokens = **$0.02**
- **Annual:** ~$10 (assuming 500 documents ingested)

### LLM Costs

**GPT-4 Turbo:**
- Input: $10/1M tokens
- Output: $30/1M tokens
- Average query:
  - Input: ~3000 tokens (system prompt + RAG chunks)
  - Output: ~1000 tokens (decision record)
- Cost per query: **$0.06**
- **Annual:** $3,000 (assuming 50,000 queries)

**Alternative (GPT-3.5 Turbo):**
- Input: $0.50/1M tokens, Output: $1.50/1M tokens
- Cost per query: **$0.003**
- **Annual:** $150 (assuming 50,000 queries)

### Infrastructure

- **n8n:** Self-hosted (free) or Cloud ($20-100/month)
- **RAG service:** Self-hosted (~$50/month VPS) or managed vector DB ($100/month)
- **GitHub:** Free (public) or Team ($4/user/month)

**Total (minimal):** $200-500/month + LLM costs

---

**Version:** 1.0
**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
