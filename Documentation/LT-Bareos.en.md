# LT Bareos

Bareos backup suite monitoring (Director, Storage Daemon, File Daemon,
catalog, jobs, pools) - LIDORIO TECH standard.

## Version
v0.2.0 - 2026-08-24

## Compatibility
- Zabbix Server 7.0 LTS (validated on 7.0.29)
- Collector tested with Zabbix Agent 2 7.2.15 (backup01, Debian 13)
- Bareos 25.1.x with PostgreSQL catalog

## Prerequisites / Installation
1. Create a read-only PostgreSQL role (zabbix_ro) with SELECT on catalog.
2. Install Scripts/Bareos/lt_bareos.py into /etc/zabbix/scripts/ (755).
3. Create /etc/zabbix/scripts/lt_bareos.conf (640 root:zabbix) from
   lt_bareos.conf.example. NEVER commit real credentials.
4. Install Scripts/Bareos/userparameter_lt_bareos.conf into
   /etc/zabbix/zabbix_agent2.d/ and restart the agent.

## Inheritance
Inherits LT Linux Base. Do NOT link LT Linux Base directly on hosts
that receive LT Bareos ("linked twice" error).

## Discovery rules (2)
- Bareos clients discovery (bareos.clients.discovery, 1h)
- Bareos pools discovery (bareos.pools.discovery, 1h)

## Macros (8)
Client/job age thresholds per level, scratch minimum (0 disables)
and Full size-drop percent (0 disables).

## Triggers (severity by level)
- Full FAILED = HIGH | Differential FAILED = AVERAGE | Incremental FAILED = WARNING
- Client without successful backup > WARN/HIGH days = AVERAGE/HIGH
- Director/SD DOWN = DISASTER | FD DOWN / catalog unreachable = HIGH
- Abrupt Full size drop = AVERAGE (continuity indicator)

## Troubleshooting
- -1 = no job of that level yet (items are Numeric float).
- agegood 99999 = client never had a successful backup ("unprotected").
- Bareos bsmtp/mailcommand errors do not change JobStatus of completed
  jobs; the collector does not depend on mailcommand by design.
- After changing prototypes, discovered items sync on the next LLD run
  (or server restart / Execute now).

## History
- v0.2.0 (2026-08-24): first release validated on Zabbix 7.0 LTS.
