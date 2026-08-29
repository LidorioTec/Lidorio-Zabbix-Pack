# LT TrueNAS

TrueNAS SCALE 25.10+ monitoring - LIDORIO TECH standard.

## Version
v0.5.0 - 2026-08-28

## Compatibility
- Zabbix Server 7.0 LTS (validated on 7.0.30)
- **TrueNAS SCALE 25.10.6** (OIDs specific to this version)

## Advantages over official Zabbix template

| Feature | Official 7.4 | **LT TrueNAS** |
|---------|--------------|----------------|
| OIDs for 25.10 | ❌ Broken | ✅ Validated on 25.10.6 |
| Capacity forecast | ❌ | ✅ `forecast()` (days to full) |
| ARC hit ratio trigger | ❌ | ✅ <80% = memory pressure |
| Agentless | ✅ SNMP | ✅ Pure SNMP (no Docker) |
| Correct datasets MIB | ❌ Swapped w/ zvols | ✅ `.1.6.1.1` (25.10) |

## Critical MIB changes in 25.10

iXsystems swapped several OIDs between datasets and zvols in version 25.10:

| Feature | Old OID (≤25.04) | Real OID (25.10+) |
|---------|-----------------|--------------------|
| Datasets | `.50536.1.2.1.1` | **`.50536.1.6.1.1`** |
| Zvols | `.50536.1.3.1.1` | **`.50536.1.2.1.1`** |
| L2ARC | `.50536.1.5.x` | **`.50536.1.4.x`** |
| ZIL | `.50536.1.6.x` | **`.50536.1.5.x`** |

## Prerequisites / Installation

1. Enable SNMP on TrueNAS: **Services → SNMP → Enable** (v2c, community `public` for lab)
2. Import `Templates/TrueNAS/LT_TrueNAS.yaml` into Zabbix
3. Link to host (SNMP v2c, community `public`)
4. Wait ~1h for LLDs to run

## Key macros
Pool/dataset capacity thresholds, ARC hit ratio, snapshot age.

## LLDs (2 rules)
- **ZFS pools discovery** (OID `.1.1.1.1.2`) → health, IOPS, bytes
- **ZFS datasets discovery** (OID `.1.6.1.1.2`, 25.10+) → used/avail/forecast

## Triggers (main)
- Pool not ONLINE = **HIGH**
- Dataset >80% = WARNING / >90% = AVERAGE
- Dataset full in <30 days = WARNING
- ARC hit ratio <80% = WARNING
- ICMP down / SNMP unavailable = HIGH/WARNING

## Validation
Tested on:
- `truenas01` (192.168.2.217) — TrueNAS SCALE 25.10.6
- Pool `tank` (MIRROR) with dataset `tank/backup`
- Zabbix Server 7.0.30 LTS

## Validation note (v0.6.0)
- Scrub: TRUENAS-MIB 25.10 does NOT expose a last-scrub OID (verified via
  snmpwalk and the official template). Scrub monitoring lands in v0.6.1 via
  SNMP traps (.1.3.6.1.4.1.50536.2) with snmptrapd on zabbix1.
- Disk temperature: VMs without sensors report 0 C; triggers only fire on
  HIGH temperature (no false positives).
