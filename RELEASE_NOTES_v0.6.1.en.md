# Lidorio-Zabbix-Pack v0.6.1 — Stable Release

**Release date:** August 30, 2026
**Status:** Stable for production

---

## What's new in this release

### LT TrueNAS v0.6.1 — Scrub Monitoring via SNMP Traps

**Problem solved:** TRUENAS-MIB 25.10 does not expose the last-scrub
timestamp via SNMP polling (verified by snmpwalk + analysis of the
official Zabbix template). Without this metric, ZFS pools can go
months without scrub, silently accumulating data corruption (bit rot)
with no alert.

**Solution:** end-to-end SNMP trap pipeline:

~~~
TrueNAS (truenas01)
  | sends trap when scrub completes/fails (OID .1.3.6.1.4.1.50536.2)
  v
firewalld (zabbix1, port 162/UDP)
  v
snmptrapd (zabbix1) + zabbix_trap_receiver.pl
  v
/var/log/snmptrap/snmptrap.log
  v
Zabbix Server (SNMPTrapperFile + StartSNMPTrapper=1)
  v
Item SNMP_TRAP: snmptrap[.*50536\.2.*]
  v
Triggers: HIGH (scrub failed) + AVERAGE (scrub found errors)
~~~

**Items added:**
- `TrueNAS: SNMP traps (alert/scrub events)` — captures TrueNAS MIB traps

**Triggers added:**
- HIGH `TrueNAS: Scrub failed (trap)` — trap contains "failed"
- AVERAGE `TrueNAS: Scrub found errors (trap)` — trap contains "errors"
- Both with `manual_close: YES` (stateless events)

---

## Issues solved in this release

| # | Issue | Root cause | Fix |
|---|-------|------------|-----|
| 1 | Traps not reaching Zabbix | firewalld: 162/udp only in permanent | `--add-port` + `--reload` |
| 2 | Perl writing to wrong path | `/tmp/zabbix_traps.tmp` hardcoded | sed to `/var/log/snmptrap/snmptrap.log` |
| 3 | SELinux blocking | snmpd_t write + zabbix_t read denied | lab: permissive; prod: audit2allow module |
| 4 | Scrub polling "No Such Object" | OID .1.1.1.1.12 missing in 25.10 | removed; scrub via traps |
| 5 | "unexpected tag triggers" on import | triggers at template level | moved inside item |

---

## Technical validation

**Environment:** Zabbix 7.0.30 LTS (Rocky 10.2) + TrueNAS SCALE 25.10.6 + snmptrapd 5.9.4

**Method:** full MIB snmpwalk; official 7.4 template analysis;
manual trap via `snmptrap`; log validation; import; trigger fire;
manual close; re-send.

**Result:** pipeline functional in < 5s from trap send.

---

## Compatibility

| Component | Version tested | Notes |
|-----------|----------------|-------|
| Zabbix Server | 7.0.30 LTS | requires `StartSNMPTrapper=1` in zabbix_server.conf |
| TrueNAS SCALE | 25.10.6 | SNMP v2c (lab) or v3 (prod) |
| snmptrapd | 5.9.4 | requires `net-snmp-perl` |
| firewalld | 1.3.x | 162/udp in runtime |
| SELinux | Rocky 10.2 | permissive (lab) or custom module (prod) |

---

## How to use

1. Import `Templates/TrueNAS/LT_TrueNAS.yaml` into Zabbix
2. TrueNAS host with SNMP v2c
3. On the Zabbix server: `net-snmp-perl` + snmptrapd.conf with
   `perl do "/usr/lib/zabbix/zabbix_trap_receiver.pl"` +
   `StartSNMPTrapper=1` + `firewall-cmd --add-port=162/udp --permanent && --reload`
4. Send a manual trap or wait for the next scrub
5. Validate at Monitoring -> Problems

---

## Project state after v0.6.1

~~~
v0.1.0  LT Linux Base
v0.2.0  LT Bareos
v0.3.0  LT NAS Storage (OMV)
v0.4.0  LT RustFS
v0.5.x  LT TrueNAS (MIB 25.10 + forecast + L2ARC/ZIL/temp)
v0.6.0  RPO/staleness/ZFS-depth
v0.6.1  Scrub via SNMP traps  <- THIS RELEASE
~~~

Full backup pipeline monitored:

~~~
Bareos (backup01) -> NAS (storage01/OMV) -> Restic -> RustFS (rustfs01)
   LT Bareos         LT NAS Storage                   LT RustFS
                                               +
                                         TrueNAS (truenas01)
                                          LT TrueNAS
~~~

---

## Next steps (v0.7.0+)

- v0.7.0 — Multi-distro install procedures + compatibility lib
- v0.8.0 — Executive Backup Dashboard
- v0.9.0 — New templates (OPNsense, MikroTik, PostgreSQL, etc.)

**Author:** Edson Lidorio | **License:** GPL-3.0
**Repo:** https://github.com/LidorioTec/Lidorio-Zabbix-Pack
