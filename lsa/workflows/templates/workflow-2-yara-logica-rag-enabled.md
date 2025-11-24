# Workflow 2: YARA Lógica (RAG-enabled)

**Purpose:** Process user queries using RAG, generate LSA decision records, commit to Git.

**Trigger:** Chat trigger, HTTP webhook, or manual trigger

---

## Workflow Overview

```
User Query
    ↓
[1. Chat/HTTP Trigger]
    ↓
[2. Code: Normalize Query]
    ↓
[3. HTTP: RAG /query]
    ↓
[4. HTTP: Fetch LSA Config]
    ↓
[5. HTTP: Fetch Domain Config]
    ↓
[6. HTTP: Fetch System Prompt]
    ↓
[7. Code: Build LLM System Prompt]
    ↓
[8. LangChain: Call LLM]
    ↓
[9. Code: Extract Decision Record JSON]
    ↓
[10. Code: Risk Assessment]
    ↓
[11. GitHub: Commit Decision Record]
    ↓
[12. If: Medium/High Risk]
    ├─ Yes → [13. GitHub: Create Review Issue]
    └─ No → Skip
    ↓
[14. Respond to User]
```

---

## Node Configuration

### Node 1: Chat/HTTP Trigger

**Option A: Chat Trigger** (for chat interfaces)

**Node Type:** `n8n-nodes-base.webhook`

**Settings:**
- **Path:** `/webhook/yara-logica-chat`
- **Method:** POST

**Expected Payload:**

```json
{
  "query": "Should we use VM0047 or VM0042 for an 8,000 ha ARR project in the Cerrado?",
  "context": {
    "project_id": "PROJ001",
    "area_ha": 8000,
    "biome": "cerrado",
    "activities": ["tree_planting", "rotational_grazing"]
  },
  "domain": "carbon_markets"
}
```

**Option B: HTTP Webhook** (for API integration)

Same as Option A, but with API key authentication:
- Header: `X-API-Key: {{$env.YARA_API_KEY}}`

---

### Node 2: Code – Normalize Query

**Node Type:** `n8n-nodes-base.function`

**Purpose:** Extract and standardize query parameters.

**Code:**

```javascript
const input = $input.first().json;

// Extract query and context
const normalized = {
  query: input.query || input.message || '',
  domain: input.domain || 'carbon_markets',
  context: input.context || {},
  timestamp: new Date().toISOString(),
  request_id: `REQ-${Date.now()}`
};

// Validate query
if (!normalized.query || normalized.query.trim() === '') {
  throw new Error('Query text is required');
}

// Add metadata
normalized.metadata = {
  biome: input.context?.biome || null,
  area_ha: input.context?.area_ha || null,
  project_type: input.context?.project_type || null
};

return [{ json: normalized }];
```

**Output:**

```json
{
  "query": "Should we use VM0047...",
  "domain": "carbon_markets",
  "context": {...},
  "timestamp": "2025-11-24T10:30:00Z",
  "request_id": "REQ-1700820600000",
  "metadata": {
    "biome": "cerrado",
    "area_ha": 8000,
    "project_type": null
  }
}
```

---

### Node 3: HTTP Request – RAG /query

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** POST
- **URL:** `{{$env.RAG_API_URL}}/query`
- **Authentication:** Header Auth
  - Header Name: `X-API-Key`
  - Header Value: `{{$env.RAG_API_KEY}}`

**Body:**

```json
{
  "query": "{{$json.query}}",
  "top_k": 8,
  "filters": {
    "domain": "{{$json.domain}}",
    "classification": ["verra-methodology", "regulation-brazil"]
  },
  "min_score": 0.7
}
```

**Response:**

```json
{
  "chunks": [
    {
      "chunk_id": "abc-123",
      "text": "...",
      "source": "knowledge/methodologies/VM0047_v1.3.pdf",
      "sha": "abc123...",
      "metadata": {...},
      "score": 0.89
    },
    ...
  ],
  "total_results": 8
}
```

---

### Node 4: HTTP Request – Fetch LSA Config

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** GET
- **URL:** `https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/config/lsa-config.yaml`

**Output:** YAML content (as text)

---

### Node 5: HTTP Request – Fetch Domain Config

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** GET
- **URL:** `https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/config/domain-{{$json.domain}}.yaml`
  - Example: `domain-carbon-markets.yaml`

**Fallback:** If domain config doesn't exist (404), use empty object.

**Output:** YAML content (as text)

---

### Node 6: HTTP Request – Fetch System Prompt

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** GET
- **URL:** `https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/config/prompts/yara-logica-system.md`

