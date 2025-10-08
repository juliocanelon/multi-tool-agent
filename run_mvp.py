import argparse
import logging
import logging.config
from pathlib import Path

import yaml
from dotenv import load_dotenv

from agents.orchestrator import Orchestrator


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/mvp.yaml")
    args = ap.parse_args()

    load_dotenv()
    log_cfg = yaml.safe_load(Path("config/logging.yaml").read_text())
    logging.config.dictConfig(log_cfg)

    cfg = yaml.safe_load(Path(args.config).read_text())
    orch = Orchestrator(cfg)
    result = orch.run()
    print(result)


if __name__ == "__main__":
    main()
