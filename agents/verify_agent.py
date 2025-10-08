from utils.shell import run
from utils.types import VerifyReport


class VerifyAgent:
    def run(self, workdir: str, tests_cmd: str, fallback_cmd: str) -> VerifyReport:
        rc, out, err = run(tests_cmd, cwd=workdir)
        cmd_used = tests_cmd
        if rc != 0:
            rc, out, err = run(fallback_cmd, cwd=workdir)
            cmd_used = fallback_cmd
        return VerifyReport(tests_passed=(rc == 0), cmd_used=cmd_used, logs=(out or "") + (err or ""))
