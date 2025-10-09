from pathlib import Path
from .agents.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
root_agent = Orchestrator(BASE_DIR)  # fallback si no usa agent.py
