#!/usr/bin/env python3
"""
External Leak Detection System

Monitors for unauthorized repository copies and code leaks across:
- GitHub (non-fork copies)
- GitLab
- Bitbucket
- Pastebin and paste sites
- Code sharing platforms (Gist, Pastebin, etc.)
- Web searches for brand + architecture keywords

Part of the YARA Lógica leak detection system.

Usage:
    python detect_leaks.py --repo owner/repo --token <TOKEN> --brand "Alter Agro" --architecture "YARA Lógica"
    python detect_leaks.py --repo owner/repo --token <TOKEN> --brand "Alter Agro" --architecture "YARA Lógica" --deep-scan true
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    print("❌ Error: requests not installed. Install with: pip install requests")
    sys.exit(1)


class LeakDetector:
    """Detects unauthorized code leaks and repository copies."""

    def __init__(
        self,
        repo_name: str,
        token: str,
        brand: str,
        architecture: str,
        keywords: str = "",
        extra_keywords: str = "",
        deep_scan: bool = False
    ):
        self.repo_name = repo_name
        self.token = token
        self.brand = brand
        self.architecture = architecture
        self.keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        if extra_keywords:
            self.keywords.extend([k.strip() for k in extra_keywords.split(",") if k.strip()])
        self.deep_scan = deep_scan

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AlterAgro-LeakDetection/1.0",
            "Accept": "application/json"
        })

        self.report = {
            "scan_time": datetime.utcnow().isoformat(),
            "repository": repo_name,
            "brand": brand,
            "architecture": architecture,
            "deep_scan": deep_scan,
            "platforms_scanned": [],
            "total_potential_leaks": 0,
            "leaks_by_platform": {},
            "high_confidence_leaks": [],
            "medium_confidence_leaks": [],
            "low_confidence_leaks": [],
            "alerts": []
        }

    def scan_all_platforms(self) -> None:
        """Scan all platforms for potential leaks."""

        print("🔍 Starting leak detection scan...")
        print(f"Brand: {self.brand}")
        print(f"Architecture: {self.architecture}")
        print(f"Keywords: {', '.join(self.keywords)}")
        print(f"Deep Scan: {self.deep_scan}\n")

        # GitHub (non-fork, non-original repos)
        self._scan_github()

        # GitLab
        self._scan_gitlab()

        # Bitbucket
        self._scan_bitbucket()

        # Pastebin-style sites
        self._scan_paste_sites()

        # Web search (Google/Bing)
        if self.deep_scan:
            self._scan_web_search()

        # Categorize leaks by confidence
        self._categorize_leaks()

    def _scan_github(self) -> None:
        """Scan GitHub for unauthorized copies (non-forks)."""

        print("🔎 Scanning GitHub...")
        platform = "github"
        self.report["platforms_scanned"].append(platform)

        search_queries = [
            f'"{self.brand}" "{self.architecture}"',
            f'"{self.architecture}" LSA PICC',
            f'"YARA Lógica" specification',
        ]

        # Add custom keywords
        for kw in self.keywords[:3]:  # Limit to avoid rate limiting
            search_queries.append(f'"{self.brand}" {kw}')

        found_repos = []

        for query in search_queries:
            try:
                # Use GitHub Code Search API
                url = f"https://api.github.com/search/code?q={quote_plus(query)}&per_page=20"
                headers = {"Authorization": f"token {self.token}"}

                response = self.session.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    for item in items:
                        repo_full_name = item.get("repository", {}).get("full_name", "")

                        # Skip our own repository
                        if repo_full_name == self.repo_name:
                            continue

                        # Check if it's a fork (would be caught by fork monitor)
                        repo_url = item.get("repository", {}).get("url", "")
                        if repo_url:
                            repo_details = self.session.get(repo_url, headers=headers, timeout=30)
                            if repo_details.status_code == 200:
                                repo_data = repo_details.json()
                                if repo_data.get("fork", False):
                                    continue  # Skip forks (handled by fork monitor)

                        found_repos.append({
                            "platform": "github",
                            "repository": repo_full_name,
                            "url": item.get("html_url", ""),
                            "file": item.get("name", ""),
                            "path": item.get("path", ""),
                            "score": item.get("score", 0),
                            "query": query
                        })

                    print(f"  Query '{query}': {len(items)} results")

                elif response.status_code == 403:
                    print(f"  ⚠️  Rate limit exceeded for GitHub search")
                    break

                # Rate limiting - GitHub allows 10 code search requests per minute
                time.sleep(7)

            except Exception as e:
                print(f"  ❌ Error searching GitHub: {e}")

        self.report["leaks_by_platform"][platform] = found_repos
        print(f"  Found {len(found_repos)} potential GitHub leaks (non-forks)\n")

    def _scan_gitlab(self) -> None:
        """Scan GitLab for unauthorized copies."""

        print("🔎 Scanning GitLab...")
        platform = "gitlab"
        self.report["platforms_scanned"].append(platform)

        search_query = f"{self.brand} {self.architecture}"
        found_repos = []

        try:
            # GitLab search API (public projects only, no auth required)
            url = f"https://gitlab.com/api/v4/projects?search={quote_plus(search_query)}&per_page=20"

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                projects = response.json()

                for proj in projects:
                    found_repos.append({
                        "platform": "gitlab",
                        "repository": proj.get("path_with_namespace", ""),
                        "url": proj.get("web_url", ""),
                        "description": proj.get("description", ""),
                        "created_at": proj.get("created_at", ""),
                        "visibility": proj.get("visibility", "unknown")
                    })

                print(f"  Found {len(found_repos)} potential GitLab matches")

        except Exception as e:
            print(f"  ❌ Error searching GitLab: {e}")

        self.report["leaks_by_platform"][platform] = found_repos
        print(f"  GitLab scan complete\n")

    def _scan_bitbucket(self) -> None:
        """Scan Bitbucket for unauthorized copies."""

        print("🔎 Scanning Bitbucket...")
        platform = "bitbucket"
        self.report["platforms_scanned"].append(platform)

        search_query = f"{self.brand} {self.architecture}"
        found_repos = []

        try:
            # Bitbucket public API
            url = f"https://api.bitbucket.org/2.0/repositories?q=name~\"{quote_plus(search_query)}\"&pagelen=20"

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                repos = data.get("values", [])

                for repo in repos:
                    found_repos.append({
                        "platform": "bitbucket",
                        "repository": repo.get("full_name", ""),
                        "url": repo.get("links", {}).get("html", {}).get("href", ""),
                        "description": repo.get("description", ""),
                        "created_on": repo.get("created_on", ""),
                        "is_private": repo.get("is_private", True)
                    })

                print(f"  Found {len(found_repos)} potential Bitbucket matches")

        except Exception as e:
            print(f"  ❌ Error searching Bitbucket: {e}")

        self.report["leaks_by_platform"][platform] = found_repos
        print(f"  Bitbucket scan complete\n")

    def _scan_paste_sites(self) -> None:
        """Scan paste sites for code leaks."""

        print("🔎 Scanning paste sites...")
        platform = "paste_sites"
        self.report["platforms_scanned"].append(platform)

        # Note: Most paste sites don't have public APIs
        # This is a placeholder for future implementation with scraping

        found_pastes = []

        # GitHub Gists (publicly searchable)
        try:
            search_query = f"{self.brand} {self.architecture}"
            url = f"https://api.github.com/search/code?q={quote_plus(search_query)}+extension:md+site:gist.github.com"
            headers = {"Authorization": f"token {self.token}"}

            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                for item in items:
                    found_pastes.append({
                        "platform": "gist",
                        "url": item.get("html_url", ""),
                        "file": item.get("name", ""),
                        "repository": item.get("repository", {}).get("full_name", "")
                    })

                print(f"  Found {len(found_pastes)} potential Gist matches")

        except Exception as e:
            print(f"  ❌ Error searching Gists: {e}")

        self.report["leaks_by_platform"][platform] = found_pastes
        print(f"  Paste sites scan complete\n")

    def _scan_web_search(self) -> None:
        """Perform web search for leaked code (deep scan only)."""

        print("🔎 Performing web search (deep scan)...")
        platform = "web_search"
        self.report["platforms_scanned"].append(platform)

        # Note: This requires a search API (Google Custom Search, Bing, etc.)
        # Placeholder for future implementation

        search_queries = [
            f'"{self.brand}" "{self.architecture}" "source code"',
            f'"{self.architecture}" LSA PICC specification site:-github.com',
            f'"YARA Lógica" repository site:-github.com',
        ]

        print("  ⚠️  Web search requires API key configuration")
        print("  Skipping web search (implement with Google Custom Search API)")

        self.report["leaks_by_platform"][platform] = []
        print(f"  Web search scan complete\n")

    def _categorize_leaks(self) -> None:
        """Categorize detected leaks by confidence level."""

        print("📊 Categorizing potential leaks...")

        for platform, leaks in self.report["leaks_by_platform"].items():
            for leak in leaks:
                confidence = self._assess_confidence(leak, platform)
                leak["confidence"] = confidence

                if confidence == "high":
                    self.report["high_confidence_leaks"].append(leak)
                    self._create_alert("high", leak)
                elif confidence == "medium":
                    self.report["medium_confidence_leaks"].append(leak)
                    self._create_alert("medium", leak)
                else:
                    self.report["low_confidence_leaks"].append(leak)

        self.report["total_potential_leaks"] = sum(
            len(leaks) for leaks in self.report["leaks_by_platform"].values()
        )

        print(f"  High confidence: {len(self.report['high_confidence_leaks'])}")
        print(f"  Medium confidence: {len(self.report['medium_confidence_leaks'])}")
        print(f"  Low confidence: {len(self.report['low_confidence_leaks'])}")
        print(f"  Total: {self.report['total_potential_leaks']}\n")

    def _assess_confidence(self, leak: Dict, platform: str) -> str:
        """Assess confidence level of a leak."""

        # High confidence criteria
        high_indicators = 0
        medium_indicators = 0

        # Check for exact architecture name
        text_fields = [
            leak.get("repository", ""),
            leak.get("description", ""),
            leak.get("file", ""),
            leak.get("path", "")
        ]
        text = " ".join(str(f) for f in text_fields).lower()

        if self.architecture.lower() in text:
            high_indicators += 1

        if self.brand.lower() in text:
            high_indicators += 1

        # Check for specific keywords
        keyword_matches = sum(1 for kw in self.keywords if kw.lower() in text)
        if keyword_matches >= 2:
            high_indicators += 1
        elif keyword_matches == 1:
            medium_indicators += 1

        # Determine confidence
        if high_indicators >= 2:
            return "high"
        elif high_indicators == 1 or medium_indicators >= 2:
            return "medium"
        else:
            return "low"

    def _create_alert(self, severity: str, leak: Dict) -> None:
        """Create an alert for a detected leak."""

        alert = {
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": leak.get("platform", "unknown"),
            "url": leak.get("url", ""),
            "repository": leak.get("repository", ""),
            "confidence": leak.get("confidence", "unknown"),
            "details": leak
        }

        self.report["alerts"].append(alert)

    def generate_reports(self) -> None:
        """Generate JSON and Markdown reports."""

        # JSON Report
        with open("leak_detection_report.json", "w") as f:
            json.dump(self.report, f, indent=2)
        print("📄 Generated: leak_detection_report.json")

        # Markdown Report
        md_content = self._generate_markdown_report()
        with open("leak_detection_report.md", "w") as f:
            f.write(md_content)
        print("📄 Generated: leak_detection_report.md")

    def _generate_markdown_report(self) -> str:
        """Generate Markdown report content."""

        md = f"""# Leak Detection Report

