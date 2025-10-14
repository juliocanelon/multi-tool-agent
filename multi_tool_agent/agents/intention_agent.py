import re
from dataclasses import dataclass, asdict
from typing import List, Literal, Optional

Severity = Literal["CRITICAL","HIGH","MEDIUM","LOW"]


@dataclass
class Intention:
    checkmarx_project_id: Optional[str] = ""
    repo_url: Optional[str] = ""
    branch: Optional[str] = ""
    severity_to_fix: List[Severity] = None
    notes: Optional[str] = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        # Normaliza listas None -> [] para evitar sorpresas aguas abajo
        if data.get("severity_to_fix") is None:
            data["severity_to_fix"] = []
        return data

SEV_MAP = {"CRITICAL","HIGH","MEDIUM","LOW","CRITICAS","ALTAS","MEDIAS","BAJAS"}

def normalize_sev(tokens: List[str]) -> List[Severity]:
    out = []
    for t in tokens:
        t=t.upper()
        t = {"CRITICAS":"CRITICAL","ALTAS":"HIGH","MEDIAS":"MEDIUM","BAJAS":"LOW"}.get(t,t)
        if t in {"CRITICAL","HIGH","MEDIUM","LOW"} and t not in out:
            out.append(t)
    return out

class IntentionAgent:
    """
    MVP: extrae repo, branch, severidades y proyecto Cx desde texto libre.
    Versión sin LLM para que corra YA; luego reemplazamos por Vertex.
    """
    RE_URL = re.compile(r"(https?://[^\s]+\.git|\b\S+@[^:\s]+:[^\s]+\.git)")
    RE_BRANCH = re.compile(r"\bbranch\s+([A-Za-z0-9_\-/\.]+)", re.IGNORECASE)
    RE_CX = re.compile(r"(?:proyecto|project|cx|checkmarx)\s*[:#\-]?\s*([A-Za-z0-9_\-]+)", re.IGNORECASE)

    def run(self, user_text:str, env_defaults:dict) -> Intention:
        repo = (self.RE_URL.search(user_text).group(0) if self.RE_URL.search(user_text) else env_defaults.get("DEFAULT_REPO_URL",""))
        branch = (self.RE_BRANCH.search(user_text).group(1) if self.RE_BRANCH.search(user_text) else env_defaults.get("DEFAULT_BRANCH",""))
        cx = (self.RE_CX.search(user_text).group(1) if self.RE_CX.search(user_text) else "")
        sev_tokens = [t.strip(",. ") for t in re.findall(r"\b(CRITICAL|HIGH|MEDIUM|LOW|críticas|altas|medias|bajas)\b", user_text, re.IGNORECASE)]
        sevs = normalize_sev(sev_tokens)
        if not sevs: sevs = ["CRITICAL","HIGH"]
        return Intention(checkmarx_project_id=cx, repo_url=repo, branch=branch, severity_to_fix=sevs, notes="")