**Output:** Markdown content (as text)

---

### Node 7: Code – Build LLM System Prompt

**Node Type:** `n8n-nodes-base.function`

**Purpose:** Combine system prompt, domain rules, and RAG chunks into final prompt.

**Code:**

```javascript
const query = $('Normalize Query').first().json;
const ragResponse = $('RAG Query').first().json;
const systemPromptTemplate = $('Fetch System Prompt').first().json;
const domainConfig = $('Fetch Domain Config').first().json;

// Format RAG chunks
const chunksText = ragResponse.chunks.map((chunk, i) => {
  return `[#${i+1}] ${chunk.text}
Source: ${chunk.source} (sha: ${chunk.sha.substring(0, 8)}, page: ${chunk.metadata.page || 'N/A'})`;
}).join('\n\n');

// Extract domain rules (parse YAML if needed, or use as-is)
const domainRulesText = `
DOMAIN: ${query.domain}

Key Rules (from domain config):
${domainConfig}
`;

// Build final system prompt
const systemMessage = `
${systemPromptTemplate}

---

## CONTEXT (Retrieved from RAG)

${chunksText}

---

## DOMAIN RULES

${domainRulesText}

---

Now, process the following query using LARA (P→I→C→C̄) reasoning:
`;

// Build user message
const userMessage = query.query;

return [{
  json: {
    system_message: systemMessage,
    user_message: userMessage,
    rag_chunks_count: ragResponse.chunks.length,
    request_id: query.request_id
  }
}];
```

**Output:**

```json
{
  "system_message": "<full system prompt with RAG chunks and domain rules>",
  "user_message": "<user query>",
  "rag_chunks_count": 8,
  "request_id": "REQ-1700820600000"
}
```

---

### Node 8: LangChain – Call LLM

**Node Type:** `n8n-nodes-langchain.lmChatOpenAi` (or similar)

**Settings:**
- **Model:** `gpt-4-turbo-preview` (or `claude-3-5-sonnet-20241022`)
- **Temperature:** 0.1 (low for consistency)
- **Max Tokens:** 4096
- **System Message:** `{{$json.system_message}}`
- **User Message:** `{{$json.user_message}}`

**Response Format:** Text (LLM response with JSON decision record)

**Expected Output:**

```
<reasoning text>

<<<BEGIN_DECISION_RECORD>>>
{
  "version": "PICC-1.0",
  "query": "...",
  "premises": [...],
  "inferences": [...],
  "contradictions": [...],
  "conclusion": {...},
  "falsifier": {...}
}
<<<END_DECISION_RECORD>>>
```

---

### Node 9: Code – Extract Decision Record JSON

**Node Type:** `n8n-nodes-base.function`

**Purpose:** Parse JSON from LLM response, validate schema.

**Code:**

```javascript
const llmResponse = $input.first().json.text || $input.first().json.output;

// Extract JSON between delimiters
const startDelimiter = '<<<BEGIN_DECISION_RECORD>>>';
const endDelimiter = '<<<END_DECISION_RECORD>>>';

const startIndex = llmResponse.indexOf(startDelimiter);
const endIndex = llmResponse.indexOf(endDelimiter);

if (startIndex === -1 || endIndex === -1) {
  throw new Error('Decision record delimiters not found in LLM response');
}

const jsonText = llmResponse.substring(
  startIndex + startDelimiter.length,
  endIndex
).trim();

// Parse JSON
let decisionRecord;
try {
  decisionRecord = JSON.parse(jsonText);
} catch (e) {
  throw new Error(`Invalid JSON in decision record: ${e.message}`);
}

// Validate required fields
const requiredFields = ['version', 'query', 'premises', 'inferences', 'conclusion', 'falsifier'];
for (const field of requiredFields) {
  if (!decisionRecord[field]) {
    throw new Error(`Missing required field: ${field}`);
  }
}

// Add metadata
const query = $('Normalize Query').first().json;
const ragResponse = $('RAG Query').first().json;

decisionRecord.metadata = {
  request_id: query.request_id,
  timestamp: query.timestamp,
  domain: query.domain,
  rag_chunks_used: ragResponse.chunks.length,
  biome: query.metadata.biome,
  area_ha: query.metadata.area_ha
};

// Generate decision ID
const date = new Date();
const decisionId = `DEC-${date.toISOString().split('T')[0].replace(/-/g, '')}-${String(date.getHours()).padStart(2, '0')}${String(date.getMinutes()).padStart(2, '0')}${String(date.getSeconds()).padStart(2, '0')}`;

decisionRecord.id = decisionId;

return [{ json: decisionRecord }];
```

**Output:** Validated decision record JSON with metadata

---

### Node 10: Code – Risk Assessment

**Node Type:** `n8n-nodes-base.function`

**Purpose:** Calculate risk level based on confidence, domain rules, and thresholds.

**Code:**

```javascript
const decision = $input.first().json;
const lsaConfig = $('Fetch LSA Config').first().json;

// Parse confidence level
const confidence = decision.conclusion.confidence;

// Count contradictions
const contradictionCount = decision.contradictions.length;

// Calculate risk score
let riskLevel = 'low';

// Rule 1: Confidence-based
if (confidence === 'LOW') {
  riskLevel = 'high';
} else if (confidence === 'MEDIUM') {
  riskLevel = 'medium';
}

// Rule 2: Contradiction threshold (if HIGH confidence but many contradictions)
if (confidence === 'HIGH' && contradictionCount > 2) {
  riskLevel = 'medium';
}

// Rule 3: Domain-specific overrides (carbon markets)
if (decision.domain === 'carbon_markets') {
  // Check if query is about methodology selection or additionality
  const criticalKeywords = ['methodology', 'additionality', 'baseline'];
  const isCritical = criticalKeywords.some(keyword =>
    decision.query.toLowerCase().includes(keyword)
  );

  if (isCritical && riskLevel === 'low') {
    riskLevel = 'medium'; // Upgrade to medium for critical decisions
  }
}

// Determine auto-approval
const autoApproved = (riskLevel === 'low');

// Add to decision metadata
decision.metadata.risk_level = riskLevel;
decision.metadata.auto_approved = autoApproved;
decision.metadata.contradiction_count = contradictionCount;

return [{ json: decision }];
```

**Output:** Decision record with risk assessment metadata

---

### Node 11: GitHub – Commit Decision Record

**Node Type:** `n8n-nodes-base.httpRequest` (GitHub API)

**Settings:**
- **Method:** PUT
- **URL:** `https://api.github.com/repos/ourobrancopedro-rgb/alter-agro-yara-logica/contents/audit-trail/decisions/{{$now.format('YYYY-MM')}}/{{$json.id}}.json`
- **Authentication:** Header Auth
  - Header Name: `Authorization`
  - Header Value: `token {{$env.GITHUB_TOKEN}}`

**Body:**

```json
{
  "message": "LSA: {{$json.id}} - {{$json.conclusion.decision}}",
  "content": "{{$json | base64encode}}",
  "branch": "main"
}
```

**Note:** GitHub API requires base64-encoded content.

**Alternative (simpler):** Use a custom API endpoint that wraps Git operations.

**Response:** GitHub commit response with SHA

---

### Node 12: If – Medium/High Risk?

**Node Type:** `n8n-nodes-base.if`

**Condition:**

```javascript
{{$json.metadata.risk_level}} !== 'low'
```

**True:** Go to Node 13 (Create Review Issue)
**False:** Skip to Node 14 (Respond to User)

---

### Node 13: GitHub – Create Review Issue

**Node Type:** `n8n-nodes-base.github`

**Settings:**
- **Resource:** Issue
- **Operation:** Create
- **Repository Owner:** `ourobrancopedro-rgb`
- **Repository Name:** `alter-agro-yara-logica`
- **Title:** `[LSA Review] {{$json.id}}: {{$json.conclusion.decision}}`
- **Body:**

```markdown
# LSA Decision Record Review Required

**Decision ID:** {{$json.id}}
**Timestamp:** {{$json.metadata.timestamp}}
**Domain:** {{$json.domain}}
**Risk Level:** {{$json.metadata.risk_level}}
**Confidence:** {{$json.conclusion.confidence}}

---

## Query

{{$json.query}}

---

## Decision

{{$json.conclusion.decision}}

**Rationale:**
{{$json.conclusion.rationale}}

---

## Premises

{{#each $json.premises}}
**{{this.id}}** [{{this.type}}]: {{this.text}}

Sources:
{{#each this.sources}}
- {{this.url}} (sha: {{this.sha}}, page: {{this.page}})
{{/each}}

{{/each}}

---

## Contradictions

{{#each $json.contradictions}}
**{{this.id}}**: {{this.text}}

{{#if this.sources}}
Sources:
{{#each this.sources}}
- {{this.url}}
{{/each}}
{{/if}}

{{/each}}

---

## Falsifier

**Metric:** {{$json.falsifier.metric}}
**Threshold:** {{$json.falsifier.threshold}}
**By:** {{$json.falsifier.by}}
**Action:** {{$json.falsifier.action}}

---

## RAG Chunks Used

{{$json.metadata.rag_chunks_used}} chunks retrieved from knowledge base.

---

## Review Checklist

- [ ] Premises validated (sources correct, citations accurate)
- [ ] Inferences logical (no unsupported leaps)
- [ ] Contradictions considered (opposing evidence addressed)
- [ ] Conclusion justified by evidence
- [ ] Falsifier appropriate (measurable, time-bound)
- [ ] Decision aligns with domain rules

**Reviewer:** Please comment with `APPROVED`, `APPROVED WITH CONDITIONS`, or `REJECTED`.
```

- **Labels:**
  - `lsa`
  - `needs-review`
  - `decision-record`
  - `risk-{{$json.metadata.risk_level}}`
  - `domain-{{$json.domain}}`
  - `confidence-{{$json.conclusion.confidence | lower}}`

---

### Node 14: Respond to User

**Node Type:** `n8n-nodes-base.respondToWebhook`

**Settings:**
- **Response Code:** 200
- **Response Body:** JSON

**Body:**

```json
{
  "status": "success",
  "decision_id": "{{$json.id}}",
  "decision": "{{$json.conclusion.decision}}",
  "confidence": "{{$json.conclusion.confidence}}",
  "risk_level": "{{$json.metadata.risk_level}}",
  "auto_approved": {{$json.metadata.auto_approved}},
  "review_required": {{!$json.metadata.auto_approved}},
  "commit_sha": "{{$('GitHub Commit').first().json.commit.sha}}",
  "review_issue_url": "{{$json.metadata.risk_level !== 'low' ? $('GitHub Issue').first().json.html_url : null}}",
  "timestamp": "{{$json.metadata.timestamp}}"
}
```

**User-Facing Summary:**

```json
{
  "summary": {
    "question": "Should we use VM0047 or VM0042?",
    "recommendation": "Use VM0047 as primary methodology",
    "confidence": "MEDIUM",
    "key_points": [
      "VM0047 applies to tree planting (ARR)",
      "Grazing component adds uncertainty",
      "Review recommended due to mixed activities"
    ],
    "next_steps": [
      "Human review required (medium risk)",
      "See GitHub issue for review checklist",
      "Validation audit will verify methodology"
    ]
  }
}
```

---

## Environment Variables

| Variable | Description | Example |
|:---------|:------------|:--------|
| `RAG_API_URL` | RAG service base URL | `https://rag.alter-agro.com` |
| `RAG_API_KEY` | API key for RAG service | `ak_live_abc123...` |
| `GITHUB_TOKEN` | GitHub PAT with repo access | `ghp_abc123...` |
| `OPENAI_API_KEY` | OpenAI API key (for LLM) | `sk-proj-abc123...` |
| `YARA_API_KEY` | API key for YARA webhook | `yk_abc123...` |

---

## Testing

### Test Query 1: Simple Methodology Selection

```bash
curl -X POST https://n8n.alter-agro.com/webhook/yara-logica-chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I use VM0047 for a 5,000 ha ARR project in the Cerrado?",
    "domain": "carbon_markets",
    "context": {
      "area_ha": 5000,
      "biome": "cerrado"
    }
  }'
```

**Expected:** LOW risk, auto-approved (if straightforward ARR project)

### Test Query 2: Complex Multi-Activity Project

```bash
curl -X POST https://n8n.alter-agro.com/webhook/yara-logica-chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should we use VM0047 or VM0042 for an 8,000 ha project with tree planting AND rotational grazing?",
    "domain": "carbon_markets",
    "context": {
      "area_ha": 8000,
      "biome": "cerrado",
      "activities": ["tree_planting", "rotational_grazing"]
    }
  }'
```

**Expected:** MEDIUM risk, human review required (mixed activities)

---

## Monitoring

### Key Metrics

- **Query latency:** Time from trigger to response
- **LLM success rate:** % of queries with valid JSON output
- **Auto-approval rate:** % of LOW risk decisions
- **Review turnaround:** Time from review issue creation to resolution

### Alerts

- LLM JSON parsing failures >10%
- Risk assessment errors
- GitHub commit failures
- Review issues not addressed within SLA (24 hours for medium, 4 hours for high)

---

## Troubleshooting

### Issue: LLM returns invalid JSON

**Solution:** Improve system prompt, add examples, increase temperature (slightly) for creativity, or use structured output API.

### Issue: RAG returns no results

**Solution:** Check if knowledge base is populated, lower `min_score` threshold, broaden filters.

### Issue: GitHub commit fails (409 conflict)

**Solution:** File already exists. Use unique decision ID or add timestamp to filename.

---

**Version:** 1.0
**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
