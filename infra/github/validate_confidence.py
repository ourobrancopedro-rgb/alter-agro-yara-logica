#!/usr/bin/env python3
"""
Confidence Propagation Validator

Validates that confidence scores follow propagation rules defined in
lsa/spec/CONFIDENCE_PROPAGATION.md

Usage:
    python validate_confidence.py <lsa_artifact.json>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_confidence_propagation(lsa_artifact: Dict) -> Tuple[bool, List[str]]:
    """
    Validate confidence propagation in LSA artifact.

    Checks:
    1. All premises have confidence (from source quality)
    2. All inferences have confidence ≤ min(supports) × 1.1
    3. Contradictions reduce confidence
    4. Conclusions reflect contestation

    Args:
        lsa_artifact: Parsed LSA JSON artifact

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Build confidence map
    confidences = {}

    # 1. Check premises
    for premise in lsa_artifact.get("premises", []):
        if "confidence" not in premise:
            errors.append(f"Premise {premise['id']} missing confidence score")
        else:
            conf = premise["confidence"]
            if not (0 <= conf <= 1):
                errors.append(f"Premise {premise['id']} has invalid confidence {conf} (must be 0-1)")
            confidences[premise["id"]] = conf

    # 2. Check inferences
    for inference in lsa_artifact.get("inferences", []):
        if "confidence" not in inference:
            errors.append(f"Inference {inference['id']} missing confidence score")
            continue

        inf_conf = inference["confidence"]
        if not (0 <= inf_conf <= 1):
            errors.append(f"Inference {inference['id']} has invalid confidence {inf_conf} (must be 0-1)")
            continue

        # Validate against supports
        support_ids = inference.get("supports", [])
        if not support_ids:
            errors.append(f"Inference {inference['id']} has no supports")
            continue

        support_confs = []
        for support_id in support_ids:
            if support_id in confidences:
                support_confs.append(confidences[support_id])
            else:
                errors.append(f"Inference {inference['id']} references unknown support: {support_id}")

        if support_confs:
            min_support = min(support_confs)
            # Allow up to 10% methodology bonus (1.1x multiplier)
            max_allowed = min_support * 1.1

            if inf_conf > max_allowed:
                errors.append(
                    f"Inference {inference['id']} confidence {inf_conf:.3f} "
                    f"exceeds maximum allowed {max_allowed:.3f} "
                    f"(min support: {min_support:.3f})"
                )

        confidences[inference["id"]] = inf_conf

    # 3. Check conclusions
    for conclusion in lsa_artifact.get("conclusions", []):
        if "confidence" not in conclusion:
            errors.append(f"Conclusion {conclusion['id']} missing confidence score")
            continue

        conc_conf = conclusion["confidence"]
        if not (0 <= conc_conf <= 1):
            errors.append(f"Conclusion {conclusion['id']} has invalid confidence {conc_conf} (must be 0-1)")
            continue

        # Contested conclusions should have reduced confidence
        contested_by = conclusion.get("contested_by", [])
        if contested_by and conc_conf > 0.8:
            errors.append(
                f"Conclusion {conclusion['id']} is contested by {len(contested_by)} contradiction(s) "
                f"but has high confidence {conc_conf:.3f} (should be ≤ 0.8)"
            )

        confidences[conclusion["id"]] = conc_conf

    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_confidence.py <lsa_artifact.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    try:
        with open(filepath, encoding="utf-8") as f:
            artifact = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    print(f"🔍 Validating confidence propagation in: {filepath}")
    print()

    is_valid, errors = validate_confidence_propagation(artifact)

    if errors:
        print("❌ Confidence Validation Errors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        sys.exit(1)
    else:
        print("✅ All confidence scores are valid and properly propagated")
        sys.exit(0)


if __name__ == "__main__":
    main()
