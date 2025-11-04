import os, subprocess, shlex, datetime
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

    def current_branch(self) -> str:
        code, out = _run("git rev-parse --abbrev-ref HEAD", self.workdir)
        return out.strip() if code == 0 else ""

    def create_feature_branch(self, base_branch: str) -> dict:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        feat = f"fix/ai-{ts}"
        code, out = _run(f"git checkout -B {feat} {base_branch}", self.workdir)
        return {"ok": code == 0, "branch": feat, "log": out}

    def commit_all(self, message: str, author_name: str, author_email: str) -> dict:
        _run(f'git config user.name "{author_name}"', self.workdir)
        _run(f'git config user.email "{author_email}"', self.workdir)
        code_add, out_add = _run("git add -A", self.workdir)
        if code_add != 0:
            return {"ok": False, "step": "git add", "log": out_add}
        code_st, out_st = _run("git diff --cached --name-only", self.workdir)
        if not out_st.strip():
            return {"ok": True, "step": "nothing_to_commit", "log": out_st}
        code_c, out_c = _run(f'git commit -m "{message}"', self.workdir)
        return {"ok": code_c == 0, "step": "git commit", "log": out_c}

    def push_branch(self, branch: str, remote: str = "origin") -> dict:
        mode = (os.getenv("GIT_AUTH_MODE") or "HTTPS").upper()
        if mode == "HTTPS":
            user = os.getenv("GIT_USERNAME", "").strip()
            token = os.getenv("GIT_TOKEN", "").strip()
            if user and token:
                code_url, out_url = _run(f"git remote get-url {remote}", self.workdir)
                if code_url == 0:
                    current = out_url.strip()
                    authed = self._url_with_auth(current)
                    if authed != current:
                        _run(f"git remote set-url {remote} {authed}", self.workdir)

        code, out = _run(f"git push {remote} {branch}:{branch}", self.workdir)
        return {"ok": code == 0, "step": "git push", "log": out}