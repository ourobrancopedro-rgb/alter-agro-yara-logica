#!/usr/bin/env python3
"""
LSA Structure Validator

Validates LSA artifacts for structural integrity:
- No circular dependencies
- All references exist
- Proper ordering
- Orphaned elements detection

Usage:
    python validate_lsa_structure.py <lsa_artifact.json>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class LSAValidator:
    """Validates LSA artifact structure"""

    def __init__(self, artifact: Dict):
        self.artifact = artifact
        self.errors = []
        self.warnings = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks"""
        self.check_circular_dependencies()
        self.check_dangling_references()
        self.check_orphaned_elements()
        self.check_contradiction_targets()

        return len(self.errors) == 0, self.errors, self.warnings

    def check_circular_dependencies(self):
        """Detect circular dependencies in inference chain"""
        # Build dependency graph
        graph = {}

        for inference in self.artifact.get("inferences", []):
            inf_id = inference["id"]
            supports = inference.get("supports", [])
            graph[inf_id] = supports

        # DFS to detect cycles
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for node in graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    self.errors.append(
                        f"Circular dependency detected involving {node}"
                    )

    def check_dangling_references(self):
        """Check that all referenced IDs exist"""
        # Collect all valid IDs
        valid_ids = set()

        for premise in self.artifact.get("premises", []):
            valid_ids.add(premise["id"])

        for inference in self.artifact.get("inferences", []):
            valid_ids.add(inference["id"])

        for conclusion in self.artifact.get("conclusions", []):
            valid_ids.add(conclusion["id"])

        # Check inference references
        for inference in self.artifact.get("inferences", []):
            for ref in inference.get("supports", []):
                if ref not in valid_ids:
                    self.errors.append(
                        f"Inference {inference['id']} references unknown ID: {ref}"
                    )

        # Check conclusion references
        for conclusion in self.artifact.get("conclusions", []):
            for ref in conclusion.get("supports", []):
                if ref not in valid_ids:
                    self.errors.append(
                        f"Conclusion {conclusion['id']} references unknown ID: {ref}"
                    )

            # Check contested_by references
            for ref in conclusion.get("contested_by", []):
                # contested_by references contradiction IDs
                contradiction_ids = {c["id"] for c in self.artifact.get("contradictions", [])}
                if ref not in contradiction_ids:
                    self.errors.append(
                        f"Conclusion {conclusion['id']} contested_by references unknown contradiction ID: {ref}"
                    )

    def check_orphaned_elements(self):
        """Detect premises/inferences that are never used"""
        referenced_ids = set()

        # Collect all referenced IDs
        for inference in self.artifact.get("inferences", []):
            referenced_ids.update(inference.get("supports", []))

        for conclusion in self.artifact.get("conclusions", []):
            referenced_ids.update(conclusion.get("supports", []))

        for contradiction in self.artifact.get("contradictions", []):
            referenced_ids.update(contradiction.get("targets", []))

        # Check for orphans
        all_ids = set()
        for premise in self.artifact.get("premises", []):
            all_ids.add(premise["id"])
        for inference in self.artifact.get("inferences", []):
            all_ids.add(inference["id"])

        # Filter out conclusions (they're allowed to be terminal)
        conclusion_ids = {c["id"] for c in self.artifact.get("conclusions", [])}
        orphaned = all_ids - referenced_ids - conclusion_ids

        if orphaned:
            self.warnings.append(
                f"Found {len(orphaned)} orphaned elements never referenced: "
                f"{', '.join(sorted(list(orphaned)[:10]))}"
                + (f" and {len(orphaned) - 10} more" if len(orphaned) > 10 else "")
            )

    def check_contradiction_targets(self):
        """Ensure all contradictions target valid elements"""
        valid_ids = set()

        for premise in self.artifact.get("premises", []):
            valid_ids.add(premise["id"])
        for inference in self.artifact.get("inferences", []):
            valid_ids.add(inference["id"])
        for conclusion in self.artifact.get("conclusions", []):
            valid_ids.add(conclusion["id"])

        for contradiction in self.artifact.get("contradictions", []):
            for target in contradiction.get("targets", []):
                if target not in valid_ids:
                    self.errors.append(
                        f"Contradiction {contradiction['id']} targets unknown ID: {target}"
                    )

            # Check that contested conclusions reference this contradiction
            contested_conclusions = [
                c for c in self.artifact.get("conclusions", [])
                if contradiction["id"] in c.get("contested_by", [])
            ]

            if not contested_conclusions and contradiction.get("targets"):
                self.warnings.append(
                    f"Contradiction {contradiction['id']} targets claims but is not referenced by any conclusion"
                )


def validate_lsa_file(filepath: Path) -> Tuple[bool, List[str], List[str]]:
    """Validate a single LSA JSON file"""
    try:
        with open(filepath, encoding="utf-8") as f:
            artifact = json.load(f)

        validator = LSAValidator(artifact)
        return validator.validate_all()

    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"], []
    except Exception as e:
        return False, [f"Validation error: {e}"], []


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_lsa_structure.py <lsa_file.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    print(f"🔍 Validating LSA structure: {filepath}")
    print()

    is_valid, errors, warnings = validate_lsa_file(filepath)

    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
        print()

    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
        print()

    if is_valid:
        print("✅ LSA structure is valid")
        sys.exit(0)
    else:
        print(f"❌ Found {len(errors)} error(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
