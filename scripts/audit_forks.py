#!/usr/bin/env python3
import os, sys, base64, json
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

REQUIRED_MARKERS = [
    "Business Source License 1.1",
    "BUSL-1.1",
    "YARA Lógica",
    "Alter Agro",
    "Logic Sorting Architecture",
    "RAG Hybrid",
]

def gh(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def get_forks(owner_repo):
    forks = []
    page = 1
    while True:
        data = gh(f"{API}/repos/{owner_repo}/forks?per_page=100&page={page}")
        if not data: break
        forks.extend(data); page += 1
    return forks

def get_file(owner_repo, path):
    try:
        data = gh(f"{API}/repos/{owner_repo}/contents/{path}")
    except Exception:
        return ""
    if isinstance(data, dict) and data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode(errors="ignore")
    return ""

def open_issue(owner_repo, title, body):
    payload = json.dumps({"title": title, "body": body}).encode()
    req = urllib.request.Request(f"{API}/repos/{REPO}/issues", data=payload, headers=HEADERS)
    req.get_method = lambda: "POST"
    with urllib.request.urlopen(req) as r:
        r.read()

def main():
    if not REPO or not TOKEN:
        print("Missing GITHUB_REPOSITORY or GITHUB_TOKEN", file=sys.stderr)
        sys.exit(1)

    forks = get_forks(REPO)
    problems = []
    for f in forks:
        full = f["full_name"]
        readme = get_file(full, "README.md")
        license_txt = get_file(full, "LICENSE") + "\n" + get_file(full, "LICENSE.md")
        notice = get_file(full, "NOTICE") + "\n" + get_file(full, "NOTICE.md")
        blob_low = (readme + "\n" + license_txt + "\n" + notice).lower()

        missing = [m for m in REQUIRED_MARKERS if m.lower() not in blob_low]
        if len(missing) >= 2:
            problems.append((full, missing))

    if problems:
        for full, miss in problems:
            title = f"Fork audit: Potential BUSL/TM removal in {full}"
            body = (
                f"Automated audit detected missing markers in **{full}**:\n\n"
                + "\n".join([f"- {m}" for m in miss]) +
                "\n\nPlease review this fork and consider friendly contact or DMCA/TM notice if appropriate."
            )
            open_issue(REPO, title, body)
        print(f"Opened {len(problems)} issue(s).")
    else:
        print("All forks seem compliant.")

if __name__ == "__main__":
    main()
