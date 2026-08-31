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

## Installation

### Prerequisites

- Zabbix Server 7.0 LTS
- Bareos Director 23.x/24.x/25.x
- PostgreSQL (Bareos catalog)
- Python 3.8+ on the Director host

### Procedure

#### 1. Prepare the database (Director host)

Debian/Ubuntu:

~~~bash
sudo apt update && sudo apt install -y postgresql-client
sudo -u postgres psql bareos << 'EOSQL'
CREATE USER zabbix_ro WITH PASSWORD 'YOUR_PASSWORD_HERE';
GRANT CONNECT ON DATABASE bareos TO zabbix_ro;
\c bareos
GRANT USAGE ON SCHEMA public TO zabbix_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO zabbix_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO zabbix_ro;
EOSQL
~~~

RHEL/Rocky/Alma: `sudo dnf install -y postgresql` + same SQL block.

#### 2. Install the collector (Director host)

~~~bash
sudo mkdir -p /etc/zabbix/scripts
sudo wget -O /etc/zabbix/scripts/lt_bareos_lastbackup.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/Bareos/lt_bareos_lastbackup.py
sudo chmod 755 /etc/zabbix/scripts/lt_bareos_lastbackup.py

sudo tee /etc/zabbix/scripts/lt_bareos.conf > /dev/null << 'EOCONF'
db_host=127.0.0.1
db_name=bareos
db_user=zabbix_ro
password=YOUR_PASSWORD_HERE
EOCONF
sudo chmod 640 /etc/zabbix/scripts/lt_bareos.conf
sudo chown root:zabbix /etc/zabbix/scripts/lt_bareos.conf

sudo wget -O /etc/zabbix/zabbix_agent2.d/lt_bareos_lastbackup.conf \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/Bareos/userparameter_lt_bareos_lastbackup.conf
sudo systemctl restart zabbix-agent2
~~~

RHEL/Rocky/Alma: same commands; restart with
`sudo systemctl restart zabbix-agent2 || sudo systemctl restart zabbix-agent`

#### 3. Test

~~~bash
sudo -u zabbix /etc/zabbix/scripts/lt_bareos_lastbackup.py "notebook-01-fd"
# expected: Unix timestamp

# from the Zabbix server:
zabbix_get -s BAREOS_IP -k "bareos.client.last.successful.backup[notebook-01-fd]"
~~~

#### 4. Import template and link host

1. Data collection → Templates → Import → `Templates/Bareos/LT_Bareos.yaml`
2. Data collection → Hosts → [Director host] → Link → `LT Bareos` → Update
3. Monitoring → Latest data → filter `last successful backup`

## Troubleshooting

### "Permission denied" on script
Fix conf perms: `chown root:zabbix` + `chmod 640`.

### "Connection refused" on PostgreSQL
Ensure `listen_addresses = 'localhost'` and
`host bareos zabbix_ro 127.0.0.1/32 md5` in pg_hba.conf; restart postgresql.

### Item "Not supported"
Check UserParameter: `zabbix_agent2 -T | grep bareos`; restart agent.
