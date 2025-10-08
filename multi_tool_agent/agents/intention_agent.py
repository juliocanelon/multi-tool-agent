"""Agent that converts scan findings into a remediation plan."""
from __future__ import annotations

import csv
import logging
from typing import Iterable

from ..utils.types import Finding, MVPConfig, Plan

LOGGER = logging.getLogger(__name__)


class IntentionAgent:
    """Generate a high-level remediation plan for a set of findings."""

    def __init__(self, config: MVPConfig) -> None:
        self._config = config

    def load_findings(self) -> Iterable[Finding]:
        """Parse the Checkmarx CSV and yield findings."""

        csv_path = self._config.checkmarx_csv
        LOGGER.info("Loading Checkmarx findings from %s", csv_path)

        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    finding = Finding(
                        project=row.get("Project", ""),
                        file=row.get("File", ""),
                        line=int(row.get("Line", "0") or 0),
                        severity=row.get("Severity", "Unknown"),
                        query=row.get("Query", ""),
                        description=row.get("Description", ""),
                        remediation=row.get("Remediation", ""),
                    )
                    LOGGER.debug("Loaded finding: %s", finding)
                    yield finding
                except ValueError as err:
                    LOGGER.warning("Skipping row due to error: %s", err)

    def generate_plan(self) -> Plan:
        """Create and persist the remediation plan file."""

        plan = Plan(findings=list(self.load_findings()))
        instruction_path = self._config.instruction_path
        LOGGER.info("Writing remediation plan to %s", instruction_path)

        lines = ["# Remediation Plan", ""]
        for finding in plan.findings:
            lines.extend(
                [
                    f"## {finding.query} ({finding.severity})",
                    f"* Project: {finding.project}",
                    f"* Location: {finding.file}:{finding.line}",
                    f"* Description: {finding.description}",
                    f"* Recommended Fix: {finding.remediation}",
                    "",
                ]
            )

        instruction_path.write_text("\n".join(lines), encoding="utf-8")
        plan.plan_path = instruction_path
        return plan

