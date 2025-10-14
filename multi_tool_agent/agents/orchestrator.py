import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    def load_dotenv(env_path: Path) -> None:
        """Minimal .env loader used when python-dotenv is unavailable."""
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

from .intention_agent import IntentionAgent
from .scan_research_agent import ScanResearchAgent
from .commanding_agent import CommandingAgent
from .verify_agent import VerifyAgent
from .repo_agent import RepoAgent

class Orchestrator:
    def __init__(self, base_dir:Path):
        load_dotenv(base_dir / ".env")
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.workdir = base_dir / "workdir"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)

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
        # Export findings para el contenedor
        findings_json = self.data_dir / "findings.json"
        self.research.dump_findings_json(findings, findings_json)

        instruction = self.research.build_instruction(intent, findings)
        (self.data_dir/"instruction.md").write_text(instruction, encoding="utf-8")

        use_docker = True  # ← cambia a False si quieres seguir local
        if use_docker:
            # Asegúrate de haber construido la imagen primero
            docker_image = os.getenv("CODE_FIX_IMAGE", "code-fix-cli:latest")
            fix = self.command.run_in_docker(docker_image, workdir=self.workdir, data_dir=self.data_dir)
        else:
            fix = self.command.apply_naive_fix(findings, repo_root=self.workdir)

        ver = self.verifyer.verify()
        return {
            "intention": intent.model_dump(),
            "repo": repo_log,
            "fix": fix,
            "verify": ver,
            "instruction_path": str(self.data_dir/"instruction.md"),
            "findings_json": str(findings_json),
            "workdir": str(self.workdir),
        }

