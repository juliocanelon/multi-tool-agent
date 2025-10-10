from pathlib import Path
from .agents.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
root_agent = Orchestrator(BASE_DIR)  # ADK prioriza agent.root_agent
