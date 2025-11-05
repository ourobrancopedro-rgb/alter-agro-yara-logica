#!/usr/bin/env python3
"""
SpecBundle Generator
Creates a SpecBundle JSON file for YARA runtime pinning.

Usage:
    python infra/github/generate_spec_bundle.py \\
        --id "lsa-spec-v2.1" \\
        --commit abc123... \\
        --files lsa/spec/LSA_PICC.md rag/spec/RAG_POLICY.md \\
        --output spec_bundle.json

    # Or generate from current HEAD
    python infra/github/generate_spec_bundle.py \\
        --id "lsa-spec-v2.1" \\
        --auto \\
        --output spec_bundle.json
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict


def get_current_commit() -> str:
    """Get current HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get current commit: {e}")


def calculate_file_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return Path(file_path).stat().st_size


def verify_files_exist(files: List[str]) -> None:
    """Verify that all specified files exist."""
    missing = [f for f in files if not Path(f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Files not found:\n" + "\n".join(f"  - {f}" for f in missing)
        )


def load_hash_ledger(ledger_path: str = "infra/github/hash_ledger.json") -> Dict[str, str]:
    """Load hash ledger for verification."""
    if not Path(ledger_path).exists():
        print(f"Warning: Hash ledger not found at {ledger_path}", file=sys.stderr)
        return {}

    return json.loads(Path(ledger_path).read_text())


def generate_spec_bundle(
    bundle_id: str,
    commit_sha: str,
    files: List[str],
    repo: str = "ourobrancopedro-rgb/alter-agro-yara-logica",
    verify_ledger: bool = True,
    include_metadata: bool = True
) -> Dict:
    """
    Generate a SpecBundle specification.

    Args:
        bundle_id: Unique identifier for this bundle (e.g., "lsa-spec-v2.1")
        commit_sha: Git commit SHA to pin
        files: List of file paths to include
        repo: GitHub repository in format "owner/repo"
        verify_ledger: Whether to verify files against hash ledger
        include_metadata: Whether to include size and created_at metadata

    Returns:
        SpecBundle dict
    """
    verify_files_exist(files)

    ledger = load_hash_ledger() if verify_ledger else {}

    file_specs = []
    for file_path in files:
        sha256 = calculate_file_sha256(file_path)

        # Verify against ledger if enabled
        if verify_ledger and file_path in ledger:
            ledger_hash = ledger[file_path]
            if sha256 != ledger_hash:
                raise ValueError(
                    f"Hash mismatch for {file_path}:\n"
                    f"  Calculated: {sha256}\n"
                    f"  Ledger:     {ledger_hash}"
                )
            print(f"✓ {file_path} verified against ledger")
        elif verify_ledger:
            print(f"⚠ {file_path} not in ledger", file=sys.stderr)

        spec = {
            "path": file_path,
            "sha256": sha256
        }

        if include_metadata:
            spec["size"] = get_file_size(file_path)

        file_specs.append(spec)
        print(f"Added {file_path} (SHA-256: {sha256[:16]}...)")

    bundle = {
        "id": bundle_id,
        "repo": repo,
        "commit_sha": commit_sha,
        "files": file_specs,
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }

    return bundle


def auto_discover_spec_files() -> List[str]:
    """
    Auto-discover specification files from standard paths.

    Returns:
        List of discovered file paths
    """
    patterns = [
        "lsa/spec/*.md",
        "rag/spec/*.md",
        "docs/*.md"
    ]

    files = []
    for pattern in patterns:
        files.extend(str(p) for p in Path(".").glob(pattern))

    # Exclude certain files
    exclude = {"README.md"}
    files = [f for f in files if Path(f).name not in exclude]

    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description="Generate SpecBundle for YARA runtime pinning"
    )
    parser.add_argument(
        "--id",
        required=True,
        help="Bundle ID (e.g., 'lsa-spec-v2.1')"
    )
    parser.add_argument(
        "--commit",
        help="Git commit SHA (defaults to current HEAD)"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to include (space-separated)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-discover spec files from standard paths"
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--repo",
        default="ourobrancopedro-rgb/alter-agro-yara-logica",
        help="GitHub repository (owner/repo)"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip hash ledger verification"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Exclude size and timestamp metadata"
    )

    args = parser.parse_args()

    # Determine commit SHA
    commit_sha = args.commit or get_current_commit()
    print(f"Using commit: {commit_sha}")

    # Determine files
    if args.auto:
        files = auto_discover_spec_files()
        print(f"Auto-discovered {len(files)} files")
    elif args.files:
        files = args.files
    else:
        parser.error("Either --files or --auto must be specified")

    if not files:
        print("Error: No files to bundle", file=sys.stderr)
        sys.exit(1)

    # Generate bundle
    try:
        bundle = generate_spec_bundle(
            bundle_id=args.id,
            commit_sha=commit_sha,
            files=files,
            repo=args.repo,
            verify_ledger=not args.no_verify,
            include_metadata=not args.no_metadata
        )

        # Write output
        output_path = Path(args.output)
        output_path.write_text(json.dumps(bundle, indent=2) + "\n")

        print(f"\n✓ SpecBundle generated: {output_path}")
        print(f"  ID:     {bundle['id']}")
        print(f"  Commit: {bundle['commit_sha'][:16]}...")
        print(f"  Files:  {len(bundle['files'])}")

    except Exception as e:
        print(f"Error generating SpecBundle: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
