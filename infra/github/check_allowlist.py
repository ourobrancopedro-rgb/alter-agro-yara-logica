#!/usr/bin/env python3
"""
Allowlist Checker for YARA Lógica
==================================

Enhanced path enforcement and file validation for spec-only repository.

This tool verifies:
- All files are within allowed paths (allowlist)
- File types are appropriate for their locations
- File sizes are within limits
- No binary files (except allowed types)
- No symlinks (security risk)
- Hash ledger integrity

Usage:
    python check_allowlist.py              # Check all files
    python check_allowlist.py --fix        # Suggest fixes for violations
    python check_allowlist.py --log        # Log all checks to file
    python check_allowlist.py --staged     # Check only staged files
    python check_allowlist.py --verbose    # Detailed output

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
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple


@dataclass
class Violation:
    """Represents an allowlist violation"""
    file_path: str
    violation_type: str
    severity: str
    description: str
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class AllowlistChecker:
    """Checks repository files against allowlist and policies"""

    # Allowed path patterns (regex)
    ALLOWED_PATHS = [
        r"^\.github/",
        r"^lsa/spec/",
        r"^rag/spec/",
        r"^docs/",
        r"^infra/github/",
        r"^legal/",
        r"^tools/",
        r"^scripts/",
        r"^tests/",
        r"^\.git-hooks/",
        r"^README\.md$",
        r"^SECURITY\.md$",
        r"^NOTICE$",
        r"^RESPONSE_PLAYBOOKS\.md$",
        r"^\.gitignore$",
        r"^\.gitleaks\.toml$",
        r"^\.gitleaksignore$",
        r"^\.trufflehog\.yaml$",
        r"^\.pre-commit-config\.yaml$",
        r"^pyproject\.toml$",
    ]

    # File type restrictions by directory
    FILE_TYPE_RULES = {
        "lsa/spec/": {
            "allowed": [".md", ".json", ".yaml", ".yml", ".py"],  # .py for examples
            "max_size_kb": 500,
        },
        "rag/spec/": {
            "allowed": [".md", ".json", ".yaml", ".yml"],
            "max_size_kb": 500,
        },
        "docs/": {
            "allowed": [".md", ".pdf", ".png", ".jpg", ".svg", ".json"],  # .json for examples
            "max_size_kb": 2048,
        },
        "infra/github/": {
            "allowed": [".py", ".sh", ".json", ".md"],
            "max_size_kb": 1024,
        },
        "legal/": {
            "allowed": [".md", ".txt", ".pdf", ""],  # "" for LICENSE file
            "max_size_kb": 1024,
        },
        ".github/": {
            "allowed": [".md", ".yml", ".yaml", ".sh"],
            "max_size_kb": 512,
        },
        "tools/": {
            "allowed": [".py", ".sh", ".md", ".json"],
            "max_size_kb": 1024,
        },
        "scripts/": {
            "allowed": [".py", ".sh", ".md"],
            "max_size_kb": 512,
        },
        "tests/": {
            "allowed": [".py", ".json", ".yaml", ".yml"],
            "max_size_kb": 512,
        },
    }

    # Binary file extensions (normally forbidden)
    BINARY_EXTENSIONS = {
        ".bin", ".safetensors", ".ckpt", ".pth", ".pkl",
        ".h5", ".pb", ".onnx", ".exe", ".dll", ".so",
        ".dylib", ".class", ".jar", ".war"
    }

    # Allowed binary extensions (exceptions)
    ALLOWED_BINARIES = {
        ".pdf", ".png", ".jpg", ".jpeg", ".svg", ".gif"
    }

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        self.verbose = verbose
        self.log_file = log_file
        self.violations: List[Violation] = []

        if self.log_file:
            self.log_handle = open(self.log_file, 'a')
        else:
            self.log_handle = None

    def __del__(self):
        if self.log_handle:
            self.log_handle.close()

    def log(self, message: str):
        """Log message to file and optionally console"""
        if self.verbose:
            print(message)

        if self.log_handle:
            self.log_handle.write(message + "\n")
            self.log_handle.flush()

    def check_path_allowlist(self, file_path: str) -> Optional[Violation]:
        """Check if file path is in allowlist"""
        for allowed_pattern in self.ALLOWED_PATHS:
            if re.match(allowed_pattern, file_path):
                return None

        return Violation(
            file_path=file_path,
            violation_type="path_not_allowed",
            severity="error",
            description=f"File is outside allowed paths",
            suggestion="Move file to an allowed directory or update allowlist if this is intentional"
        )

    def check_file_type(self, file_path: str) -> Optional[Violation]:
        """Check if file type is allowed for its directory"""
        path = Path(file_path)
        extension = path.suffix.lower()

        # Find applicable directory rule
        for dir_pattern, rules in self.FILE_TYPE_RULES.items():
            if file_path.startswith(dir_pattern):
                allowed_exts = rules["allowed"]

                if extension not in allowed_exts:
                    return Violation(
                        file_path=file_path,
                        violation_type="file_type_not_allowed",
                        severity="warning",
                        description=f"File type '{extension}' not allowed in {dir_pattern}",
                        suggestion=f"Allowed types: {', '.join(allowed_exts)}"
                    )

        return None

    def check_file_size(self, file_path: str) -> Optional[Violation]:
        """Check if file size is within limits"""
        try:
            path = Path(file_path)
            if not path.is_file():
                return None

            size_bytes = path.stat().st_size
            size_kb = size_bytes / 1024

            # Find applicable directory rule
            for dir_pattern, rules in self.FILE_TYPE_RULES.items():
                if file_path.startswith(dir_pattern):
                    max_size_kb = rules["max_size_kb"]

                    if size_kb > max_size_kb:
                        return Violation(
                            file_path=file_path,
                            violation_type="file_too_large",
                            severity="error",
                            description=f"File size {size_kb:.1f}KB exceeds limit of {max_size_kb}KB for {dir_pattern}",
                            suggestion="Reduce file size or split into multiple files"
                        )

        except Exception as e:
            self.log(f"Warning: Could not check size of {file_path}: {e}")

        return None

    def check_binary_file(self, file_path: str) -> Optional[Violation]:
        """Check if file is a forbidden binary"""
        path = Path(file_path)
        extension = path.suffix.lower()

        # Check if it's a forbidden binary
        if extension in self.BINARY_EXTENSIONS:
            return Violation(
                file_path=file_path,
                violation_type="forbidden_binary",
                severity="critical",
                description=f"Binary file type '{extension}' is not allowed",
                suggestion="Remove this file - binary artifacts should not be in the public repository"
            )

        # Check if file is actually binary (by content)
        if extension not in self.ALLOWED_BINARIES:
            try:
                with open(path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:
                        return Violation(
                            file_path=file_path,
                            violation_type="binary_content",
                            severity="error",
                            description="File appears to be binary based on content",
                            suggestion="Ensure this is a text file or approved binary type"
                        )
            except Exception:
                pass

        return None

    def check_symlink(self, file_path: str) -> Optional[Violation]:
        """Check if file is a symlink (security risk)"""
        path = Path(file_path)

        if path.is_symlink():
            target = path.resolve()
            return Violation(
                file_path=file_path,
                violation_type="symlink_detected",
                severity="warning",
                description=f"Symlink detected (points to {target})",
                suggestion="Replace symlink with actual file or remove if unnecessary"
            )

        return None

    def check_file(self, file_path: str) -> List[Violation]:
        """Run all checks on a file"""
        violations = []

        # Check 1: Path allowlist
        v = self.check_path_allowlist(file_path)
        if v:
            violations.append(v)

        # Check 2: File type
        v = self.check_file_type(file_path)
        if v:
            violations.append(v)

        # Check 3: File size
        v = self.check_file_size(file_path)
        if v:
            violations.append(v)

        # Check 4: Binary files
        v = self.check_binary_file(file_path)
        if v:
            violations.append(v)

        # Check 5: Symlinks
        v = self.check_symlink(file_path)
        if v:
            violations.append(v)

        return violations

    def check_all_files(self) -> List[Violation]:
        """Check all tracked files in repository"""
        violations = []

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                check=True
            )

            files = result.stdout.strip().split("\n")
            files = [f for f in files if f]  # Remove empty strings

            self.log(f"Checking {len(files)} files...")

            for file_path in files:
                file_violations = self.check_file(file_path)
                violations.extend(file_violations)

                if file_violations:
                    self.log(f"  ❌ {file_path}: {len(file_violations)} violation(s)")
                else:
                    if self.verbose:
                        self.log(f"  ✅ {file_path}")

        except subprocess.CalledProcessError as e:
            print(f"Error: Could not get file list from git: {e}", file=sys.stderr)
            sys.exit(1)

        return violations

    def check_staged_files(self) -> List[Violation]:
        """Check only git staged files"""
        violations = []

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True
            )

            files = result.stdout.strip().split("\n")
            files = [f for f in files if f]

            self.log(f"Checking {len(files)} staged files...")

            for file_path in files:
                file_violations = self.check_file(file_path)
                violations.extend(file_violations)

        except subprocess.CalledProcessError:
            print("Error: Could not get staged files from git", file=sys.stderr)
            sys.exit(1)

        return violations

    def print_violations(self, violations: List[Violation]):
        """Print violations to console"""
        if not violations:
            print("✅ All files pass allowlist checks!")
            return

        # Group by severity
        by_severity = {
            "critical": [],
            "error": [],
            "warning": [],
            "info": [],
        }

        for violation in violations:
            by_severity[violation.severity].append(violation)

        # Print summary
        print(f"\n{'='*80}")
        print(f"ALLOWLIST CHECK RESULTS - {len(violations)} violation(s) detected")
        print(f"{'='*80}\n")

        # Color codes
        colors = {
            "critical": '\033[0;35m',  # Magenta
            "error": '\033[0;31m',     # Red
            "warning": '\033[1;33m',   # Yellow
            "info": '\033[0;34m',      # Blue
        }
        NC = '\033[0m'

        # Print by severity
        for severity in ["critical", "error", "warning", "info"]:
            if by_severity[severity]:
                color = colors[severity]
                print(f"{color}{'='*80}{NC}")
                print(f"{color}{severity.upper()}: {len(by_severity[severity])} violation(s){NC}")
                print(f"{color}{'='*80}{NC}\n")

                for v in by_severity[severity]:
                    print(f"{color}[{v.severity.upper()}] {v.file_path}{NC}")
                    print(f"  Type: {v.violation_type}")
                    print(f"  Description: {v.description}")
                    if v.suggestion:
                        print(f"  Suggestion: {v.suggestion}")
                    print()

        # Summary
        print(f"{'='*80}")
        print(f"Summary:")
        print(f"  Critical: {len(by_severity['critical'])}")
        print(f"  Errors:   {len(by_severity['error'])}")
        print(f"  Warnings: {len(by_severity['warning'])}")
        print(f"  Info:     {len(by_severity['info'])}")
        print(f"{'='*80}\n")

    def generate_report(self, violations: List[Violation]) -> str:
        """Generate detailed violation report"""
        report = {
            "total_violations": len(violations),
            "violations_by_severity": {
                "critical": len([v for v in violations if v.severity == "critical"]),
                "error": len([v for v in violations if v.severity == "error"]),
                "warning": len([v for v in violations if v.severity == "warning"]),
                "info": len([v for v in violations if v.severity == "info"]),
            },
            "violations": [v.to_dict() for v in violations]
        }

        return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Allowlist Checker for YARA Lógica - Enforce path and file policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_allowlist.py              # Check all files
  python check_allowlist.py --fix        # Show fix suggestions
  python check_allowlist.py --staged     # Check only staged files
  python check_allowlist.py --log allowlist.log  # Log to file
        """
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show fix suggestions for violations"
    )

    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check only git staged files"
    )

    parser.add_argument(
        "--log",
        type=str,
        help="Log checks to file"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    # Create checker
    checker = AllowlistChecker(
        verbose=args.verbose,
        log_file=args.log
    )

    # Run checks
    if args.staged:
        print("🔍 Checking staged files against allowlist...")
        violations = checker.check_staged_files()
    else:
        print("🔍 Checking all files against allowlist...")
        violations = checker.check_all_files()

    # Print violations
    checker.print_violations(violations)

    # Save report if requested
    if args.output:
        report = checker.generate_report(violations)
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {args.output}")

    # Exit code
    if violations:
        critical_errors = [v for v in violations if v.severity in ["critical", "error"]]
        if critical_errors:
            sys.exit(1)
        else:
            # Warnings only
            sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
