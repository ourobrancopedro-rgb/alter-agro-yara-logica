#!/usr/bin/env python3
"""
Hash Ledger with Historical Tracking

Enhanced version of hash ledger that maintains full audit trail of file changes.
Compatible with existing verify_hashes.py - can be used to migrate existing ledgers.

Usage:
    # Verify with history
    python hash_ledger_history.py --verify

    # Update ledger with new commit
    python hash_ledger_history.py --update --author "user@example.com" --commit "abc123"

    # Generate audit report
    python hash_ledger_history.py --audit-report

    # Migrate old ledger format
    python hash_ledger_history.py --migrate
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


LEDGER_PATH = Path(__file__).resolve().parent / "hash_ledger_history.json"
OLD_LEDGER_PATH = Path(__file__).resolve().parent / "hash_ledger.json"


class HistoricalHashLedger:
    """Hash ledger with full change history"""

    def __init__(self, ledger_path: Path):
        self.ledger_path = ledger_path
        self.ledger = self.load_ledger()

    def load_ledger(self) -> Dict:
        """Load ledger with history"""
        if not self.ledger_path.is_file():
            return {}

        with open(self.ledger_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check format: old format is {"file": "hash"}, new is {"file": {"current_hash": ..., "history": [...]}}
        if data and isinstance(list(data.values())[0] if data.values() else None, str):
            # Old format detected - migrate it
            print(f"⚠️  Old format detected in {self.ledger_path}, migrating...")
            return self.migrate_to_history_format(data)

        return data

    def migrate_to_history_format(self, old_ledger: Dict[str, str]) -> Dict:
        """Convert old single-hash format to history format"""
        new_ledger = {}

        for filepath, hash_value in old_ledger.items():
            new_ledger[filepath] = {
                "current_hash": hash_value,
                "history": [
                    {
                        "hash": hash_value,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "author": "migration",
                        "commit": "initial",
                        "note": "Migrated from old ledger format"
                    }
                ]
            }

        return new_ledger

    def update_file(self, filepath: str, new_hash: str, author: str, commit: str, note: str = ""):
        """Record new hash for file"""
        if filepath not in self.ledger:
            self.ledger[filepath] = {
                "current_hash": new_hash,
                "history": []
            }

        # Add to history
        entry = {
            "hash": new_hash,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "author": author,
            "commit": commit
        }
        if note:
            entry["note"] = note

        self.ledger[filepath]["history"].append(entry)

        # Update current
        self.ledger[filepath]["current_hash"] = new_hash

    def get_current_hash(self, filepath: str) -> Optional[str]:
        """Get current hash for file"""
        if filepath not in self.ledger:
            return None
        return self.ledger[filepath].get("current_hash")

    def get_history(self, filepath: str) -> List[Dict]:
        """Get full change history for file"""
        if filepath not in self.ledger:
            return []
        return self.ledger[filepath].get("history", [])

    def detect_tampering(self, filepath: str, actual_hash: str) -> bool:
        """Check if file was tampered with (hash doesn't match history)"""
        if filepath not in self.ledger:
            return False

        expected = self.ledger[filepath]["current_hash"]
        return actual_hash != expected

    def save_ledger(self):
        """Save ledger to disk"""
        with open(self.ledger_path, 'w', encoding="utf-8") as f:
            json.dump(self.ledger, f, indent=2, sort_keys=True)
            f.write("\n")

    def generate_audit_report(self) -> str:
        """Generate human-readable audit report"""
        report = ["# Hash Ledger Audit Report", ""]
        report.append(f"Generated: {datetime.utcnow().isoformat()}Z")
        report.append(f"Total files tracked: {len(self.ledger)}")
        report.append("")

        for filepath in sorted(self.ledger.keys()):
            entry = self.ledger[filepath]
            history = entry.get("history", [])

            report.append(f"## {filepath}")
            report.append(f"")
            report.append(f"**Current hash:** `{entry['current_hash'][:16]}...`")
            report.append(f"**Total changes:** {len(history)}")
            report.append("")

            if history:
                report.append("### Change History")
                report.append("")
                # Show last 5 changes
                for change in history[-5:]:
                    timestamp = change.get('timestamp', 'unknown')
                    author = change.get('author', 'unknown')
                    commit = change.get('commit', 'unknown')[:8]
                    hash_short = change.get('hash', 'unknown')[:8]

                    report.append(f"- **{timestamp}** by `{author}`")
                    report.append(f"  - Commit: `{commit}`")
                    report.append(f"  - Hash: `{hash_short}...`")
                    if 'note' in change:
                        report.append(f"  - Note: {change['note']}")
                    report.append("")

                if len(history) > 5:
                    report.append(f"*...and {len(history) - 5} earlier change(s)*")
                    report.append("")

        return "\n".join(report)


def compute_hash(path: Path) -> str:
    """Compute SHA-256 hash of file"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_git_info() -> Tuple[str, str]:
    """Get current git author and commit"""
    try:
        author = subprocess.check_output(
            ["git", "config", "user.email"],
            text=True
        ).strip()
    except:
        author = "unknown@example.com"

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()
    except:
        commit = "unknown"

    return author, commit


def discover_tracked_files() -> set:
    """Discover files that should be tracked (same logic as verify_hashes.py)"""
    # Import from verify_hashes if available
    try:
        import verify_hashes
        return verify_hashes.discover_tracked_files()
    except:
        # Fallback: basic discovery
        files = set()
        for path in Path(".").rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json", ".py", ".yml", ".yaml"}:
                files.add(path.as_posix())
        return files


def verify_command(ledger: HistoricalHashLedger):
    """Verify all tracked files against ledger"""
    tracked = discover_tracked_files()
    errors = []

    print(f"🔍 Verifying {len(tracked)} tracked files...")
    print()

    for filepath in sorted(tracked):
        if filepath == "infra/github/hash_ledger_history.json":
            continue

        path = Path(filepath)
        if not path.exists():
            errors.append(f"❌ Missing file: {filepath}")
            continue

        actual_hash = compute_hash(path)
        expected_hash = ledger.get_current_hash(filepath)

        if expected_hash is None:
            errors.append(f"⚠️  Not in ledger: {filepath}")
        elif ledger.detect_tampering(filepath, actual_hash):
            errors.append(f"❌ Hash mismatch: {filepath}")
            errors.append(f"   Expected: {expected_hash}")
            errors.append(f"   Actual:   {actual_hash}")

    if errors:
        print("Verification failed:")
        for error in errors:
            print(f"  {error}")
        return False

    print("✅ All files verified successfully")
    return True


def update_command(ledger: HistoricalHashLedger, author: Optional[str], commit: Optional[str]):
    """Update ledger with current file hashes"""
    if author is None or commit is None:
        author, commit = get_git_info()

    tracked = discover_tracked_files()

    print(f"📝 Updating ledger for {len(tracked)} tracked files...")
    print(f"   Author: {author}")
    print(f"   Commit: {commit[:8]}")
    print()

    updated_count = 0
    for filepath in sorted(tracked):
        if filepath == "infra/github/hash_ledger_history.json":
            continue

        path = Path(filepath)
        if not path.exists():
            continue

        new_hash = compute_hash(path)
        old_hash = ledger.get_current_hash(filepath)

        if old_hash != new_hash:
            ledger.update_file(filepath, new_hash, author, commit)
            updated_count += 1
            print(f"  ✓ Updated: {filepath}")

    ledger.save_ledger()
    print()
    print(f"✅ Ledger updated ({updated_count} files changed)")
    print(f"   Saved to: {ledger.ledger_path}")


def audit_report_command(ledger: HistoricalHashLedger, output_path: Optional[Path]):
    """Generate audit report"""
    report = ledger.generate_audit_report()

    if output_path:
        with open(output_path, 'w', encoding="utf-8") as f:
            f.write(report)
        print(f"✅ Audit report saved to: {output_path}")
    else:
        print(report)


def migrate_command(ledger: HistoricalHashLedger):
    """Migrate old ledger format to new format"""
    if not OLD_LEDGER_PATH.exists():
        print(f"❌ Old ledger not found: {OLD_LEDGER_PATH}")
        return

    print(f"🔄 Migrating {OLD_LEDGER_PATH} to {LEDGER_PATH}...")

    with open(OLD_LEDGER_PATH, encoding="utf-8") as f:
        old_ledger = json.load(f)

    new_ledger = ledger.migrate_to_history_format(old_ledger)
    ledger.ledger = new_ledger
    ledger.save_ledger()

    print(f"✅ Migration complete!")
    print(f"   {len(new_ledger)} files migrated")
    print(f"   New ledger: {LEDGER_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Hash ledger with historical tracking"
    )
    parser.add_argument("--verify", action="store_true", help="Verify hashes against ledger")
    parser.add_argument("--update", action="store_true", help="Update ledger with current hashes")
    parser.add_argument("--audit-report", action="store_true", help="Generate audit report")
    parser.add_argument("--migrate", action="store_true", help="Migrate old ledger format")
    parser.add_argument("--author", help="Author email for update")
    parser.add_argument("--commit", help="Commit SHA for update")
    parser.add_argument("--output", type=Path, help="Output file for audit report")

    args = parser.parse_args()

    ledger = HistoricalHashLedger(LEDGER_PATH)

    if args.verify:
        success = verify_command(ledger)
        sys.exit(0 if success else 1)

    elif args.update:
        update_command(ledger, args.author, args.commit)

    elif args.audit_report:
        audit_report_command(ledger, args.output)

    elif args.migrate:
        migrate_command(ledger)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
