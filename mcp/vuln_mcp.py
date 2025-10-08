import csv
from pathlib import Path
from typing import List

from utils.types import Finding


class VulnMCP:
    def load_findings(self, csv_path: str, severities: list[str]) -> List[Finding]:
        rows = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("Severity") in severities:
                    rows.append(
                        Finding(
                            file=row.get("File", ""),
                            line=int(row.get("Line") or 0),
                            type=row.get("Type", ""),
                            severity=row.get("Severity", ""),
                            desc=row.get("Description", "").strip(),
                        )
                    )
        return rows
