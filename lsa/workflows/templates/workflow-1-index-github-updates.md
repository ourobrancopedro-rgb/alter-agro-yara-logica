# Workflow 1: Index GitHub Updates

**Purpose:** Automatically ingest new/updated documents from `/knowledge/` into the RAG index.

**Trigger:** GitHub webhook (push events to `/knowledge/**`) or cron job

---

## Workflow Overview

```
GitHub Push Event
    ↓
[1. GitHub Webhook Trigger]
    ↓
[2. Filter: Only knowledge/** files]
    ↓
[3. Loop: For Each Changed File]
    ↓
[4. HTTP: Fetch File from GitHub]
    ↓
[5. HTTP: POST /ingest-file (RAG API)]
    ↓
[6. Code: Aggregate Results]
    ↓
[7. GitHub: Create Log Issue (Optional)]
    ↓
[8. Slack: Notify Team (Optional)]
```

---

## Node Configuration

### Node 1: GitHub Webhook Trigger

**Node Type:** `n8n-nodes-base.webhook`

**Settings:**
- **Path:** `/webhook/github-push`
- **Method:** POST
- **Authentication:** None (use webhook secret verification in next node)

**Expected Payload (GitHub Push Event):**

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "ourobrancopedro-rgb/alter-agro-yara-logica",
    "clone_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica.git"
  },
  "commits": [
    {
      "id": "abc123def456",
      "message": "docs: add VM0047 v1.3",
      "added": ["knowledge/methodologies/VM0047_v1.3.pdf"],
      "modified": [],
      "removed": []
    }
  ]
}
```

---

### Node 2: Filter – Only knowledge/** Files

**Node Type:** `n8n-nodes-base.function`

**Code:**

```javascript
// Extract all changed files (added or modified) in knowledge/
const changedFiles = [];

for (const commit of $input.first().json.commits) {
  // Added files
  for (const file of commit.added || []) {
    if (file.startsWith('knowledge/')) {
      changedFiles.push({
        path: file,
        action: 'added',
        commit_sha: commit.id,
        commit_message: commit.message
      });
    }
  }

  // Modified files
  for (const file of commit.modified || []) {
    if (file.startsWith('knowledge/')) {
      changedFiles.push({
        path: file,
        action: 'modified',
        commit_sha: commit.id,
        commit_message: commit.message
      });
    }
  }
}

// If no knowledge/ files changed, stop workflow
if (changedFiles.length === 0) {
  return [];
}

// Return one item per changed file
return changedFiles.map(file => ({ json: file }));
```

**Output:** Array of items, one per changed file in `knowledge/`

---

### Node 3: Loop – For Each Changed File

**Node Type:** Built-in loop (no explicit node needed in n8n)

n8n automatically loops over array items from Node 2.

---

### Node 4: HTTP Request – Fetch File from GitHub

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** GET
- **URL:** `https://raw.githubusercontent.com/{{$json.repository}}/{{$json.ref}}/{{$json.path}}`
  - Example: `https://raw.githubusercontent.com/ourobrancopedro-rgb/alter-agro-yara-logica/main/knowledge/methodologies/VM0047_v1.3.pdf`
- **Response Format:** File (binary)

**Authentication:** None (public repo) or GitHub token (private repo)

**Output:** Binary file content + metadata

---

### Node 5: HTTP Request – POST /ingest-file (RAG API)

**Node Type:** `n8n-nodes-base.httpRequest`

**Settings:**
- **Method:** POST
- **URL:** `{{$env.RAG_API_URL}}/ingest-file`
  - Environment variable: `RAG_API_URL=https://rag.alter-agro.com`
- **Authentication:** Header Auth
  - Header Name: `X-API-Key`
  - Header Value: `{{$env.RAG_API_KEY}}`
- **Body Content Type:** JSON

**Body:**

```json
{
  "repo": "{{$json.repository}}",
  "path": "{{$json.path}}",
  "sha": "{{$json.commit_sha}}",
  "content_url": "https://raw.githubusercontent.com/{{$json.repository}}/{{$json.ref}}/{{$json.path}}",
  "metadata": {
    "commit_message": "{{$json.commit_message}}",
    "action": "{{$json.action}}"
  }
}
```

**Response Handling:**
- **Success (200):** Extract `chunks_created` from response
- **Error (4xx, 5xx):** Log error, continue to next file

---

### Node 6: Code – Aggregate Results

**Node Type:** `n8n-nodes-base.function`

**Code:**

```javascript
// Aggregate results from all ingestion calls
const results = $input.all();

const summary = {
  total_files: results.length,
  successful: 0,
  failed: 0,
  total_chunks: 0,
  files: []
};

for (const item of results) {
  const data = item.json;

  if (data.status === 'success') {
    summary.successful++;
    summary.total_chunks += data.chunks_created || 0;
    summary.files.push({
      path: data.file,
      sha: data.sha,
      chunks: data.chunks_created,
      status: 'success'
    });
  } else {
    summary.failed++;
    summary.files.push({
      path: data.file || 'unknown',
      error: data.message || 'Unknown error',
      status: 'failed'
    });
  }
}

return [{ json: summary }];
```

