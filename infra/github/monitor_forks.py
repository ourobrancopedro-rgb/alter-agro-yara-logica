#!/usr/bin/env python3
"""
Fork Monitoring and Visibility Analysis

Monitors GitHub forks for:
- New public forks (potential IP exposure)
- Visibility changes (private -> public)
- Fork activity and modifications
- Unauthorized distribution patterns

Part of the YARA Lógica leak detection system.

Usage:
    python monitor_forks.py --repo owner/repo --token <GITHUB_TOKEN>
    python monitor_forks.py --repo owner/repo --token <GITHUB_TOKEN> --create-issue-on-alert
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

try:
    from github import Github, GithubException
    from github.Repository import Repository
except ImportError:
    print("❌ Error: PyGithub not installed. Install with: pip install PyGithub")
    sys.exit(1)


class ForkMonitor:
    """Monitors repository forks for security concerns."""

    def __init__(self, repo_name: str, token: str):
        self.repo_name = repo_name
        self.github = Github(token)
        self.repo: Optional[Repository] = None
        self.alerts: List[Dict] = []
        self.report: Dict = {
            "scan_time": datetime.utcnow().isoformat(),
            "repository": repo_name,
            "total_forks": 0,
            "public_forks": 0,
            "private_forks": 0,
            "new_forks_24h": 0,
            "new_forks_7d": 0,
            "suspicious_forks": [],
            "alerts": []
        }

    def load_repository(self) -> bool:
        """Load the repository object."""
        try:
            self.repo = self.github.get_repo(self.repo_name)
            print(f"✅ Loaded repository: {self.repo.full_name}")
            return True
        except GithubException as e:
            print(f"❌ Error loading repository: {e}")
            return False

    def analyze_forks(self) -> None:
        """Analyze all forks for security concerns."""
        if not self.repo:
            print("❌ Repository not loaded")
            return

        print("\n🔍 Analyzing forks...")
        print(f"Total forks: {self.repo.forks_count}\n")

        self.report["total_forks"] = self.repo.forks_count

        # Time thresholds for "new" forks
        now = datetime.utcnow()
        threshold_24h = now - timedelta(hours=24)
        threshold_7d = now - timedelta(days=7)

        try:
            forks = self.repo.get_forks()

            for fork in forks:
                self._analyze_fork(fork, threshold_24h, threshold_7d)

        except GithubException as e:
            print(f"❌ Error fetching forks: {e}")
            self.report["alerts"].append({
                "severity": "error",
                "message": f"Failed to fetch forks: {e}"
            })

    def _analyze_fork(
        self,
        fork: Repository,
        threshold_24h: datetime,
        threshold_7d: datetime
    ) -> None:
        """Analyze individual fork for security concerns."""

        # Basic fork information
        fork_data = {
            "name": fork.full_name,
            "owner": fork.owner.login,
            "created_at": fork.created_at.isoformat(),
            "updated_at": fork.updated_at.isoformat(),
            "is_private": fork.private,
            "has_issues": fork.has_issues,
            "has_wiki": fork.has_wiki,
            "size": fork.size,
            "default_branch": fork.default_branch,
            "concerns": []
        }

        # Count public/private forks
        if fork.private:
            self.report["private_forks"] += 1
        else:
            self.report["public_forks"] += 1

        # Check if fork is new
        is_new_24h = fork.created_at >= threshold_24h
        is_new_7d = fork.created_at >= threshold_7d

        if is_new_24h:
            self.report["new_forks_24h"] += 1
            fork_data["concerns"].append("NEW_FORK_24H")
            print(f"🆕 New fork (24h): {fork.full_name}")

        elif is_new_7d:
            self.report["new_forks_7d"] += 1
            fork_data["concerns"].append("NEW_FORK_7D")
            print(f"🆕 New fork (7d): {fork.full_name}")

        # Security concerns for PUBLIC forks
        if not fork.private:
            fork_data["concerns"].append("PUBLIC_VISIBILITY")

            # Alert on new public forks
            if is_new_24h:
                self._create_alert(
                    severity="high",
                    fork=fork,
                    message=f"New public fork created: {fork.full_name}",
                    reason="Public forks expose repository content"
                )

            # Check if fork has been modified (potential redistribution)
            if fork.updated_at > fork.created_at + timedelta(hours=1):
                time_since_update = now.utcnow() - fork.updated_at
                if time_since_update < timedelta(days=7):
                    fork_data["concerns"].append("RECENT_MODIFICATIONS")

            # Check fork size - significant increase may indicate additions
            try:
                if fork.size > (self.repo.size * 1.5):
                    fork_data["concerns"].append("SIZE_INCREASED")
                    self._create_alert(
                        severity="medium",
                        fork=fork,
                        message=f"Fork size exceeds parent: {fork.full_name}",
                        reason=f"Fork size ({fork.size}KB) > Parent size ({self.repo.size}KB)"
                    )
            except Exception:
                pass

            # Check if fork has different default branch
            if fork.default_branch != self.repo.default_branch:
                fork_data["concerns"].append("DIFFERENT_DEFAULT_BRANCH")

        # Flag suspicious forks
        if len(fork_data["concerns"]) > 0:
            self.report["suspicious_forks"].append(fork_data)
            if not fork.private:
                print(f"⚠️  Suspicious fork: {fork.full_name}")
                print(f"   Concerns: {', '.join(fork_data['concerns'])}")

    def _create_alert(
        self,
        severity: str,
        fork: Repository,
        message: str,
        reason: str
    ) -> None:
        """Create an alert for security team."""
        alert = {
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "fork": fork.full_name,
            "fork_url": fork.html_url,
            "owner": fork.owner.login,
            "message": message,
            "reason": reason,
            "is_private": fork.private
        }

        self.alerts.append(alert)
        self.report["alerts"].append(alert)

        # Print alert
        emoji = "🚨" if severity == "high" else "⚠️"
        print(f"\n{emoji} ALERT [{severity.upper()}]")
        print(f"   Fork: {fork.full_name}")
        print(f"   Message: {message}")
        print(f"   Reason: {reason}")
        print(f"   URL: {fork.html_url}\n")

    def generate_reports(self) -> None:
        """Generate JSON and Markdown reports."""

        # JSON Report
        with open("fork_monitoring_report.json", "w") as f:
            json.dump(self.report, f, indent=2)
        print("📄 Generated: fork_monitoring_report.json")

        # Markdown Report
        md_content = self._generate_markdown_report()
        with open("fork_monitoring_report.md", "w") as f:
            f.write(md_content)
        print("📄 Generated: fork_monitoring_report.md")

    def _generate_markdown_report(self) -> str:
        """Generate Markdown report content."""

        md = f"""# Fork Monitoring Report

