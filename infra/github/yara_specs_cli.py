#!/usr/bin/env python3
"""
YARA Specs CLI — Developer-friendly interface for spec repository operations

Commands:
    yara-specs pull      - Fetch specs at pinned commit
    yara-specs propose   - Propose spec changes via PR
    yara-specs promote   - Promote pin to new commit
    yara-specs verify    - Verify specs against ledger
    yara-specs bundle    - Generate SpecBundle

Usage:
    # Pull specs at pinned commit
    yara-specs pull --pin abc123 --files lsa/spec/LSA_PICC.md --output ./specs

    # Propose update
    yara-specs propose --branch yara/update-lsa --edit lsa/spec/LSA_PICC.md

    # Promote pin
    yara-specs promote --commit def456 --environment production

    # Verify integrity
    yara-specs verify --bundle spec_bundle.json

    # Generate bundle
    yara-specs bundle --id lsa-spec-v2.1 --output bundle.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Import our modules
try:
    from infra.github.runtime_integration import (
        fetch_file,
        load_spec_bundle,
        generate_provenance_stamp
    )
    from infra.github.generate_spec_bundle import generate_spec_bundle
    from infra.github.git_write_api import GitWriter, update_hash_ledger
except ImportError:
    # Fallback for running from different directory
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from infra.github.runtime_integration import (
        fetch_file,
        load_spec_bundle,
        generate_provenance_stamp
    )
    from infra.github.generate_spec_bundle import generate_spec_bundle
    from infra.github.git_write_api import GitWriter, update_hash_ledger

logger = logging.getLogger(__name__)


class Config:
    """Configuration management for CLI."""

    def __init__(self):
        self.config_path = Path.home() / ".yara-specs" / "config.json"
        self.config = self._load()

    def _load(self) -> dict:
        """Load config from disk."""
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {
            "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
            "current_pin": None,
            "github_token": os.environ.get("GITHUB_TOKEN")
        }

    def save(self):
        """Save config to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.config, indent=2))
        logger.info(f"Config saved: {self.config_path}")

    def get(self, key: str, default=None):
        """Get config value."""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set config value."""
        self.config[key] = value


def cmd_pull(args):
    """
    Pull specs at pinned commit.

    Example:
        yara-specs pull --pin abc123 --files lsa/spec/LSA_PICC.md rag/spec/RAG_POLICY.md
    """
    config = Config()
    token = args.token or config.get("github_token")

    if not token:
        logger.error("GitHub token required. Set via --token or GITHUB_TOKEN env var")
        sys.exit(1)

    owner, repo = config.get("repo").split("/")
    pin_commit = args.pin or config.get("current_pin")

    if not pin_commit:
        logger.error("Commit pin required. Use --pin or set default with 'promote'")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Pulling specs @ {pin_commit[:7]}")

    for file_path in args.files:
        content, sha256 = fetch_file(
            owner=owner,
            repo=repo,
            path=file_path,
            commit_sha=pin_commit,
            token=token
        )

        output_file = output_dir / Path(file_path).name
        output_file.write_bytes(content)

        logger.info(f"✓ {file_path} → {output_file} (SHA-256: {sha256[:16]}...)")

    print(f"\n✓ Pulled {len(args.files)} file(s) to {output_dir}")


def cmd_propose(args):
    """
    Propose spec changes via PR.

    Example:
        yara-specs propose --branch yara/update-lsa \\
            --edit lsa/spec/LSA_PICC.md \\
            --message "feat(lsa): tighten PCB gate"
    """
    config = Config()
    token = args.token or config.get("github_token")

    if not token:
        logger.error("GitHub token required")
        sys.exit(1)

    owner, repo = config.get("repo").split("/")
    writer = GitWriter(owner=owner, repo=repo, token=token)

    # Read edited file
    edited_file = Path(args.edit)
    if not edited_file.exists():
        logger.error(f"File not found: {edited_file}")
        sys.exit(1)

    new_content = edited_file.read_text()

    # Update hash ledger
    ledger_content = update_hash_ledger(
        ledger_path="infra/github/hash_ledger.json",
        updated_files={args.edit: new_content}
    )

    # Create PR
    pr_url = writer.propose_spec_update(
        branch_name=args.branch,
        files={
            args.edit: new_content,
            "infra/github/hash_ledger.json": ledger_content
        },
        commit_message=args.message,
        pr_title=f"YARA: {args.message}",
        pr_body=(
            f"Automated spec update proposed by YARA runtime.\n\n"
            f"**Changed files:**\n"
            f"- {args.edit}\n"
            f"- infra/github/hash_ledger.json\n\n"
            f"**Note:** Review changes and ensure CI passes before merging."
        )
    )

    print(f"\n✓ PR created: {pr_url}")


def cmd_promote(args):
    """
    Promote pin to new commit.

    Example:
        yara-specs promote --commit def456 --environment production
    """
    config = Config()

    if args.environment == "production":
        config.set("current_pin", args.commit)
        config.save()
        logger.info(f"Production pin updated: {args.commit[:7]}")
    elif args.environment == "staging":
        config.set("staging_pin", args.commit)
        config.save()
        logger.info(f"Staging pin updated: {args.commit[:7]}")

    print(f"✓ Pin promoted to {args.environment}: {args.commit}")


def cmd_verify(args):
    """
    Verify specs against hash ledger.

    Example:
        yara-specs verify --bundle spec_bundle.json
    """
    config = Config()
    token = args.token or config.get("github_token")

    if not token:
        logger.error("GitHub token required")
        sys.exit(1)

    try:
        bundle = load_spec_bundle(
            bundle_path=args.bundle,
            token=token,
            verify_ledger=True,
            cache_dir=args.cache_dir
        )

        stamp = generate_provenance_stamp(bundle)

        print("\n✓ Verification successful")
        print(json.dumps(stamp, indent=2))

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)


def cmd_bundle(args):
    """
    Generate SpecBundle.

    Example:
        yara-specs bundle --id lsa-spec-v2.1 --auto --output bundle.json
    """
    from infra.github.generate_spec_bundle import (
        generate_spec_bundle as gen_bundle,
        auto_discover_spec_files,
        get_current_commit
    )

    commit_sha = args.commit or get_current_commit()
    files = args.files or auto_discover_spec_files()

    bundle = gen_bundle(
        bundle_id=args.id,
        commit_sha=commit_sha,
        files=files,
        verify_ledger=not args.no_verify
    )

    Path(args.output).write_text(json.dumps(bundle, indent=2) + "\n")

    print(f"\n✓ SpecBundle generated: {args.output}")
    print(f"  ID:     {bundle['id']}")
    print(f"  Commit: {bundle['commit_sha'][:16]}...")
    print(f"  Files:  {len(bundle['files'])}")


def cmd_config(args):
    """
    Manage configuration.

    Example:
        yara-specs config --set current_pin abc123
        yara-specs config --get current_pin
        yara-specs config --list
    """
    config = Config()

    if args.list:
        print(json.dumps(config.config, indent=2))

    elif args.get:
        value = config.get(args.get)
        if value:
            print(value)
        else:
            logger.warning(f"Config key not found: {args.get}")

    elif args.set and args.value:
        config.set(args.set, args.value)
        config.save()
        print(f"✓ Set {args.set} = {args.value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="yara-specs",
        description="YARA Specs CLI — Manage spec repository operations"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )
    parser.add_argument(
        "--token",
        help="GitHub API token (or set GITHUB_TOKEN env var)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Fetch specs at pinned commit")
    pull_parser.add_argument("--pin", help="Commit SHA to fetch")
    pull_parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="File paths to fetch"
    )
    pull_parser.add_argument(
        "--output",
        default="./specs",
        help="Output directory"
    )

    # Propose command
    propose_parser = subparsers.add_parser("propose", help="Propose spec changes")
    propose_parser.add_argument(
        "--branch",
        required=True,
        help="Branch name"
    )
    propose_parser.add_argument(
        "--edit",
        required=True,
        help="File to edit"
    )
    propose_parser.add_argument(
        "--message",
        required=True,
        help="Commit message"
    )

    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote pin")
    promote_parser.add_argument(
        "--commit",
        required=True,
        help="Commit SHA"
    )
    promote_parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        default="staging",
        help="Target environment"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify specs")
    verify_parser.add_argument(
        "--bundle",
        required=True,
        help="SpecBundle JSON path"
    )
    verify_parser.add_argument(
        "--cache-dir",
        help="Cache directory"
    )

    # Bundle command
    bundle_parser = subparsers.add_parser("bundle", help="Generate SpecBundle")
    bundle_parser.add_argument(
        "--id",
        required=True,
        help="Bundle ID"
    )
    bundle_parser.add_argument(
        "--commit",
        help="Commit SHA (defaults to HEAD)"
    )
    bundle_parser.add_argument(
        "--files",
        nargs="*",
        help="File paths (or use --auto)"
    )
    bundle_parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-discover files"
    )
    bundle_parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path"
    )
    bundle_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip ledger verification"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--list", action="store_true", help="List all config")
    config_parser.add_argument("--get", help="Get config value")
    config_parser.add_argument("--set", help="Set config key")
    config_parser.add_argument("--value", help="Config value (with --set)")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Route to command handlers
    commands = {
        "pull": cmd_pull,
        "propose": cmd_propose,
        "promote": cmd_promote,
        "verify": cmd_verify,
        "bundle": cmd_bundle,
        "config": cmd_config
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
