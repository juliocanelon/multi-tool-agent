import logging
import os
from pathlib import Path

from utils.shell import run
from utils.types import FixResult


log = logging.getLogger("CommandingAgent")


class CommandingAgent:
    def __init__(self, mode: str, docker_image: str):
        self.mode = mode.upper()
        self.docker_image = docker_image

    def run(self, workdir: Path, instruction_md: Path, diff_format: str = "unified-diff") -> FixResult:
        if self.mode == "STUB":
            target = self._pick_any_java_file(workdir)
            if not target:
                return FixResult(status="FAIL", diff="", stdout="", stderr="no java file found")
            diff = f"""--- {target}
+++ {target}
@@
+// TODO: security hardening applied by AI agent
"""
            return FixResult(status="SUCCESS", diff=diff, stdout="stub diff", stderr="")
        elif self.mode == "DOCKER_GEMINI":
            cmd = (
                f"docker run --rm "
                f"-v {workdir}:/workspace "
                f"-v {instruction_md.parent}:/data "
                f"-v {Path.home() / '.config/gcloud'}:/root/.config/gcloud:ro "
                f"{self.docker_image} "
                f"code --repo /workspace --instruction /data/{instruction_md.name} --format {diff_format}"
            )
            rc, out, err = run(cmd)
            status = "SUCCESS" if rc == 0 and out.strip() else "FAIL"
            return FixResult(status=status, diff=out, stdout=out, stderr=err)
        else:
            return FixResult(status="FAIL", diff="", stdout="", stderr=f"unknown mode {self.mode}")

    def _pick_any_java_file(self, workdir: Path) -> str:
        for p in workdir.rglob("*.java"):
            rel = str(p.relative_to(workdir))
            return rel
        return ""
