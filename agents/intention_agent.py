from utils.types import Intent


class IntentionAgent:
    """En v1, parsea directo desde la config; en v2, LLM a JSON."""

    def from_config(self, cfg: dict) -> Intent:
        return Intent(
            repo_url=cfg["repo"]["url"],
            branch=cfg["repo"]["branch"],
            levels=cfg["vulns"]["severities"],
            policy=cfg.get("policy", {})
        )
