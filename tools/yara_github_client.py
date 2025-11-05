# tools/yara_github_client.py
import os
import json
import hashlib
import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import requests


@dataclass
class RepoRef:
    owner: str
    repo: str
    ref: str  # commit SHA or branch


@dataclass
class SpecFile:
    path: str
    sha256: Optional[str] = None


class YaraGitHubClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "YARA-Logica-Client"
        })

    # ---------- helpers ----------
    @staticmethod
    def _sha256_bytes(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    @staticmethod
    def _now_iso() -> str:
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _get(self, url: str, **kwargs) -> requests.Response:
        r = self.session.get(url, **kwargs); r.raise_for_status(); return r

    def _post(self, url: str, json=None) -> requests.Response:
        r = self.session.post(url, json=json); r.raise_for_status(); return r

    def _patch(self, url: str, json=None) -> requests.Response:
        r = self.session.patch(url, json=json); r.raise_for_status(); return r

    # ---------- READ ----------
    def fetch_raw_file(self, ref: RepoRef, path: str) -> bytes:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/contents/{path}"
        r = self._get(url, params={"ref": ref.ref}, headers={"Accept": "application/vnd.github.raw"})
        return r.content

    def fetch_ledger_json(self, ref: RepoRef, ledger_path: str = "infra/github/hash_ledger.json") -> list:
        raw = self.fetch_raw_file(ref, ledger_path)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("Ledger must be a list.")
        return data

    def verify_against_ledger(self, ref: RepoRef, files: List[SpecFile], ledger_path: str = "infra/github/hash_ledger.json") -> Tuple[bool, Dict[str, str]]:
        ledger = self.fetch_ledger_json(ref, ledger_path=ledger_path)
        by_path = {e["path"]: e for e in ledger if "path" in e and "sha256" in e}
        status, ok = {}, True
        for f in files:
            content = self.fetch_raw_file(ref, f.path)
            calc = self._sha256_bytes(content)
            if f.sha256 and f.sha256 != calc:
                ok = False; status[f.path] = f"Mismatch local spec sha256={f.sha256} calc={calc}"; continue
            entry = by_path.get(f.path)
            if not entry:
                ok = False; status[f.path] = "Missing in ledger"; continue
            if entry["sha256"] != calc:
                ok = False; status[f.path] = f"Ledger {entry['sha256']} != calc {calc}"; continue
            status[f.path] = "OK"
        return ok, status

    # ---------- WRITE (PR-only) ----------
    def get_ref_sha(self, ref: RepoRef) -> str:
        url = f"{self.base_url}/repos/{ref.owner}/{ref.repo}/git/ref/heads/{ref.ref}"
        return self._get(url).json()["object"]["sha"]

    def create_branch(self, owner: str, repo: str, base_sha: str, branch: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
        return self._post(url, json={"ref": f"refs/heads/{branch}", "sha": base_sha}).json()["ref"]

    def create_blob(self, owner: str, repo: str, content_utf8: str) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs"
        return self._post(url, json={"content": content_utf8, "encoding": "utf-8"}).json()["sha"]

    def create_tree(self, owner: str, repo: str, base_tree: str, path_to_blob_sha: Dict[str, str]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        tree = [{"path": p, "mode": "100644", "type": "blob", "sha": bsha} for p, bsha in path_to_blob_sha.items()]
        return self._post(url, json={"base_tree": base_tree, "tree": tree}).json()["sha"]

    def get_commit(self, owner: str, repo: str, sha: str) -> Dict:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{sha}"
        return self._get(url).json()

    def create_commit(self, owner: str, repo: str, message: str, tree_sha: str, parents: List[str]) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        return self._post(url, json={"message": message, "tree": tree_sha, "parents": parents}).json()["sha"]

    def update_ref(self, owner: str, repo: str, branch: str, new_sha: str, force: bool = False):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        self._patch(url, json={"sha": new_sha, "force": force})

    def open_pr(self, owner: str, repo: str, head_branch: str, base_branch: str, title: str, body: str) -> int:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        return self._post(url, json={"title": title, "head": head_branch, "base": base_branch, "body": body}).json()["number"]

    # ---------- AUTO-LEDGER PR ----------
    @staticmethod
    def calc_sha256s_local(files_to_write: dict) -> dict:
        out = {}
        for path, content in files_to_write.items():
            b = content.encode("utf-8")
            out[path] = {"sha256": hashlib.sha256(b).hexdigest(), "size": len(b)}
        return out

    @staticmethod
    def merge_ledger(ledger: list, new_entries: list) -> list:
        by_path = {e["path"]: e for e in ledger if "path" in e}
        for e in new_entries:
            by_path[e["path"]] = e
        merged = list(by_path.values())
        merged.sort(key=lambda x: x["path"])
        return merged

    def propose_changes_via_pr(self, base: RepoRef, new_branch: str, files_to_write: Dict[str, str], commit_message: str, pr_title: str, pr_body: str) -> int:
        base_sha = self.get_ref_sha(RepoRef(base.owner, base.repo, base.ref))
        base_commit = self.get_commit(base.owner, base.repo, base_sha)
        base_tree = base_commit["tree"]["sha"]
        self.create_branch(base.owner, base.repo, base_sha, new_branch)

        path_to_blob_sha = {p: self.create_blob(base.owner, base.repo, c) for p, c in files_to_write.items()}
        tree_sha = self.create_tree(base.owner, base.repo, base_tree, path_to_blob_sha)
        new_commit_sha = self.create_commit(base.owner, base.repo, commit_message, tree_sha, parents=[base_sha])
        self.update_ref(base.owner, base.repo, new_branch, new_commit_sha, force=False)
        return self.open_pr(base.owner, base.repo, head_branch=new_branch, base_branch=base.ref, title=pr_title, body=pr_body)

    def propose_changes_via_pr_with_ledger(self, base: RepoRef, new_branch: str, files_to_write: dict, ledger_path: str, commit_message: str, pr_title: str, pr_body: str) -> int:
        base_sha = self.get_ref_sha(RepoRef(base.owner, base.repo, base.ref))
        base_commit = self.get_commit(base.owner, base.repo, base_sha)
        base_tree = base_commit["tree"]["sha"]
        self.create_branch(base.owner, base.repo, base_sha, new_branch)

        calc = self.calc_sha256s_local(files_to_write)
        now = self._now_iso()
        new_entries = [{"path": p, "sha256": m["sha256"], "size": m["size"], "commit_sha": "PENDING", "created_at": now} for p, m in calc.items()]

        current_ledger = self.fetch_ledger_json(base, ledger_path=ledger_path)
        merged_ledger = self.merge_ledger(current_ledger, new_entries)

        path_to_blob_sha = {p: self.create_blob(base.owner, base.repo, c) for p, c in files_to_write.items()}
        ledger_blob_sha = self.create_blob(base.owner, base.repo, json.dumps(merged_ledger, ensure_ascii=False, indent=2))
        path_to_blob_sha[ledger_path] = ledger_blob_sha

        tree_sha = self.create_tree(base.owner, base.repo, base_tree, path_to_blob_sha)
        first_commit_sha = self.create_commit(base.owner, base.repo, commit_message, tree_sha, parents=[base_sha])

        patched = []
        for e in merged_ledger:
            e2 = dict(e)
            if e2.get("commit_sha") == "PENDING" and e2["path"] in files_to_write:
                e2["commit_sha"] = first_commit_sha
            patched.append(e2)

        patched_blob = self.create_blob(base.owner, base.repo, json.dumps(patched, ensure_ascii=False, indent=2))
        tree2_sha = self.create_tree(base.owner, base.repo, tree_sha, {ledger_path: patched_blob})
        second_commit_sha = self.create_commit(base.owner, base.repo, "chore(ledger): fill commit_sha", tree2_sha, parents=[first_commit_sha])

        self.update_ref(base.owner, base.repo, new_branch, second_commit_sha, force=False)
        return self.open_pr(base.owner, base.repo, head_branch=new_branch, base_branch=base.ref, title=pr_title, body=pr_body)
