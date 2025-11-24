# Knowledge Base

**Purpose:** Source documents for RAG (Retrieval-Augmented Generation) system.

All documents in this directory are ingested into the vector database and used as evidence sources for YARA Lógica decision-making.

---

## Directory Structure

```
knowledge/
├── methodologies/      # Carbon credit methodologies (Verra, Gold Standard, etc.)
├── regulations/        # Brazilian laws, regulations, environmental codes
├── regen-docs/         # Regenerative agriculture documentation
├── projects/           # Project-specific documents (PDDs, feasibility studies)
└── README.md          # This file
```

---

## Document Requirements

### 1. File Naming Convention

Use descriptive, version-controlled names:

- **Methodologies:** `{Standard}_{ID}_v{Version}.{ext}`
  - Example: `VM0047_v1.3.pdf`, `VM0042_v2.0.pdf`

- **Regulations:** `{topic}-{identifier}.{ext}`
  - Example: `forest-code-lei-12651-2012.pdf`, `lgpd-lei-13709-2018.pdf`

- **Project docs:** `{project-id}-{type}-{date}.{ext}`
  - Example: `PROJ001-PDD-2025-01-15.pdf`, `PROJ001-feasibility-study-2025-01-10.pdf`

### 2. Supported Formats

- **PDF** — Primary format for official documents
- **Markdown** — For curated summaries, technical notes
- **TXT** — Plain text extracts

### 3. Metadata Requirements

Each subdirectory must maintain a `README.md` with document metadata:

```yaml
documents:
  - file: VM0047_v1.3.pdf
    title: "VM0047 Afforestation, Reforestation and Revegetation"
    version: "1.3"
    published: "2023-06-15"
    source_url: "https://verra.org/methodologies/vm0047/"
    classification: "verra-methodology"
    domain: "carbon_markets"
    language: "en"
    sha256: "<computed by Git>"
```

### 4. Version Control

- All documents are tracked in Git
- Git SHA serves as immutable version identifier
- Updates to documents trigger re-ingestion into RAG

---

## Document Classification

| Classification | Description | Examples |
|:--------------|:------------|:---------|
| `verra-methodology` | Verra VCS methodologies | VM0047, VM0042, VM0010 |
| `gold-standard-methodology` | Gold Standard methodologies | GS-specific docs |
| `regulation-brazil` | Brazilian federal/state laws | Forest Code, LGPD |
| `regulation-international` | International agreements | Paris Agreement, UNFCCC |
| `regen-agriculture` | Regenerative ag best practices | Soil health, grazing management |
| `project-document` | Project-specific artifacts | PDDs, monitoring reports |
| `technical-reference` | Scientific papers, technical guides | Peer-reviewed studies |

---

## Domain Tags

Use domain tags to filter retrieval:

- `carbon_markets` — Carbon credit methodologies, baselines, additionality
- `regenerative_agriculture` — Soil carbon, biodiversity, holistic grazing
- `compliance_legal` — Laws, regulations, compliance requirements
- `finance_audit` — Financial additionality, audit standards

---

## Ingestion Pipeline

### Automatic Ingestion (via n8n Workflow)

When you push a new file to this directory:

1. GitHub webhook fires on push event
2. n8n Workflow 1 ("Index GitHub Updates") triggers
3. n8n fetches file + Git SHA from GitHub
4. n8n calls RAG service: `POST /ingest-file`
5. RAG service:
   - Downloads file
   - Splits into chunks (512 tokens, 128 overlap)
   - Generates embeddings
   - Stores in vector DB with metadata (source, SHA, page)
6. n8n logs ingestion result to GitHub issue

### Manual Ingestion

If automatic ingestion fails, manually trigger via RAG API:

```bash
curl -X POST https://rag.alter-agro.com/ingest-file \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $RAG_API_KEY" \
  -d '{
    "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
    "path": "knowledge/methodologies/VM0047_v1.3.pdf",
    "sha": "abc123...",
    "content_url": "https://raw.githubusercontent.com/.../VM0047_v1.3.pdf",
    "metadata": {
      "title": "VM0047 ARR v1.3",
      "classification": "verra-methodology",
      "domain": "carbon_markets"
    }
  }'
```

---

## Document Quality Standards

### Evidence Sources (for LSA Decision Records)

- **FACT premises require 2+ independent sources**
- Sources must be:
  - Publicly accessible (HTTPS URLs)
  - Authoritative (government, academic, industry standards)
  - Dated (publication/version date)

### Source Authority Hierarchy

1. **Tier 1 (Highest Authority)**
   - Government regulations (laws, executive orders)
   - International standards (ISO, ASTM)
   - Regulatory body guidance (Verra, Gold Standard)

2. **Tier 2 (High Authority)**
   - Peer-reviewed academic research
   - Technical standards organizations
   - Recognized industry associations

3. **Tier 3 (Moderate Authority)**
   - Vendor technical documentation
   - Industry whitepapers
   - Expert opinions with credentials

---

## Usage in YARA Lógica

### RAG Query Flow

1. User asks: *"What are VM0047 eligibility criteria for Cerrado?"*
2. n8n calls RAG: `POST /query`
3. RAG returns top 8 chunks:
   ```json
   {
     "text": "Section 4.1: Eligibility Criteria...",
     "source": "knowledge/methodologies/VM0047_v1.3.pdf",
     "sha": "abc123...",
     "metadata": {
       "page": 12,
       "methodology": "VM0047",
       "domain": "carbon_markets"
     }
   }
   ```
4. n8n builds LLM prompt with chunks + Git SHA citations
5. LLM generates decision record citing [#1], [#2], etc.
6. Decision record committed to `audit-trail/` with source provenance

---

## Maintenance

### Adding New Documents

1. Add file to appropriate subdirectory
2. Update subdirectory `README.md` with metadata
3. Commit to Git with message: `docs: add {document name}`
4. Push to GitHub → automatic ingestion via n8n

### Updating Existing Documents

1. Replace file (keep same name if minor update, add version suffix if major)
2. Update metadata in `README.md`
3. Commit with message: `docs: update {document name} to v{version}`
4. Push → re-ingestion triggered (old version retained with old SHA)

### Removing Documents

1. Delete file
2. Update `README.md`
3. Commit with message: `docs: remove {document name} - {reason}`
4. RAG service: manually delete chunks via API (or wait for cleanup cron)

---

## Security & Compliance

### Data Classification

- **Public (P0):** Publicly available methodologies, regulations
- **Internal (P1):** Curated summaries, internal technical notes
- **Confidential (P2):** Project-specific documents (use private repo if sensitive)

### No PII or Secrets

- Do NOT commit files containing:
  - Personal identifiable information (PII)
  - Credentials, API keys, passwords
  - Proprietary business-sensitive data (unless in private repo)

### Access Control

- Public repo: anyone can read
- Write access: Alter Agro team only
- Confidential docs: use private repository with strict access controls

---

## Support

**Questions:** See [THREE_LAYER_ARCHITECTURE.md](/docs/THREE_LAYER_ARCHITECTURE.md)
**Issues:** Create GitHub issue with label `knowledge-base`
**Contact:** contatoalteragro@gmail.com

---

**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
