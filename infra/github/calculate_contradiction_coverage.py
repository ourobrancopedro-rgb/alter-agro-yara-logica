#!/usr/bin/env python3
"""
Contradiction Coverage Calculator

Calculates and validates contradiction coverage for LSA artifacts.
See rag/spec/CONTRADICTION_COVERAGE.md for specification.

Usage:
    python calculate_contradiction_coverage.py <lsa_artifact.json>
    python calculate_contradiction_coverage.py lsa/artifacts/*.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def calculate_contradiction_coverage(lsa_artifact: Dict) -> Tuple[float, Dict]:
    """
    Calculate contradiction coverage with detailed breakdown

    Args:
        lsa_artifact: Parsed LSA JSON artifact

    Returns:
        (coverage_ratio, details_dict)
    """
    inferences = lsa_artifact.get("inferences", [])
    conclusions = lsa_artifact.get("conclusions", [])

    # Count checkable claims (excluding exemptions)
    checkable = []
    exempt = []

    for inf in inferences:
        if inf.get("contradiction_check", {}).get("exempt", False):
            exempt.append({
                "id": inf["id"],
                "reason": inf.get("contradiction_check", {}).get("exempt_reason", "unspecified")
            })
        else:
            checkable.append(inf["id"])

    for conc in conclusions:
        if conc.get("contradiction_check", {}).get("exempt", False):
            exempt.append({
                "id": conc["id"],
                "reason": conc.get("contradiction_check", {}).get("exempt_reason", "unspecified")
            })
        else:
            checkable.append(conc["id"])

    total_checkable = len(checkable)

    if total_checkable == 0:
        return 1.0, {
            "total_claims": len(inferences) + len(conclusions),
            "exempt_claims": len(exempt),
            "checkable_claims": 0,
            "checked_claims": 0,
            "unchecked_claims": 0,
            "coverage": 1.0,
            "unchecked_ids": [],
            "exemptions": exempt
        }

    # Count checked claims
    checked = set()

    # Claims with contradictions targeting them
    for contradiction in lsa_artifact.get("contradictions", []):
        checked.update(contradiction.get("targets", []))

    # Claims explicitly marked as checked
    for inf in inferences:
        if inf.get("contradiction_check", {}).get("performed"):
            checked.add(inf["id"])

    for conc in conclusions:
        if conc.get("contradiction_check", {}).get("performed"):
            checked.add(conc["id"])

    # Only count checked claims that are checkable
    checked_checkable = checked.intersection(set(checkable))

    coverage = len(checked_checkable) / total_checkable if total_checkable > 0 else 1.0

    details = {
        "total_claims": len(inferences) + len(conclusions),
        "exempt_claims": len(exempt),
        "checkable_claims": total_checkable,
        "checked_claims": len(checked_checkable),
        "unchecked_claims": total_checkable - len(checked_checkable),
        "coverage": coverage,
        "unchecked_ids": sorted(list(set(checkable) - checked)),
        "exemptions": exempt
    }

    return coverage, details


def validate_threshold(coverage: float, threshold: float = 0.90) -> bool:
    """Check if coverage meets threshold"""
    return coverage >= threshold


def print_report(filepath: Path, coverage: float, details: Dict, threshold: float = 0.90):
    """Print human-readable coverage report"""
    print(f"\n{'='*60}")
    print(f"Contradiction Coverage Report")
    print(f"{'='*60}")
    print(f"File: {filepath}")
    print(f"Total claims: {details['total_claims']}")
    print(f"Exempt claims: {details['exempt_claims']}")
    print(f"Checkable claims: {details['checkable_claims']}")
    print(f"Checked claims: {details['checked_claims']}")
    print(f"Unchecked claims: {details['unchecked_claims']}")
    print(f"Coverage: {coverage:.1%}")
    print(f"Threshold: {threshold:.1%}")
    print(f"{'='*60}")

    if validate_threshold(coverage, threshold):
        print(f"✅ PASS - Meets coverage threshold")
    else:
        print(f"❌ FAIL - Below coverage threshold")

    if details['exemptions']:
        print(f"\n📋 Exemptions ({len(details['exemptions'])}):")
        for exemption in details['exemptions'][:5]:
            print(f"  • {exemption['id']}: {exemption['reason']}")
        if len(details['exemptions']) > 5:
            print(f"  ... and {len(details['exemptions']) - 5} more")

    if details['unchecked_ids']:
        print(f"\n⚠️  Unchecked Claims ({len(details['unchecked_ids'])}):")
        for claim_id in details['unchecked_ids'][:10]:
            print(f"  • {claim_id}")
        if len(details['unchecked_ids']) > 10:
            print(f"  ... and {len(details['unchecked_ids']) - 10} more")

    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate_contradiction_coverage.py <lsa_file.json> [threshold]")
        print("Example: python calculate_contradiction_coverage.py lsa/artifacts/analysis.json 0.90")
        sys.exit(1)

    threshold = 0.90
    if len(sys.argv) > 2:
        try:
            threshold = float(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid threshold: {sys.argv[2]}")
            sys.exit(1)

    # Process all input files
    filepaths = []
    for arg in sys.argv[1:]:
        if arg.replace('.', '', 1).isdigit():  # Skip threshold argument
            continue
        path = Path(arg)
        if path.exists() and path.suffix == '.json':
            filepaths.append(path)
        elif '*' in arg:
            # Handle glob patterns
            parent = Path(arg).parent if Path(arg).parent.exists() else Path('.')
            pattern = Path(arg).name
            filepaths.extend(parent.glob(pattern))

    if not filepaths:
        print("❌ No valid JSON files found")
        sys.exit(1)

    all_passed = True

    for filepath in filepaths:
        try:
            with open(filepath, encoding="utf-8") as f:
                artifact = json.load(f)

            coverage, details = calculate_contradiction_coverage(artifact)
            passed = validate_threshold(coverage, threshold)

            print_report(filepath, coverage, details, threshold)

            if not passed:
                all_passed = False

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {filepath}: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            all_passed = False

    if all_passed:
        print("✅ All files pass contradiction coverage requirements")
        sys.exit(0)
    else:
        print("❌ Some files failed contradiction coverage requirements")
        sys.exit(1)


if __name__ == "__main__":
    main()
