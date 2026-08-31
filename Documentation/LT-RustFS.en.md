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

## Installation

### Prerequisites

- Zabbix Server 7.0 LTS
- RustFS (S3-compatible storage)
- Python 3.8+ with `requests` library
- Zabbix Agent 2 on RustFS host

### Procedure

#### 1. Install dependencies (RustFS host)

Debian/Ubuntu:

~~~bash
sudo apt update && sudo apt install -y python3 python3-pip
sudo pip3 install requests
~~~

RHEL/Rocky/Alma:

~~~bash
sudo dnf install -y python3 python3-pip
sudo pip3 install requests
~~~

#### 2. Install collector

~~~bash
sudo mkdir -p /etc/zabbix/scripts

# Download main script
sudo wget -O /etc/zabbix/scripts/lt_rustfs.py \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/RustFS/lt_rustfs.py
sudo chmod 755 /etc/zabbix/scripts/lt_rustfs.py

# Create configuration file
sudo tee /etc/zabbix/scripts/lt_rustfs.conf > /dev/null << 'EOCONF'
rustfs_url=http://localhost:9000
access_key=YOUR_ACCESS_KEY_HERE
secret_key=YOUR_SECRET_KEY_HERE
EOCONF

sudo chmod 640 /etc/zabbix/scripts/lt_rustfs.conf
sudo chown root:zabbix /etc/zabbix/scripts/lt_rustfs.conf

# Install UserParameter
sudo wget -O /etc/zabbix/zabbix_agent2.d/lt_rustfs.conf \
  https://raw.githubusercontent.com/LidorioTec/Lidorio-Zabbix-Pack/main/Scripts/RustFS/userparameter_lt_rustfs.conf

# Restart agent
sudo systemctl restart zabbix-agent2
~~~

#### 3. Test

~~~bash
# Test script directly
sudo -u zabbix /etc/zabbix/scripts/lt_rustfs.py buckets
# expected: list of buckets

# Test via Zabbix (from Zabbix server)
zabbix_get -s RUSTFS_IP -k "rustfs.discover.buckets"
# expected: JSON with bucket list
~~~

#### 4. Import template and link host

1. Data collection → Templates → Import → `Templates/RustFS/LT_RustFS.yaml`
2. Data collection → Hosts → [RustFS host] → Link → `LT RustFS` → Update
3. Monitoring → Latest data → filter `rustfs`

## Troubleshooting

### "Permission denied" on script
Fix conf perms: `chown root:zabbix` + `chmod 640`

### "Connection refused" to RustFS
Verify RustFS is running and accessible at configured URL

### Item "Not supported"
Check UserParameter: `zabbix_agent2 -T | grep rustfs`; restart agent
