#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LT Samba AD Collector - LIDORIO TECH v0.8.0
Modern read-only LDAP monitoring for Samba4/AD Domain Controllers.

Exclusividades LIDORIO TECH vs. templates legados (Galvy 2021 et al.):
- Sem shell scripts, sem cron, sem sudo, sem subprocess samba-tool
- Discovery automatico de DCs via DNS SRV (_ldap._tcp)
- Queries LDAP diretas com bind read-only (rapido e remoto)
- Metricas exclusivas: FSMO mapping, tombstone lifetime, password
  policy compliance, contas locked/expired, functional level

Dependencias: pip3 install ldap3 dnspython
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, "/etc/zabbix/lib")
try:
    import lib_lt
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
    import lib_lt

LOG = lib_lt.get_logger("samba_ad")

CONF_FILE = "/etc/zabbix/scripts/lt_samba_ad.conf"
CACHE_FILE = "/tmp/lt_samba_ad.cache.json"

DEFAULTS = {
    "domain": "",            # ex: lab.lidorio.tech
    "bind_dn": "",           # ex: zabbix_ro@lab.lidorio.tech (read-only)
    "bind_password": "",
    "ldap_uri": "",          # opcional; vazio = auto-discover via SRV
    "cache_ttl": "120",
}

FUNCTIONAL_LEVELS = {0: "2000", 2: "2003", 3: "2008", 4: "2008R2",
                     5: "2012", 6: "2012R2", 7: "2016+"}

FSMO_TARGETS = [
    ("schema", "CN=Schema,CN=Configuration,{root}"),
    ("naming", "CN=Partitions,CN=Configuration,{root}"),
    ("pdc", "{root}"),
    ("rid", "CN=RID Manager$,CN=System,{root}"),
    ("infra", "CN=Infrastructure,{root}"),
]

# ---------------------------------------------------------------------------
# Config / cache
# ---------------------------------------------------------------------------
def load_config():
    return lib_lt.load_config(CONF_FILE, DEFAULTS)

def _read_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _write_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        LOG.warning(f"cache write error: {e}")

def get_cached(key, ttl, fn):
    cache = _read_cache()
    entry = cache.get(key)
    now = time.time()
    if entry and now - entry.get("ts", 0) < ttl:
        LOG.info(f"cache hit: {key}")
        return entry["val"]
    val = fn()
    cache[key] = {"ts": now, "val": val}
    _write_cache(cache)
    return val

