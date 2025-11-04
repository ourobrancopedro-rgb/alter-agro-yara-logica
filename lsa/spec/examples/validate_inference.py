"""
LSA/PICC Inference Validator

Validates inferences according to the LSA_PICC specification.
A valid inference must reference one or more premises/prior inferences and include
methodology tags and confidence bounds.

Reference: lsa/spec/LSA_PICC.md
"""

from typing import Dict, List, Tuple, Set


def validate_inference(inference: Dict, valid_ids: Set[str] = None) -> Tuple[bool, str]:
    """
    Validate inference according to LSA_PICC spec.

    A valid inference requires:
    - id: Unique identifier (e.g., "inference-001")
    - supports: List of one or more premise/inference IDs
    - methodology: String describing reasoning method (e.g., "LSA::delta-carbon")
    - confidence: Numeric value between 0.0 and 1.0
    - statement: Derived claim from supporting evidence

    Args:
        inference: Dictionary with id, supports, methodology, confidence, statement
        valid_ids: Optional set of valid premise/inference IDs to check references against

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid

    Example:
        >>> inference = {
        ...     "id": "inference-001",
        ...     "supports": ["premise-001"],
        ...     "methodology": "LSA::delta-carbon",
        ...     "confidence": 0.82,
        ...     "statement": "Regenerative practice achieved targeted carbon gain."
        ... }
        >>> validate_inference(inference)
        (True, '')
    """
    # Check required fields
    required_fields = ["id", "supports", "methodology", "confidence", "statement"]
    missing_fields = [field for field in required_fields if field not in inference]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Validate id format (non-empty string)
    if not isinstance(inference["id"], str) or not inference["id"].strip():
        return False, "Field 'id' must be a non-empty string"

    # Validate supports (must be a non-empty list of strings)
    supports = inference["supports"]
    if not isinstance(supports, list):
        return False, "Field 'supports' must be a list"

    if len(supports) == 0:
        return False, "Field 'supports' must contain at least one reference"

    for idx, ref_id in enumerate(supports):
        if not isinstance(ref_id, str) or not ref_id.strip():
            return False, f"Field 'supports[{idx}]' must be a non-empty string"

    # Validate supports references against known IDs (if provided)
    if valid_ids is not None:
        invalid_refs = [ref_id for ref_id in supports if ref_id not in valid_ids]
        if invalid_refs:
            return False, f"Field 'supports' references unknown IDs: {', '.join(invalid_refs)}"

    # Validate methodology (non-empty string, preferably with namespace)
    methodology = inference["methodology"]
    if not isinstance(methodology, str) or not methodology.strip():
        return False, "Field 'methodology' must be a non-empty string"

    # Validate confidence (must be numeric between 0.0 and 1.0)
    confidence = inference["confidence"]
    if not isinstance(confidence, (int, float)):
        return False, "Field 'confidence' must be a number"

    if not 0.0 <= confidence <= 1.0:
        return False, f"Field 'confidence' must be between 0.0 and 1.0 (got {confidence})"

    # Validate statement (non-empty string)
    if not isinstance(inference["statement"], str) or not inference["statement"].strip():
        return False, "Field 'statement' must be a non-empty string"

    return True, ""


def validate_inference_batch(inferences: List[Dict], valid_ids: Set[str] = None) -> Dict:
    """
    Validate a batch of inferences.

    Args:
        inferences: List of inference dictionaries
        valid_ids: Optional set of valid premise/inference IDs for reference checking

    Returns:
        Dictionary with validation results:
        {
            "valid": int,
            "invalid": int,
            "errors": [{"index": int, "id": str, "error": str}],
            "avg_confidence": float
        }

    Example:
        >>> inferences = [
        ...     {"id": "i-001", "supports": ["p-001"], "methodology": "LSA::test",
        ...      "confidence": 0.9, "statement": "Test inference"},
        ...     {"id": "i-002", "supports": [], "methodology": "LSA::test",
        ...      "confidence": 1.5, "statement": "Bad confidence"}  # Invalid
        ... ]
        >>> result = validate_inference_batch(inferences)
        >>> result["valid"]
        1
        >>> result["invalid"]
        1
    """
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "avg_confidence": 0.0
    }

    total_confidence = 0.0
    valid_count = 0

    for idx, inference in enumerate(inferences):
        is_valid, error = validate_inference(inference, valid_ids)
        if is_valid:
            results["valid"] += 1
            total_confidence += inference["confidence"]
            valid_count += 1
        else:
            results["invalid"] += 1
            results["errors"].append({
                "index": idx,
                "id": inference.get("id", f"<unknown-{idx}>"),
                "error": error
            })

    if valid_count > 0:
        results["avg_confidence"] = total_confidence / valid_count

    return results


