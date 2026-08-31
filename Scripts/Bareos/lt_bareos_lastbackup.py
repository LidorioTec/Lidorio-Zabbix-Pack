#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LT Bareos - Last successful backup per client (v0.7.0, lib_lt refactor)"""
import os, subprocess, sys

sys.path.insert(0, "/etc/zabbix/lib")
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

LOG = lib_lt.get_logger("bareos")
CONF_PATH = "/etc/zabbix/scripts/lt_bareos.conf"
DEFAULTS = {"db_host": "127.0.0.1", "db_name": "bareos",
            "db_user": "zabbix_ro", "password": ""}

def main():
    if len(sys.argv) < 2:
        lib_lt.emit(0)
    client = sys.argv[1]

    cfg = lib_lt.load_config(CONF_PATH, DEFAULTS)
    sql = ("SELECT COALESCE(EXTRACT(EPOCH FROM max(endtime)),0) "
           "FROM job j JOIN client cl ON j.clientid=cl.clientid "
           "WHERE cl.name='" + client.replace("'", "''") + "' "
           "AND j.jobstatus='T' AND j.type='B'")

    env = os.environ.copy()
    env["PGPASSWORD"] = cfg["password"]
    try:
        r = subprocess.run(["psql", "-h", cfg["db_host"], "-U", cfg["db_user"],
                            "-d", cfg["db_name"], "-t", "-A", "-c", sql],
                           capture_output=True, text=True, env=env, timeout=10)
        out = r.stdout.strip()
        result = int(float(out)) if out else 0
        LOG.info(f"client={client} last_success_epoch={result}")
        lib_lt.emit(result)
    except subprocess.TimeoutExpired:
        LOG.error(f"client={client} psql timeout")
        lib_lt.emit(0)
    except Exception as e:
        LOG.error(f"client={client} error={e}")
        lib_lt.emit(0)

if __name__ == "__main__":
    main()
