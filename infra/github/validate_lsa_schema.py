#!/usr/bin/env python3
"""
LSA JSON Schema Validator

Validates LSA artifacts against formal JSON schema.
Ensures structural compliance before other validators run.

Usage:
    python validate_lsa_schema.py <lsa_artifact.json>
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Note: jsonschema package required: pip install jsonschema
try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("❌ jsonschema package not installed")
    print("   Install with: pip install jsonschema")
    sys.exit(1)


# LSA Artifact JSON Schema (Draft 7)
LSA_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "YARA Lógica LSA Artifact",
    "description": "Schema for Logic-Sorting Architecture (LSA) reasoning artifacts",
    "type": "object",
    "required": ["premises", "inferences", "contradictions", "conclusions", "audit"],
    "properties": {
        "premises": {
            "type": "array",
            "description": "Foundational facts from verified sources",
            "items": {
                "type": "object",
                "required": ["id", "statement", "source_sha256", "byte_range"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^premise-[0-9]+$",
                        "description": "Unique premise identifier"
                    },
                    "statement": {
                        "type": "string",
                        "minLength": 10,
                        "description": "The factual statement"
                    },
                    "source_sha256": {
                        "type": "string",
                        "pattern": "^([a-f0-9]{64}|private)$",
                        "description": "SHA-256 hash of source document or 'private'"
                    },
                    "byte_range": {
                        "type": "string",
                        "pattern": "^[0-9]+-[0-9]+$",
                        "description": "Byte range in source (start-end)"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence score (0-1)"
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Type of source (peer-reviewed, government, etc.)"
                    },
                    "contradiction_check": {
                        "type": "object",
                        "properties": {
                            "performed": {"type": "boolean"},
                            "exempt": {"type": "boolean"},
                            "exempt_reason": {"type": "string"}
                        }
                    }
                },
                "additionalProperties": False
            }
        },
        "inferences": {
            "type": "array",
            "description": "Logical derivations from premises",
            "items": {
                "type": "object",
                "required": ["id", "supports", "methodology", "statement"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^inference-[0-9]+$"
                    },
                    "supports": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "IDs of supporting premises/inferences"
                    },
                    "methodology": {
                        "type": "string",
                        "pattern": "^LSA::",
                        "description": "Reasoning methodology (must start with LSA::)"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "statement": {
                        "type": "string",
                        "minLength": 10
                    },
                    "contradiction_check": {
                        "type": "object",
                        "properties": {
                            "performed": {"type": "boolean"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "search_queries": {"type": "array", "items": {"type": "string"}},
                            "sources_searched": {"type": "integer", "minimum": 0},
                            "contradictions_found": {"type": "integer", "minimum": 0},
                            "exempt": {"type": "boolean"},
                            "exempt_reason": {"type": "string"}
                        }
                    }
                },
                "additionalProperties": False
            }
        },
        "contradictions": {
            "type": "array",
            "description": "Contested claims found during validation",
            "items": {
                "type": "object",
                "required": ["id", "targets", "statement", "label"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^contradiction-[0-9]+$"
                    },
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "IDs of claims being contradicted"
                    },
                    "statement": {
                        "type": "string",
                        "minLength": 10
                    },
                    "label": {
                        "type": "string",
                        "enum": ["FACT(CONTESTED)"],
                        "description": "Contradiction marker"
                    },
                    "source_sha256": {
                        "type": "string",
                        "pattern": "^([a-f0-9]{64}|private)$"
                    },
                    "byte_range": {
                        "type": "string",
                        "pattern": "^[0-9]+-[0-9]+$"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    }
                },
                "additionalProperties": False
            }
        },
        "conclusions": {
            "type": "array",
            "description": "Final reasoning conclusions",
            "items": {
                "type": "object",
                "required": ["id", "supports", "contested_by", "statement", "decision_state"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^conclusion-[0-9]+$"
                    },
                    "supports": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    },
                    "contested_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs of contradictions contesting this conclusion"
                    },
                    "statement": {
                        "type": "string",
                        "minLength": 10
                    },
                    "decision_state": {
                        "type": "string",
                        "enum": ["approved", "pending", "rejected"]
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "contradiction_check": {
                        "type": "object",
                        "properties": {
                            "performed": {"type": "boolean"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "search_queries": {"type": "array", "items": {"type": "string"}},
                            "sources_searched": {"type": "integer", "minimum": 0},
                            "contradictions_found": {"type": "integer", "minimum": 0},
                            "methodology": {"type": "string"},
                            "exempt": {"type": "boolean"},
                            "exempt_reason": {"type": "string"}
                        }
                    }
                },
                "additionalProperties": False
            }
        },
        "audit": {
            "type": "object",
            "description": "Audit trail metadata",
            "required": ["author", "timestamp", "hash", "signing_key"],
            "properties": {
                "author": {
                    "type": "string",
                    "format": "email",
                    "description": "Author email"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO 8601 timestamp"
                },
                "hash": {
                    "type": "string",
                    "pattern": "^[a-f0-9]{64}$",
                    "description": "SHA-256 hash of artifact"
                },
                "signing_key": {
                    "type": "string",
                    "description": "GPG key fingerprint or identifier"
                }
            },
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}


def validate_lsa_schema(lsa_artifact: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate LSA artifact against JSON schema

    Args:
        lsa_artifact: Parsed LSA JSON artifact

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    try:
        # Validate against schema
        validator = Draft7Validator(LSA_SCHEMA)
        validation_errors = sorted(validator.iter_errors(lsa_artifact), key=lambda e: e.path)

        for error in validation_errors:
            # Format path
            path = ".".join(str(p) for p in error.path) if error.path else "root"

            # Format error message
            if error.validator == "required":
                errors.append(f"{path}: Missing required field '{error.message.split("'")[1]}'")
            elif error.validator == "pattern":
                errors.append(f"{path}: Value does not match required pattern")
            elif error.validator == "type":
                errors.append(f"{path}: Invalid type (expected {error.validator_value})")
            elif error.validator == "enum":
                errors.append(f"{path}: Value must be one of {error.validator_value}")
            elif error.validator == "minItems":
                errors.append(f"{path}: Array must have at least {error.validator_value} item(s)")
            elif error.validator == "minLength":
                errors.append(f"{path}: String must be at least {error.validator_value} characters")
            else:
                errors.append(f"{path}: {error.message}")

    except Exception as e:
        errors.append(f"Schema validation error: {e}")

    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_lsa_schema.py <lsa_artifact.json>")
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

    print(f"🔍 Validating LSA schema: {filepath}")
    print()

    is_valid, errors = validate_lsa_schema(artifact)

    if errors:
        print(f"❌ Schema Validation Errors ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        sys.exit(1)
    else:
        print("✅ LSA artifact conforms to schema")
        sys.exit(0)


if __name__ == "__main__":
    main()