# ---------------------------------------------------------------------------
# Conectores
# ---------------------------------------------------------------------------
def discover_dcs_dns(domain):
    """Lista de hostnames dos DCs via DNS SRV _ldap._tcp.<domain>."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(f"_ldap._tcp.{domain}", "SRV")
        dcs = sorted({str(r.target).rstrip(".").split(".")[0] for r in answers})
        LOG.info(f"DNS SRV discovered {len(dcs)} DC(s)")
        return dcs
    except Exception as e:
        LOG.error(f"DNS SRV discovery failed: {e}")
        return []

def ldap_connect(cfg, uri=None):
    """Conexao LDAP com bind read-only. Retorna Connection ou None."""
    try:
        import ldap3
        target = uri or cfg.get("ldap_uri") or f"ldap://{cfg['domain']}"
        server = ldap3.Server(target, connect_timeout=5, get_info=ldap3.NONE)
        conn = ldap3.Connection(server, user=cfg["bind_dn"],
                                password=cfg["bind_password"],
                                auto_bind=True, receive_timeout=10)
        return conn
    except Exception as e:
        LOG.error(f"LDAP bind failed ({uri or 'default'}): {e}")
        return None

def domain_root(domain):
    return ",".join(f"DC={p}" for p in domain.split("."))

# ---------------------------------------------------------------------------
# Coletores LDAP
# ---------------------------------------------------------------------------
def collect_fsmo(cfg):
    """Mapa das 5 roles FSMO -> DC owner."""
    conn = ldap_connect(cfg)
    if not conn:
        return {}
    root = domain_root(cfg["domain"])
    roles = {}
    for role, dn_tpl in FSMO_TARGETS:
        dn = dn_tpl.format(root=root)
        try:
            conn.search(dn, "(objectClass=*)", attributes=["fSMORoleOwner"])
            if conn.entries:
                owner_dn = str(conn.entries[0]["fSMORoleOwner"])
                m = re.search(r"CN=NTDS Settings,CN=([^,]+),CN=Servers", owner_dn)
                roles[role] = m.group(1) if m else "unknown"
        except Exception as e:
            LOG.error(f"FSMO query failed ({role}): {e}")
            roles[role] = "unknown"
    conn.unbind()
    LOG.info(f"FSMO roles: {roles}")
    return roles

def collect_domain(cfg):
    """Metricas de dominio: functional level, tombstone, password policy."""
    conn = ldap_connect(cfg)
    if not conn:
        return {}
    root = domain_root(cfg["domain"])
    out = {}
    try:
        conn.search(root, "(objectClass=domainDNS)",
                    attributes=["msDS-Behavior-Version", "minPwdLength",
                                "maxPwdAge", "lockoutThreshold", "pwdHistoryLength"])
        if conn.entries:
            e = conn.entries[0]
            lvl = int(str(e["msDS-Behavior-Version"]))
            out["functional_level"] = FUNCTIONAL_LEVELS.get(lvl, f"unknown({lvl})")
            out["min_pwd_len"] = int(str(e["minPwdLength"]))
            out["lockout_threshold"] = int(str(e["lockoutThreshold"]))
            out["pwd_history_len"] = int(str(e["pwdHistoryLength"]))
            max_age = int(str(e["maxPwdAge"]))
            out["max_pwd_age_days"] = round(abs(max_age) / 864000000000.0, 1) if max_age else 0
    except Exception as e:
        LOG.error(f"domain query failed: {e}")
    try:
        ds_dn = f"CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,{root}"
        conn.search(ds_dn, "(objectClass=*)", attributes=["tombstoneLifetime"])
        if conn.entries:
            out["tombstone_days"] = int(str(conn.entries[0]["tombstoneLifetime"]))
        else:
            out["tombstone_days"] = 180  # default AD/Samba
    except Exception as e:
        LOG.error(f"tombstone query failed: {e}")
        out["tombstone_days"] = 180
    conn.unbind()
    LOG.info(f"domain metrics: {out}")
    return out

def collect_accounts(cfg):
    """Contagens: users, computers, locked, expired."""
    conn = ldap_connect(cfg)
    if not conn:
        return {}
    root = domain_root(cfg["domain"])
    out = {}
    queries = {
        "users": "(&(objectClass=user)(objectCategory=person))",
        "computers": "(objectClass=computer)",
        "locked": "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=16))",
        "expired": ("(&(objectClass=user)(!(accountExpires=0))"
                    "(!(accountExpires=9223372036854775807))"
                    f"(accountExpires<={int((time.time() + 11644473600) * 10000000)}))"),
    }
    for key, flt in queries.items():
        try:
            conn.search(root, flt, attributes=["dn"])
            out[key] = len(conn.entries)
        except Exception as e:
            LOG.error(f"account query failed ({key}): {e}")
            out[key] = -1
    conn.unbind()
    LOG.info(f"account metrics: {out}")
    return out

def check_dc(cfg, dc_name, metric):
    """Metricas por DC: ldap | dns | roles."""
    if metric == "ldap":
        conn = ldap_connect(cfg, uri=f"ldap://{dc_name}.{cfg['domain']}")
        if conn:
            conn.unbind()
            return 1
        return 0
    if metric == "dns":
        try:
            import dns.resolver
            dns.resolver.resolve(f"{dc_name}.{cfg['domain']}", "A")
            return 1
        except Exception:
            return 0
    if metric == "roles":
        ttl = int(cfg.get("cache_ttl", 120))
        fsmo = get_cached("fsmo", ttl, lambda: collect_fsmo(cfg))
        held = [r for r, owner in fsmo.items() if owner.lower() == dc_name.lower()]
        return len(held)
    return -1

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        lib_lt.emit("Uso: lt_samba_ad.py <ping|discover_dcs|fsmo|domain|accounts|dc>", 1)

    cfg = load_config()
    ttl = int(cfg.get("cache_ttl", 120))
    cmd = sys.argv[1]

    try:
        if cmd == "ping":
            conn = ldap_connect(cfg)
            if conn:
                conn.unbind()
                lib_lt.emit(1)
            lib_lt.emit(0)

        elif cmd == "discover_dcs":
            dcs = discover_dcs_dns(cfg["domain"])
            lib_lt.emit(json.dumps({"data": [{"{#DC}": d} for l in [dcs] for d in l]}))

        elif cmd == "fsmo":
            fsmo = get_cached("fsmo", ttl, lambda: collect_fsmo(cfg))
            lib_lt.emit(json.dumps(fsmo))

        elif cmd == "domain" and len(sys.argv) == 3:
            dom = get_cached("domain", ttl, lambda: collect_domain(cfg))
            lib_lt.emit(dom.get(sys.argv[2], -1))

        elif cmd == "accounts" and len(sys.argv) == 3:
            acc = get_cached("accounts", ttl, lambda: collect_accounts(cfg))
            lib_lt.emit(acc.get(sys.argv[2], -1))

        elif cmd == "dc" and len(sys.argv) == 4:
            lib_lt.emit(check_dc(cfg, sys.argv[2], sys.argv[3]))

        else:
            LOG.error(f"unknown command: {cmd}")
            lib_lt.emit(-1, 1)
    except Exception as e:
        LOG.error(f"unhandled exception: {e}")
        lib_lt.emit(-1, 1)

if __name__ == "__main__":
    main()
