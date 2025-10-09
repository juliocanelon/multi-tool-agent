from dataclasses import dataclass
from pathlib import Path
import csv

@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    summary: str

class ScanResearchAgent:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _parse_row(self, row: dict) -> Finding | None:
        """
        Adapta filas de dos esquemas:
        A) file,line,rule,severity,summary
        B) file_path,line_number,vulnerability_type,(sin severity),description
        """
        # Normaliza claves a minúsculas
        low = {k.lower(): v for k, v in row.items()}

        # Esquema A
        if "file" in low and "line" in low:
            try:
                ln = int((low.get("line") or "0").strip() or "0")
            except:
                ln = 0
            return Finding(
                file=(low.get("file") or "").strip(),
                line=ln,
                rule=(low.get("rule") or "").strip(),
                severity=(low.get("severity") or "").strip().upper() or "HIGH",
                summary=(low.get("summary") or "").strip(),
            )

        # Esquema B
        if "file_path" in low and "line_number" in low:
            try:
                ln = int((low.get("line_number") or "0").strip() or "0")
            except:
                ln = 0
            # No hay severidad -> asumimos HIGH para el MVP
            return Finding(
                file=(low.get("file_path") or "").strip(),
                line=ln,
                rule=(low.get("vulnerability_type") or "").strip(),
                severity="HIGH",
                summary=(low.get("description") or "").strip(),
            )

        return None

    def collect_findings(self, intention) -> list[Finding]:
        csv_path = self.data_dir / "checkmarx.csv"
        findings: list[Finding] = []
        if csv_path.exists():
            with csv_path.open("r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    fx = self._parse_row(row)
                    if not fx:
                        continue
                    # Filtra por severidad si el registro trae severidad; si no trae, ya es HIGH por defecto
                    if intention.severity_to_fix and fx.severity.upper() not in intention.severity_to_fix:
                        continue
                    findings.append(fx)
        return findings

    def build_instruction(self, intention, findings: list[Finding]) -> str:
        lines = [
            "# Instrucción para coding agent",
            f"Repo: {intention.repo_url}",
            f"Branch: {intention.branch}",
            f"Checkmarx Project: {intention.checkmarx_project_id}",
            f"Severidades objetivo: {', '.join(intention.severity_to_fix) or 'HIGH'}",
            "",
            "## Hallazgos prioritarios (del CSV)",
        ]
        for fx in findings[:200]:
            lines.append(f"- [{fx.severity}] {fx.rule} — {fx.file}:{fx.line} — {fx.summary}")
        lines += ["", "## Tareas", "1) Corregir hallazgos listados.", "2) Generar breve changelog."]
        return "\n".join(lines)
    
    def dump_findings_json(self, findings: list[Finding], out_path):
        import json
        data = [dict(file=f.file, line=f.line, rule=f.rule, severity=f.severity, summary=f.summary) for f in findings]
        Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

