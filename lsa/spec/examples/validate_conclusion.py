"""
LSA/PICC Conclusion Validator

Validates conclusions according to the LSA_PICC specification.
A valid conclusion must enumerate both supporting and contesting references,
demonstrating transparent reasoning under uncertainty.

Reference: lsa/spec/LSA_PICC.md
"""

from typing import Dict, List, Tuple, Set


def validate_conclusion(
    conclusion: Dict,
    valid_ids: Set[str] = None,
    contradiction_ids: Set[str] = None
) -> Tuple[bool, str]:
    """
    Validate conclusion according to LSA_PICC spec.

    A valid conclusion requires:
    - id: Unique identifier (e.g., "conclusion-001")
    - supports: List of supporting premise/inference IDs (may be empty)
    - contested_by: List of contradiction IDs that challenge this conclusion (may be empty)
    - statement: Final position incorporating both support and contestation
    - decision_state: Current state ("approved", "pending", or "rejected")

    Args:
        conclusion: Dictionary with id, supports, contested_by, statement, decision_state
        valid_ids: Optional set of valid premise/inference IDs for reference checking
        contradiction_ids: Optional set of valid contradiction IDs

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid

    Example:
        >>> conclusion = {
        ...     "id": "conclusion-001",
        ...     "supports": ["inference-001"],
        ...     "contested_by": ["contradiction-001"],
        ...     "statement": "Claim remains under review pending reconciliation.",
        ...     "decision_state": "pending"
        ... }
        >>> validate_conclusion(conclusion)
        (True, '')
    """
    # Check required fields
    required_fields = ["id", "supports", "contested_by", "statement", "decision_state"]
    missing_fields = [field for field in required_fields if field not in conclusion]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Validate id format (non-empty string)
    if not isinstance(conclusion["id"], str) or not conclusion["id"].strip():
        return False, "Field 'id' must be a non-empty string"

    # Validate supports (must be a list, may be empty)
    supports = conclusion["supports"]
    if not isinstance(supports, list):
        return False, "Field 'supports' must be a list"

    for idx, ref_id in enumerate(supports):
        if not isinstance(ref_id, str) or not ref_id.strip():
            return False, f"Field 'supports[{idx}]' must be a non-empty string"

    # Validate supports references against known IDs (if provided)
    if valid_ids is not None and len(supports) > 0:
        invalid_refs = [ref_id for ref_id in supports if ref_id not in valid_ids]
        if invalid_refs:
            return False, f"Field 'supports' references unknown IDs: {', '.join(invalid_refs)}"

    # Validate contested_by (must be a list, may be empty)
    contested_by = conclusion["contested_by"]
    if not isinstance(contested_by, list):
        return False, "Field 'contested_by' must be a list"

    for idx, ref_id in enumerate(contested_by):
        if not isinstance(ref_id, str) or not ref_id.strip():
            return False, f"Field 'contested_by[{idx}]' must be a non-empty string"

    # Validate contested_by references against known contradiction IDs (if provided)
    if contradiction_ids is not None and len(contested_by) > 0:
        invalid_refs = [ref_id for ref_id in contested_by if ref_id not in contradiction_ids]
        if invalid_refs:
            return False, f"Field 'contested_by' references unknown contradiction IDs: {', '.join(invalid_refs)}"

    # Validate statement (non-empty string)
    if not isinstance(conclusion["statement"], str) or not conclusion["statement"].strip():
        return False, "Field 'statement' must be a non-empty string"

    # Validate decision_state (must be one of the allowed states)
    allowed_states = ["approved", "pending", "rejected"]
    decision_state = conclusion["decision_state"]

    if not isinstance(decision_state, str):
        return False, "Field 'decision_state' must be a string"

    if decision_state not in allowed_states:
        return False, f"Field 'decision_state' must be one of {allowed_states} (got '{decision_state}')"

    # Warn if conclusion is approved but has unresolved contradictions
    # (This is a warning, not an error, as per spec guidelines)
    if decision_state == "approved" and len(contested_by) > 0:
        # This could be flagged as a warning in a more sophisticated validator
        pass

    return True, ""


