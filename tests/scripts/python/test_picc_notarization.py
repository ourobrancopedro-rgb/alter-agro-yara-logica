#!/usr/bin/env python3
"""
YARA PICC Notarization - Python Test Suite

Usage:
    export N8N_WEBHOOK_URL='https://your-n8n.com/webhook/yara/picc/notarize'
    export HMAC_SECRET='your-hmac-secret-here'
    pytest test_picc_notarization.py -v
"""

import os
import json
import time
import hmac
import hashlib
from typing import Dict, Any, Tuple
import requests
import pytest


# Configuration
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
HMAC_SECRET = os.environ.get('HMAC_SECRET', '')


def compute_hmac_signature(payload: Dict[str, Any], secret: str) -> str:
    """
    Compute HMAC-SHA256 signature for payload.

    Args:
        payload: Request payload dictionary
        secret: HMAC secret key

    Returns:
        HMAC signature in format 'sha256=<hex>'
    """
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f'sha256={signature}'


def send_picc_request(
    payload: Dict[str, Any],
    hmac_secret: str = HMAC_SECRET,
    webhook_url: str = N8N_WEBHOOK_URL
) -> Tuple[int, Dict[str, Any]]:
    """
    Send PICC notarization request to n8n webhook.

    Args:
        payload: PICC decision payload
        hmac_secret: HMAC secret for authentication
        webhook_url: n8n webhook URL

    Returns:
        Tuple of (status_code, response_json)
    """
    signature = compute_hmac_signature(payload, hmac_secret)

    headers = {
        'Content-Type': 'application/json',
        'X-Signature-256': signature
    }

    response = requests.post(webhook_url, json=payload, headers=headers)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        response_json = {'error': 'Invalid JSON response', 'text': response.text}

    return response.status_code, response_json


def create_valid_payload(nonce: str = None, **overrides) -> Dict[str, Any]:
    """
    Create a valid PICC payload with current timestamp.

    Args:
        nonce: Optional nonce (generates unique if not provided)
        **overrides: Override specific fields

    Returns:
        Valid PICC payload dictionary
    """
    current_ts = int(time.time())
    nonce = nonce or f'pytest-{current_ts}'

    payload = {
        'schema_version': 'PICC-1.0',
        'ts': current_ts,
        'nonce': nonce,
        'decision': {
            'question': 'Is this a pytest test decision?',
            'conclusion': 'Yes, this is a pytest test',
            'confidence': 'HIGH',
            'premises': [
                {
                    'type': 'FACT',
                    'text': 'This is a test premise for pytest',
                    'evidence': [
                        'https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica',
                        'https://example.com/pytest-evidence'
                    ]
                }
            ],
            'falsifier': 'If validation fails, pytest should catch it'
        },
        'metadata': {
            'actor': 'pytest',
            'context': 'automated-test'
        }
    }

    # Apply overrides
    for key, value in overrides.items():
        if '.' in key:
            # Handle nested keys like 'decision.confidence'
            parts = key.split('.')
            current = payload
            for part in parts[:-1]:
                current = current[part]
            current[parts[-1]] = value
        else:
            payload[key] = value

    return payload


# Fixtures
@pytest.fixture(scope='session')
def webhook_url():
    """Ensure webhook URL is configured."""
    if not N8N_WEBHOOK_URL:
        pytest.skip('N8N_WEBHOOK_URL environment variable not set')
    return N8N_WEBHOOK_URL


@pytest.fixture(scope='session')
def hmac_secret():
    """Ensure HMAC secret is configured."""
    if not HMAC_SECRET:
        pytest.skip('HMAC_SECRET environment variable not set')
    return HMAC_SECRET


