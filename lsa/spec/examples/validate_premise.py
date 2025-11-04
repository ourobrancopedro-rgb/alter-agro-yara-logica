"""
LSA/PICC Premise Validator

Validates premises according to the LSA_PICC specification.
A valid premise must include cryptographic source binding and byte-range citation.

Reference: lsa/spec/LSA_PICC.md
"""

import re
from typing import Dict, Tuple


def validate_premise(premise: Dict) -> Tuple[bool, str]:
    """
    Validate premise according to LSA_PICC spec.

    A valid premise requires:
    - id: Unique identifier (e.g., "premise-001")
    - statement: Atomic, self-contained claim
    - source_sha256: SHA-256 hash of source document (64 hex chars)
    - byte_range: Byte offset range in format "start-end"

    Args:
        premise: Dictionary with id, statement, source_sha256, byte_range

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid

    Example:
        >>> premise = {
        ...     "id": "premise-001",
        ...     "statement": "Soil organic carbon increased by 2.1%.",
        ...     "source_sha256": "a" * 64,
        ...     "byte_range": "123-231"
        ... }
        >>> validate_premise(premise)
        (True, '')
    """
    # Check required fields
    required_fields = ["id", "statement", "source_sha256", "byte_range"]
    missing_fields = [field for field in required_fields if field not in premise]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Validate id format (non-empty string)
    if not isinstance(premise["id"], str) or not premise["id"].strip():
        return False, "Field 'id' must be a non-empty string"

    # Validate statement (non-empty string)
    if not isinstance(premise["statement"], str) or not premise["statement"].strip():
        return False, "Field 'statement' must be a non-empty string"

    # Validate source_sha256 (must be 64 hex characters)
    sha256 = premise["source_sha256"]
    if sha256 == "private":
        # Special case: private source allowed per spec
        pass
    elif not isinstance(sha256, str) or not re.match(r'^[a-fA-F0-9]{64}$', sha256):
        return False, "Field 'source_sha256' must be a 64-character hexadecimal SHA-256 hash or 'private'"

    # Validate byte_range format (must be "start-end" with integers)
    byte_range = premise["byte_range"]
    if not isinstance(byte_range, str):
        return False, "Field 'byte_range' must be a string in format 'start-end'"

    range_match = re.match(r'^(\d+)-(\d+)$', byte_range)
    if not range_match:
        return False, "Field 'byte_range' must be in format 'start-end' (e.g., '123-231')"

    start, end = int(range_match.group(1)), int(range_match.group(2))
    if start > end:
        return False, f"Invalid byte_range: start ({start}) must be <= end ({end})"

    return True, ""


def validate_premise_batch(premises: list) -> Dict:
    """
    Validate a batch of premises.

    Args:
        premises: List of premise dictionaries

    Returns:
        Dictionary with validation results:
        {
            "valid": int,
            "invalid": int,
            "errors": [{"index": int, "id": str, "error": str}]
        }

    Example:
        >>> premises = [
        ...     {"id": "p-001", "statement": "Test", "source_sha256": "a"*64, "byte_range": "0-10"},
        ...     {"id": "p-002", "statement": "Bad"}  # Missing fields
        ... ]
        >>> result = validate_premise_batch(premises)
        >>> result["valid"]
        1
        >>> result["invalid"]
        1
    """
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": []
    }

    for idx, premise in enumerate(premises):
        is_valid, error = validate_premise(premise)
        if is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1
            results["errors"].append({
                "index": idx,
                "id": premise.get("id", f"<unknown-{idx}>"),
                "error": error
            })

    return results


if __name__ == "__main__":
    # Example usage
    examples = [
        # Valid premise
        {
            "id": "premise-001",
            "statement": "Soil organic carbon increased by 2.1%.",
            "source_sha256": "abcd1234" * 8,  # 64 hex chars
            "byte_range": "123-231"
        },
        # Valid premise with private source
        {
            "id": "premise-002",
            "statement": "Independent audit recorded 1.2% gain.",
            "source_sha256": "private",
            "byte_range": "88-141"
        },
        # Invalid premise (missing fields)
        {
            "id": "premise-003",
            "statement": "Missing source reference"
        },
        # Invalid premise (bad byte range)
        {
            "id": "premise-004",
            "statement": "Bad range",
            "source_sha256": "f" * 64,
            "byte_range": "500-100"  # start > end
        }
    ]

    print("LSA/PICC Premise Validator Demo")
    print("=" * 50)

    for i, premise in enumerate(examples):
        is_valid, error = validate_premise(premise)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nExample {i+1}: {status}")
        print(f"  ID: {premise.get('id', 'N/A')}")
        if not is_valid:
            print(f"  Error: {error}")

    print("\n" + "=" * 50)
    print("\nBatch Validation:")
    batch_result = validate_premise_batch(examples)
    print(f"  Valid: {batch_result['valid']}")
    print(f"  Invalid: {batch_result['invalid']}")
    print(f"  Errors: {len(batch_result['errors'])}")
