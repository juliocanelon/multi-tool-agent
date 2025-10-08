import subprocess, shlex, logging
from typing import Tuple, Optional

log = logging.getLogger("shell")

def run(cmd: str, cwd: Optional[str]=None, timeout: Optional[int]=None) -> Tuple[int,str,str]:
    log.info(f"$ {cmd}")
    p = subprocess.run(shlex.split(cmd), cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if p.stdout: log.info(p.stdout.strip())
    if p.stderr: log.warning(p.stderr.strip())
    return p.returncode, p.stdout, p.stderr
