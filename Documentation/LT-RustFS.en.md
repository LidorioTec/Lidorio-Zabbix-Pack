# LT RustFS

RustFS S3-compatible object storage monitoring - LIDORIO TECH standard.

## Version
v0.4.0 - 2026-08-27

## Compatibility
- Zabbix Server 7.0 LTS (validated on 7.0.30)
- RustFS 1.0.0-rc.3 (rustfs01, Debian 12)
- rc client 0.1.31

## Prerequisites / Installation
1. Install the rc binary (RustFS client) on the monitored host.
2. Install Scripts/RustFS/lt_rustfs.py into /etc/zabbix/scripts/ (755).
3. Create /etc/zabbix/scripts/lt_rustfs.conf (640 root:zabbix) from
   lt_rustfs.conf.example. NEVER commit real credentials.
4. Configure rc alias for the zabbix user (HOME=/var/lib/zabbix):
   sudo -u zabbix rc alias set rustfs_zabbix http://127.0.0.1:9000 USER PASS
5. Install Scripts/RustFS/userparameter_lt_rustfs.conf into
   /etc/zabbix/zabbix_agent2.d/ and restart the agent.

## Collection methods
- Health endpoints (/health, /minio/health/cluster) without auth.
- rc CLI (with alias) for buckets, objects and bytes.
- du/df for data volume capacity.
- 120s cache at /tmp/lt_rustfs.cache.json.

## Discovery rules (1)
- RustFS buckets discovery (rustfs.discover.buckets, 1h)

## Macros (3)
Capacity thresholds (WARN/HIGH) and minimum objects per bucket.

## Triggers
- RustFS unreachable = HIGH
- Cluster degraded = HIGH
- Data volume filling up / critically full = WARNING / HIGH
- Bucket empty = WARNING

## Known limitations
- RustFS 1.0.0-rc.3 does not expose admin.data-usage; the collector uses
  rc ls --recursive --summarize (client-side scan) for bytes/objects.

## History
- v0.4.0 (2026-08-27): first release (single-node, buckets LLD).
