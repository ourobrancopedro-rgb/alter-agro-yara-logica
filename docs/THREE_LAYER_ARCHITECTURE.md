# Three-Layer Architecture: GitHub → n8n → RAG

**YARA Lógica Orchestration & Audit Design**
**Version:** 1.0
**Date:** 2025-11-24
**Status:** Implementation Specification

---

## Executive Summary

This document defines the **three-layer architecture** for YARA Lógica, integrating:

1. **GitHub** — Source of truth + immutable audit trail
2. **n8n** — Orchestration & workflow glue
3. **RAG Service** — Embeddings + retrieval for LLM reasoning

The design aligns with:
- **LSA Application Protocol** — decision records, audit trail, Git-backed storage
- **LARA v3** — P→I→C→C̄ reasoning framework (premise → inference → contradiction → conclusion)
- **RTOA v3** — Reality-Tested Ontological Architecture (no identity, no metaphysics, drift detection)
- **Logos/Unified Spec v3.0** — Truth-seeking, falsifiability, audit-grade integrity

---

## 1. Architecture Overview

### 1.1 The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│                          GitHub                              │
│  • Source of truth for knowledge, config, audit trail       │
│  • Version-controlled, immutable, cryptographic integrity   │
│  • Three logical folders: /knowledge, /config, /audit-trail │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                           n8n                                │
│  • Orchestration layer (no "thinking")                      │
│  • Workflow 1: GitHub → RAG (ingest pipeline)               │
│  • Workflow 2: Query → RAG → LLM → GitHub (audit pipeline)  │
│  • Triggers: webhooks, cron, chat                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       RAG Service                            │
│  • Embeddings + vector retrieval                            │
│  • API: POST /ingest-file, POST /query                      │
│  • Stores: chunks + metadata (source, SHA, page, etc.)      │
│  • Returns: ranked chunks with audit metadata               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Core Principles

1. **GitHub as Canonical Truth**
   - All knowledge documents live in `/knowledge/`
   - All configs live in `/config/`
   - All decision records live in `/audit-trail/`
   - Every document has a Git SHA for tamper-evident versioning

2. **n8n as Stateless Orchestrator**
   - n8n does NOT store state
   - n8n does NOT make decisions
   - n8n coordinates: fetch → process → store → notify

3. **RAG as Evidence Provider**
   - RAG provides chunks + metadata (source, SHA, page)
   - RAG does NOT generate reasoning
   - RAG enables LLM to cite specific Git-backed sources

4. **Audit-Grade Integrity**
   - Every decision record includes:
     - Premises with sources (Git SHA + URL)
     - Inferences (logical steps)
     - Contradictions (opposing evidence)
     - Conclusion with confidence level
     - Falsifier (Popperian validation criteria)
   - Every decision is committed to Git with cryptographic hash

---

## 2. GitHub: What It Owns

### 2.1 Directory Structure

```
alter-agro-yara-logica/
├── knowledge/              # Documents for RAG
│   ├── methodologies/      # Verra VM0047, VM0042, etc.
│   │   ├── VM0047_v1.3.pdf
│   │   ├── VM0042_v2.0.pdf
│   │   └── README.md       # Methodology index
│   ├── regulations/        # Brazilian law, Forest Code
│   │   ├── forest-code-2012.pdf
│   │   ├── lgpd-lei-13709.pdf
│   │   └── README.md
│   ├── regen-docs/         # Regen Network, regenerative ag
│   │   └── README.md
│   ├── projects/           # Project-specific docs (PDDs, studies)
│   │   └── README.md
│   └── README.md           # Knowledge base overview
│
├── config/                 # LSA + domain configurations
│   ├── lsa-config.yaml     # System-level LSA config
│   ├── domain-carbon-markets.yaml  # Carbon markets rules
│   ├── domain-regenerative-ag.yaml # Regen ag rules
│   ├── prompts/            # System prompts
│   │   ├── lara-v3-base.md
│   │   ├── rtoa-v3-ambient.md
│   │   └── yara-logica-system.md
│   └── README.md
│
├── audit-trail/            # Decision records & reviews
│   ├── decisions/          # LSA Decision Records
│   │   ├── 2025-11/
│   │   │   ├── DEC-20251124-001.json
│   │   │   └── DEC-20251124-002.json
│   │   └── README.md
│   ├── reviews/            # Human review artifacts
│   │   └── README.md
│   └── README.md
│
├── lsa/                    # LSA system (existing)
├── rag/                    # RAG service implementation
├── docs/                   # Documentation
└── ...
```