# Test Classes
class TestValidPayloads:
    """Test cases for valid PICC payloads."""

    def test_minimal_valid_payload(self, webhook_url, hmac_secret):
        """Test minimal valid payload with required fields only."""
        payload = create_valid_payload(nonce='pytest-minimal-001')
        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200, f'Expected 200, got {status_code}'
        assert response.get('ok') is True, 'Expected ok=true'
        assert 'issue_url' in response, 'Expected issue_url in response'
        assert 'hash' in response, 'Expected hash in response'

    def test_complete_payload_with_all_fields(self, webhook_url, hmac_secret):
        """Test complete payload with all optional fields."""
        current_ts = int(time.time())
        payload = {
            'schema_version': 'PICC-1.0',
            'ts': current_ts,
            'nonce': f'pytest-complete-{current_ts}',
            'decision': {
                'question': 'Complete payload test with all fields?',
                'conclusion': 'Yes, comprehensive test',
                'confidence': 'HIGH',
                'premises': [
                    {
                        'type': 'FACT',
                        'text': 'FACT with multiple evidence',
                        'evidence': [
                            'https://example.com/evidence1',
                            'https://example.com/evidence2',
                            'https://example.com/evidence3'
                        ]
                    },
                    {
                        'type': 'ASSUMPTION',
                        'text': 'Assumption without evidence'
                    },
                    {
                        'type': 'EXPERT_OPINION',
                        'text': 'Expert opinion with single evidence',
                        'evidence': ['https://example.com/expert']
                    }
                ],
                'inferences': [
                    'First inference',
                    'Second inference'
                ],
                'contradictions': [
                    'First contradiction',
                    'Second contradiction'
                ],
                'falsifier': 'Comprehensive falsifier for complete payload test'
            },
            'metadata': {
                'actor': 'pytest',
                'context': 'test-complete'
            }
        }

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True
        assert 'issue_url' in response

    def test_high_confidence_decision(self, webhook_url, hmac_secret):
        """Test HIGH confidence decision."""
        payload = create_valid_payload(
            nonce='pytest-high-confidence',
            **{'decision.confidence': 'HIGH'}
        )
        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True

    def test_medium_confidence_decision(self, webhook_url, hmac_secret):
        """Test MEDIUM confidence decision."""
        payload = create_valid_payload(nonce='pytest-medium-conf')
        payload['decision']['confidence'] = 'MEDIUM'

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True

    def test_low_confidence_decision(self, webhook_url, hmac_secret):
        """Test LOW confidence decision."""
        payload = create_valid_payload(nonce='pytest-low-conf')
        payload['decision']['confidence'] = 'LOW'

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True


class TestInvalidPayloads:
    """Test cases for invalid PICC payloads (should be rejected)."""

    def test_bad_hmac_signature(self, webhook_url, hmac_secret):
        """Test that bad HMAC signature is rejected."""
        payload = create_valid_payload(nonce='pytest-bad-hmac')

        # Use wrong HMAC secret
        status_code, response = send_picc_request(
            payload,
            hmac_secret='wrong-secret-00000000000000000000000000000000',
            webhook_url=webhook_url
        )

        assert status_code == 401, 'Expected 401 Unauthorized'
        assert response.get('ok') is False
        assert response.get('code') == 'BAD_SIG'

    def test_expired_timestamp(self, webhook_url, hmac_secret):
        """Test that expired timestamp is rejected (outside 5-min window)."""
        old_timestamp = int(time.time()) - 400  # 6 minutes 40 seconds ago
        payload = create_valid_payload(nonce='pytest-expired-ts')
        payload['ts'] = old_timestamp

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'TS_WINDOW'

    def test_bad_schema_version(self, webhook_url, hmac_secret):
        """Test that invalid schema version is rejected."""
        payload = create_valid_payload(nonce='pytest-bad-schema')
        payload['schema_version'] = 'PICC-2.0'

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'SCHEMA_VERSION'

    def test_short_nonce(self, webhook_url, hmac_secret):
        """Test that nonce shorter than 8 characters is rejected."""
        payload = create_valid_payload(nonce='short')

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'NONCE_INVALID'

    def test_missing_evidence_for_fact(self, webhook_url, hmac_secret):
        """Test that FACT premise without evidence is rejected."""
        payload = create_valid_payload(nonce='pytest-no-evidence')
        payload['decision']['premises'] = [
            {
                'type': 'FACT',
                'text': 'FACT without evidence',
                'evidence': []
            }
        ]

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'FACT_EVIDENCE'

    def test_single_evidence_for_fact(self, webhook_url, hmac_secret):
        """Test that FACT premise with only 1 evidence is rejected (needs ≥2)."""
        payload = create_valid_payload(nonce='pytest-single-evidence')
        payload['decision']['premises'] = [
            {
                'type': 'FACT',
                'text': 'FACT with only one evidence',
                'evidence': ['https://example.com/only-one']
            }
        ]

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'FACT_EVIDENCE'

    def test_non_https_evidence(self, webhook_url, hmac_secret):
        """Test that HTTP (non-HTTPS) evidence URLs are rejected."""
        payload = create_valid_payload(nonce='pytest-http-evidence')
        payload['decision']['premises'] = [
            {
                'type': 'FACT',
                'text': 'FACT with HTTP evidence',
                'evidence': [
                    'http://insecure.example.com/evidence1',
                    'http://insecure.example.com/evidence2'
                ]
            }
        ]

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 401
        assert response.get('code') == 'EVIDENCE_HTTPS'


