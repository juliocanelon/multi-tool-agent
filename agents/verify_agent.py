from pathlib import Path

class VerifyAgent:
    def __init__(self, workdir:Path):
        self.workdir = workdir

    def verify(self) -> dict:
        out = (self.workdir/"stdout.log").read_text(encoding="utf-8") if (self.workdir/"stdout.log").exists() else ""
        changed = 0
        for token in out.split():
            if token.startswith("changed="):
                try:
                    changed = int(token.split("=",1)[1])
                except: pass
        return {"verified": changed > 0, "details": out[:500], "changed": changed}
