"""Utility functions for invoking shell commands with logging."""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Iterable, Mapping, Optional

LOGGER = logging.getLogger(__name__)


class ShellCommandError(RuntimeError):
    """Raised when a shell command exits with a non-zero status code."""

    def __init__(self, command: Iterable[str], returncode: int, stdout: str, stderr: str):
        self.command = list(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = (
            f"Command {' '.join(self.command)} failed with code {returncode}.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
        super().__init__(message)


def run_command(
    command: Iterable[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    input_text: Optional[str] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute a command and return the completed process.

    Args:
        command: Sequence of command components.
        cwd: Directory to execute the command in.
        env: Additional environment variables.
        input_text: Optional string passed to stdin.
        check: Whether to raise on non-zero exit status.

    Returns:
        subprocess.CompletedProcess with decoded stdout/stderr.
    """

    LOGGER.info("Running command: %s", " ".join(command))
    process = subprocess.run(  # noqa: S603,S607
        list(command),
        cwd=str(cwd) if cwd else None,
        env={**os.environ, **dict(env)} if env else None,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )

    if check and process.returncode != 0:
        raise ShellCommandError(command, process.returncode, process.stdout, process.stderr)

    if process.stdout:
        LOGGER.debug("Command stdout: %s", process.stdout)
    if process.stderr:
        LOGGER.debug("Command stderr: %s", process.stderr)

    return process