class TestIdempotency:
    """Test idempotency guarantees (duplicate submissions)."""

    def test_duplicate_submission_returns_same_issue(self, webhook_url, hmac_secret):
        """Test that submitting identical payload twice returns same issue."""
        current_ts = int(time.time())
        nonce = f'pytest-idempotency-{current_ts}'
        payload = create_valid_payload(nonce=nonce)

        # First submission
        status_code_1, response_1 = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code_1 == 200
        assert response_1.get('ok') is True
        issue_number_1 = response_1.get('issue_number')
        issue_url_1 = response_1.get('issue_url')
        hash_1 = response_1.get('hash')

        # Wait briefly
        time.sleep(2)

        # Second submission (identical payload)
        status_code_2, response_2 = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code_2 == 200
        assert response_2.get('ok') is True
        assert response_2.get('idempotent') is True, 'Second submission should be marked idempotent'

        issue_number_2 = response_2.get('issue_number')
        issue_url_2 = response_2.get('issue_url')

        # Verify same issue returned
        assert issue_number_1 == issue_number_2, 'Should return same issue number'
        assert issue_url_1 == issue_url_2, 'Should return same issue URL'
        assert response_2.get('created') is not True, 'Second submission should not create new issue'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_nonce_length(self, webhook_url, hmac_secret):
        """Test nonce with maximum allowed length (128 characters)."""
        long_nonce = 'a' * 128
        payload = create_valid_payload(nonce=long_nonce)

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True

    def test_minimum_nonce_length(self, webhook_url, hmac_secret):
        """Test nonce with minimum allowed length (8 characters)."""
        min_nonce = 'a' * 8
        payload = create_valid_payload(nonce=min_nonce)

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True

    def test_multiple_fact_premises(self, webhook_url, hmac_secret):
        """Test decision with multiple FACT premises."""
        current_ts = int(time.time())
        payload = create_valid_payload(nonce=f'pytest-multi-facts-{current_ts}')
        payload['decision']['premises'] = [
            {
                'type': 'FACT',
                'text': 'First FACT',
                'evidence': ['https://example.com/fact1a', 'https://example.com/fact1b']
            },
            {
                'type': 'FACT',
                'text': 'Second FACT',
                'evidence': ['https://example.com/fact2a', 'https://example.com/fact2b']
            },
            {
                'type': 'ASSUMPTION',
                'text': 'An assumption'
            }
        ]

        status_code, response = send_picc_request(payload, hmac_secret, webhook_url)

        assert status_code == 200
        assert response.get('ok') is True


if __name__ == '__main__':
    import sys

    # Check configuration
    if not N8N_WEBHOOK_URL or not HMAC_SECRET:
        print('Error: Required environment variables not set')
        print()
        print('Usage:')
        print('  export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"')
        print('  export HMAC_SECRET="your-hmac-secret-here"')
        print('  pytest test_picc_notarization.py -v')
        sys.exit(1)

    # Run pytest
    pytest.main([__file__, '-v', '--tb=short'])
