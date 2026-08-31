#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LT Bareos - LIDORIO TECH
Read-only collector for the Bareos catalog (PostgreSQL).
v0.7.0 (lib_lt refactor)
"""
import json, os, subprocess, sys, time

# Import lib_lt
sys.path.insert(0, "/etc/zabbix/lib")
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

LOG = lib_lt.get_logger("bareos")

CONF_FILE = "/etc/zabbix/scripts/lt_bareos.conf"
CACHE_FILE = "/var/lib/zabbix/lt_bareos.cache.json"
CACHE_TTL = 120

STATUS_MAP = {"T": 0, "W": 1, "E": 2, "f": 2}
NO_DATA = 99999

def load_conf():
    """Load config using lib_lt, with Bareos-specific defaults."""
    defaults = {"host": "127.0.0.1", "port": "5432", "db": "bareos",
                "user": "zabbix_ro", "password": ""}
    return lib_lt.load_config(CONF_FILE, defaults)

def sql(conf, query):
    env = dict(os.environ)
    env["PGPASSWORD"] = conf.get("password", "")
    res = subprocess.run(
        ["psql", "-h", conf["host"], "-p", conf["port"], "-U", conf["user"],
         "-d", conf["db"], "-t", "-A", "-F", "|", "-v", "ON_ERROR_STOP=1",
         "-c", query],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, env=env, timeout=30)
    if res.returncode != 0:
        LOG.error(f"SQL error: {res.stderr.strip()}")
        raise RuntimeError(res.stderr.strip())
    return [l.split("|") for l in res.stdout.splitlines() if l.strip()]

def build_data(conf):
    LOG.info("starting full catalog collection")
    now = int(time.time())
    data = {"ts": now, "clients": {}, "pools": {}}
    for r in sql(conf, "SELECT Name FROM Client ORDER BY Name"):
        data["clients"][r[0]] = {"lastgood": 0, "agegood": NO_DATA}
    rows = sql(conf, """
        SELECT DISTINCT ON (c.Name, j.Level) c.Name, j.Level, j.JobStatus,
          COALESCE(EXTRACT(EPOCH FROM j.EndTime)::bigint,0),
          COALESCE(j.JobBytes,0), COALESCE(j.JobFiles,0),
          COALESCE(EXTRACT(EPOCH FROM (j.EndTime - j.StartTime))::bigint,0)
        FROM Job j JOIN Client c ON c.ClientId = j.ClientId
        WHERE j.Type = 'B'
        ORDER BY c.Name, j.Level, j.EndTime DESC""")
    for r in rows:
        cname, level, st = r[0], r[1], r[2]
        end, byt, fil, dur = int(r[3]), int(r[4]), int(r[5]), int(r[6])
        data["clients"].setdefault(cname, {"lastgood": 0, "agegood": NO_DATA})
        data["clients"][cname][level] = {
            "status": STATUS_MAP.get(st, 3), "end": end, "bytes": byt,
            "files": fil, "dur": dur,
            "age": round((now - end) / 86400.0, 3) if end else NO_DATA}
    rows = sql(conf, """
        SELECT c.Name, COALESCE(MAX(EXTRACT(EPOCH FROM j.EndTime)::bigint),0)
        FROM Client c
        LEFT JOIN Job j ON j.ClientId = c.ClientId AND j.Type='B'
          AND j.JobStatus = 'T'
        GROUP BY c.Name""")
    for r in rows:
        if r[0] in data["clients"]:
            lg = int(r[1])
            data["clients"][r[0]]["lastgood"] = lg
            data["clients"][r[0]]["agegood"] = \
                round((now - lg) / 86400.0, 3) if lg else NO_DATA
    rows = sql(conf, """
        SELECT p.Name, COUNT(m.VolumeName), COALESCE(SUM(m.VolBytes),0)
        FROM Pool p LEFT JOIN Media m ON m.PoolId = p.PoolId
        GROUP BY p.Name ORDER BY p.Name""")
    for r in rows:
        data["pools"][r[0]] = {"volumes": int(r[1]), "bytes": int(r[2])}
    LOG.info(f"collected {len(data['clients'])} clients, {len(data['pools'])} pools")
    return data

def get_data(conf):
    try:
        with open(CACHE_FILE) as fh:
            cache = json.load(fh)
        if now_ts() - int(cache.get("ts", 0)) < CACHE_TTL:
            LOG.info("cache hit")
            return cache
    except (OSError, ValueError):
        pass
    data = build_data(conf)
    tmp = CACHE_FILE + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        os.replace(tmp, CACHE_FILE)
        LOG.info("cache saved (atomic)")
    except OSError as e:
        LOG.warning(f"cache write error: {e}")
    return data

def now_ts():
    return int(time.time())

def main():
    conf = load_conf()
    args = sys.argv[1:]
    if not args:
        lib_lt.emit(0)
        return
    cmd = args[0]
    if cmd == "ping":
        try:
            sql(conf, "SELECT 1")
            LOG.info("ping: 1")
            lib_lt.emit(1)
        except Exception as e:
            LOG.error(f"ping failed: {e}")
            lib_lt.emit(0)
        return
    data = get_data(conf)
    if cmd == "clients":
        lib_lt.emit(json.dumps({"data": [{"{#CLIENT}": c}
              for c in sorted(data["clients"])]}))
    elif cmd == "pools":
        lib_lt.emit(json.dumps({"data": [{"{#POOL}": p}
              for p in sorted(data["pools"])]}))
    elif cmd == "job" and len(args) == 4:
        lib_lt.emit(data["clients"].get(args[1], {}).get(args[2], {})
              .get(args[3], -1))
    elif cmd == "client" and len(args) == 3:
        lib_lt.emit(data["clients"].get(args[1], {}).get(args[2], -1))
    elif cmd == "pool" and len(args) == 3:
        lib_lt.emit(data["pools"].get(args[1], {}).get(args[2], -1))
    else:
        LOG.error(f"unknown command: {cmd}")
        lib_lt.emit(0)

if __name__ == "__main__":
    main()
