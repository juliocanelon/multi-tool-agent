"""Agent that executes verification commands such as tests or builds."""
from __future__ import annotations

import logging
import shlex

from ..utils import shell
from ..utils.types import VerificationConfig, VerificationResult

LOGGER = logging.getLogger(__name__)


class VerifyAgent:
    """Run post-change verification steps."""

    def __init__(self, config: VerificationConfig) -> None:
        self._config = config

    def run(self) -> VerificationResult:
        """Execute the configured verification command if enabled."""

        if not self._config.enabled:
            LOGGER.info("Verification disabled; skipping execution")
            return VerificationResult(
                succeeded=True,
                output="Verification disabled",
                command=self._config.command,
            )

        LOGGER.info("Running verification command: %s", self._config.command)
        try:
            result = shell.run_command(
                shlex.split(self._config.command),
                cwd=self._config.working_directory,
                check=False,
            )
            success = result.returncode == 0
            if success:
                LOGGER.info("Verification succeeded")
            else:
                LOGGER.error("Verification failed with code %s", result.returncode)
            return VerificationResult(
                succeeded=success,
                output=result.stdout + result.stderr,
                command=self._config.command,
            )
        except Exception as err:  # noqa: BLE001
            LOGGER.exception("Unexpected error while running verification: %s", err)
            return VerificationResult(
                succeeded=False,
                output=str(err),
                command=self._config.command,
            )

