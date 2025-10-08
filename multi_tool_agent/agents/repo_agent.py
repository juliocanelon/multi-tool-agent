"""Agent handling all git and repository interactions."""
from __future__ import annotations

import logging
from datetime import datetime

from ..utils import shell
from ..utils.types import RepoConfig

LOGGER = logging.getLogger(__name__)


class RepoAgent:
    """Encapsulates git operations for applying fixes."""

    def __init__(self, config: RepoConfig) -> None:
        self._config = config
        self._repo_path = config.path.resolve()
        LOGGER.info("Repo agent initialized for %s", self._repo_path)

    def prepare_branch(self) -> str:
        """Checkout the base branch and create a new working branch."""

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        branch_name = f"{self._config.branch_prefix}/{timestamp}"

        shell.run_command(["git", "checkout", self._config.base_branch], cwd=self._repo_path)
        shell.run_command(["git", "pull", "--ff-only"], cwd=self._repo_path)
        shell.run_command(["git", "checkout", "-b", branch_name], cwd=self._repo_path)
        LOGGER.info("Created branch %s", branch_name)
        return branch_name

    def apply_diff(self, diff: str) -> None:
        """Apply a unified diff to the repository."""

        LOGGER.info("Applying diff to repository")
        shell.run_command(
            ["git", "apply", "--whitespace=fix"],
            cwd=self._repo_path,
            input_text=diff,
        )

    def stage_all(self) -> None:
        """Stage all changes for commit."""

        shell.run_command(["git", "add", "-A"], cwd=self._repo_path)

    def commit(self, message: str) -> None:
        """Commit staged changes."""

        shell.run_command(["git", "commit", "-m", message], cwd=self._repo_path)

    def push(self, branch_name: str) -> None:
        """Push the working branch to the remote if enabled."""

        if not self._config.push:
            LOGGER.info("Push disabled in configuration; skipping push.")
            return

        shell.run_command(["git", "push", "-u", "origin", branch_name], cwd=self._repo_path)

    def create_pr(self, branch_name: str) -> None:
        """Placeholder for PR creation logic."""

        if not self._config.create_pr:
            LOGGER.info("PR creation disabled in configuration; skipping.")
            return

        LOGGER.warning("PR creation is not implemented in the MVP.")

