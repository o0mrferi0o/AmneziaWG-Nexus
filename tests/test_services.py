from app.models import ConnectionState
from app.core import StateManager
from app.security import safe_profile_path
from app.services import parse_awg_show

def test_parse_show():
    d=parse_awg_show("peer: x\n endpoint: 203.0.113.9:51820\n allowed ips: 0.0.0.0/0\n latest handshake: 9 seconds ago\n transfer: 1.5 MiB received, 4 KiB sent", "awg0")
    assert (d.endpoint,d.handshake,d.rx,d.tx)==("203.0.113.9:51820","9 seconds ago",1572864,4096)

def test_profile_path_blocks_traversal(tmp_path):
    try: safe_profile_path(tmp_path / "bad.conf", tmp_path / "other")
    except ValueError: pass
    else: assert False

def test_state_transitions():
    state=StateManager(); state.transition(ConnectionState.CONNECTING); state.transition(ConnectionState.CONNECTED)
