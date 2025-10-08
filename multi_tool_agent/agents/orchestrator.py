"""Main orchestrator for the Code Fix Agent MVP."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .commanding_agent import CommandingAgent
from .intention_agent import IntentionAgent
from .repo_agent import RepoAgent
from .scan_research_agent import ScanResearchAgent
from .verify_agent import VerifyAgent
from ..utils.types import CommandingResponse, MVPConfig, Plan, VerificationResult

LOGGER = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """Aggregates the outcomes of the orchestrated run."""

    plan: Plan
    commanding_response: CommandingResponse
    verification: VerificationResult | None


class Orchestrator:
    """Coordinates the flow between individual agents."""

    def __init__(
        self,
        config: MVPConfig,
        *,
        intention_agent: IntentionAgent,
        scan_agent: ScanResearchAgent,
        commanding_agent: CommandingAgent,
        repo_agent: RepoAgent,
        verify_agent: VerifyAgent,
    ) -> None:
        self._config = config
        self._intention_agent = intention_agent
        self._scan_agent = scan_agent
        self._commanding_agent = commanding_agent
        self._repo_agent = repo_agent
        self._verify_agent = verify_agent

    def run(self) -> OrchestratorResult:
        """Execute the end-to-end code fix workflow."""

        LOGGER.info("Starting orchestrator run")
        plan = self._intention_agent.generate_plan()
        plan.findings = self._scan_agent.enrich(plan.findings)

        response = self._commanding_agent.generate_diff(plan)
        verification: VerificationResult | None = None

        if response.diff:
            LOGGER.info("Applying diff returned by commanding agent")
            branch_name = self._repo_agent.prepare_branch()
            self._repo_agent.apply_diff(response.diff)
            self._repo_agent.stage_all()
            self._repo_agent.commit("Apply automated security fix")
            self._repo_agent.push(branch_name)
            self._repo_agent.create_pr(branch_name)
            verification = self._verify_agent.run()
        else:
            LOGGER.warning("No diff received from commanding agent; skipping repo operations")

        return OrchestratorResult(plan=plan, commanding_response=response, verification=verification)

