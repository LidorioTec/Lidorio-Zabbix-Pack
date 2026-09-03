"""LT Samba FS - share discovery + status.

Estrategia de discovery (LIDORIO TECH):
1. testparm -s  (parse dos [share] sections) - sempre disponivel
2. net conf list  (registry backend, raro)
3. unsupported_config_backend

Para cada share, coletamos metadados ricos:
- path (caminho no filesystem)
- filesystem type (ext4/xfs/btrfs...)
- mounted (1/0)
- read_only (1/0)
- guest_ok (1/0) -> compliance check
- browseable, printable, etc.
"""

import os
import re

from . import utils

# Seccoes internas que NAO sao shares de usuario
INTERNAL = frozenset(["global", "homes", "printers", "print$"])


def _parse_testparm(text):
    """Parse de testparm -s: extrai secoes [share] com seus parametros."""
    shares = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        # [sharename]
        m = re.match(r"^\[([^\]]+)\]\s*$", line)
        if m:
            current = m.group(1)
            shares[current] = {}
            continue
        #   key = value
        if current and "=" in line:
            key, _, val = line.partition("=")
            shares[current][key.strip().lower()] = val.strip()
    return shares


def _net_conf_list():
    """net conf list -> output simples: sharename + path."""
    rc, out, _ = utils.run_cmd(["net", "conf", "list"])
    if rc != 0:
        return None
    shares = {}
    current = None
    for line in out.splitlines():
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            shares[current] = {}
        elif current and " " in line.strip():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                shares[current][parts[0].lower()] = parts[1]
    return shares


def _stat_bool(cfg, key, default):
    v = cfg.get(key, "").lower()
    if v in ("yes", "true", "1"):
        return True
    if v in ("no", "false", "0"):
        return False
    return default


def _fs_type(path):
    """Tipo de filesystem via /proc/mounts (sem subprocess)."""
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[1] == path:
                    return parts[2]
    except Exception:
        pass
    return "unknown"


def _mounted(path):
    """Verifica se path esta montado via /proc/mounts."""
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == path:
                    return 1
    except Exception:
        pass
    return 0


def discover():
    """Retorna lista de shares de usuario com metadados ricos."""
    rc, out, _ = utils.run_cmd(["testparm", "-s"])
    if rc == 127:
        parsed = _net_conf_list()
        method = "net_conf" if parsed else "unsupported"
    else:
        parsed = _parse_testparm(out)
        method = "testparm"

    if not parsed:
        return {"shares": [], "method": method, "count": 0}

    shares = []
    for name, cfg in parsed.items():
        if name.lower() in INTERNAL:
            continue
        path = cfg.get("path", "")
        shares.append({
            "{#SHARE}": name,
            "name": name,
            "path": path,
            "filesystem": _fs_type(path) if path else "unknown",
            "mounted": _mounted(path) if path else 0,
            "read_only": 1 if _stat_bool(cfg, "read only", False) else 0,
            "guest_ok": 1 if _stat_bool(cfg, "guest ok", False) else 0,
            "browseable": 1 if _stat_bool(cfg, "browseable", True) else 0,
            "printable": 1 if _stat_bool(cfg, "printable", False) else 0,
        })

    return {"shares": shares, "method": method, "count": len(shares)}
