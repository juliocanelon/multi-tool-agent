# docker/tools/naive_fix.py
from pathlib import Path
import json, sys

def comment_prefix(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in [".java", ".js", ".ts", ".c", ".cpp", ".go", ".kt", ".swift"]:
        return "//"
    if ext in [".py", ".rb", ".sh", ".yaml", ".yml", ".toml"]:
        return "#"
    if ext in [".xml", ".html"]:
        return "<!--"
    return "//"

def comment_suffix(p: Path) -> str:
    return " -->" if p.suffix.lower() in [".xml", ".html"] else ""

def main(workspace: Path, findings_json: Path, stdout_path: Path, changelog_path: Path):
    data = json.loads(findings_json.read_text(encoding="utf-8"))
    changed = []
    skipped = []

    for fx in data:
        target = (workspace / fx["file"]).resolve()
        if not target.exists() or not target.is_file():
            skipped.append({"file": fx["file"], "reason": "not found"})
            continue
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            skipped.append({"file": fx["file"], "reason": f"read error: {e}"})
            continue

        pref = comment_prefix(target)
        suff = comment_suffix(target)
        line = fx.get("line") or 0
        try:
            line = int(line)
        except:
            line = 0
        idx = max(0, min((line - 1) if line > 0 else 0, len(lines)))
        note = f"{pref} AUTO-FIX (naive docker) {fx.get('rule','')}: {fx.get('summary','')}{suff}"
        lines.insert(idx, note)

        try:
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            changed.append({"file": fx["file"], "line": line, "rule": fx.get("rule","")})
        except Exception as e:
            skipped.append({"file": fx["file"], "reason": f"write error: {e}"})

    # changelog
    cl = ["# Changelog (naive in Docker)", ""]
    if changed:
        cl.append("## Archivos modificados")
        for c in changed:
            cl.append(f"- {c['file']} (línea {c['line']}, regla {c['rule']})")
    if skipped:
        cl += ["", "## Saltados", *[f"- {s['file']}: {s['reason']}" for s in skipped]]
    changelog_path.write_text("\n".join(cl) + "\n", encoding="utf-8")

    stdout_path.write_text(f"NAIVE_FIX_DOCKER: changed={len(changed)} skipped={len(skipped)}", encoding="utf-8")

if __name__ == "__main__":
    # /app/tools/naive_fix.py /workspace /data/findings.json /workspace/stdout.log /workspace/changelog.md
    if len(sys.argv) < 5:
        print("usage: naive_fix.py <workspace> <findings.json> <stdout.log> <changelog.md>")
        sys.exit(2)
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
