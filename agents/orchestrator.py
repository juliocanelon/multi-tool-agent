from __future__ import annotations

import logging
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

from agents.commanding_agent import CommandingAgent
from agents.intention_agent import IntentionAgent
from agents.repo_agent import RepoAgent
from agents.scan_research_agent import ScanResearchAgent
from agents.verify_agent import VerifyAgent
from mcp.vuln_mcp import VulnMCP
from utils.types import FixResult


log = logging.getLogger("Orchestrator")


class Orchestrator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.repo = RepoAgent()
        self.vuln = VulnMCP()
        self.scan = ScanResearchAgent()
        self.verify = VerifyAgent()
        self.cmd = CommandingAgent(
            mode=cfg["commanding"]["mode"],
            docker_image=cfg["commanding"]["docker_image"],
        )

    def run(self) -> dict:
        intent = IntentionAgent().from_config(self.cfg)
        log.info(f"Intent: {intent}")

        workdir = self.repo.clone(intent.repo_url, intent.branch)
        target_branch = self.repo.create_branch(
            from_ref=intent.branch, prefix=self.cfg["repo"]["fix_branch_prefix"]
        )

        findings = self.vuln.load_findings(
            self.cfg["vulns"]["csv_path"], intent.levels
        )
        plan = self.scan.build_plan(
            findings,
            intent.repo_url,
            intent.branch,
            target_branch,
            self.cfg["verify"]["tests_cmd"],
        )

        instruction_md = Path(self.cfg["commanding"]["instruction_md"])
        self.scan.render_instruction(
            plan,
            intent.repo_url,
            intent.branch,
            target_branch,
            str(instruction_md),
        )

        attempts = 0
        max_attempts = self.cfg["policy"]["max_attempts"]
        last_result: FixResult | None = None

        while attempts < max_attempts:
            attempts += 1
            log.info(f"Attempt {attempts}/{max_attempts}")

            result = self.cmd.run(
                workdir=workdir,
                instruction_md=instruction_md,
                diff_format=self.cfg["commanding"]["diff_format"],
            )
            last_result = result
            if result.status != "SUCCESS" or not result.diff.strip():
                log.warning("No diff generated; stopping or retrying...")
                break

            applied = self.repo.apply_patch(result.diff)
            if not applied:
                log.warning("Patch failed to apply")
                break

            sha = self.repo.commit("chore(ai): auto-fix by code agent MVP")
            self.repo.push(target_branch)

            vr = self.verify.run(
                str(workdir),
                self.cfg["verify"]["tests_cmd"],
                self.cfg["verify"]["fallback_cmd"],
            )
            if vr.tests_passed:
                pr = self.repo.open_pr(
                    intent.repo_url,
                    base=intent.branch,
                    head=target_branch,
                    title="AI Fix (MVP)",
                    body="Automated fix by Code Agent MVP",
                )
                return {
                    "status": "SUCCESS",
                    "branch": target_branch,
                    "commit": sha,
                    "pr": pr,
                    "verify": vr.model_dump(),
                }
            else:
                log.warning("Verification failed; will not open PR")
                break

        return {
            "status": "FAIL",
            "last_result": (last_result.model_dump() if last_result else None),
            "branch": target_branch,
        }
