from pathlib import Path
from typing import List

from jinja2 import Template

from utils.types import Finding, FixPlan

_MD_TEMPLATE = """# Code Fix Plan (Security)

## Context
Repo: {{ repo }}
Branch: {{ branch }}
Target branch: {{ target_branch }}

## Findings ({{ findings|length }})
{% for f in findings -%}
- File: {{f.file}} (line {{f.line}}), Severity: {{f.severity}}, Type: {{f.type}}
  Desc: {{f.desc}}
{% endfor %}

## Requirements
- Minimizar cambios; mantener estilo del proyecto.
- Evitar hardcode de credenciales; usar configuración/secretos.
- Validar/sanitizar inputs; manejar nulos y límites.
- Añadir/actualizar tests si corresponde.

## Commands
Run tests: `{{ tests_cmd }}`

## Deliverables
- Unified diff patch (git format)
- Resumen de pruebas
"""


class ScanResearchAgent:
    def build_plan(
        self,
        findings: List[Finding],
        repo: str,
        branch: str,
        target_branch: str,
        tests_cmd: str,
    ) -> FixPlan:
        guidance = [
            "evitar hardcode; usar variables de entorno o propiedades seguras",
            "sanitizar y validar entradas antes de usarlas",
            "manejar excepciones y nulos explícitamente",
        ]
        return FixPlan(findings=findings, guidance=guidance, tests_cmd=tests_cmd)

    def render_instruction(
        self,
        plan: FixPlan,
        repo: str,
        branch: str,
        target_branch: str,
        out_path: str,
    ) -> Path:
        tpl = Template(_MD_TEMPLATE)
        md = tpl.render(
            repo=repo,
            branch=branch,
            target_branch=target_branch,
            findings=plan.findings,
            tests_cmd=plan.tests_cmd,
        )
        p = Path(out_path)
        p.write_text(md, encoding="utf-8")
        return p