**Repository:** {self.report['repository']}
**Scan Time:** {self.report['scan_time']}

## Summary

| Metric | Count |
|--------|-------|
| Total Forks | {self.report['total_forks']} |
| Public Forks | {self.report['public_forks']} |
| Private Forks | {self.report['private_forks']} |
| New Forks (24h) | {self.report['new_forks_24h']} |
| New Forks (7d) | {self.report['new_forks_7d']} |
| Suspicious Forks | {len(self.report['suspicious_forks'])} |
| Alerts Generated | {len(self.report['alerts'])} |

## Alerts

"""
        if self.report['alerts']:
            for alert in self.report['alerts']:
                severity_emoji = "🚨" if alert['severity'] == 'high' else "⚠️"
                md += f"""### {severity_emoji} {alert['severity'].upper()}: {alert['message']}

- **Fork:** [{alert['fork']}]({alert['fork_url']})
- **Owner:** {alert['owner']}
- **Visibility:** {'Private' if alert['is_private'] else 'Public'}
- **Reason:** {alert['reason']}
- **Time:** {alert['timestamp']}

"""
        else:
            md += "✅ No alerts generated.\n\n"

        md += "## Suspicious Forks\n\n"

        if self.report['suspicious_forks']:
            for fork in self.report['suspicious_forks']:
                md += f"""### {fork['name']}

- **Owner:** {fork['owner']}
- **Created:** {fork['created_at']}
- **Updated:** {fork['updated_at']}
- **Visibility:** {'Private' if fork['is_private'] else '**PUBLIC**'}
- **Size:** {fork['size']} KB
- **Concerns:** {', '.join(fork['concerns'])}

"""
        else:
            md += "✅ No suspicious forks detected.\n\n"

        md += """---

