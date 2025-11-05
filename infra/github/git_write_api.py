#!/usr/bin/env python3
"""
Git Data API — Write Path for YARA Runtime

Create branches, commits, and PRs programmatically using GitHub's Git Data API.
This is the "write path" for YARA runtime to propose spec updates.

Usage:
    from infra.github.git_write_api import GitWriter

    writer = GitWriter(
        owner="ourobrancopedro-rgb",
        repo="alter-agro-yara-logica",
        token="<github_token>"
    )

    # Create branch + commit + PR in one call
    pr_url = writer.propose_spec_update(
        branch_name="yara/update-lsa-spec",
        files={
            "lsa/spec/LSA_PICC.md": "new content...",
            "infra/github/hash_ledger.json": "updated ledger..."
        },
        commit_message="feat(lsa): tighten PCB gate requirement",
        pr_title="YARA: Update LSA spec + ledger",
        pr_body="Updated specs + ledger; passes KPI gates."
    )
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails."""
    pass


class GitWriter:
    """
    GitHub Git Data API client for write operations.
    """

    def __init__(self, owner: str, repo: str, token: str):
        """
        Initialize Git writer.

        Args:
            owner: GitHub repository owner
            repo: Repository name
            token: GitHub API token (PAT or App token)
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _request(self, method: str, path: str, **kwargs) -> Dict:
        """
        Make authenticated GitHub API request.

        Args:
            method: HTTP method (GET, POST, PATCH)
            path: API path (e.g., "/repos/{owner}/{repo}/git/refs")
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON

        Raises:
            GitHubAPIError: If request fails
        """
        url = f"{self.api_base}{path}"
        kwargs.setdefault("headers", {}).update(self.headers)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"{method} {path} failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise GitHubAPIError(f"API request failed: {e}")

    def get_ref(self, ref: str) -> str:
        """
        Get SHA of a reference (branch, tag).

        Args:
            ref: Reference name (e.g., "heads/main", "tags/v1.0")

        Returns:
            Commit SHA
        """
        data = self._request("GET", f"/repos/{self.owner}/{self.repo}/git/ref/{ref}")
        return data["object"]["sha"]

    def create_branch(self, branch_name: str, base_ref: str = "heads/main") -> str:
        """
        Create a new branch from base ref.

        Args:
            branch_name: New branch name (without "refs/heads/")
            base_ref: Base reference to branch from

        Returns:
            Base commit SHA
        """
        base_sha = self.get_ref(base_ref)
        logger.info(f"Creating branch '{branch_name}' from {base_sha[:7]}")

        self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/refs",
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
        )

        return base_sha

    def create_blob(self, content: str, encoding: str = "utf-8") -> str:
        """
        Create a blob (file content).

        Args:
            content: File content (string)
            encoding: Content encoding

        Returns:
            Blob SHA
        """
        data = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/blobs",
            json={
                "content": content,
                "encoding": encoding
            }
        )
        return data["sha"]

    def create_tree(
        self,
        files: Dict[str, str],
        base_tree_sha: Optional[str] = None
    ) -> str:
        """
        Create a tree (directory structure) with file changes.

        Args:
            files: Dict mapping file paths to content
            base_tree_sha: Base tree to apply changes on top of

        Returns:
            Tree SHA
        """
        tree_entries = []

        for path, content in files.items():
            blob_sha = self.create_blob(content)
            tree_entries.append({
                "path": path,
                "mode": "100644",  # Regular file
                "type": "blob",
                "sha": blob_sha
            })
            logger.debug(f"Created blob for {path}: {blob_sha[:7]}")

        tree_data = {"tree": tree_entries}
        if base_tree_sha:
            tree_data["base_tree"] = base_tree_sha

        data = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/trees",
            json=tree_data
        )

        return data["sha"]

    def create_commit(
        self,
        message: str,
        tree_sha: str,
        parent_shas: List[str]
    ) -> str:
        """
        Create a commit.

        Args:
            message: Commit message
            tree_sha: Tree SHA (from create_tree)
            parent_shas: List of parent commit SHAs

        Returns:
            Commit SHA
        """
        data = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/git/commits",
            json={
                "message": message,
                "tree": tree_sha,
                "parents": parent_shas
            }
        )

        commit_sha = data["sha"]
        logger.info(f"Created commit: {commit_sha[:7]} - {message}")
        return commit_sha

    def update_ref(self, ref: str, sha: str, force: bool = False) -> None:
        """
        Update a reference (branch) to point to a commit.

        Args:
            ref: Reference name (e.g., "heads/feature-branch")
            sha: Commit SHA to point to
            force: Force update (allows non-fast-forward)
        """
        self._request(
            "PATCH",
            f"/repos/{self.owner}/{self.repo}/git/refs/{ref}",
            json={
                "sha": sha,
                "force": force
            }
        )
        logger.info(f"Updated {ref} → {sha[:7]}")

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str = "main",
        body: str = ""
    ) -> Dict:
        """
        Create a pull request.

        Args:
            title: PR title
            head: Head branch name (without refs/heads/)
            base: Base branch name
            body: PR description

        Returns:
            PR data dict with 'number' and 'html_url'
        """
        data = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
        )

        logger.info(f"Created PR #{data['number']}: {data['html_url']}")
        return data

    def propose_spec_update(
        self,
        branch_name: str,
        files: Dict[str, str],
        commit_message: str,
        pr_title: str,
        pr_body: str,
        base_ref: str = "heads/main"
    ) -> str:
        """
        Full workflow: create branch, commit files, open PR.

        Args:
            branch_name: New branch name
            files: Dict of {file_path: content}
            commit_message: Commit message
            pr_title: Pull request title
            pr_body: Pull request description
            base_ref: Base branch to branch from

        Returns:
            PR URL

        Example:
            pr_url = writer.propose_spec_update(
                branch_name="yara/update-lsa-spec-2025-11-05",
                files={
                    "lsa/spec/LSA_PICC.md": new_lsa_content,
                    "infra/github/hash_ledger.json": updated_ledger
                },
                commit_message="feat(lsa): tighten PCB gate requirement",
                pr_title="YARA: Update LSA spec + ledger",
                pr_body="Updated specs + ledger; passes KPI gates."
            )
        """
        logger.info(f"Proposing spec update via branch: {branch_name}")

        # 1. Create branch from main
        base_sha = self.create_branch(branch_name, base_ref=base_ref)

        # 2. Get base tree
        base_commit_data = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/git/commits/{base_sha}"
        )
        base_tree_sha = base_commit_data["tree"]["sha"]

        # 3. Create tree with file changes
        tree_sha = self.create_tree(files, base_tree_sha=base_tree_sha)

        # 4. Create commit
        commit_sha = self.create_commit(
            message=commit_message,
            tree_sha=tree_sha,
            parent_shas=[base_sha]
        )

        # 5. Move branch ref to new commit
        self.update_ref(f"heads/{branch_name}", commit_sha)

        # 6. Create pull request
        pr_data = self.create_pull_request(
            title=pr_title,
            head=branch_name,
            base="main",
            body=pr_body
        )

        return pr_data["html_url"]


def update_hash_ledger(
    ledger_path: str,
    updated_files: Dict[str, str]
) -> str:
    """
    Update hash ledger with new file hashes.

    Args:
        ledger_path: Path to existing hash_ledger.json
        updated_files: Dict of {file_path: content}

    Returns:
        Updated ledger JSON string
    """
    from pathlib import Path

    # Load existing ledger
    ledger = json.loads(Path(ledger_path).read_text())

    # Update with new hashes
    for file_path, content in updated_files.items():
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        ledger[file_path] = sha256
        logger.info(f"Ledger updated: {file_path} → {sha256[:16]}...")

    return json.dumps(ledger, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python git_write_api.py <token> [branch_name]\n"
            "Example test: creates a branch and proposes a minimal change"
        )
        sys.exit(1)

    token = sys.argv[1]
    branch_name = sys.argv[2] if len(sys.argv) > 2 else "yara/test-api-write"

    logging.basicConfig(level=logging.INFO)

    writer = GitWriter(
        owner="ourobrancopedro-rgb",
        repo="alter-agro-yara-logica",
        token=token
    )

    # Example: Update README with timestamp
    from datetime import datetime

    test_content = f"<!-- Test update: {datetime.utcnow().isoformat()} -->\n"

    try:
        pr_url = writer.propose_spec_update(
            branch_name=branch_name,
            files={"README.md": test_content},
            commit_message="test: API write path validation",
            pr_title="[TEST] API Write Path Validation",
            pr_body="Automated test of Git Data API write path.\n\n**Do not merge.**"
        )

        print(f"\n✓ PR created: {pr_url}")

    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        sys.exit(1)