### 2.2 Knowledge Base (`/knowledge/`)

**Purpose:** Store all documents that will be embedded into the RAG index.

**Contents:**
- Verra methodologies (PDF, Markdown)
- Brazilian regulations (PDF)
- Regen Network documentation
- Project-specific documents (PDDs, feasibility studies)
- Technical references

**Metadata Requirements:**
- Every document must have:
  - Git SHA (automatic via Git)
  - Version number (if applicable)
  - Publication date
  - Source URL (if external)
  - Classification (methodology, regulation, project, etc.)

**Example Metadata (in README.md):**

```yaml
# knowledge/methodologies/README.md
documents:
  - file: VM0047_v1.3.pdf
    title: "VM0047 Afforestation, Reforestation and Revegetation v1.3"
    version: "1.3"
    published: "2023-06-15"
    source_url: "https://verra.org/methodologies/vm0047/"
    classification: "verra-methodology"

  - file: VM0042_v2.0.pdf
    title: "VM0042 Methodology for Improved Agricultural Land Management v2.0"
    version: "2.0"
    published: "2022-11-10"
    source_url: "https://verra.org/methodologies/vm0042/"
    classification: "verra-methodology"
```

### 2.3 Configuration (`/config/`)

**Purpose:** Store LSA system configs, domain rules, and system prompts.

**Key Files:**

1. **`lsa-config.yaml`** — System-level LSA configuration
   - Confidence thresholds
   - Risk assessment rules
   - Evidence requirements
   - Falsifier policies

2. **`domain-carbon-markets.yaml`** — Carbon markets domain rules
   - Methodology selection criteria
   - Additionality requirements
   - Baseline/project scenario rules
   - Risk thresholds specific to carbon projects

3. **`domain-regenerative-ag.yaml`** — Regenerative agriculture rules
   - Soil carbon sequestration protocols
   - Grazing management best practices
   - Biodiversity requirements

4. **`prompts/`** — System prompts for LLM
   - `lara-v3-base.md` — Core LARA reasoning instructions
   - `rtoa-v3-ambient.md` — RTOA environmental constraints
   - `yara-logica-system.md` — YARA Lógica system prompt template

**Example:**

```yaml
# config/lsa-config.yaml
version: "1.0"
lsa:
  evidence_requirements:
    FACT:
      min_sources: 2
      source_types: ["https", "git+https"]
    EXPERT_OPINION:
      min_sources: 1
      require_credentials: true

  confidence_levels:
    HIGH:
      min_premises: 3
      max_contradictions: 1
      min_evidence_quality: 0.8
    MEDIUM:
      min_premises: 2
      max_contradictions: 2
      min_evidence_quality: 0.6
    LOW:
      min_premises: 1
      max_contradictions: 999
      min_evidence_quality: 0.0

  risk_assessment:
    auto_approve_threshold: "low"
    human_review_threshold: "medium"
    escalation_threshold: "high"
```

### 2.4 Audit Trail (`/audit-trail/`)

**Purpose:** Store immutable decision records and review artifacts.

**Structure:**
- `/decisions/YYYY-MM/` — Decision records by month
- `/reviews/YYYY-MM/` — Human review artifacts

**Decision Record Format (JSON):**

