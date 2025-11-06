/**
 * YARA PICC Notarization - JavaScript Test Suite
 *
 * Usage:
 *   export N8N_WEBHOOK_URL='https://your-n8n.com/webhook/yara/picc/notarize'
 *   export HMAC_SECRET='your-hmac-secret-here'
 *   npm test
 */

const crypto = require('crypto');

// Configuration
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL;
const HMAC_SECRET = process.env.HMAC_SECRET;

// Check configuration before running tests
if (!N8N_WEBHOOK_URL || !HMAC_SECRET) {
  console.error('Error: Required environment variables not set');
  console.error('');
  console.error('Usage:');
  console.error('  export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"');
  console.error('  export HMAC_SECRET="your-hmac-secret-here"');
  console.error('  npm test');
  process.exit(1);
}

/**
 * Compute HMAC-SHA256 signature for payload
 */
function computeHmacSignature(payload, secret) {
  const payloadStr = JSON.stringify(payload);
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payloadStr);
  return 'sha256=' + hmac.digest('hex');
}

/**
 * Send PICC notarization request to n8n webhook
 */
async function sendPiccRequest(payload, hmacSecret = HMAC_SECRET, webhookUrl = N8N_WEBHOOK_URL) {
  const signature = computeHmacSignature(payload, hmacSecret);

  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Signature-256': signature
    },
    body: JSON.stringify(payload)
  });

  const responseData = await response.json();

  return {
    statusCode: response.status,
    data: responseData
  };
}

/**
 * Create a valid PICC payload with current timestamp
 */
function createValidPayload(nonce = null, overrides = {}) {
  const currentTs = Math.floor(Date.now() / 1000);
  nonce = nonce || `jest-${currentTs}`;

  const payload = {
    schema_version: 'PICC-1.0',
    ts: currentTs,
    nonce: nonce,
    decision: {
      question: 'Is this a Jest test decision?',
      conclusion: 'Yes, this is a Jest test',
      confidence: 'HIGH',
      premises: [
        {
          type: 'FACT',
          text: 'This is a test premise for Jest',
          evidence: [
            'https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica',
            'https://example.com/jest-evidence'
          ]
        }
      ],
      falsifier: 'If validation fails, Jest should catch it'
    },
    metadata: {
      actor: 'jest',
      context: 'automated-test'
    }
  };

  // Apply overrides
  return { ...payload, ...overrides };
}

// Test Suites

describe('Valid PICC Payloads', () => {
  test('Minimal valid payload with required fields only', async () => {
    const payload = createValidPayload('jest-minimal-001');
    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.issue_url).toBeDefined();
    expect(data.hash).toBeDefined();
  });

  test('Complete payload with all optional fields', async () => {
    const currentTs = Math.floor(Date.now() / 1000);
    const payload = {
      schema_version: 'PICC-1.0',
      ts: currentTs,
      nonce: `jest-complete-${currentTs}`,
      decision: {
        question: 'Complete payload test with all fields?',
        conclusion: 'Yes, comprehensive test',
        confidence: 'HIGH',
        premises: [
          {
            type: 'FACT',
            text: 'FACT with multiple evidence',
            evidence: [
              'https://example.com/evidence1',
              'https://example.com/evidence2',
              'https://example.com/evidence3'
            ]
          },
          {
            type: 'ASSUMPTION',
            text: 'Assumption without evidence'
          },
          {
            type: 'EXPERT_OPINION',
            text: 'Expert opinion with single evidence',
            evidence: ['https://example.com/expert']
          }
        ],
        inferences: [
          'First inference',
          'Second inference'
        ],
        contradictions: [
          'First contradiction',
          'Second contradiction'
        ],
        falsifier: 'Comprehensive falsifier for complete payload test'
      },
      metadata: {
        actor: 'jest',
        context: 'test-complete'
      }
    };

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.issue_url).toBeDefined();
  });

  test('HIGH confidence decision', async () => {
    const payload = createValidPayload('jest-high-conf');
    payload.decision.confidence = 'HIGH';

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });

  test('MEDIUM confidence decision', async () => {
    const payload = createValidPayload('jest-medium-conf');
    payload.decision.confidence = 'MEDIUM';

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });

  test('LOW confidence decision', async () => {
    const payload = createValidPayload('jest-low-conf');
    payload.decision.confidence = 'LOW';

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });
});

