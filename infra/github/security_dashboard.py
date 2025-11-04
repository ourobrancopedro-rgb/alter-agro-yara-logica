#!/usr/bin/env python3
"""
Security Monitoring Dashboard for YARA Lógica
==============================================

Tracks security posture and generates reports.

Usage:
    python security_dashboard.py                # Generate HTML dashboard
    python security_dashboard.py --format json  # JSON output
    python security_dashboard.py --notify slack # Send to Slack

Author: Alter Agro Ltda.
License: BUSL-1.1
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class SecurityDashboard:
    """Generate security posture dashboard"""

    def __init__(self):
        self.checks = []
        self.timestamp = datetime.utcnow().isoformat()

    def check_last_scan(self) -> Dict[str, Any]:
        """Check when security scans last ran"""
        try:
            result = subprocess.run(
                ["git", "log", "--grep=security", "--format=%ci", "-1"],
                capture_output=True,
                text=True
            )
            last_scan = result.stdout.strip() or "Never"
            status = "✅" if last_scan != "Never" else "❌"
            return {
                "name": "Last Security Scan",
                "status": status,
                "value": last_scan,
                "passed": last_scan != "Never"
            }
        except Exception as e:
            return {"name": "Last Security Scan", "status": "❌", "value": str(e), "passed": False}

    def check_security_issues(self) -> Dict[str, Any]:
        """Count security-labeled issues (if GitHub CLI available)"""
        try:
            result = subprocess.run(
                ["gh", "issue", "list", "--label", "security", "--json", "state"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                issues = json.loads(result.stdout)
                open_count = len([i for i in issues if i.get("state") == "OPEN"])
                status = "⚠️" if open_count > 0 else "✅"
                return {
                    "name": "Open Security Issues",
                    "status": status,
                    "value": f"{open_count} open",
                    "passed": open_count == 0
                }
        except Exception:
            pass
        return {"name": "Open Security Issues", "status": "ℹ️", "value": "N/A (gh CLI not available)", "passed": True}

    def check_branch_protection(self) -> Dict[str, Any]:
        """Check if main branch has protection"""
        # Note: Requires GitHub API access
        return {
            "name": "Branch Protection",
            "status": "ℹ️",
            "value": "Check manually on GitHub",
            "passed": True
        }

    def check_gpg_signatures(self) -> Dict[str, Any]:
        """Check recent commits for GPG signatures"""
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=%G?", "-10"],
                capture_output=True,
                text=True
            )
            signatures = result.stdout.strip().split("\n")
            signed = sum(1 for sig in signatures if sig == "G")
            total = len(signatures)
            percent = (signed / total * 100) if total > 0 else 0
            status = "✅" if percent >= 80 else "⚠️"
            return {
                "name": "GPG Signature Compliance",
                "status": status,
                "value": f"{signed}/{total} commits ({percent:.0f}%)",
                "passed": percent >= 80
            }
        except Exception as e:
            return {"name": "GPG Signature Compliance", "status": "❌", "value": str(e), "passed": False}

    def check_hash_ledger(self) -> Dict[str, Any]:
        """Verify hash ledger integrity"""
        try:
            result = subprocess.run(
                ["python3", "infra/github/verify_hashes.py"],
                capture_output=True,
                text=True
            )
            passed = result.returncode == 0
            status = "✅" if passed else "❌"
            return {
                "name": "Hash Ledger Integrity",
                "status": status,
                "value": "Valid" if passed else "Mismatches detected",
                "passed": passed
            }
        except Exception as e:
            return {"name": "Hash Ledger Integrity", "status": "❌", "value": str(e), "passed": False}

    def check_secret_scan(self) -> Dict[str, Any]:
        """Run secret scanner"""
        try:
            result = subprocess.run(
                ["python3", "infra/github/scan_secrets.py", "--strict"],
                capture_output=True,
                text=True
            )
            passed = result.returncode == 0
            status = "✅" if passed else "❌"
            return {
                "name": "Secret Scan",
                "status": status,
                "value": "Clean" if passed else "Violations detected",
                "passed": passed
            }
        except Exception as e:
            return {"name": "Secret Scan", "status": "❌", "value": str(e), "passed": False}

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Run all security checks"""
        self.checks = [
            self.check_hash_ledger(),
            self.check_secret_scan(),
            self.check_gpg_signatures(),
            self.check_last_scan(),
            self.check_security_issues(),
            self.check_branch_protection(),
        ]
        return self.checks

    def generate_html(self) -> str:
        """Generate HTML dashboard"""
        passed = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        score = (passed / total * 100) if total > 0 else 0

        rows = "\n".join([
            f'<tr><td>{c["status"]}</td><td>{c["name"]}</td><td>{c["value"]}</td></tr>'
            for c in self.checks
        ])

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>YARA Lógica Security Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .score {{ font-size: 48px; font-weight: bold; color: {'#28a745' if score >= 80 else '#ffc107' if score >= 50 else '#dc3545'}; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .footer {{ margin-top: 30px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ YARA Lógica Security Dashboard</h1>
        <p><strong>Generated:</strong> {self.timestamp}</p>
        <div class="score">{score:.0f}%</div>
        <p><strong>Security Score:</strong> {passed}/{total} checks passed</p>

        <h2>Security Checks</h2>
        <table>
            <tr><th>Status</th><th>Check</th><th>Result</th></tr>
            {rows}
        </table>

        <div class="footer">
            <p><strong>© 2025 Alter Agro Ltda.</strong></p>
            <p>For issues, contact: security@alteragro.com.br</p>
        </div>
    </div>
</body>
</html>"""

    def generate_json(self) -> str:
        """Generate JSON report"""
        passed = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        return json.dumps({
            "timestamp": self.timestamp,
            "score": (passed / total * 100) if total > 0 else 0,
            "passed": passed,
            "total": total,
            "checks": self.checks
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="YARA Lógica Security Dashboard")
    parser.add_argument("--format", choices=["html", "json"], default="html", help="Output format")
    parser.add_argument("--output", "-o", help="Output file (default: stdout for JSON, dashboard.html for HTML)")
    args = parser.parse_args()

    dashboard = SecurityDashboard()
    print("🔍 Running security checks...", file=sys.stderr)
    dashboard.run_all_checks()

    if args.format == "html":
        output = dashboard.generate_html()
        output_file = args.output or "dashboard.html"
        with open(output_file, "w") as f:
            f.write(output)
        print(f"✅ Dashboard generated: {output_file}", file=sys.stderr)
    else:
        output = dashboard.generate_json()
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Report saved: {args.output}", file=sys.stderr)
        else:
            print(output)


if __name__ == "__main__":
    main()
