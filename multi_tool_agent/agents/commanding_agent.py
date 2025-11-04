import difflib
import os
import subprocess
import textwrap
from collections import defaultdict
from pathlib import Path

from .repo_agent import RepoAgent


def _comment_prefix(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".java", ".js", ".jsx", ".tsx", ".ts", ".c", ".cpp", ".cs", ".go", ".kt", ".swift"]:
        return "//"
    if ext in [".py", ".rb", ".sh", ".bash", ".ps1", ".yaml", ".yml", ".toml"]:
        return "#"
    if ext in [".xml", ".html"]:
        return "<!--"
    if ext in [".php"]:
        return "//"
    return "//"


def _comment_suffix(path: Path) -> str:
    return " -->" if path.suffix.lower() in [".xml", ".html"] else ""


class CommandingAgent:
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)

    def dry_run(self, instruction_md: str) -> dict:
        (self.workdir / "instruction.md").write_text(instruction_md, encoding="utf-8")
        (self.workdir / "stdout.log").write_text("SIMULATED: fix attempt ok", encoding="utf-8")
        (self.workdir / "stderr.log").write_text("", encoding="utf-8")
        return {"status": "SIMULATED_OK", "stdout": "SIMULATED: fix attempt ok"}

    # --- Automated fixer helpers -------------------------------------------------

    def _build_guard_lines(self, target: Path, original_line: str, summary: str) -> list[str]:
        indent = original_line[: len(original_line) - len(original_line.lstrip(" \t"))]
        stripped = original_line.strip()
        prefix = _comment_prefix(target)
        suffix = _comment_suffix(target)
        msg = summary or "Security safeguard inserted automatically"
        msg = " ".join(msg.split())
        msg_short = msg[:220]
        escaped_double = msg_short.replace("\"", "\\\"")

        comment_line = None
        if stripped:
            comment_line = f"{indent}{prefix} Disabled insecure code: {stripped}{suffix}".rstrip()

        ext = target.suffix.lower()
        replacement: str
        if ext == ".py":
            replacement = f'{indent}raise RuntimeError("AUTO_FIX mitigated: {escaped_double}")'
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            replacement = f'{indent}throw new Error("AUTO_FIX mitigated: {escaped_double}");'
        elif ext in {".java", ".kt"}:
            replacement = f'{indent}throw new RuntimeException("AUTO_FIX mitigated: {escaped_double}");'
        elif ext == ".go":
            replacement = f'{indent}panic("AUTO_FIX mitigated: {escaped_double}")'
        elif ext in {".rb"}:
            replacement = f'{indent}raise "AUTO_FIX mitigated: {escaped_double}"'
        elif ext == ".php":
            replacement = f'{indent}throw new \\RuntimeException("AUTO_FIX mitigated: {escaped_double}");'
        elif ext in {".swift"}:
            replacement = f'{indent}fatalError("AUTO_FIX mitigated: {escaped_double}")'
        elif ext in {".cs"}:
            replacement = f'{indent}throw new System.Exception("AUTO_FIX mitigated: {escaped_double}");'
        elif ext in {".c", ".cpp", ".h", ".hpp"}:
            replacement = f'{indent}#error "AUTO_FIX mitigated: {escaped_double}"'
        elif ext in {".sh", ".bash"}:
            replacement = f'{indent}echo "AUTO_FIX mitigated: {escaped_double}" 1>&2; exit 1'
        elif ext == ".ps1":
            replacement = f'{indent}throw "AUTO_FIX mitigated: {escaped_double}"'
        elif ext in {".yaml", ".yml"}:
            replacement = f'{indent}auto_fix_block: "{escaped_double}"'
        elif ext == ".toml":
            replacement = f'{indent}auto_fix_block = "{escaped_double}"'
        elif ext in {".json"}:
            replacement = f'{indent}"auto_fix_block": "{escaped_double}"'
        elif ext in {".xml", ".html"}:
            replacement = f'{indent}<div data-auto-fix="blocked">AUTO_FIX mitigated: {escaped_double}</div>'
        else:
            replacement = f'{indent}/* AUTO_FIX mitigated: {escaped_double} */'

        new_lines: list[str] = []
        if comment_line:
            new_lines.append(comment_line)
        new_lines.append(replacement)
        return new_lines

    def _determine_validation_command(self, repo_root: Path) -> str | None:
        env_cmd = os.getenv("CODE_FIX_VALIDATE", "").strip()
        if env_cmd:
            return env_cmd

        if (repo_root / "package.json").exists():
            return os.getenv("CODE_FIX_NPM_CMD", "npm test --silent")
        if (repo_root / "pom.xml").exists():
            return os.getenv("CODE_FIX_MVN_CMD", "mvn -B test")
        if (repo_root / "gradlew").exists():
            return os.getenv("CODE_FIX_GRADLE_CMD", "./gradlew test")
        if (repo_root / "build.gradle").exists():
            return os.getenv("CODE_FIX_GRADLE_CMD", "gradle test")
        if (repo_root / "Makefile").exists():
            return os.getenv("CODE_FIX_MAKE_CMD", "make test")
        if (repo_root / "pytest.ini").exists() or (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
            return os.getenv("CODE_FIX_PYTEST_CMD", "pytest")
        return None

    def _run_validation(self, command: str, repo_root: Path) -> dict:
        try:
            proc = subprocess.run(
                command,
                cwd=repo_root,
                shell=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            return {
                "ok": False,
                "error": f"Validation command not found: {exc}",
                "stdout": "",
                "stderr": str(exc),
                "returncode": 127,
            }
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "returncode": proc.returncode,
        }

    # --- Main entry point -------------------------------------------------------

    def apply_naive_fix(self, findings: list, repo_root: Path) -> dict:
        """Apply protective edits based on findings and validate the result."""

        repo_root = repo_root.resolve()
        backups: dict[Path, str] = {}
        patches: dict[Path, str] = {}
        changed: list[dict[str, object]] = []
        skipped: list[dict[str, object]] = []

        grouped: dict[str, list] = defaultdict(list)
        for fx in findings:
            if not fx.file:
                skipped.append({"file": fx.file, "reason": "empty path"})
                continue
            grouped[fx.file].append(fx)

        for rel, file_findings in grouped.items():
            target = (repo_root / rel).resolve()
            if not target.exists() or not target.is_file():
                skipped.append({"file": rel, "reason": "not found"})
                continue

            try:
                original = target.read_text(encoding="utf-8")
            except Exception as exc:
                skipped.append({"file": rel, "reason": f"read error: {exc}"})
                continue

            backups.setdefault(target, original)
            lines = original.splitlines()

            for fx in sorted(file_findings, key=lambda f: f.line or 0):
                idx = fx.line - 1 if isinstance(fx.line, int) and fx.line > 0 else len(lines)
                idx = max(0, min(idx, len(lines)))
                original_line = lines[idx] if idx < len(lines) else ""
                new_lines = self._build_guard_lines(target, original_line, fx.summary or fx.rule)

                if idx < len(lines):
                    lines[idx : idx + 1] = new_lines
                else:
                    lines.extend(new_lines)

                changed.append({"file": rel, "line": fx.line, "rule": fx.rule})

            new_content = "\n".join(lines) + "\n"
            try:
                target.write_text(new_content, encoding="utf-8")
            except Exception as exc:
                skipped.append({"file": rel, "reason": f"write error: {exc}"})
                original_content = backups.pop(target, None)
                if original_content is not None:
                    target.write_text(original_content, encoding="utf-8")
                continue

            diff = "\n".join(
                difflib.unified_diff(
                    original.splitlines(),
                    new_content.splitlines(),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="",
                )
            )
            patches[target] = diff

        validation_cmd = self._determine_validation_command(repo_root)
        validation_result = None
        if validation_cmd:
            validation_result = self._run_validation(validation_cmd, repo_root)
        else:
            validation_result = {
                "ok": True,
                "stdout": "",
                "stderr": "",
                "returncode": 0,
                "skipped": True,
                "reason": "No validation command detected",
            }

        success = bool(changed) and validation_result.get("ok", False)

        if not success:
            # revert
            for path, content in backups.items():
                path.write_text(content, encoding="utf-8")
            changed = []
            patches = {}

        # changelog
        cl_lines = ["# Changelog (automated)", ""]
        if changed:
            cl_lines.append("## Archivos modificados")
            for entry in changed:
                cl_lines.append(
                    f"- {entry['file']} (línea {entry['line']}, regla {entry['rule']})"
                )
        else:
            cl_lines.append("No se aplicaron cambios debido a validación fallida o ausencia de hallazgos.")
        if skipped:
            cl_lines += ["", "## Saltados", *[f"- {s['file']}: {s['reason']}" for s in skipped]]
        (self.workdir / "changelog.md").write_text("\n".join(cl_lines) + "\n", encoding="utf-8")

        # commit if success
        commit_log: dict[str, object] | None = None
        if success:
            repo_agent = RepoAgent(repo_root)
            commit_log = repo_agent.commit_all(
                message="chore(ai-fix): automated safeguard",
                author_name=os.getenv("GIT_AUTHOR_NAME", "CodeFix Bot"),
                author_email=os.getenv("GIT_AUTHOR_EMAIL", "bot@local"),
            )

        status = "FIXED" if success else "FAILED"
        stdout_summary = textwrap.shorten(
            validation_result.get("stdout", "") if validation_result else "",
            width=400,
            placeholder="...",
        )
        stderr_summary = textwrap.shorten(
            validation_result.get("stderr", "") if validation_result else "",
            width=400,
            placeholder="...",
        )
        log_line = f"CODE_FIX: status={status} changed={len(changed)} skipped={len(skipped)}"
        if validation_cmd:
            log_line += f" validate='{validation_cmd}' rc={validation_result.get('returncode')}"
        (self.workdir / "stdout.log").write_text(log_line, encoding="utf-8")
        (self.workdir / "stderr.log").write_text(
            (stdout_summary + "\n" + stderr_summary).strip(), encoding="utf-8"
        )

        return {
            "status": status,
            "changed": len(changed),
            "skipped": skipped,
            "patches": {str(p.relative_to(repo_root)): diff for p, diff in patches.items()},
            "validation": validation_result,
            "commit": commit_log,
        }

    def run_in_docker(self, image: str, workdir: Path, data_dir: Path) -> dict:
        """
        Ejecuta el script naive dentro del contenedor.
        Monta:
          - workdir -> /workspace
          - data    -> /data
        Llama: python /app/tools/naive_fix.py /workspace /data/findings.json /workspace/stdout.log /workspace/changelog.md
        """
        # Normaliza rutas absolutas (Windows friendly)
        wabs = str(workdir.resolve())
        dabs = str(data_dir.resolve())

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{wabs}:/workspace",
            "-v", f"{dabs}:/data",
            image,
            "bash", "-lc",
            "python /app/tools/naive_fix.py /workspace /data/findings.json /workspace/stdout.log /workspace/changelog.md"
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
            out = (self.workdir/"stdout.log").read_text(encoding="utf-8") if (self.workdir/"stdout.log").exists() else ""
            return {
                "status": "DOCKER_OK" if proc.returncode == 0 else "DOCKER_ERROR",
                "code": proc.returncode,
                "docker_stdout": proc.stdout[-500:],
                "docker_stderr": proc.stderr[-500:],
                "agent_stdout": out[-500:]
            }
        except FileNotFoundError:
            return {"status": "DOCKER_NOT_FOUND", "hint": "Instala Docker Desktop o agrega 'docker' al PATH."}