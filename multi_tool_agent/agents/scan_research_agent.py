"""Agent responsible for contextualizing scan findings."""
from __future__ import annotations

import logging
from typing import Iterable, List

from ..utils.types import Finding

LOGGER = logging.getLogger(__name__)


class ScanResearchAgent:
    """Provides lightweight enrichment for scan findings."""

    def enrich(self, findings: Iterable[Finding]) -> List[Finding]:
        """Perform enrichment on the provided findings.

        For the MVP we simply log and return the findings unchanged, but the hook
        is kept to demonstrate where additional research or call-outs to other
        systems could be inserted.
        """

        enriched: List[Finding] = []
        for finding in findings:
            LOGGER.info(
                "Enriching finding for %s at %s:%s", finding.project, finding.file, finding.line
            )
            enriched.append(finding)
        return enriched

