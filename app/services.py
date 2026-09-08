from __future__ import annotations
import configparser
import ipaddress
import re
from pathlib import Path
from .models import ConnectionDetails, Profile
from .security import PROFILE_DIRECTORY, run_command, safe_profile_path

REQUIRED = {"Interface": ("PrivateKey", "Address"), "Peer": ("PublicKey", "AllowedIPs")}

def validate_profile(path: Path, root: Path = PROFILE_DIRECTORY) -> tuple[bool, tuple[str, ...], dict[str, str]]:
    try:
        path = safe_profile_path(path, root)
        raw = path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return False, ("Profile cannot be read",), {}
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try: parser.read_string(raw)
    except configparser.Error: return False, ("Invalid configuration format",), {}
    errors = [f"Missing required field: {field}" for section, fields in REQUIRED.items() for field in fields if not parser.has_option(section, field)]
    # Return only non-secret metadata.
    metadata = {"address": parser.get("Interface", "Address", fallback=""), "endpoint": parser.get("Peer", "Endpoint", fallback="")}
    return not errors, tuple(errors), metadata

def discover_profiles(root: Path = PROFILE_DIRECTORY) -> list[Profile]:
    if not root.is_dir(): return []
    profiles = []
    for path in sorted(root.glob("*.conf"), key=lambda item: item.name.casefold()):
        if path.parent != root: continue
        valid, errors, metadata = validate_profile(path, root)
        profiles.append(Profile(path.stem, path, path.stem, metadata["endpoint"], valid, errors))
    return profiles

def parse_awg_show(output: str, interface: str) -> ConnectionDetails:
    details = ConnectionDetails(interface=interface)
    endpoint = re.search(r"endpoint:\s*(.+)", output)
    handshake = re.search(r"latest handshake:\s*(.+)", output)
    allowed = re.search(r"allowed ips:\s*(.+)", output)
    transfer = re.search(r"transfer:\s*([0-9.]+)\s*(\w+) received,\s*([0-9.]+)\s*(\w+) sent", output)
    details.endpoint = endpoint.group(1).strip() if endpoint else "—"
    details.handshake = handshake.group(1).strip() if handshake else "Never"
    details.allowed_ips = allowed.group(1).strip() if allowed else "—"
    if transfer:
        details.rx = int(float(transfer.group(1)) * _unit(transfer.group(2)))
        details.tx = int(float(transfer.group(3)) * _unit(transfer.group(4)))
    return details

def _unit(value: str) -> int:
    return {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}.get(value, 1)

class AWGService:
    def active_interfaces(self) -> list[str]:
        result = run_command(["awg", "show", "interfaces"], timeout=5)
        return result.stdout.split() if result.returncode == 0 else []
    def details(self, interface: str) -> ConnectionDetails:
        result = run_command(["awg", "show", interface], timeout=5)
        details = parse_awg_show(result.stdout, interface)
        address = run_command(["ip", "-4", "-o", "addr", "show", "dev", interface], timeout=5)
        match = re.search(r"inet\s+(\S+)", address.stdout)
        details.tunnel_ip = match.group(1) if match else "—"
        return details
    def public_ip(self) -> str:
        for url in ("https://api.ipify.org", "https://icanhazip.com"):
            result = run_command(["curl", "-4", "--max-time", "4", "-fsS", url], timeout=6)
            try: return str(ipaddress.IPv4Address(result.stdout.strip()))
            except ipaddress.AddressValueError: pass
        return "Unavailable"
