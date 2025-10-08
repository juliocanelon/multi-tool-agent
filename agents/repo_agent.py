import os
import base64
import time
import logging
from pathlib import Path

import requests

from utils.shell import run

log = logging.getLogger("RepoAgent")


class RepoAgent:
    def __init__(self, workdir: str = "workdir"):
        self.workdir = Path(workdir)

    # ---- Git local ----
    def clone(self, repo_url: str, branch: str) -> Path:
        if self.workdir.exists():
            run("git status", cwd=str(self.workdir))
            return self.workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        rc, _, err = run(f"git clone --branch {branch} {repo_url} {self.workdir}")
        if rc != 0:
            raise RuntimeError(f"git clone failed: {err}")
        return self.workdir

    def create_branch(self, from_ref: str, prefix: str = "fix/ai") -> str:
        ts = int(time.time())
        new_branch = f"{prefix}-{ts}"
        rc, _, err = run(f"git checkout -b {new_branch}", cwd=str(self.workdir))
        if rc != 0:
            raise RuntimeError(f"git checkout -b failed: {err}")
        return new_branch

    def apply_patch(self, diff: str) -> bool:
        patch_file = self.workdir / "ai_fix.patch"
        patch_file.write_text(diff, encoding="utf-8")
        rc, _, _ = run(
            "git apply -p0 --reject --whitespace=fix ai_fix.patch",
            cwd=str(self.workdir),
        )
        return rc == 0

    def commit(self, message: str) -> str:
        run("git add -A", cwd=str(self.workdir))
        rc, out, err = run(f'git commit -m "{message}"', cwd=str(self.workdir))
        if rc != 0:
            raise RuntimeError(f"git commit failed: {err}")
        rc, sha, _ = run("git rev-parse HEAD", cwd=str(self.workdir))
        return sha.strip()

    def push(self, branch: str) -> None:
        rc, _, err = run(f"git push origin {branch}", cwd=str(self.workdir))
        if rc != 0:
            raise RuntimeError(f"git push failed: {err}")

    # ---- GitHub PR (REST) ----
    def open_pr(self, repo_url: str, base: str, head: str, title: str, body: str) -> dict:
        """repo_url: https://github.com/owner/repo"""
        token = os.getenv("GITHUB_TOKEN")
        assert token, "GITHUB_TOKEN is required"

        owner, repo = repo_url.rstrip("/").split("/")[-2:]
        api = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {"title": title, "body": body, "head": head, "base": base}
        r = requests.post(api, headers=headers, json=payload, timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"open_pr failed: {r.status_code} {r.text}")
        return r.json()
