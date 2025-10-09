from dataclasses import dataclass
from pathlib import Path
import csv

@dataclass
class Finding:
    file:str
    line:str
    rule:str
    severity:str
    summary:str

class ScanResearchAgent:
    """
    MVP: 'investiga' leyendo data/checkmarx.csv y arma instruction.md
    filtrando por severidades pedidas.
    """
    def __init__(self, data_dir:Path):
        self.data_dir = data_dir

    def build_instruction(self, intention) -> str:
        csv_path = self.data_dir / "checkmarx.csv"
        findings = []
        if csv_path.exists():
            with csv_path.open("r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    if row.get("severity","").upper() in intention.severity_to_fix:
                        findings.append(Finding(
                            file=row.get("file",""),
                            line=row.get("line",""),
                            rule=row.get("rule",""),
                            severity=row.get("severity",""),
                            summary=row.get("summary",""),
                        ))
        # Instrucción mínima
        lines = [
            "# Instrucción para coding agent",
            f"Repo: {intention.repo_url}",
            f"Branch: {intention.branch}",
            f"Checkmarx Project: {intention.checkmarx_project_id}",
            f"Severidades objetivo: {', '.join(intention.severity_to_fix)}",
            "",
            "## Hallazgos prioritarios (resumen del CSV)",
        ]
        for fx in findings[:50]:
            lines.append(f"- [{fx.severity}] {fx.rule} — {fx.file}:{fx.line} — {fx.summary}")
        lines += ["", "## Tareas", "1) Corregir hallazgos listados.", "2) Generar breve changelog."]
        return "\n".join(lines)
