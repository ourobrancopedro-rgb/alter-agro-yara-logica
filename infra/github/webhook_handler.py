#!/usr/bin/env python3
"""
GitHub Webhook Handler for YARA Runtime Integration

Handles webhook events from the spec repository to trigger YARA runtime updates.

Usage:
    # Run as Flask app
    export WEBHOOK_SECRET="your-secret"
    python infra/github/webhook_handler.py

    # Or use with WSGI server
    gunicorn infra.github.webhook_handler:app
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["WEBHOOK_SECRET"] = os.environ.get("WEBHOOK_SECRET", "")
app.config["YARA_CALLBACK_URL"] = os.environ.get("YARA_CALLBACK_URL", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.

    Args:
        payload_body: Raw webhook payload bytes
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def notify_yara_runtime(event_type: str, data: Dict) -> None:
    """
    Notify YARA runtime about spec repository events.

    Args:
        event_type: Type of event (pr_opened, pr_merged, main_updated, etc.)
        data: Event data payload
    """
    callback_url = app.config["YARA_CALLBACK_URL"]

    if not callback_url:
        logger.warning("YARA_CALLBACK_URL not configured, skipping notification")
        return

    try:
        import requests
        response = requests.post(
            callback_url,
            json={
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Notified YARA runtime: {event_type}")
    except Exception as e:
        logger.error(f"Failed to notify YARA runtime: {e}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "yara-webhook-handler"}), 200


@app.route("/webhooks/github", methods=["POST"])
def github_webhook():
    """
    Main webhook endpoint for GitHub events.

    Expected headers:
        X-Hub-Signature-256: HMAC signature
        X-GitHub-Event: Event type
        X-GitHub-Delivery: Unique delivery ID
    """
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature, app.config["WEBHOOK_SECRET"]):
        logger.warning("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    payload = request.json

    logger.info(f"Received {event_type} event (delivery: {delivery_id})")

    # Route to handlers
    if event_type == "pull_request":
        handle_pull_request(payload)
    elif event_type == "push":
        handle_push(payload)
    elif event_type == "check_suite":
        handle_check_suite(payload)
    elif event_type == "workflow_run":
        handle_workflow_run(payload)
    elif event_type == "repository_dispatch":
        handle_repository_dispatch(payload)
    else:
        logger.info(f"Ignoring event type: {event_type}")

    return jsonify({"status": "processed"}), 200


def handle_pull_request(payload: Dict) -> None:
    """
    Handle pull_request events.

    Events:
        - opened: Run shadow validation
        - synchronize: Re-validate on new commits
        - closed (merged): Promote pin to staging
    """
    action = payload["action"]
    pr = payload["pull_request"]

    pr_number = pr["number"]
    pr_title = pr["title"]
    pr_author = pr["user"]["login"]

    if action == "opened":
        logger.info(f"PR #{pr_number} opened by {pr_author}: {pr_title}")

        # Trigger shadow validation in YARA runtime
        notify_yara_runtime("pr_opened", {
            "pr_number": pr_number,
            "head_sha": pr["head"]["sha"],
            "base_sha": pr["base"]["sha"],
            "changed_files": [f["filename"] for f in pr.get("files", [])]
        })

    elif action == "synchronize":
        logger.info(f"PR #{pr_number} updated (new commits)")

        notify_yara_runtime("pr_updated", {
            "pr_number": pr_number,
            "head_sha": pr["head"]["sha"]
        })

    elif action == "closed" and pr.get("merged"):
        merge_sha = pr["merge_commit_sha"]
        logger.info(f"PR #{pr_number} merged → commit {merge_sha[:7]}")

        # Promote pin to staging (after CI passes)
        notify_yara_runtime("pr_merged", {
            "pr_number": pr_number,
            "merge_commit_sha": merge_sha,
            "merged_by": pr.get("merged_by", {}).get("login"),
            "changed_files": [f["filename"] for f in pr.get("files", [])]
        })


def handle_push(payload: Dict) -> None:
    """
    Handle push events (mainly to main branch).

    Action: Consider rotating production pin after CI validation.
    """
    ref = payload["ref"]
    before = payload["before"]
    after = payload["after"]

    if ref == "refs/heads/main":
        logger.info(f"Main branch updated: {before[:7]} → {after[:7]}")

        commits = payload.get("commits", [])
        logger.info(f"  {len(commits)} new commit(s)")

        # Wait for CI, then consider production rotation
        notify_yara_runtime("main_updated", {
            "commit_sha": after,
            "commits": [
                {
                    "sha": c["id"],
                    "message": c["message"],
                    "author": c["author"]["name"]
                }
                for c in commits
            ]
        })


def handle_check_suite(payload: Dict) -> None:
    """
    Handle check_suite events (CI status).

    Action: If checks pass on main, promote pin to production.
    """
    action = payload["action"]
    check_suite = payload["check_suite"]

    status = check_suite.get("status")
    conclusion = check_suite.get("conclusion")
    head_sha = check_suite["head_sha"]
    branch = check_suite.get("head_branch")

    if action == "completed" and branch == "main":
        if conclusion == "success":
            logger.info(f"✓ CI passed for {head_sha[:7]} on main")

            notify_yara_runtime("ci_passed_main", {
                "commit_sha": head_sha,
                "check_suite_id": check_suite["id"]
            })
        else:
            logger.warning(f"✗ CI failed for {head_sha[:7]} on main: {conclusion}")


def handle_workflow_run(payload: Dict) -> None:
    """
    Handle workflow_run events (GitHub Actions).

    Similar to check_suite but more granular.
    """
    action = payload["action"]
    workflow_run = payload["workflow_run"]

    status = workflow_run.get("status")
    conclusion = workflow_run.get("conclusion")
    workflow_name = workflow_run.get("name")
    head_sha = workflow_run["head_sha"]

    if action == "completed" and status == "completed":
        logger.info(
            f"Workflow '{workflow_name}' completed: {conclusion} ({head_sha[:7]})"
        )

        if conclusion == "success":
            notify_yara_runtime("workflow_success", {
                "workflow_name": workflow_name,
                "commit_sha": head_sha
            })


def handle_repository_dispatch(payload: Dict) -> None:
    """
    Handle repository_dispatch events (manual triggers).

    Example dispatch payloads:
        - {"event_type": "rotate-pin", "commit_sha": "abc123..."}
        - {"event_type": "invalidate-cache"}
    """
    event_type = payload.get("event_type")
    client_payload = payload.get("client_payload", {})

    logger.info(f"Repository dispatch: {event_type}")
    logger.debug(f"Payload: {json.dumps(client_payload, indent=2)}")

    if event_type == "rotate-pin":
        commit_sha = client_payload.get("commit_sha")
        if commit_sha:
            notify_yara_runtime("manual_pin_rotation", {
                "commit_sha": commit_sha,
                "requested_by": payload.get("sender", {}).get("login")
            })

    elif event_type == "invalidate-cache":
        notify_yara_runtime("invalidate_cache", {})


@app.route("/trigger/rotate-pin", methods=["POST"])
def trigger_pin_rotation():
    """
    Manual endpoint to trigger pin rotation (authenticated).

    Request body:
        {
            "commit_sha": "abc123...",
            "environment": "staging|production"
        }
    """
    # In production, add authentication here (API key, JWT, etc.)

    data = request.json
    commit_sha = data.get("commit_sha")
    environment = data.get("environment", "staging")

    if not commit_sha:
        return jsonify({"error": "commit_sha required"}), 400

    logger.info(f"Manual pin rotation to {commit_sha[:7]} ({environment})")

    notify_yara_runtime("manual_pin_rotation", {
        "commit_sha": commit_sha,
        "environment": environment
    })

    return jsonify({"status": "rotation triggered"}), 200


if __name__ == "__main__":
    if not app.config["WEBHOOK_SECRET"]:
        logger.warning(
            "WEBHOOK_SECRET not set! Set via: export WEBHOOK_SECRET=<secret>"
        )

    # Development server (use gunicorn/uwsgi in production)
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=os.environ.get("DEBUG", "").lower() == "true"
    )