**Output:** Single item with aggregated summary

---

### Node 7: GitHub – Create Log Issue (Optional)

**Node Type:** `n8n-nodes-base.github`

**Settings:**
- **Resource:** Issue
- **Operation:** Create
- **Repository Owner:** `ourobrancopedro-rgb`
- **Repository Name:** `alter-agro-yara-logica`
- **Title:** `[RAG Ingestion] {{$now.format('YYYY-MM-DD HH:mm')}} – {{$json.total_files}} files`
- **Body:**

```markdown
# RAG Ingestion Summary

**Timestamp:** {{$now.format('YYYY-MM-DD HH:mm:ss')}}
**Total Files:** {{$json.total_files}}
**Successful:** {{$json.successful}}
**Failed:** {{$json.failed}}
**Total Chunks Created:** {{$json.total_chunks}}

## Files Processed

{{#each $json.files}}
- **{{this.path}}** ({{this.status}})
  {{#if this.chunks}}
  - Chunks: {{this.chunks}}
  - SHA: {{this.sha}}
  {{/if}}
  {{#if this.error}}
  - Error: {{this.error}}
  {{/if}}
{{/each}}
```

- **Labels:** `rag-ingestion`, `automated`

**Condition:** Only create issue if `$json.total_files > 0`

---

### Node 8: Slack – Notify Team (Optional)

**Node Type:** `n8n-nodes-base.slack`

**Settings:**
- **Resource:** Message
- **Operation:** Post
- **Channel:** `#yara-logica-rag`
- **Message:**

```
🔄 RAG Ingestion Complete

Files: {{$json.successful}}/{{$json.total_files}} successful
Chunks: {{$json.total_chunks}} created
Time: {{$now.format('YYYY-MM-DD HH:mm')}}

{{#if $json.failed}}
⚠️ {{$json.failed}} files failed to ingest
{{/if}}
```

**Condition:** Only send if `$json.total_files > 0`

---

## Environment Variables

Set these in n8n settings or environment:

| Variable | Description | Example |
|:---------|:------------|:--------|
| `RAG_API_URL` | RAG service base URL | `https://rag.alter-agro.com` |
| `RAG_API_KEY` | API key for RAG service | `ak_live_abc123...` |
| `GITHUB_TOKEN` | GitHub personal access token (if private repo) | `ghp_abc123...` |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | `https://hooks.slack.com/...` |

---

## GitHub Webhook Setup

1. Go to GitHub repo settings → Webhooks → Add webhook
2. **Payload URL:** `https://n8n.alter-agro.com/webhook/github-push`
3. **Content type:** `application/json`
4. **Secret:** (optional, for signature verification)
5. **Events:** Select "Just the push event"
6. **Active:** ✅ Checked

---

## Testing

### Test with Sample Commit

1. Add a test file to `knowledge/test/sample.md`:

```markdown
# Test Document

This is a test document for RAG ingestion.
```

2. Commit and push:

```bash
git add knowledge/test/sample.md
git commit -m "docs: add test document for RAG ingestion"
git push
```

3. Check n8n execution log:
   - Workflow triggered by webhook
   - File fetched from GitHub
   - RAG API called successfully
   - Chunks created (should be 1-2 for small file)
   - GitHub issue created (optional)
   - Slack notification sent (optional)

### Manual Trigger

For testing without pushing to GitHub:

1. Go to n8n workflow editor
2. Click "Execute Workflow" (manual trigger)
3. Provide sample webhook payload in "Test URL" → "Webhook Data"

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "ourobrancopedro-rgb/alter-agro-yara-logica"
  },
  "commits": [
    {
      "id": "abc123",
      "message": "test",
      "added": ["knowledge/test/sample.md"],
      "modified": [],
      "removed": []
    }
  ]
}
```

---

## Monitoring

### Key Metrics

- **Ingestion success rate:** `successful / total_files`
- **Average chunks per file:** `total_chunks / successful`
- **Ingestion latency:** Time from webhook to completion

### Alerts

**Set up alerts for:**
- Ingestion failure rate >20%
- RAG API errors (5xx responses)
- No ingestions for >7 days (possible webhook failure)

---

## Troubleshooting

### Issue: Webhook not triggering

**Cause:** Webhook not configured or n8n not reachable

**Solution:**
1. Check GitHub webhook delivery logs
2. Verify n8n webhook URL is publicly accessible
3. Test webhook with "Redeliver" in GitHub

### Issue: RAG API returns 409 (already ingested)

**Cause:** File with same SHA already in database (idempotent operation)

**Solution:** This is expected behavior. RAG API returns 409 for duplicate SHAs. Log as "skipped" rather than "failed".

### Issue: File download fails (404)

**Cause:** File path incorrect or branch mismatch

**Solution:**
1. Verify file exists at commit SHA
2. Check branch in webhook payload (`ref` field)
3. Ensure raw GitHub URL is correct

---

**Version:** 1.0
**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
