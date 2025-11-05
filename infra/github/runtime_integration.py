#!/usr/bin/env python3
"""
YARA Runtime Integration Library
Fetch specification files from GitHub at pinned commits with SHA-256 verification.

Usage:
    from infra.github.runtime_integration import fetch_file, load_spec_bundle

    # Fetch single file
    content, sha256 = fetch_file(
        owner="ourobrancopedro-rgb",
        repo="alter-agro-yara-logica",
        path="lsa/spec/LSA_PICC.md",
        commit_sha="abc123...",
        token="<github_token>"
    )

    # Load entire SpecBundle
    bundle = load_spec_bundle("path/to/spec_bundle.json", token="<github_token>")
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class SpecIntegrityError(Exception):
    """Raised when specification integrity verification fails."""
    pass


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails."""
    pass


def fetch_file(
    owner: str,
    repo: str,
    path: str,
    commit_sha: str,
    token: str,
    timeout: int = 30
) -> Tuple[bytes, str]:
    """
    Fetch a file from GitHub at exact commit SHA with integrity verification.

    Args:
        owner: GitHub repository owner
        repo: Repository name
        path: File path within repository
        commit_sha: Exact commit SHA to fetch from
        token: GitHub API token (PAT or App token)
        timeout: Request timeout in seconds

    Returns:
        Tuple of (file_content, sha256_hash)

    Raises:
        GitHubAPIError: If API request fails
        SpecIntegrityError: If content cannot be verified
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github.raw",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    params = {"ref": commit_sha}

    logger.info(f"Fetching {path} @ {commit_sha[:7]}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Failed to fetch {path}: {e}")

    content = response.content
    sha256 = hashlib.sha256(content).hexdigest()

    logger.debug(f"Fetched {len(content)} bytes, SHA-256: {sha256}")

    return content, sha256


def verify_against_ledger(
    path: str,
    content_sha256: str,
    ledger_path: str = "infra/github/hash_ledger.json"
) -> bool:
    """
    Verify file SHA-256 against hash ledger.

    Args:
        path: File path to verify
        content_sha256: Calculated SHA-256 of content
        ledger_path: Path to hash ledger JSON

    Returns:
        True if hash matches ledger, False otherwise

    Raises:
        FileNotFoundError: If ledger doesn't exist
        SpecIntegrityError: If hash mismatch detected
    """
    ledger = json.loads(Path(ledger_path).read_text())

    if path not in ledger:
        logger.warning(f"Path {path} not found in ledger")
        return False

    ledger_hash = ledger[path]

    if content_sha256 != ledger_hash:
        raise SpecIntegrityError(
            f"Hash mismatch for {path}:\n"
            f"  Expected (ledger): {ledger_hash}\n"
            f"  Got (content):     {content_sha256}"
        )

    logger.info(f"✓ Hash verified for {path}")
    return True


def load_spec_bundle(
    bundle_path: str,
    token: str,
    verify_ledger: bool = True,
    cache_dir: Optional[str] = None
) -> Dict:
    """
    Load and verify a complete SpecBundle.

    Args:
        bundle_path: Path to SpecBundle JSON file
        token: GitHub API token
        verify_ledger: Whether to verify against hash ledger
        cache_dir: Optional directory to cache downloaded files

    Returns:
        Dict with loaded and verified spec files

    Example SpecBundle format:
        {
            "id": "lsa-spec-v2.1",
            "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
            "commit_sha": "abc123...",
            "files": [
                {"path": "lsa/spec/LSA_PICC.md", "sha256": "..."},
                {"path": "rag/spec/RAG_POLICY.md", "sha256": "..."}
            ],
            "sealed_at": "2025-11-04T21:10:00-03:00"
        }
    """
    bundle = json.loads(Path(bundle_path).read_text())

    owner, repo = bundle["repo"].split("/")
    commit_sha = bundle["commit_sha"]

    logger.info(f"Loading SpecBundle: {bundle['id']} @ {commit_sha[:7]}")

    results = {
        "bundle_id": bundle["id"],
        "commit_sha": commit_sha,
        "sealed_at": bundle["sealed_at"],
        "files": {}
    }

    if cache_dir:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

    for file_spec in bundle["files"]:
        path = file_spec["path"]
        expected_sha256 = file_spec["sha256"]

        # Check cache first
        if cache_dir:
            cached_file = cache_path / expected_sha256
            if cached_file.exists():
                content = cached_file.read_bytes()
                calculated_sha256 = hashlib.sha256(content).hexdigest()

                if calculated_sha256 == expected_sha256:
                    logger.info(f"✓ Cache hit for {path}")
                    results["files"][path] = {
                        "content": content,
                        "sha256": calculated_sha256,
                        "source": "cache"
                    }
                    continue

        # Fetch from GitHub
        content, calculated_sha256 = fetch_file(
            owner=owner,
            repo=repo,
            path=path,
            commit_sha=commit_sha,
            token=token
        )

        # Verify against SpecBundle declaration
        if calculated_sha256 != expected_sha256:
            raise SpecIntegrityError(
                f"SpecBundle hash mismatch for {path}:\n"
                f"  Expected (bundle): {expected_sha256}\n"
                f"  Got (fetched):     {calculated_sha256}"
            )

        # Optionally verify against ledger
        if verify_ledger:
            verify_against_ledger(path, calculated_sha256)

        # Cache if enabled
        if cache_dir:
            cached_file = cache_path / expected_sha256
            cached_file.write_bytes(content)
            logger.debug(f"Cached {path} as {expected_sha256}")

        results["files"][path] = {
            "content": content,
            "sha256": calculated_sha256,
            "source": "github"
        }

    logger.info(f"✓ SpecBundle loaded: {len(results['files'])} files verified")
    return results


def generate_provenance_stamp(
    spec_bundle: Dict,
    additional_metadata: Optional[Dict] = None
) -> Dict:
    """
    Generate provenance stamp for runtime inference logging.

    Args:
        spec_bundle: Loaded SpecBundle dict from load_spec_bundle()
        additional_metadata: Optional extra metadata to include

    Returns:
        Provenance stamp dict for logging

    Example output:
        {
            "timestamp": "2025-11-05T10:15:00Z",
            "spec_repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
            "commit_sha": "abc123...",
            "bundle_id": "lsa-spec-v2.1",
            "files": {
                "lsa/spec/LSA_PICC.md": "sha256:7b41...",
                "rag/spec/RAG_POLICY.md": "sha256:1f0c..."
            }
        }
    """
    stamp = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "spec_repo": f"ourobrancopedro-rgb/alter-agro-yara-logica",
        "commit_sha": spec_bundle["commit_sha"],
        "bundle_id": spec_bundle["bundle_id"],
        "files": {
            path: f"sha256:{info['sha256']}"
            for path, info in spec_bundle["files"].items()
        }
    }

    if additional_metadata:
        stamp["metadata"] = additional_metadata

    return stamp


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python runtime_integration.py <spec_bundle.json> [github_token]")
        sys.exit(1)

    bundle_path = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else None

    if not token:
        print("Warning: No GitHub token provided, will fail if rate limited")

    logging.basicConfig(level=logging.INFO)

    try:
        bundle = load_spec_bundle(
            bundle_path=bundle_path,
            token=token,
            verify_ledger=True,
            cache_dir=".spec_cache"
        )

        stamp = generate_provenance_stamp(bundle)

        print("\n✓ SpecBundle loaded successfully")
        print(json.dumps(stamp, indent=2))

    except Exception as e:
        logger.error(f"Failed to load SpecBundle: {e}")
        sys.exit(1)
