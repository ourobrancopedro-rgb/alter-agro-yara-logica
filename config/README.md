# Configuration Files

**Purpose:** LSA system configurations, domain rules, and system prompts for YARA Lógica.

All configuration files are version-controlled in Git to ensure:
- Reproducibility (every decision references specific config version)
- Auditability (changes tracked with commit history)
- Rollback capability (revert to previous configs if needed)

---

## Directory Structure

```
config/
├── lsa-config.yaml                 # System-level LSA configuration
├── domain-carbon-markets.yaml      # Carbon markets domain rules
├── domain-regenerative-ag.yaml     # Regenerative agriculture rules
├── prompts/                        # System prompts for LLM
│   ├── lara-v3-base.md            # Core LARA reasoning framework
│   ├── rtoa-v3-ambient.md         # RTOA environmental constraints
│   └── yara-logica-system.md      # YARA Lógica system prompt
└── README.md                       # This file
```

---

## Configuration Files

### 1. `lsa-config.yaml`

**Purpose:** Core LSA system configuration.

**Contents:**
- Evidence requirements (FACT, ASSUMPTION, EXPERT_OPINION)
- Confidence level thresholds (HIGH, MEDIUM, LOW)
- Risk assessment rules
- Falsifier policies
- Audit trail settings

**Usage:** Loaded by n8n workflow before every decision.

**Example:**
```yaml
version: "1.0"
lsa:
  evidence_requirements:
    FACT:
      min_sources: 2
      source_types: ["https", "git+https"]
  confidence_levels:
    HIGH:
      min_premises: 3
      max_contradictions: 1
  risk_assessment:
    auto_approve_threshold: "low"
    human_review_threshold: "medium"
```

### 2. `domain-carbon-markets.yaml`

**Purpose:** Domain-specific rules for carbon markets.

**Contents:**
- Methodology selection criteria
- Additionality requirements
- Baseline/project scenario validation rules
- Risk thresholds for carbon projects
- Regulatory compliance checks (Verra, Gold Standard)

**Usage:** Loaded when query has `domain: carbon_markets` tag.

**Example:**
```yaml
domain: carbon_markets
version: "1.0"
rules:
  methodology_selection:
    ARR:
      eligible_methodologies: ["VM0047", "VM0010"]
      eligibility_criteria:
        - "Land not classified as forest for ≥10 years"
        - "No displacement of existing agriculture"
  additionality:
    required: true
    validation_methods: ["financial", "barrier", "common_practice"]
```

### 3. `domain-regenerative-ag.yaml`

**Purpose:** Domain-specific rules for regenerative agriculture.

**Contents:**
- Soil carbon sequestration protocols
- Grazing management best practices
- Biodiversity requirements
- Water cycle restoration criteria

**Usage:** Loaded when query has `domain: regenerative_agriculture` tag.

### 4. `prompts/`

**Purpose:** System prompts for LLM agents.

**Files:**
- **`lara-v3-base.md`** — Core LARA (P→I→C→C̄) reasoning instructions
- **`rtoa-v3-ambient.md`** — RTOA constraints (no identity, reality-primacy, falsifiability)
- **`yara-logica-system.md`** — Complete YARA Lógica system prompt (combines LARA + RTOA + domain)

---

## How Configs Are Used in n8n Workflow

### Workflow 2: YARA Lógica (RAG-enabled)

```
User Query
    ↓
n8n: Identify domain (e.g., carbon_markets)
    ↓
n8n: Fetch configs from GitHub
    ├─ lsa-config.yaml (always)
    ├─ domain-carbon-markets.yaml (if domain = carbon_markets)
    └─ prompts/yara-logica-system.md
    ↓
n8n: Call RAG: POST /query (get chunks)
    ↓
n8n: Build LLM prompt:
    System = LARA + RTOA + Domain Rules + RAG Chunks (with SHA citations)
    User = Normalized query
    ↓
n8n: Call LLM → get decision record
    ↓
n8n: Validate against lsa-config.yaml thresholds
    ↓
n8n: Commit decision to audit-trail/ (with config Git SHA)
```

**Key:** Every decision record includes:
- `config_version`: Git SHA of config files used
- `domain`: Which domain config was applied
- `prompt_version`: Git SHA of system prompt

This ensures **full reproducibility** — you can always see which rules were active when a decision was made.

---

## Version Control Best Practices

### Making Changes

1. **Edit config file**
   - Update `version` field (e.g., `1.0` → `1.1`)
   - Document changes in commit message

2. **Test changes**
   - Run test queries against updated config
   - Verify decision records meet expectations

3. **Commit with clear message**
   ```bash
   git commit -m "config: increase FACT min_sources from 2 to 3 for HIGH confidence"
   ```

4. **Push to GitHub**
   - n8n workflows automatically use latest config from `main` branch
   - (Alternative: pin to specific SHA for stable production)

### Breaking Changes

If a config change breaks existing workflows:
- Increment major version (e.g., `1.5` → `2.0`)
- Add migration notes in commit message
- Update n8n workflows if needed

---

## Security & Compliance

### Data Classification

- **Internal (P1):** Config files, domain rules
- **Confidential (P2):** Custom prompts with proprietary business logic (if any)

### No Secrets in Configs

- Do NOT commit:
  - API keys
  - Passwords
  - Access tokens
  - Proprietary algorithms (if trade secret)

- Use environment variables or n8n credential store for secrets

### Access Control

- Read access: Alter Agro team + approved auditors
- Write access: Technical lead only
- All changes require review (pull request + approval)

---

## Maintenance

### Regular Reviews

- **Quarterly:** Review domain rules for regulatory updates
- **Annually:** Audit lsa-config.yaml thresholds for effectiveness
- **As-needed:** Update prompts when LARA/RTOA specs evolve

### Deprecation Policy

- Old configs are never deleted (preserved in Git history)
- Deprecated rules marked with `deprecated: true` and `deprecated_reason`
- Archived configs moved to `config/archive/` after 1 year

---

## Support

**Questions:** See [THREE_LAYER_ARCHITECTURE.md](/docs/THREE_LAYER_ARCHITECTURE.md)
**Issues:** Create GitHub issue with label `configuration`
**Contact:** contatoalteragro@gmail.com

---

**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
