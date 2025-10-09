import subprocess, shlex
from pathlib import Path

class RepoAgent:
    """
    MVP: clonado opcional (no usado aún en el flujo). Dejado listo.
    Requiere 'git' instalado.
    """
    def __init__(self, workdir:Path):
        self.workdir = workdir

    def clone_or_update(self, url:str, branch:str|None="main") -> str:
        if not (self.workdir/".git").exists():
            cmd = f"git clone --depth=1 --branch {branch} {url} ."
        else:
            cmd = "git fetch --all --prune && git reset --hard origin/{branch}".format(branch=branch or "main")
        proc = subprocess.run(shlex.split(cmd), cwd=self.workdir, capture_output=True, text=True)
        return proc.stdout + proc.stderr
