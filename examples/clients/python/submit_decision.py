#!/usr/bin/env python3
"""
YARA Lógica PICC Notarization - Python Client

Usage:
    pip install requests
    python submit_decision.py

Environment Variables:
    N8N_WEBHOOK_URL - n8n webhook endpoint (required)
    HMAC_SECRET     - Shared secret for HMAC authentication (required)

Example:
    export N8N_WEBHOOK_URL="https://n8n.example.com/webhook/yara/picc/notarize"
    export HMAC_SECRET="your-secret-key-here"
    python submit_decision.py
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict

import requests


def canonical(obj: Any) -> str:
    """
    Canonical JSON serialization (sorted keys, no whitespace).
    Used for deterministic hashing and idempotency.

    Args:
        obj: Object to canonicalize

    Returns:
        Canonical JSON string
    """
    if isinstance(obj, list):
        return '[' + ','.join(canonical(item) for item in obj) + ']'
    elif isinstance(obj, dict):
        keys = sorted(obj.keys())
        pairs = [json.dumps(k) + ':' + canonical(obj[k]) for k in keys]
        return '{' + ','.join(pairs) + '}'
    else:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def compute_hash(payload: Dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of canonical JSON.

    Args:
        payload: Decision payload

    Returns:
        64-character hex hash
    """
    canonical_str = canonical(payload)
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()


def submit_decision(endpoint: str, secret: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit PICC decision to n8n notarization webhook.

    Args:
        endpoint: n8n webhook URL
        secret: HMAC secret
        payload: PICC decision payload

    Returns:
        Response from webhook

    Raises:
        ValueError: If required parameters are missing
        requests.HTTPError: If HTTP request fails
        RuntimeError: If response indicates failure
    """
    # Validate required parameters
    if not endpoint:
        raise ValueError('endpoint is required')
    if not secret:
        raise ValueError('secret is required')
    if not payload:
        raise ValueError('payload is required')

    # Serialize payload (NOT canonical, use standard json.dumps)
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

    # Compute HMAC-SHA256 signature
    signature = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Send POST request
    headers = {
        'Content-Type': 'application/json',
        'X-Signature-256': signature,
    }

    response = requests.post(endpoint, headers=headers, data=body)

    # Parse response
    try:
        json_response = response.json()
    except json.JSONDecodeError:
        response.raise_for_status()
        raise RuntimeError(f'Invalid JSON response: {response.text}')

    # Check for errors
    if not response.ok or not json_response.get('ok'):
        error_code = json_response.get('code', response.status_code)
        error_msg = json_response.get('msg', 'Unknown error')
        raise RuntimeError(f'{error_code}: {error_msg}')

    return json_response


def main():
    """Example usage (demo)."""
    # Configuration (from environment or hardcoded for demo)
    endpoint = os.getenv('N8N_WEBHOOK_URL', '<SET_N8N_WEBHOOK_URL>')
    secret = os.getenv('HMAC_SECRET', '<SET_HMAC_SECRET>')

    # Generate unique nonce (32 hex chars = 16 bytes)
    nonce = secrets.token_hex(16)

    # Build PICC-1.0 decision payload
    payload = {
        'schema_version': 'PICC-1.0',
        'ts': int(time.time()),  # Current Unix timestamp
        'nonce': nonce,
        'decision': {
            'question': 'Should we adopt regenerative agriculture practices?',
            'conclusion': 'Yes, based on carbon sequestration evidence',
            'confidence': 'HIGH',
            'premises': [
                {
                    'type': 'FACT',
                    'text': 'Regenerative agriculture increases soil carbon by 0.5-1.5 tC/ha/yr',
                    'evidence': [
                        'https://doi.org/10.1038/s41558-020-0738-9',
                        'https://www.sciencedirect.com/science/article/pii/S0167880920301584',
                    ],
                },
                {
                    'type': 'ASSUMPTION',
                    'text': 'Farmers will adopt practices if economically viable',
                },
            ],
            'inferences': [
                'Carbon markets can provide economic incentive',
                'Policy support accelerates adoption',
            ],
            'contradictions': [
                'Initial costs may deter small farmers',
            ],
            'falsifier': 'If peer-reviewed studies show no carbon benefit, conclusion is invalid',
        },
        'metadata': {
            'actor': 'python-client-demo',
            'context': 'spec-example',
        },
    }

    try:
        print('Submitting decision to n8n...')
        print(f'Endpoint: {endpoint}')
        print(f'Nonce: {nonce}')

        # Compute and display hash (for reference)
        decision_hash = compute_hash(payload)
        print(f'Hash: {decision_hash}')
        print(f'Hash Label: hash:{decision_hash[:16]}')

        # Submit decision
        result = submit_decision(endpoint, secret, payload)

        print('\n✅ Success!')
        print(f'Code: {result["code"]}')
        print(f'Message: {result["msg"]}')
        print(f'Issue URL: {result["issue_url"]}')
        print(f'Issue Number: {result["issue_number"]}')
        print(f'Hash: {result["hash"]}')

    except Exception as error:
        print(f'\n❌ Error: {error}')
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()