describe('Invalid PICC Payloads', () => {
  test('Bad HMAC signature should be rejected', async () => {
    const payload = createValidPayload('jest-bad-hmac');

    // Use wrong HMAC secret
    const wrongSecret = 'wrong-secret-00000000000000000000000000000000';
    const { statusCode, data } = await sendPiccRequest(payload, wrongSecret);

    expect(statusCode).toBe(401);
    expect(data.ok).toBe(false);
    expect(data.code).toBe('BAD_SIG');
  });

  test('Expired timestamp should be rejected', async () => {
    const oldTimestamp = Math.floor(Date.now() / 1000) - 400; // 6 min 40 sec ago
    const payload = createValidPayload('jest-expired-ts');
    payload.ts = oldTimestamp;

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('TS_WINDOW');
  });

  test('Invalid schema version should be rejected', async () => {
    const payload = createValidPayload('jest-bad-schema');
    payload.schema_version = 'PICC-2.0';

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('SCHEMA_VERSION');
  });

  test('Short nonce (< 8 chars) should be rejected', async () => {
    const payload = createValidPayload('short');

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('NONCE_INVALID');
  });

  test('FACT premise without evidence should be rejected', async () => {
    const payload = createValidPayload('jest-no-evidence');
    payload.decision.premises = [
      {
        type: 'FACT',
        text: 'FACT without evidence',
        evidence: []
      }
    ];

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('FACT_EVIDENCE');
  });

  test('FACT premise with only 1 evidence should be rejected', async () => {
    const payload = createValidPayload('jest-single-evidence');
    payload.decision.premises = [
      {
        type: 'FACT',
        text: 'FACT with only one evidence',
        evidence: ['https://example.com/only-one']
      }
    ];

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('FACT_EVIDENCE');
  });

  test('Non-HTTPS evidence URLs should be rejected', async () => {
    const payload = createValidPayload('jest-http-evidence');
    payload.decision.premises = [
      {
        type: 'FACT',
        text: 'FACT with HTTP evidence',
        evidence: [
          'http://insecure.example.com/evidence1',
          'http://insecure.example.com/evidence2'
        ]
      }
    ];

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(401);
    expect(data.code).toBe('EVIDENCE_HTTPS');
  });
});

describe('Idempotency', () => {
  test('Duplicate submission should return same issue', async () => {
    const currentTs = Math.floor(Date.now() / 1000);
    const nonce = `jest-idempotency-${currentTs}`;
    const payload = createValidPayload(nonce);

    // First submission
    const { statusCode: statusCode1, data: data1 } = await sendPiccRequest(payload);

    expect(statusCode1).toBe(200);
    expect(data1.ok).toBe(true);
    const issueNumber1 = data1.issue_number;
    const issueUrl1 = data1.issue_url;
    const hash1 = data1.hash;

    // Wait briefly
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Second submission (identical payload)
    const { statusCode: statusCode2, data: data2 } = await sendPiccRequest(payload);

    expect(statusCode2).toBe(200);
    expect(data2.ok).toBe(true);
    expect(data2.idempotent).toBe(true);

    // Verify same issue returned
    expect(data2.issue_number).toBe(issueNumber1);
    expect(data2.issue_url).toBe(issueUrl1);
    expect(data2.created).not.toBe(true);
  });
});

describe('Edge Cases', () => {
  test('Maximum nonce length (128 characters)', async () => {
    const longNonce = 'a'.repeat(128);
    const payload = createValidPayload(longNonce);

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });

  test('Minimum nonce length (8 characters)', async () => {
    const minNonce = 'a'.repeat(8);
    const payload = createValidPayload(minNonce);

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });

  test('Multiple FACT premises', async () => {
    const currentTs = Math.floor(Date.now() / 1000);
    const payload = createValidPayload(`jest-multi-facts-${currentTs}`);
    payload.decision.premises = [
      {
        type: 'FACT',
        text: 'First FACT',
        evidence: ['https://example.com/fact1a', 'https://example.com/fact1b']
      },
      {
        type: 'FACT',
        text: 'Second FACT',
        evidence: ['https://example.com/fact2a', 'https://example.com/fact2b']
      },
      {
        type: 'ASSUMPTION',
        text: 'An assumption'
      }
    ];

    const { statusCode, data } = await sendPiccRequest(payload);

    expect(statusCode).toBe(200);
    expect(data.ok).toBe(true);
  });
});
