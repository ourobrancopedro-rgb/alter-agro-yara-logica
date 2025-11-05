#!/usr/bin/env python3
# tools/yara_specs_cli.py

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from yara_github_client import YaraGitHubClient, RepoRef, SpecFile  # same dir (tools/)


def _token_or_die():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        print("ERROR: GITHUB_TOKEN not set. Provide a GitHub App installation token or read/write PAT.", file=sys.stderr)
        sys.exit(2)
    return tok


def cmd_pull(args):
    token = _token_or_die()
    client = YaraGitHubClient(token)
    ref = RepoRef(args.owner, args.repo, args.ref)

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    pulled = []
    for relpath in args.files:
        content = client.fetch_raw_file(ref, relpath)
        sha256 = client._sha256_bytes(content)
        target = outdir / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        pulled.append({"path": relpath, "sha256": sha256, "bytes": len(content)})

    print(json.dumps({"repo": f"{args.owner}/{args.repo}", "ref": args.ref, "pulled": pulled}, indent=2))


def cmd_verify(args):
    token = _token_or_die()
    client = YaraGitHubClient(token)
    ref = RepoRef(args.owner, args.repo, args.ref)
    files = [SpecFile(p) for p in args.files]
    ok, details = client.verify_against_ledger(ref, files, ledger_path=args.ledger_path)
    print(json.dumps({"ok": ok, "details": details}, indent=2))
    if not ok:
        sys.exit(1)


def cmd_propose(args):
    token = _token_or_die()
    client = YaraGitHubClient(token)
    base = RepoRef(args.owner, args.repo, args.base)
    branch = args.branch or f"feature/yara-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    files_to_write = {}
    for mapping in args.add or []:
        try:
            repo_path, local_path = mapping.split("=", 1)
        except ValueError:
            print(f"Bad --add mapping (use repo_path=local_path): {mapping}", file=sys.stderr)
            sys.exit(2)
        files_to_write[repo_path] = Path(local_path).read_text(encoding="utf-8")

    pr = client.propose_changes_via_pr(
        base=base,
        new_branch=branch,
        files_to_write=files_to_write,
        commit_message=args.message,
        pr_title=args.title,
        pr_body=args.body or ""
    )
    print(json.dumps({"pr_number": pr, "branch": branch}, indent=2))


def cmd_propose_auto(args):
    token = _token_or_die()
    client = YaraGitHubClient(token)
    base = RepoRef(args.owner, args.repo, args.base)
    branch = args.branch or f"feature/yara-auto-ledger-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    files_to_write = {}
    for mapping in args.add or []:
        try:
            repo_path, local_path = mapping.split("=", 1)
        except ValueError:
            print(f"Bad --add mapping (use repo_path=local_path): {mapping}", file=sys.stderr)
            sys.exit(2)
        files_to_write[repo_path] = Path(local_path).read_text(encoding="utf-8")

    pr = client.propose_changes_via_pr_with_ledger(
        base=base,
        new_branch=branch,
        files_to_write=files_to_write,
        ledger_path=args.ledger_path,
        commit_message=args.message,
        pr_title=args.title,
        pr_body=args.body or ""
    )
    print(json.dumps({"pr_number": pr, "branch": branch}, indent=2))


def cmd_promote(args):
    payload = {
        "spec_repo": f"{args.owner}/{args.repo}",
        "pin_commit": args.commit_sha,
        "files": {
            "lsa": args.lsa_path,
            "rag": args.rag_path,
            "ledger": args.ledger_path
        },
        "sealed_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    }
    print(json.dumps(payload, indent=2))


def build_parser():
    p = argparse.ArgumentParser(prog="yara", description="YARA Lógica – GitHub specs integration CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("specs", help="Specs commands")
    sub2 = sp.add_subparsers(dest="subcmd", required=True)

    p_pull = sub2.add_parser("pull", help="Pull spec files at a given ref and write locally")
    p_pull.add_argument("--owner", required=True)
    p_pull.add_argument("--repo", required=True)
    p_pull.add_argument("--ref", required=True, help="commit SHA or branch (use SHA in prod)")
    p_pull.add_argument("--outdir", required=True)
    p_pull.add_argument("--files", nargs="+", required=True)
    p_pull.set_defaults(func=cmd_pull)

    p_verify = sub2.add_parser("verify", help="Verify files against ledger at a given ref")
    p_verify.add_argument("--owner", required=True)
    p_verify.add_argument("--repo", required=True)
    p_verify.add_argument("--ref", required=True)
    p_verify.add_argument("--ledger-path", default="infra/github/hash_ledger.json")
    p_verify.add_argument("--files", nargs="+", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_prop = sub2.add_parser("propose", help="Open a PR with given files (no auto-ledger)")
    p_prop.add_argument("--owner", required=True)
    p_prop.add_argument("--repo", required=True)
    p_prop.add_argument("--base", default="main")
    p_prop.add_argument("--branch")
    p_prop.add_argument("--message", required=True)
    p_prop.add_argument("--title", required=True)
    p_prop.add_argument("--body")
    p_prop.add_argument("--add", action="append", required=True, help="repo_path=local_path")
    p_prop.set_defaults(func=cmd_propose)

    p_prop2 = sub2.add_parser("propose-auto-ledger", help="Open a PR and auto-update ledger")
    p_prop2.add_argument("--owner", required=True)
    p_prop2.add_argument("--repo", required=True)
    p_prop2.add_argument("--base", default="main")
    p_prop2.add_argument("--branch")
    p_prop2.add_argument("--ledger-path", default="infra/github/hash_ledger.json")
    p_prop2.add_argument("--message", required=True)
    p_prop2.add_argument("--title", required=True)
    p_prop2.add_argument("--body")
    p_prop2.add_argument("--add", action="append", required=True, help="repo_path=local_path")
    p_prop2.set_defaults(func=cmd_propose_auto)

    p_prom = sub2.add_parser("promote", help="Emit config JSON to pin a commit in runtime")
    p_prom.add_argument("--owner", required=True)
    p_prom.add_argument("--repo", required=True)
    p_prom.add_argument("--commit-sha", required=True)
    p_prom.add_argument("--lsa-path", default="lsa/spec/LSA_PICC.md")
    p_prom.add_argument("--rag-path", default="rag/spec/RAG_POLICY.md")
    p_prom.add_argument("--ledger-path", default="infra/github/hash_ledger.json")
    p_prom.set_defaults(func=cmd_promote)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
