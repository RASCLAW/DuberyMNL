"""Story rotation monitor -- checks GitHub Actions `story-rotation.yml` workflow.

Queries the most recent run and derives state from age + conclusion:
  age < 4h  + success     -> active
  age < 4h  + not-success -> offline
  4h <= age < 8h          -> degraded
  age >= 8h               -> offline (stale)

EXPENSIVE: hits the GitHub REST API (network + rate-limited).
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitors import ServiceStatus  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

EXPENSIVE = True
TIMEOUT_SEC = 6
WORKFLOW_FILE = "story-rotation.yml"
DEFAULT_OWNERS = ["sarinas03", "sarinasmedia"]


def age_human(seconds: float) -> str:
    seconds = int(max(0, seconds))
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m"
    d, rem = divmod(seconds, 86400)
    h = rem // 3600
    return f"{d}d {h}h"


def _detect_owner_from_git() -> str | None:
    try:
        out = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3,
        )
        url = (out.stdout or "").strip()
        if not url:
            return None
        # git@github.com:OWNER/REPO.git  or  https://github.com/OWNER/REPO.git
        if url.startswith("git@"):
            tail = url.split(":", 1)[1]
        else:
            tail = url.split("github.com/", 1)[-1]
        owner = tail.split("/", 1)[0]
        return owner or None
    except Exception:
        return None


def _resolve_owner() -> str | None:
    env_owner = os.environ.get("GITHUB_OWNER")
    if env_owner:
        return env_owner
    detected = _detect_owner_from_git()
    if detected:
        return detected
    return DEFAULT_OWNERS[0]


def check() -> ServiceStatus:
    owner = _resolve_owner()
    if not owner:
        return ServiceStatus.now("story_rotation", "not_wired", "no GITHUB_OWNER / git remote")

    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = (
        f"https://api.github.com/repos/{owner}/DuberyMNL/"
        f"actions/workflows/{WORKFLOW_FILE}/runs?per_page=1"
    )

    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SEC)
    except Exception as exc:
        return ServiceStatus.now(
            "story_rotation", "offline", f"{type(exc).__name__}: {exc}"
        )

    if resp.status_code == 403:
        return ServiceStatus.now("story_rotation", "not_wired", "GH API rate limited")
    if resp.status_code == 404:
        return ServiceStatus.now(
            "story_rotation", "not_wired", f"workflow not found ({owner}/DuberyMNL)"
        )
    if resp.status_code != 200:
        return ServiceStatus.now(
            "story_rotation", "offline", f"HTTP {resp.status_code}"
        )

    try:
        runs = resp.json().get("workflow_runs") or []
    except Exception as exc:
        return ServiceStatus.now(
            "story_rotation", "offline", f"bad JSON: {type(exc).__name__}"
        )

    if not runs:
        return ServiceStatus.now("story_rotation", "not_wired", "no runs yet")

    run = runs[0]
    created_at = run.get("created_at")
    conclusion = run.get("conclusion") or run.get("status") or "unknown"

    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except Exception:
        return ServiceStatus.now("story_rotation", "offline", f"bad created_at: {created_at}")

    age_sec = (datetime.now(timezone.utc) - created_dt).total_seconds()
    age_s = age_human(age_sec)

    if age_sec < 4 * 3600:
        if conclusion == "success":
            return ServiceStatus.now("story_rotation", "active", f"last run {age_s} ago, success")
        return ServiceStatus.now("story_rotation", "offline", f"last run {age_s} ago, {conclusion}")
    if age_sec < 8 * 3600:
        return ServiceStatus.now("story_rotation", "degraded", f"last run {age_s} ago")
    return ServiceStatus.now("story_rotation", "offline", f"last run {age_s} ago (stale)")


if __name__ == "__main__":
    print(check())
