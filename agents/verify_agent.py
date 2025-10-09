from pathlib import Path

class VerifyAgent:
    """
    MVP: verificación ficticia: lee stdout.log y declara PASS si contiene 'ok'.
    """
    def __init__(self, workdir:Path):
        self.workdir = workdir

    def verify(self) -> dict:
        out = (self.workdir/"stdout.log").read_text(encoding="utf-8") if (self.workdir/"stdout.log").exists() else ""
        return {"verified": "ok" in out.lower(), "details": out[:500]}