**Repository:** {self.report['repository']}
**Brand:** {self.report['brand']}
**Architecture:** {self.report['architecture']}
**Scan Time:** {self.report['scan_time']}
**Deep Scan:** {self.report['deep_scan']}

## Summary

| Metric | Count |
|--------|-------|
| Platforms Scanned | {len(self.report['platforms_scanned'])} |
| Total Potential Leaks | {self.report['total_potential_leaks']} |
| High Confidence | {len(self.report['high_confidence_leaks'])} |
| Medium Confidence | {len(self.report['medium_confidence_leaks'])} |
| Low Confidence | {len(self.report['low_confidence_leaks'])} |
| Alerts Generated | {len(self.report['alerts'])} |

## Platforms Scanned

{', '.join(self.report['platforms_scanned'])}

## High Confidence Leaks

"""
        if self.report['high_confidence_leaks']:
            for leak in self.report['high_confidence_leaks']:
                md += f"""### 🚨 {leak.get('platform', 'unknown').upper()}: {leak.get('repository', 'Unknown')}

- **URL:** {leak.get('url', 'N/A')}
- **Confidence:** {leak.get('confidence', 'unknown')}
- **Details:** {leak.get('description', leak.get('file', 'N/A'))}

"""
        else:
            md += "✅ No high-confidence leaks detected.\n\n"

        md += "## Medium Confidence Leaks\n\n"

        if self.report['medium_confidence_leaks']:
            for leak in self.report['medium_confidence_leaks']:
                md += f"""### ⚠️ {leak.get('platform', 'unknown').upper()}: {leak.get('repository', 'Unknown')}

