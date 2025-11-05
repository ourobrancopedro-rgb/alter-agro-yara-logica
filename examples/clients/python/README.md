# YARA Lógica PICC Notarization - Python Client

Python client for submitting PICC decisions to the YARA Lógica notarization webhook.

## Requirements

- Python 3.8+
- `requests` library

## Installation

```bash
pip install requests
```

Or using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install requests
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
python submit_decision.py
```

Or make it executable:

```bash
chmod +x submit_decision.py
./submit_decision.py
```

### Import as Module

```python
import os
import secrets
import time
from submit_decision import submit_decision, compute_hash, canonical

# Build payload
payload = {
    'schema_version': 'PICC-1.0',
    'ts': int(time.time()),
    'nonce': secrets.token_hex(16),
    'decision': {
        'question': 'Your question here',
        'conclusion': 'Your conclusion',
        'confidence': 'HIGH',
        'premises': [
            {
                'type': 'FACT',
                'text': 'Some fact',
                'evidence': [
                    'https://example.com/1',
                    'https://example.com/2'
                ]
            }
        ],
        'falsifier': 'Condition that would invalidate conclusion'
    },
    'metadata': {
        'actor': 'your-actor-id',
        'context': 'your-context'
    }
}

# Submit
try:
    result = submit_decision(
        endpoint=os.getenv('N8N_WEBHOOK_URL'),
        secret=os.getenv('HMAC_SECRET'),
        payload=payload
    )

    print(f'Decision notarized: {result["issue_url"]}')
except Exception as error:
    print(f'Submission failed: {error}')
```

## API

### `canonical(obj: Any) -> str`

Converts an object to canonical JSON (sorted keys, no whitespace).

**Parameters:**
- `obj` (any) - Object to canonicalize

**Returns:** `str` - Canonical JSON string

---

### `compute_hash(payload: Dict[str, Any]) -> str`

Computes SHA-256 hash of canonical JSON.

**Parameters:**
- `payload` (dict) - Decision payload

**Returns:** `str` - 64-character hex hash

---

### `submit_decision(endpoint: str, secret: str, payload: Dict[str, Any]) -> Dict[str, Any]`

Submits a PICC decision to the notarization webhook.

**Parameters:**
- `endpoint` (str) - n8n webhook URL
- `secret` (str) - HMAC shared secret
- `payload` (dict) - PICC-1.0 decision payload

**Returns:** `dict` - Response from webhook
- `ok` (bool) - Success indicator
- `code` (str) - Status code (`CREATED`, `IDEMPOTENT`)
- `msg` (str) - Human-readable message
- `issue_url` (str) - GitHub issue URL
- `issue_number` (int) - GitHub issue number
- `hash` (str) - SHA-256 hash of decision

**Raises:**
- `ValueError` - If required parameters are missing
- `requests.HTTPError` - If HTTP request fails
- `RuntimeError` - If response indicates failure

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

## Type Hints

This module uses Python type hints for better IDE support and type checking. To validate types:

```bash
pip install mypy
mypy submit_decision.py
```

## Testing

```python
import unittest
from submit_decision import canonical, compute_hash

class TestCanonical(unittest.TestCase):
    def test_sorted_keys(self):
        obj = {'z': 1, 'a': 2}
        result = canonical(obj)
        self.assertEqual(result, '{"a":2,"z":1}')

    def test_nested_objects(self):
        obj = {'outer': {'z': 1, 'a': 2}}
        result = canonical(obj)
        self.assertEqual(result, '{"outer":{"a":2,"z":1}}')

    def test_hash_determinism(self):
        obj1 = {'a': 1, 'b': 2}
        obj2 = {'b': 2, 'a': 1}
        hash1 = compute_hash(obj1)
        hash2 = compute_hash(obj2)
        self.assertEqual(hash1, hash2)

if __name__ == '__main__':
    unittest.main()
```

## References

- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **JSON Schema:** `/spec/schemas/picc-1.0.schema.json`
- **JavaScript Client:** `/examples/clients/javascript/submit_decision.js`