```json
{
  "id": "DEC-20251124-001",
  "timestamp": "2025-11-24T10:30:00Z",
  "version": "PICC-1.0",
  "query": "Should we use VM0047 or VM0042 for an 8,000 ha ARR project in the Cerrado?",
  "premises": [
    {
      "id": "P1",
      "type": "FACT",
      "text": "VM0047 is designed for ARR (Afforestation, Reforestation, Revegetation) projects",
      "sources": [
        {
          "url": "https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/knowledge/methodologies/VM0047_v1.3.pdf",
          "sha": "abc123...",
          "page": 5
        }
      ]
    }
  ],
  "inferences": [
    {
      "id": "I1",
      "from_premises": ["P1", "P2"],
      "text": "VM0047 is the applicable methodology for this project type"
    }
  ],
  "contradictions": [
    {
      "id": "C1",
      "text": "VM0042 could also apply if the project includes agricultural land management",
      "sources": [...]
    }
  ],
  "conclusion": {
    "decision": "Recommend VM0047 as primary methodology",
    "confidence": "HIGH",
    "rationale": "Project meets all VM0047 eligibility criteria with no major contradictions"
  },
  "falsifier": {
    "metric": "Auditor non-conformances on methodology selection",
    "threshold": ">0",
    "by": "2026-06-01",
    "action": "Reassess methodology selection and update decision record"
  },
  "metadata": {
    "domain": "carbon_markets",
    "risk_level": "low",
    "auto_approved": true,
    "rag_chunks_used": 8,
    "git_commit": "ef23dbf..."
  }
}
```

---

## 3. n8n: Orchestration Layer

### 3.1 Workflow 1: Index GitHub Updates (GitHub → RAG)

**Purpose:** Automatically ingest new/updated documents from `/knowledge/` into the RAG index.

**Trigger:** GitHub webhook (push events to `/knowledge/**`) or cron job

**Steps:**

1. **GitHub Webhook Trigger**
   - Listen for push events
   - Filter: only files in `knowledge/**`

2. **Extract Changed Files**
   - Parse webhook payload
   - Get list of added/modified files

3. **For Each File:**
   - **Fetch File Content**
     - Use GitHub API or raw URL
     - Get file content + SHA

   - **Call RAG Ingest API**
     - `POST /ingest-file`
     - Send: `{ repo, path, sha, content_url }`

   - **Log Ingestion**
     - Create GitHub issue or append to log file
     - Record: file, SHA, timestamp, status

4. **Notify (Optional)**
   - Slack/email notification on successful ingestion
   - Include: number of files ingested, total chunks created

**n8n Nodes:**
1. GitHub Trigger (webhook)
2. Filter (only `knowledge/**` files)
3. Loop: For each file
4. HTTP Request: Fetch file from GitHub
5. HTTP Request: POST /ingest-file
6. Code: Aggregate results
7. GitHub: Create issue (optional log)
8. Slack/Email: Notify team

**Example Workflow (Conceptual):**

```
GitHub Webhook
    ↓
[Filter: knowledge/**]
    ↓
[Loop: Changed Files]
    ↓
[HTTP: Fetch from GitHub]
    ↓
[HTTP: POST /ingest-file]
    ↓
[Code: Aggregate Results]
    ↓
[GitHub: Log Issue]
    ↓
[Slack: Notify Team]
```

### 3.2 Workflow 2: YARA Lógica (RAG-enabled Query → Decision)

**Purpose:** Process user queries using RAG, generate LSA decision records, commit to Git.

**Trigger:** Chat trigger, HTTP webhook, or manual trigger

**Steps:**

1. **Trigger: Receive Query**
   - Chat message, API call, or manual input
   - Input: user question + optional context (project metadata)

2. **Normalize Query**
   - Extract explicit question
   - Add project metadata if available
   - Set domain filter (e.g., `carbon_markets`)

3. **Call RAG Service**
   - `POST /query`
   - Send: `{ query, top_k: 8, filters: { domain: "carbon_markets" } }`
   - Receive: list of chunks with metadata (text, source, SHA, page)

