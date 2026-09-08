from __future__ import annotations
import threading
from dataclasses import dataclass
from .models import ConnectionState, Profile
from .security import privileged_awg_quick, run_command
from .services import AWGService

@dataclass
class StateManager:
    state: ConnectionState = ConnectionState.DISCONNECTED
    error: str = ""
    active_profile: Profile | None = None
    def transition(self, new: ConnectionState) -> None:
        allowed = {ConnectionState.DISCONNECTED:{ConnectionState.CONNECTING}, ConnectionState.CONNECTING:{ConnectionState.CONNECTED,ConnectionState.ERROR}, ConnectionState.CONNECTED:{ConnectionState.DISCONNECTING}, ConnectionState.DISCONNECTING:{ConnectionState.DISCONNECTED,ConnectionState.ERROR}, ConnectionState.ERROR:{ConnectionState.DISCONNECTED,ConnectionState.CONNECTING}}
        if new not in allowed[self.state]: raise ValueError(f"Invalid state transition: {self.state} -> {new}")
        self.state = new

class ConnectionManager:
    def __init__(self, state: StateManager, service: AWGService | None = None):
        self.state, self.service, self._lock = state, service or AWGService(), threading.Lock()
    def connect(self, profile: Profile) -> None:
        if not profile.valid: raise ValueError(profile.errors[0] if profile.errors else "Invalid profile")
        if not self._lock.acquire(blocking=False): raise RuntimeError("Another VPN operation is already running")
        try:
            if self.state.state == ConnectionState.CONNECTED and self.state.active_profile != profile: self._down(self.state.active_profile)
            self.state.transition(ConnectionState.CONNECTING)
            result = run_command(privileged_awg_quick("up", profile.path), timeout=30)
            if result.returncode or profile.interface not in self.service.active_interfaces():
                self.state.state, self.state.error = ConnectionState.ERROR, "Unable to establish secure tunnel"
                return
            self.state.state, self.state.active_profile = ConnectionState.CONNECTED, profile
        finally: self._lock.release()
    def disconnect(self) -> None:
        if not self.state.active_profile: return
        if not self._lock.acquire(blocking=False): raise RuntimeError("Another VPN operation is already running")
        try: self._down(self.state.active_profile)
        finally: self._lock.release()
    def _down(self, profile: Profile | None) -> None:
        if not profile: return
        self.state.state = ConnectionState.DISCONNECTING
        result = run_command(privileged_awg_quick("down", profile.path), timeout=30)
        if result.returncode: self.state.state, self.state.error = ConnectionState.ERROR, "Unable to disconnect tunnel"
        else: self.state.state, self.state.active_profile = ConnectionState.DISCONNECTED, None
