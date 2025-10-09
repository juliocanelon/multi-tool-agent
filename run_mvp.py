from pathlib import Path
from agents.orchestrator import Orchestrator
import json, sys

BASE = Path(__file__).resolve().parent
_orch = Orchestrator(BASE)

def app():
    """
    Entry-point para ADK Web: retorna un objeto con método handle(str)->dict.
    """
    return _orch

if __name__ == "__main__":
    user_text = " ".join(sys.argv[1:]) or "Escanea y corrige HIGH en DEFAULT repo branch main proyecto Cx-123"
    out = _orch.handle(user_text)
    print(json.dumps(out, indent=2, ensure_ascii=False))
