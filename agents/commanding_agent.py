from pathlib import Path

def _comment_prefix(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".java", ".js", ".ts", ".c", ".cpp", ".go", ".kt", ".swift"]:
        return "//"
    if ext in [".py", ".rb", ".sh", ".yaml", ".yml", ".toml"]:
        return "#"
    if ext in [".xml", ".html"]:
        return "<!--"
    return "//"

def _comment_suffix(path: Path) -> str:
    return " -->" if path.suffix.lower() in [".xml", ".html"] else ""

class CommandingAgent:
    def __init__(self, workdir:Path):
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)

    def dry_run(self, instruction_md:str) -> dict:
        (self.workdir/"instruction.md").write_text(instruction_md, encoding="utf-8")
        (self.workdir/"stdout.log").write_text("SIMULATED: fix attempt ok", encoding="utf-8")
        (self.workdir/"stderr.log").write_text("", encoding="utf-8")
        return {"status":"SIMULATED_OK","stdout":"SIMULATED: fix attempt ok"}

    def apply_naive_fix(self, findings: list, repo_root: Path) -> dict:
        """
        Inserta un comentario junto a la línea reportada. Si la línea es 0 o inválida,
        inserta al principio del archivo. Genera 'changelog.md'.
        """
        changed = []
        skipped = []
        for fx in findings:
            target = (repo_root / fx.file).resolve()
            if not target.exists() or not target.is_file():
                skipped.append({"file": fx.file, "reason":"not found"})
                continue
            try:
                content = target.read_text(encoding="utf-8").splitlines()
            except Exception as e:
                skipped.append({"file": fx.file, "reason": f"read error: {e}"})
                continue

            prefix = _comment_prefix(target)
            suffix = _comment_suffix(target)
            note = f"{prefix} AUTO-FIX (naive) {fx.rule}: {fx.summary}{suffix}"

            idx = max(0, min((fx.line - 1) if isinstance(fx.line, int) and fx.line > 0 else 0, len(content)))
            # inserta arriba de la línea si existe
            content.insert(idx, note)

            try:
                target.write_text("\n".join(content) + "\n", encoding="utf-8")
                changed.append({"file": fx.file, "line": fx.line, "rule": fx.rule})
            except Exception as e:
                skipped.append({"file": fx.file, "reason": f"write error: {e}"})
                continue

        # changelog
        cl = ["# Changelog (naive)", ""]
        if changed:
            cl.append("## Archivos modificados")
            for c in changed:
                cl.append(f"- {c['file']} (línea {c['line']}, regla {c['rule']})")
        if skipped:
            cl += ["", "## Saltados", *[f"- {s['file']}: {s['reason']}" for s in skipped]]
        (self.workdir/"changelog.md").write_text("\n".join(cl) + "\n", encoding="utf-8")

        # log para verificación
        (self.workdir/"stdout.log").write_text(
            f"NAIVE_FIX: changed={len(changed)} skipped={len(skipped)}", encoding="utf-8"
        )
        return {"status":"NAIVE_OK", "changed": len(changed), "skipped": skipped}
