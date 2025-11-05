# YARA Lógica PICC Notarization - JavaScript Client

Node.js client for submitting PICC decisions to the YARA Lógica notarization webhook.

## Requirements

- Node.js 18+ (for native `fetch` and ES modules)
- `node-fetch` package

## Installation

```bash
npm install node-fetch
```

## Configuration

Set environment variables:

```bash
export N8N_WEBHOOK_URL="https://your-n8n-instance.com/webhook/yara/picc/notarize"
export HMAC_SECRET="your-shared-secret-key"
```

**Security Note:** Never commit secrets to version control. Use environment variables or a secrets manager.

## Usage

### Run the Example

```bash
node submit_decision.js
```

### Import as Module

```javascript
import { submitDecision, computeHash, canonical } from './submit_decision.js';

const payload = {
  schema_version: 'PICC-1.0',
  ts: Math.floor(Date.now() / 1000),
  nonce: crypto.randomBytes(16).toString('hex'),
  decision: {
    question: 'Your question here',
    conclusion: 'Your conclusion',
    confidence: 'HIGH',
    premises: [
      {
        type: 'FACT',
        text: 'Some fact',
        evidence: ['https://example.com/1', 'https://example.com/2']
      }
    ],
    falsifier: 'Condition that would invalidate conclusion'
  },
  metadata: {
    actor: 'your-actor-id',
    context: 'your-context'
  }
};

try {
  const result = await submitDecision({
    endpoint: process.env.N8N_WEBHOOK_URL,
    secret: process.env.HMAC_SECRET,
    payload
  });

  console.log('Decision notarized:', result.issue_url);
} catch (error) {
  console.error('Submission failed:', error.message);
}
```

## API

### `canonical(obj)`

Converts an object to canonical JSON (sorted keys, no whitespace).

**Parameters:**
- `obj` (any) - Object to canonicalize

**Returns:** `string` - Canonical JSON string

---

### `computeHash(payload)`

Computes SHA-256 hash of canonical JSON.

**Parameters:**
- `payload` (object) - Decision payload

**Returns:** `string` - 64-character hex hash

---

### `submitDecision({ endpoint, secret, payload })`

Submits a PICC decision to the notarization webhook.

**Parameters:**
- `endpoint` (string) - n8n webhook URL
- `secret` (string) - HMAC shared secret
- `payload` (object) - PICC-1.0 decision payload

**Returns:** `Promise<object>` - Response from webhook
- `ok` (boolean) - Success indicator
- `code` (string) - Status code (`CREATED`, `IDEMPOTENT`)
- `msg` (string) - Human-readable message
- `issue_url` (string) - GitHub issue URL
- `issue_number` (number) - GitHub issue number
- `hash` (string) - SHA-256 hash of decision

**Throws:** `Error` - If submission fails (HTTP error or validation failure)

## Error Handling

| Error Code | Meaning | Resolution |
|:-----------|:--------|:-----------|
| `BAD_SIG` | HMAC signature mismatch | Verify `HMAC_SECRET` matches server |
| `TS_WINDOW` | Timestamp outside 5-min window | Sync system clock with NTP |
| `NONCE_INVALID` | Nonce too short/long | Use 8-128 character nonces |
| `NONCE_REUSE` | Nonce already used | Generate fresh nonce for each request |
| `FACT_EVIDENCE` | FACT premise needs ≥2 evidence URLs | Add more evidence or change type |
| `EVIDENCE_HTTPS` | Evidence URLs must be HTTPS | Update URLs to use `https://` |
| `RATE_LIMIT` | Too many requests | Wait and retry (check `Retry-After` header) |

## Example Output

```
Submitting decision to n8n...
Endpoint: https://n8n.example.com/webhook/yara/picc/notarize
Nonce: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Hash: e7f4a2b9c8d1...
Hash Label: hash:e7f4a2b9c8d1f2e3

✅ Success!
Code: CREATED
Message: Decision notarized
Issue URL: https://github.com/org/repo/issues/42
Issue Number: 42
Hash: e7f4a2b9c8d1...
```

## References

- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **JSON Schema:** `/spec/schemas/picc-1.0.schema.json`
- **Python Client:** `/examples/clients/python/submit_decision.py`
