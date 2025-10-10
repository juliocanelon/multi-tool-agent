import os, subprocess, shlex
from pathlib import Path

def _run(cmd: str, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(shlex.split(cmd), cwd=cwd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)

class RepoAgent:
    """
    Clona o actualiza un repo en workdir. Soporta:
    - HTTPS con usuario/token vía env (GIT_USERNAME/GIT_TOKEN)
    - SSH usando el agente local (o GIT_SSH_COMMAND si apuntas a una llave específica)
    """
    def __init__(self, workdir: Path):
        self.workdir = workdir

    def _prepare_env(self) -> dict:
        env = os.environ.copy()
        key_path = os.getenv("GIT_SSH_KEY_PATH", "").strip()
        if key_path:
            env["GIT_SSH_COMMAND"] = f"ssh -i {key_path} -o StrictHostKeyChecking=no"
        return env

    def _url_with_auth(self, url: str) -> str:
        mode = (os.getenv("GIT_AUTH_MODE") or "HTTPS").upper()
        if mode != "HTTPS":
            return url
        user = os.getenv("GIT_USERNAME", "").strip()
        token = os.getenv("GIT_TOKEN", "").strip()
        if not (user and token):  # sin credenciales, devuelvo tal cual
            return url
        # Inserta user:token en la URL https://
        # OJO: no imprimas esta URL con token en logs.
        if url.startswith("https://"):
            return url.replace("https://", f"https://{user}:{token}@")
        return url

    def clone_or_update(self, url: str, branch: str | None = "main") -> dict:
        self.workdir.mkdir(parents=True, exist_ok=True)
        env = self._prepare_env()
        authed_url = self._url_with_auth(url)

        if not (self.workdir / ".git").exists():
            code, out = _run(f"git init .", self.workdir)
            if code != 0: return {"ok": False, "step": "git init", "log": out}
            code, out = _run(f"git remote add origin {authed_url}", self.workdir)
            if code != 0 and "already exists" not in out:
                return {"ok": False, "step": "git remote add", "log": out}
            # fetch y checkout branch específico (si existe), si no, default
            code, out = _run(f"git fetch origin --depth=1 {branch}", self.workdir)
            if code != 0:
                # intenta traer default branch
                code, out2 = _run("git fetch origin --depth=1", self.workdir)
                if code != 0: return {"ok": False, "step": "git fetch", "log": out + out2}
                # detecta default
                code, head = _run("git remote show origin", self.workdir)
                default_branch = "main"
                for line in head.splitlines():
                    if "HEAD branch:" in line:
                        default_branch = line.split(":",1)[1].strip()
                        break
                branch = default_branch
            code, out3 = _run(f"git checkout -B {branch} FETCH_HEAD", self.workdir)
            if code != 0: return {"ok": False, "step": "git checkout", "log": out3}
            return {"ok": True, "step": "cloned", "branch": branch}
        else:
            # update
            code, out = _run("git fetch origin --prune", self.workdir)
            if code != 0: return {"ok": False, "step": "git fetch", "log": out}
            code, out2 = _run(f"git checkout {branch}", self.workdir)
            if code != 0: return {"ok": False, "step": "git checkout", "log": out2}
            code, out3 = _run(f"git reset --hard origin/{branch}", self.workdir)
            if code != 0: return {"ok": False, "step": "git reset", "log": out3}
            return {"ok": True, "step": "updated", "branch": branch}
