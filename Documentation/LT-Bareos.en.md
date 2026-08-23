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

## Design decisions (vs. legacy community templates)

LT Bareos was designed based on a critical analysis of historical
implementations (2015-2018, Zabbix 2.4-3.4 / Bareos 15-17). The
following architectural decisions are deliberate differentiators of
this project:

### Non-invasive collection (read-only)
Legacy templates depend on hooks in `bareos-dir.conf`'s `mailcommand`
and `zabbix_sender` to push data to the server. This couples monitoring
to the job lifecycle and breaks when the mailer is unavailable. LT
Bareos queries the catalog via SQL in read-only mode (user `zabbix_ro`
with SELECT only), without changing any Bareos configuration.

### Data cache (120s)
All queries are batched into a single pass every 120 seconds,
regardless of the number of clients, pools or active items. Legacy
templates issued queries per job or per item, causing unnecessary
load on the catalog at scale.

### LLD combined with dynamic severity per level
Older templates had LLD (client discovery) **or** severity by backup
level (Full/Diff/Inc), but never both. LT Bareos uses trigger
prototypes inside the LLD to assign appropriate severity per level:
Full = HIGH, Differential = AVERAGE, Incremental = WARNING.

### Continuity indicators
Beyond last-job status, the template monitors:
- Age of the last successful backup per client (`agegood`)
- Abrupt size drop between consecutive Fulls (continuity / possible
  ransomware indicator)
- Specific age per level (Full, Diff, Inc)

These indicators detect policy failures and anomalous behavior that
a simple "last job failed?" misses.

### Explicit "no data" semantics
- `-1`: no job of that level yet (does not fire trigger)
- `99999`: client never had a successful backup (fires "unprotected")

Legacy templates often produced false positives or monitoring gaps in
these situations.

### Thresholds 100% via macros
All 8 threshold macros are adjustable per host without editing any
trigger. Setting a macro to `0` disables the corresponding indicator
(e.g., `{$BAREOS.SIZE.DROP.PCT}=0` turns off size-drop detection for
small/volatile clients).

### Inheritance and standardization
LT Bareos inherits LT Linux Base, avoiding duplication of OS/infra
items. Standardized tags (`component:*`, `service:bareos`) enable
consistent filtering in dashboards and actions. Zabbix host names do
not need to match Bareos client names (unlike some legacy
implementations), thanks to LLD.

## History
- v0.2.0 (2026-08-24): first release validated on Zabbix 7.0 LTS.