4. **Load System Config**
   - Fetch `config/lsa-config.yaml` from GitHub
   - Fetch `config/domain-carbon-markets.yaml`
   - Fetch system prompts from `config/prompts/`

5. **Build LSA System Prompt**
   - Combine:
     - LARA v3 reasoning framework
     - RTOA v3 ambient constraints
     - Domain-specific rules
     - Retrieved RAG chunks (with sources + SHA)
   - Format:
     ```
     You are YARA Lógica, using LARA (P→I→C→C̄) in RTOA v3 mode.
     Use ONLY the information below as factual basis.
     Cite explicitly which chunk [#N] each premise comes from.

     CONTEXT:
     [#1] <chunk 1 text>
     Source: knowledge/VM0047_v1.3.pdf (sha: abc123..., page: 5)

     [#2] <chunk 2 text>
     Source: knowledge/forest-code-2012.pdf (sha: def456..., page: 12)

     ...

     DOMAIN RULES (carbon_markets):
     - Additionality is mandatory per VM0047 Section 4.2
     - Baseline must be validated per Brazilian Forest Code
     - ...
     ```

6. **Call LLM (LSA Agent)**
   - Use LangChain or direct API call
   - System message: constructed prompt from Step 5
   - User message: normalized query
   - Expect response with:
     - `<<<BEGIN_DECISION_RECORD>>>`
     - JSON decision record (PICC format)
     - `<<<END_DECISION_RECORD>>>`

7. **Extract Decision Record**
   - Parse JSON between delimiters
   - Validate schema (PICC-1.0)
   - Add metadata:
     - `git_commit`: current HEAD SHA
     - `rag_chunks_used`: number of chunks
     - `domain`: from config
     - `timestamp`: ISO-8601

8. **Risk Assessment**
   - Calculate risk score based on:
     - Confidence level
     - Number of contradictions
     - Evidence quality
     - Domain-specific thresholds
   - Route:
     - **Low risk** → auto-approve
     - **Medium/High risk** → human review

9. **Save to GitHub (Audit Trail)**
   - Generate filename: `audit-trail/decisions/YYYY-MM/DEC-{timestamp}.json`
   - Commit to GitHub:
     - Branch: `main` (or audit branch)
     - Message: `LSA: DEC-{id} - {short summary}`
     - Include decision record JSON

10. **Create GitHub Issue (if human review needed)**
    - Title: `[LSA Review] DEC-{id}: {short summary}`
    - Body:
      - Decision record
      - RAG chunks used (with SHA + sources)
      - Risk score + rationale
      - Reviewer checklist
    - Labels: `lsa`, `needs-review`, `risk-{level}`, `domain-{name}`

11. **Return Response to User**
    - Summary of decision
    - Confidence level
    - Key premises and contradictions
    - Link to GitHub commit (audit trail)
    - Link to GitHub issue (if review needed)

**n8n Nodes:**
1. Chat Trigger (or HTTP webhook)
2. Code: Normalize query
3. HTTP: POST /query (RAG)
4. HTTP: Fetch config from GitHub (lsa-config.yaml, domain config)
5. HTTP: Fetch prompts from GitHub
6. Code: Build system prompt
7. LangChain Chat: Call LLM
8. Code: Extract decision record JSON
9. Code: Risk assessment
10. GitHub: Commit decision record
11. GitHub: Create issue (if review needed)
12. Respond to chat/webhook

**Example Workflow (Conceptual):**

```
Chat Trigger
    ↓
[Code: Normalize Query]
    ↓
[HTTP: RAG /query]
    ↓
[HTTP: Fetch LSA Config]
    ↓
[HTTP: Fetch Domain Config]
    ↓
[Code: Build System Prompt]
    ↓
[LangChain: LLM Agent]
    ↓
[Code: Extract Decision Record]
    ↓
[Code: Risk Assessment]
    ↓
[If: Risk Level]
   ├─ Low → [GitHub: Commit]
   └─ Medium/High → [GitHub: Commit + Issue]
    ↓
[Respond to User]
```