def validate_conclusion_batch(
    conclusions: List[Dict],
    valid_ids: Set[str] = None,
    contradiction_ids: Set[str] = None
) -> Dict:
    """
    Validate a batch of conclusions.

    Args:
        conclusions: List of conclusion dictionaries
        valid_ids: Optional set of valid premise/inference IDs
        contradiction_ids: Optional set of valid contradiction IDs

    Returns:
        Dictionary with validation results:
        {
            "valid": int,
            "invalid": int,
            "errors": [{"index": int, "id": str, "error": str}],
            "state_counts": {"approved": int, "pending": int, "rejected": int},
            "contested_conclusions": int
        }

    Example:
        >>> conclusions = [
        ...     {"id": "c-001", "supports": ["i-001"], "contested_by": [],
        ...      "statement": "Approved claim", "decision_state": "approved"},
        ...     {"id": "c-002", "supports": [], "contested_by": ["ct-001"],
        ...      "statement": "Rejected claim", "decision_state": "rejected"}
        ... ]
        >>> result = validate_conclusion_batch(conclusions)
        >>> result["valid"]
        2
    """
    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "state_counts": {"approved": 0, "pending": 0, "rejected": 0},
        "contested_conclusions": 0
    }

    for idx, conclusion in enumerate(conclusions):
        is_valid, error = validate_conclusion(conclusion, valid_ids, contradiction_ids)
        if is_valid:
            results["valid"] += 1

            # Track decision state counts
            state = conclusion["decision_state"]
            if state in results["state_counts"]:
                results["state_counts"][state] += 1

            # Track contested conclusions
            if len(conclusion["contested_by"]) > 0:
                results["contested_conclusions"] += 1
        else:
            results["invalid"] += 1
            results["errors"].append({
                "index": idx,
                "id": conclusion.get("id", f"<unknown-{idx}>"),
                "error": error
            })

    return results


def check_conclusion_integrity(
    premises: List[Dict],
    inferences: List[Dict],
    contradictions: List[Dict],
    conclusions: List[Dict]
) -> Tuple[bool, List[str]]:
    """
    Check that all conclusion references are valid and complete.

    Validates that:
    - All 'supports' references point to existing premises or inferences
    - All 'contested_by' references point to existing contradictions
    - Contradictions are properly acknowledged in conclusions
    - Decision states align with contestation status

    Args:
        premises: List of premise dictionaries
        inferences: List of inference dictionaries
        contradictions: List of contradiction dictionaries
        conclusions: List of conclusion dictionaries

    Returns:
        Tuple of (is_valid, errors)
        - (True, []) if valid
        - (False, [error_messages]) if invalid

    Example:
        >>> premises = [{"id": "p-001"}]
        >>> inferences = [{"id": "i-001"}]
        >>> contradictions = [{"id": "ct-001"}]
        >>> conclusions = [{
        ...     "id": "c-001",
        ...     "supports": ["i-001"],
        ...     "contested_by": ["ct-001"],
        ...     "statement": "Under review",
        ...     "decision_state": "pending"
        ... }]
        >>> is_valid, errors = check_conclusion_integrity(premises, inferences, contradictions, conclusions)
        >>> is_valid
        True
    """
    errors = []
    warnings = []

    # Build sets of valid IDs
    valid_ids = {p["id"] for p in premises if "id" in p}
    valid_ids.update(i["id"] for i in inferences if "id" in i)
    contradiction_ids = {c["id"] for c in contradictions if "id" in c}

    # Track which contradictions are referenced
    referenced_contradictions = set()

    # Validate each conclusion
    for idx, conclusion in enumerate(conclusions):
        if "id" not in conclusion:
            errors.append(f"Conclusion at index {idx} missing 'id' field")
            continue

        conc_id = conclusion["id"]

        # Validate the conclusion
        is_valid, error = validate_conclusion(conclusion, valid_ids, contradiction_ids)
        if not is_valid:
            errors.append(f"Conclusion '{conc_id}': {error}")
            continue

        # Track referenced contradictions
        if "contested_by" in conclusion:
            referenced_contradictions.update(conclusion["contested_by"])

        # Check for potential issues with decision state
        if conclusion.get("decision_state") == "approved" and len(conclusion.get("contested_by", [])) > 0:
            warnings.append(
                f"Warning: Conclusion '{conc_id}' is approved but has unresolved contradictions: "
                f"{', '.join(conclusion['contested_by'])}"
            )

        # Check for conclusions with no support
        if len(conclusion.get("supports", [])) == 0 and conclusion.get("decision_state") == "approved":
            warnings.append(
                f"Warning: Conclusion '{conc_id}' is approved but has no supporting evidence"
            )

    # Check for unreferenced contradictions
    unreferenced = contradiction_ids - referenced_contradictions
    if unreferenced:
        warnings.append(
            f"Warning: {len(unreferenced)} contradictions are not referenced in any conclusion: "
            f"{', '.join(sorted(unreferenced))}"
        )

    # Add warnings to errors list (as informational)
    if warnings:
        errors.extend(warnings)

    # Only fail on actual errors, not warnings
    has_errors = any(not msg.startswith("Warning:") for msg in errors)
    return not has_errors, errors


