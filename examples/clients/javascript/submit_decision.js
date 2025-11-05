/**
 * YARA Lógica PICC Notarization - JavaScript Client
 *
 * Usage:
 *   npm install node-fetch
 *   node submit_decision.js
 *
 * Environment Variables:
 *   N8N_WEBHOOK_URL - n8n webhook endpoint (required)
 *   HMAC_SECRET     - Shared secret for HMAC authentication (required)
 *
 * Example:
 *   export N8N_WEBHOOK_URL="https://n8n.example.com/webhook/yara/picc/notarize"
 *   export HMAC_SECRET="your-secret-key-here"
 *   node submit_decision.js
 */

import crypto from 'node:crypto';
import fetch from 'node-fetch';

/**
 * Canonical JSON serialization (sorted keys, no whitespace)
 * Used for deterministic hashing and idempotency.
 *
 * @param {*} obj - Object to canonicalize
 * @returns {string} Canonical JSON string
 */
export function canonical(obj) {
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonical).join(',') + ']';
  }
  if (obj && typeof obj === 'object' && obj !== null) {
    const keys = Object.keys(obj).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + canonical(obj[k])).join(',') + '}';
  }
  return JSON.stringify(obj);
}

/**
 * Compute SHA-256 hash of canonical JSON
 *
 * @param {object} payload - Decision payload
 * @returns {string} 64-character hex hash
 */
export function computeHash(payload) {
  const canonicalStr = canonical(payload);
  return crypto.createHash('sha256').update(canonicalStr).digest('hex');
}

/**
 * Submit PICC decision to n8n notarization webhook
 *
 * @param {object} options
 * @param {string} options.endpoint - n8n webhook URL
 * @param {string} options.secret - HMAC secret
 * @param {object} options.payload - PICC decision payload
 * @returns {Promise<object>} Response from webhook
 */
export async function submitDecision({ endpoint, secret, payload }) {
  // Validate required parameters
  if (!endpoint) throw new Error('endpoint is required');
  if (!secret) throw new Error('secret is required');
  if (!payload) throw new Error('payload is required');

  // Serialize payload (NOT canonical, use standard JSON.stringify)
  const body = JSON.stringify(payload);

  // Compute HMAC-SHA256 signature
  const signature = 'sha256=' + crypto.createHmac('sha256', secret).update(body).digest('hex');

  // Send POST request
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Signature-256': signature,
    },
    body,
  });

  // Parse response
  const json = await response.json();

  // Check for errors
  if (!response.ok || !json.ok) {
    const error = new Error(`${json.code || response.status}: ${json.msg || 'Unknown error'}`);
    error.code = json.code;
    error.response = json;
    throw error;
  }

  return json;
}

/**
 * Example usage (demo)
 */
async function main() {
  // Configuration (from environment or hardcoded for demo)
  const endpoint = process.env.N8N_WEBHOOK_URL || '<SET_N8N_WEBHOOK_URL>';
  const secret = process.env.HMAC_SECRET || '<SET_HMAC_SECRET>';

  // Generate unique nonce
  const nonce = crypto.randomBytes(16).toString('hex');

  // Build PICC-1.0 decision payload
  const payload = {
    schema_version: 'PICC-1.0',
    ts: Math.floor(Date.now() / 1000), // Current Unix timestamp
    nonce: nonce,
    decision: {
      question: 'Should we adopt regenerative agriculture practices?',
      conclusion: 'Yes, based on carbon sequestration evidence',
      confidence: 'HIGH',
      premises: [
        {
          type: 'FACT',
          text: 'Regenerative agriculture increases soil carbon by 0.5-1.5 tC/ha/yr',
          evidence: [
            'https://doi.org/10.1038/s41558-020-0738-9',
            'https://www.sciencedirect.com/science/article/pii/S0167880920301584',
          ],
        },
        {
          type: 'ASSUMPTION',
          text: 'Farmers will adopt practices if economically viable',
        },
      ],
      inferences: [
        'Carbon markets can provide economic incentive',
        'Policy support accelerates adoption',
      ],
      contradictions: [
        'Initial costs may deter small farmers',
      ],
      falsifier: 'If peer-reviewed studies show no carbon benefit, conclusion is invalid',
    },
    metadata: {
      actor: 'javascript-client-demo',
      context: 'spec-example',
    },
  };

  try {
    console.log('Submitting decision to n8n...');
    console.log(`Endpoint: ${endpoint}`);
    console.log(`Nonce: ${nonce}`);

    // Compute and display hash (for reference)
    const hash = computeHash(payload);
    console.log(`Hash: ${hash}`);
    console.log(`Hash Label: hash:${hash.substring(0, 16)}`);

    // Submit decision
    const result = await submitDecision({ endpoint, secret, payload });

    console.log('\n✅ Success!');
    console.log(`Code: ${result.code}`);
    console.log(`Message: ${result.msg}`);
    console.log(`Issue URL: ${result.issue_url}`);
    console.log(`Issue Number: ${result.issue_number}`);
    console.log(`Hash: ${result.hash}`);
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response:', JSON.stringify(error.response, null, 2));
    }
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
