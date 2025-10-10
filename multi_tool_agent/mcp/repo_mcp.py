from pathlib import Path
import csv

class RepoMCP:
    """
    'MCP casero' para exponer utilidades del repo y del CSV de hallazgos.
    """
    def __init__(self, base_dir:Path):
        self.base = base_dir
        self.data = base_dir/"data"
        self.work = base_dir/"workdir"

    def list_repo_files(self, relative=True):
        files=[]
        for p in self.work.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                files.append(str(p.relative_to(self.work) if relative else p))
        return files

    def read_checkmarx_csv(self):
        path = self.data/"checkmarx.csv"
        out=[]
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    out.append(row)
        return out