def check_inference_chain_integrity(
    premises: List[Dict],
    inferences: List[Dict]
) -> Tuple[bool, List[str]]:
    """
    Check that all inference references form a valid chain.

    Validates that:
    - All 'supports' references point to existing premises or prior inferences
    - No circular dependencies exist
    - Inference chain is well-ordered

    Args:
        premises: List of premise dictionaries
        inferences: List of inference dictionaries

    Returns:
        Tuple of (is_valid, errors)
        - (True, []) if valid
        - (False, [error_messages]) if invalid

    Example:
        >>> premises = [{"id": "p-001", "statement": "Base fact"}]
        >>> inferences = [
        ...     {"id": "i-001", "supports": ["p-001"], "methodology": "LSA::test",
        ...      "confidence": 0.8, "statement": "First inference"},
        ...     {"id": "i-002", "supports": ["i-001"], "methodology": "LSA::test",
        ...      "confidence": 0.7, "statement": "Second inference"}
        ... ]
        >>> is_valid, errors = check_inference_chain_integrity(premises, inferences)
        >>> is_valid
        True
    """
    errors = []

    # Build set of all valid IDs
    valid_ids = {p["id"] for p in premises if "id" in p}

    # Process inferences in order, adding valid ones to the ID set
    for idx, inference in enumerate(inferences):
        if "id" not in inference:
            errors.append(f"Inference at index {idx} missing 'id' field")
            continue

        inf_id = inference["id"]

        # Check for duplicate IDs
        if inf_id in valid_ids:
            errors.append(f"Duplicate ID '{inf_id}' (already exists in premises or prior inferences)")
            continue

        # Validate the inference
        is_valid, error = validate_inference(inference, valid_ids)
        if not is_valid:
            errors.append(f"Inference '{inf_id}': {error}")
            continue

        # Add to valid IDs for subsequent inferences
        valid_ids.add(inf_id)

    return len(errors) == 0, errors


if __name__ == "__main__":
    # Example usage
    premises = [
        {"id": "premise-001"},
        {"id": "premise-002"}
    ]

    examples = [
        # Valid inference
        {
            "id": "inference-001",
            "supports": ["premise-001"],
            "methodology": "LSA::delta-carbon",
            "confidence": 0.82,
            "statement": "Regenerative practice achieved the targeted carbon gain."
        },
        # Valid inference referencing another inference
        {
            "id": "inference-002",
            "supports": ["inference-001", "premise-002"],
            "methodology": "LSA::convergent-evidence",
            "confidence": 0.91,
            "statement": "Multiple sources confirm carbon gain trend."
        },
        # Invalid: confidence out of range
        {
            "id": "inference-003",
            "supports": ["premise-001"],
            "methodology": "LSA::test",
            "confidence": 1.5,
            "statement": "Bad confidence value"
        },
        # Invalid: empty supports
        {
            "id": "inference-004",
            "supports": [],
            "methodology": "LSA::test",
            "confidence": 0.5,
            "statement": "No supporting evidence"
        },
        # Invalid: references unknown ID
        {
            "id": "inference-005",
            "supports": ["unknown-premise"],
            "methodology": "LSA::test",
            "confidence": 0.7,
            "statement": "References non-existent premise"
        }
    ]

    print("LSA/PICC Inference Validator Demo")
    print("=" * 50)

    # Build valid ID set
    valid_ids = {p["id"] for p in premises}

    for i, inference in enumerate(examples):
        is_valid, error = validate_inference(inference, valid_ids)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nExample {i+1}: {status}")
        print(f"  ID: {inference.get('id', 'N/A')}")
        print(f"  Confidence: {inference.get('confidence', 'N/A')}")
        if not is_valid:
            print(f"  Error: {error}")
        else:
            # Add valid inferences to ID set for subsequent checks
            valid_ids.add(inference["id"])

    print("\n" + "=" * 50)
    print("\nChain Integrity Check:")
    is_valid, errors = check_inference_chain_integrity(premises, examples)
    if is_valid:
        print("  ✓ Inference chain is valid")
    else:
        print(f"  ✗ Found {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")