- **URL:** {leak.get('url', 'N/A')}
- **Confidence:** {leak.get('confidence', 'unknown')}

"""
        else:
            md += "✅ No medium-confidence leaks detected.\n\n"

        md += """---

## Recommendations

### For High-Confidence Leaks:
1. **Investigate immediately** - Verify if unauthorized
2. **Document evidence** - Take screenshots, archive pages
3. **Contact platform** - Request takedown if unauthorized
4. **Legal action** - Escalate to legal@alteragro.com.br if needed

### For Medium-Confidence Leaks:
1. **Review manually** - Determine if false positive
2. **Monitor** - Add to watchlist if uncertain
3. **Escalate** - Promote to high-confidence if confirmed

### General:
- Run deep scans regularly (weekly recommended)
- Monitor new leaks via automated CI/CD
- Update keywords based on findings
- Consider DMCA takedowns for GitHub/GitLab violations

**Resources:**
- [Security Policy](../.github/SECURITY.md)
- [Legal Contact](mailto:legal@alteragro.com.br)
- [DMCA Process](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)
"""

        return md

    def print_summary(self) -> None:
        """Print scan summary."""

        print("\n" + "=" * 70)
        print("LEAK DETECTION SUMMARY")
        print("=" * 70)
        print(f"Repository: {self.report['repository']}")
        print(f"Brand: {self.report['brand']}")
        print(f"Architecture: {self.report['architecture']}")
        print(f"Scan Time: {self.report['scan_time']}")
        print(f"\nPlatforms Scanned: {len(self.report['platforms_scanned'])}")
        print(f"  - {', '.join(self.report['platforms_scanned'])}")
        print(f"\nPotential Leaks Found: {self.report['total_potential_leaks']}")
        print(f"  - High Confidence: {len(self.report['high_confidence_leaks'])}")
        print(f"  - Medium Confidence: {len(self.report['medium_confidence_leaks'])}")
        print(f"  - Low Confidence: {len(self.report['low_confidence_leaks'])}")

        if self.report['high_confidence_leaks']:
            print(f"\n🚨 HIGH-CONFIDENCE LEAKS DETECTED: {len(self.report['high_confidence_leaks'])}")

        print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Detect unauthorized code leaks across platforms"
    )
    parser.add_argument("--repo", required=True, help="Repository in format owner/repo")
    parser.add_argument("--token", required=True, help="GitHub token for API access")
    parser.add_argument("--brand", required=True, help="Brand name to search for")
    parser.add_argument("--architecture", required=True, help="Architecture name to search for")
    parser.add_argument("--keywords", default="", help="Comma-separated keywords to search")
    parser.add_argument("--extra-keywords", default="", help="Additional keywords from workflow")
    parser.add_argument("--deep-scan", default="false", help="Enable deep web search")
    parser.add_argument("--create-issue-on-alert", action="store_true", help="Create GitHub issue if leaks found")

    args = parser.parse_args()

    deep_scan = args.deep_scan.lower() in ["true", "1", "yes"]

    # Initialize detector
    detector = LeakDetector(
        repo_name=args.repo,
        token=args.token,
        brand=args.brand,
        architecture=args.architecture,
        keywords=args.keywords,
        extra_keywords=args.extra_keywords,
        deep_scan=deep_scan
    )

    # Scan all platforms
    detector.scan_all_platforms()

    # Generate reports
    detector.generate_reports()

    # Print summary
    detector.print_summary()

    # Exit with error if high-confidence leaks found
    if len(detector.report['high_confidence_leaks']) > 0:
        print(f"⚠️  Exiting with error code due to {len(detector.report['high_confidence_leaks'])} high-confidence leaks")
        sys.exit(1)

    print("✅ Leak detection complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
