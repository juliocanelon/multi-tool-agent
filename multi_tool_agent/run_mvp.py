"""Entry point for running the Code Fix Agent MVP."""
from __future__ import annotations

import argparse
import logging
import logging.config
from pathlib import Path
from typing import Any, Dict

import yaml

from multi_tool_agent.agents import (
    CommandingAgent,
    IntentionAgent,
    Orchestrator,
    RepoAgent,
    ScanResearchAgent,
    VerifyAgent,
)
from multi_tool_agent.utils.types import (
    CommandingConfig,
    MVPConfig,
    RepoConfig,
    VerificationConfig,
)

LOGGER = logging.getLogger(__name__)


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_config(config_path: Path) -> MVPConfig:
    raw = load_yaml(config_path)
    base_dir = config_path.parent

    stub_path = raw["commanding"].get("stub_diff_path")
    commanding_cfg = CommandingConfig(
        provider=raw["commanding"]["provider"],
        stub_diff_path=(base_dir / stub_path) if stub_path else None,
    )

    repo_cfg = RepoConfig(
        path=(base_dir / raw["repo"]["path"]).resolve(),
        base_branch=raw["repo"]["base_branch"],
        branch_prefix=raw["repo"]["branch_prefix"],
        push=bool(raw["repo"].get("push", False)),
        create_pr=bool(raw["repo"].get("create_pr", False)),
    )

    verification_cfg = VerificationConfig(
        enabled=bool(raw["verification"].get("enabled", False)),
        command=raw["verification"]["command"],
        working_directory=(base_dir / raw["verification"].get("working_directory", ".")).resolve(),
    )

    return MVPConfig(
        checkmarx_csv=(base_dir / raw["checkmarx_csv"]).resolve(),
        instruction_path=(base_dir / raw["instruction_path"]).resolve(),
        commanding=commanding_cfg,
        repo=repo_cfg,
        verification=verification_cfg,
    )


def configure_logging(logging_config_path: Path) -> None:
    if not logging_config_path.exists():
        logging.basicConfig(level=logging.INFO)
        LOGGER.warning("Logging config not found at %s. Using basicConfig().", logging_config_path)
        return

    config_dict = load_yaml(logging_config_path)
    logging.config.dictConfig(config_dict)


def main() -> None:
    package_root = Path(__file__).resolve().parent
    default_config = package_root / "config" / "mvp.yaml"
    default_logging_config = package_root / "config" / "logging.yaml"

    parser = argparse.ArgumentParser(description="Run the Code Fix Agent MVP workflow")
    parser.add_argument("--config", type=Path, default=default_config, help="Path to the MVP YAML config")
    parser.add_argument(
        "--logging-config", type=Path, default=default_logging_config, help="Path to logging configuration YAML"
    )
    args = parser.parse_args()

    configure_logging(args.logging_config)
    LOGGER.info("Loading configuration from %s", args.config)
    config = load_config(args.config)

    intention_agent = IntentionAgent(config)
    scan_agent = ScanResearchAgent()
    commanding_agent = CommandingAgent(config.commanding)
    repo_agent = RepoAgent(config.repo)
    verify_agent = VerifyAgent(config.verification)

    orchestrator = Orchestrator(
        config,
        intention_agent=intention_agent,
        scan_agent=scan_agent,
        commanding_agent=commanding_agent,
        repo_agent=repo_agent,
        verify_agent=verify_agent,
    )

    result = orchestrator.run()

    LOGGER.info("Remediation plan saved to %s", result.plan.plan_path)
    if result.commanding_response.diff:
        LOGGER.info("Diff successfully applied using provider %s", result.commanding_response.provider)
    else:
        LOGGER.warning("No diff applied during this run")

    if result.verification:
        LOGGER.info("Verification status: %s", "passed" if result.verification.succeeded else "failed")


if __name__ == "__main__":
    main()

