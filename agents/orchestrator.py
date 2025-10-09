import os
from pathlib import Path
from dotenv import load_dotenv

from .intention_agent import IntentionAgent
from .scan_research_agent import ScanResearchAgent
from .commanding_agent import CommandingAgent
from .verify_agent import VerifyAgent
from .repo_agent import RepoAgent

class Orchestrator:
    def __init__(self, base_dir:Path):
        load_dotenv(base_dir/".env")
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.workdir  = base_dir / "workdir"

        self.intention = IntentionAgent()
        self.research  = ScanResearchAgent(self.data_dir)
        self.command   = CommandingAgent(self.workdir)
        self.verifyer  = VerifyAgent(self.workdir)
        self.repo      = RepoAgent(self.workdir)

    def handle(self, user_text:str) -> dict:
        env_defaults = {
            "DEFAULT_REPO_URL": os.getenv("DEFAULT_REPO_URL",""),
            "DEFAULT_BRANCH": os.getenv("DEFAULT_BRANCH","main"),
        }
        intent = self.intention.run(user_text, env_defaults)

        repo_log = self.repo.clone_or_update(intent.repo_url or env_defaults["DEFAULT_REPO_URL"],
                                             intent.branch or env_defaults["DEFAULT_BRANCH"])

        findings = self.research.collect_findings(intent)
        instruction = self.research.build_instruction(intent, findings)
        (self.data_dir/"instruction.md").write_text(instruction, encoding="utf-8")

        # NUEVO: aplicar fix naive sobre el repo clonado en workdir
        fix = self.command.apply_naive_fix(findings, repo_root=self.workdir)

        ver = self.verifyer.verify()
        return {
            "intention": intent.model_dump(),
            "repo": repo_log,
            "fix": fix,
            "verify": ver,
            "instruction_path": str(self.data_dir/"instruction.md"),
            "workdir": str(self.workdir),
        }
