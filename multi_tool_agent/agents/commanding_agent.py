"""Agent responsible for interfacing with the code commanding backend."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..utils.types import CommandingConfig, CommandingResponse, Plan

LOGGER = logging.getLogger(__name__)


class CommandingAgent:
    """Produce code changes by delegating to a provider (stub for MVP)."""

    def __init__(self, config: CommandingConfig) -> None:
        self._config = config

    def generate_diff(self, plan: Plan) -> CommandingResponse:
        """Generate a diff based on the provided plan.

        The MVP implementation uses a stub backend that either returns a diff
        from a configured file path or a static placeholder.
        """

        LOGGER.info("Generating diff using provider: %s", self._config.provider)

        diff: Optional[str] = None
        if self._config.provider.lower() == "stub":
            diff = self._load_stub_diff()
        else:
            LOGGER.warning("Provider %s is not implemented. Returning empty diff.", self._config.provider)

        return CommandingResponse(diff=diff, provider=self._config.provider)

    def _load_stub_diff(self) -> Optional[str]:
        path: Optional[Path] = self._config.stub_diff_path
        if path and path.exists():
            LOGGER.info("Loading stub diff from %s", path)
            return path.read_text(encoding="utf-8")

        LOGGER.warning("Stub diff path not provided or missing. Returning empty diff.")
        return None