if __name__ == "__main__":
    # Example usage
    premises = [{"id": "premise-001"}, {"id": "premise-002"}]
    inferences = [{"id": "inference-001"}]
    contradictions = [{"id": "contradiction-001"}, {"id": "contradiction-002"}]

    examples = [
        # Valid conclusion (pending with contestation)
        {
            "id": "conclusion-001",
            "supports": ["inference-001"],
            "contested_by": ["contradiction-001"],
            "statement": "Claim remains under review pending reconciliation.",
            "decision_state": "pending"
        },
        # Valid conclusion (approved without contestation)
        {
            "id": "conclusion-002",
            "supports": ["premise-001", "premise-002"],
            "contested_by": [],
            "statement": "Claim approved based on convergent evidence.",
            "decision_state": "approved"
        },
        # Valid conclusion (rejected due to contradictions)
        {
            "id": "conclusion-003",
            "supports": ["inference-001"],
            "contested_by": ["contradiction-001", "contradiction-002"],
            "statement": "Claim rejected due to multiple contradictions.",
            "decision_state": "rejected"
        },
        # Invalid: bad decision state
        {
            "id": "conclusion-004",
            "supports": [],
            "contested_by": [],
            "statement": "Invalid state",
            "decision_state": "maybe"
        },
        # Invalid: references unknown support ID
        {
            "id": "conclusion-005",
            "supports": ["unknown-inference"],
            "contested_by": [],
            "statement": "References non-existent inference",
            "decision_state": "pending"
        }
    ]

    print("LSA/PICC Conclusion Validator Demo")
    print("=" * 50)

    # Build valid ID sets
    valid_ids = {p["id"] for p in premises}
    valid_ids.update(i["id"] for i in inferences)
    contradiction_ids = {c["id"] for c in contradictions}

    for i, conclusion in enumerate(examples):
        is_valid, error = validate_conclusion(conclusion, valid_ids, contradiction_ids)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nExample {i+1}: {status}")
        print(f"  ID: {conclusion.get('id', 'N/A')}")
        print(f"  State: {conclusion.get('decision_state', 'N/A')}")
        print(f"  Contested: {len(conclusion.get('contested_by', []))} contradictions")
        if not is_valid:
            print(f"  Error: {error}")

    print("\n" + "=" * 50)
    print("\nBatch Validation:")
    batch_result = validate_conclusion_batch(examples, valid_ids, contradiction_ids)
    print(f"  Valid: {batch_result['valid']}")
    print(f"  Invalid: {batch_result['invalid']}")
    print(f"  Decision states: {batch_result['state_counts']}")
    print(f"  Contested conclusions: {batch_result['contested_conclusions']}")

    print("\n" + "=" * 50)
    print("\nIntegrity Check:")
    is_valid, messages = check_conclusion_integrity(premises, inferences, contradictions, examples)
    if is_valid:
        print("  ✓ Conclusion integrity is valid")
    if messages:
        print(f"  Found {len(messages)} messages:")
        for msg in messages:
            print(f"    - {msg}")