---

## 4. RAG Service: API Specification

### 4.1 Overview

The RAG service is a **separate microservice** (not part of n8n) that provides:
- Document ingestion (chunking, embedding, storage)
- Query-based retrieval (semantic search)

**Technology Stack (Suggested):**
- Python (FastAPI)
- Vector DB: ChromaDB, Weaviate, or Pinecone
- Embeddings: OpenAI `text-embedding-3-small` or open-source (e.g., `all-MiniLM-L6-v2`)

### 4.2 API Endpoints

#### 4.2.1 POST `/ingest-file`

**Purpose:** Ingest a document from GitHub into the RAG index.

**Request:**

```json
{
  "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
  "path": "knowledge/methodologies/VM0047_v1.3.pdf",
  "sha": "abc123def456...",
  "content_url": "https://raw.githubusercontent.com/.../VM0047_v1.3.pdf",
  "metadata": {
    "title": "VM0047 Afforestation, Reforestation and Revegetation v1.3",
    "version": "1.3",
    "classification": "verra-methodology",
    "domain": "carbon_markets"
  }
}
```

**Process:**
1. Download file from `content_url`
2. Split into chunks (e.g., 512 tokens, 128 overlap)
3. Generate embeddings for each chunk
4. Store in vector DB with metadata:
   - `repo`, `path`, `sha`
   - `chunk_id`, `page`, `section`
   - `title`, `version`, `classification`, `domain`

**Response:**

```json
{
  "status": "success",
  "file": "knowledge/methodologies/VM0047_v1.3.pdf",
  "sha": "abc123def456...",
  "chunks_created": 87,
  "timestamp": "2025-11-24T10:35:00Z"
}
```

**Error Handling:**
- 400: Invalid request (missing required fields)
- 404: File not found at `content_url`
- 409: File already ingested (idempotent based on SHA)
- 500: Internal error (embedding/storage failure)

#### 4.2.2 POST `/query`

**Purpose:** Retrieve relevant chunks for a query.

**Request:**

```json
{
  "query": "What are the eligibility criteria for VM0047 ARR projects in the Cerrado?",
  "top_k": 8,
  "filters": {
    "domain": "carbon_markets",
    "classification": "verra-methodology"
  }
}
```

**Process:**
1. Generate embedding for query
2. Perform semantic search in vector DB
3. Apply filters (domain, classification, etc.)
4. Return top K results with metadata

**Response:**

```json
{
  "query": "What are the eligibility criteria for VM0047 ARR projects in the Cerrado?",
  "chunks": [
    {
      "text": "Section 4.1: Eligibility Criteria. For ARR projects under VM0047, the project area must meet the following: (1) not classified as forest for at least 10 years prior to project start...",
      "source": "knowledge/methodologies/VM0047_v1.3.pdf",
      "sha": "abc123def456...",
      "metadata": {
        "page": 12,
        "section": "4.1",
        "methodology": "VM0047",
        "version": "1.3",
        "domain": "carbon_markets"
      },
      "score": 0.89
    },
    {
      "text": "The Cerrado biome requires specific additionality justification under Brazilian Forest Code Article 12...",
      "source": "knowledge/regulations/forest-code-2012.pdf",
      "sha": "def456ghi789...",
      "metadata": {
        "page": 8,
        "section": "Article 12",
        "domain": "carbon_markets"
      },
      "score": 0.82
    }
    // ... 6 more chunks
  ],
  "total_results": 8,
  "timestamp": "2025-11-24T10:40:00Z"
}
```

**Error Handling:**
- 400: Invalid request (missing query)
- 500: Internal error (embedding/retrieval failure)

#### 4.2.3 GET `/health`

