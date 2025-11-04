#!/usr/bin/env python3
"""
Data Loss Prevention (DLP) Scanner for YARA Lógica
===================================================

Custom pattern detection for Alter Agro trade secrets and sensitive information.

This scanner detects:
- Customer names and companies (configurable)
- Pricing information patterns
- Internal domain references
- Prompt engineering patterns
- Model references
- Infrastructure details
- API endpoints and secrets

Usage:
    python scan_secrets.py                    # Scan all files
    python scan_secrets.py --strict           # Exit with error on violations
    python scan_secrets.py --staged           # Scan only staged files
    python scan_secrets.py --output report.json  # Save JSON report
    python scan_secrets.py --interactive      # Interactive mode with prompts

Author: Alter Agro Ltda.
License: BUSL-1.1
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Set, Optional


class Severity(Enum):
    """Severity levels for violations"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Violation:
    """Represents a security violation"""
    file_path: str
    line_number: int
    severity: str
    category: str
    pattern: str
    matched_text: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


class DLPScanner:
    """Data Loss Prevention Scanner"""

    def __init__(self, strict: bool = False, verbose: bool = True):
        self.strict = strict
        self.verbose = verbose
        self.violations: List[Violation] = []

        # Pattern categories and their definitions
        self.patterns = self._init_patterns()

    def _init_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize detection patterns"""
        return {
            "secrets": [
                {
                    "name": "api_key",
                    "pattern": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w\-]{16,}",
                    "severity": Severity.CRITICAL,
                    "description": "API key detected"
                },
                {
                    "name": "secret_key",
                    "pattern": r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?[\w\-]{16,}",
                    "severity": Severity.CRITICAL,
                    "description": "Secret key detected"
                },
                {
                    "name": "password",
                    "pattern": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][\w\-@#$%^&*()]{6,}",
                    "severity": Severity.CRITICAL,
                    "description": "Password detected"
                },
                {
                    "name": "bearer_token",
                    "pattern": r"(?i)bearer\s+[\w\-\.=]+",
                    "severity": Severity.CRITICAL,
                    "description": "Bearer token detected"
                },
                {
                    "name": "aws_key",
                    "pattern": r"AKIA[0-9A-Z]{16}",
                    "severity": Severity.CRITICAL,
                    "description": "AWS access key detected"
                },
                {
                    "name": "private_key",
                    "pattern": r"-----BEGIN.*PRIVATE KEY-----",
                    "severity": Severity.CRITICAL,
                    "description": "Private key detected"
                },
            ],
            "customer_data": [
                {
                    "name": "customer_placeholder",
                    "pattern": r"(?i)(customer[_-]?name|client[_-]?name)\s*[:=]\s*['\"](?!placeholder|example|test|demo)[\w\s]+['\"]",
                    "severity": Severity.ERROR,
                    "description": "Potential customer name detected"
                },
                {
                    "name": "company_placeholder",
                    "pattern": r"(?i)(company|empresa)\s*[:=]\s*['\"](?!Alter Agro|Example|Test|Demo)[\w\s]+['\"]",
                    "severity": Severity.ERROR,
                    "description": "Potential company name detected"
                },
                {
                    "name": "external_email",
                    "pattern": r"[a-zA-Z0-9._%+-]+@(?!alteragro\.com\.br|example\.com|test\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    "severity": Severity.WARNING,
                    "description": "External email address detected"
                },
                {
                    "name": "phone_number",
                    "pattern": r"(\+55[0-9]{10,11}|\\([0-9]{2}\\)\s*[0-9]{4,5}-[0-9]{4})",
                    "severity": Severity.ERROR,
                    "description": "Phone number detected"
                },
                {
                    "name": "cpf",
                    "pattern": r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}",
                    "severity": Severity.ERROR,
                    "description": "CPF (Brazilian tax ID) detected"
                },
                {
                    "name": "cnpj",
                    "pattern": r"[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}",
                    "severity": Severity.ERROR,
                    "description": "CNPJ (Brazilian company ID) detected"
                },
            ],
            "pricing": [
                {
                    "name": "currency_amounts",
                    "pattern": r"(?i)(price|pricing|cost|valor|preço)\s*[:=]?\s*[R$USD€£]\s*[0-9,]+(\.[0-9]{2})?",
                    "severity": Severity.WARNING,
                    "description": "Pricing information detected"
                },
                {
                    "name": "specific_amounts",
                    "pattern": r"(R\$|USD|BRL)\s*[0-9]{3,}",
                    "severity": Severity.WARNING,
                    "description": "Specific monetary amount detected"
                },
            ],
            "infrastructure": [
                {
                    "name": "internal_domain",
                    "pattern": r"[\w\-]+\.alteragro\.internal",
                    "severity": Severity.ERROR,
                    "description": "Internal domain reference detected"
                },
                {
                    "name": "internal_ip",
                    "pattern": r"(?i)(server|host|endpoint)\s*[:=]\s*['\"]?(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)",
                    "severity": Severity.ERROR,
                    "description": "Internal IP address detected"
                },
                {
                    "name": "aws_resource",
                    "pattern": r"(?i)(aws|amazon).*(bucket|s3|ec2|rds|lambda)",
                    "severity": Severity.WARNING,
                    "description": "AWS resource reference detected"
                },
                {
                    "name": "azure_resource",
                    "pattern": r"(?i)azure.*(storage|vm|database|function)",
                    "severity": Severity.WARNING,
                    "description": "Azure resource reference detected"
                },
            ],
            "prompts": [
                {
                    "name": "prompt_template",
                    "pattern": r"(?i)(system|user|assistant)\s*:\s*['\"]",
                    "severity": Severity.WARNING,
                    "description": "Prompt template pattern detected"
                },
                {
                    "name": "instruction_pattern",
                    "pattern": r"(?i)<\|im_(start|end)\|>",
                    "severity": Severity.WARNING,
                    "description": "LLM instruction delimiter detected"
                },
                {
                    "name": "llama_format",
                    "pattern": r"<<SYS>>|<</SYS>>",
                    "severity": Severity.WARNING,
                    "description": "Llama prompt format detected"
                },
            ],
            "models": [
                {
                    "name": "model_reference",
                    "pattern": r"(?i)(gpt-4|gpt-5|claude-3|claude-4|gemini|llama-[0-9])",
                    "severity": Severity.WARNING,
                    "description": "Specific model reference detected"
                },
                {
                    "name": "fine_tuned",
                    "pattern": r"(?i)fine-?tuned|ft-|custom-model",
                    "severity": Severity.ERROR,
                    "description": "Fine-tuned model reference detected"
                },
                {
                    "name": "model_file",
                    "pattern": r"\.(bin|safetensors|ckpt|pth|pkl)$",
                    "severity": Severity.CRITICAL,
                    "description": "Model weight file detected"
                },
            ],
        }

    def scan_file(self, file_path: Path) -> List[Violation]:
        """Scan a single file for violations"""
        violations = []

        try:
            # Skip binary files
            if self._is_binary(file_path):
                return violations

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                # Check all pattern categories
                for category, patterns in self.patterns.items():
                    for pattern_def in patterns:
                        pattern = pattern_def["pattern"]
                        matches = re.finditer(pattern, line)

                        for match in matches:
                            violation = Violation(
                                file_path=str(file_path),
                                line_number=line_num,
                                severity=pattern_def["severity"].value,
                                category=category,
                                pattern=pattern_def["name"],
                                matched_text=match.group(0)[:100],  # Truncate for safety
                                description=pattern_def["description"]
                            )
                            violations.append(violation)

        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

        return violations

    def scan_directory(self, directory: Path = Path(".")) -> List[Violation]:
        """Scan all files in directory recursively"""
        violations = []

        # Allowed paths (from repository structure)
        allowed_patterns = [
            r"^\.github/",
            r"^lsa/spec/",
            r"^rag/spec/",
            r"^docs/",
            r"^infra/github/",
            r"^legal/",
            r"^README\.md$",
            r"^\.gitignore$",
            r"^\.git-hooks/",
        ]

        # Excluded paths
        excluded_patterns = [
            r"^\.git/",
            r"^node_modules/",
            r"^venv/",
            r"^__pycache__/",
            r"\.pyc$",
        ]

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            # Check if file should be scanned
            rel_path = file_path.relative_to(directory)
            str_path = str(rel_path)

            # Skip excluded paths
            if any(re.match(pattern, str_path) for pattern in excluded_patterns):
                continue

            # Scan the file
            file_violations = self.scan_file(file_path)
            violations.extend(file_violations)

        return violations

    def scan_staged_files(self) -> List[Violation]:
        """Scan only git staged files"""
        violations = []

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True
            )

            staged_files = result.stdout.strip().split("\n")
            staged_files = [f for f in staged_files if f]  # Remove empty strings

            for file_path_str in staged_files:
                file_path = Path(file_path_str)
                if file_path.is_file():
                    file_violations = self.scan_file(file_path)
                    violations.extend(file_violations)

        except subprocess.CalledProcessError:
            print("Error: Could not get staged files from git", file=sys.stderr)
            sys.exit(1)

        return violations

    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return True

    def print_violations(self, violations: List[Violation]):
        """Print violations to console with color"""
        if not violations:
            if self.verbose:
                print("✅ No violations detected!")
            return

        # Group by severity
        by_severity = {
            Severity.CRITICAL.value: [],
            Severity.ERROR.value: [],
            Severity.WARNING.value: [],
            Severity.INFO.value: [],
        }

        for violation in violations:
            by_severity[violation.severity].append(violation)

        # Print summary
        print(f"\n{'='*80}")
        print(f"DLP SCAN RESULTS - {len(violations)} violation(s) detected")
        print(f"{'='*80}\n")

        # Print by severity
        colors = {
            Severity.CRITICAL.value: '\033[0;35m',  # Magenta
            Severity.ERROR.value: '\033[0;31m',     # Red
            Severity.WARNING.value: '\033[1;33m',   # Yellow
            Severity.INFO.value: '\033[0;34m',      # Blue
        }
        NC = '\033[0m'

        for severity in [Severity.CRITICAL.value, Severity.ERROR.value,
                        Severity.WARNING.value, Severity.INFO.value]:
            if by_severity[severity]:
                color = colors[severity]
                print(f"{color}{'='*80}{NC}")
                print(f"{color}{severity.upper()}: {len(by_severity[severity])} violation(s){NC}")
                print(f"{color}{'='*80}{NC}\n")

                for v in by_severity[severity]:
                    print(f"{color}[{v.severity.upper()}] {v.file_path}:{v.line_number}{NC}")
                    print(f"  Category: {v.category}")
                    print(f"  Pattern: {v.pattern}")
                    print(f"  Description: {v.description}")
                    print(f"  Matched: {v.matched_text}")
                    print()

        # Summary
        print(f"{'='*80}")
        print(f"Summary:")
        print(f"  Critical: {len(by_severity[Severity.CRITICAL.value])}")
        print(f"  Errors:   {len(by_severity[Severity.ERROR.value])}")
        print(f"  Warnings: {len(by_severity[Severity.WARNING.value])}")
        print(f"  Info:     {len(by_severity[Severity.INFO.value])}")
        print(f"{'='*80}\n")

    def save_report(self, violations: List[Violation], output_path: str):
        """Save violations report as JSON"""
        report = {
            "scan_timestamp": subprocess.run(
                ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                capture_output=True,
                text=True
            ).stdout.strip(),
            "total_violations": len(violations),
            "violations_by_severity": {
                Severity.CRITICAL.value: len([v for v in violations if v.severity == Severity.CRITICAL.value]),
                Severity.ERROR.value: len([v for v in violations if v.severity == Severity.ERROR.value]),
                Severity.WARNING.value: len([v for v in violations if v.severity == Severity.WARNING.value]),
                Severity.INFO.value: len([v for v in violations if v.severity == Severity.INFO.value]),
            },
            "violations": [v.to_dict() for v in violations]
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        if self.verbose:
            print(f"📄 Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DLP Scanner for YARA Lógica - Detect sensitive information leaks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_secrets.py                    # Scan all files
  python scan_secrets.py --strict           # Exit with error on violations
  python scan_secrets.py --staged           # Scan only staged files
  python scan_secrets.py --output report.json  # Save JSON report
        """
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if violations found (for CI/CD)"
    )

    parser.add_argument(
        "--staged",
        action="store_true",
        help="Scan only git staged files"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Save report to JSON file"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode with prompts"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output except errors"
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)"
    )

    args = parser.parse_args()

    # Create scanner
    scanner = DLPScanner(
        strict=args.strict,
        verbose=not args.quiet
    )

    # Run scan
    if args.staged:
        if scanner.verbose:
            print("🔍 Scanning staged files...")
        violations = scanner.scan_staged_files()
    else:
        if scanner.verbose:
            print(f"🔍 Scanning directory: {args.directory}")
        violations = scanner.scan_directory(Path(args.directory))

    # Print results
    scanner.print_violations(violations)

    # Save report if requested
    if args.output:
        scanner.save_report(violations, args.output)

    # Determine exit code
    if violations:
        critical_errors = [v for v in violations if v.severity in [Severity.CRITICAL.value, Severity.ERROR.value]]

        if args.strict:
            # In strict mode, any violation is an error
            sys.exit(1)
        elif critical_errors:
            # Critical/error violations always cause failure
            sys.exit(1)
        else:
            # Warnings only - exit successfully
            sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
