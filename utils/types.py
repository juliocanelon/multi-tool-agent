from pydantic import BaseModel
from typing import List, Optional

class Intent(BaseModel):
    repo_url: str
    branch: str
    levels: List[str]
    policy: dict

class Finding(BaseModel):
    file: str
    line: int
    type: str
    severity: str
    desc: str

class FixPlan(BaseModel):
    findings: List[Finding]
    guidance: List[str]
    tests_cmd: str

class FixResult(BaseModel):
    status: str              # SUCCESS | PARTIAL | FAIL
    diff: str                # unified diff
    stdout: str = ""
    stderr: str = ""

class VerifyReport(BaseModel):
    tests_passed: bool
    cmd_used: str
    logs: str