**Purpose:** Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "vector_db": "connected",
  "embedding_service": "operational",
  "total_documents": 42,
  "total_chunks": 3847,
  "timestamp": "2025-11-24T10:45:00Z"
}
```

### 4.3 Implementation Notes

**Chunking Strategy:**
- PDF: Use `pymupdf` or `pdfplumber` to extract text by page
- Markdown: Split by headers + token count
- Chunk size: 512 tokens (adjust based on embedding model)
- Overlap: 128 tokens (to preserve context across boundaries)

**Embedding Model:**
- **Option 1:** OpenAI `text-embedding-3-small` (1536 dimensions, cost-effective)
- **Option 2:** Open-source `all-MiniLM-L6-v2` (384 dimensions, free)

**Vector Database:**
- **ChromaDB** — Simple, local, good for prototyping
- **Weaviate** — Production-grade, scalable, open-source
- **Pinecone** — Managed, serverless, easy to deploy

**Metadata Schema:**

```python
{
  "repo": str,           # GitHub repo name
  "path": str,           # File path in repo
  "sha": str,            # Git SHA of file
  "chunk_id": str,       # Unique chunk ID (sha + chunk index)
  "page": int,           # Page number (if PDF)
  "section": str,        # Section/header (if structured)
  "title": str,          # Document title
  "version": str,        # Document version
  "classification": str, # Document type (methodology, regulation, etc.)
  "domain": str,         # Domain tag (carbon_markets, regen_ag, etc.)
  "ingested_at": str     # ISO-8601 timestamp
}
```

---

## 5. Wiring the Three Layers Together

### 5.1 Data Flow: GitHub → RAG (Ingestion)

```
Developer pushes new PDF to /knowledge/
    ↓
GitHub webhook fires
    ↓
n8n Workflow 1 triggered
    ↓
n8n fetches file from GitHub (with SHA)
    ↓
n8n calls RAG: POST /ingest-file
    ↓
RAG downloads file, chunks, embeds, stores
    ↓
RAG returns: chunks_created, SHA
    ↓
n8n logs ingestion to GitHub (optional issue)
    ↓
n8n notifies team (Slack/email)
```

**Key Properties:**
- **Immutability:** File SHA ensures we always know which version was ingested
- **Idempotency:** Re-ingesting same SHA is a no-op (or updates metadata only)
- **Auditability:** GitHub issue log shows when/what was ingested

### 5.2 Data Flow: User Query → Decision → Audit (RAG-enabled Reasoning)

```
User asks: "Should we use VM0047 for this project?"
    ↓
n8n Workflow 2 triggered (Chat/API)
    ↓
n8n calls RAG: POST /query
    ↓
RAG returns: 8 chunks with sources (path, SHA, page)
    ↓
n8n fetches config from GitHub (lsa-config.yaml, domain config)
    ↓
n8n builds system prompt:
    - LARA v3 framework
    - Domain rules
    - Retrieved chunks [with SHA citations]
    ↓
n8n calls LLM (LangChain)
    ↓
LLM generates decision record (PICC format)
    ↓
n8n extracts JSON, validates schema
    ↓
n8n calculates risk score
    ↓
[Low risk] → n8n commits to GitHub (audit-trail/decisions/)
[Medium/High risk] → n8n commits + creates GitHub issue for review
    ↓
n8n responds to user:
    - Decision summary
    - Confidence level
    - Link to GitHub commit (audit trail)
    - Link to review issue (if needed)
```

**Key Properties:**
- **Traceability:** Every premise cites source (file path + SHA + page)
- **Immutability:** Decision record committed to Git (tamper-evident)
- **Falsifiability:** Falsifier criteria enable future validation
- **Human-in-the-loop:** Medium/high risk decisions require review

### 5.3 Closed-Loop Verification

**Periodic Falsifier Check (Automated):**

```
Cron job (weekly/monthly)
    ↓
Fetch all decision records from audit-trail/
    ↓
For each decision with falsifier:
    ↓
    Check if falsifier "by" date has passed
    ↓
    If yes: fetch metric (from external system or manual input)
    ↓
    If metric exceeds threshold:
        ↓
        Create GitHub issue: "FALSIFIER TRIGGERED: DEC-{id}"
        ↓
        Notify team for remediation
