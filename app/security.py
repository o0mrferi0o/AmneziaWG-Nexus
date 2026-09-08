"""Boundary checks for all local privileged operations."""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Sequence

PROFILE_DIRECTORY = Path("/etc/amnezia")

def safe_profile_path(path: Path | str, root: Path = PROFILE_DIRECTORY) -> Path:
    root = root.resolve()
    resolved = Path(path).resolve()
    if resolved.parent != root or resolved.suffix != ".conf":
        raise ValueError("Profile must be a .conf file directly inside /etc/amnezia")
    return resolved

def run_command(command: Sequence[str], *, timeout: int = 12, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run an explicit argv safely; shell expansion is never permitted."""
    return subprocess.run(list(command), text=True, capture_output=True, timeout=timeout, check=check, shell=False)

def privileged_awg_quick(action: str, profile_path: Path) -> list[str]:
    if action not in {"up", "down"}:
        raise ValueError("Invalid awg-quick action")
    return ["pkexec", "awg-quick", action, str(safe_profile_path(profile_path))]