**Recommendations:**

1. Review all public forks for unauthorized redistribution
2. Contact owners of suspicious forks to verify intent
3. For unauthorized copies, initiate takedown procedures
4. Consider enabling fork visibility restrictions if available
5. Monitor fork activity regularly (automated via CI/CD)

**Resources:**
- [Security Policy](../.github/SECURITY.md)
- [Legal Contact](mailto:legal@alteragro.com.br)
- [DMCA Takedown Guide](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)
"""

        return md

    def create_github_issue(self) -> None:
        """Create GitHub issue if high-severity alerts exist."""

        high_alerts = [a for a in self.alerts if a['severity'] == 'high']

        if not high_alerts:
            print("ℹ️  No high-severity alerts - skipping issue creation")
            return

        print(f"\n📝 Creating GitHub issue for {len(high_alerts)} high-severity alerts...")

        try:
            title = f"🚨 Fork Security Alert - {len(high_alerts)} new public fork(s) detected"

            body = f"""## Fork Monitoring Alert

**Detection Time:** {datetime.utcnow().isoformat()}
**High-Severity Alerts:** {len(high_alerts)}

### Summary

Automated fork monitoring has detected new public forks of this repository.

"""
            for alert in high_alerts:
                body += f"""### {alert['message']}

- **Fork:** [{alert['fork']}]({alert['fork_url']})
- **Owner:** {alert['owner']}
- **Reason:** {alert['reason']}
- **Time:** {alert['timestamp']}

"""

            body += """### Next Steps

1. **Review the forks** listed above
2. **Verify legitimacy** - Check if forks are authorized (team members, collaborators)
3. **For unauthorized forks:**
   - Contact fork owner politely asking about their intent
   - If redistributing or violating license: request takedown
   - If no response: file DMCA takedown notice
4. **Update monitoring** if false positive

### Resources

- [Fork Monitoring Report](../fork_monitoring_report.md)
- [Security Policy](../.github/SECURITY.md)
- [Legal Team](mailto:legal@alteragro.com.br)
- [DMCA Takedown Process](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)

---

*Auto-generated by Fork Monitoring System*
"""

            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=["security", "fork-alert", "urgent"]
            )

            print(f"✅ Created issue: {issue.html_url}")

        except GithubException as e:
            print(f"❌ Failed to create issue: {e}")

    def print_summary(self) -> None:
        """Print monitoring summary."""

        print("\n" + "=" * 70)
        print("FORK MONITORING SUMMARY")
        print("=" * 70)
        print(f"Repository: {self.report['repository']}")
        print(f"Scan Time: {self.report['scan_time']}")
        print(f"\nTotal Forks: {self.report['total_forks']}")
        print(f"  - Public: {self.report['public_forks']}")
        print(f"  - Private: {self.report['private_forks']}")
        print(f"\nNew Forks:")
        print(f"  - Last 24h: {self.report['new_forks_24h']}")
        print(f"  - Last 7d: {self.report['new_forks_7d']}")
        print(f"\nSuspicious Forks: {len(self.report['suspicious_forks'])}")
        print(f"Alerts Generated: {len(self.report['alerts'])}")

        high_alerts = len([a for a in self.alerts if a['severity'] == 'high'])
        if high_alerts > 0:
            print(f"\n🚨 HIGH-SEVERITY ALERTS: {high_alerts}")

        print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor GitHub forks for security concerns"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in format owner/repo"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="GitHub personal access token"
    )
    parser.add_argument(
        "--create-issue-on-alert",
        action="store_true",
        help="Create GitHub issue if high-severity alerts found"
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = ForkMonitor(args.repo, args.token)

    # Load repository
    if not monitor.load_repository():
        sys.exit(1)

    # Analyze forks
    monitor.analyze_forks()

    # Generate reports
    monitor.generate_reports()

    # Print summary
    monitor.print_summary()

    # Create issue if requested and alerts exist
    if args.create_issue_on_alert:
        monitor.create_github_issue()

    # Exit with error code if high-severity alerts
    high_alerts = len([a for a in monitor.alerts if a['severity'] == 'high'])
    if high_alerts > 0:
        print(f"⚠️  Exiting with error code due to {high_alerts} high-severity alerts")
        sys.exit(1)

    print("✅ Monitoring complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