```

---

## 6. Integration with LARA, RTOA, and LSA

### 6.1 LARA v3 (Logic and Reasoning Architecture)

**P→I→C→C̄ Framework:**
- **P (Premises):** Facts, assumptions, expert opinions (from RAG)
- **I (Inferences):** Logical deductions (from LLM reasoning)
- **C (Contradictions):** Opposing evidence (from RAG + domain rules)
- **C̄ (Conclusion):** Final decision with confidence level

**Implementation in System Prompt:**

```markdown
# LARA v3 Reasoning Instructions

You are operating under LARA v3 (P→I→C→C̄). Follow this structure:

1. PREMISES (P): Extract from retrieved chunks [#1], [#2], etc.
   - Type: FACT (requires 2+ sources), ASSUMPTION, EXPERT_OPINION
   - Cite: [#N] chunk number + source file + SHA + page

2. INFERENCES (I): Logical steps from premises
   - Format: "From P1, P2 → I1: <inference>"
   - No leaps; each inference must follow from stated premises

3. CONTRADICTIONS (C): Opposing evidence or limitations
   - Actively search for: conflicting data, edge cases, alternative interpretations
   - Cite sources as with premises

4. CONCLUSION (C̄): Final decision
   - Confidence: HIGH (strong evidence, few contradictions), MEDIUM, LOW
   - Explicit rationale referencing P, I, C

5. FALSIFIER: Popperian validation
   - Metric: what to measure
   - Threshold: when to invalidate decision
   - By: deadline (ISO-8601)
   - Action: remediation if falsified
```

### 6.2 RTOA v3 (Reality-Tested Ontological Architecture)

**Constraints:**
- **No identity:** Don't assign persistent identity to entities (e.g., "the farm" vs "a 8000 ha area in Cerrado")
- **No metaphysics:** Only observable, measurable, falsifiable claims
- **Drift detection:** Monitor when real-world observations diverge from model predictions

**Implementation in System Prompt:**

```markdown
# RTOA v3 Environmental Constraints

1. REALITY PRIMACY: Only reference observable, measurable facts
   - ✅ "8,000 ha area at coordinates X, classified as Cerrado per MapBiomas 2023"
   - ❌ "the farm" (without specific coordinates/boundaries)

2. NO IDENTITY: Use descriptive properties, not persistent names
   - ✅ "An ARR project meeting VM0047 criteria in Cerrado biome"
   - ❌ "Project Alpha" (unless it's a formal registered name with evidence)

3. DRIFT DETECTION: Flag when observations contradict model
   - If auditor finds non-conformance: update decision record, trigger falsifier

4. FALSIFIABILITY: Every claim must have measurable validation criteria
   - ✅ "Additionality demonstrated by <metric> < <threshold> by <date>"
   - ❌ "Additionality is clearly present" (no measurable criteria)
```

### 6.3 LSA Application Protocol

**Components (Already Implemented):**
- Decision Records (PICC-1.0 schema)
- GitHub Issues storage
- Cryptographic hashing (SHA-256)
- n8n workflow automation
- Confidence propagation

**What This Architecture Adds:**
- **RAG layer:** Evidence retrieval with Git SHA provenance
- **Config layer:** Domain-specific rules in version control
- **Closed-loop falsifier checks:** Automated validation pipeline

---

## 7. Implementation Roadmap

### Phase 1: Directory Structure + Config (Week 1)
- [ ] Create `/knowledge/`, `/config/`, `/audit-trail/` directories
- [ ] Add README.md to each directory with structure guidelines
- [ ] Create `lsa-config.yaml`, `domain-carbon-markets.yaml`
- [ ] Write LARA v3 + RTOA v3 system prompts

### Phase 2: RAG Service (Week 2-3)
- [ ] Implement POST `/ingest-file` endpoint
- [ ] Implement POST `/query` endpoint
- [ ] Set up vector database (ChromaDB or Weaviate)
- [ ] Test with sample PDFs from Verra

### Phase 3: n8n Workflow 1 (Week 3)
- [ ] Create "Index GitHub Updates" workflow
- [ ] Set up GitHub webhook for `/knowledge/**`
- [ ] Test ingestion pipeline with sample files

### Phase 4: n8n Workflow 2 (Week 4-5)
- [ ] Create "YARA Lógica RAG-enabled" workflow
- [ ] Integrate RAG query → LLM → audit pipeline
- [ ] Test with sample carbon markets queries
- [ ] Implement risk assessment + routing logic

### Phase 5: Audit + Review (Week 6)
- [ ] Set up GitHub issue templates for human review
- [ ] Create dashboard for decision record search
- [ ] Implement falsifier check automation (cron job)

### Phase 6: Production Hardening (Week 7+)
- [ ] Add authentication (HMAC for webhooks, API keys for RAG)
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Implement rate limiting + error handling
- [ ] Write operational runbooks

---

## 8. Security & Compliance

### 8.1 Authentication
- **n8n Webhooks:** HMAC-SHA256 (X-Signature-256 header)
- **RAG API:** API key authentication (X-API-Key header)
- **GitHub API:** Personal Access Token (PAT) or GitHub App

### 8.2 Data Classification
- **Public (P0):** Specifications, schemas, public methodologies
- **Internal (P1):** Configuration files, system prompts
- **Confidential (P2):** Project-specific documents, decision records (if business-sensitive)

### 8.3 Secrets Management
- Store secrets in environment variables (not in Git)
- Use n8n credentials store for API keys
- Rotate keys quarterly

### 8.4 Audit Requirements
- All decision records committed to Git (tamper-evident)
- All API calls logged (timestamp, user, endpoint, response status)
- All human reviews recorded in GitHub issues

---

## 9. Monitoring & Observability

### 9.1 Key Metrics

**RAG Service:**
- `rag_ingest_total` — Total documents ingested
- `rag_ingest_duration_seconds` — Ingestion latency
- `rag_query_total` — Total queries processed
- `rag_query_duration_seconds` — Query latency
- `rag_chunks_returned` — Average chunks per query

**n8n Workflows:**
- `n8n_workflow_executions_total` — Total executions
- `n8n_workflow_errors_total` — Failed executions
- `n8n_workflow_duration_seconds` — Execution time

**LSA System:**
- `lsa_decisions_total` — Total decisions created
- `lsa_decisions_by_confidence` — Breakdown by confidence level
- `lsa_decisions_by_risk` — Breakdown by risk level
- `lsa_human_reviews_pending` — Decisions awaiting review
- `lsa_falsifiers_triggered_total` — Falsifiers that failed validation

### 9.2 Alerting

**Critical Alerts:**
- RAG service down (health check fails)
- n8n workflow error rate >5%
- Decision record schema validation failures
- Falsifier triggered (requires immediate review)

**Warning Alerts:**
- RAG query latency >5s (p95)
- GitHub API rate limit approaching (>80%)
- Pending human reviews >10

---

## 10. References

### Internal Documentation
- [LSA Decision Record System](/lsa/README.md)
- [LSA PICC Specification](/lsa/spec/LSA_PICC.md)
- [RAG Policy](/rag/spec/RAG_POLICY.md)
- [YARA Taxonomy](/docs/YARA_TAXONOMY.md)

### External Standards
- Verra VCS Program Guide: https://verra.org/programs/verified-carbon-standard/
- VM0047 Methodology: https://verra.org/methodologies/vm0047/
- Brazilian Forest Code (Lei 12.651/2012): http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12651.htm

---

**Document Owner:** Alter Agro Technical Team
**Last Updated:** 2025-11-24
**Version:** 1.0
**Status:** ✅ Implementation Specification

© 2025 Alter Agro Ltda. All rights reserved.
