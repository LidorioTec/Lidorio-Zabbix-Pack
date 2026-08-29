#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LT Bareos - Last successful backup per client (v0.6.0)"""
import os, subprocess, sys

CONF = "/etc/zabbix/scripts/lt_bareos.conf"

def load_conf():
    c = {"db_host": "127.0.0.1", "db_name": "bareos",
         "db_user": "zabbix_ro", "password": ""}
    try:
        with open(CONF) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    c[k.strip()] = v.strip()
    except Exception:
        pass
    return c

def main():
    if len(sys.argv) < 2:
        print(0); return
    client = sys.argv[1]
    c = load_conf()
    sql = ("SELECT COALESCE(EXTRACT(EPOCH FROM max(endtime)),0) "
           "FROM job j JOIN client cl ON j.clientid=cl.clientid "
           "WHERE cl.name='" + client.replace("'", "''") + "' "
           "AND j.jobstatus='T' AND j.type='B'")
    env = os.environ.copy()
    env["PGPASSWORD"] = c["password"]
    try:
        r = subprocess.run(["psql", "-h", c["db_host"], "-U", c["db_user"],
                            "-d", c["db_name"], "-t", "-A", "-c", sql],
                           capture_output=True, text=True, env=env, timeout=10)
        out = r.stdout.strip()
        print(int(float(out)) if out else 0)
    except Exception:
        print(0)

if __name__ == "__main__":
    main()
