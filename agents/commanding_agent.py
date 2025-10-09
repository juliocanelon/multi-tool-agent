from pathlib import Path

class CommandingAgent:
    """
    MVP: 'ejecuta' el coding agent. Por ahora, sólo dry-run que guarda archivos.
    Luego llamaremos al CLI real (local o dentro de Docker).
    """
    def __init__(self, workdir:Path):
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)

    def dry_run(self, instruction_md:str) -> dict:
        (self.workdir/"instruction.md").write_text(instruction_md, encoding="utf-8")
        (self.workdir/"stdout.log").write_text("SIMULATED: fix attempt ok", encoding="utf-8")
        (self.workdir/"stderr.log").write_text("", encoding="utf-8")
        return {"status":"SIMULATED_OK","stdout":"SIMULATED: fix attempt ok"}
