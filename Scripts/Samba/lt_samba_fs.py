#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LT Samba FS Collector - LIDORIO TECH v0.9.0-wip
Modern Samba File Server monitoring (SMB/CIFS shares).

Irmao do LT Samba AD: cobre a role File Server
(smbd/nmbd, shares, sessions, locks), NAO Active Directory.

Fases V1: (a) health/config -> (c) shares -> (b) sessions/locks.
Regra de ouro: metrica nao confiavel nao entra no template.
"""

import json
import os
import sys

sys.path.insert(0, "/etc/zabbix/lib")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

from lt_samba import collector, config, discovery, health, shares

LOG = lib_lt.get_logger("samba_fs")

CONF_FILE = "/etc/zabbix/scripts/lt_samba_fs.conf"
DEFAULTS = {
    "cache_ttl_health": "60",
    "cache_ttl_config": "300",
    "cache_ttl_shares": "300",
}


def load_config():
    return lib_lt.load_config(CONF_FILE, DEFAULTS)


def main():
    if len(sys.argv) < 2:
        print("Uso: lt_samba_fs.py <ping|version|health|config|discover_shares|share_detail>")
        sys.exit(1)

    cfg = load_config()
    cmd = sys.argv[1]

    try:
        if cmd == "ping":
            h = collector.get_cached("health", int(cfg["cache_ttl_health"]),
                                     health.collect_health)
            c = collector.get_cached("config", int(cfg["cache_ttl_config"]),
                                     config.validate_config)
            lib_lt.emit(1 if h.get("smbd") == 1 and c.get("status") == 0
                        else 0)

        elif cmd == "version":
            h = collector.get_cached("health", int(cfg["cache_ttl_health"]),
                                     health.collect_health)
            lib_lt.emit(h.get("version", "unknown"))

        elif cmd == "health" and len(sys.argv) == 3:
            h = collector.get_cached("health", int(cfg["cache_ttl_health"]),
                                     health.collect_health)
            lib_lt.emit(h.get(sys.argv[2], -1))

        elif cmd == "config":
            c = collector.get_cached("config", int(cfg["cache_ttl_config"]),
                                     config.validate_config)
            lib_lt.emit(c.get("status", 1))

        elif cmd == "discover_shares":
            d = collector.get_cached("shares", int(cfg["cache_ttl_shares"]),
                                     discovery.discover_shares_json)
            print(d)

        elif cmd == "share_detail" and len(sys.argv) == 4:
            # usage: share_detail <sharename> <field>
            d = collector.get_cached("shares", int(cfg["cache_ttl_shares"]),
                                     lambda: shares.discover())
            target = sys.argv[2]
            field = sys.argv[3]
            for s in d["shares"]:
                if s["name"] == target:
                    lib_lt.emit(s.get(field, "unknown"))
                    return
            lib_lt.emit("unknown")

        else:
            print("ZBX_NOTSUPPORTED")
            sys.exit(1)
    except Exception as e:
        LOG.error(f"unhandled exception: {e}")
        print("ZBX_NOTSUPPORTED")
        sys.exit(1)


if __name__ == "__main__":
    main()
