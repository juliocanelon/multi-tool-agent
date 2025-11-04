# agents/orchestrator.py
import os
from pathlib import Path
from dataclasses import is_dataclass, asdict
from typing import Any, Dict

def _to_dict(obj: Any):
    """
    Normaliza objetos a tipos JSON-serializables.
    - Pydantic v2 -> .model_dump()
    - Pydantic v1 -> .dict()
    - dataclasses -> asdict()
    - Path -> str
    - set/frozenset -> list
    - dict/list/tupla/primitivos -> se devuelven tal cual
    - fallback -> str(obj)
    """
    if obj is None:
        return None
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    # Pydantic v1
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    # Dataclass
    if is_dataclass(obj):
        try:
            return asdict(obj)
        except Exception:
            pass
    # Path
    if isinstance(obj, Path):
        return str(obj)
    # Conjuntos
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    # Diccionario
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    # Lista / Tupla
    if isinstance(obj, (list, tuple)):
        return [ _to_dict(v) for v in obj ]
    # Primitivos
    if isinstance(obj, (str, int, float, bool)):
        return obj
    # Fallback
    return str(obj)

# Carga .env con tolerancia a entornos mínimos
try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv(env_path: Path) -> None:
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
    """
    Flujo MVP:
      1) Intención (parseo local)
      2) Repo: clone/update
      3) Research: CSV -> findings + instruction.md + findings.json
      4) Fix: docker (o local)
      5) Verify
      6) (C6) Rama fix/ai-<timestamp> + commit + (opcional) push
    """
    def __init__(self, base_dir: Path):
        load_dotenv(base_dir / ".env")
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.workdir  = base_dir / "workdir"

        # Garantiza estructura
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)

        # Agentes
        self.intention = IntentionAgent()
        self.research  = ScanResearchAgent(self.data_dir)
        self.command   = CommandingAgent(self.workdir)
        self.verifyer  = VerifyAgent(self.workdir)
        self.repo      = RepoAgent(self.workdir)

    def handle(self, user_text: str) -> Dict[str, Any]:
        print(f"[ORCH] handle called: {user_text[:120]}")

        # Defaults desde .env
        env_defaults = {
            "DEFAULT_REPO_URL": os.getenv("DEFAULT_REPO_URL", ""),
            "DEFAULT_BRANCH":   os.getenv("DEFAULT_BRANCH", "main"),
        }

        # 1) Intención
        intent = self.intention.run(user_text, env_defaults)
        print(f"[ORCH] intention: repo={intent.repo_url or env_defaults['DEFAULT_REPO_URL']}, "
              f"branch={intent.branch or env_defaults['DEFAULT_BRANCH']}, "
              f"sevs={intent.severity_to_fix}")

        # 2) Repo
        repo_log = self.repo.clone_or_update(
            intent.repo_url or env_defaults["DEFAULT_REPO_URL"],
            intent.branch   or env_defaults["DEFAULT_BRANCH"]
        )
        print(f"[ORCH] repo step: {repo_log.get('step')} ok={repo_log.get('ok')}")

        # 3) Research (CSV -> findings + instruction.md + findings.json)
        findings = self.research.collect_findings(intent)
        findings_json = self.data_dir / "findings.json"
        self.research.dump_findings_json(findings, findings_json)
        instruction = self.research.build_instruction(intent, findings)
        (self.data_dir / "instruction.md").write_text(instruction, encoding="utf-8")
        print(f"[ORCH] findings: {len(findings)} -> {findings_json.name}, instruction.md listo")

        # 4) Fix (Docker o local)
        use_docker = os.getenv("USE_DOCKER", "true").lower() == "true"
        if use_docker:
            docker_image = os.getenv("CODE_FIX_IMAGE", "code-fix-cli:latest")
            print(f"[ORCH] running fix in docker, image={docker_image}")
            fix = self.command.run_in_docker(docker_image, workdir=self.workdir, data_dir=self.data_dir)
        else:
            print("[ORCH] running local naive fix")
            fix = self.command.apply_naive_fix(findings, repo_root=self.workdir)

        print(f"[ORCH] fix status: {fix.get('status')}")

        # 5) Verify
        ver = self.verifyer.verify()
        print(f"[ORCH] verify: verified={ver.get('verified')} changed={ver.get('changed')}")

        # 6) C6 — Branch/commit/push
        git_push     = os.getenv("GIT_PUSH", "false").lower() == "true"
        author_name  = os.getenv("GIT_AUTHOR_NAME", "CodeFix Bot")
        author_email = os.getenv("GIT_AUTHOR_EMAIL", "bot@local")
        remote_name  = os.getenv("GIT_REMOTE_NAME", "origin")

        feature = {"ok": False, "branch": ""}
        commit  = {"ok": False, "step": ""}
        push    = {"ok": False, "step": ""}

        if ver.get("verified"):
            feature = self.repo.create_feature_branch(intent.branch or env_defaults["DEFAULT_BRANCH"])
            print(f"[ORCH] feature branch: {feature.get('branch')} ok={feature.get('ok')}")
            commit  = self.repo.commit_all(
                message="chore(ai-fix): auto-fix (naive docker)",
                author_name=author_name,
                author_email=author_email
            )
            print(f"[ORCH] commit: {commit.get('step')} ok={commit.get('ok')}")
            if git_push and feature.get("branch"):
                push = self.repo.push_branch(feature["branch"], remote=remote_name)
                print(f"[ORCH] push: {push.get('step')} ok={push.get('ok')}")
        else:
            print("[ORCH] verification failed, skipping branch/commit/push")

        # Respuesta serializable
        return {
            "intention":      _to_dict(intent),
            "repo":           _to_dict(repo_log),
            "fix":            _to_dict(fix),
            "verify":         _to_dict(ver),
            "git": {
                "feature_branch": _to_dict(feature),
                "commit":         _to_dict(commit),
                "push":           _to_dict(push),
            },
            "instruction_path": str(self.data_dir / "instruction.md"),
            "findings_json":    str(self.data_dir / "findings.json"),
            "workdir":          str(self.workdir),
        }
