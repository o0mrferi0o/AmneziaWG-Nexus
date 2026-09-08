from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

@dataclass(frozen=True)
class Profile:
    name: str
    path: Path
    interface: str
    endpoint: str = ""
    valid: bool = True
    errors: tuple[str, ...] = ()

@dataclass
class ConnectionDetails:
    interface: str = "—"
    tunnel_ip: str = "—"
    endpoint: str = "—"
    handshake: str = "—"
    rx: int = 0
    tx: int = 0
    allowed_ips: str = "—"
    public_ip: str = "—"
